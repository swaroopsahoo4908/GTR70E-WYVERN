#!/usr/bin/env python3
"""GTR70E WYVERN -- full fit-check assembly: every printed part plus every bought part, in place.

Bought parts come from two sources:
  vendor STEP  (3D parts/vendor/): Adafruit BNO085 4754, BME688 5046, microSD 4682, Feather
               RP2040 RFM form factor (5712 model; the 5714 RFM95 board shares the PCB outline,
               holes and RFM module footprint), Pololu 2810 MOSFET switch, Pololu D24V10F5 buck.
               Adafruit models: github.com/adafruit/Adafruit_CAD_Parts (MIT). Pololu: product pages.
  datasheet-built (no public model reachable): KST X08 Plus servo, AeroTech F67 motor (29 x 83),
               2S LiPo, packed 24 in chute + Nomex + shock cord, M5 eyebolt, 1010 rail buttons,
               O-rings, 3/8 in bypass tube, perfboard parts, whip antenna, nose ballast pour.

Checks (written to assembly/fit_report.json + FIT_REPORT.md):
  1. pairwise interference volume between every pair of components (bounding-box prefilter,
     then an exact boolean); designed contacts come out as ~0 mm^3
  2. every component inside the airframe bore (radial clearance to the tube wall)
  3. control fins swept to +/-15 deg about their hinge, checked against the body and stabilizers
  4. print-bed fit of every printed part on a 256 x 256 x 256 mm printer (flight + tunnel)
Outputs: assembly/GTR70E_WYVERN_fit_assembly.step, assembly/fit_report.json, FIT_REPORT.md,
         assembly/fit_meshes/*.stl (for the D6 render)
"""
import json, math, os, sys, glob, itertools, time
import numpy as np
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Simulations"))
import wf_core as C

D3 = os.path.join(ROOT, "3D parts")
VEND = os.path.join(D3, "vendor")
ASM = os.path.join(D3, "assembly"); os.makedirs(os.path.join(ASM, "fit_meshes"), exist_ok=True)
L = C.L_TOTAL
def zx(x): return L - x
FACE_AZ = dict(px=0, py=90, nx=180, ny=270)

comps = []   # (name, shape(cq.Workplane or Shape), group, color, source)
def add(name, wp, group, color, source):
    sh = wp.val() if isinstance(wp, cq.Workplane) else wp
    if isinstance(wp, cq.Workplane) and len(wp.vals()) > 1:
        sh = cq.Compound.makeCompound([v for v in wp.vals() if isinstance(v, cq.Shape)])
    comps.append(dict(name=name, shape=sh, group=group, color=color, source=source))

def step(fname, sub="flight"):
    return cq.importers.importStep(os.path.join(D3, sub, fname))

def rz(wp, deg):
    return wp.rotate((0, 0, 0), (0, 0, 1), deg)

def box(dx, dy, dz, cx=0, cy=0, cz=0):
    return cq.Workplane("XY").box(dx, dy, dz).translate((cx, cy, cz))

