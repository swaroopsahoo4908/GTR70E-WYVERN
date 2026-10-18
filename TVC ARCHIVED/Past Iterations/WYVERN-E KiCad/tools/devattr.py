import sys;sys.path.insert(0,'/tmp/w/conv')
import epru,sch,importlib,json
def dev_attrs(D):
    out={}
    for d in D:
        if d['head']['docType']!='DEVICE': continue
        L=epru.resolve(d)
        a={}
        for h,b in L:
            if h['type']=='ATTR' and isinstance(b,dict): a[b['key']]=b['value']
            elif isinstance(b,dict) and 'attributes' in b: a.update(b['attributes'])
        out[d['head']['uuid'].split('_')[-1]]=a
    return out
if __name__=='__main__':
    cfg=importlib.import_module(sys.argv[1]).cfg
    D=epru.load(cfg['epru'])
    for d in D: epru.resolve(d)
    DA=dev_attrs(D)
    comps=sch.page(D)[0]
    res={}
    for c in comps:
        r=c['attrs'].get('Designator')
        if not r: continue
        a=dict(DA.get(c['attrs'].get('Device'),{}))
        for k,v in c['attrs'].items():
            if v is not None: a[k]=v
        res[r]=a
    json.dump(res,open(sys.argv[2],'w'),indent=1)
    for r in sorted(res, key=lambda s:(s.rstrip('0123456789'),int(''.join(ch for ch in s if ch.isdigit()) or 0))):
        a=res[r]; print(r,'|',a.get('Value'),'|',a.get('Manufacturer Part'),'|',a.get('Supplier Part'),'|',a.get('Supplier Footprint') or a.get('Footprint'))
