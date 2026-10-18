#!/usr/bin/env python3
"""
XRIM-117 WYVERN avionics — shared KiCad file generator.
Emits KiCad 7-format s-expressions (sch 20230121 / pcb 20221018).
KiCad 8/9 open these natively and migrate on save.

Conventions:
  PCB: absolute mm, +y down. Board: circle center (100,100) r=31.
  Schematic: every pin gets a 2.54mm stub wire + local net label  -> robust netlist.
"""
import uuid, math

def u(): return str(uuid.uuid4())

# ───────────────────────── SCHEMATIC SYMBOLS ─────────────────────────

PIN_TYPES = {"in":"input","out":"output","bi":"bidirectional","pwr":"power_in",
             "pwo":"power_out","pas":"passive","nc":"no_connect","oc":"open_collector"}

def _pin(name, num, x, y, ang, ptype):
    return (f'      (pin {PIN_TYPES[ptype]} line (at {x:.2f} {y:.2f} {ang}) (length 2.54)\n'
            f'        (name "{name}" (effects (font (size 1.0 1.0))))\n'
            f'        (number "{num}" (effects (font (size 1.0 1.0))))\n      )')

def make_box_symbol(lib, name, ref, value, footprint, left, right, top=None, bot=None, w=14.0):
    """left/right/top/bot: list of (pin_name, pin_num, ptype). Returns lib_symbol s-expr."""
    top = top or []; bot = bot or []
    n = max(len(left), len(right), 1)
    h = (n + 1) * 2.54
    hw, hh = w/2, h/2
    s = [f'  (symbol "{lib}:{name}"',
         '    (pin_names (offset 0.508)) (in_bom yes) (on_board yes)',
         f'    (property "Reference" "{ref}" (at 0 {hh+2.2:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Value" "{value}" (at 0 {-(hh+2.2):.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Footprint" "{footprint}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (symbol "{name}_0_1"',
         f'      (rectangle (start {-hw:.2f} {hh:.2f}) (end {hw:.2f} {-hh:.2f})'
         f' (stroke (width 0.254) (type default)) (fill (type background)))',
         '    )',
         f'    (symbol "{name}_1_1"']
    for i,(pn,pnum,pt) in enumerate(left):
        s.append(_pin(pn, pnum, -(hw+2.54), hh-2.54*(i+1), 0, pt))
    for i,(pn,pnum,pt) in enumerate(right):
        s.append(_pin(pn, pnum,  hw+2.54, hh-2.54*(i+1), 180, pt))
    nt = len(top)
    for i,(pn,pnum,pt) in enumerate(top):
        s.append(_pin(pn, pnum, -(nt-1)*1.27+2.54*i, hh+2.54, 270, pt))
    nb = len(bot)
    for i,(pn,pnum,pt) in enumerate(bot):
        s.append(_pin(pn, pnum, -(nb-1)*1.27+2.54*i, -(hh+2.54), 90, pt))
    s += ['    )', '  )']
    return '\n'.join(s)

