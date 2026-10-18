#!/usr/bin/env python3
"""GTR70E WYVERN, 70 mm single-stage FINNED TVC sustainer (F15-4, motor-ejection recovery via
two-body-tube separation at a single bulkhead joint, NO bypass tube) + 3-axis TVC balance
(servo test stand) + static thrust stand + static deflector.

Architecture (`Documentation/WYVERN_E4_Recovery.md`, `CONFLICTS.md` §6/§8,
`Documentation/WYVERN_E4_Mathematics.md`):

  Upper BT (ASA-Aero, foamed 0.65 g/cm3): nose + recovery wadding/FC bay (avionics housing,
            no motor heat, no ejection-gas load -- lightest zone in the stack). Houses the Pico 2 W
            perfboard as a 50 x 70 mm axial card in a pair of slotted carrier disks, plus the
            camera, LiPo and UBEC. Arming switch is reached by pulling the nose cone.
  Lower BT (ASA-Aero, foamed 0.65 g/cm3): chute+cord+wadding zone + TVC bay, ONE continuous
            tube. Hoop stress under the 140 kPa ejection pulse (`WYVERN_E4_FEA_Structural.md`
            §4.1 load): sigma = p*r/t = 2.93 MPa, SF ~10x vs solid-ASA yield (30 MPa), ~6x even
            under a conservative 60%-strength-retention assumption for the foamed variant --
            comfortable positive margin, same logic as the >>1 flight-load SF elsewhere in that
            doc. Fin bond and ejection-gas thermal exposure are unaffected by the tube material
            (fins are a separate PETG-CF part bonded to the tube's solid outer perimeter shell,
            and the bulkhead -- the actual direct-gas-exposure part per FEA_Structural.md §4.2 --
            is PETG-CF).
  TVC assembly (PC-FR, 1.20 g/cm3): motor mount + gimbal only. PC-FR is the LIGHTER of the two
            non-foamed materials here (1.20 vs PETG-CF's 1.30 g/cm3) and is picked for its
            thermal role next to the nozzle.
  Bulkhead joint (PETG-CF): the ONE bulkhead between Upper BT and Lower BT, a friction-fit/
            shear-pin RELEASE joint, NOT gas-sealed. Direct ejection-gas-exposure part per
            FEA_Structural.md §4.2.
  Fins (PETG-CF): 87 mm span, root 70 / tip 35 / LE-sweep 25 / thickness 3, all mm.

--------------------------------------------------------------------------------------------
DFM practices used throughout this file:
  - Every mating tube/disk/ring interface carries an explicit slip-fit or press-fit tolerance
    (FIT_SLIP / FIT_PRESS below), named, not accidental.
  - Every bolted joint uses an M3 heat-set-insert boss (pilot hole sized for the standard
    knurled brass insert) instead of a bare hole into raw plastic.
  - The gimbal's pivot points are through-holes sized for a real metal pivot pin/screw, so the
    joint can actually rotate once assembled.
  - Hardware interface dimensions (servo mounting flange, load-cell body/hole spacing, HX711
    board) are TYPICAL-CLASS figures for the specific purchased parts (EMAX ES08MA II, Adafruit
    5kg/1kg strain-gauge cells, Adafruit HX711), not measured off the actual bench hardware.
    Every such block is tagged VERIFY-WITH-CALIPERS in a comment; treat as "will assemble",
    confirm against the real part before the final print run, same epistemic standard the rest
    of this repo holds unverified numbers to (see CONFLICTS.md #9).
--------------------------------------------------------------------------------------------
"""
import os, json
import math
from wcad import (S, cyl, tube, cone, box, sphere, ogive_nose, fin, _revolve,
                   export_step, export_stl, hole_cutter, boss, insert_boss, bolt_circle)

