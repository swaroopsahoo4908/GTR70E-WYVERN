import math,json,uuid,re
MIL=0.0254
def mm(v): return round(v*MIL,4)
LAYER={1:'F.Cu',2:'B.Cu',3:'F.SilkS',4:'B.SilkS',5:'F.Mask',6:'B.Mask',7:'F.Paste',8:'B.Paste',13:'F.Fab',48:'F.Fab',49:'F.Fab',9:'F.Fab',10:'B.Fab',14:'Dwgs.User'}
def U(): return str(uuid.uuid4())
def P(x,y): return (mm(x),mm(-y))   # y-up mil -> kicad mm y-down
def arc_mid(p0,sweep,p1):
    # p0,p1 in y-up coords; sweep deg, positive = CCW in y-up
    (x0,y0),(x1,y1)=p0,p1
    a=math.radians(sweep)
    if abs(a)<1e-9: return None
    dx,dy=x1-x0,y1-y0; c=math.hypot(dx,dy)
    if c<1e-9: return None
    r=c/2/math.sin(abs(a)/2)
    mx,my=(x0+x1)/2,(y0+y1)/2
    # distance from chord mid to center
    h=math.sqrt(max(r*r-(c/2)**2,0))
    nx,ny=-dy/c,dx/c   # left normal (CCW side)
    # for CCW sweep <180 center is on left
    s=1 if a>0 else -1
    if abs(a)>math.pi: s=-s
    cx,cy=mx+s*nx*h,my+s*ny*h
    a0=math.atan2(y0-cy,x0-cx); am=a0+a/2
    return (cx+r*math.cos(am),cy+r*math.sin(am)),(cx,cy),r
def parse_path(path):
    """returns list of shapes: ('poly',[pts],closed) with arcs approximated; or ('circle',cx,cy,r); or ('rect',...)"""
    out=[]
    if not path: return out
    if isinstance(path[0],list):
        for sp in path: out+=parse_path(sp)
        return out
    if path[0]=='CIRCLE': return [('circle',path[1],path[2],path[3])]
    if path[0]=='R':
        x,y,w,h=path[1:5]; r=path[6] if len(path)>6 else 0
        # EasyEDA R: x,y top-left (y-up: top), w,h
        return [('poly',[(x,y),(x+w,y),(x+w,y-h),(x,y-h),(x,y)],True,[])]
    pts=[(path[0],path[1])]; i=2; mode='L'; segs=[]
    while i<len(path):
        t=path[i]
        if t in('L','ARC','C','CARC'): mode=t; i+=1; continue
        if mode=='L':
            p=(path[i],path[i+1]); segs.append(('L',pts[-1],p)); pts.append(p); i+=2
        elif mode in('ARC','CARC'):
            sw=path[i]; p=(path[i+1],path[i+2]); segs.append(('A',pts[-1],p,sw)); pts.append(p); i+=3
        elif mode=='C':
            c1=(path[i],path[i+1]);c2=(path[i+2],path[i+3]);p=(path[i+4],path[i+5])
            p0=pts[-1]
            for k in range(1,9):
                t_=k/8
                q=((1-t_)**3*p0[0]+3*(1-t_)**2*t_*c1[0]+3*(1-t_)*t_**2*c2[0]+t_**3*p[0],(1-t_)**3*p0[1]+3*(1-t_)**2*t_*c1[1]+3*(1-t_)*t_**2*c2[1]+t_**3*p[1])
                segs.append(('L',pts[-1],q)); pts.append(q)
            i+=6
        else: i+=1
    closed=len(pts)>2 and abs(pts[0][0]-pts[-1][0])<1e-6 and abs(pts[0][1]-pts[-1][1])<1e-6
    return [('path',segs,closed)]
def flatten(segs,n=12):
    pts=[]
    for s in segs:
        if not pts: pts.append(s[1])
        if s[0]=='L': pts.append(s[2])
        else:
            r=arc_mid(s[1],s[3],s[2])
            if not r: pts.append(s[2]); continue
            _,(cx,cy),rad=r
            a0=math.atan2(s[1][1]-cy,s[1][0]-cx); a=math.radians(s[3])
            k=max(2,int(abs(s[3])/10))
            for j in range(1,k+1): pts.append((cx+rad*math.cos(a0+a*j/k),cy+rad*math.sin(a0+a*j/k)))
    return pts
