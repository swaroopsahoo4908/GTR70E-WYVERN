"""remove given uuids, route listed nets first (by DRC unconnected order), then everything else; cleanup violations."""
import sys,json,subprocess,shutil
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,gridroute,striptracks
from route import fill
src,dst=sys.argv[1],sys.argv[2]; rm=sys.argv[3].split(','); first=sys.argv[4].split(',')
T='/tmp/w/_tg'
def drc(b):
    fill(b); pcbnew.SaveBoard(T+'.kicad_pcb',b)
    for e in ('kicad_pro','kicad_dru'): shutil.copy(src.replace('kicad_pcb',e),T+'.'+e)
    subprocess.run(['kicad-cli','pcb','drc','--severity-error','--format','json','-o',T+'.json',T+'.kicad_pcb'],capture_output=True)
    d=json.load(open(T+'.json'))
    return d['unconnected_items'],[v for v in d['violations'] if v['type'] in ('clearance','shorting_items','hole_clearance','tracks_crossing','hole_to_hole')]
b=pcbnew.LoadBoard(src)
ids={t.m_Uuid.AsString() for t in b.GetTracks() if any(t.m_Uuid.AsString().startswith(p) for p in rm)}
striptracks.remove_uuids(src,T+'0.kicad_pcb',ids)
for e in ('kicad_pro','kicad_dru'): shutil.copy(src.replace('kicad_pcb',e),T+'0.'+e)
b=pcbnew.LoadBoard(T+'0.kicad_pcb')
RL=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
uc,vi=drc(b); print('after rip',len(uc),flush=True)
for rnd in range(3):
    order=sorted(uc,key=lambda u:(0 if u['items'][0]['description'].split('[')[1].split(']')[0] in first else 1))
    for u in order:
        it=u['items']; net=it[0]['description'].split('[')[1].split(']')[0]
        a=(it[0]['pos']['x'],it[0]['pos']['y']); z=(it[1]['pos']['x'],it[1]['pos']['y'])
        ok=False
        for m in (2,5,10):
            r=gridroute.Router(b,(100,100),46.05,clr=0.11,layers=RL,tw=0.1,clr_check=0.129,via=0.5); r.fine_zones=[(50,50,150,150)]; r.fine_clr=0.099
            if r.route(b.FindNet(net).GetNetCode(),a,z,margin=m) or r.route(b.FindNet(net).GetNetCode(),z,a,margin=m): ok=True; break
        print(' ',net,ok,flush=True)
    uc,vi=drc(b); print('round',rnd,len(uc),len(vi),flush=True)
    if vi:
        bad={x['uuid'] for v in vi for x in v['items'] if x['description'].startswith(('Track','Via'))}
        pcbnew.SaveBoard(T+'w.kicad_pcb',b); striptracks.remove_uuids(T+'w.kicad_pcb',T+'w.kicad_pcb',bad); b=pcbnew.LoadBoard(T+'w.kicad_pcb')
        uc,vi=drc(b); print(' cleaned',len(uc),len(vi),flush=True)
    if not uc: break
pcbnew.SaveBoard(dst,b); print('final',len(uc),len(vi))
