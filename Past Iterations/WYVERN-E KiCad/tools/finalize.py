import sys,importlib,json,math,os,re,subprocess
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,post,sesimport,silk,gridroute
from route import add_zone,circle_poly,fill
from pcbbuild import V,MM
cfg=importlib.import_module(sys.argv[1]).cfg
DRU="""(version 1)
"""+''.join(f"(rule \"Fine-pitch escape {r_}\" (condition \"A.intersectsCourtyard('{r_}') && B.intersectsCourtyard('{r_}')\") (constraint clearance (min 0.1mm)))\n" for r_ in cfg['pcb'].get('fine_refs',['U1']))+''.join(f"(rule \"Footprint-internal hole {r_}\" (condition \"A.intersectsCourtyard('{r_}') && B.intersectsCourtyard('{r_}')\") (constraint hole_clearance (min 0mm)))\n" for r_ in cfg['pcb'].get('hole_exempt',[]))+cfg['pcb'].get('extra_dru','')
ses=sys.argv[2]
tag=cfg['name'].split('_')[-1]; OUT=f'/tmp/w/out/{tag}'
import striptracks; striptracks.strip(f'{OUT}/stage_placed.kicad_pcb',f'{OUT}/stage_notracks.kicad_pcb')
import shutil; shutil.copy(f'{OUT}/stage_placed.kicad_pro',f'{OUT}/stage_notracks.kicad_pro')
b=pcbnew.LoadBoard(f'{OUT}/stage_notracks.kicad_pcb')
print('netclass check',b.FindNet('+3V3').GetNetClassName() if b.FindNet('+3V3') else '')
b.SetLayerType(pcbnew.In1_Cu,pcbnew.LT_POWER); b.SetLayerType(pcbnew.In2_Cu,pcbnew.LT_SIGNAL)
b.SetLayerName(pcbnew.In1_Cu,'In1.GND'); b.SetLayerName(pcbnew.In2_Cu,'In2.SIG_PWR')
print('ses',sesimport.import_ses(b,ses))
_bp=pcbnew.LoadBoard(f'{OUT}/stage_planes.kicad_pcb'); _n=0
for t in _bp.GetTracks():
    if t.IsLocked():
        if t.GetClass()=='PCB_VIA':
            v=pcbnew.PCB_VIA(b); v.SetPosition(t.GetPosition()); v.SetWidth(t.GetWidth(pcbnew.F_Cu)); v.SetDrill(t.GetDrillValue()); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(b.FindNet(t.GetNetname())); b.Add(v)
        else:
            n=pcbnew.PCB_TRACK(b); n.SetStart(t.GetStart()); n.SetEnd(t.GetEnd()); n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNet(b.FindNet(t.GetNetname())); b.Add(n)
        _n+=1
