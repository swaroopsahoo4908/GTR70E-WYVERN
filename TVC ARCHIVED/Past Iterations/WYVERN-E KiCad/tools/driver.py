import sys,os,json,collections,importlib
sys.path.insert(0,'/tmp/w/conv')
import epru,sch,fp,schwrite,symlib,netprep
def footprint_lib(D,libdir):
    os.makedirs(libdir,exist_ok=True)
    byuuid={};bytitle={};seen={}
    for d in D:
        if d['head']['docType']!='FOOTPRINT': continue
        epru.resolve(d)
        title=[b for h,b in d['live'] if h['type']=='META'][0]['title']
        nm=fp.safe(title)
        txt=fp.footprint(d,nm)
        # dedupe by content signature (pads only)
        sig=''.join(sorted(l.split('(uuid')[0] for l in txt.split('\n') if '(pad ' in l))
        if nm in seen and seen[nm]!=sig:
            i=2
            while f'{nm}_v{i}' in seen and seen[f'{nm}_v{i}']!=sig: i+=1
            nm=f'{nm}_v{i}'; txt=fp.footprint(d,nm)
        seen[nm]=sig
        open(f'{libdir}/{nm}.kicad_mod','w').write(txt)
        byuuid[d['head']['uuid']]=nm; byuuid[d['head']['uuid'].split('_')[-1]]=nm
        bytitle.setdefault(title,nm)
    return byuuid,bytitle
def pcb_fp_of_ref(D,byuuid,bytitle):
    pcb=[d for d in D if d['head']['docType']=='PCB'][0]; epru.resolve(pcb)
    attrs=collections.defaultdict(dict)
    for h,b in epru.live(pcb,'ATTR'): attrs[b['parentId']][b['key']]=b['value']
    out={}
    for h,b in epru.live(pcb,'COMPONENT'):
        a=attrs[h['id']]; ref=a.get('Designator'); v=a.get('Footprint')
        if not ref: continue
        out[ref]=byuuid.get(v) or byuuid.get((v or '').split('_')[-1]) or bytitle.get(v)
    return out
