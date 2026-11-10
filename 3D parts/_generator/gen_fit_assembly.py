#!/usr/bin/env python3
"""GTR70E WYVERN -- full fit-check assembly: every printed part plus every bought part, in place.

Bought parts come from two sources:
  vendor STEP  (3D parts/vendor/): Adafruit BNO085 4754, BME688 5046, microSD 4682, Feather
               RP2040 RFM form factor (5712 model; the 5714 RFM95 board shares the PCB outline,
               holes and RFM module footprint), Adafruit MPM3610 5 V buck (4739), Pololu 2810 MOSFET switch.
               Adafruit models: github.com/adafruit/Adafruit_CAD_Parts (MIT). Pololu: product pages.
  datasheet-built (no public model reachable): EMAX ES9251 II servo, AeroTech motor (29 x 83),
               2S LiPo, packed 24 in chute + shock cord, Adafruit 254 microSD (owned),
               perfboard parts, arm button + LED, nose ballast pour. Rev 3e prints the bypass tube
               (PC-FR), the cord anchor and the 1010 rail buttons (no metal recovery hardware).

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
rbs = step("13_rail_button_1010_printed_PETGCF_x2.step")
add("rail_button_printed_lower", rbs, "printed", PRINTED_COL["PETGCF"], "printed")
z_up = zx(C.X_RB_BOT) - 10.0
add("rail_button_printed_upper", rbs.translate((0, 0, z_up - (zx(C.X_MB_BOT) + 20))), "printed", PRINTED_COL["PETGCF"], "printed")

# ------------------------------------------------------------------ servos (datasheet-built EMAX ES9251 II)
sv = C.SERVO
zc = zx(C.X_CT_BOT) + C.SERVO_RING_Z
zh = zx(C.X_HINGE)
def x08():
    body = box(sv["H"], sv["W"], sv["L"], C.SERVO_BASE_R + sv["H"] / 2, 0, zc)
    ears = box(sv["ear_t"], sv["W"], sv["ear_span"], C.PAD_INNER_R - sv["ear_t"] / 2, 0, zc)
    spl = cyl_x(5.0, sv["spline_len"], C.SERVO_TOP_R, 0, zh)
    horn = cyl_x(sv["horn_disc_d"] - 0.1, 1.0, C.SPLINE_TOP_R, 0, zh)
    if sv.get("horn_type") == "arm":
        horn = horn.union(box(1.0, sv["horn_arm_w"] - 0.1, sv["horn_arm_L"] / 2, C.SPLINE_TOP_R + 0.5, 0, zh + sv["horn_arm_L"] / 4))
    return body.union(ears).union(spl), horn
s_body, s_horn = x08()
for a in (0, 90, 180, 270):
    add(f"EMAX_ES9251II_az{a}", rz(s_body, a), "servo", (0.12, 0.30, 0.75), f"datasheet-built ({sv['L']} x {sv['W']} x {sv['H']}, ears {sv['ear_span']}, VERIFY)")
    add(f"servo_horn_az{a}", rz(s_horn, a), "servo", (0.85, 0.85, 0.85), "datasheet-built (single-arm horn, in hub pocket)")

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
        add(bd["key"], place_board(shp, bd), "vendor", (0.05, 0.35, 0.55),
            f"vendor STEP {bd['step']}" + (" (same outline as the 3966)" if bd["key"] == "bmp388" else ""))
    elif bd["key"] == "battery":
        b = cq.Workplane("XY").box(bd["L"], bd["W"], 14.0).translate((bd["L"] / 2, bd["W"] / 2, 7.0))
        add("lipo_2S_450", place_board(b, bd), "cots", (0.85, 0.65, 0.10), "datasheet-built 57 x 30 x 14 (VERIFY on the owned pack)")
    elif bd["key"] == "perfboard":
        pb = cq.Workplane("XY").box(bd["L"], bd["W"], 1.6).translate((bd["L"] / 2, bd["W"] / 2, 0.8))
        add("perfboard_16x62", place_board(pb, bd), "cots", (0.55, 0.35, 0.15), "datasheet-built FR4 0.1 in perf")
        bk = cq.importers.importStep(os.path.join(VEND, "adafruit_4739_mpm3610_buck.step"))
        bk = bk.rotate((0, 0, 0), (0, 0, 1), 90)
        bb = bk.val().BoundingBox(); bk = bk.translate((-bb.xmin + 4.0, -bb.ymin + (bd["W"] - (bb.ymax - bb.ymin)) / 2, 1.6))
        add("adafruit_MPM3610_buck", place_board(bk, bd), "vendor", (0.10, 0.10, 0.12), "vendor STEP adafruit_4739 (Adafruit_CAD_Parts), logic rail")
        add("adafruit_MPM3610_buck_servo", place_board(bk.translate((36.0, 0, 0)), bd), "vendor", (0.10, 0.10, 0.12), "vendor STEP adafruit_4739, servo rail (rev 3f)")
        cap = cq.Workplane("YZ").workplane(offset=20.0).center(8.0, -3.4).circle(3.15).extrude(11.0)
        add("cap_470uF_under_board", place_board(cap, bd), "cots", (0.10, 0.10, 0.40), "datasheet-built 6.3 x 11 mm, under the perfboard")
    elif bd["key"] == "pico2w":
        # rev 4b: 1.0 mm PCB, 2.0 mm component envelope (RP2350, CYW43 can, flash), micro-USB 3.0 mm tall
        # at the lower end (local x = L is the lower end), solder stubs under the castellated edges
        pb = cq.Workplane("XY").box(bd["L"], bd["W"], 1.0).translate((bd["L"] / 2, bd["W"] / 2, 0.5))
        pb = pb.union(cq.Workplane("XY").box(bd["L"] - 8.0, bd["W"] - 5.0, 2.0).translate((bd["L"] / 2, bd["W"] / 2, 2.0)))
        pb = pb.union(cq.Workplane("XY").box(5.6, 8.0, 3.0).translate((bd["L"] - 5.6 / 2 + 1.0, bd["W"] / 2, 2.5)))
        for yy in (0.8, bd["W"] - 0.8):
            pb = pb.union(cq.Workplane("XY").box(bd["L"] - 6.0, 1.0, 1.0).translate((bd["L"] / 2, yy, -0.5)))
        add("pico2w", place_board(pb, bd), "cots", (0.10, 0.45, 0.20), "datasheet-built 51 x 21 mm Pico 2 W (Raspberry Pi datasheet)")

# Pololu 2810 in its wall cradle at +Y (rev 3e): component side out, knob under the wall slot
sw_ = C.SWITCH
sw = cq.importers.importStep(os.path.join(VEND, "pololu_2810_mini_mosfet_switch.step"))
sw = sw.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 180)        # x -> -X, y -> Z, z -> +Y
sw = sw.translate((sw_["size"] / 2, C.RI - 0.3 - sw_["h"], z0s + sw_["z0"]))
add("pololu_2810_switch", sw, "vendor", (0.10, 0.45, 0.20), "vendor STEP pololu_2810, in the CT wall cradle under the slot")

# rev 4: arm button (6 x 6 x 3.5 body + 3.5 mm plunger) and 3 mm LED in the -Y wall cradle
bt = C.BUTTON; zbt = z0s + bt["z0"] + bt["body"] / 2
btn = box(3.5, bt["body"], bt["body"], C.RI - 0.2 - 1.75, 0, zbt).union(cyl_x(bt["plunger_d"], 1.5, C.RI - 0.2, 0, zbt))
add("arm_button_6mm", rz(btn, 270), "cots", (0.20, 0.20, 0.22), "datasheet-built 6 x 6 tactile (Adafruit 367), plunger 0.3 mm under the skin")
led = cyl_x(bt["led_d"], 5.3, C.R - 0.5 - 5.3, 0, zbt + bt["led_dz"])
add("arm_led_3mm", rz(led, 270), "cots", (0.85, 0.10, 0.10), "datasheet-built 3 mm LED (SparkFun COM-00533)")

# ------------------------------------------------------------------ motor, bypass, recovery, hardware
mot = C.MOTORS[C.FLIGHT_MOTOR]
za = zx(C.X_MOTOR_AFT)
m = cylz(C.MOTOR_D / 2, za, mot["L"]).cut(cylz(5.0, za - 1, 14.0))
add(f"AeroTech_{C.FLIGHT_MOTOR}", m, "cots", (0.45, 0.20, 0.70), f"datasheet-built 29 x {mot['L']:.0f} mm (thrustcurve.org)")
zf = zx(C.X_RB_BOT)
# packed recovery: chute bundle under the nose shoulder, cord bundle above the floor (rev 4b: no Nomex)
zn = zx(C.X_RB_TOP) - C.NOSE["shoulder"]
add("chute_24in_packed", cylz(23.0, zn - 2 - 95.0, 95.0), "recovery", (0.95, 0.55, 0.10), "datasheet-built (Estes 24 in rip-stop, packed 46 x 95, VERIFY)")
add("shock_cord_bundle", cylz(11.0, zf + 22.0, 45.0, x=6.0), "recovery", (0.95, 0.85, 0.30), "datasheet-built 19 ft aramid, z-folded")
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
ALLOW = [("14_bypass_tube", "08_plenum"), ("14_bypass_tube", "03_rb_floor"),
         ("servo_horn", "servo_hub"), ("rail_button_printed", "04_control_tube"), ("rail_button_printed", "07_motor_bay"),
         ("rail_button_printed", "02_recovery"), ("rail_button_printed", "03_rb_floor"),
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
      f"## Tightest radial clearance to the bore (radius {C.RI:.1f} mm)", "", "| part | outermost radius (mm) | clearance (mm) |", "|---|---|---|"]
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
