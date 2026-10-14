import sys,math,json,collections
sys.path.insert(0,'/tmp/w/conv')
import pcbnew
from shapely.geometry import Polygon,Point,LineString,MultiPolygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
from pcbbuild import V,MM
from route import add_zone,circle_poly,fill
TOMM=pcbnew.ToMM
CU=None
def polyset_to_shapely(ps):
    polys=[]
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i); pts=[(TOMM(o.CPoint(j).x),TOMM(o.CPoint(j).y)) for j in range(o.PointCount())]
        holes=[]
        for h in range(ps.HoleCount(i)):
            hh=ps.Hole(i,h); holes.append([(TOMM(hh.CPoint(j).x),TOMM(hh.CPoint(j).y)) for j in range(hh.PointCount())])
        if len(pts)>=3: polys.append(Polygon(pts,holes).buffer(0))
    return unary_union(polys) if polys else Polygon()
def copper_items(b,layer):
    items=[]  # (netcode, geom)
    for f in b.Footprints():
        for p in f.Pads():
            if not p.IsOnLayer(layer): continue
            ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,layer,0,MM(0.005),pcbnew.ERROR_INSIDE)
            items.append((p.GetNetCode(),polyset_to_shapely(ps),p))
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                items.append((-1,Point(TOMM(p.GetPosition().x),TOMM(p.GetPosition().y)).buffer(TOMM(p.GetDrillSizeX())/2+0.05,16),p))
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA':
            if t.IsOnLayer(layer): items.append((t.GetNetCode(),Point(TOMM(t.GetPosition().x),TOMM(t.GetPosition().y)).buffer(TOMM(t.GetWidth(layer))/2,16),t))
        elif t.GetLayer()==layer:
            s,e=t.GetStart(),t.GetEnd()
            g=LineString([(TOMM(s.x),TOMM(s.y)),(TOMM(e.x),TOMM(e.y))]).buffer(TOMM(t.GetWidth())/2,8) if s!=e else Point(TOMM(s.x),TOMM(s.y)).buffer(TOMM(t.GetWidth())/2)
            items.append((t.GetNetCode(),g,t))
    return items
def widen(b,targets,edge_poly,clr_extra=0.0,clrmap=None):
    clrmap=clrmap or {}
    """targets: {netclass: [widths desc]}"""
    ns=b.GetDesignSettings().m_NetSettings
    nchanged=0
    for layer in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]:
        items=copper_items(b,layer)
        if not items: continue
        geoms=[g for n,g,o in items]; tree=STRtree(geoms)
        for idx,(n,g,o) in enumerate(items):
            if not isinstance(o,pcbnew.PCB_TRACK) or o.GetClass()=='PCB_VIA': continue
            cls=o.GetNetClassName().split(',')[0] if hasattr(o,'GetNetClassName') else o.GetEffectiveNetClass().GetName()
            if cls not in targets: continue
            clr=clrmap.get(cls,0.15)+clr_extra
            s,e=o.GetStart(),o.GetEnd()
            ls=LineString([(TOMM(s.x),TOMM(s.y)),(TOMM(e.x),TOMM(e.y))]) if s!=e else Point(TOMM(s.x),TOMM(s.y))
            cur=TOMM(o.GetWidth())
            for w in targets[cls]:
                if w<=cur+1e-6: break
                cand=ls.buffer(w/2,8)
                if not edge_poly.contains(cand): continue
                test=ls.buffer(w/2+clr,8)
                bad=False
                for j in tree.query(test):
                    nj,gj,oj=items[j]
                    if nj==n: continue
                    if test.intersects(gj): bad=True;break
                if not bad:
                    o.SetWidth(MM(w)); items[idx]=(n,cand,o); geoms[idx]=cand; nchanged+=1
                    tree=STRtree(geoms)
                    break
    return nchanged
def stitch(b,gnd,R,center,pitch=2.6,via=0.6,drill=0.3,clr=0.2,edge_ring=True):
    fill(b)
    ni=b.FindNet(gnd)
    lay=[pcbnew.F_Cu,pcbnew.B_Cu]
    gf={}
    for z in [b.GetArea(i) for i in range(b.GetAreaCount())]:
        if z.GetNetname()==gnd and z.GetLayer() in lay:
            gf.setdefault(z.GetLayer(),[]).append(polyset_to_shapely(z.GetFilledPolysList(z.GetLayer())))
    if not all(l in gf for l in lay): return 0
    ok=unary_union(gf[lay[0]]).buffer(-(via/2+0.05)).intersection(unary_union(gf[lay[1]]).buffer(-(via/2+0.05)))
    # avoid other-net copper on inner signal layer
    inner=[pcbnew.In1_Cu,pcbnew.In2_Cu]
    block=[]
    for l in inner:
        for n,g,o in copper_items(b,l):
            if n!=ni.GetNetCode(): block.append(g.buffer(via/2+clr))
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH,):
                block.append(Point(TOMM(p.GetPosition().x),TOMM(p.GetPosition().y)).buffer(TOMM(p.GetDrillSizeX())/2+via/2+0.3))
    blk=unary_union(block) if block else Polygon()
    ok=ok.difference(blk)
    pts=[]
    cx,cy=center
    if edge_ring:
        rr=R-1.0; n=int(2*math.pi*rr/2.0)
        pts+=[(cx+rr*math.cos(2*math.pi*k/n),cy+rr*math.sin(2*math.pi*k/n)) for k in range(n)]
    x=cx-R
    while x<cx+R:
        y=cy-R
        while y<cy+R:
            if math.hypot(x-cx,y-cy)<R-2.0: pts.append((x,y))
            y+=pitch
        x+=pitch
    placed=[]
    for x,y in pts:
        if not ok.contains(Point(x,y)): continue
        if any(math.hypot(x-a,y-c)<pitch*0.8 for a,c in placed): continue
        v=pcbnew.PCB_VIA(b); v.SetPosition(V(x,y)); v.SetWidth(MM(via)); v.SetDrill(MM(drill)); v.SetNet(ni); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        b.Add(v); placed.append((x,y))
    return len(placed)
