import sys,json,re,subprocess,shutil
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,gridroute
pcbf,nets,w=sys.argv[1],set(sys.argv[2].split(',')),float(sys.argv[3])
lay={'F':pcbnew.F_Cu,'1':pcbnew.In1_Cu,'2':pcbnew.In2_Cu,'B':pcbnew.B_Cu}
RL=[lay[c] for c in (sys.argv[4] if len(sys.argv)>4 else 'F2B')]
clr=float(sys.argv[5]) if len(sys.argv)>5 else 0.15
C=(100,100)
def fill(b): pcbnew.ZONE_FILLER(b).Fill(b.Zones())
def unconnected(b):
    fill(b); tmp=pcbf.replace('.kicad_pcb','_tmpu.kicad_pcb'); pcbnew.SaveBoard(tmp,b)
    shutil.copy(pcbf.replace('.kicad_pcb','.kicad_pro'),tmp.replace('.kicad_pcb','.kicad_pro'))
    try: shutil.copy(pcbf.replace('.kicad_pcb','.kicad_dru'),tmp.replace('.kicad_pcb','.kicad_dru'))
    except Exception: pass
    subprocess.run(['kicad-cli','pcb','drc','--format','json','-o','/tmp/w/_u.json',tmp],capture_output=True)
    d=json.load(open('/tmp/w/_u.json')); out=[]
    for u in d.get('unconnected_items',[]):
        its=u['items']; net=re.search(r'\[([^\]]+)\]',its[0]['description']).group(1)
        out.append((net,(its[0]['pos']['x'],its[0]['pos']['y']),(its[1]['pos']['x'],its[1]['pos']['y']),its[0]['description'],its[1]['description']))
    return out
b=pcbnew.LoadBoard(pcbf)
R=pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetWidth())/2
uc=[u for u in unconnected(b) if u[0] in nets]
print('todo',len(uc))
for z in b.Zones(): z.UnFill()
r=gridroute.Router(b,C,R,clr=clr,layers=RL,tw=w,clr_check=clr,via=float(__import__("os").environ.get("VIA","0.5")),drill=float(__import__("os").environ.get("DRILL","0.3")))
r.fine_clr=0.1
import autoplace
fr=sys.argv[6].split(',') if len(sys.argv)>6 else []
if fr: r.fine_zones=[autoplace.rect_of(f) for f in b.Footprints() if f.GetReference() in fr]
for net,a,z,da,dz in sorted(uc,key=lambda u:(u[1][0]-u[2][0])**2+(u[1][1]-u[2][1])**2):
    code=b.FindNet(net).GetNetCode()
    la,lb=gridroute.lay_of(da),gridroute.lay_of(dz)
    la=la if la in RL else None; lb=lb if lb in RL else None
    ok=r.route(code,a,z,margin=6.0,w=w,a_lay=la,b_lay=lb) or r.route(code,a,z,margin=15.0,w=w,a_lay=la,b_lay=lb)
    print(net,ok,flush=True)
fill(b); b.Save(pcbf)
print('left',[u[0] for u in unconnected(pcbnew.LoadBoard(pcbf)) ])
