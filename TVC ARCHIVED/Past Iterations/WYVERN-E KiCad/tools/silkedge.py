import pcbnew,sys
from shapely.geometry import LineString,Point
T=pcbnew.ToMM; M=pcbnew.FromMM
p=sys.argv[1]; R=float(sys.argv[2]); lib=sys.argv[3] if len(sys.argv)>3 else None
b=pcbnew.LoadBoard(p); circ=Point(100,100).buffer(R-0.3,256); n=0; touched=set()
for f in b.GetFootprints():
    for g in list(f.GraphicalItems()):
        if g.GetLayer() not in (pcbnew.F_SilkS,pcbnew.B_SilkS) or g.GetClass()!='PCB_SHAPE' or g.GetShape()!=pcbnew.SHAPE_T_SEGMENT: continue
        s,e=g.GetStart(),g.GetEnd(); ln=LineString([(T(s.x),T(s.y)),(T(e.x),T(e.y))]); w=T(g.GetWidth())
        if circ.buffer(-w/2).contains(ln): continue
        cl=ln.intersection(circ.buffer(-w/2))
        parts=[cl] if cl.geom_type=='LineString' else list(getattr(cl,'geoms',[]))
        parts=[q for q in parts if q.geom_type=='LineString' and q.length>=0.3]
        if parts:
            c=list(parts[0].coords); g.SetStart(pcbnew.VECTOR2I(M(c[0][0]),M(c[0][1]))); g.SetEnd(pcbnew.VECTOR2I(M(c[-1][0]),M(c[-1][1])))
        else: f.Delete(g)
        n+=1; touched.add(f.GetReference())
b.Save(p); print('silk clipped',n,touched)
