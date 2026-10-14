import sch
def pinnames(D,comps=None):
    S=sch.symbols(D)
    comps=comps or sch.page(D)[0]
    m={}
    for c in comps:
        ref=c['attrs'].get('Designator')
        if not ref: continue
        part=S[c['attrs']['Symbol']]['parts'][c['partId']]
        for p in part['pins']: m[f"{ref}.{p['num']}"]=p['name']
    return m,S
