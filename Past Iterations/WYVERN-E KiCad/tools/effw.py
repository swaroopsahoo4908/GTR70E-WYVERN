import pcbnew,sys,math,collections
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import unary_union
T=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]); cur={k:float(v) for k,v in (x.split('=') for x in sys.argv[2].split(','))}
def wreq(I,internal,dT=20):
    k=0.024 if internal else 0.048
    A=(I/(k*dT**0.44))**(1/0.725); t=1.378*(0.5 if internal else 1.0)
    return A/t*0.0254
def ps2shp(ps):
    out=[]
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i); pts=[(T(o.CPoint(k).x),T(o.CPoint(k).y)) for k in range(o.PointCount())]
        if len(pts)>2:
            p=Polygon(pts)
            for h in range(ps.HoleCount(i)):
                hh=ps.Hole(i,h); p=p.difference(Polygon([(T(hh.CPoint(k).x),T(hh.CPoint(k).y)) for k in range(hh.PointCount())]))
            out.append(p.buffer(0))
    return out
cop=collections.defaultdict(list)
for t in b.GetTracks():
    n=t.GetNetname()
    if n not in cur: continue
    if t.GetClass()=='PCB_VIA':
        for L in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu): cop[(n,L)].append(Point(T(t.GetPosition().x),T(t.GetPosition().y)).buffer(T(t.GetWidth(pcbnew.F_Cu))/2))
    else:
        s,e=t.GetStart(),t.GetEnd(); cop[(n,t.GetLayer())].append(LineString([(T(s.x),T(s.y)),(T(e.x),T(e.y))]).buffer(T(t.GetWidth())/2,8) if s!=e else Point(T(s.x),T(s.y)).buffer(T(t.GetWidth())/2))
for z in b.Zones():
    n=z.GetNetname()
    if n not in cur: continue
    for L in z.GetLayerSet().CuStack():
        if z.HasFilledPolysForLayer(L): cop[(n,L)]+=ps2shp(z.GetFilledPolysList(L))
for f in b.GetFootprints():
    for p in f.Pads():
        n=p.GetNetname()
        if n not in cur: continue
        for L in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu):
            if p.IsOnLayer(L):
                ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,L,0,pcbnew.FromMM(0.01),pcbnew.ERROR_INSIDE); cop[(n,L)]+=ps2shp(ps)
U={k:unary_union(v) for k,v in cop.items()}
rep=collections.defaultdict(lambda:[0,0,99])
for t in b.GetTracks():
    n=t.GetNetname()
    if n not in cur or t.GetClass()!='PCB_TRACK': continue
    s,e=t.GetStart(),t.GetEnd(); L=t.GetLayer()
    if s==e: continue
    a=(T(s.x),T(s.y)); c=(T(e.x),T(e.y)); ln=math.dist(a,c)
    if ln<0.8: continue
    internal=L in (pcbnew.In1_Cu,pcbnew.In2_Cu)
    req=wreq(cur[n],internal)
    dx,dy=(c[0]-a[0])/ln,(c[1]-a[1])/ln; worst=99
    for fr in (0.25,0.5,0.75):
        m=(a[0]+dx*ln*fr,a[1]+dy*ln*fr)
        cut=LineString([(m[0]-dy*8,m[1]+dx*8),(m[0]+dy*8,m[1]-dx*8)]).intersection(U[(n,L)])
        segs=[cut] if cut.geom_type=='LineString' else list(getattr(cut,'geoms',[]))
        w=max((g.length for g in segs if g.geom_type=='LineString' and g.distance(Point(m))<1e-3),default=T(t.GetWidth()))
        worst=min(worst,w)
    r=rep[n]; r[0]+=ln; r[2]=min(r[2],worst)
    if worst<req:
        r[1]+=ln
        if "-v" in sys.argv: print("  NARROW",n,b.GetLayerName(L),[round(v,2) for v in a],[round(v,2) for v in c],"w",round(T(t.GetWidth()),2),"eff",round(worst,2),"need",round(req,2))
print(f"{'net':12} {'I(A)':>5} {'need_out':>8} {'len_mm':>7} {'under_mm':>8} {'min_eff_w':>9}")
for n,(L,u,mw) in sorted(rep.items()):
    print(f"{n:12} {cur[n]:5.1f} {wreq(cur[n],False):8.2f} {L:7.1f} {u:8.1f} {mw:9.2f}")