def cylz(r, z0, h, x=0, y=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(h)

def cyl_x(d, length, x0, y=0.0, z=0.0):
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(d / 2).extrude(length)

# ------------------------------------------------------------------ printed parts (from the generator)
PRINTED_COL = dict(ASAAero=(0.80, 0.82, 0.86), PCFR=(0.72, 0.42, 0.12), PETGCF=(0.20, 0.22, 0.25))
def mat_of(fn):
    for k in PRINTED_COL:
        if k in fn: return k
    return "PETGCF"
for fn in sorted(glob.glob(os.path.join(D3, "flight", "*.step"))):
    b = os.path.basename(fn)
    if b.startswith(("06_servo_hub", "12_rect_fin", "13_rail_button")): continue
    add(b[:-5], step(b), "printed", PRINTED_COL[mat_of(b)], "printed (gen_wyvern_fin.py)")
hub = step("06_servo_hub_PETGCF_x4.step"); rf = step("12_rect_fin_PETGCF_x4.step")
H = int(C.CFIN_H_NOMINAL)
cfin = cq.importers.importStep(os.path.join(D3, "control_fins", "NACA0006", f"cfin_NACA0006_H{H}_PETGCF.step"))
for a in (0, 90, 180, 270):
    add(f"servo_hub_az{a}", rz(hub, a), "printed", PRINTED_COL["PETGCF"], "printed")
    add(f"control_fin_az{a}", rz(cfin, a), "fin", (0.76, 0.25, 0.05), "printed")
for i in range(4):
    add(f"stabilizer_{i}", rz(rf, 90 * i), "printed", (0.12, 0.16, 0.22), "printed")
rbs = step("13_rail_button_spacer_PETGCF_x2.step")
add("rail_button_spacer_lower", rbs, "printed", PRINTED_COL["PETGCF"], "printed")
z_up = zx(C.X_RB_BOT) - 10.0
add("rail_button_spacer_upper", rbs.translate((0, 0, z_up - (zx(C.X_MB_BOT) + 20))), "printed", PRINTED_COL["PETGCF"], "printed")

# ------------------------------------------------------------------ servos (datasheet-built KST X08 Plus)
sv = C.SERVO
zc = zx(C.X_CT_BOT) + C.SERVO_RING_Z
zh = zx(C.X_HINGE)
def x08():
    body = box(sv["H"], sv["W"], sv["L"], C.SERVO_BASE_R + sv["H"] / 2, 0, zc)
    ears = box(sv["ear_t"], sv["W"], sv["ear_span"], C.PAD_INNER_R - sv["ear_t"] / 2, 0, zc)
    spl = cyl_x(5.0, sv["spline_len"], C.SERVO_TOP_R, 0, zh)
    horn = cyl_x(11.0, 1.0, C.SPLINE_TOP_R, 0, zh)
    return body.union(ears).union(spl), horn
s_body, s_horn = x08()
for a in (0, 90, 180, 270):
    add(f"KST_X08_Plus_az{a}", rz(s_body, a), "servo", (0.12, 0.30, 0.75), "datasheet-built (23.5 x 8 x 16.8, ears 30.3)")
    add(f"servo_horn_az{a}", rz(s_horn, a), "servo", (0.85, 0.85, 0.85), "datasheet-built (round horn, in hub pocket)")

# ------------------------------------------------------------------ spine boards (vendor STEP)
z0s = zx(C.X_CT_BOT) + C.SPINE_Z0
def place_board(shape, bd):
    """board local: x along L (axial), y across W, z = thickness (component side +z).
    World: inner face of the PCB at BOARD_PLANE on the board's face, components outward."""
    P = C.board_plane(bd)
    s = shape.rotate((0, 0, 0), (0, 1, 0), 90)             # local z -> world +x, local x -> world -z
    s = s.translate((P, -bd["W"] / 2 + bd.get("offset", 0.0), z0s + bd["z0"] + bd["L"]))
    return rz(s, FACE_AZ[bd["face"]])
for bd in C.SPINE_BOARDS:
    if bd["step"]:
        shp = cq.importers.importStep(os.path.join(VEND, bd["step"]))
        bbx = shp.val().BoundingBox()
        shp = shp.translate((-bbx.xmin if bbx.xmin < 0 else 0, 0, 0))
        add(bd["key"], place_board(shp, bd), "vendor", (0.05, 0.35, 0.55) if bd["key"] != "feather" else (0.10, 0.10, 0.12),
            f"vendor STEP {bd['step']}")
    elif bd["key"] == "battery":
        b = cq.Workplane("XY").box(bd["L"], bd["W"], 14.0).translate((bd["L"] / 2, bd["W"] / 2, 7.0))
        add("lipo_2S_450", place_board(b, bd), "cots", (0.85, 0.65, 0.10), "datasheet-built 57 x 30 x 14 (VERIFY on the owned pack)")
    elif bd["key"] == "perfboard":
        pb = cq.Workplane("XY").box(bd["L"], bd["W"], 1.6).translate((bd["L"] / 2, bd["W"] / 2, 0.8))
        add("perfboard_16x62", place_board(pb, bd), "cots", (0.55, 0.35, 0.15), "datasheet-built FR4 0.1 in perf")
        sw = cq.importers.importStep(os.path.join(VEND, "pololu_2810_mini_mosfet_switch.step"))
        bb = sw.val().BoundingBox(); sw = sw.translate((-bb.xmin + 30.0, -bb.ymin + 0.4, 1.6))
        add("pololu_2810_switch", place_board(sw, bd), "vendor", (0.10, 0.45, 0.20), "vendor STEP pololu_2810")
        bk = cq.importers.importStep(os.path.join(VEND, "pololu_D24V10F5_buck.step"))
        bb = bk.val().BoundingBox()
        bk = bk.rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 0, 0))
        bb = bk.val().BoundingBox(); bk = bk.translate((-bb.xmin + 4.0, -bb.ymin + 1.65, 1.6))
        add("pololu_D24V10F5_buck", place_board(bk, bd), "vendor", (0.10, 0.45, 0.20), "vendor STEP pololu_D24V10F5")
        v = C.SCREW_SWITCH_V
        ss = cq.Workplane("XY").center(v, 8.0).circle(2.0).extrude(4.0).translate((0, 0, 1.6))
        add("screw_switch_standoff_M2", place_board(ss, bd), "cots", (0.80, 0.65, 0.20), "datasheet-built brass M2 standoff + screw")
        bz = cq.Workplane("XY").center(53.0, 8.0).circle(6.0).extrude(6.5).translate((0, 0, 1.6))
        add("piezo_12mm_lowprofile", place_board(bz, bd), "cots", (0.15, 0.15, 0.15), "datasheet-built 12 x 6.5 mm")
        cap = cq.Workplane("YZ").workplane(offset=20.0).center(8.0, -3.4).circle(3.15).extrude(11.0)
        add("cap_470uF_under_board", place_board(cap, bd), "cots", (0.10, 0.10, 0.40), "datasheet-built 6.3 x 11 mm, under the perfboard")

