import sys,json;sys.path.insert(0,'/tmp/w/conv')
import pcbnew,epru,pcbbuild as PB,importlib
from pcbbuild import V,MM
cfg=importlib.import_module(sys.argv[1]).cfg
tag=cfg['name'].split('_')[-1]; OUT=f'/tmp/w/out/{tag}'; LIB='WYVERN_'+tag
des=json.load(open(f'{OUT}/_design.json'))
D=epru.load(cfg['epru'])
for d in D: epru.resolve(d)
pl,pcb=PB.comp_placement(D)
circ,lines,holes,strings=PB.outline_holes(pcb)
cx,cy,r=circ[0]; off=(100-cx,100-cy)
b=pcbnew.BOARD()
PB.setup_board(b,cfg['pcb'])
PB.add_outline(b,circ,lines,off)
for i,h in enumerate(holes): PB.add_hole(b,h[0]+off[0],h[1]+off[1],h[2],ref=f'MH{i+1}')
nets={}
def net(n):
    if n not in nets:
        ni=pcbnew.NETINFO_ITEM(b,n); b.Add(ni); nets[n]=ni
    return nets[n]
pinnet=des['nets']
place=dict(pl); place.update(cfg['pcb'].get('place',{})); place.update(cfg['pcb'].get('fixed',{}))
missing=[]
for ref,fpn in des['fp'].items():
    lib,name=fpn.split(':')
    f=pcbnew.FootprintLoad(f'{OUT}/{lib}.pretty',name)
    f.SetReference(ref); f.SetValue(des['parts'][ref]['value'][:40])
    f.SetFPID(pcbnew.LIB_ID(lib,name))
    p=place.get(ref)
    if not p: missing.append(ref); p=dict(x=cx+r+10,y=cy,angle=0,side='F')
    f.SetPosition(V(p['x'],p['y']) if p.get('abs') else V(p['x']+off[0],p['y']+off[1]))
    f.SetOrientationDegrees(p['angle'])
    for pad in f.Pads():
        k=f'{ref}.{pad.GetNumber()}'
        if pinnet.get(k): pad.SetNet(net(pinnet[k]))
    for k in ('LCSC','MPN'):
        if des['parts'][ref].get(k):
            f.SetField(k,des["parts"][ref][k]); fl=f.GetField(k); fl.SetVisible(False); fl.SetLayer(pcbnew.F_Fab)
    b.Add(f)
    if p.get('side')=='B': f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
print('unplaced',missing)
import autoplace
byref={f.GetReference():f for f in b.Footprints()}
if cfg['pcb'].get('floorplan'):
    import floorplan
    for l in floorplan.run(b,cfg,byref,r): print(l)
for ref,anc,sides in cfg['pcb']['autoplace']:
    f=byref[ref]
    axy=anc if isinstance(anc,tuple) else (pcbnew.ToMM(byref[anc].GetPosition().x),pcbnew.ToMM(byref[anc].GetPosition().y))
    res=autoplace.place(b,f,axy,sides,center=(100,100),R=r,keepout=cfg['pcb'].get('keepout',{}),margin=cfg['pcb'].get('ap_margin',0.35))
    print(ref,res)
    if res is None: raise SystemExit('cannot place '+ref)

for s in strings:
    t=pcbnew.PCB_TEXT(b); t.SetText(s['text']); t.SetLayer(pcbnew.F_SilkS if s['layer'] in (1,3) else pcbnew.B_SilkS)
    t.SetTextSize(V(s['size']*0.8,s['size']*0.8)); t.SetTextThickness(MM(max(0.15,s['size']*0.1)))
    t.SetPosition(V(s['x']+off[0],s['y']+off[1])); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_BOTTOM)
    if s['layer'] in (2,4): t.SetMirrored(True)
    b.Add(t)
for f in b.Footprints():
    f.Value().SetVisible(False) if False else None
    f.Value().SetLayer(pcbnew.B_Fab if f.GetLayer()==pcbnew.B_Cu else pcbnew.F_Fab)
    f.Reference().SetTextSize(V(0.8,0.8)); f.Reference().SetTextThickness(MM(0.12))
lg=cfg['pcb'].get('legacy')
if lg:
    import legacy
    lm={1:pcbnew.F_Cu,2:pcbnew.B_Cu,15:pcbnew.In1_Cu,16:pcbnew.In2_Cu}
    print('legacy',legacy.legacy_copper(b,D,des,off,set(cfg.get('removed',[])),{k:lm[k] for k in lg['layers']},(),exclude=set(cfg['pcb'].get('preroute',[]))))
pcbnew.SaveBoard(f'{OUT}/stage_placed.kicad_pcb',b)
