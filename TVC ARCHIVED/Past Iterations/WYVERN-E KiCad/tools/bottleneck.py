import pcbnew,sys,math,collections,heapq
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
T=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
pairs=[p.split('~') for p in sys.argv[2].split(',')]   # NET:REF.PAD~REF.PAD
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
LAY=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
def run(net,A,B):
    items=[]  # (geom, layers, width, kind, name)
    for t in b.GetTracks():
        if t.GetNetname()!=net: continue
        if t.GetClass()=='PCB_VIA':
            d=T(t.GetDrillValue()); w=math.pi*d*0.9  # plated barrel circumference ~ equivalent width (25um ~ 0.7oz)
            items.append((Point(T(t.GetPosition().x),T(t.GetPosition().y)).buffer(T(t.GetWidth(pcbnew.F_Cu))/2),set(LAY),w,'via',''))
        else:
            s,e=t.GetStart(),t.GetEnd(); w=T(t.GetWidth())
            if t.GetLayer() in (pcbnew.In1_Cu,pcbnew.In2_Cu): w*=0.5   # 0.5 oz inner
            g=LineString([(T(s.x),T(s.y)),(T(e.x),T(e.y))]).buffer(T(t.GetWidth())/2,8) if s!=e else Point(T(s.x),T(s.y)).buffer(T(t.GetWidth())/2)
            items.append((g,{t.GetLayer()},w,'trk',''))
    for z in b.Zones():
        if z.GetNetname()!=net: continue
        for L in z.GetLayerSet().CuStack():
            if z.HasFilledPolysForLayer(L):
                for p in ps2shp(z.GetFilledPolysList(L)):
                    # zone conductance proxy: 2x the largest inscribed radius (clipped to 3 mm)
                    r=0; lo,hi=0,3
                    for _ in range(10):
                        m=(lo+hi)/2
                        if not p.buffer(-m).is_empty: lo=m
                        else: hi=m
                    w=min(2*lo,6.0)*(0.5 if L in (pcbnew.In1_Cu,pcbnew.In2_Cu) else 1)
                    items.append((p,{L},w,'zone',z.GetZoneName()))
    pads={}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()!=net: continue
            ls=set(L for L in LAY if p.IsOnLayer(L))
            ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,list(ls)[0],0,pcbnew.FromMM(0.01),pcbnew.ERROR_INSIDE)
            g=unary_union(ps2shp(ps)); w=min(T(p.GetSize(list(ls)[0]).x),T(p.GetSize(list(ls)[0]).y))*2
            pads[f'{f.GetReference()}.{p.GetNumber()}']=len(items)
            items.append((g,ls,max(w,1.0),'pad',f'{f.GetReference()}.{p.GetNumber()}'))
    tree=STRtree([g for g,*_ in items])
    adj=collections.defaultdict(list)
    for i,(g,ls,w,k,nm) in enumerate(items):
        for j in tree.query(g.buffer(0.005)):
            if j<=i: continue
            g2,ls2,w2,k2,nm2=items[j]
            if not (ls & ls2): continue
            if g.distance(g2)>0.005: continue
            adj[i].append(j); adj[j].append(i)
    s,t=pads[A],pads[B]
    ca,cb=items[s][0].centroid,items[t][0].centroid
    ESC=float(__import__('os').environ.get('ESC','0'))
    W=[ (1e9 if ESC and it[3] in ('trk','via','pad') and (it[0].distance(ca)<ESC or it[0].distance(cb)<ESC) else it[2]) for it in items]
    # maximin path
    best={s:1e9}; h=[(-1e9,s)]; prev={}
    while h:
        nb,u=heapq.heappop(h); nb=-nb
        if u==t: break
        if nb<best.get(u,-1): continue
        for v in adj[u]:
            c=min(nb,W[v])
            if c>best.get(v,-1): best[v]=c; prev[v]=u; heapq.heappush(h,(-c,v))
    if t not in best: return None,None
    # find limiting element
    path=[t]; 
    while path[-1]!=s: path.append(prev[path[-1]])
    lim=min(path,key=lambda i:W[i])
    g=items[lim][0]
    return best[t],(items[lim][3],items[lim][4],[round(v,1) for v in g.centroid.coords[0]])
for netp,B in pairs:
    net,A=netp.split(':')
    w,lim=run(net,A,B)
    print(f"{net:11} {A:>10} -> {B:<10} bottleneck {w if w is None else round(w,2)} mm-eq  limited by {lim}")