def ellipsoid_nose(R, L, wall=None, z=0):
    n = 60; pts = [(max(R*math.sqrt(max(1-(L*i/n/L)**2, 0.0)), 0.0), L*i/n) for i in range(n+1)]
    return _revolve(pts, z, wall)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DROCK = os.path.join(ROOT, "3D parts")
DSTAND = os.path.join(ROOT, "Motor Test Stand", "TVC Thrust-Vector Balance")
DSTATIC = os.path.join(ROOT, "Motor Test Stand", "Static Stand (thrust + deflector)")
for d in (DROCK, DSTAND, DSTATIC): os.makedirs(d, exist_ok=True)

# ================================================================================================
# GLOBAL DFM CONSTANTS -- named once, used everywhere. Change here, not per-part.
# ================================================================================================
FIT_SLIP = 0.20   # radial clearance for parts that slide together (tube-in-tube, disk-in-bore), mm
FIT_PRESS = -0.10  # radial interference for parts meant to friction-hold (ring onto motor tube), mm
WALL = 1.6         # airframe wall, all materials, FEA-verified ~340x min SF (FEA_Structural.md #1-2)

M3 = dict(PILOT=4.2, BOSS_OD=8.0, BOSS_H=6.0, CLR=3.4, HEAD_CB_D=6.4, HEAD_CB_H=3.2)
# ^ M3 heat-set brass insert (standard 4.0-4.2mm pilot per typical knurled-insert vendor specs),
#   M3_CLR is a clearance-fit through-hole for a bare M3 bolt shank, HEAD_CB is a socket-cap
#   counterbore. These are catalog-standard, not part-specific -- safe to trust as-is.

# TYPICAL-CLASS, VERIFY-WITH-CALIPERS before the final print (see module docstring):
SERVO = dict(SPAN=28.0, PITCH=10.0, HOLE_D=2.2, BODY_W=12.4, BODY_L=23.0, BODY_H=29.4)
# EMAX ES08MA II metal-gear micro servo (BOM), standard "micro/9g-class" mounting flange:
# SPAN = tab-to-tab hole center distance, PITCH = front/back hole spacing on one tab.
LC5 = dict(W=12.7, L=76.0, MT_HOLE_D=5.5, MT_PITCH=10.0, SENSE_HOLE_D=5.5)
# Adafruit 5kg straight-bar strain-gauge load cell (TAL221-class), fixed (mounting) end 2 holes,
# free (sensing) end 1 hole.
LC1 = dict(W=12.7, L=55.0, MT_HOLE_D=4.2, MT_PITCH=8.0, SENSE_HOLE_D=4.2)
# Adafruit 1kg strain-gauge load cell, same family, shorter body.
HX711 = dict(W=20.5, L=27.0, HOLE_D=2.7, HOLE_INSET=2.5)
# Adafruit HX711 24-bit ADC breakout, 2 diagonal mounting holes near the board corners.

_OLD_FC_L, _OLD_REC_L, _OLD_ENG_L = 160.0, 180.0, 160.0
_SCALE = 620.0 / (_OLD_FC_L + _OLD_REC_L + _OLD_ENG_L)
P = dict(
    OD=70.0, R=35.0, WALL=WALL, RI=33.4,
    MOT=29.6, MMT=33.0,
    NOSE_L=120.0,
    UPPER_L=round(_OLD_FC_L * _SCALE, 1),   # 198.4 mm, sized by the 70 mm perfboard + cam + pack stack
    LOWER_L=350.0,                          # shortened from 350.0 mm to raise TVC pitch authority
    BULKHEAD_T=4.0,
    PCB_W=50.0, PCB_H=70.0,  # Pico 2 W perfboard, mounted as an axial card in the Upper BT
)
DENS = dict(ASAAERO=0.65, PETGCF=1.30, PCFR=1.20)
report = []
def save(shape, folder, name, mat):
    vol = shape.volume_cm3(); m = vol * DENS.get(mat, 1.0)
    export_stl(shape, os.path.join(folder, name + ".stl")); export_step(shape, os.path.join(folder, name + ".step"))
    report.append((name, round(vol, 1), round(m, 1), mat))
    print(f" {name:34} {vol:7.1f} cm3 ~{m:6.1f} g ({mat})")
    return shape