def gfx_items(kind,layer,shapes,width,fill,prefix='fp'):
    """emit s-expr strings for fp_ or gr_ items"""
    out=[];w=max(mm(width),0.05) if width else 0.12
    for s in shapes:
        if s[0]=='circle':
            cx,cy=P(s[1],s[2]); r=mm(s[3])
            out.append(f'({prefix}_circle (center {cx} {cy}) (end {round(cx+r,4)} {cy}) (stroke (width {0 if fill else w}) (type solid)) (fill {"yes" if fill else "no"}) (layer "{layer}") (uuid "{U()}"))')
        elif s[0]=='poly':
            pts=' '.join(f'(xy {P(*p)[0]} {P(*p)[1]})' for p in s[1])
            out.append(f'({prefix}_poly (pts {pts}) (stroke (width {w}) (type solid)) (fill {"yes" if fill else "no"}) (layer "{layer}") (uuid "{U()}"))')
        elif s[0]=='path':
            segs,closed=s[1],s[2]
            if fill and closed:
                pts=flatten(segs)
                if len(pts)>=3:
                    ps=' '.join(f'(xy {P(*p)[0]} {P(*p)[1]})' for p in pts)
                    out.append(f'({prefix}_poly (pts {ps}) (stroke (width 0) (type solid)) (fill yes) (layer "{layer}") (uuid "{U()}"))')
                continue
            for sg in segs:
                if sg[0]=='L':
                    a,b=P(*sg[1]),P(*sg[2])
                    if a==b: continue
                    out.append(f'({prefix}_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{U()}"))')
                else:
                    r=arc_mid(sg[1],sg[3],sg[2])
                    if not r:
                        a,b=P(*sg[1]),P(*sg[2])
                        out.append(f'({prefix}_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{U()}"))'); continue
                    m=r[0]
                    if abs(sg[3])>=359.9:
                        (cx,cy)=P(*r[1]); out.append(f'({prefix}_circle (center {cx} {cy}) (end {round(cx+mm(r[2]),4)} {cy}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))'); continue
                    a,mp,b=P(*sg[1]),P(*m),P(*sg[2])
                    out.append(f'({prefix}_arc (start {a[0]} {a[1]}) (mid {mp[0]} {mp[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{U()}"))')
    return out
def pad_sexpr(b):
    num=b['num']; x,y=P(b['centerX'],b['centerY']); ang=b.get('padAngle') or 0
    dp=b['defaultPad']; hole=b.get('hole'); lay=b['layerId']
    th=hole and (hole.get('width') or 0)>0
    smd_layers={1:'"F.Cu" "F.Paste" "F.Mask"',2:'"B.Cu" "B.Paste" "B.Mask"'}
    if th:
        typ='thru_hole' if b.get('plated',True) else 'np_thru_hole'
        layers='"*.Cu" "*.Mask"'
    else:
        typ='smd'; layers=smd_layers.get(lay,'"F.Cu" "F.Paste" "F.Mask"')
    pt=dp['padType']; extra=''
    if pt=='POLYGON':
        # custom pad relative to pad center, angle 0
        segs=parse_path(dp['path'])
        pts=flatten(segs[0][1]) if segs and segs[0][0]=='path' else []
        rel=' '.join(f'(xy {mm(px-b["centerX"])} {mm(-(py-b["centerY"]))})' for px,py in pts[:-1] if True)
        # anchor size: small
        xs=[mm(px-b['centerX']) for px,py in pts]; ys=[mm(py-b['centerY']) for px,py in pts]
        a=round(max(0.1,min(max(xs)-min(xs),max(ys)-min(ys))*0.5),3)
        shape='custom'; size=f'(size {a} {a})'
        extra=f'(options (clearance outline) (anchor rect)) (primitives (gr_poly (pts {rel}) (width 0) (fill yes)))'
        ang_s=0
    else:
        w,h=mm(dp['width']),mm(dp['height'])
        shape={'RECT':'rect','ELLIPSE':'circle','OVAL':'oval'}.get(pt,'rect')
        if pt=='RECT' and dp.get('radius'):
            shape='roundrect'; extra=f'(roundrect_rratio {round(min(0.5,dp["radius"]/100),3)})'
        if shape=='circle' and abs(w-h)>1e-3: shape='oval'
        size=f'(size {w} {h})'; ang_s=ang
    drill=''
    if th:
        hw,hh=mm(hole['width']),mm(hole['height'])
        if hole['holeType']=='SLOT' and abs(hw-hh)>1e-3:
            # orient slot along pad major axis
            L_,W_=max(hw,hh),min(hw,hh)
            if pt!='POLYGON' and mm(dp['height'])>mm(dp['width']): drill=f'(drill oval {W_} {L_})'
            else: drill=f'(drill oval {L_} {W_})'
        else: drill=f'(drill {hw})'
    at=f'(at {x} {y}{" "+str(ang_s) if ang_s else ""})'
    return f'(pad "{num}" {typ} {shape} {at} {size} {drill} (layers {layers}) {extra} (uuid "{U()}"))', (x,y)
