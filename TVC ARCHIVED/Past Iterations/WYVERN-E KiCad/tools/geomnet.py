import sch,collections
def onseg(p,s,eps=0.01):
    x,y=p;x1,y1,x2,y2=s
    if min(x1,x2)-eps<=x<=max(x1,x2)+eps and min(y1,y2)-eps<=y<=max(y1,y2)+eps:
        return abs((x2-x1)*(y-y1)-(y2-y1)*(x-x1))<eps*max(1,abs(x2-x1)+abs(y2-y1))
    return False
def build(D):
    S=sch.symbols(D); comps,wl,_=sch.page(D)
    pins=[]  # (ref,num,(x,y))
    for c in comps:
        ref=c['attrs'].get('Designator')
        if not ref: continue
        part=S[c['attrs']['Symbol']]['parts'][c['partId']]
        for p in part['pins']:
            pins.append((ref,p['num'],sch.xform(p['x'],p['y'],c)))
    parent={}
    def f(a):
        while parent.setdefault(a,a)!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def u(a,b): parent[f(a)]=f(b)
    segs=[]
    for wid,w in wl.items():
        for i,s in enumerate(w['segs']):
            segs.append(((wid,i),s)); u(('w',wid),('s',wid,i))
            u(('s',wid,i),('w',wid))
    # segment-segment endpoint connections
    for (k1,s1) in segs:
        for (k2,s2) in segs:
            if k1>=k2: continue
            for p in [(s1[0],s1[1]),(s1[2],s1[3])]:
                if onseg(p,s2): u(('s',)+k1,('s',)+k2)
            for p in [(s2[0],s2[1]),(s2[2],s2[3])]:
                if onseg(p,s1): u(('s',)+k1,('s',)+k2)
    for ref,num,pt in pins:
        u(('p',ref,num),('p',ref,num))
        for k,s in segs:
            if onseg(pt,s): u(('p',ref,num),('s',)+k)
    # pin-pin touching
    bypt=collections.defaultdict(list)
    for ref,num,pt in pins: bypt[(round(pt[0],2),round(pt[1],2))].append((ref,num))
    for v in bypt.values():
        for a in v[1:]: u(('p',)+v[0],('p',)+a)
    # named nets
    named=collections.defaultdict(list)
    for wid,w in wl.items():
        if w['net']: named[w['net']].append(('w',wid))
    for v in named.values():
        for a in v[1:]: u(v[0],a)
    groups=collections.defaultdict(set)
    for ref,num,pt in pins: groups[f(('p',ref,num))].add(f'{ref}.{num}')
    return [g for g in groups.values()], pins, S, comps, wl