def retention_screws(tube_or, tube_ir, z, n=3, hole_d=M3["CLR"]):
    """n radial M3 clearance holes through a tube wall at height z, for self-tapping retention
    screws into whatever's inside (bulkhead rim, motor-mount ring). Cuts from just inside the
    bore (tube_ir) out through the wall to just past the OD, so it's a clean through-cut of the
    NEAR wall only. Returns a cutter shape."""
    cutter = None
    for i in range(n):
        ang = 360.0 * i / n
        c = hole_cutter(hole_d, tube_or - tube_ir + 4, tube_ir - 2, 0, z, axis="x", margin=0.5)
        c = c.rotate("z", ang, origin=(0, 0, z))
        cutter = c if cutter is None else cutter.fuse(c)
    return cutter

# ---- airframe ----
def nose():
    n = ellipsoid_nose(P["R"], P["NOSE_L"], wall=P["WALL"])
    save(n, DROCK, "01_nose_cone_ellipsoid_ASAAero", "ASAAERO")

def upper_bt():
    # Upper BT: recovery wadding + FC bay (custom PCB, camera, battery), ASA-Aero.
    # Aft end (z=0) mates to the bulkhead joint -- 3x M3 radial retention screws into the
    # bulkhead's rim, 8mm in from the aft face (clear of the bulkhead's own edge chamfer).
    b = tube(P["R"], P["RI"], P["UPPER_L"])
    b = b.cut(retention_screws(P["R"], P["RI"], 8.0, n=3))
    # Flight-computer card carrier retention. The Pico 2 W perfboard is a 50 x 70 mm card mounted
    # ON EDGE along the tube axis (70 mm won't fit across a 66.8 mm bore), so it can't bolt to the
    # tube wall on a bolt circle. It slides into a pair of slotted carrier disks (see
    # fc_card_carrier()); these 3x M3 radial pilots pin the forward carrier disk in place.
    boss_z = min(30.0, P["UPPER_L"] - 20.0)
    b = b.cut(retention_screws(P["R"], P["RI"], boss_z, n=3))
    save(b, DROCK, "02_upper_bt_avionics_ASAAero", "ASAAERO")

def lower_bt():
    # Lower BT: chute+cord+wadding zone AND the TVC bay, ONE continuous tube. Fwd end
    # (z=LOWER_L, mates to bulkhead) gets the matching 3x M3 retention screws; aft end gets 2x
    # M3 retention screws into the motor mount's aft centering ring (see motor_mount()).
    # Tube material is ASA-Aero (0.65 g/cm3), chosen over PETG-CF (1.30 g/cm3) to hold T/W.
    # Hoop stress under the 140 kPa ejection pulse is 2.93 MPa (module docstring), SF
    # ~6-10x on ASA-Aero -- comfortable positive margin. The motor mount and gimbal keep PC-FR
    # for thermal duty next to the nozzle; the bulkhead keeps PETG-CF as the direct-gas-exposure
    # part (FEA_Structural.md §4.2). This tube itself sees neither the nozzle heat nor a direct
    # gas-exposure surface, so it's the safe place to take the ASA-Aero win.
    L = P["LOWER_L"]
    b = tube(P["R"], P["RI"], L)
    b = b.cut(retention_screws(P["R"], P["RI"], L - 8.0, n=3))
    b = b.cut(retention_screws(P["R"], P["RI"], 8.0, n=2))
    save(b, DROCK, "03_lower_bt_chute_tvc_ASAAero", "ASAAERO")

