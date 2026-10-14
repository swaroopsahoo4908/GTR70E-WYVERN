"""apply manual edits: python3 medit.py board.kicad_pcb edits.json -> in place; prints DRC delta"""
import sys,json,subprocess,shutil,re
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,striptracks
from pcbbuild import V,MM
src=sys.argv[1]; E=json.load(open(sys.argv[2]))
def drc(p):
    subprocess.run(['kicad-cli','pcb','drc','--refill-zones','--severity-error','--format','json','-o','/tmp/w/_me.json',p],capture_output=True)
    d=json.load(open('/tmp/w/_me.json'))
    return d['unconnected_items'],[v for v in d['violations'] if v['type'] not in ('starved_thermal',)]
u0,v0=drc(src)
b=pcbnew.LoadBoard(src)
rm=set()
for t in b.GetTracks():
    if any(t.m_Uuid.AsString().startswith(p) for p in E.get('remove',[])): rm.add(t.m_Uuid.AsString())
tmp='/tmp/w/_me.kicad_pcb'
striptracks.remove_uuids(src,tmp,rm)
for ext in ('kicad_pro','kicad_dru'): shutil.copy(src.replace('kicad_pcb',ext),tmp.replace('kicad_pcb',ext))
b=pcbnew.LoadBoard(tmp)
L={'F':pcbnew.F_Cu,'B':pcbnew.B_Cu,'In2':pcbnew.In2_Cu}
for net,lay,pts,w in E.get('tracks',[]):
    for a,c in zip(pts,pts[1:]):
        t=pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(MM(w)); t.SetLayer(L[lay]); t.SetNetCode(b.FindNet(net).GetNetCode()); b.Add(t)
for net,x,y,d,dr in E.get('vias',[]):
    v=pcbnew.PCB_VIA(b); v.SetPosition(V(x,y)); v.SetWidth(MM(d)); v.SetDrill(MM(dr)); v.SetNetCode(b.FindNet(net).GetNetCode()); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
for ref,(x,y,a) in E.get('move',{}).items():
    f=[f for f in b.Footprints() if f.GetReference()==ref][0]; f.SetPosition(V(x,y)); f.SetOrientationDegrees(a)
pcbnew.SaveBoard(tmp,b)
u1,v1=drc(tmp)
print('removed',len(rm),'unconnected',len(u0),'->',len(u1),'viol',len(v0),'->',len(v1))
for v in v1: print('  V',v['type'],[ (i['description'][:50],round(i['pos']['x'],2),round(i['pos']['y'],2)) for i in v['items']])
for u in u1: print('  U',[ (i['description'][:45],round(i['pos']['x'],2),round(i['pos']['y'],2)) for i in u['items']])
if len(sys.argv)>3 and sys.argv[3]=='commit': shutil.copy(tmp,src); print('committed')
