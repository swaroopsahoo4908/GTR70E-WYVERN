import epru,collections,math,json
def symbols(D):
    S={}
    for d in D:
        if d['head']['docType']!='SYMBOL': continue
        L=d.get('live') or epru.resolve(d)
        parts=collections.OrderedDict()
        attrs=collections.defaultdict(dict)
        for h,b in L:
            if h['type']=='ATTR': attrs[b['parentId']][b['key']]=b['value']
        for h,b in L:
            if h['type']=='PART': parts[h['id']]={'bbox':b.get('BBOX'),'pins':[],'gfx':[]}
        for h,b in L:
            if h['type'] in('META','CANVAS','PART','ATTR','ELE_PLACEHOLDER'): continue
            pid=b.get('partId') if isinstance(b,dict) else None
            if pid not in parts: continue
            if h['type']=='PIN':
                a=attrs[h['id']]
                parts[pid]['pins'].append(dict(x=b['x'],y=b['y'],len=b['length'],rot=b['rotation'],num=a.get('Pin Number'),name=a.get('Pin Name'),type=a.get('Pin Type'),shape=b.get('pinShape'),display=b.get('display',True)))
            else: parts[pid]['gfx'].append((h['type'],b))
        S[d['head']['uuid'].split('_')[-1]]={'parts':parts,'attrs':attrs[''],'title':[b for h,b in L if h['type']=='META'][0].get('title')}
    return S
def xform(px,py,c):
    # component rotation (deg CCW) + mirror, symbol y-up, page y-up
    x,y=px,py
    if c['isMirror']: x=-x
    r=math.radians(c['rotation'])
    xr=x*math.cos(r)-y*math.sin(r); yr=x*math.sin(r)+y*math.cos(r)
    return (round(c['x']+xr,3),round(c['y']+yr,3))
def page(D):
    sp=[d for d in D if d['head']['docType']=='SCH_PAGE'][0]
    L=sp.get('live') or epru.resolve(sp)
    attrs=collections.defaultdict(dict); attrrec=collections.defaultdict(dict)
    for h,b in L:
        if h['type']=='ATTR': attrs[b['parentId']][b['key']]=b['value']; attrrec[b['parentId']][b['key']]=b
    comps=[]
    for h,b in L:
        if h['type']=='COMPONENT':
            c=dict(b); c['id']=h['id']; c['attrs']=attrs[h['id']]; c['attrrec']=attrrec[h['id']]; comps.append(c)
    wires=collections.defaultdict(list)
    for h,b in L:
        if h['type']=='LINE' and b.get('lineGroup'):
            wires[b['lineGroup']].append((b['startX'],b['startY'],b['endX'],b['endY']))
    wl={}
    for h,b in L:
        if h['type']=='WIRE': wl[h['id']]={'segs':wires.get(h['id'],[]),'net':attrs[h['id']].get('NET',''),'netrec':attrrec[h['id']].get('NET')}
    other=[(h,b) for h,b in L if h['type']=='LINE' and not b.get('lineGroup')]
    return comps,wl,other