# whip antenna: down the wall over the +X face, from the Feather's top end
fe = [b for b in C.SPINE_BOARDS if b["key"] == "feather"][0]
zt = z0s + fe["z0"] + fe["L"]
add("whip_915MHz_78mm", cylz(0.6, zt - 78.0, 78.0, x=C.RI - 3.5, y=6.0), "cots", (0.10, 0.45, 0.85), "datasheet-built 1/4-wave wire")

# ------------------------------------------------------------------ motor, bypass, recovery, hardware
mot = C.MOTORS[C.FLIGHT_MOTOR]
za = zx(C.X_MOTOR_AFT)
m = cylz(C.MOTOR_D / 2, za, mot["L"]).cut(cylz(5.0, za - 1, 14.0))
add(f"AeroTech_{C.FLIGHT_MOTOR}", m, "cots", (0.45, 0.20, 0.70), f"datasheet-built 29 x {mot['L']:.0f} mm (thrustcurve.org)")
zb_top = zx(C.X_BYPASS_TOP); zb_bot = zx(C.X_BYPASS_BOT)
tube = cylz(C.BYPASS["od"] / 2, zb_bot, zb_top - zb_bot).cut(cylz(C.BYPASS["id"] / 2, zb_bot - 1, zb_top - zb_bot + 2))
add("bypass_tube_3_8in_Al", tube, "cots", (0.70, 0.70, 0.72), C.BYPASS["mat"])
for nm, z in (("oring_plenum", zx(C.X_PLENUM_TOP) - 2.2), ("oring_rb_floor", zx(C.X_RB_BOT) - 14.5 + 1.0)):
    o = cq.Workplane("XY").workplane(offset=z - 0.85).circle(C.BYPASS["od"] / 2 + 1.6).circle(C.BYPASS["od"] / 2).extrude(1.7)
    add(nm, o, "cots", (0.05, 0.05, 0.05), "AS568-012 Buna-N (9.25 x 1.78)")
