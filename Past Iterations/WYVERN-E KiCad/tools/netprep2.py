import geomnet,pinmap,collections,re
GENERIC=re.compile(r'^(\d+|[A-Z]?\d+|PIN\d+|GND|VSS|VDD|VCC|NC|RES|Res|EP|EH|A|K|S|D|G|\+|-|CD|DGND|AGND|PGND)$')
def auto_names(groups,pm):
    names={}
    used=collections.Counter()
    for gi,g in enumerate(groups):
        ps=sorted(g)
        cand=[]
        for p in ps:
            ref,num=p.split('.',1); nm=pm.get(p) or ''
            if not ref.startswith(('U','CARD','USBC','X')) or GENERIC.match(nm): continue
            nm=re.sub(r'[^A-Za-z0-9_+\-]','_',nm.split('(')[0].split('/')[0]).strip('_')
            if not nm: continue
            score=0 if not ref=='U1' else 1
            if nm.startswith('GPIO'): score+=2
            cand.append((score,ref,nm))
        if cand:
            cand.sort(); s,ref,nm=cand[0]
            name=nm if ref=='U1' else f'{ref}_{nm}'
        else:
            name='Net-'+ps[0].replace('.','-Pad')
        used[name]+=1
        if used[name]>1: name=f'{name}_{used[name]}'
        names[gi]=name
    return names
def from_geom(D,cfg):
    G,pins,S,comps,wl=geomnet.build(D)
    pm,_=pinmap.pinnames(D,comps)
    G=[g for g in G]
    names=auto_names(G,pm)
    orig={}
    for gi,g in enumerate(G):
        for p in g: orig[p]=names[gi] if len(g)>1 else None
    # manual names by member pin
    ren={}
    for pin,nm in cfg['netnames_by_pin'].items():
        if orig.get(pin): ren[orig[pin]]=nm
    rm=set(cfg.get('removed',[]))
    nop={p:(ren.get(n,n) if n else None) for p,n in orig.items() if p.split('.',1)[0] not in rm}
    base=dict(nop)
    for pin,tgt in cfg.get('pin_fixes',[]):
        if tgt.startswith('@'): tgt=base.get(tgt[1:]) or nop[tgt[1:]]
        nop[pin]=None if tgt=='NC' else tgt
    nop={p:n for p,n in nop.items() if n}
    return nop,pm