def make_2pin_symbol(lib, name, ref, value, footprint, glyph, p1="~", p2="~", ptype="pas"):
    """Small vertical 2-pin device. glyph: 'R','C','CP','L','LED','D','SW','XTAL'."""
    g = []
    if glyph == 'R':
        g.append('      (rectangle (start -1.016 2.032) (end 1.016 -2.032) (stroke (width 0.254) (type default)) (fill (type none)))')
    elif glyph in ('C','CP'):
        g.append('      (polyline (pts (xy -1.524 0.508) (xy 1.524 0.508)) (stroke (width 0.4) (type default)) (fill (type none)))')
        g.append('      (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508)) (stroke (width 0.4) (type default)) (fill (type none)))')
        if glyph=='CP':
            g.append('      (text "+" (at -1.1 1.4 0) (effects (font (size 1.0 1.0))))')
    elif glyph == 'L':
        g.append('      (arc (start 0 2.032) (mid 0.6 1.524) (end 0 1.016) (stroke (width 0.25) (type default)) (fill (type none)))')
        g.append('      (arc (start 0 1.016) (mid 0.6 0.508) (end 0 0) (stroke (width 0.25) (type default)) (fill (type none)))')
        g.append('      (arc (start 0 0) (mid 0.6 -0.508) (end 0 -1.016) (stroke (width 0.25) (type default)) (fill (type none)))')
        g.append('      (arc (start 0 -1.016) (mid 0.6 -1.524) (end 0 -2.032) (stroke (width 0.25) (type default)) (fill (type none)))')
    elif glyph in ('LED','D'):
        g.append('      (polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
        g.append('      (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
    elif glyph == 'SW':
        g.append('      (polyline (pts (xy 0 2.032) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
        g.append('      (circle (center 0 2.032) (radius 0.254) (stroke (width 0.2) (type default)) (fill (type none)))')
        g.append('      (circle (center 0 -2.032) (radius 0.254) (stroke (width 0.2) (type default)) (fill (type none)))')
    elif glyph == 'XTAL':
        g.append('      (rectangle (start -1.2 0.8) (end 1.2 -0.8) (stroke (width 0.254) (type default)) (fill (type none)))')
        g.append('      (polyline (pts (xy -1.6 1.2) (xy 1.6 1.2)) (stroke (width 0.3) (type default)) (fill (type none)))')
        g.append('      (polyline (pts (xy -1.6 -1.2) (xy 1.6 -1.2)) (stroke (width 0.3) (type default)) (fill (type none)))')
    s = [f'  (symbol "{lib}:{name}"',
         '    (pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) (in_bom yes) (on_board yes)',
         f'    (property "Reference" "{ref}" (at 2.2 1.2 0) (effects (font (size 1.0 1.0)) (justify left)))',
         f'    (property "Value" "{value}" (at 2.2 -1.2 0) (effects (font (size 1.0 1.0)) (justify left)))',
         f'    (property "Footprint" "{footprint}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (symbol "{name}_0_1"'] + g + ['    )', f'    (symbol "{name}_1_1"',
         _pin(p1, "1", 0,  5.08, 270, ptype),
         _pin(p2, "2", 0, -5.08, 90, ptype),
         '    )', '  )']
    return '\n'.join(s)

def make_mosfet_symbol(lib, name, value, footprint):
    """N-MOSFET, SOT-23: 1=G, 2=S, 3=D. G left, D top, S bottom."""
    s = [f'  (symbol "{lib}:{name}"',
         '    (pin_names (offset 0.508)) (in_bom yes) (on_board yes)',
         f'    (property "Reference" "Q" (at 3.5 2.5 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Value" "{value}" (at 3.5 -2.5 0) (effects (font (size 1.27 1.27)) (justify left)))',
         f'    (property "Footprint" "{footprint}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'    (symbol "{name}_0_1"',
         '      (polyline (pts (xy -0.762 1.778) (xy -0.762 -1.778)) (stroke (width 0.3) (type default)) (fill (type none)))',
         '      (polyline (pts (xy 0 1.27) (xy 0 -1.27)) (stroke (width 0.3) (type default)) (fill (type none)))',
         '      (polyline (pts (xy 0 1.27) (xy 1.27 1.27) (xy 1.27 2.54)) (stroke (width 0.25) (type default)) (fill (type none)))',
         '      (polyline (pts (xy 0 -1.27) (xy 1.27 -1.27) (xy 1.27 -2.54)) (stroke (width 0.25) (type default)) (fill (type none)))',
         '    )',
         f'    (symbol "{name}_1_1"',
         _pin("G","1", -3.302, 0, 0, "in"),
         _pin("D","3", 1.27, 5.08, 270, "pas"),
         _pin("S","2", 1.27, -5.08, 90, "pas"),
         '    )', '  )']
    return '\n'.join(s)

def make_power_symbol(name):
    is_gnd = "GND" in name.upper()
    if is_gnd:
        glyph = ('      (polyline (pts (xy 0 0) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))\n'
                 '      (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0) (type default)) (fill (type none)))\n'
                 '      (polyline (pts (xy -0.762 -1.905) (xy 0.762 -1.905)) (stroke (width 0) (type default)) (fill (type none)))\n'
                 '      (polyline (pts (xy -0.381 -2.54) (xy 0.381 -2.54)) (stroke (width 0) (type default)) (fill (type none)))')
        vy = -3.81
    else:
        glyph = ('      (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))\n'
                 '      (polyline (pts (xy -0.762 1.27) (xy 0 2.032) (xy 0.762 1.27) (xy -0.762 1.27)) (stroke (width 0) (type default)) (fill (type outline)))')
        vy = 3.81
    return (f'  (symbol "power:{name}"\n'
            '    (power) (pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) (in_bom no) (on_board no)\n'
            f'    (property "Reference" "#PWR" (at 0 {vy-2:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Value" "{name}" (at 0 {vy:.2f} 0) (effects (font (size 1.0 1.0))))\n'
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (symbol "{name}_0_1"\n{glyph}\n    )\n'
            f'    (symbol "{name}_1_1"\n'
            + _pin("~","1",0,0,270 if not is_gnd else 90,"pwr") + '\n    )\n  )')

PWR_FLAG = ('  (symbol "power:PWR_FLAG"\n'
            '    (power) (pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) (in_bom no) (on_board no)\n'
            '    (property "Reference" "#FLG" (at 0 2.77 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            '    (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.0 1.0))))\n'
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            '    (symbol "PWR_FLAG_0_1"\n'
            '      (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))\n'
            '    )\n'
            '    (symbol "PWR_FLAG_1_1"\n'
            + _pin("pwr","1",0,0,270,"pwo") + '\n    )\n  )')


# ───────────────────────── SCHEMATIC DOCUMENT ─────────────────────────

class Schematic:
    def __init__(self, title, company, comments, paper="A2"):
        self.title=title; self.company=company; self.comments=comments; self.paper=paper
        self.lib_symbols=[]; self.body=[]
        self.symbol_pins={}   # symname -> list of (name,num,ptype,(x,y,ang)) in symbol coords
        self.placed=[]        # (ref, lib_id, x, y, rot)
        self.netlist={}       # net -> [(ref,pinnum)]
        self._refcount={}

    def add_lib_symbol(self, sexpr, name, pins):
        """pins: list of (pname, pnum, ptype, x, y, ang) in symbol-local coords (y up)."""
        self.lib_symbols.append(sexpr)
        self.symbol_pins[name]=pins

    @staticmethod
    def box_pins(left, right, top=None, bot=None, w=14.0):
        top=top or []; bot=bot or []
        n=max(len(left),len(right),1); h=(n+1)*2.54; hw,hh=w/2,h/2
        out=[]
        for i,(pn,pnum,pt) in enumerate(left):  out.append((pn,pnum,pt,-(hw+2.54), hh-2.54*(i+1),0))
        for i,(pn,pnum,pt) in enumerate(right): out.append((pn,pnum,pt, (hw+2.54), hh-2.54*(i+1),180))
        nt=len(top)
        for i,(pn,pnum,pt) in enumerate(top):   out.append((pn,pnum,pt,-(nt-1)*1.27+2.54*i, hh+2.54,270))
        nb=len(bot)
        for i,(pn,pnum,pt) in enumerate(bot):   out.append((pn,pnum,pt,-(nb-1)*1.27+2.54*i,-(hh+2.54),90))
        return out

    TWO_PIN = [("~","1","pas",0,5.08,270),("~","2","pas",0,-5.08,90)]
    FET_PIN = [("G","1","in",-3.302,0,0),("D","3","pas",1.27,5.08,270),("S","2","pas",1.27,-5.08,90)]

    def place(self, lib_id, sym_name, ref, value, x, y, nets, rot=0, footprint=None,
              extra_props=None, nc_pins=()):
        """nets: dict pin_num -> net name ('' to leave). Adds stub+label per pin.
        Symbol local coords are y-up; schematic is y-down. rot in {0,90,180,270} CCW."""
        pins = self.symbol_pins[sym_name]
        props = ''
        fp = footprint or ''
        def rotp(px,py,ang):
            # symbol-local (y up) -> sheet offset (y down), with CCW rotation rot
            a = math.radians(rot)
            rx = px*math.cos(a)-py*math.sin(a)
            ry = px*math.sin(a)+py*math.cos(a)
            return x+rx, y-ry, (ang+rot)%360
        body=[f'  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit 1)',
              '    (in_bom yes) (on_board yes) (dnp no)', f'    (uuid "{u()}")',
              f'    (property "Reference" "{ref}" (at {x:.2f} {y-1.4:.2f} 0) (effects (font (size 1.0 1.0))))',
              f'    (property "Value" "{value}" (at {x:.2f} {y+1.4:.2f} 0) (effects (font (size 1.0 1.0))))',
              f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
              f'    (property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))']
        for pn,pnum,pt,px,py,pang in pins:
            body.append(f'    (pin "{pnum}" (uuid "{u()}"))')
        body.append(f'    (instances (project "xrim" (path "/" (reference "{ref}") (unit 1))))')
        body.append('  )')
        self.body.append('\n'.join(body))
        # stubs + labels
        for pn,pnum,pt,px,py,pang in pins:
            gx,gy,gang = rotp(px,py,pang)
            net = nets.get(pnum, None)
            if net:
                # stub direction: pin angle points INTO symbol; stub extends outward = pang direction reversed?
                # In KiCad a pin's (at) is its connection point; angle is direction toward body.
                # Wire from connection point outward 2.54mm opposite to body direction:
                dx = {0:-2.54, 90:0, 180:2.54, 270:0}[gang]
                dy = {0:0, 90:2.54, 180:0, 270:-2.54}[gang]
                ex,ey = gx+dx, gy+dy
                self.body.append(f'  (wire (pts (xy {gx:.2f} {gy:.2f}) (xy {ex:.2f} {ey:.2f})) (stroke (width 0) (type default)) (uuid "{u()}"))')
                just = "right" if dx<0 else "left"
                self.body.append(f'  (label "{net}" (at {ex:.2f} {ey:.2f} 0) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid "{u()}"))')
                self.netlist.setdefault(net,[]).append((ref,pnum))
            elif pnum in nc_pins or net is None and nets.get('__nc_default__'):
                self.body.append(f'  (no_connect (at {gx:.2f} {gy:.2f}) (uuid "{u()}"))')
        for pnum in nc_pins:
            pass
        self.placed.append((ref,lib_id,x,y,rot))

    def power_flag(self, net, x, y):
        ref=f"#FLG{len([1 for p in self.placed if p[0].startswith('#FLG')])+1:03d}"
        self.body.append(
            f'  (symbol (lib_id "power:PWR_FLAG") (at {x:.2f} {y:.2f} 0) (unit 1)\n'
            '    (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid "{u()}")\n'
            f'    (property "Reference" "{ref}" (at {x:.2f} {y-2:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Value" "PWR_FLAG" (at {x:.2f} {y-3.5:.2f} 0) (effects (font (size 1.0 1.0))))\n'
            f'    (property "Footprint" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Datasheet" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (pin "1" (uuid "{u()}"))\n'
            f'    (instances (project "xrim" (path "/" (reference "{ref}") (unit 1))))\n  )')
        self.body.append(f'  (wire (pts (xy {x:.2f} {y:.2f}) (xy {x:.2f} {y+2.54:.2f})) (stroke (width 0) (type default)) (uuid "{u()}"))')
        self.body.append(f'  (label "{net}" (at {x:.2f} {y+2.54:.2f} 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{u()}"))')
        self.placed.append((ref,"power:PWR_FLAG",x,y,0))

    def text(self, txt, x, y, size=2.0, bold=True):
        b=" bold" if bold else ""
        self.body.append(f'  (text "{txt}" (at {x:.2f} {y:.2f} 0) (effects (font (size {size} {size}){b}) (justify left bottom)) (uuid "{u()}"))')

    def rect(self, x1,y1,x2,y2):
        self.body.append(f'  (rectangle (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type dash) (color 120 120 120 1)) (fill (type none)) (uuid "{u()}"))')

    def emit(self):
        head=(f'(kicad_sch (version 20230121) (generator "xrim_gen")\n'
              f'  (uuid "{u()}")\n  (paper "{self.paper}")\n  (title_block\n'
              f'    (title "{self.title}")\n    (date "2026-06-09")\n    (rev "B")\n'
              f'    (company "{self.company}")\n')
        for i,c in enumerate(self.comments[:9]):
            head+=f'    (comment {i+1} "{c}")\n'
        head+='  )\n  (lib_symbols\n'
        out=head + '\n'.join(self.lib_symbols) + '\n  )\n' + '\n'.join(self.body)
        out+='\n  (sheet_instances (path "/" (page "1")))\n)\n'
        return out


# ───────────────────────── PCB FOOTPRINT PRIMITIVES ─────────────────────────

class Pad:
    def __init__(self, num, x, y, w, h, shape="roundrect", kind="smd", drill=None,
                 layers=None, ang=0):
        self.num=num; self.x=x; self.y=y; self.w=w; self.h=h
        self.shape=shape; self.kind=kind; self.drill=drill; self.ang=ang
        if layers is None:
            layers='(layers "F.Cu" "F.Paste" "F.Mask")' if kind=="smd" else '(layers "*.Cu" "*.Mask")'
        self.layers=layers

class FP:
    """Footprint definition in local coords (y down, rot CCW)."""
    def __init__(self, name, pads, courtyard, silk=None, attr="smd"):
        self.name=name; self.pads=pads; self.courtyard=courtyard; self.silk=silk or []
        self.attr=attr

def fp_sexpr(fp, ref, value, x, y, rot, pad_nets, net_ids, extra=""):
    """Emit a footprint instance. pad_nets: padnum->netname."""
    a=math.radians(rot)
    s=[f'  (footprint "XRIM:{fp.name}" (layer "F.Cu")', f'    (uuid "{u()}")',
       f'    (at {x:.3f} {y:.3f} {rot})',
       f'    (attr {fp.attr})',
       f'    (property "Reference" "{ref}" (at 0 {-(fp.courtyard[3]+1.2):.2f} {-rot}) (layer "F.SilkS") (uuid "{u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
       f'    (property "Value" "{value}" (at 0 {fp.courtyard[3]+1.2:.2f} {-rot}) (layer "F.Fab") (uuid "{u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
       ]
    x1,y1,x2,y2 = fp.courtyard[0],fp.courtyard[1],fp.courtyard[2],fp.courtyard[3]
    s.append(f'    (fp_rect (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") (uuid "{u()}"))')
    for sl in fp.silk:
        s.append('    '+sl.replace('TSTAMP', u()))
    for p in fp.pads:
        net = pad_nets.get(str(p.num), "")
        nets = f' (net {net_ids[net]} "{net}")' if net else ''
        drill = f' (drill {p.drill:.2f})' if p.drill else ''
        rr = ' (roundrect_rratio 0.25)' if p.shape=="roundrect" else ''
        pang = (p.ang + rot) % 360
        s.append(f'    (pad "{p.num}" {p.kind} {p.shape} (at {p.x:.3f} {p.y:.3f} {pang}){drill} (size {p.w:.3f} {p.h:.3f}) {p.layers}{rr}{nets} (uuid "{u()}"))')
    if extra: s.append(extra)
    s.append('  )')
    return '\n'.join(s)

def pad_abs_pos(fp, x, y, rot):
    """Return dict padnum -> (abs_x, abs_y) for a placed footprint."""
    a=math.radians(rot); out={}
    for p in fp.pads:
        # KiCad: pad pos rotates with footprint, footprint rot is CCW but +y down → screen CW.
        # Pad at local (px,py): abs = pos + R(-rot_screen)... KiCad applies rotation in its
        # coordinate sense: abs_x = x + px*cos(a) + py*sin(a)? Empirically for KiCad with y-down,
        # a footprint rotated by +rot degrees rotates pads counter-clockwise on screen:
        # abs = (x + px*cos - py*sin_neg ...). Use standard KiCad transform:
        rx = p.x*math.cos(a) + p.y*math.sin(a)
        ry = -p.x*math.sin(a) + p.y*math.cos(a)
        out[str(p.num)] = (x+rx, y+ry)
    return out


# ───────────────────────── PCB DOCUMENT ─────────────────────────

class Board:
    def __init__(self, title, cx=100.0, cy=100.0, radius=31.0):
        self.title=title; self.cx=cx; self.cy=cy; self.r=radius
        self.nets={"":0}; self._nid=0
        self.footprints=[]   # sexpr strings
        self.fp_index=[]     # (ref, fp, x, y, rot, pad_nets)
        self.tracks=[]; self.vias=[]; self.zones=[]; self.graphics=[]
        self.netclass_width={"Default":0.25}

    def net(self, name):
        if name not in self.nets:
            self._nid+=1; self.nets[name]=self._nid
        return self.nets[name]

    def add_fp(self, fp, ref, value, x, y, rot, pad_nets):
        for n in pad_nets.values():
            if n: self.net(n)
        self.footprints.append(fp_sexpr(fp, ref, value, x, y, rot, pad_nets, self.nets))
        self.fp_index.append((ref, fp, x, y, rot, pad_nets))

    def track(self, net, pts, layer="F.Cu", width=0.25):
        nid=self.net(net)
        for (x1,y1),(x2,y2) in zip(pts[:-1],pts[1:]):
            if abs(x1-x2)<1e-6 and abs(y1-y2)<1e-6: continue
            self.tracks.append((x1,y1,x2,y2,width,layer,nid,net))

    def via(self, net, x, y, size=0.6, drill=0.3):
        self.vias.append((x,y,size,drill,self.net(net),net))

    def route(self, net, pts, layer="F.Cu", width=0.25, via_at=()):
        """pts may contain ('via', x, y) markers to switch layer."""
        cur=layer; seg=[]
        for p in pts:
            if isinstance(p, tuple) and len(p)==3 and p[0]=='via':
                seg.append((p[1],p[2]))
                if len(seg)>1: self.track(net, seg, cur, width)
                self.via(net, p[1], p[2])
                cur = "B.Cu" if cur=="F.Cu" else "F.Cu"
                seg=[(p[1],p[2])]
            else:
                seg.append(p)
        if len(seg)>1: self.track(net, seg, cur, width)

    def gnd_zone(self, layer):
        nid=self.net("GND")
        r=self.r-0.25
        pts=[]
        for i in range(72):
            a=2*math.pi*i/72
            pts.append(f'(xy {self.cx+r*math.cos(a):.3f} {self.cy+r*math.sin(a):.3f})')
        self.zones.append(
            f'  (zone (net {nid}) (net_name "GND") (layer "{layer}") (uuid "{u()}") (name "GND_{layer}")\n'
            '    (hatch edge 0.5)\n'
            '    (connect_pads (clearance 0.3))\n'
            '    (min_thickness 0.25) (filled_areas_thickness no)\n'
            '    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.5))\n'
            f'    (polygon (pts {" ".join(pts)}))\n'
            '  )')

    def emit(self):
        s=[f'(kicad_pcb (version 20221018) (generator "xrim_gen")',
           '  (general (thickness 1.6))', '  (paper "A4")',
           f'  (title_block (title "{self.title}") (date "2026-06-09") (rev "B") (company "Skylight Industries LLC / Legacy Systems Research Group"))',
           '  (layers',
           '    (0 "F.Cu" signal) (31 "B.Cu" signal)',
           '    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")',
           '    (34 "B.Paste" user) (35 "F.Paste" user)',
           '    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")',
           '    (38 "B.Mask" user) (39 "F.Mask" user)',
           '    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")',
           '    (44 "Edge.Cuts" user) (45 "Margin" user)',
           '    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")',
           '    (48 "B.Fab" user) (49 "F.Fab" user)',
           '  )',
           '  (setup (pad_to_mask_clearance 0.05)',
           '    (pcbplotparams (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000) (disableapertmacros false) (usegerberextensions false) (usegerberattributes true) (usegerberadvancedattributes true) (creategerberjobfile true) (dashed_line_dash_ratio 12.000000) (dashed_line_gap_ratio 3.000000) (svgprecision 4) (plotframeref false) (viasonmask false) (mode 1) (useauxorigin false) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15.000000) (dxfpolygonmode true) (dxfimperialunits true) (dxfusepcbnewfont true) (psnegative false) (psa4output false) (plotreference true) (plotvalue true) (plotinvisibletext false) (sketchpadsonfab false) (subtractmaskfromsilk false) (outputformat 1) (mirror false) (drillshape 1) (scaleselection 1) (outputdirectory ""))',
           '  )']
        for name,nid in sorted(self.nets.items(), key=lambda kv: kv[1]):
            s.append(f'  (net {nid} "{name}")')
        # board edge
        s.append(f'  (gr_circle (center {self.cx} {self.cy}) (end {self.cx+self.r} {self.cy}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{u()}"))')
        s += self.graphics
        s += self.footprints
        for (x1,y1,x2,y2,w,layer,nid,net) in self.tracks:
            s.append(f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (width {w:.3f}) (layer "{layer}") (net {nid}) (uuid "{u()}"))')
        for (x,y,size,drill,nid,net) in self.vias:
            s.append(f'  (via (at {x:.3f} {y:.3f}) (size {size:.2f}) (drill {drill:.2f}) (layers "F.Cu" "B.Cu") (net {nid}) (uuid "{u()}"))')
        s += self.zones
        s.append(')')
        return '\n'.join(s)

def project_file(name):
    return ('{\n  "board": { "design_settings": { "rules": {\n'
            '    "min_clearance": 0.1, "min_track_width": 0.127,\n'
            '    "min_via_diameter": 0.5, "min_via_drill": 0.3 } } },\n'
            f'  "meta": {{ "filename": "{name}.kicad_pro", "version": 1 }},\n'
            '  "net_settings": { "classes": [ {\n'
            '      "name": "Default", "clearance": 0.127, "track_width": 0.2,\n'
            '      "via_diameter": 0.6, "via_drill": 0.3, "bus_width": 12, "diff_pair_gap": 0.25,\n'
            '      "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0,\n'
            '      "microvia_diameter": 0.3, "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)",\n'
            '      "schematic_color": "rgba(0, 0, 0, 0.000)", "wire_width": 6 } ], "meta": { "version": 3 } },\n'
            '  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] },\n'
            '  "sheets": [], "text_variables": {}\n}\n')


def escape_stubs(board, fp, x, y, rot, pad_nets, skip_nets=("GND",), pitch_max=0.55,
                 short=1.0, long=2.0, width=0.2, dogbone=False):
    """Dogbone escapes: staggered stub + pre-placed 0.45/0.25 via (fine-pitch, 2-layer)."""
    import math as _m
    a=_m.radians(rot)
    for idx,p in enumerate(fp.pads):
        net=pad_nets.get(str(p.num),"")
        if not net or net in skip_nets: continue
        if p.kind!="smd": continue
        if max(p.w,p.h) < 0.7 and min(p.w,p.h) > 0.45: continue  # not fine pitch
        if abs(p.x)>=abs(p.y): d=(1.0 if p.x>0 else -1.0, 0.0)
        else: d=(0.0, 1.0 if p.y>0 else -1.0)
        L = short if idx%2==0 else long
        ex,ey = p.x+d[0]*L, p.y+d[1]*L
        def tr(px,py):
            rx=px*_m.cos(a)+py*_m.sin(a); ry=-px*_m.sin(a)+py*_m.cos(a)
            return (x+rx, y+ry)
        board.track(net,[tr(p.x,p.y),tr(ex,ey)],"F.Cu",width)
        if dogbone:
            vx,vy=tr(ex,ey)
            board.via(net,vx,vy,size=0.45,drill=0.25)
