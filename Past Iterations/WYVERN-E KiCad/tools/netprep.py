import tel,collections
def from_tel(cfg):
    parts,nets=tel.parse(cfg['tel'])
    nop={}
    for n,ps in nets.items():
        nm=cfg['netnames'].get(n,n.replace('$','N'))
        for p in ps: nop[p]=nm
    for p,n in cfg.get('pin_fixes',[]): nop[p]=None if n=='NC' else n
    return parts,nop
