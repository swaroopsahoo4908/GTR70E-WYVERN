"""JLCPCB fab + assembly package: Gerbers, Excellon drill, BOM (LCSC), CPL with rotation corrections."""
import sys,os,csv,re,json,subprocess,zipfile,collections,importlib
sys.path.insert(0,'/tmp/w/conv')
proj_dir,name,cfgmod=sys.argv[1],sys.argv[2],sys.argv[3]
cfg=importlib.import_module(cfgmod).cfg
pcb=f'{proj_dir}/{name}.kicad_pcb'; sch=f'{proj_dir}/{name}.kicad_sch'
J=f'{proj_dir}/jlcpcb'; G=f'{J}/gerber'; os.makedirs(G,exist_ok=True)
for f in os.listdir(G): os.remove(f'{G}/{f}')
run=lambda *a: subprocess.run(a,capture_output=True,text=True)
L='F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
r=run('kicad-cli','pcb','export','gerbers','-o',G+'/','-l',L,'--no-x2','--subtract-soldermask','--check-zones','--use-drill-file-origin',pcb); print(r.stdout[-300:],r.stderr[-300:])
r=run('kicad-cli','pcb','export','drill','-o',G+'/','--format','excellon','--excellon-separate-th','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-oval-format','alternate','--drill-origin','plot','--generate-map','--map-format','gerberx2',pcb); print(r.stdout[-200:])
with zipfile.ZipFile(f'{J}/{name}_gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(G)): z.write(f'{G}/{f}',f)
# ---------- position file
raw=f'{J}/_pos_raw.csv'
run('kicad-cli','pcb','export','pos','-o',raw,'--format','csv','--units','mm','--side','both','--use-drill-file-origin','--exclude-dnp',pcb)
# rotation corrections for footprints that are NOT EasyEDA/LCSC-native (KiCad library ones), from the
# JLCKicadTools rotation DB (matthewlai/JLCKicadTools cpl_rotations_db.csv)
CORR=[(r'^SOT-223',180),(r'^TestPoint',0),(r'^L_Wuerth_PMFI',0),(r'^L_Sunlord_SWPA',0)]
dnp=set(cfg.get('dnp',[]))
des=json.load(open(f'/tmp/w/out/{name.split("_")[-1]}/_design.json'))

rows=list(csv.DictReader(open(raw)))
cpl=[]
for rw in rows:
    ref=rw['Ref']
    if ref in dnp or ref.startswith('MH'): continue
    fpn=rw['Package']; rot=float(rw['Rot'])
    for pat,c in CORR:
        if re.search(pat,fpn): rot=rot+c; break
    rot=rot%360
    cpl.append(dict(Designator=ref,**{'Mid X':f"{float(rw['PosX']):.4f}mm",'Mid Y':f"{float(rw['PosY']):.4f}mm"},Layer='Top' if rw['Side']=='top' else 'Bottom',Rotation=f'{rot:.1f}'))
with open(f'{J}/{name}_CPL.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=['Designator','Mid X','Mid Y','Layer','Rotation']); w.writeheader(); w.writerows(cpl)
os.remove(raw)
# ---------- BOM grouped by LCSC
grp=collections.OrderedDict()
cplrefs={c['Designator'] for c in cpl}
for ref in sorted(des['parts'],key=lambda s:(re.sub(r'\d','',s),int(re.sub(r'\D','',s) or 0))):
    if ref in dnp: continue
    p=des['parts'][ref]; fpn=des['fp'][ref].split(':')[1]
    k=(p['LCSC'],fpn)
    grp.setdefault(k,[]).append(ref)
with open(f'{J}/{name}_BOM.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['Comment','Designator','Footprint','LCSC Part #','Manufacturer Part','Quantity'])
    for (lc,fpn),refs in grp.items():
        w.writerow([des['parts'][refs[0]]['value'],','.join(refs),fpn,lc,des['parts'][refs[0]]['MPN'],len(refs)])
missing=[r for refs in grp.values() for r in refs if r not in cplrefs]
print('BOM lines',len(grp),'parts',sum(len(v) for v in grp.values()),'CPL rows',len(cpl),'BOM refs missing from CPL',missing)
print('no LCSC:',[r for (lc,_),refs in grp.items() if not lc for r in refs])