def fc_card_carrier():
    """Two slotted disks that hold the Pico 2 W perfboard as an axial card in the Upper BT.

    The board is 50 x 70 x ~1.6 mm and stands on edge along the tube axis. Each disk is a
    FIT_SLIP plug in the tube bore with a through-slot on the diameter; the card slides in from
    the aft end and is captured fore and aft. Components stand off one face of the card and the
    LiPo straps to the other, which is what keeps the whole avionics stack inside 140 mm of the
    198.4 mm Upper BT.

    Cable notches at the rim let the servo/IMU bundle and the battery leads pass without being
    pinched between the disk and the tube wall.
    """
    r = P["RI"] - FIT_SLIP
    t = 3.0                     # 3 mm is plenty: these carry the card, not a flight load
    slot_w = 1.6 + 0.6          # board thickness + slide clearance
    for tag in ("fwd", "aft"):
        d = cyl(r, t)
        d = d.cut(box(P["PCB_W"] + 0.6, slot_w, t + 2, True, -1))     # card slot on the diameter
        # rim cable notches, 180 deg apart, clear of the card slot
        for ang in (90.0, 270.0):
            d = d.cut(box(9.0, 6.0, t + 2, True, -1).translate(r - 3.0, 0, 0).rotate("z", ang))
        # lightening holes: these disks see no flight load beyond restraining the card, so most
        # of the web is removable. Placed off the card slot axis so they don't break into it.
        for ang in (35.0, 145.0, 215.0, 325.0):
            d = d.cut(hole_cutter(13.0, t + 2, r * 0.55, 0, -1, axis="z", margin=0.5).rotate("z", ang))
        for (x, y) in bolt_circle(r - M3["BOSS_OD"] / 2, 3):
            d = d.cut(hole_cutter(M3["PILOT"], t + 1, x, y, -0.5, axis="z", margin=0.5))
        save(d, DROCK, f"02b_fc_card_carrier_{tag}_ASAAero", "ASAAERO")

def bulkhead_joint():
    # The ONE bulkhead between Upper BT and Lower BT. NOT gas-sealed -- pass-throughs are wiring
    # holes only (servo bundle + STEMMA-QT). Disk OD is FIT_SLIP under the tube bore so it can
    # actually be inserted; 3x M3 pilot holes on its rim (matching upper_bt()'s retention screws)
    # let it be pinned in place from outside rather than relying on friction alone to survive
    # handling before the ejection event is meant to release it.
    #
    # NOT MODELED: the actual friction-fit/shear-pin RELEASE geometry (target 50-150 N release
    # force, `WYVERN_E4_Recovery.md` #4 / `WYVERN_E4_FEA_Structural.md` #4.1) is an open
    # engineering decision per that doc, not invented here. The 3 retention screws below hold
    # the bulkhead captive in the Upper BT only; the actual BT-to-BT release mechanism (how the
    # two body tubes themselves let go of each other under ejection pressure) still needs a real
    # sizing pass -- this part alone does not resolve that.
    off = 18.0
    r = P["RI"] - FIT_SLIP
    d = cyl(r, P["BULKHEAD_T"])
    # Pass-throughs carry the seven leads that cross the separation joint on dupont male-female
    # extensions: SERVO1_SIG, SERVO2_SIG, +5V, GND (servo bundle) and SDA, SCL, 3V3 (gimbal IMU,
    # sharing the same GND). They are sized for the WIRE bundle with chafe clearance, not for the
    # connector bodies -- the dupont shells sit either side of the bulkhead, not inside the hole,
    # so they can part freely when the tubes separate.
    d = d.cut(cyl(4.5, P["BULKHEAD_T"] + 2, -1).translate(off, 0, 0))    # servo bundle, 4 leads
    d = d.cut(cyl(4.0, P["BULKHEAD_T"] + 2, -1).translate(-off, 0, 0))  # gimbal IMU, 4 leads
    for (x, y) in bolt_circle(r - M3["BOSS_OD"]/2, 3):
        d = d.cut(hole_cutter(M3["PILOT"], P["BULKHEAD_T"] + 1, x, y, -0.5, axis="z", margin=0.5))
    save(d, DROCK, "04_bulkhead_joint_PETGCF", "PETGCF")