print('locked copied',_n)
import fanout
print('EP vias (post)',fanout.ep_vias(b,'GND',check=True))
bb=b.GetBoardEdgesBoundingBox(); R=pcbnew.ToMM(bb.GetWidth())/2; C=(100,100)
pts=circle_poly(C[0],C[1],R-0.4)
z1=add_zone(b,pcbnew.In1_Cu,'GND',pts,prio=0,clear=0.2)
RL=[pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu] if cfg['pcb'].get('in1_plane',True) else [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
fill(b)
def unconnected(b):
    fill(b)
    tmp=f'{OUT}/_tmp_drc.kicad_pcb'; pcbnew.SaveBoard(tmp,b); shutil.copy(f'{OUT}/stage_placed.kicad_pro',f'{OUT}/_tmp_drc.kicad_pro')
    open(f'{OUT}/_tmp_drc.kicad_dru','w').write(DRU)
    subprocess.run(['kicad-cli','pcb','drc','--format','json','-o',f'{OUT}/_tmp_drc.json',tmp],capture_output=True)
    d=json.load(open(f'{OUT}/_tmp_drc.json'))
    out=[]
    for u in d.get('unconnected_items',[]):
        its=u['items']
        net=re.search(r'\[([^\]]+)\]',its[0]['description']).group(1)
        out.append((net,(its[0]['pos']['x'],its[0]['pos']['y']),(its[1]['pos']['x'],its[1]['pos']['y']),its[0]['description'],its[1]['description']))
    return out,d
uc,_=unconnected(b); print('unconnected before gridroute',len(uc))
r=gridroute.Router(b,C,R,clr=cfg['pcb'].get('gr_clr',0.18),layers=RL,tw=cfg['pcb'].get('gr_tw',0.15))
import autoplace
fine_refs=cfg['pcb'].get('fine_refs',['U1'])
r.fine_zones=cfg['pcb'].get('gr_fine_zones') or [autoplace.rect_of(f) for f in b.Footprints() if f.GetReference() in fine_refs]; r.fine_clr=cfg['pcb'].get('gr_fine_clr',0.12)
failed=[]
for net,a,z,da,dz in uc:
    code=b.FindNet(net).GetNetCode()
    ok=r.route(code,a,z,a_lay=gridroute.lay_of(da),b_lay=gridroute.lay_of(dz))
    if not ok: ok=r.route(code,a,z,margin=20.0,a_lay=gridroute.lay_of(da),b_lay=gridroute.lay_of(dz))
    if not ok: ok=False
    print('route',net,ok,flush=True)
    if not ok: failed.append((net,da,dz))
uc,_=unconnected(b); print('unconnected after gridroute',len(uc)); 
for u in uc: print('  ',u[0],u[3],'<->',u[4])
from shapely.geometry import Point as _P, LineString as _L
protect={'GND'}
for attempt in range(0):
    if not uc: break
    snap=f'{OUT}/_snap.kicad_pcb'; pcbnew.SaveBoard(snap,b); prev_n=len(uc); prev_uc=uc
    fail=set(u[0] for u in uc)
    rip=set(fail)
    rad=1.2+0.6*attempt
    for net,a,z,da,dz in uc:
        for pt in (a,z):
            P=_P(*pt)
            for t in b.GetTracks():
                nn=t.GetNetname()
                if nn in rip or nn in protect: continue
                if t.GetClass()=='PCB_VIA':
                    if P.distance(_P(pcbnew.ToMM(t.GetPosition().x),pcbnew.ToMM(t.GetPosition().y)))<rad: rip.add(nn)
                else:
                    s_,e_=t.GetStart(),t.GetEnd()
                    if s_!=e_ and P.distance(_L([(pcbnew.ToMM(s_.x),pcbnew.ToMM(s_.y)),(pcbnew.ToMM(e_.x),pcbnew.ToMM(e_.y))]))<rad: rip.add(nn)
    for grp in cfg['pcb'].get('rip_groups',[]):
        if rip & set(grp): rip|=set(grp)
    print('attempt',attempt,'fail',sorted(fail),'ripup',len(rip),flush=True)
    for t in list(b.GetTracks()):
        if t.GetNetname() in rip: b.Remove(t)
    fill(b)
    uc2,_=unconnected(b)
    r=gridroute.Router(b,C,R,clr=cfg['pcb'].get('gr_clr',0.18),layers=RL,tw=cfg['pcb'].get('gr_tw',0.15)); r.fine_zones=cfg['pcb'].get('gr_fine_zones') or [autoplace.rect_of(f) for f in b.Footprints() if f.GetReference() in fine_refs]; r.fine_clr=cfg['pcb'].get('gr_fine_clr',0.12)
    todo=[u for u in uc2 if u[0] in rip]
    first=[u for u in todo if u[0] in fail]; rest=[u for u in todo if u[0] not in fail]
    key=lambda u:(u[1][0]-u[2][0])**2+(u[1][1]-u[2][1])**2
    for net,a,z,da,dz in sorted(first,key=key)+sorted(rest,key=key):
        if b.FindNet(net) is None: print('  no net',net,da); continue
        code=b.FindNet(net).GetNetCode()
        cls=b.FindNet(net).GetNetClassName() if hasattr(b.FindNet(net),'GetNetClassName') else 'Default'
        w=0.2 if any(k in cls for k in ('Power','HighCurrent')) else 0.15
        ok=r.route(code,a,z,margin=10.0,w=w) or r.route(code,a,z,margin=25.0,w=w)
    uc,_=unconnected(b); print('unconnected after attempt',attempt,len(uc),flush=True)
    if len(uc)>=prev_n:
        b=pcbnew.LoadBoard(snap); uc=prev_uc
        z1=[b.GetArea(i) for i in range(b.GetAreaCount())][0]
        print('attempt worse, reverted',flush=True); break
    for u in uc: print('  ',u[0],u[3],'<->',u[4])

def violations(b):
    fill(b)
    tmp=f'{OUT}/_tmp_drc.kicad_pcb'; pcbnew.SaveBoard(tmp,b); shutil.copy(f'{OUT}/stage_placed.kicad_pro',f'{OUT}/_tmp_drc.kicad_pro')
    open(f'{OUT}/_tmp_drc.kicad_dru','w').write(DRU)
    subprocess.run(['kicad-cli','pcb','drc','--severity-error','--format','json','-o',f'{OUT}/_tmp_v.json',tmp],capture_output=True)
    d=json.load(open(f'{OUT}/_tmp_v.json'))
    bad=set()
    for v in d['violations']:
        if v['type'] in ('clearance','shorting_items','tracks_crossing','hole_clearance','copper_edge_clearance','hole_to_hole','holes_co_located','track_dangling','via_dangling'):
            for it in v['items']:
                if it['description'].startswith(('Track','Via','Arc')): bad.add(it['uuid'])
    return bad
for rep_i in range(4):
    bad=violations(b)
    print('repair',rep_i,'bad items',len(bad),flush=True)
    if not bad: break
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() in bad: b.Remove(t)
    fill(b)
    uc,_=unconnected(b); print('  unconnected',len(uc),flush=True)
    r=gridroute.Router(b,C,R,clr=cfg['pcb'].get('gr_clr',0.2),layers=RL,tw=cfg['pcb'].get('gr_tw',0.15)); r.fine_zones=cfg['pcb'].get('gr_fine_zones') or [autoplace.rect_of(f) for f in b.Footprints() if f.GetReference() in fine_refs]; r.fine_clr=cfg['pcb'].get('gr_fine_clr',0.12)
    for net,a,z,da,dz in sorted(uc,key=lambda u:(u[1][0]-u[2][0])**2+(u[1][1]-u[2][1])**2):
        if b.FindNet(net) is None: continue
        code=b.FindNet(net).GetNetCode()
        ok=r.route(code,a,z,margin=10.0,a_lay=gridroute.lay_of(da),b_lay=gridroute.lay_of(dz)) or r.route(code,a,z,margin=25.0,a_lay=gridroute.lay_of(da),b_lay=gridroute.lay_of(dz)) or False
    uc,_=unconnected(b); print('  after repair routing',len(uc),flush=True)
for u in uc: print('  ',u[0],u[3],'<->',u[4])
b.Remove(z1)
from shapely.geometry import Point
edge=Point(*C).buffer(R-0.3,256)
n=post.widen(b,cfg['pcb']['widen'],edge,clrmap={k:0.17 for k in cfg['pcb']['netclasses']}); print('widened',n)
add_zone(b,pcbnew.In1_Cu,'GND',pts,prio=0,clear=0.2)
add_zone(b,pcbnew.In2_Cu,cfg['pcb'].get('in2_net','+3V3'),pts,prio=0,clear=0.25)
add_zone(b,pcbnew.F_Cu,'GND',pts,prio=0,clear=0.25)
add_zone(b,pcbnew.B_Cu,'GND',pts,prio=0,clear=0.25)
nv=post.stitch(b,'GND',R,C,pitch=cfg['pcb'].get('stitch_pitch',3.0)); print('stitch vias',nv)
fill(b)
print('silk refs',silk.place_refs(b,C,R))
ns=b.GetDesignSettings().m_NetSettings
tb=b.GetTitleBlock(); tb.SetTitle(cfg['title']); tb.SetRevision(cfg['rev']); tb.SetDate(cfg['date']); tb.SetCompany(cfg.get('company',''))
tb.SetComment(0,cfg.get('comment1','')); tb.SetComment(1,cfg.get('comment2',''))
out=f'{OUT}/{cfg["name"]}.kicad_pcb'
pcbnew.SaveBoard(out,b)
t=open(out).read().replace('"USB_DM"','"USB_DN"'); open(out,'w').write(t)
print('saved',out)
