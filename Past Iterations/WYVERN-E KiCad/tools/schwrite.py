import math,uuid,collections,sch,geomnet,symlib
from symlib import U,esc
S_=0.254
def fmt(v): return ('%g'%round(v,4))
def build_sch(D,cfg,net_of_pin,parts_final,out_path,lib_prefix,fp_of_ref,proj):
    """net_of_pin: {'U1.5':'GND'}; parts_final: {ref:{value,..}}"""
    S=sch.symbols(D); comps,wl,_=sch.page(D)
    removed=set(cfg.get('removed',[]))
    # component list
    C=[]
    for c in comps:
        ref=c['attrs'].get('Designator')
        if not ref or ref in removed or ref not in parts_final: continue
        C.append(dict(ref=ref,sym=c['attrs']['Symbol'],partId=c['partId'],x=c['x'],y=c['y'],rotation=c['rotation'],isMirror=c['isMirror'],attrs=c['attrs']))
    byref={c['ref']:c for c in C}
    for e in cfg.get('extra',[]):
        if 'part' in e:
            key='custom_'+e['ref']; S[key]={'parts':{e['part_name']:e['part']},'attrs':{},'title':e['part_name']}
            C.append(dict(ref=e['ref'],sym=key,partId=e['part_name'],x=e['sch'][0],y=e['sch'][1],rotation=0,isMirror=False,attrs={}))
            continue
        src=byref[e['sym_from']] if e['sym_from'] in byref else None
        C.append(dict(ref=e['ref'],sym=src['sym'],partId=src['partId'],x=e['sch'][0],y=e['sch'][1],rotation=e['sch'][2] if len(e['sch'])>2 else 0,isMirror=False,attrs=dict(src['attrs'])))
    # symbol defs
    symdefs={}; symname={}
    for c in C:
        key=(c['sym'],c['partId'])
        if key not in symname:
            nm=symlib.safe(c['partId'].rsplit('.',1)[0])
            base=nm;i=2
            while nm in symdefs and symdefs[nm][0]!=key: nm=f'{base}_{i}';i+=1
            part=S[c['sym']]['parts'][c['partId']]
            two=len(part['pins'])==2 and c['ref'][0] in 'RCLFD'
            symdefs[nm]=(key,symlib.symbol_def(nm,part,''.join(ch for ch in c['ref'] if ch.isalpha()) or 'U',two_pin_passive=two))
            symname[key]=nm
        c['symname']=symname[key]
    # pins
    allpins=[]
    for c in C:
        part=S[c['sym']]['parts'][c['partId']]
        for p in part['pins']:
            ax,ay=sch.xform(p['x'],p['y'],c)
            # pin direction (outward) for label orientation: pin rot is direction into body
            r=(p['rot']+c['rotation'])%360
            if c['isMirror'] and p['rot'] in (0,180): r=(180-p['rot']+c['rotation'])%360
            allpins.append(dict(ref=c['ref'],num=p['num'],x=ax,y=ay,rot=r,key=f"{c['ref']}.{p['num']}"))
    # geometric groups from wires (only original comps)
    parent={}
    def F(a):
        while parent.setdefault(a,a)!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def UN(a,b): parent[F(a)]=F(b)
    segs=[]
    for wid,w in wl.items():
        for i,s in enumerate(w['segs']): segs.append(((wid,i),s)); UN(('s',wid,i),('w',wid))
    for k1,s1 in segs:
        for k2,s2 in segs:
            if k1>=k2: continue
            if any(geomnet.onseg(p,s2) for p in [(s1[0],s1[1]),(s1[2],s1[3])]) or any(geomnet.onseg(p,s1) for p in [(s2[0],s2[1]),(s2[2],s2[3])]): UN(('s',)+k1,('s',)+k2)
    pinseg=collections.defaultdict(list)
    for p in allpins:
        for k,s in segs:
            if geomnet.onseg((p['x'],p['y']),s): UN(('p',p['key']),('s',)+k); pinseg[p['key']].append(k)
    # also pins of removed comps
    removed_pts=[]
    for c in comps:
        ref=c['attrs'].get('Designator')
        if ref in removed:
            for p in S[c['attrs']['Symbol']]['parts'][c['partId']]['pins']:
                removed_pts.append(sch.xform(p['x'],p['y'],c))
    groups=collections.defaultdict(lambda:{'pins':[],'segs':[]})
    for p in allpins:
        if pinseg[p['key']]: groups[F(('p',p['key']))]['pins'].append(p)
    for k,s in segs: groups[F(('s',)+k)]['segs'].append(s)
    wires=[];labels=[];junctions=set();nocon=[]
    covered=set()
    for g in groups.values():
        if not g['pins']: continue
        nets={net_of_pin.get(p['key']) for p in g['pins']}
        touches_removed=any(any(geomnet.onseg(pt,s) for s in g['segs']) for pt in removed_pts)
        if len(nets)==1 and None not in nets and not touches_removed:
            net=nets.pop()
            # split segments at interior points
            pts=[(p['x'],p['y']) for p in g['pins']]+[(s[0],s[1]) for s in g['segs']]+[(s[2],s[3]) for s in g['segs']]
            for s in g['segs']:
                cut=[(s[0],s[1]),(s[2],s[3])]+[q for q in pts if geomnet.onseg(q,s)]
                cut=sorted(set((round(a,3),round(b,3)) for a,b in cut),key=lambda q:(q[0]-s[0])**2+(q[1]-s[1])**2)
                for a,b in zip(cut,cut[1:]):
                    if a!=b: wires.append((a,b))
            for p in g['pins']: covered.add(p['key'])
            lp=sorted(g['pins'],key=lambda p:(p['ref'],p['num']))[0]
            labels.append((net,lp))
        # invalid groups: drop
    # prune dangling stubs
    pinpts0={(round(p['x'],3),round(p['y'],3)) for p in allpins}
    changed=True
    while changed:
        changed=False
        for i,(a,b) in enumerate(wires):
            for e in (a,b):
                if e in pinpts0: continue
                if any(j!=i and (e==c or e==d or geomnet.onseg(e,(c[0],c[1],d[0],d[1]))) for j,(c,d) in enumerate(wires)): continue
                wires.pop(i); changed=True; break
            if changed: break
    # junctions: points where >=3 wire ends meet, or wire end + pin + another wire
    endc=collections.Counter()
    for a,b in wires: endc[a]+=1; endc[b]+=1
    pinpts={(round(p['x'],3),round(p['y'],3)) for p in allpins}
    for pt,n in endc.items():
        if n>=3 or (n>=2 and pt in pinpts): junctions.add(pt)
    # remaining pins
    netsize=collections.Counter(net_of_pin.values())
    for p in allpins:
        if p['key'] in covered: continue
        n=net_of_pin.get(p['key'])
        if n is None or netsize[n]<2: nocon.append(p)
        else: labels.append((n,p))
    # page coords
    xs=[p['x'] for p in allpins]; ys=[p['y'] for p in allpins]
    minx,maxx,miny,maxy=min(xs),max(xs),min(ys),max(ys)
    W=(maxx-minx)*S_+80; Hh=(maxy-miny)*S_+80
    paper='A2' if W<=594 and Hh<=420 else ('A1' if W<=841 and Hh<=594 else 'A0')
    ox=40-minx*S_; oy=40+maxy*S_
    oy=round(oy/1.27)*1.27; ox=round(ox/1.27)*1.27
    X=lambda x: ox+x*S_; Y=lambda y: oy-y*S_
    root=U()
    o=[]
    o.append(f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid "{root}") (paper "{paper}")')
    o.append(f'(title_block (title "{esc(cfg["title"])}") (date "{cfg["date"]}") (rev "{cfg["rev"]}") (company "{esc(cfg.get("company",""))}") (comment 1 "{esc(cfg.get("comment1",""))}") (comment 2 "{esc(cfg.get("comment2",""))}"))')
    o.append('(lib_symbols '+'\n'.join(d.replace(f'(symbol "{n}"',f'(symbol "{lib_prefix}:{n}"',1) for n,(k,d) in symdefs.items())+')')
    for a,b in wires:
        o.append(f'(wire (pts (xy {fmt(X(a[0]))} {fmt(Y(a[1]))}) (xy {fmt(X(b[0]))} {fmt(Y(b[1]))})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    for j in junctions:
        o.append(f'(junction (at {fmt(X(j[0]))} {fmt(Y(j[1]))}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
    for p in nocon:
        o.append(f'(no_connect (at {fmt(X(p["x"]))} {fmt(Y(p["y"]))}) (uuid "{U()}"))')
    for net,p in labels:
        # label angle: pin rot = direction from endpoint into body; label goes opposite
        ang={0:180,180:0,90:270,270:90}[int(p['rot'])%360]
        just='right' if ang in (180,270) else 'left'
        o.append(f'(global_label "{esc(net)}" (shape passive) (at {fmt(X(p["x"]))} {fmt(Y(p["y"]))} {ang}) (fields_autoplaced yes) (effects (font (size 1.016 1.016)) (justify {just})) (uuid "{U()}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {fmt(X(p["x"]))} {fmt(Y(p["y"]))} 0) (effects (font (size 1.016 1.016)) (hide yes))))')
    for c in C:
        pf=parts_final[c['ref']]
        x,y=X(c['x']),Y(c['y'])
        part=S[c['sym']]['parts'][c['partId']]
        bb=part.get('bbox') or [-10,-10,10,10]
        top=max(bb[1],bb[3]); bot=min(bb[1],bb[3]); right=max(bb[0],bb[2])
        props=[('Reference',c['ref'],(x+right*S_*0+0, y-(top+4)*S_),False),('Value',pf.get('value',''),(x,y-(bot-4)*S_),False),
               ('Footprint',fp_of_ref.get(c['ref'],''),(x,y),True),('Datasheet',pf.get('datasheet','') or '',(x,y),True),
               ('Description',pf.get('description','') or '',(x,y),True)]
        for k in ('LCSC','MPN','Manufacturer'):
            if pf.get(k): props.append((k,pf[k],(x,y),True))
        mir=' (mirror y)' if c['isMirror'] else ''
        o.append(f'(symbol (lib_id "{lib_prefix}:{c["symname"]}") (at {fmt(x)} {fmt(y)} {int(c["rotation"])%360}){mir} (unit 1) (exclude_from_sim no) (in_bom {"no" if c["ref"] in cfg.get("dnp",[]) else "yes"}) (on_board yes) (dnp {"yes" if c["ref"] in cfg.get("dnp",[]) else "no"}) (uuid "{U()}")')
        for k,v,(px,py),hid in props:
            o.append(f'  (property "{k}" "{esc(v)}" (at {fmt(px)} {fmt(py)} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hid else ""}))')
        for p in part['pins']: o.append(f'  (pin "{esc(p["num"])}" (uuid "{U()}"))')
        o.append(f'  (instances (project "{proj}" (path "/{root}" (reference "{c["ref"]}") (unit 1)))))')
    o.append(f'(sheet_instances (path "/" (page "1"))))')
    open(out_path,'w').write('\n'.join(o))
    lib='(kicad_symbol_lib (version 20231120) (generator "wyvern_epru2kicad")\n'+'\n'.join(d for n,(k,d) in symdefs.items())+'\n)\n'
    return lib,len(wires),len(labels),len(nocon)