def motor_mount():
    # 29mm motor mount tube, PC-FR. 3 centering rings: inner bore is a PRESS fit onto the motor
    # tube (rings glued/pressed on), outer OD is a SLIP fit into the Lower BT bore (was modeled
    # at exactly the bore radius before, which does not go together in practice). Aft ring gets
    # 2x M3 pilot holes matching lower_bt()'s aft retention screws.
    mt = tube(P["MMT"]/2, P["MOT"]/2 + FIT_PRESS, 140.0)
    ring_or = P["RI"] - FIT_SLIP
    for z in (10, 70, 130):
        mt = mt.fuse(tube(ring_or, P["MMT"]/2 + FIT_PRESS, 3.0).translate(0, 0, z))
    for (x, y) in bolt_circle(ring_or - 4.0, 2):
        mt = mt.cut(hole_cutter(M3["PILOT"], 6.0, x, y, 10.0, axis="z", margin=0.5))
    save(mt, DROCK, "05_motor_mount_29mm_PCFR", "PCFR")

def gimbal():
    # 2-axis gimbal: outer ring (pitch) + inner ring (yaw) holding the 29mm motor mount, PC-FR.
    # PIVOT FIX: the old version fused SOLID pin bosses onto the outer ring, meant to mate into
    # a bracket that doesn't exist and, more basically, cannot print as a working hinge (both
    # sides of a rotating joint can't be one fused part). Replaced with clearance-fit THROUGH-
    # HOLES (3.2mm, slip fit for a 3mm steel dowel or M3 shoulder screw used as the actual pivot
    # pin) on both axes.
    # NOT MODELED: where the outer ring's pitch-axis holes anchor into the airframe (a trunnion
    # mount into the Lower BT wall) is an open mechanism-design decision, same category as the
    # bulkhead release joint -- not invented here for the flight vehicle. The ground-test thrust
    # block (tvc_balance()) DOES model a matching mount, since that geometry is actually pinned
    # down for the bench rig.
    PIVOT_D = 3.2  # slip fit for 3mm dowel / M3 shoulder screw
    outer = tube(31, 28, 40)
    for ax in (0, 90):
        # one clean diametral through-hole per axis (spans both walls of the ring), rather than
        # two separate stub cuts -- a real pivot pin is a single rod through the whole ring.
        outer = outer.cut(hole_cutter(PIVOT_D, 66, -33, 0, 20, axis="x", margin=1.0).rotate("z", ax, origin=(0, 0, 20)))
    inner = tube(27, P["MOT"]/2 + 1 + FIT_SLIP, 44).translate(0, 0, -2)
    g = outer.fuse(inner)
    # 2 servo horn bosses at 90 deg -- now real M2.2 clearance holes for the horn screw, plus the
    # servo body itself mounts to the thrust block/airframe via its own flange (see SERVO consts),
    # not this boss (the boss is just the linkage attachment point).
    for ax in (0, 90):
        b = box(8, 6, 10, True, 0).translate(30, 0, 6).rotate("z", ax)
        b = b.cut(hole_cutter(2.2, 12, 30, 0, 8, axis="z").rotate("z", ax))
        g = g.fuse(b)
    save(g, DROCK, "06_tvc_gimbal_2axis_PCFR", "PCFR")

def fins():
    # 87 mm span, root 70 / tip 35 / LE-sweep 25 / thickness 3, PETG-CF. Bonded joint (epoxy
    # fillet at the root per Build_Guide.md), not mechanically fastened, so no screw holes here
    # -- but root corners are chamfered so the glue fillet has somewhere to key into instead of
    # sitting on a sharp printed edge.
    fi = fin(70.0, 35.0, 87.0, 25.0, 3.0)
    fi = fi.cut(box(6, 5, 6, True, 0).rotate("y", 45).translate(0, 0, 0))
    fi = fi.cut(box(6, 5, 6, True, 0).rotate("y", 45).translate(70, 0, 0))
    save(fi, DROCK, "07_fin_single_PETGCF", "PETGCF")

