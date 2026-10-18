import pcbnew,math,autoplace
from pcbbuild import V
def padpos(byref,key):
    r,n=key.split('.',1)
    for p in byref[r].Pads():
        if p.GetNumber()==n: return (pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y))
    raise KeyError(key)
def run(b,cfg,byref,R):
    FP=cfg['pcb']['floorplan']
    keep=set(FP['keep'])|{r for r in byref if r.startswith('MH')}
    fixed=FP['fixed']
    for ref,(x,y,a) in fixed.items():
        f=byref[ref]; f.SetOrientationDegrees(a); f.SetPosition(V(x,y))
    movable=[r for r in byref if r not in keep and r not in fixed]
    for i,r in enumerate(movable): byref[r].SetPosition(V(300+(i%20)*8,300+(i//20)*8))
    placed=set(keep)|set(fixed)
    first=[r for r in FP.get('order_first',[]) if r in movable]
    rest=sorted([r for r in movable if r not in first],key=lambda r:(r in FP.get('anchors',{}) and 0 or 1,r))
    log=[]
    queue=first+rest
    while queue:
        r=queue.pop(0)
        f=byref[r]
        a=FP.get('anchors',{}).get(r)
        if a and a.split('.')[0] not in placed:
            queue.append(r); continue
        if a: axy=padpos(byref,a)
        else:
            best=None
            for p in f.Pads():
                nn=p.GetNetname()
                if not nn or nn=='GND': continue
                for q in placed:
                    for pp in byref[q].Pads():
                        if pp.GetNetname()==nn:
                            pr=(0 if q[0] in 'UX' else 1)
                            pos=(pcbnew.ToMM(pp.GetPosition().x),pcbnew.ToMM(pp.GetPosition().y))
                            if best is None or pr<best[0]: best=(pr,pos)
            axy=best[1] if best else (100,100)
        res=autoplace.place(b,f,axy,('F',),center=(100,100),R=R,keepout=FP.get('keepout',{}),margin=FP.get('margin',0.4),angles=(0,90,180,270) if r.startswith(('LED','D','X','U')) else (0,90))
        if res is None: raise SystemExit('cannot place '+r)
        placed.add(r); log.append((r,a or 'auto',res[1]))
    return log
