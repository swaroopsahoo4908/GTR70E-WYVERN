#!/usr/bin/env python3
"""GTR70E WYVERN (fin-control revision) -- parametric CAD for every printed part.

All dimensions come from Simulations/wf_core.py (one source of truth). Parts are modelled in
ASSEMBLY coordinates: +Z is the long axis, nose up, z = L_TOTAL - x_station, so z = 0 is the
aft face of the motor bay. Slicers re-seat STLs on the bed, so assembly coordinates cost nothing
at print time and keep every exported part registered to every other part.

Outputs (folders relative to "3D parts/"):
  flight/               airframe, couplers, plenum, motor mount, servo hubs, IMU deck, FC pads
  control_fins/<prof>/  4 aerofoil blocks x 5 heights (RQ1 x RQ2 test matrix), PETG-CF
  wind_tunnel/          tunnel nose + tail fairings for the control-tube test article,
                        sting adapter, 228 mm junction-ring <-> 200 mm square adapters,
                        8 in duct-fan transition
  assembly/             full flight assembly STEP + STL, preview PNGs
  _generator/mass_report.json   printed-part masses + CG stations -> wf_core.mass_properties()

Fits are named, never accidental: FIT_SLIP (0.20 mm radial) for tube/coupler/disk slides, the
bypass tube runs in 13.5 mm clearance holes and seals with O-rings at both ends.
Hardware interfaces tagged VERIFY-WITH-CALIPERS (servo flange, Feather hole pattern, battery
outline) are typical-class figures for the purchased parts; confirm on the bench before the final
print run.
"""
import json, math, os, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Simulations"))
import wf_core as C
sys.path.insert(0, os.path.join(ROOT, "Simulations", "CFD"))
from airfoil_profiles import section_points

D3 = os.path.join(ROOT, "3D parts")
DIRS = {k: os.path.join(D3, k) for k in ("flight", "control_fins", "wind_tunnel", "assembly")}
for d in DIRS.values(): os.makedirs(d, exist_ok=True)

L = C.L_TOTAL
def zx(x):  # station (mm from nose tip) -> assembly z
    return L - x

M3_PILOT, M3_CLR, M2_PILOT, M2_CLR = 4.2, 3.4, 3.2, 2.4   # heat-set pilots / clearance (mm)
report = []

def save(shape, folder, name, mat, flight=True, qty=1, export=True):
    solid = shape.val() if isinstance(shape, cq.Workplane) else shape
    vol = solid.Volume() / 1000.0
    m = vol * C.DENS[mat]
    com = cq.Shape.centerOfMass(solid)
    bb = solid.BoundingBox()
    if export:
        p = os.path.join(folder, name)
        cq.exporters.export(shape, p + ".step")
        cq.exporters.export(shape, p + ".stl", tolerance=0.05, angularTolerance=0.2)
    report.append(dict(name=name, mat=mat, qty=qty, vol_cm3=round(vol, 2), mass_g=round(m * qty, 2),
                       x_cg_mm=round(L - com.z, 1), length_mm=round(bb.zlen, 1), flight=flight,
                       folder=os.path.relpath(folder, D3)))
    print(f"  {name:44s} {vol:8.2f} cm3 x{qty} {m*qty:7.1f} g  ({mat})  x_cg={L-com.z:6.1f}")
    return shape

# ------------------------------------------------------------------------------- primitives
def tube(ro, ri, z0, h):
    return cq.Workplane("XY").workplane(offset=z0).circle(ro).circle(ri).extrude(h)

def disk(r, z0, h):
    return cq.Workplane("XY").workplane(offset=z0).circle(r).extrude(h)

def cyl_x(d, length, x0, y=0.0, z=0.0):
    """cylinder along +X from x0"""
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(d / 2).extrude(length)

def radial_hole(d, z, az_deg, r_in=C.RI - 3, r_out=C.R + 3):
    return cyl_x(d, r_out - r_in, r_in, 0, z).rotate((0, 0, 0), (0, 0, 1), az_deg)

def box(dx, dy, dz, cx=0, cy=0, cz=0):
    return cq.Workplane("XY").box(dx, dy, dz).translate((cx, cy, cz))

def bypass_xy():
    a = math.radians(C.BYPASS["az_deg"]); r = C.BYPASS["r_center"]
    return r * math.cos(a), r * math.sin(a)

def bypass_hole(z0, h, d=13.5):
    bx, by = bypass_xy()
    return cq.Workplane("XY").workplane(offset=z0).center(bx, by).circle(d / 2).extrude(h)

def screw_ring(z, n=3, az0=0.0, d=M3_CLR):
    s = None
    for i in range(n):
        h = radial_hole(d, z, az0 + 360 * i / n)
        s = h if s is None else s.union(h)
    return s

# ------------------------------------------------------------------------------- nose cone
def nose():
    Ln, R, w = C.NOSE["L"], C.R, C.NOSE["wall"]
    rho = (R * R + Ln * Ln) / (2 * R)
    n = 60
    outer = []
    for i in range(n + 1):
        xx = Ln * i / n                     # from tip
        y = math.sqrt(max(rho * rho - (Ln - xx) ** 2, 0)) + R - rho
        outer.append((max(y, 0.0), zx(xx)))
    # profile: outer skin tip->base, then inner skin base->ballast-bay top, close on axis
    zb = zx(Ln)
    inner = [(max(r - w, 0.0), z) for (r, z) in outer]
    bay = C.NOSE["ballast_bay_L"]           # solid-capable tip region is just the hollow tip;
    prof = [(0.0, outer[0][1])] + outer[1:] + [(C.RI - C.FIT_SLIP - 0.0, zb)]
    # shoulder
    rs_o = C.RI - C.FIT_SLIP; rs_i = rs_o - 1.6; zs = zb - C.NOSE["shoulder"]
    prof += [(rs_o, zs), (rs_i, zs), (rs_i, zb - 3.0)]
    # inner skin back up to the ballast-bay ceiling (tip region left solid-walled hollow)
    for (r, z) in reversed(inner[8:]):
        prof.append((max(r, 0.8), z))
    prof.append((0.0, inner[8][1]))
    s = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    # shoulder floor bulkhead with shock-cord bar (closes the shoulder, 3 mm)
    floor = disk(rs_i + 0.5, zs, 3.0)
    bar_hole = box(16, 6, 3.2, 0, 0, zs + 1.5)
    floor = floor.cut(bar_hole)
    bar = box(22, 4, 4, 0, 0, zs + 5).union(box(4, 4, 6, -9, 0, zs + 3)).union(box(4, 4, 6, 9, 0, zs + 3))
    s = s.union(floor).union(bar)
    # ballast fill port (M8 grub-screw plug) into the tip void
    s = s.cut(cq.Workplane("XY").workplane(offset=zs - 1).circle(3.4).extrude(30))
    return save(s, DIRS["flight"], "01_nose_tangent_ogive_150_ASAAero", "ASAAERO")

