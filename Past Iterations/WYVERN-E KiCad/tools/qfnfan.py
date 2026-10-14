"""Deterministic QFN/LFCSP fanout: every signal/power pad gets a short stub + via, alternating inward/outward,
geometrically checked against all copper so the autorouter only has to connect vias on the inner layers."""
import pcbnew,math
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
import post
from pcbbuild import V,MM
T=pcbnew.ToMM
def fan(b,ref,skip=('GND',),via=0.5,drill=0.3,clr=0.13,tw=0.15,inward_ok=True,n_in=None,rows_out=(0.45,1.2,1.95),exclude_pins=()):
    f=[x for x in b.Footprints() if x.GetReference()==ref][0]
    cx,cy=T(f.GetPosition().x),T(f.GetPosition().y)
    pads=[p for p in f.Pads() if p.GetNetname() and p.GetNetname() not in skip and p.GetNumber() not in exclude_pins]
    # geometry of everything on F.Cu and vias on all layers
    items=post.copper_items(b,pcbnew.F_Cu)
    geoms=[(g,n) for n,g,o in items]
    allv=[]
    for L in (pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu):
        for n,g,o in post.copper_items(b,L):
            if o is not None and o.GetClass()=='PCB_VIA': allv.append((g,n))
    added=[]   # (geom,netcode,isvia)
    # side geometry
    def side(p):
        dx=T(p.GetPosition().x)-cx; dy=T(p.GetPosition().y)-cy
        if abs(dx)>abs(dy): return (math.copysign(1,dx),0),dy,abs(dx)
        return (0,math.copysign(1,dy)),dx,abs(dy)
    # pad tip distances
    res=[0,0]
    order=sorted(pads,key=lambda p:(side(p)[0],side(p)[1]))
    idx={}
    for p in order:
        s,t,d=side(p); idx.setdefault(s,[]).append(p)
    for s,lst in idx.items():
        lst.sort(key=lambda p:side(p)[1])
        for k,p in enumerate(lst):
            nrm,t,d=side(p)
            sz=p.GetBoundingBox(); half=max(T(sz.GetWidth()),T(sz.GetHeight()))/2
            tip_out=d+half; tip_in=d-half
            px,py=T(p.GetPosition().x),T(p.GetPosition().y)
            tang=(-nrm[1],nrm[0])
            code=p.GetNetCode()
            cand=[]
            ins=[('in',tip_in-clr-via/2-0.02)] if inward_ok else []
            outs=[('out',tip_out+r+0.0) for r in rows_out]
            seq=(ins+outs) if (k%2==1) else (outs[:1]+ins+outs[1:])
            for kind,dn in seq:
                for dt in (0,0.2,-0.2,0.4,-0.4):
                    vx=px+nrm[0]*(dn-d)+tang[0]*dt; vy=py+nrm[1]*(dn-d)+tang[1]*dt
                    # stub: pad center -> along normal to (dn - 0.0) then lateral
                    mx=px+nrm[0]*(dn-d); my=py+nrm[1]*(dn-d)
                    pts=[(px,py),(mx,my)]+([(vx,vy)] if dt else [])
                    cand.append((pts,(vx,vy)))
            done=False
            for pts,(vx,vy) in cand:
                st=LineString(pts).buffer(tw/2,8); vg=Point(vx,vy).buffer(via/2,16)
                ok=True
                for g,n in geoms+[(a[0],a[1]) for a in added]:
                    if n==code: continue
                    lim=clr if not g.within(Point(cx,cy).buffer(d+half+0.05)) else 0.1
                    if g.distance(st)<lim or g.distance(vg)<clr: ok=False; break
                if ok:
                    for g,n in allv:
                        if n!=code and g.distance(vg)<clr: ok=False; break
                if ok:
                    for a in added:
                        if a[1]!=code and a[2] and a[0].distance(vg)<clr: ok=False; break
                if not ok: continue
                for (a,c) in zip(pts,pts[1:]):
                    tr=pcbnew.PCB_TRACK(b); tr.SetStart(V(*a)); tr.SetEnd(V(*c)); tr.SetWidth(MM(tw)); tr.SetLayer(pcbnew.F_Cu); tr.SetNetCode(code); tr.SetLocked(True); b.Add(tr)
                vi=pcbnew.PCB_VIA(b); vi.SetPosition(V(vx,vy)); vi.SetWidth(MM(via)); vi.SetDrill(MM(drill)); vi.SetNetCode(code); vi.SetViaType(pcbnew.VIATYPE_THROUGH); vi.SetLocked(True); b.Add(vi)
                added.append((st,code,False)); added.append((vg,code,True)); done=True; break
            res[0 if done else 1]+=1
            if not done: print('  fanout fail',ref,p.GetNumber(),p.GetNetname())
    return res
