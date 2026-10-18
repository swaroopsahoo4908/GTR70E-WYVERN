#!/usr/bin/env python3
"""
Independent ERC / DRC / connectivity verifier for generated boards.
Works on the Board object (pre-emit) + design netlist.

Checks:
  N1  PCB pad nets == schematic netlist (exact set match per net)
  N2  every net with >=2 pads is fully connected through copper
      (pads + tracks + vias + computed GND zone fill)
  D1  clearance between different-net copper >= CLR (tracks/pads/vias)
  D2  copper to board edge >= EDGE_CLR
  D3  courtyard overlaps
  D4  everything inside board
  Z1  GND zone fill connects all GND pads (fill computed like KiCad: board
      minus other-net copper buffered by zone clearance)
"""
import math
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity
from kicadgen import pad_abs_pos

CLR = 0.125       # JLCPCB min clearance capability 0.127; design classes 0.13+
EDGE_CLR = 0.25
ZONE_CLR = 0.3    # zone to other copper

def pad_shape(p, ax, ay, rot):
    ang = (p.ang + rot) % 360
    if p.shape == "circle" or (p.kind=="np_thru_hole"):
        return Point(ax, ay).buffer(max(p.w,p.h)/2, 16)
    g = box(ax-p.w/2, ay-p.h/2, ax+p.w/2, ay+p.h/2)
    if ang % 180 == 90:
        g = box(ax-p.h/2, ay-p.w/2, ax+p.h/2, ay+p.w/2)
    elif ang % 90 != 0:
        g = affinity.rotate(g, -ang, origin=(ax,ay))
    return g

def pad_layers(p):
    if p.kind in ("thru_hole","np_thru_hole"): return ("F.Cu","B.Cu")
    if '"B.Cu"' in p.layers: return ("B.Cu",)
    return ("F.Cu",)