# ------------------------------------------------------------------------------- recovery bay
def rb_tube():
    z0 = zx(C.X_RB_BOT)
    s = tube(C.R, C.RI, z0, C.L_RB)
    s = s.cut(screw_ring(z0 + 10, 3, 0))                    # into the RB-floor coupler
    return save(s, DIRS["flight"], "02_recovery_bay_tube_ASAAero", "ASAAERO")

def rb_floor_coupler():
    """Coupler between RB and CT with the gas-tight recovery-bay floor (3 mm) at the joint plane,
    the CENTRAL bypass-tube exit socket (O-ring groove), and an off-axis M5 eyebolt for the cord."""
    zj = zx(C.X_RB_BOT)
    ro = C.RI - C.FIT_SLIP; ri = ro - C.COUPLER_WALL
    s = tube(ro, ri, zj - C.COUPLER_L / 2, C.COUPLER_L)
    s = s.union(disk(ri + 0.1, zj - 1.5, 3.0))
    s = s.cut(screw_ring(zj + 10, 3, 0, M3_PILOT)).cut(screw_ring(zj - 10, 3, 60, M3_PILOT))
    # M5 eyebolt boss at r = 20 mm, az 180 (clear of the central exit)
    s = s.union(cq.Workplane("XY").workplane(offset=zj - 7).center(-20, 0).circle(5.5).extrude(6))
    s = s.cut(cq.Workplane("XY").workplane(offset=zj - 8).center(-20, 0).circle(2.6).extrude(12))
    # central bypass socket: boss under the floor, through-hole, O-ring groove
    s = s.union(cq.Workplane("XY").workplane(offset=zj - 14).circle(9.5).extrude(12))
    s = s.cut(cq.Workplane("XY").workplane(offset=zj - 16).circle(C.BYPASS["od"] / 2 + 0.15).extrude(25))
    s = s.cut(cq.Workplane("XY").workplane(offset=zj - 14.5).circle(C.BYPASS["od"] / 2 + 1.6).extrude(2.0))
    return save(s, DIRS["flight"], "03_rb_floor_coupler_PCFR", "PCFR")

# ------------------------------------------------------------------------------- control tube
def ct_tube():
    """Control tube. ONE servo ring: four KST X08 Plus servos, each bolted by its ears to a pad
    printed into the tube wall, output shaft radial through the wall into the fin hub. All four
    fins share one station. The bypass tube runs up the centre; the avionics spine (separate part)
    sits on the IMU deck above the ring. Vertical pads/corbels print without supports nose-up."""
    zb = zx(C.X_CT_BOT)
    s = tube(C.R, C.RI, zb, C.L_CT)
    sv = C.SERVO
    zc = zb + C.SERVO_RING_Z                       # servo body centre
    zh = zb + C.HINGE_Z                            # hinge / shaft station
    pad_h = sv["ear_span"] + 4.0
    depth = C.RI - C.PAD_INNER_R + 0.5
    for az in (0, 90, 180, 270):
        p = box(depth, 16.0, pad_h, C.PAD_INNER_R + depth / 2, 0, zc)
        p = p.intersect(disk(C.RI + 0.4, zc - pad_h, 2 * pad_h))
        p = p.cut(box(depth + 2, sv["W"] + 0.4, sv["L"] + 0.4, C.PAD_INNER_R + depth / 2, 0, zc))   # servo window
        for dz in (-sv["hole_pitch"] / 2, sv["hole_pitch"] / 2):
            p = p.cut(cyl_x(1.8, depth + 1, C.PAD_INNER_R - 0.5, 0, zc + dz))                       # M2 ear screws
        p = p.cut(cyl_x(C.CFIN["hub_flange_d"] + 1.0, C.RI - C.SPLINE_TOP_R + 0.8, C.SPLINE_TOP_R - 0.3, 0, zh))   # hub-flange pocket
        s = s.union(p.rotate((0, 0, 0), (0, 0, 1), az))
        s = s.cut(radial_hole(C.CFIN["hub_d"] + 0.4, zh, az))                                      # hub through the wall
    # IMU deck corbels
    zd = zb + C.IMU_DECK_Z
    for az in (45, 165, 285):
        cb = box(6, 8, 6, C.RI - 2.5, 0, zd - 3).rotate((0, 0, 0), (0, 0, 1), az)
        cb = cb.cut(cq.Workplane("XY").workplane(offset=zd - 7).center(C.RI - 2.5, 0).circle(M2_PILOT / 2).extrude(8).rotate((0, 0, 0), (0, 0, 1), az))
        s = s.union(cb.intersect(disk(C.RI + 0.4, zd - 7, 8)))
    # static ports for the BME688, screw-switch access over the +Y (power perfboard) spine face
    bme = [b for b in C.SPINE_BOARDS if b["key"] == "bme688"][0]
    perf = [b for b in C.SPINE_BOARDS if b["key"] == "perfboard"][0]
    for az in (20, 110, 200, 290):
        s = s.cut(radial_hole(1.2, zb + C.SPINE_Z0 + bme["z0"] + bme["L"] / 2, az))
    s = s.cut(radial_hole(3.0, zb + C.SPINE_Z0 + perf["z0"] + C.SCREW_SWITCH_V, 90))
    s = s.cut(screw_ring(zb + C.L_CT - 10, 3, 60)).cut(screw_ring(zb + 10, 3, 30))
    return save(s, DIRS["flight"], "04_control_tube_servo_ring_ASAAero", "ASAAERO")

