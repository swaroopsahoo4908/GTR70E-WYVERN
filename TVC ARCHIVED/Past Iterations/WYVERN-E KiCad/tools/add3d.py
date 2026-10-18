import sys,json,re,math,os,shutil
sys.path.insert(0,'/tmp/w/conv')
import pcbnew
proj=sys.argv[1]; name=sys.argv[2]
M=json.load(open('/tmp/w/m3d/map.json'))
FIX=json.load(open('/tmp/w/m3d/stepfix.json'))
des=json.load(open(f'/tmp/w/out/{name.split("_")[-1]}/_design.json'))
E2K='/tmp/w/m3d/lib.pretty'; SH='/tmp/w/m3d/lib.3dshapes'
os.makedirs(f'{proj}/3dmodels',exist_ok=True)
def pads_e2k(fpname):
    s=open(f'{E2K}/{fpname}.kicad_mod').read()
    P={}
    for num,x,y in re.findall(r'\(pad "?([^\s"]*)"? \w+ \w+ \(at ([-\d.]+) ([-\d.]+)',s):
        P.setdefault(num,[]).append((float(x),float(y)))
    mo=re.search(r'\(model "([^"]+)"\s*\(offset \(xyz ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\)\s*\(scale \(xyz ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\)\s*\(rotate \(xyz ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\)',s)
    return {k:(sum(a for a,b in v)/len(v),sum(b for a,b in v)/len(v),len(v)) for k,v in P.items() if k},mo
def pads_ours(f):
    P={}
    o=f.GetPosition(); a=math.radians(f.GetOrientationDegrees())
    for p in f.Pads():
        if not p.GetNumber(): continue
        q=p.GetPosition(); dx=pcbnew.ToMM(q.x-o.x); dy=pcbnew.ToMM(q.y-o.y)
        # undo footprint rotation (screen CCW by a): local = R(-a)
        lx= dx*math.cos(a) - dy*math.sin(a); ly= dx*math.sin(a) + dy*math.cos(a)
        P.setdefault(p.GetNumber(),[]).append((lx,ly))
    return {k:(sum(a for a,b in v)/len(v),sum(b for a,b in v)/len(v),len(v)) for k,v in P.items()}
def rot(p,th):
    c,s=math.cos(math.radians(th)),math.sin(math.radians(th)); x,y=p
    return (x*c+y*s,-x*s+y*c)
b=pcbnew.LoadBoard(f'{proj}/{name}.kicad_pcb')
report=[]; libmodels={}
for f in b.Footprints():
    r=f.GetReference()
    if r not in des['parts'] or not des['parts'][r].get('LCSC'): continue
    lc=des['parts'][r]['LCSC']; mm=M[lc]
    pe,mo=pads_e2k(mm['fp']); po=pads_ours(f)
    keys=[k for k in po if k in pe and po[k][2]==1 and pe[k][2]==1] or [k for k in po if k in pe]
    pe={k:v[:2] for k,v in pe.items()}; po={k:v[:2] for k,v in po.items()}
    best=None
    for th in (0,90,180,270):
        tr=[rot(pe[k],th) for k in keys]
        tx=sum(po[k][0]-q[0] for k,q in zip(keys,tr))/len(keys); ty=sum(po[k][1]-q[1] for k,q in zip(keys,tr))/len(keys)
        res=max(math.hypot(po[k][0]-q[0]-tx,po[k][1]-q[1]-ty) for k,q in zip(keys,tr))
        if best is None or res<best[0]: best=(res,th,tx,ty)
    res,th,tx,ty=best
    ox,oy,oz=float(mo.group(2)),float(mo.group(3)),float(mo.group(4)); rz=float(mo.group(10))
    q=rot((ox,-oy),th); nx,ny=q[0]+tx,q[1]+ty
    step=os.path.basename(mo.group(1)).replace('.wrl','.step')
    shutil.copy(f'{SH}/{step}',f'{proj}/3dmodels/{step}')
    rzt=(rz+th)%360; d=FIX.get(step,[0,0,0]); c,sn=math.cos(math.radians(rzt)),math.sin(math.radians(rzt))
    cx,cy=d[0]*c-d[1]*sn, d[0]*sn+d[1]*c
    nx+=cx; ny-=cy; oz+=d[2]
    m=pcbnew.FP_3DMODEL(); m.m_Filename='${KIPRJMOD}/3dmodels/'+step
    m.m_Offset=pcbnew.VECTOR3D(nx,-ny,oz); m.m_Rotation=pcbnew.VECTOR3D(float(mo.group(8)),float(mo.group(9)),(rz+th)%360); m.m_Scale=pcbnew.VECTOR3D(1,1,1); m.m_Show=True
    f.Models().clear(); f.Add3DModel(m)
    libmodels[f.GetFPID().GetLibItemName().wx_str() if hasattr(f.GetFPID().GetLibItemName(),'wx_str') else str(f.GetFPID().GetLibItemName())]=(m.m_Filename,(nx,-ny,oz),(float(mo.group(8)),float(mo.group(9)),(rz+th)%360))
    report.append((r,lc,mm['fp'],th,round(res,3)))
pcbnew.SaveBoard(f'{proj}/{name}.kicad_pcb',b)
# library footprints
lib=[d for d in os.listdir(proj) if d.endswith('.pretty')][0]
for fpn,(fn,off,rotv) in libmodels.items():
    p=f'{proj}/{lib}/{fpn}.kicad_mod'
    if not os.path.exists(p): continue
    s=open(p).read(); s=re.sub(r'\n\s*\(model .*?\n\s*\)\s*\n?(?=\s*\))','\n',s,flags=re.S)
    blk=f'\n  (model "{fn}" (offset (xyz {off[0]:.4f} {off[1]:.4f} {off[2]:.4f})) (scale (xyz 1 1 1)) (rotate (xyz {rotv[0]:g} {rotv[1]:g} {rotv[2]:g})))\n'
    s=s.rstrip(); assert s.endswith(')'); s=s[:-1]+blk+')\n'; open(p,'w').write(s)
bad=[x for x in report if x[4]>0.05]
print('models',len(report),'bad fits',bad)
print(sorted({(x[2],x[3]) for x in report if x[3]!=0}))
