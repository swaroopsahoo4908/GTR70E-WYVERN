import sys,json,subprocess,re,shutil,importlib
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,gridroute,autoplace
from route import fill
from shapely.geometry import Point,LineString
cfg=importlib.import_module(sys.argv[1]).cfg
T='/tmp/w/_p2_'+sys.argv[1]
src=sys.argv[2]; dst=sys.argv[3]
proj=src.replace('.kicad_pcb','.kicad_pro'); dru=src.replace('.kicad_pcb','.kicad_dru')
def load(p): return pcbnew.LoadBoard(p)
def check(b):
    fill(b); tmp=T+'.kicad_pcb'; pcbnew.SaveBoard(tmp,b)
    shutil.copy(proj,T+'.kicad_pro'); shutil.copy(dru,T+'.kicad_dru')
    subprocess.run(['kicad-cli','pcb','drc','--severity-error','--format','json','-o',T+'.json',tmp],capture_output=True)
    d=json.load(open(T+'.json'))
    uc=[]
    for u in d.get('unconnected_items',[]):
        its=u['items']; net=re.search(r'\[([^\]]+)\]',its[0]['description']).group(1)
        uc.append((net,(its[0]['pos']['x'],its[0]['pos']['y']),(its[1]['pos']['x'],its[1]['pos']['y']),its[0]['description'],its[1]['description']))
    vi=[v for v in d['violations'] if v['type'] in ('clearance','shorting_items','hole_clearance','tracks_crossing','hole_to_hole','via_dangling','track_dangling')]
    return uc,vi
RL=[pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu] if cfg['pcb'].get('in1_plane',True) else [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
fine=cfg['pcb'].get('fine_refs',['U1'])
def router(b):
    R=pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetWidth())/2
    r=gridroute.Router(b,(100,100),R,clr=0.135,layers=RL,tw=0.15,clr_check=0.129,via=0.5)
    r.fine_zones=[autoplace.rect_of(f) for f in b.Footprints() if f.GetReference() in fine]; r.fine_clr=0.11
    return r
cur=src
b=load(cur); uc,vi=check(b); best=len(uc); print('start',best,len(vi),flush=True)
pcbnew.SaveBoard(T+'best.kicad_pcb',b)
for rad in (0.8,1.3,2.0):
    progress=True
    while progress and uc:
        progress=False
        for (net,a,z,da,dz) in list(uc):
            b=load(T+'best.kicad_pcb')
            rip=set()
            for pt in (a,z):
                P=Point(*pt)
                for t in b.GetTracks():
                    nn=t.GetNetname()
                    if nn==net: continue
                    if t.GetClass()=='PCB_VIA':
                        if P.distance(Point(pcbnew.ToMM(t.GetPosition().x),pcbnew.ToMM(t.GetPosition().y)))<rad: rip.add(t.m_Uuid.AsString())
                    else:
                        s_,e_=t.GetStart(),t.GetEnd()
                        if s_!=e_ and P.distance(LineString([(pcbnew.ToMM(s_.x),pcbnew.ToMM(s_.y)),(pcbnew.ToMM(e_.x),pcbnew.ToMM(e_.y))]))<rad: rip.add(t.m_Uuid.AsString())
            import striptracks
            striptracks.remove_uuids(T+'best.kicad_pcb',T+'work.kicad_pcb',rip); b=load(T+'work.kicad_pcb')
            uc2,_=check(b)
            # route target first, then others
            order=[u for u in uc2 if u[0]==net]+[u for u in uc2 if u[0]!=net]
            r=router(b)
            for n2,a2,z2,d2a,d2z in order:
                if b.FindNet(n2) is None: continue
                code=b.FindNet(n2).GetNetCode()
                r.route(code,a2,z2,margin=6,a_lay=gridroute.lay_of(d2a),b_lay=gridroute.lay_of(d2z)) or r.route(code,a2,z2,margin=14,a_lay=gridroute.lay_of(d2a),b_lay=gridroute.lay_of(d2z))
            uc3,vi3=check(b)
            for _fix in range(3):
                if not vi3: break
                bad=set()
                for v in vi3:
                    for it in v['items']:
                        if it['description'].startswith(('Track','Via')): bad.add(it['uuid'])
                if not bad: break
                pcbnew.SaveBoard(T+'work2.kicad_pcb',b); striptracks.remove_uuids(T+'work2.kicad_pcb',T+'work2.kicad_pcb',bad); b=load(T+'work2.kicad_pcb')
                uc3,vi3=check(b); r=router(b)
                for n2,a2,z2,d2a,d2z in uc3:
                    if b.FindNet(n2) is None: continue
                    r.route(b.FindNet(n2).GetNetCode(),a2,z2,margin=10,a_lay=gridroute.lay_of(d2a),b_lay=gridroute.lay_of(d2z))
                uc3,vi3=check(b)
            print(f'rad {rad} target {net}: ripped {len(rip)} -> unconnected {len(uc3)} viol {len(vi3)} (best {best})',flush=True)
            if len(uc3)<best and not vi3:
                best=len(uc3); uc=uc3; pcbnew.SaveBoard(T+'best.kicad_pcb',b); progress=True; break
shutil.copy(T+'best.kicad_pcb',dst); print('final',best)