def imu_deck():
    """Spine deck above the servo ring (the BNO085 moved onto the spine in rev 3): central hole
    for the bypass tube, four diagonal slots that carry the servo leads up, a square socket that
    locates the avionics spine, three M2 holes onto the corbels."""
    zd = zx(C.X_CT_BOT) + C.IMU_DECK_Z
    s = disk(C.RI - C.FIT_SLIP, zd, 2.5)
    s = s.cut(cq.Workplane("XY").workplane(offset=zd - 1).circle(C.BYPASS["od"] / 2 + 0.4).extrude(5))
    for az in (45, 135, 225, 315):
        s = s.cut(cq.Workplane("XY").workplane(offset=zd - 1).center(17.0, 0).rect(9, 5).extrude(5).rotate((0, 0, 0), (0, 0, 1), az))
    for az in (45, 165, 285):
        s = s.cut(cq.Workplane("XY").workplane(offset=zd - 1).center(C.RI - 2.5, 0).circle(M2_CLR / 2).extrude(5).rotate((0, 0, 0), (0, 0, 1), az))
    f = C.SPINE_FLAT
    sq = cq.Workplane("XY").workplane(offset=zd + 2.5).rect(2 * f + 4, 2 * f + 4).extrude(3)
    sq = sq.cut(cq.Workplane("XY").workplane(offset=zd + 2).rect(2 * f + 0.3, 2 * f + 0.3).extrude(5))
    s = s.union(sq)
    return save(s, DIRS["flight"], "05_spine_deck_PETGCF", "PETGCF")

FACE_AZ = dict(px=0, py=90, nx=180, ny=270)

def avionics_spine():
    """Square sleeve around the central bypass tube, faces SPINE_FLAT off-axis. Every board in
    wf_core.SPINE_BOARDS gets standoffs or pillars up to its face's BOARD_PLANE, at the hole grid
    read from the vendor STEP. Board planes keep every corner clear of its neighbours inside the
    27.4 mm bore (gen_fit_assembly.py checks it with the vendor models in place).
      +X BNO085 (lowest, nearest the fins) + Feather RP2040 RFM95, 2 mm standoffs
      -X 2S LiPo on foam tape, two strap slots
      +Y 16 x 60 mm power perfboard on 9 mm pillars (screw switch under the wall hole)
      -Y BME688 + 3V microSD on 9 mm pillars
    A 3-spoke spider at the top keeps it centred in the bore."""
    z0 = zx(C.X_CT_BOT) + C.SPINE_Z0
    f = C.SPINE_FLAT; bore = C.BYPASS["od"] / 2 + 0.3; BP = C.BOARD_PLANE
    s = cq.Workplane("XY").workplane(offset=z0).rect(2 * f, 2 * f).extrude(C.SPINE_L)
    s = s.cut(cq.Workplane("XY").workplane(offset=z0 - 1).circle(bore).extrude(C.SPINE_L + 2))
    for az in (0, 90, 270):           # lightening windows (the battery face stays solid)
        s = s.cut(box(4, 6, C.SPINE_L - 20, f, 0, z0 + C.SPINE_L / 2).rotate((0, 0, 0), (0, 0, 1), az))
    for bd in C.SPINE_BOARDS:
        az = FACE_AZ[bd["face"]]; h = C.board_plane(bd) - f
        for (u, v) in bd["holes"]:          # u across the face (from the board's edge), v along the axis
            t = u - bd["W"] / 2 + bd.get("offset", 0.0); zz = z0 + bd["z0"] + v
            post = cyl_x(5.0 if h < 4 else 4.0, h + 0.2, f - 0.2, t, zz)
            pil = cyl_x(1.7, h + 2.5, f - 2.0, t, zz)
            s = s.union(post.rotate((0, 0, 0), (0, 0, 1), az)).cut(pil.rotate((0, 0, 0), (0, 0, 1), az))
        if bd["face"] == "nx":
            for zz in (bd["z0"] + 6, bd["z0"] + bd["L"] - 6):
                s = s.cut(box(4.0, 2 * f + 2, 4.0, -f + 1.0, 0, z0 + zz))
    spider = cq.Workplane("XY").workplane(offset=z0 + C.SPINE_L).circle(C.RI - C.FIT_SLIP).circle(C.RI - C.FIT_SLIP - 1.6).extrude(3)
    for az in (45, 165, 285):
        spider = spider.union(box(C.RI - f, 3, 3, (C.RI + f) / 2 - 1, 0, z0 + C.SPINE_L + 1.5).rotate((0, 0, 0), (0, 0, 1), az))
    s = s.union(spider)
    s = s.union(cq.Workplane("XY").workplane(offset=z0 + C.SPINE_L).rect(2 * f, 2 * f).extrude(3)
                .cut(cq.Workplane("XY").workplane(offset=z0 + C.SPINE_L - 1).circle(bore).extrude(6)))
    return save(s, DIRS["flight"], "05b_avionics_spine_PETGCF", "PETGCF")