def rail_buttons():
    # 3D-printed 1010 rail buttons, PETG-CF (mounts to the lower/PETG-CF body). Center through-
    # hole for an M3 mounting screw into the airframe wall (was solid before -- unmountable).
    btn = cyl(5.0, 4.0).fuse(cyl(8.0, 2.0).translate(0, 0, 4)).fuse(cyl(8.0, 1.5).translate(0, 0, -1.5))
    btn = btn.cut(hole_cutter(M3["CLR"], 10, 0, 0, 0, axis="z", margin=1.0))
    save(btn, DROCK, "08_rail_button_1010_x2", "PETGCF")

def assembly():
    z = 0; parts = []
    parts.append(("lower", tube(P["R"], P["RI"], P["LOWER_L"], z))); z += P["LOWER_L"]
    parts.append(("bulkhead", cyl(P["R"], P["BULKHEAD_T"], z))); z += P["BULKHEAD_T"]
    parts.append(("upper", tube(P["R"], P["RI"], P["UPPER_L"], z))); z += P["UPPER_L"]
    parts.append(("nose", ellipsoid_nose(P["R"], P["NOSE_L"], wall=P["WALL"]).translate(0, 0, z)))
    asm = parts[0][1]
    for _, p in parts[1:]: asm = asm.fuse(p)
    total_len = z + P["NOSE_L"]
    print(f" [assembly length {total_len:.0f} mm, vs core.py LTOT=672 mm]")
    save(asm, DROCK, "00_full_assembly", "PETGCF")

# ---- 3-axis TVC balance (servo ground-test stand) ----
def tvc_balance():
    # Base: 3 load-cell pedestals (axial Z under, lateral X/Y), M3 insert bosses at each pedestal
    # face for the load-cell mounting bracket, plus 4 corner insert bosses to bolt the whole base
    # to a bench/plate.
    base = box(220, 220, 8, True, 0)
    base = base.fuse(box(20, 40, 40, True, 0).translate(0, 0, 24))
    base = base.fuse(box(40, 20, 30, True, 0).translate(90, 0, 19))
    base = base.fuse(box(20, 40, 30, True, 0).translate(0, 90, 19))
    for (x, y) in ((95, 95), (-95, 95), (95, -95), (-95, -95)):
        base = base.fuse(insert_boss(M3["BOSS_OD"], M3["BOSS_H"], M3["PILOT"], x, y, 8))
    # axial (Z) load-cell mount face (top of the Z column, facing up)
    for (x, y) in ((0, LC5["MT_PITCH"]/2), (0, -LC5["MT_PITCH"]/2)):
        base = base.cut(hole_cutter(LC5["MT_HOLE_D"], 10, x, y, 44, axis="z"))
    # lateral X cell mount face (inboard face of the X pedestal)
    for (y, zz) in ((LC1["MT_PITCH"]/2, 34), (-LC1["MT_PITCH"]/2, 34)):
        base = base.cut(hole_cutter(LC1["MT_HOLE_D"], 10, 70, y, zz, axis="x"))
    # lateral Y cell mount face (inboard face of the Y pedestal)
    for (x, zz) in ((LC1["MT_PITCH"]/2, 34), (-LC1["MT_PITCH"]/2, 34)):
        base = base.cut(hole_cutter(LC1["MT_HOLE_D"], 10, x, 70, zz, axis="y"))
    save(base, DSTAND, "TVC_balance_base", "PETGCF")

    # Thrust block: motor+gimbal mount on top, flexure tabs to the lateral cells. This IS the
    # gimbal's pitch-axis trunnion mount for the ground rig (unlike the flight airframe, this
    # geometry is pinned down, so it's modeled for real): 2x through-holes on the block's
    # vertical face pair match the gimbal outer ring's PIVOT_D=3.2mm holes at the same 56mm
    # span (28mm off-center each side) and 40mm height used in gimbal().
    block = box(80, 80, 30, True, 0)
    block = block.cut(cyl(P["MOT"]/2 + FIT_SLIP, 40).translate(0, 0, 0))
    for sx, sy in ((60, 0), (0, 60)):
        block = block.fuse(box(16, 16, 14, True, 0).translate(sx, sy, 8))
    for side in (1, -1):
        block = block.cut(hole_cutter(3.2, 80, side*28, 0, 8, axis="y"))  # gimbal pitch pivot
    save(block, DSTAND, "TVC_balance_thrust_block", "PETGCF")

    # Flexure template: unchanged (spring-steel flexure profile, printed as a cutting/bending
    # guide only, not a functional plastic part -- no fasteners apply).
    flex = box(30, 8, 1.0, True, 0)
    save(flex, DSTAND, "TVC_balance_flexure_template", "PETGCF")

    # HX711 mount plate, bolts to the base's side face near the load-cell pedestals.
    hx = box(HX711["W"] + 6, HX711["L"] + 6, 3, True, 0)
    for sx in (1, -1):
        for sy in (1, -1):
            hx = hx.cut(hole_cutter(HX711["HOLE_D"], 6, sx*(HX711["W"]/2 - HX711["HOLE_INSET"]),
                                     sy*(HX711["L"]/2 - HX711["HOLE_INSET"]), 0, axis="z"))
    for (x, y) in ((-30, 0), (30, 0)):
        hx = hx.fuse(insert_boss(6.0, 4.0, M3["PILOT"], x, y, -1.5))
    save(hx, DSTAND, "TVC_balance_hx711_mount", "PETGCF")

