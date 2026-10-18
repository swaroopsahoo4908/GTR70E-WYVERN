import sys; sys.path.insert(0,'/tmp/w/conv')
import pcbnew,post
from shapely.geometry import LineString,Point
from shapely.strtree import STRtree
T=pcbnew.ToMM; M=pcbnew.FromMM
p=sys.argv[1]; nets=set(sys.argv[2].split(',')); R=float(sys.argv[3]); clr=float(sys.argv[4]) if len(sys.argv)>4 else 0.2
WS=[1.5,1.2,1.0,0.8,0.6,0.5,0.4,0.3,0.25]
b=pcbnew.LoadBoard(p)
for z in b.Zones(): z.UnFill()
edge=Point(100,100).buffer(R-0.35,256); n=0
for L in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu):
    items=post.copper_items(b,L); geoms=[g for _,g,_ in items]; tree=STRtree(geoms)
    for idx,(nc,g,o) in enumerate(items):
        if not isinstance(o,pcbnew.PCB_TRACK) or o.GetClass()=='PCB_VIA' or o.GetNetname() not in nets: continue
        s,e=o.GetStart(),o.GetEnd()
        ls=LineString([(T(s.x),T(s.y)),(T(e.x),T(e.y))]) if s!=e else Point(T(s.x),T(s.y))
        cur=T(o.GetWidth())
        for w in WS:
            if w<=cur+1e-6: break
            cand=ls.buffer(w/2,8)
            if not edge.contains(cand): continue
            test=ls.buffer(w/2+clr,8)
            if any(items[j][0]!=nc and test.intersects(items[j][1]) for j in tree.query(test)): continue
            o.SetWidth(M(w)); items[idx]=(nc,cand,o); geoms[idx]=cand; tree=STRtree(geoms); n+=1; break
b.Save(p); print('widened',n)