def servo_hub():
    """Servo-to-fin hub. Flange pocket captures the servo's round horn (2 x M2), D-flat 8 mm shaft
    passes the wall, M2 cross-pin locks the fin's root boss. Modelled at az 0; all four identical."""
    zc = zx(C.X_HINGE)
    sp = C.SPLINE_TOP_R
    fl = cyl_x(C.CFIN["hub_flange_d"], C.HUB_FLANGE_T, sp)
    pocket = cyl_x(11.5, 1.2, sp - 0.1)                           # horn disc pocket (VERIFY)
    r_root = C.R + C.CFIN["gap"]; hub_end = r_root + C.CFIN["root_boss_L"] - 1.0   # stops 0.2 short of the bore bottom
    sh = cyl_x(C.CFIN["hub_d"], hub_end - (sp + C.HUB_FLANGE_T), sp + C.HUB_FLANGE_T)
    s = fl.cut(pocket).union(sh)
    s = s.cut(box(12, 3, 12, hub_end - 4.0, C.CFIN["hub_d"] / 2 + 0.5, 0))      # D-flat (1 mm)
    s = s.cut(cyl_x(2.2, 20, sp - 1))                                 # servo screw access bore
    for hy in (-3.5, 3.5):
        s = s.cut(cyl_x(M2_CLR, 4, sp - 1, hy, 0))
    s = s.cut(cq.Workplane("XY").workplane(offset=-6).center(r_root + 3.0, 0).circle(1.1).extrude(12))
    s = s.translate((0, 0, zc))
    return save(s, DIRS["flight"], "06_servo_hub_PETGCF_x4", "PETGCF", qty=4)

# ------------------------------------------------------------------------------- motor bay
def mb_tube():
    zt = zx(C.X_MB_TOP)
    zb = zx(C.X_MB_BOT)
    s = tube(C.R, C.RI, zb, C.L_MB)
    # integral forward shoulder into the CT (20 mm)
    ro = C.RI - C.FIT_SLIP
    s = s.union(tube(ro, ro - 1.8, zt, C.COUPLER_L / 2))
    s = s.cut(screw_ring(zt + 10, 3, 30, M3_PILOT))
    # through-the-wall fin slots
    rf = C.RECT_FIN
    zle = zx(C.X_RECT_LE)
    for i in range(4):
        az = rf["az0_deg"] + 90 * i
        sl = box(10, rf["t"] + 0.3, rf["root"] - 20, C.R - 3, 0, zle - rf["root"] / 2).rotate((0, 0, 0), (0, 0, 1), az)
        s = s.cut(sl)
    # lower rail-button boss (internal pad, 1010 button #8 screw)
    zbtn = zb + 20
    pad_ = box(5, 12, 14, C.RI - 1.5, 0, zbtn).rotate((0, 0, 0), (0, 0, 1), C.RAIL_BUTTON_AZ_DEG)
    s = s.union(pad_.intersect(disk(C.RI + 0.5, zbtn - 8, 16)))
    s = s.cut(radial_hole(3.5, zbtn, C.RAIL_BUTTON_AZ_DEG, C.RI - 6))
    s = s.cut(screw_ring(zb + 2, 4, 0, M3_CLR))   # retainer cap screws pass the MB wall into the aft ring
    return save(s, DIRS["flight"], "07_motor_bay_tube_ASAAero", "ASAAERO")

def plenum():
    """Plenum bulkhead (PC-FR). The motor's ejection charge vents through the MMT's thrust ring
    (25 mm bore) into a 6 mm full-bore gas gallery under this disk; 4 posts carry the motor
    thrust from the MMT ring into the disk, and the gallery feeds the central bypass socket on the vehicle axis.
    The ~18 cm3 gallery is deliberate: it caps the pressure spike (and the motor kick-out load)
    that a tight plenum would produce -- see Simulations/wf_bypass.py."""
    zt = zx(C.X_PLENUM_TOP)
    z0 = zt - C.PLENUM_T
    ro = C.RI - C.FIT_SLIP
    s = disk(ro, z0, C.PLENUM_T)
    gh = C.GALLERY_H
    for az in (0, 90, 180, 270):
        post = cq.Workplane("XY").workplane(offset=z0 - gh + 4.0).center(14.6, 0).circle(3.0).extrude(gh - 4.0)   # lands on the MMT stand-off ring (MMT top + 2 mm ring)
        s = s.union(post.rotate((0, 0, 0), (0, 0, 1), az + 22.5))
    # 14 mm skirt bonded to the MB bore: spreads the gallery pressure load into the tube wall
    s = s.union(tube(ro, ro - 2.0, zt, 14.0))
    bx, by = bypass_xy()
    s = s.cut(cq.Workplane("XY").workplane(offset=z0 - 1).center(bx, by).circle(C.BYPASS["id"] / 2).extrude(C.PLENUM_T + 2))
    s = s.cut(cq.Workplane("XY").workplane(offset=zt - 4).center(bx, by).circle(C.BYPASS["od"] / 2 + 0.15).extrude(5))
    s = s.cut(cq.Workplane("XY").workplane(offset=zt - 3.4).center(bx, by).circle(C.BYPASS["od"] / 2 + 1.6).extrude(2.4))   # AS568-012 gland
    s = s.cut(screw_ring(z0 + C.PLENUM_T / 2, 3, 0, 2.6))
    return save(s, DIRS["flight"], "08_plenum_bulkhead_PCFR", "PCFR")

def mmt():
    zt = zx(C.X_MOTOR_TOP) + 2.0
    zb = zx(C.X_MOTOR_AFT)
    s = tube(C.MMT_ID / 2 + C.MMT_WALL, C.MMT_ID / 2, zb, zt - zb)
    # forward stand-off ring (gallery spacer) between motor cap and plenum
    s = s.union(tube(C.MMT_ID / 2 + C.MMT_WALL, 12.5, zt, 2.0))
    # aft centring ring (integral) + retainer bosses
    ring = tube(C.RI - C.FIT_SLIP, C.MMT_ID / 2 + 0.5, zb, 4.0)
    for az in (0, 90, 180, 270):    # lightening holes between the fin tabs
        ring = ring.cut(cq.Workplane("XY").workplane(offset=zb - 1).center((C.RI + C.MMT_ID / 2 + C.MMT_WALL) / 2, 0).circle(3.2).extrude(6).rotate((0, 0, 0), (0, 0, 1), az))
    s = s.union(ring)
    rf = C.RECT_FIN
    zle = zx(C.X_RECT_LE)
    for i in range(4):
        az = rf["az0_deg"] + 90 * i
        s = s.cut(box(4, rf["t"] + 0.3, rf["root"] - 20, C.MMT_ID / 2 + C.MMT_WALL + 0.5, 0, zle - rf["root"] / 2).rotate((0, 0, 0), (0, 0, 1), az))
        # aft ring notch for the tab
        s = s.cut(box(C.RI - 16, rf["t"] + 0.3, 7, (C.RI + 16) / 2, 0, zb + 3).rotate((0, 0, 0), (0, 0, 1), az))
    return save(s, DIRS["flight"], "09_motor_mount_tube_aft_ring_PCFR", "PCFR")