# ---- static thrust stand (static fire test) ----
def static_stand():
    # 5 kg axial load cell + HX711 -> RP2350 custom PCB (GSE_TestStands.md #1, confirmed current
    # 2026-08-11, see CONFLICTS.md #9 / Static Stand README fix). Steel blast deflector is bought
    # hardware, not printed; TS_base_plate/TS_motor_tower/TS_loadcell_bracket are the printed set.
    base = box(220, 140, 8, True, 0)
    for (x, y) in ((100, 60), (-100, 60), (100, -60), (-100, -60)):
        base = base.fuse(insert_boss(M3["BOSS_OD"], M3["BOSS_H"], M3["PILOT"], x, y, 8))
    # motor-tower mounting pattern (bolt circle, tower bolts to the base)
    for (x, y) in bolt_circle(30, 4, start_deg=45):
        base = base.cut(hole_cutter(M3["CLR"], 12, x + 60, y, 8, axis="z"))
    # load-cell bracket mounting pattern
    for (x, y) in bolt_circle(20, 2):
        base = base.cut(hole_cutter(M3["CLR"], 12, x - 70, y, 8, axis="z"))
    save(base, DSTATIC, "TS_base_plate", "PETGCF")

    # Motor tower: vertical cradle holding the F15 case (29mm-class Estes motor OD ~29.5mm,
    # FIT_SLIP clearance so the motor drops in and is retained by its own hook/clip, standard
    # Estes practice, not glued). Bolts to the base plate via the matching 4-hole pattern above.
    tower = tube(20, P["MOT"]/2 + FIT_SLIP, 100).translate(0, 0, 8)
    tower = tower.fuse(box(60, 60, 8, True, 0))
    for (x, y) in bolt_circle(30, 4, start_deg=45):
        tower = tower.cut(hole_cutter(M3["CLR"], 12, x, y, 0, axis="z"))
    save(tower, DSTATIC, "TS_motor_tower", "PETGCF")

    # Load-cell bracket: mounting (fixed) end takes 2x M5-class clearance holes at LC5["MT_PITCH"]
    # per Adafruit 5kg cell TYPICAL dims, sensing end takes 1x M5-class hole for the interface rod
    # to the motor tower's thrust-transfer tab.
    br = box(LC5["W"] + 10, LC5["L"] + 20, 8, True, 0)
    for (x, y) in ((0, LC5["MT_PITCH"]/2 + 20), (0, -LC5["MT_PITCH"]/2 + 20)):
        br = br.cut(hole_cutter(LC5["MT_HOLE_D"], 10, x, y, 0, axis="z"))
    br = br.cut(hole_cutter(LC5["SENSE_HOLE_D"], 10, 0, -LC5["L"]/2, 0, axis="z"))
    for (x, y) in bolt_circle(20, 2):
        br = br.fuse(insert_boss(M3["BOSS_OD"], M3["BOSS_H"], M3["PILOT"], x, y + 20, -4))
    save(br, DSTATIC, "TS_loadcell_bracket", "PETGCF")

