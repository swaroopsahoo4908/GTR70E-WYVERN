import sys; sys.path.insert(0,'/tmp/w/conv')
import pcbnew,post,math
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
T=pcbnew.ToMM; M=pcbnew.FromMM
p=sys.argv[1]; R=float(sys.argv[2]); jobs=[(a.split('@')[0],tuple(map(float,a.split('@')[1].split(':')))) for a in sys.argv[3].split(',')]; N=int(sys.argv[4]) if len(sys.argv)>4 else 3
b=pcbnew.LoadBoard(p)
for z in b.Zones(): z.UnFill()
LAY=(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)
V=lambda q: pcbnew.VECTOR2I(M(q[0]),M(q[1]))
edge=Point(100,100).buffer(R-1.0,256)
for net,pos in jobs:
    nobj=b.FindNet(net); code=nobj.GetNetCode()
    obs={L:[(g,nn) for nn,g,o in post.copper_items(b,L)] for L in LAY}
    trees={L:STRtree([g for g,_ in v]) for L,v in obs.items()}
    # layers used by tracks touching the via
    lays=set()
    for t in b.GetTracks():
        if t.GetNetCode()==code and t.GetClass()=='PCB_TRACK':
            for e in (t.GetStart(),t.GetEnd()):
                if math.dist(T(e),pos)<0.05: lays.add(t.GetLayer())
    lays=lays or {pcbnew.F_Cu,pcbnew.B_Cu}
    def ok(geom,layers,c=0.2):
        for L in layers:
            for i in trees[L].query(geom.buffer(c+0.1)):
                g,nn=obs[L][i]
                if nn!=code and g.distance(geom)<c: return False
        return True
    added=[]
    for r in (0.9,1.2,1.5,1.8,2.1):
        for a in range(0,360,30):
            q=(pos[0]+r*math.cos(math.radians(a)),pos[1]+r*math.sin(math.radians(a)))
            if len(added)>=N: break
            if not edge.contains(Point(q)): continue
            if any(math.dist(q,x)<0.9 for x in added): continue
            vg=Point(q).buffer(0.3)
            lg=LineString([pos,q]).buffer(0.3)
            if not ok(vg,LAY) or not ok(lg,lays): continue
            v=pcbnew.PCB_VIA(b); v.SetPosition(V(q)); v.SetWidth(M(0.6)); v.SetDrill(M(0.3)); v.SetNet(nobj); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
            for L in lays:
                t=pcbnew.PCB_TRACK(b); t.SetStart(V(pos)); t.SetEnd(V(q)); t.SetWidth(M(0.6)); t.SetLayer(L); t.SetNet(nobj); b.Add(t)
            added.append(q)
            obs={L:[(g,nn) for nn,g,o in post.copper_items(b,L)] for L in LAY}; trees={L:STRtree([g for g,_ in v]) for L,v in obs.items()}
    print(net,pos,'added',len(added),[b.GetLayerName(L) for L in lays])
b.Save(p)