def retainer():
    zb = zx(C.X_MOTOR_AFT)
    # aft flange (motor nozzle lip, 24 mm bore) + 8 mm collar OUTSIDE the MB tube
    s = tube(C.R + 2.2, 12.0, zb - 3.0, 3.0).union(tube(C.R + 2.2, C.R + 0.2, zb, 8.0))
    for az in (0, 90, 180, 270):   # 4 x M3 through collar + MB wall into heat-set inserts in the MMT aft ring
        s = s.cut(radial_hole(M3_CLR, zb + 2, az, C.R - 1, C.R + 4))
    for i in range(4):             # slots so the collar slides over the stabilizer roots (fit check)
        s = s.cut(box(4.0, C.RECT_FIN["t"] + 0.6, 9.0, C.R + 1.2, 0, zb + 4.5).rotate((0, 0, 0), (0, 0, 1), C.RECT_FIN["az0_deg"] + 90 * i))
    return save(s, DIRS["flight"], "10_motor_retainer_cap_PCFR", "PCFR")

def f15_spacer():
    z = zx(C.X_MOTOR_TOP)
    s = tube(14.6, 10.0, z - 10.0, 10.0)
    return save(s, DIRS["flight"], "11_F15_spacer_ring_10mm_PCFR", "PCFR", flight=False)

def rect_fin(i=0, export=True):
    rf = C.RECT_FIN
    zle = zx(C.X_RECT_LE)
    t, c, sp = rf["t"], rf["root"], rf["span"]
    r0 = C.R
    blade = box(sp, t, c, r0 + sp / 2, 0, zle - c / 2)
    try:
        blade = blade.edges("|Y").fillet(1.2)
    except Exception:
        pass
    tab_r0 = C.MMT_ID / 2 + C.MMT_WALL + 0.2
    tab = None
    for zc in (zle - 25.0, zle - c + 25.0):      # two 30 mm through-the-wall tabs, not a full-length tab
        tb_ = box(r0 - tab_r0 + 0.5, t, 30.0, (r0 + tab_r0) / 2, 0, zc)
        tab = tb_ if tab is None else tab.union(tb_)
    s = blade.union(tab).rotate((0, 0, 0), (0, 0, 1), rf["az0_deg"] + 90 * i)
    return save(s, DIRS["flight"], "12_rect_fin_PETGCF_x4", "PETGCF", qty=4, export=export) if (i == 0 and export) else s

def rail_button_spacer():
    zb = zx(C.X_MB_BOT) + 20
    s = cyl_x(11.0, C.RAIL_BUTTON_STANDOFF + 0.6, C.R - 0.6).cut(cyl_x(4.0, 6, C.R - 2)).translate((0, 0, zb))
    s = s.cut(cq.Workplane("XY").workplane(offset=zb - 10).circle(C.R).extrude(20))     # saddle: underside follows the tube
    s = s.rotate((0, 0, 0), (0, 0, 1), C.RAIL_BUTTON_AZ_DEG)
    return save(s, DIRS["flight"], "13_rail_button_spacer_PETGCF_x2", "PETGCF", qty=2)

def upper_rail_pad():
    """Upper 1010 button lands in the RB-floor coupler overlap (5.0 mm of wall + coupler)."""
    pass

# ------------------------------------------------------------------------------- control fins
def control_fin(profile, H, az=0.0, x_hinge=None, export=True, folder=None):
    c = C.CFIN["root"]; hf = C.CFIN["hinge_frac"]
    x_hinge = C.X_HINGE_A if x_hinge is None else x_hinge
    zh = zx(x_hinge)
    z_le, z_te = zh + hf * c, zh - (1 - hf) * c
    r_root = C.R + C.CFIN["gap"]
    secs = []
    spans = [0.0, 0.25, 0.5, 0.75, 0.93]
    wires = []
    for f in spans:
        sp = f * H
        cl = max(c * (1 - f), 4.0)
        zl = z_te + cl
        pts = section_points(profile, cl, n=36)     # (u along chord from LE, y thickness)
        plane = cq.Plane(origin=(r_root + sp, 0, zl), xDir=(0, 0, -1), normal=(1, 0, 0))
        w = cq.Workplane(plane).polyline(pts).close()
        wires.append(w.val())
    # loft through the section wires
    solid = cq.Solid.makeLoft([cq.Wire.assembleEdges(wr.Edges()) if not isinstance(wr, cq.Wire) else wr for wr in wires], True)
    s = cq.Workplane("XY").add(solid)
    # root boss with D-bore + cross-pin hole
    boss = cyl_x(C.CFIN["root_boss_d"], C.CFIN["root_boss_L"], r_root).translate((0, 0, zh))
    s = s.union(boss)
    s = s.cut(cyl_x(C.CFIN["hub_d"] + 0.25, C.CFIN["root_boss_L"] - 0.8, r_root - 0.1).translate((0, 0, zh)))
    s = s.union(box(C.CFIN["root_boss_L"] - 0.8, 2.0, 10, r_root + (C.CFIN["root_boss_L"] - 0.8) / 2, C.CFIN["hub_d"] / 2 + 0.1, zh).intersect(   # key sits 0.1 off the hub D-flat
        cyl_x(C.CFIN["root_boss_d"], C.CFIN["root_boss_L"], r_root).translate((0, 0, zh))))
    s = s.cut(cq.Workplane("XY").workplane(offset=zh - 8).center(r_root + 3.0, 0).circle(1.1).extrude(16))
    s = s.rotate((0, 0, 0), (0, 0, 1), az)
    if export:
        fold = folder or os.path.join(DIRS["control_fins"], profile)
        os.makedirs(fold, exist_ok=True)
        return save(s, fold, f"cfin_{profile}_H{int(H)}_PETGCF", "PETGCF", flight=False, qty=4)
    return s

