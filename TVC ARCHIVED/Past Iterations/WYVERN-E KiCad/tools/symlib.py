import math,uuid,re
S_=0.254
def U(): return str(uuid.uuid4())
def f(v): 
    v=round(v*S_,4); return ('%g'%v)
def esc(s): return (s or '').replace('\\','\\\\').replace('"','\\"')
def pin_type(t):
    return {'BI':'bidirectional'}.get(t,'passive')
def symbol_def(name,part,refprefix,two_pin_passive=False,hide_names=None):
    pins=part['pins']
    numeric=all((p['name'] or '')==(p['num'] or '') or (p['name'] or '').isdigit() for p in pins)
    hide_names = numeric if hide_names is None else hide_names
    hide_nums = two_pin_passive
    g=[]
    for t,b in part['gfx']:
        if t=='RECT':
            g.append(f'(rectangle (start {f(b["dotX1"])} {f(b["dotY1"])}) (end {f(b["dotX2"])} {f(b["dotY2"])}) (stroke (width 0.1524) (type default)) (fill (type background)))')
        elif t=='POLY':
            pts=b['points']
            if len(pts)<2: continue
            if b.get('closed'): pts=pts+[pts[0]]
            ps=' '.join(f'(xy {f(p["x"])} {f(p["y"])})' for p in pts)
            g.append(f'(polyline (pts {ps}) (stroke (width 0.1524) (type default)) (fill (type none)))')
        elif t in('CIRCLE','ELLIPSE'):
            r=abs(b.get('radius') or b.get('radiusX') or 1)
            fill='outline' if r<=2 else 'none'
            g.append(f'(circle (center {f(b["centerX"])} {f(b["centerY"])}) (radius {f(r)}) (stroke (width 0.1524) (type default)) (fill (type {fill})))')
        elif t=='ARC':
            g.append(f'(arc (start {f(b["startX"])} {f(b["startY"])}) (mid {f(b["referX"])} {f(b["referY"])}) (end {f(b["endX"])} {f(b["endY"])}) (stroke (width 0.1524) (type default)) (fill (type none)))')
        elif t=='TEXT':
            g.append(f'(text "{esc(b["value"])}" (at {f(b["x"])} {f(b["y"])} 0) (effects (font (size 1 1))))')
    pl=[]
    for p in pins:
        L=f(p['len']); rot=int(p['rot'])%360
        nm=esc(p['name'] or '~'); num=esc(p['num'])
        shape='inverted' if p.get('shape')=='DOT' else 'line'
        pl.append(f'(pin {pin_type(p["type"])} {shape} (at {f(p["x"])} {f(p["y"])} {rot}) (length {L}) (name "{nm}" (effects (font (size 1.016 1.016)))) (number "{num}" (effects (font (size 1.016 1.016)))))')
    bb=part.get('bbox') or [-10,-10,10,10]
    top=max(bb[1],bb[3]); bot=min(bb[1],bb[3])
    pn=f'(pin_numbers (hide yes)) ' if hide_nums else ''
    pnm=f'(pin_names (offset 0.254) (hide yes))' if hide_names else '(pin_names (offset 0.254))'
    return f'''(symbol "{esc(name)}" {pn}{pnm} (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "{refprefix}" (at 0 {f(top+6)} 0) (effects (font (size 1.27 1.27))))
  (property "Value" "{esc(name)}" (at 0 {f(bot-6)} 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (symbol "{esc(name)}_0_1" {" ".join(g)})
  (symbol "{esc(name)}_1_1" {" ".join(pl)})
)'''
def safe(n): return re.sub(r'[^A-Za-z0-9_.\-+]','_',n).strip('_')
