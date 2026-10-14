import sys;sys.path.insert(0,'/tmp/w/conv')
from driver import *
import netprep,netprep2,shutil,importlib
STD={'L_Sunlord_SWPA6045S':'Inductor_SMD','L_Wuerth_PMFI-201610':'Inductor_SMD','Fuse_2920_7451Metric':'Fuse','SOT-223-3_TabPin2':'Package_TO_SOT_SMD','TestPoint_Pad_D1.5mm':'TestPoint'}
def run(cfgmod,mode):
    cfg=importlib.import_module(cfgmod).cfg
    OUT=f'/tmp/w/out/{cfg["name"].split("_")[-1]}'; os.makedirs(OUT,exist_ok=True)
    LIB='WYVERN_'+cfg['name'].split('_')[-1]
    D=epru.load(cfg['epru'])
    for d in D: epru.resolve(d)
    byuuid,bytitle=footprint_lib(D,f'{OUT}/{LIB}.pretty')
    for n,l in STD.items(): shutil.copy(f'/usr/share/kicad/footprints/{l}.pretty/{n}.kicad_mod',f'{OUT}/{LIB}.pretty/')
    pfp=pcb_fp_of_ref(D,byuuid,bytitle)
    comps=sch.page(D)[0]
    import devattr
    DA=devattr.dev_attrs(D)
    cattr={}
    for c in comps:
        r=c['attrs'].get('Designator')
        if not r: continue
        a=dict(DA.get(c['attrs'].get('Device'),{}))
        a.update({k:v for k,v in c['attrs'].items() if v is not None})
        cattr[r]=a
    ex={e['ref']:e for e in cfg['extra']}
    if mode=='tel':
        tparts,nop=netprep.from_tel(cfg)
        for r in ex:
            if r not in tparts: tparts[r]={'val':cfg.get('values',{}).get(r,''),'fp':None,'dev':''}
    else:
        nop,pm=netprep2.from_geom(D,cfg)
        tparts={r:{'val':cattr[r].get('Value') or '','fp':None,'dev':cattr[r].get('Name') or ''} for r in cattr}
        for r in ex: tparts[r]={'val':cfg.get('values',{}).get(r,''),'fp':None,'dev':''}
    parts_final={};fp_of_ref={}
    rmv=set(cfg.get('removed',[]))-set(ex)
    for ref,tp in tparts.items():
        if ref in rmv: continue
        a=cattr.get(ref) or cattr.get(ex.get(ref,{}).get('sym_from'),{})
        val=cfg.get('values',{}).get(ref) or tp['val']
        mpn=ex[ref]['mpn'] if ref in ex else a.get('Manufacturer Part') or ''
        if not val or '{' in val: val=mpn or a.get('Name') or tp['dev']
        parts_final[ref]=dict(value=val,MPN=mpn,LCSC=(ex[ref].get('lcsc') if ref in ex else a.get('Supplier Part')) or '',Manufacturer='' if ref in ex else a.get('Manufacturer',''),datasheet='' if ref in ex else (a.get('Datasheet') or ''),description='' if ref in ex else (a.get('Description') or ''))
        bo=cfg.get('bom',{}).get(ref)
        if bo:
            pf=parts_final[ref]
            if bo.get('value'): pf['value']=bo['value']
            if 'lcsc' in bo: pf['LCSC']=bo['lcsc']
            if bo.get('mpn'): pf['MPN']=bo['mpn']
            if bo.get('mfr') is not None: pf['Manufacturer']=bo['mfr']
        fpn=cfg['fp_override'].get(ref) or pfp.get(ref) or bytitle.get(tp['fp'])
        if fpn is None: print('NO FP',ref,tp['fp'])
        fp_of_ref[ref]=f'{LIB}:{fpn}'
    import jlc
    for ref,pf in parts_final.items():
        if pf.get('LCSC'):
            x=jlc.lookup(pf['LCSC'])
            if x:
                pf['Manufacturer']=x['brand'] or ''; pf['datasheet']=f"https://www.lcsc.com/product-detail/{pf['LCSC']}.html"
                pf['description']=(x['desc'] or '').replace(' ROHS','')[:200]; pf['MPN']=x['model'] or pf.get('MPN','')
    json.dump(dict(parts=parts_final,fp=fp_of_ref,nets=nop),open(f'{OUT}/_design.json','w'),indent=1)
    lib,nw,nl,nn=schwrite.build_sch(D,cfg,nop,parts_final,f'{OUT}/{cfg["name"]}.kicad_sch',LIB,fp_of_ref,cfg['name'])
    open(f'{OUT}/{LIB}.kicad_sym','w').write(lib)
    print('wires',nw,'labels',nl,'nc',nn)
    open(f'{OUT}/sym-lib-table','w').write(f'(sym_lib_table (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr "WYVERN converted symbols"))\n)\n')
    open(f'{OUT}/fp-lib-table','w').write(f'(fp_lib_table (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")(options "")(descr "WYVERN converted footprints"))\n)\n')
    if not os.path.exists(f'{OUT}/{cfg["name"]}.kicad_pro'):
        open(f'{OUT}/{cfg["name"]}.kicad_pro','w').write(json.dumps({"meta":{"filename":cfg["name"]+".kicad_pro","version":3}}))
    return OUT,cfg
if __name__=='__main__':
    OUT,cfg=run(sys.argv[1],sys.argv[2])
    os.system(f'cd {OUT} && kicad-cli sch upgrade {cfg["name"]}.kicad_sch >/dev/null 2>&1; kicad-cli sch erc -o erc.rpt {cfg["name"]}.kicad_sch 2>&1 | grep -v assert; grep "^\\[" erc.rpt | sed "s/\\].*//" | sort | uniq -c; kicad-cli sch export netlist --format kicadsexpr -o net.net {cfg["name"]}.kicad_sch >/dev/null 2>&1; python3 /tmp/w/conv/cmpnet.py net.net _design.json')