# ------------------------------------------------------------------------------- wind tunnel
WT = dict(ts_w=200.0, ts_h=200.0, ts_L=750.0, ring_od=228.0, ring_id=202.0, sting_d=12.0)

def wt_parts():
    """Tunnel-only parts. The test article is the REAL control tube (servos, hubs, fins, IMU)
    with a short ogive nose and a boat-tail fairing that carries the sting socket."""
    out = os.path.join(DIRS["wind_tunnel"])
    # nose fairing (100 mm tangent ogive) with 20 mm shoulder into the CT top
    Ln = 100.0; R = C.R; rho = (R * R + Ln * Ln) / (2 * R)
    pts = [(0.0, Ln)]
    for i in range(1, 41):
        xx = Ln * i / 40
        y = math.sqrt(max(rho * rho - (Ln - xx) ** 2, 0)) + R - rho
        pts.append((y, Ln - xx))
    ro = C.RI - C.FIT_SLIP
    outer = pts + [(ro, 0.0), (ro, -20.0), (0.0, -20.0)]
    s = cq.Workplane("XZ").polyline(outer).close().revolve(360, (0, 0, 0), (0, 1, 0))
    inner = [(0.0, Ln - 12)] + [(max(r - 2.0, 0.5), z) for (r, z) in pts[6:]] + [(ro - 2.0, 0.0), (ro - 2.0, -21.0), (0.0, -21.0)]
    s = s.cut(cq.Workplane("XZ").polyline(inner).close().revolve(360, (0, 0, 0), (0, 1, 0)))
    save(s, out, "WT_nose_fairing_ogive100_ASA", "ASA", flight=False)
    # tail fairing: 20 mm shoulder into the CT aft end, 80 mm boat-tail 70 -> 30, sting socket
    pts = [(ro - 2, 20.0), (ro, 20.0), (ro, 0.0), (R, 0.0), (15.0, -80.0), (0.0, -80.0), (0.0, 18.0)]
    s = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
    hollow = [(ro - 2.0, 21.0), (ro - 2.0, -2.0), (R - 2.5, -2.0), (13.0, -62.0), (0.0, -62.0), (0.0, 21.0)]
    s = s.cut(cq.Workplane("XZ").polyline(hollow).close().revolve(360, (0, 0, 0), (0, 1, 0)))
    s = s.union(cq.Workplane("XY").workplane(offset=-80).circle(WT["sting_d"] / 2 + 3.0).extrude(40))   # sting boss
    s = s.cut(cq.Workplane("XY").workplane(offset=-81).circle(WT["sting_d"] / 2 + 0.1).extrude(60))
    s = s.cut(screw_ring(-40, 2, 0, M3_PILOT))
    save(s, out, "WT_tail_fairing_sting_socket_ASA", "ASA", flight=False)
    # junction-ring adapter: Jerrod's 228 mm square module flange -> 200 x 200 test-section frame
    sq = cq.Workplane("XY").rect(WT["ring_od"], WT["ring_od"]).extrude(12)
    sq = sq.cut(cq.Workplane("XY").rect(WT["ts_w"], WT["ts_h"]).extrude(12))
    for (x, y) in ((-104, -104), (104, -104), (-104, 104), (104, 104)):
        sq = sq.cut(cq.Workplane("XY").center(x * 0.95, y * 0.95).circle(2.75).extrude(12))
    save(sq, out, "WT_adapter_228sq_to_200sq_x2_PETG", "PETGCF", flight=False, qty=2)
    # sting strut fairing (NACA 0020-ish, 40 mm chord) for the floor-mounted sting
    from airfoil_profiles import section_points as sp_
    pts = sp_("NACA0012", 40.0, n=30)
    pts = [(u, y * 1.6) for (u, y) in pts]
    s = cq.Workplane("XY").polyline(pts).close().extrude(110)
    s = s.cut(cq.Workplane("XY").center(14, 0).circle(WT["sting_d"] / 2 + 0.6).extrude(110))
    save(s, out, "WT_strut_fairing_ASA", "ASA", flight=False)
    # 200 sq -> 8 in (203 mm) round transition for the AC Infinity Cloudline T8, 150 mm long
    a = cq.Workplane("XY").rect(WT["ts_w"] + 6, WT["ts_h"] + 6).workplane(offset=150).circle(106.5).loft()
    b = cq.Workplane("XY").rect(WT["ts_w"], WT["ts_h"]).workplane(offset=150).circle(101.6).loft()
    save(a.cut(b), out, "WT_diffuser_200sq_to_8in_round_PETG", "PETGCF", flight=False)

