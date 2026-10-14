import cadquery as cq,pcbnew,os,sys
from shapely.geometry import box
T=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]); D=sys.argv[2]
def crt(f):
    ps=f.GetCourtyard(pcbnew.F_CrtYd)
    bb=ps.BBox() if ps.OutlineCount() else f.GetBoundingBox(False)
    return box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
C={f.GetReference():crt(f) for f in b.GetFootprints()}
MB={}
for r in C:
    p=f'{D}/{r}.step'
    if not os.path.exists(p): continue
    a=cq.importers.importStep(p); bb=cq.Compound.makeCompound(a.vals()).BoundingBox()
    MB[r]=(box(bb.xmin,-bb.ymax,bb.xmax,-bb.ymin),bb.zmin,bb.zmax)
n=0
for r,(g,z0,z1) in MB.items():
    for o,(g2,a0,a1) in MB.items():
        if o<=r: continue
        if g.intersection(g2).area>0.02: print('3D overlap',r,o,round(g.intersection(g2).area,2),'mm2'); n+=1
    over=g.difference(C[r].buffer(0.3)).area
    if over>1.0: print(r,'body outside own courtyard',round(over,1),'mm2')
print('pairs overlapping',n,'models',len(MB))
