import sys,importlib;sys.path.insert(0,'/tmp/w/conv')
from route import *
cfg=importlib.import_module(sys.argv[1]).cfg
tag=cfg['name'].split('_')[-1]; OUT=f'/tmp/w/out/{tag}'
b=pcbnew.LoadBoard(f'{OUT}/stage_placed.kicad_pcb')
PLANE=cfg['pcb'].get('in1_plane',True)
b.SetLayerType(pcbnew.In1_Cu,pcbnew.LT_POWER if PLANE else pcbnew.LT_SIGNAL); b.SetLayerType(pcbnew.In2_Cu,pcbnew.LT_SIGNAL)
b.SetLayerName(pcbnew.In1_Cu,'In1.GND' if PLANE else 'In1.SIG_GND'); b.SetLayerName(pcbnew.In2_Cu,'In2.SIG_PWR')
bb=b.GetBoardEdgesBoundingBox(); R=pcbnew.ToMM(bb.GetWidth())/2
pts=circle_poly(100,100,R-0.5)
if PLANE: add_zone(b,pcbnew.In1_Cu,'GND',pts,prio=0,clear=0.2,thermal=True)
import fanout,gridroute,json,subprocess,re
pr=cfg['pcb'].get('preroute',[])
if pr:
    tmp=f'{OUT}/_pre.kicad_pcb'; pcbnew.SaveBoard(tmp,b)
    subprocess.run(['kicad-cli','pcb','drc','--format','json','-o',f'{OUT}/_pre.json',tmp],capture_output=True)
    d=json.load(open(f'{OUT}/_pre.json'))
    rr=gridroute.Router(b,(100,100),R,clr=0.18)
    import autoplace
    rr.fine_zones=[autoplace.rect_of(f) for f in b.Footprints() if f.GetReference() in cfg['pcb'].get('fine_refs',['U1'])]; rr.fine_clr=0.12
    ulist=[]
    for u in d.get('unconnected_items',[]):
        its=u['items']; net=re.search(r'\[([^\]]+)\]',its[0]['description']).group(1)
        if net in pr: ulist.append((pr.index(net),net,its))
    for _,net,its in sorted(ulist,key=lambda t:t[0]):
        if True:
            ok=rr.route(b.FindNet(net).GetNetCode(),(its[0]['pos']['x'],its[0]['pos']['y']),(its[1]['pos']['x'],its[1]['pos']['y']),margin=8,lock=True)
            print('preroute',net,ok,flush=True)
_pg=cfg['pcb'].get('preroute_geom')
if _pg:
    from pcbbuild import V as _V, MM as _MM
    for net,pts,w in _pg['tracks']:
        for a,c in zip(pts,pts[1:]):
            t=pcbnew.PCB_TRACK(b); t.SetStart(_V(*a)); t.SetEnd(_V(*c)); t.SetWidth(_MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(b.FindNet(net).GetNetCode()); t.SetLocked(True); b.Add(t)
    for net,x,y,d,dr in _pg['vias']:
        v=pcbnew.PCB_VIA(b); v.SetPosition(_V(x,y)); v.SetWidth(_MM(d)); v.SetDrill(_MM(dr)); v.SetNetCode(b.FindNet(net).GetNetCode()); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLocked(True); b.Add(v)
    print('preroute geom',len(_pg['tracks']),len(_pg['vias']))
print('EP vias',fanout.ep_vias(b,'GND'))
import qfnfan
for _r,_o in cfg['pcb'].get('qfn_fanout',{}).items(): print('qfn fanout',_r,qfnfan.fan(b,_r,exclude_pins=_o.get('exclude',())))
if PLANE: print('fanout GND',fanout.fanout(b,'GND',(100,100),R))
fill(b)
pcbnew.SaveBoard(f'{OUT}/stage_planes.kicad_pcb',b)
dsn=f'{OUT}/{tag.lower()}.dsn'
print('dsn',pcbnew.ExportSpecctraDSN(b,dsn),R)
s=open(dsn).read()
i=s.index('(class HighCurrent'); j=s.index('(use_via',i)
s=s[:j]+'(use_layer F.Cu B.Cu)\n        '+s[j:]
open(dsn,'w').write(s)