# eyebolt M5, eye in the tangential plane, 20 mm off-axis at az 180
zf = zx(C.X_RB_BOT)
eye = cq.Workplane("YZ").workplane(offset=-20 - 1.75).center(0, zf + 1.5 + 8.5).circle(8.5).circle(5.0).extrude(3.5)
shank = cylz(2.5, zf - 8.0, 10.0, x=-20)
add("M5_eyebolt", eye.union(shank), "cots", (0.70, 0.70, 0.72), "datasheet-built M5 forged eyebolt, eye 10 ID / 17 OD")
# packed recovery: chute bundle under the nose shoulder, Nomex wrap, cord bundle above the floor
zn = zx(C.X_RB_TOP) - C.NOSE["shoulder"]
add("chute_24in_packed", cylz(23.0, zn - 2 - 95.0, 95.0), "recovery", (0.95, 0.55, 0.10), "datasheet-built (Estes 24 in rip-stop, packed 46 x 95, VERIFY)")
add("nomex_wrap", cylz(25.5, zn - 2 - 100.0, 100.0).cut(cylz(24.0, zn - 103.0, 104.0)), "recovery", (0.85, 0.75, 0.30), "datasheet-built 12 x 12 in blanket, wrapped")
add("shock_cord_bundle", cylz(14.0, zf + 22.0, 45.0, x=6.0), "recovery", (0.95, 0.85, 0.30), "datasheet-built 19 ft aramid, z-folded")
# nose ballast: steel shot + epoxy (5.0 g/cm3 effective) poured into the tip cavity
Ln = C.NOSE["L"]; rho = (C.R ** 2 + Ln ** 2) / (2 * C.R)
def r_in(x): return max(math.sqrt(max(rho ** 2 - (Ln - x) ** 2, 0)) + C.R - rho - C.NOSE["wall"], 0.0)
x8 = Ln * 8 / 60; vol = C.BALLAST_G / 5.0 * 1000; acc = 0.0; xs = x8
while acc < vol and xs < Ln:
    acc += math.pi * r_in(xs) ** 2 * 0.5; xs += 0.5
pts = [(0.0, zx(x8))] + [(r_in(x) - 0.05, zx(x)) for x in np.linspace(x8, xs, 30)] + [(0.0, zx(xs))]
bal = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
add("nose_ballast_pour", bal, "cots", (0.35, 0.35, 0.38), f"{C.BALLAST_G:.0f} g steel shot + epoxy, fills {xs - x8:.0f} mm of the tip")
BALLAST_FILL = xs - x8
# rail buttons (1010): base 11.1 x 2.4, neck 7.9 x 3.0, head 11.1 x 2.4 on the 3 mm spacers
def button(zc_):
    r0 = C.R + C.RAIL_BUTTON_STANDOFF
    b = cyl_x(11.1, 2.4, r0, 0, zc_).union(cyl_x(7.9, 3.0, r0 + 2.4, 0, zc_)).union(cyl_x(11.1, 2.4, r0 + 5.4, 0, zc_))
    return rz(b, C.RAIL_BUTTON_AZ_DEG)
add("rail_button_1010_lower", button(zx(C.X_MB_BOT) + 20), "cots", (0.95, 0.95, 0.95), "datasheet-built 1010 Delrin button")
add("rail_button_1010_upper", button(z_up), "cots", (0.95, 0.95, 0.95), "datasheet-built 1010 Delrin button")

# ------------------------------------------------------------------ checks
def vol(sh):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(sh.wrapped, p); return p.Mass()
def common_vol(a, b):
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped); op.Build()
    if not op.IsDone(): return float("nan")
    return vol(cq.Shape.cast(op.Shape()))
