import pcbnew,math
from pcbbuild import V,MM
def rect_of(f):
    bb=None
    for lay in (pcbnew.F_CrtYd,pcbnew.B_CrtYd):
        ps=f.GetCourtyard(lay)
        if ps.OutlineCount():
            b=ps.BBox(); bb=b if bb is None else bb.Merge(b) or bb
    if bb is None: bb=f.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()),pcbnew.ToMM(bb.GetTop()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
def side_of(f): return 'B' if f.GetLayer()==pcbnew.B_Cu else 'F'
def is_tht(f): return any(p.GetAttribute()in(pcbnew.PAD_ATTRIB_PTH,pcbnew.PAD_ATTRIB_NPTH) for p in f.Pads())
def ov(a,b,m): return not(a[2]+m<=b[0] or b[2]+m<=a[0] or a[3]+m<=b[1] or b[3]+m<=a[1])
def place(board,f,anchor_xy,sides=('F','B'),center=(100,100),R=33,edge=1.2,margin=0.35,rmax=30,angles=(0,90),keepout=None):
    keepout=keepout or {}
    fps=[x for x in board.Footprints() if x is not f and x.GetReference()!=f.GetReference()]
    for side in sides:
        if side_of(f)!=side: f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        obst=[]
        for x in fps:
            if x.GetReference().startswith('_'): continue
            if side_of(x)==side or is_tht(x) or x.GetReference().startswith('MH'):
                rr=rect_of(x); k=keepout.get(x.GetReference(),0)
                obst.append((rr[0]-k,rr[1]-k,rr[2]+k,rr[3]+k) if side_of(x)==side else rr)
        best=None
        ax,ay=anchor_xy
        step=0.25
        for ring in range(0,int(rmax/step)):
            rr=ring*step
            n=max(1,int(2*math.pi*rr/step))
            for k in range(n):
                th=2*math.pi*k/n
                x=ax+rr*math.cos(th); y=ay+rr*math.sin(th)
                for a in angles:
                    f.SetOrientationDegrees(a); f.SetPosition(V(x,y))
                    r=rect_of(f)
                    # inside circle
                    if any(math.hypot(px-center[0],py-center[1])>R-edge for px in (r[0],r[2]) for py in (r[1],r[3])): continue
                    if any(ov(r,o,margin) for o in obst): continue
                    return side,(x,y,a)
    return None