def wt_phase_a():
    """Phase A: single-fin half-model in the STOCK 100 x 100 mm test section. The flight fin, hub
    and a KST X08 Plus sit on a reflection-plane wall panel; the servo hangs outside the tunnel
    on a cradle carried by two 100 g load cells (normal force + centre of pressure).
    The fin root sits 1.0 mm off the panel, the same gap as on the airframe, and the servo spline
    sits as far behind the airflow face as it does behind the flight wall (R - SPLINE_TOP_R),
    so the flight hub fits."""
    out = os.path.join(DIRS["wind_tunnel"])
    sv = C.SERVO
    # reflection-plane wall panel, 175 x 100 x 4 (replaces one side wall of the stock section)
    t = 4.0
    p = cq.Workplane("XY").box(175.0, 100.0, t).translate((0, 0, -t / 2))   # airflow face at z = 0
    p = p.cut(cq.Workplane("XY").workplane(offset=-t - 1).circle(C.CFIN["hub_d"] / 2 + 1.0).extrude(t + 2))
    for (x, y) in ((-80, -42), (80, -42), (-80, 42), (80, 42)):          # VERIFY against Jerrod part 4
        p = p.cut(cq.Workplane("XY").workplane(offset=-t - 1).center(x, y).circle(M3_CLR / 2).extrude(t + 2))
    # leading-edge bevel on the upstream end keeps the plate boundary layer thin (plate LE at x = -87.5)
    p = p.cut(cq.Workplane("XZ").polyline([(-88, 0.01), (-88, -t - 0.1), (-80, -t - 0.1)]).close().extrude(60, both=True))
    save(p, out, "WTA_reflection_plane_wall_panel_PETG", "PETGCF", flight=False)
    # servo cradle: the flight pad geometry (ears on a pad, servo top through a window),
    # floating on two TAL221 100 g cells 60 mm apart along the chord.
    # Distances behind the airflow face copy the flight wall exactly (R - r): spline tip, servo top,
    # ear plane, servo base -> the flight hub and fin fit unchanged.
    zc = -(C.R - C.PAD_INNER_R)                       # ear plane (ears bear on the pad's lower face)
    z_base = -(C.R - C.SERVO_BASE_R)
    pad = cq.Workplane("XY").box(sv["ear_span"] + 6, 16.0, 4.0).translate((0, 0, zc + 2.0))
    pad = pad.cut(cq.Workplane("XY").box(sv["L"] + 0.4, sv["W"] + 0.4, 10).translate((0, 0, zc + 2.0)))
    for dx in (-sv["hole_pitch"] / 2, sv["hole_pitch"] / 2):
        pad = pad.cut(cq.Workplane("XY").workplane(offset=zc - 2).center(dx, 0).circle(0.9).extrude(8))
    base = cq.Workplane("XY").box(90.0, 24.0, 5.0).translate((0, 0, z_base - 3.0))
    for dx in (-30, 30):                                                  # cell end blocks: 2 x M3 each (VERIFY TAL221)
        for dy in (-2.5, 2.5):
            base = base.cut(cq.Workplane("XY").workplane(offset=z_base - 7).center(dx, dy * 2).circle(M3_CLR / 2).extrude(8))
    legs = None
    for dx in (-(sv["ear_span"] + 6) / 2 + 3, (sv["ear_span"] + 6) / 2 - 3):
        lg = cq.Workplane("XY").box(6.0, 16.0, zc - (z_base - 0.5)).translate((dx, 0, (zc + z_base - 0.5) / 2))
        legs = lg if legs is None else legs.union(lg)
    cr = pad.union(legs).union(base)
    save(cr, out, "WTA_servo_balance_cradle_PETG", "PETGCF", flight=False)
    # stock section exit -> 8 in round for the Cloudline T8 (250 mm long, 100 sq -> 203 round)
    a_ = cq.Workplane("XY").rect(106, 106).workplane(offset=250).circle(106.5).loft()
    b_ = cq.Workplane("XY").rect(100, 100).workplane(offset=250).circle(101.6).loft()
    save(a_.cut(b_), out, "WTA_diffuser_100sq_to_8in_round_PETG", "PETGCF", flight=False)

def wt_phase_b():
    """Phase B: full four-fin control tube + a removable stabilizer tail in the 200 x 200 section.
    The tail section reproduces the airframe from the control-tube aft end to the stabilizer
    trailing edge, with four through-the-wall slots so the flight-pattern stabilizer blades
    (any span) can be fitted or removed between runs. Slot plugs close the wall when the
    blades are off, so the body stays the same."""
    out = os.path.join(DIRS["wind_tunnel"])
    rf = C.RECT_FIN
    L_tail = (C.X_RECT_LE + rf["root"]) - C.X_CT_BOT + 4.0                 # CT aft end -> stab TE + 4
    ro = C.RI - C.FIT_SLIP
    s = tube(C.R, C.RI, -L_tail, L_tail).union(tube(ro, ro - 2.0, 0.0, 20.0))   # 20 mm shoulder into the CT
    z_le = -(C.X_RECT_LE - C.X_CT_BOT)
    for i in range(4):
        az = rf["az0_deg"] + 90 * i
        for zc in (z_le - 25.0, z_le - rf["root"] + 25.0):
            s = s.cut(box(6.0, rf["t"] + 0.3, 30.4, C.R - 1.0, 0, zc).rotate((0, 0, 0), (0, 0, 1), az))
        # internal M3 boss between the two tabs to pin the blade
        s = s.union(box(5.0, 8.0, 8.0, C.RI - 2.0, 0, z_le - rf["root"] / 2).rotate((0, 0, 0), (0, 0, 1), az).intersect(disk(C.RI + 0.3, -L_tail, L_tail)))
        s = s.cut(radial_hole(M3_PILOT, z_le - rf["root"] / 2, az, C.RI - 6, C.R + 2))
    s = s.cut(screw_ring(10.0, 3, 30))
    save(s, out, "WTB_stabilizer_tail_section_ASA", "ASA", flight=False)
    # blade for the tunnel: flight planform, two 30 mm tabs that stop at the inner wall, M3 pin hole
    blades = {}
    for sp in C.STAB_SPANS_WT:
        bl = box(sp, rf["t"], rf["root"], C.R + sp / 2, 0, -rf["root"] / 2)
        for zc in (-25.0, -rf["root"] + 25.0):
            bl = bl.union(box(C.R - C.RI + 0.4, rf["t"], 30.0, (C.R + C.RI) / 2 - 0.2, 0, zc))
        bl = bl.cut(cq.Workplane("XZ").workplane(offset=-5).center(C.R + 4.0, -rf["root"] / 2).circle(M3_CLR / 2).extrude(10))
        save(bl, out, f"WTB_stabilizer_blade_span{int(sp)}_PETGCF_x4", "PETGCF", flight=False, qty=4)
    plug = box(5.6, rf["t"], 30.0, C.R - 1.0, 0, -15.0)
    save(plug, out, "WTB_slot_plug_x8_PETG", "PETGCF", flight=False, qty=8)