class Geom:
    def __init__(self, board, netlist):
        self.b = board; self.netlist = netlist
        self.pad_geoms = []   # (ref,pad,num,net,layerset,shapely,is_hole)
        self.errors = []; self.warnings = []
        for (ref, fp, x, y, rot, pad_nets) in board.fp_index:
            pos = pad_abs_pos(fp, x, y, rot)
            for p in fp.pads:
                ax, ay = pos[str(p.num)]
                g = pad_shape(p, ax, ay, rot)
                net = pad_nets.get(str(p.num), "")
                self.pad_geoms.append(dict(ref=ref, num=str(p.num), net=net,
                    layers=pad_layers(p), geom=g, x=ax, y=ay,
                    nph=(p.kind=="np_thru_hole"), th=(p.kind=="thru_hole")))
        self.tracks = [dict(net=t[7], layer=t[5], width=t[4],
                            geom=LineString([(t[0],t[1]),(t[2],t[3])]).buffer(t[4]/2,8),
                            line=LineString([(t[0],t[1]),(t[2],t[3])]))
                       for t in board.tracks]
        self.vias = [dict(net=v[5], x=v[0], y=v[1],
                          geom=Point(v[0],v[1]).buffer(v[2]/2,12)) for v in board.vias]
        self.board_disc = Point(board.cx, board.cy).buffer(board.r, 64)

    # ---- N1: netlist match ----
    def check_netlist(self):
        sch = {}
        for net, pins in self.netlist.items():
            sch[net] = set(pins)
        pcb = {}
        for pg in self.pad_geoms:
            if pg['net']:
                pcb.setdefault(pg['net'], set()).add((pg['ref'], pg['num']))
        for net in sorted(set(sch) | set(pcb)):
            a = sch.get(net, set()); b = pcb.get(net, set())
            # schematic may list a (ref,pin) once; pcb pads with multiple same-number pads ok
            if a - b:
                self.errors.append(f"N1 {net}: in schematic but not on PCB: {sorted(a-b)}")
            extra = {(r,p) for (r,p) in (b - a) if not p.startswith("MP")}
            if extra:
                self.errors.append(f"N1 {net}: on PCB but not in schematic: {sorted(extra)}")

    # ---- zone fill (GND) ----
    def gnd_fill(self, layer):
        keep_out = []
        for t in self.tracks:
            if t['net'] != "GND" and t['layer'] == layer:
                keep_out.append(t['geom'].buffer(ZONE_CLR, 8))
        for v in self.vias:
            if v['net'] != "GND":
                keep_out.append(v['geom'].buffer(ZONE_CLR, 8))
        for pg in self.pad_geoms:
            if layer in pg['layers']:
                if pg['nph']:
                    keep_out.append(pg['geom'].buffer(ZONE_CLR, 8))
                elif pg['net'] != "GND":
                    keep_out.append(pg['geom'].buffer(ZONE_CLR, 8))
        fill = Point(self.b.cx, self.b.cy).buffer(self.b.r-0.25, 64)
        if keep_out:
            fill = fill.difference(unary_union(keep_out))
        # drop slivers
        fill = fill.buffer(-0.125, 8).buffer(0.125, 8)
        return fill

    # ---- N2/Z1: connectivity ----
    def check_connectivity(self):
        fills = {"F.Cu": self.gnd_fill("F.Cu"), "B.Cu": self.gnd_fill("B.Cu")}
        nets = {}
        for pg in self.pad_geoms:
            if pg['net']: nets.setdefault(pg['net'], []).append(pg)
        for net, pads in sorted(nets.items()):
            items = []
            for pg in pads:
                items.append(("pad", pg['layers'], pg['geom'], f"{pg['ref']}.{pg['num']}"))
            for t in self.tracks:
                if t['net']==net: items.append(("trk",(t['layer'],), t['geom'], "trk"))
            for v in self.vias:
                if v['net']==net: items.append(("via",("F.Cu","B.Cu"), v['geom'], "via"))
            if net == "GND":
                for lyr, f in fills.items():
                    geoms = list(f.geoms) if f.geom_type=="MultiPolygon" else [f]
                    for g in geoms:
                        items.append(("zone",(lyr,), g, f"zone{lyr}"))
            n = len(items)
            if n == 0: continue
            parent = list(range(n))
            def find(i):
                while parent[i]!=i:
                    parent[i]=parent[parent[i]]; i=parent[i]
                return i
            def union(i,j):
                ri,rj=find(i),find(j)
                if ri!=rj: parent[ri]=rj
            for i in range(n):
                for j in range(i+1,n):
                    if set(items[i][1]) & set(items[j][1]):
                        if items[i][2].intersects(items[j][2]):
                            union(i,j)
            comps = {}
            for i in range(n):
                comps.setdefault(find(i), []).append(i)
            pad_comps = set()
            for root, members in comps.items():
                if any(items[m][0]=="pad" for m in members):
                    pad_comps.add(root)
            if len(pad_comps) > 1:
                detail = []
                for root in pad_comps:
                    pads_in = [items[m][3] for m in comps[root] if items[m][0]=="pad"]
                    detail.append(str(pads_in[:6]))
                self.errors.append(f"N2 {net}: {len(pad_comps)} islands: " + " | ".join(detail))

    # ---- D1: clearance (STRtree) ----
    def check_clearance(self):
        from shapely.strtree import STRtree
        per_layer = {"F.Cu": [], "B.Cu": []}
        for pg in self.pad_geoms:
            tag = f"pad {pg['ref']}.{pg['num']}"
            for lyr in pg['layers']:
                if lyr in per_layer: per_layer[lyr].append((pg['net'], pg['geom'], tag))
        for t in self.tracks:
            per_layer[t['layer']].append((t['net'], t['geom'], "track"))
        for v in self.vias:
            for lyr in ("F.Cu","B.Cu"):
                per_layer[lyr].append((v['net'], v['geom'], f"via@{v['x']:.1f},{v['y']:.1f}"))
        reported=set()
        for lyr, items in per_layer.items():
            geoms=[it[1] for it in items]
            tree=STRtree(geoms)
            for i,gi in enumerate(geoms):
                idxs=tree.query(gi.buffer(CLR))
                for j in idxs:
                    j=int(j)
                    if j<=i: continue
                    if items[i][0]==items[j][0]: continue
                    ti,tj=items[i][2],items[j][2]
                    if ti.startswith('pad ') and tj.startswith('pad ') and                        ti.split()[1].split('.')[0]==tj.split()[1].split('.')[0]:
                        continue  # same-footprint package geometry
                    key=(lyr,i,j)
                    if key in reported: continue
                    d=gi.distance(geoms[j])
                    if d < CLR:
                        reported.add(key)
                        c1=gi.centroid
                        self.errors.append(
                            f"D1 {lyr}: '{items[i][0]}'({items[i][2]}) vs '{items[j][0]}'({items[j][2]}) = {d:.3f}mm @({c1.x:.1f},{c1.y:.1f})")

    # ---- D2/D4: edge ----
    def check_edge(self):
        rim = self.board_disc.boundary
        R = self.b.r
        for pg in self.pad_geoms:
            d = math.hypot(pg['x']-self.b.cx, pg['y']-self.b.cy)
            if pg['nph']: continue
            g=pg['geom']
            maxr = max(math.hypot(px-self.b.cx, py-self.b.cy) for px,py in g.exterior.coords)
            if maxr > R - EDGE_CLR and pg['ref'] not in ("J3",):  # SMA hangs over edge by design
                self.errors.append(f"D2 pad {pg['ref']}.{pg['num']} {R-maxr:.2f}mm from edge")
        for t in self.tracks:
            for px,py in t['line'].coords:
                if math.hypot(px-self.b.cx, py-self.b.cy) > R - EDGE_CLR - t['width']/2:
                    self.errors.append(f"D2 track net {t['net']} near edge @({px:.1f},{py:.1f})")
        for v in self.vias:
            if math.hypot(v['x']-self.b.cx, v['y']-self.b.cy) > R - EDGE_CLR - 0.3:
                self.errors.append(f"D2 via {v['net']} near edge")

    # ---- D3: courtyard ----
    def check_courtyard(self):
        crts=[]
        for (ref, fp, x, y, rot, pad_nets) in self.b.fp_index:
            x1,y1,x2,y2 = fp.courtyard
            g = box(x1,y1,x2,y2)
            if rot % 360:
                g = affinity.rotate(g, -rot, origin=(0,0))
            g = affinity.translate(g, x, y)
            crts.append((ref,g))
        for i in range(len(crts)):
            for j in range(i+1,len(crts)):
                if crts[i][1].intersects(crts[j][1]):
                    ov = crts[i][1].intersection(crts[j][1]).area
                    if ov > 0.01:
                        self.errors.append(f"D3 courtyard overlap {crts[i][0]} x {crts[j][0]} ({ov:.2f}mm2)")

    def run(self):
        self.check_netlist()
        self.check_connectivity()
        self.check_clearance()
        self.check_edge()
        self.check_courtyard()
        return self.errors, self.warnings

def verify(board, netlist, name):
    g = Geom(board, netlist)
    errors, warnings = g.run()
    print(f"==== VERIFY {name}: {len(errors)} errors, {len(warnings)} warnings ====")
    for e in errors[:80]: print("  ERR", e)
    for w in warnings[:20]: print("  WRN", w)
    return len(errors) == 0