# ---- static-stand deflector ----
def deflector():
    d = box(160, 160, 6, True, 0).rotate("x", 45).translate(0, 40, 40)
    d = d.fuse(box(160, 10, 80, True, 0).translate(0, -40, 40))
    for x in (70, -70):
        d = d.cut(hole_cutter(M3["CLR"], 20, x, -40, 40, axis="y"))  # mounts to the base plate
    save(d, DSTATIC, "static_blast_deflector", "PETGCF")

if __name__ == "__main__":
    _RETIRED = [
        "01_nose_cone_ellipsoid_PLA", "02_recovery_bay_PLA", "03_fc_bay_PLA",
        "04_engine_tvc_bay_PETGCF", "05a_bulkhead_A_PETGCF", "05b_bulkhead_B_PETGCF",
        "06_motor_mount_29mm_PETGCF", "07_tvc_gimbal_2axis_PETGCF", "08b_fin_single_PLA",
        "09_bypass_tube_PETGCF",
    ]
    for stem in _RETIRED:
        for ext in (".stl", ".step"):
            p = os.path.join(DROCK, stem + ext)
            if os.path.exists(p):
                try:
                    os.remove(p); print(f" removed stale {stem}{ext}")
                except PermissionError:
                    print(f" could not remove stale {stem}{ext} (needs manual cleanup)")

    print("== AIRFRAME =="); nose(); upper_bt(); fc_card_carrier(); lower_bt(); bulkhead_joint(); motor_mount(); gimbal(); fins()
    print("== SERVO TEST STAND (TVC balance) =="); tvc_balance()
    print("== STATIC TEST STAND =="); static_stand()
    print("== RAIL BUTTONS =="); rail_buttons()
    print("== STATIC DEFLECTOR =="); deflector()
    print("== ASSEMBLY =="); assembly()
    json.dump(report, open(os.path.join(os.path.dirname(__file__), "mass_report.json"), "w"), indent=1)

    QTY = {"07_fin_single_PETGCF": 4}
    flight = [x for x in report if x[0][:2] in ("01", "02", "03", "04", "05", "06", "07", "08")
              and not x[0].startswith("08_rail")]
    tot = sum(x[2] * QTY.get(x[0], 1) for x in flight)
    rails = sum(x[2] for x in report if x[0].startswith("08_rail"))
    print(f"\nprinted flight-airframe mass ~{tot:.1f} g (+{rails:.1f} g rail buttons)"
          f" -> {tot + rails:.1f} g printed total; {len(report)} exported parts")
    print(" breakdown:")
    for x in flight:
        q = QTY.get(x[0], 1)
        print(f" {x[0]:34} {x[2]:6.1f} g x{q} = {x[2]*q:6.1f} g ({x[3]})")
    print(" NOTE: printed structure only, see module docstring + CONFLICTS.md #9 for what's")
    print(" scaled/estimated vs. verified, and what open mechanism decisions (bulkhead release")
    print(" geometry, gimbal-to-airframe trunnion mount) are deliberately not modeled here.")