# ------------------------------------------------------------------------------- run
if __name__ == "__main__":
    only_mass = "--mass-only" in sys.argv
    print("== flight parts")
    parts = {}
    parts["nose"] = nose()
    parts["rb"] = rb_tube()
    parts["rbc"] = rb_floor_coupler()
    parts["ct"] = ct_tube()
    parts["imu"] = imu_deck()
    parts["spine"] = avionics_spine()
    hub = servo_hub()
    parts["mb"] = mb_tube()
    parts["plenum"] = plenum()
    parts["mmt"] = mmt()
    parts["ret"] = retainer()
    # F15 spacer retired in rev 3 (83 mm F67 case)
    fin0 = rect_fin(0)
    rail_button_spacer()
    print("== control fins (flight copy at nominal H)")
    cf = [control_fin("NACA0006", C.CFIN_H_NOMINAL, az, xh, export=False)
          for az, xh in ((0, C.X_HINGE_A), (180, C.X_HINGE_A), (90, C.X_HINGE_B), (270, C.X_HINGE_B))]
    vol = sum(c.val().Volume() for c in cf) / 1000
    com_z = sum(cq.Shape.centerOfMass(c.val()).z * c.val().Volume() for c in cf) / sum(c.val().Volume() for c in cf)
    report.append(dict(name=f"control fins x4 (NACA0006 H{int(C.CFIN_H_NOMINAL)}, nominal)", mat="PETGCF", qty=4,
                       vol_cm3=round(vol, 2), mass_g=round(vol * C.DENS["PETGCF"], 2),
                       x_cg_mm=round(L - com_z, 1), length_mm=60.0, flight=True, folder="control_fins"))
    if not only_mass:
        print("== RQ1 x RQ2 fin matrix")
        for prof in C.CFIN_PROFILES:
            for H in C.CFIN_HEIGHTS + C.CFIN_FLIGHT_EXTRA:
                control_fin(prof, H)
        print("== wind tunnel")
        wt_parts()
        wt_phase_a()
        wt_phase_b()
    # assembly (flight config)
    print("== assembly")
    hubs = [hub.rotate((0, 0, 0), (0, 0, 1), a) for a in (0, 90, 180, 270)]
    fins = [rect_fin(i, export=False) for i in range(4)]
    asm = cq.Assembly(name="GTR70E_WYVERN_fin")
    cols = dict(nose=(0.95, 0.95, 0.95), rb=(0.9, 0.9, 0.92), rbc=(0.2, 0.2, 0.2), ct=(0.25, 0.25, 0.28), spine=(0.15, 0.5, 0.25),
                imu=(0.2, 0.2, 0.2), mb=(0.25, 0.25, 0.28), plenum=(0.85, 0.85, 0.8), mmt=(0.85, 0.85, 0.8),
                ret=(0.85, 0.85, 0.8))
    for k, p in parts.items():
        asm.add(p, name=k, color=cq.Color(*cols.get(k, (0.5, 0.5, 0.5))))
    for i, h in enumerate(hubs): asm.add(h, name=f"hub{i}", color=cq.Color(0.1, 0.1, 0.1))
    for i, f in enumerate(fins): asm.add(f, name=f"rfin{i}", color=cq.Color(0.1, 0.1, 0.1))
    for i, f in enumerate(cf): asm.add(f, name=f"cfin{i}", color=cq.Color(0.75, 0.2, 0.15))
    bx, by = bypass_xy()
    bp = cq.Workplane("XY").workplane(offset=zx(C.X_BYPASS_BOT)).center(bx, by).circle(C.BYPASS["od"] / 2).circle(C.BYPASS["id"] / 2).extrude(C.BYPASS["L"])
    asm.add(bp, name="bypass_tube_Al", color=cq.Color(0.7, 0.7, 0.75))
    # servo envelopes (for interference checks): one ring, four servos
    sv = C.SERVO
    zc = zx(C.X_CT_BOT) + C.SERVO_RING_Z
    for ax in (0, 90, 180, 270):
        body = box(sv["H"], sv["W"], sv["L"], C.SERVO_BASE_R + sv["H"] / 2, 0, zc)
        ears = box(sv["ear_t"], sv["W"], sv["ear_span"], C.PAD_INNER_R - sv["ear_t"] / 2 - 0.05, 0, zc)
        spl = cyl_x(5.0, sv["spline_len"] - 0.1, C.SERVO_TOP_R, 0, zx(C.X_HINGE))
        env = body.union(ears).union(spl).rotate((0, 0, 0), (0, 0, 1), ax)
        asm.add(env, name=f"servo_{ax}", color=cq.Color(0.15, 0.35, 0.7))
    asm.save(os.path.join(DIRS["assembly"], "GTR70E_WYVERN_fin_assembly.step"))
    comp = asm.toCompound()
    cq.exporters.export(cq.Workplane().add(comp), os.path.join(DIRS["assembly"], "GTR70E_WYVERN_fin_assembly.stl"), tolerance=0.1, angularTolerance=0.3)
    # interference check: servo envelopes vs bypass tube and vs each other
    print("== interference checks")
    names = [n for n in asm.children]
    def shp(n): return asm.objects[n].obj.val() if hasattr(asm.objects[n].obj, "val") else asm.objects[n].obj
    checks = {}
    servo_names = [c.name for c in asm.children if c.name.startswith("servo_")]
    for a in servo_names + ["imu", "spine"]:
        for b in ["bypass_tube_Al", "ct", "spine"] + [s_ for s_ in servo_names if s_ != a]:
            if a == b: continue
            va = shp(a); vb = shp(b)
            inter = va.intersect(vb).Volume()
            if inter > 1e-3: checks[f"{a} x {b}"] = round(inter, 3)
    print("   overlaps (mm3):", checks or "none")
    json.dump(dict(generator="gen_wyvern_fin.py", L_total_mm=L, interference=checks, parts=report),
              open(os.path.join(HERE, "mass_report.json"), "w"), indent=2)
    tot = sum(p["mass_g"] for p in report if p["flight"])
    print(f"printed flight parts total: {tot:.1f} g")