def bb_overlap(a, b, tol=0.0):
    A, B = a.BoundingBox(), b.BoundingBox()
    return not (A.xmax < B.xmin - tol or B.xmax < A.xmin - tol or A.ymax < B.ymin - tol or B.ymax < A.ymin - tol
                or A.zmax < B.zmin - tol or B.zmax < A.zmin - tol)

t0 = time.time()
pairs = []
for a, b in itertools.combinations(comps, 2):
    if a["group"] == "printed" and b["group"] == "printed" and not (a["name"].startswith(("servo_hub", "control_fin")) or b["name"].startswith(("servo_hub", "control_fin"))):
        # printed-printed pairs were checked by the generator's assembly; still include tube/insert stack
        pass
    if not bb_overlap(a["shape"], b["shape"]): continue
    v = common_vol(a["shape"], b["shape"])
    if v > 0.5:
        pairs.append(dict(a=a["name"], b=b["name"], mm3=round(v, 2)))
print(f"interference pass {time.time() - t0:.0f} s, {len(pairs)} overlapping pairs")

# radial clearance to the bore for internal parts (min over the part's vertices)
bore = []
for c_ in comps:
    if c_["group"] in ("printed", "fin"): continue
    if c_["name"].startswith(("rail_button", "nose_ballast")): continue
    vs = np.array([[v.X, v.Y, v.Z] for v in c_["shape"].Vertices()]) if c_["shape"].Vertices() else None
    if vs is None or len(vs) == 0:
        continue
    r = np.hypot(vs[:, 0], vs[:, 1]).max()
    bore.append(dict(name=c_["name"], r_max=round(float(r), 2), clearance_to_bore=round(C.RI - float(r), 2)))
bore.sort(key=lambda d: d["clearance_to_bore"])

# fin sweep +/-15 deg about the hinge axis (radial X axis through the hinge station), az 0 fin
fin0 = [c_ for c_ in comps if c_["name"] == "control_fin_az0"][0]["shape"]
body_parts = [c_ for c_ in comps if c_["name"].startswith(("04_control_tube", "07_motor_bay", "stabilizer"))]
sweep = []
for d in (-15, -10, -5, 5, 10, 15):
    fr = fin0.rotate(cq.Vector(0, 0, zh), cq.Vector(1, 0, zh), d)
    worst = 0.0; who = ""
    for bp in body_parts:
        if bb_overlap(fr, bp["shape"]):
            v = common_vol(fr, bp["shape"])
            if v > worst: worst, who = v, bp["name"]
    sweep.append(dict(defl_deg=d, overlap_mm3=round(worst, 2), with_=who))

# print-bed check (256 mm cube): every printed STEP, flight + tunnel + control fins
bed = []
for sub in ("flight", "wind_tunnel", "control_fins/NACA0006"):
    for fn in sorted(glob.glob(os.path.join(D3, sub, "*.step"))):
        bb = cq.importers.importStep(fn).val().BoundingBox()
        dims = sorted([bb.xlen, bb.ylen, bb.zlen], reverse=True)
        bed.append(dict(part=os.path.basename(fn)[:-5], dims_mm=[round(d, 1) for d in dims], fits_256=bool(dims[0] <= 256 and dims[1] <= 256)))

# allowed contacts: designed press/bond/clamp interfaces reported but not counted as faults
ALLOW = [("bypass_tube", "08_plenum"), ("bypass_tube", "03_rb_floor"), ("oring", "bypass_tube"),
         ("oring", "08_plenum"), ("oring", "03_rb_floor"), ("M5_eyebolt", "03_rb_floor"),
         ("servo_horn", "servo_hub"), ("rail_button", "rail_button_spacer"), ("rail_button_spacer", "04_control_tube"), ("rail_button_spacer", "07_motor_bay"),
         ("rail_button", "02_recovery"), ("rail_button", "03_rb_floor"), ("rail_button", "07_motor_bay"),
         ("nose_ballast", "01_nose")]
def allowed(p):
    for x, y in ALLOW:
        if (p["a"].startswith(x) and p["b"].startswith(y)) or (p["b"].startswith(x) and p["a"].startswith(y)): return True
        if (x in p["a"] and y in p["b"]) or (x in p["b"] and y in p["a"]): return True
    return False
