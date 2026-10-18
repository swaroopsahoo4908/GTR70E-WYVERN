import sys,importlib,pcbnew,collections
sys.path.insert(0,'/tmp/w/conv')
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
from pcbbuild import MM
cfg=importlib.import_module(sys.argv[1]).cfg; src=sys.argv[2]
b=pcbnew.LoadBoard(src)
hc=[n for n,c in cfg['pcb']['netclass_assign'].items() if c=='HighCurrent']
geo=collections.defaultdict(list)
for t in b.GetTracks():
    if t.GetClass()!='PCB_TRACK' or t.GetNetname() not in hc: continue
    if t.GetLayer() not in (pcbnew.F_Cu,pcbnew.B_Cu): continue
    s,e=t.GetStart(),t.GetEnd()
    if s==e: continue
    geo[(t.GetNetname(),t.GetLayer())].append(LineString([(pcbnew.ToMM(s.x),pcbnew.ToMM(s.y)),(pcbnew.ToMM(e.x),pcbnew.ToMM(e.y))]).buffer(0.9,4))
for f in b.Footprints():
    for p in f.Pads():
        if p.GetNetname() in hc:
            for L in (pcbnew.F_Cu,pcbnew.B_Cu):
                if p.IsOnLayer(L) and (p.GetNetname(),L) in geo:
                    bb=p.GetBoundingBox(); geo[(p.GetNetname(),L)].append(Point(pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)).buffer(max(pcbnew.ToMM(bb.GetWidth()),pcbnew.ToMM(bb.GetHeight()))/2+0.3,8))
n=0
for (net,L),gs in geo.items():
    u=unary_union(gs).simplify(0.05)
    polys=[u] if u.geom_type=='Polygon' else list(u.geoms)
    for poly in polys:
        z=pcbnew.ZONE(b); z.SetLayer(L); z.SetNet(b.FindNet(net))
        o=z.Outline(); o.NewOutline()
        for x,y in list(poly.exterior.coords)[:-1]: o.Append(MM(x),MM(y))
        z.SetAssignedPriority(5); z.SetLocalClearance(MM(0.2)); z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetZoneName(f'HC_{net}'); b.Add(z); n+=1
pcbnew.SaveBoard(src,b); print('hc zones',n)