def footprint(doc,name,lib='WYVERN'):
    L=doc['live']
    items=[];pads=[];bbox=[]
    for h,b in L:
        t=h['type']
        if t=='PAD':
            s,(x,y)=pad_sexpr(b); pads.append(s)
            dp=b['defaultPad']
            if dp.get('width'): 
                r=max(mm(dp['width']),mm(dp['height']))/2
                if b.get('padAngle') in (0,180,None,-180): bbox+= [(x-mm(dp['width'])/2,y-mm(dp['height'])/2),(x+mm(dp['width'])/2,y+mm(dp['height'])/2)]
                else: bbox+=[(x-r,y-r),(x+r,y+r)]
            else:
                for sh in parse_path(dp['path']):
                    if sh[0]=='path':
                        for p in flatten(sh[1]): bbox.append(P(*p))
        elif t in('POLY','FILL'):
            lay=b['layerId']
            if lay==12 and t=='FILL':
                for sh in parse_path(b['path']):
                    if sh[0]=='circle':
                        cx,cy=P(sh[1],sh[2]); d=round(2*mm(sh[3]),4)
                        pads.append(f'(pad "" np_thru_hole circle (at {cx} {cy}) (size {d} {d}) (drill {d}) (layers "*.Cu" "*.Mask") (uuid "{U()}"))')
                        bbox+=[(cx-d/2,cy-d/2),(cx+d/2,cy+d/2)]
                continue
            if lay not in LAYER: continue
            if lay in (1,2):  # copper graphics in footprint: keep as copper
                pass
            shapes=parse_path(b['path'])
            fill = (t=='FILL') and lay in (1,2,3,4,5,6,7,8)
            layer=LAYER[lay]
            if lay==49 and fill: layer='F.Fab'
            items+=gfx_items('fp',layer,shapes,b.get('width',5) if not fill else 0,fill)
            if lay==48:
                for sh in shapes:
                    if sh[0]=='path':
                        for p in flatten(sh[1]): bbox.append(P(*p))
                    elif sh[0]=='poly':
                        for p in sh[1]: bbox.append(P(*p))
                    elif sh[0]=='circle':
                        cx,cy=P(sh[1],sh[2]); r=mm(sh[3]); bbox+=[(cx-r,cy-r),(cx+r,cy+r)]
    if bbox:
        x0=min(p[0] for p in bbox)-0.25;x1=max(p[0] for p in bbox)+0.25
        y0=min(p[1] for p in bbox)-0.25;y1=max(p[1] for p in bbox)+0.25
        items.append(f'(fp_rect (start {round(x0,3)} {round(y0,3)}) (end {round(x1,3)} {round(y1,3)}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{U()}"))')
    else: x0=y0=-1;x1=y1=1
    smd=all(' smd ' in p for p in pads if 'np_thru' not in p)
    attr='smd' if smd else 'through_hole'
    head=f'''(footprint "{name}"
  (version 20241229) (generator "wyvern_epru2kicad") (generator_version "1.0")
  (layer "F.Cu")
  (property "Reference" "REF**" (at 0 {round(y0-0.8,3)} 0) (layer "F.SilkS") (uuid "{U()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Value" "{name}" (at 0 {round(y1+0.8,3)} 0) (layer "F.Fab") (uuid "{U()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1))))
  (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1))))
  (property "Description" "Converted from EasyEDA Pro footprint {name}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1))))
  (attr {attr})
  (fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{U()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
'''
    return head+'\n'.join('  '+s for s in items+pads)+'\n)\n'
def safe(n): return re.sub(r'[^A-Za-z0-9_.\-+]','_',n)