faults = [p for p in pairs if not allowed(p)]
designed = [p for p in pairs if allowed(p)]
rep = dict(components=len(comps), interference_faults=faults, designed_contacts=designed,
           bore_clearance=bore, fin_sweep=sweep, print_bed_256=bed, ballast_fill_mm=round(BALLAST_FILL, 1),
           sources={c_["name"]: c_["source"] for c_ in comps if c_["group"] != "printed"})
json.dump(rep, open(os.path.join(ASM, "fit_report.json"), "w"), indent=1)

# ------------------------------------------------------------------ assembly STEP + meshes
asm = cq.Assembly(name="GTR70E_WYVERN_fit")
for c_ in comps:
    asm.add(c_["shape"], name=c_["name"], color=cq.Color(*c_["color"]))
asm.save(os.path.join(ASM, "GTR70E_WYVERN_fit_assembly.step"))
for c_ in comps:
    try:
        cq.exporters.export(cq.Workplane().add(c_["shape"]), os.path.join(ASM, "fit_meshes", c_["name"] + ".stl"), tolerance=0.08, angularTolerance=0.3)
    except Exception as e:
        print("mesh fail", c_["name"], e)
json.dump({c_["name"]: dict(group=c_["group"], color=c_["color"]) for c_ in comps}, open(os.path.join(ASM, "fit_meshes", "index.json"), "w"), indent=1)

print(json.dumps(dict(faults=faults, designed=len(designed), tightest_bore=bore[:6], fin_sweep=sweep,
                      bed_fail=[b for b in bed if not b["fits_256"]], ballast_fill=BALLAST_FILL), indent=1))

# ------------------------------------------------------------------ human-readable report
md = ["# Fit check report", "",
      "_Generated by `3D parts/_generator/gen_fit_assembly.py`. Assembly: `GTR70E_WYVERN_fit_assembly.step`. Render: `Documentation/diagrams/D6_fit_check.png`._", "",
      f"{len(comps)} components: every printed part, plus vendor STEP models where a public one exists and datasheet-built models where it does not.", "",
      "## Interference", "",
      ("No interference faults." if not faults else "| part A | part B | overlap (mm³) |\n|---|---|---|\n" + "\n".join(f"| {p['a']} | {p['b']} | {p['mm3']} |" for p in faults)), "",
      "Designed contacts (glands, seats): " + (", ".join(f"{p['a']} / {p['b']} ({p['mm3']} mm³)" for p in designed) if designed else "none"), "",
      "## Tightest radial clearance to the bore (radius 27.4 mm)", "", "| part | outermost radius (mm) | clearance (mm) |", "|---|---|---|"]
md += [f"| {b['name']} | {b['r_max']:.2f} | {b['clearance_to_bore']:.2f} |" for b in bore[:10]]
md += ["", "## Control fins swept about the hinge", "", "| deflection | overlap with tube / stabilizers |", "|---|---|"]
md += [f"| {s_['defl_deg']:+d}° | {s_['overlap_mm3']} mm³ |" for s_ in sweep]
md += ["", "## Print bed (256 x 256 x 256 mm)", "", "| part | bounding box (mm) | fits |", "|---|---|---|"]
md += [f"| {b['part']} | {' x '.join(str(d) for d in b['dims_mm'])} | {'yes' if b['fits_256'] else 'NO'} |" for b in bed]
md += ["", "## Where each bought-part model came from", "", "| component | source |", "|---|---|"]
md += [f"| {k} | {v} |" for k, v in rep["sources"].items()]
md += ["", f"Nose ballast ({C.BALLAST_G:.0f} g steel shot + epoxy at ~5 g/cm³) fills the first {BALLAST_FILL:.0f} mm of the tip cavity."]
open(os.path.join(ASM, "FIT_REPORT.md"), "w").write("\n".join(md) + "\n")
print("wrote FIT_REPORT.md")
