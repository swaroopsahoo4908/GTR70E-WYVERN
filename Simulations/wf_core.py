#!/usr/bin/env python3
"""GTR70E WYVERN (fin-control revision) -- single source of truth.

Every number the CAD generator, the simulations, the firmware comments and the docs quote comes
from this file (geometry, COTS masses, motors, aero helpers). Change it here and re-run the
cascade:

    3D parts/_generator/gen_wyvern_fin.py   -> mass_report.json (printed-part masses)
    Simulations/wf_core.py --report          -> canonical_numbers.json
    Simulations/wf_flightsim.py              -> trajectories, control, motor trade
    Simulations/wf_fin_authority.py          -> VLM + panel CFD sweep (RQ1/RQ2 predictions)
    Simulations/wf_bypass.py, wf_power.py, wf_link_budget.py
    Documentation/*                          -> quote canonical_numbers.json, never retype

Conventions
  * Stations x are measured from the nose tip, positive aft, in mm (CAD uses +Z = nose-up; the
    generator converts).
  * "Pair A" = control fins at azimuth 0/180 deg, "pair B" = 90/270 deg. All four servos sit in
    ONE ring at the same station (X_HINGE); X_HINGE_A / X_HINGE_B are kept as aliases.
  * The ejection bypass tube runs up the vehicle centreline; the avionics hang on a square spine
    around it.
  * Fixed rectangular fins sit at 45/135/225/315 deg (interdigitated with the control fins), so
    a deflected control fin's tip vortex streams between the fixed fins rather than onto them.
"""
from __future__ import annotations
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MASS_REPORT = os.path.join(ROOT, "3D parts", "_generator", "mass_report.json")
_trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))

# =============================================================================================
# 1. GEOMETRY (mm)
# =============================================================================================
# OD is DERIVED from the servo ring (revision 3): servo bases 5.0 mm from the axis, servo body
# radial, spline, 2 mm hub flange, 0.4 mm clearance, 1.6 mm wall -> 58 mm OD (was 70).
WALL = 1.6                 # airframe wall (all printed tubes)
FIT_SLIP = 0.20            # radial clearance, sliding fits
COUPLER_L = 40.0           # every section joint: 20 mm into each tube
COUPLER_WALL = 1.6

NOSE = dict(type="tangent_ogive", L=150.0, shoulder=35.0, wall=1.6,
            ballast_bay_L=40.0)  # ballast bay = solid-ish tip region, fill per BALLAST_G below

# Section lengths (exposed tube lengths, joints are internal couplers)
L_RB = float(os.environ.get("WYV_L_RB", 250.0))   # <= 256 so it prints upright on a 256 mm printer   # recovery bay: chute, Nomex, shock cord. Only the nose separates.
L_MB = COUPLER_L / 2 + 6.0 + 10.0 + 83.0   # motor bay: shoulder + plenum + gallery + 83 mm motor (aft-flush)



# ---- Servo: KST X08 Plus (V2) -- 23.5 x 8 x 16.8 mm, coreless, steel gears, aluminium case,
# 3.8-8.4 V (runs straight off 2S), 5.3 kg-cm / 0.09 s per 60 deg at 8.4 V, 333 Hz frame.
# Mounted DIRECTLY to the control-tube wall: its ears bolt to a pad printed into the wall, the
# output shaft points radially out through the wall into the fin hub. Short height (16.8 mm) is
# what lets all FOUR servos sit at ONE station around a central bypass tube.
SERVO = dict(name="KST X08 Plus", L=23.5, W=8.0, H=16.8, mass_g=9.0,
             torque_kgcm={3.8: 2.4, 6.0: 3.85, 7.4: 4.85, 8.4: 5.3},
             speed_s60={3.8: 0.18, 6.0: 0.15, 7.4: 0.12, 8.4: 0.09},
             v_range=(3.8, 8.4),
             # VERIFY-WITH-CALIPERS (vendor pages give only the case size):
             ear_span=30.3, ear_t=1.5, ear_from_top=4.0, spline_len=3.0,
             shaft_from_end=5.5, hole_pitch=26.5)
SERVO_BASE_R = 5.0                                           # inner end of each servo (set by Sky, rev 3)
SERVO_TOP_R = SERVO_BASE_R + SERVO["H"]                      # 21.8: servo output face
SPLINE_TOP_R = SERVO_TOP_R + SERVO["spline_len"]             # 24.8: spline tip; horn in the hub-flange pocket
PAD_INNER_R = SERVO_TOP_R - SERVO["ear_from_top"]           # 17.8: ears bear on the wall pad here
HUB_FLANGE_T = 1.6        # 13 mm flange: its corners must clear the bore (fit check)
RI = round(SPLINE_TOP_R + HUB_FLANGE_T + 1.0, 3)                # 27.4 bore radius
R = RI + WALL                                                # 29.0
OD = 2 * R                                                   # 58.0 mm

# One servo ring, all four fins at the same station (measured up from the CT aft end)
SERVO_RING_Z = COUPLER_L / 2 + 3.0 + SERVO["ear_span"] / 2   # servo body centre
HINGE_Z = SERVO_RING_Z + SERVO["L"] / 2 - SERVO["shaft_from_end"]   # shaft toward the nose end
IMU_DECK_Z = SERVO_RING_Z + SERVO["ear_span"] / 2 + 4.0
SPINE_Z0 = IMU_DECK_Z + 4.0                                  # avionics spine around the bypass tube
SPINE_L = 88.0                                               # rev 3c: +4 mm for the high-g accel row on -Y
SPINE_FLAT = 7.0                                             # spine faces 7 mm from the axis
# board planes (distance of the board's inner face from the axis), chosen so no board corner meets
# a neighbour and everything stays inside the 27.4 mm bore (checked in gen_fit_assembly.py):
BOARD_PLANE = dict(px=9.0,      # +X: BNO085 + Feather on 2 mm standoffs
                   nx=7.5,      # -X: 2S LiPo on foam tape straight on the face
                   py=16.0,     # +Y: power perfboard on 9 mm pillars
                   ny=16.0)     # -Y: BME688 + microSD on 9 mm pillars
# Every board on the spine: face, z0 above the spine foot, axial length, width, mass (g),
# mounting holes (lateral, axial) relative to the board's lower-left corner, vendor STEP model.
# Board sizes and hole grids are read from the vendor STEP files in 3D parts/vendor/.
SCREW_SWITCH_V = 27.0                 # screw switch, mm up the perfboard (under the 3 mm wall hole)
SPINE_BOARDS = [
    dict(key="bno085", name="BNO085 IMU (Adafruit 4754)", face="px", z0=2.0, L=25.4, W=22.86, mass=3.0,
         holes=[(2.54, 2.54), (20.32, 2.54), (2.54, 22.86), (20.32, 22.86)], step="adafruit_4754_bno085.step"),
    dict(key="feather", name="Feather RP2040 RFM95 (Adafruit 5714)", face="px", z0=31.0, L=50.8, W=22.86, mass=8.0,
         holes=[(2.54, 2.54), (20.32, 2.54), (2.54, 48.26), (20.32, 48.26)],
         step="adafruit_5712_feather_rp2040_rfm_formfactor.step"),
    # -Y boards use ONE line of holes each, shifted (offset) so the pillars run up between the
    # Feather standoffs and the battery / high-g accel (pillar centres within x = -7.5 .. +6.7)
    dict(key="bme688", name="BME688 (Adafruit 5046)", face="ny", z0=5.0, L=25.4, W=17.78, mass=1.5, offset=6.85,
         holes=[(2.54, 2.54), (2.54, 22.86)], step="adafruit_5046_bme688.step"),
    dict(key="microsd", name="microSD 3V breakout (Adafruit 4682) + card", face="ny", z0=33.0, L=25.4, W=22.86, mass=3.8,
         offset=-4.89, holes=[(20.32, 2.54), (20.32, 22.86)], step="adafruit_4682_microsd.step"),
    # rev 3c: the boost can pass the BNO085's 8 g accelerometer range, so the vertical channel uses
    # this +/-200 g part during boost (Wire1 with the BNO, core 0). Rev 3d: it takes the -Y slot the
    # GPS had (GPS removed), one line of screws like the other -Y boards.
    dict(key="adxl375", name="ADXL375 +/-200 g accel (Adafruit 5374)", face="ny", z0=61.0, L=25.4, W=17.78, mass=1.0,
         offset=6.85, holes=[(2.54, 2.54), (2.54, 22.86)],
         step="adafruit_4097_adxl343_formfactor_for_5374_adxl375.step"),
    dict(key="battery", name="2S 450 mAh LiPo", face="nx", z0=14.0, L=57.0, W=30.0, mass=27.0, holes=[], step=None),
    dict(key="perfboard", name="power perfboard 16 x 62 mm (Pololu 2810 + D24V10F5, screw switch, divider, buzzer, 470 uF)",
         face="py", z0=12.0, L=62.0, W=16.0, mass=8.0,
         holes=[(3.5, 2.0), (12.5, 2.0), (3.5, 60.0), (12.5, 60.0)], step=None),
]
def board_plane(bd):
    """Distance of a spine board's inner face from the axis (per-board override, else its face's)."""
    return bd.get("plane", BOARD_PLANE[bd["face"]])
L_CT = round(SPINE_Z0 + SPINE_L + 4.0 + COUPLER_L / 2, 0)    # control tube length
X_HINGE = None             # set after the stations below

X_NOSE_BASE = NOSE["L"]
X_RB_TOP, X_RB_BOT = X_NOSE_BASE, X_NOSE_BASE + L_RB
X_CT_TOP, X_CT_BOT = X_RB_BOT, X_RB_BOT + L_CT
X_MB_TOP, X_MB_BOT = X_CT_BOT, X_CT_BOT + L_MB
L_TOTAL = X_MB_BOT
# ---- Motor mount (29 mm). Sized for the 83 mm AeroTech single-use case (F67W / F42T /
# G74W all share the 29 x 83 mm case; the F67C is 112 mm and does not fit), the motor budget (<= $100, no certification needed).
MOTOR_D = 29.0
MMT_ID = 29.5              # motor slip fit
MMT_WALL = 2.0
PLENUM_T = 6.0             # plenum bulkhead disk (PC-FR) + 14 mm bonded skirt; gallery below it
GALLERY_H = 10.0            # full-bore gas gallery height (~18 cm3) -- caps the ejection pressure spike
X_PLENUM_TOP = X_MB_TOP + COUPLER_L / 2          # plenum sits just below the CT/MB coupler
X_MOTOR_TOP = X_PLENUM_TOP + PLENUM_T + GALLERY_H  # full-bore gas gallery above the MMT
MOTOR_BAY_LEN = 83.0
X_MOTOR_AFT = X_MOTOR_TOP + MOTOR_BAY_LEN         # = MB aft end (+/- retainer)

# ---- Fixed rectangular fins ("run the height of the motor"). Rev 3b: span = control-fin H* (40 mm),
# the same height as the triangular fins (Sky); +20 g ballast restores the margin. See aim54 trade in SQ1.
RECT_FIN = dict(n=4, root=float(os.environ.get("WYV_STAB_ROOT", 81.0)), tip=float(os.environ.get("WYV_STAB_ROOT", 81.0)), span=float(os.environ.get("WYV_STAB_SPAN", 20.0)), t=2.4, sweep=0.0,
                az0_deg=45.0, mat="PETGCF")
# SQ1 (stabilizer impact): spans swept in simulation and the three spans printed for tunnel Phase B
STAB_SPANS_SIM = [0.0, 20.0, 30.0, 40.0, 45.0, 50.0, 55.0, 60.0]
STAB_OFFSETS_DEG = [0.0, 22.5, 45.0]      # stabilizer azimuth relative to the control fins
STAB_SPANS_WT = [20.0, 30.0, 40.0]        # tunnel Phase B: off (plugs), 20 (flight, rev 3d), 30, 40 (rev 3b flight)
X_RECT_LE = X_MOTOR_AFT - RECT_FIN["root"] - 1.0   # stabilizers run the motor length, aft edge 1 mm ahead of the nozzle plane

X_HINGE = X_CT_BOT - HINGE_Z
X_HINGE_A = X_HINGE_B = X_HINGE      # one station for all four fins (names kept for the sims)
X_IMU = X_CT_BOT - (SPINE_Z0 + SPINE_BOARDS[0]["z0"] + SPINE_BOARDS[0]["L"] / 2)

# ---- Control fins (triangular, all-moving, hinge on the servo shaft)
CFIN = dict(root=60.0, hinge_frac=0.45, gap=1.0, hub_d=8.0, hub_flange_d=13.0,
            hub_flange_t=1.6, root_boss_d=10.0, root_boss_L=6.0, mat="PETGCF",
            defl_max_deg=15.0)
CFIN_HEIGHTS = [20.0, 25.0, 30.0, 35.0, 40.0]   # RQ2 tunnel + CFD increments (5 mm)
CFIN_HEIGHTS_SIM = [15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]   # CFD/flight-sim sweep
CFIN_FLIGHT_EXTRA = [45.0]   # H* + 1 increment when H* = 40 (printed for flight only)
CFIN_PROFILES = ["flat_plate", "double_wedge", "NACA0006", "NACA0012"]  # RQ1 blocks
CFIN_H_NOMINAL = 45.0      # rev 3d flight fin (top of the H sweep). H* = 40 from wf_fin_authority still sets the research flights at H*-5, H*, H*+5

# ---- Ejection bypass tube (motor plenum -> recovery bay floor) ON THE CENTRELINE, through the
# middle of the servo ring and the avionics spine; see wf_bypass.py for the diameter trade.
BYPASS = dict(od=9.525, id=7.75, mat="6061-T6 aluminium, 3/8 in OD x 0.035 in wall",
              r_center=0.0, az_deg=0.0, density=2.70)
X_BYPASS_TOP = X_RB_BOT - 2.0          # exits flush with the recovery-bay floor
X_BYPASS_BOT = X_PLENUM_TOP + 4.0      # seats in an O-ring socket in the plenum bulkhead
BYPASS["L"] = X_BYPASS_BOT - X_BYPASS_TOP

# ---- Rail (Estes Pro Series II launch rail: 6 ft two-piece aluminium, 1010 buttons)
RAIL_LEN_M = 1.829
RAIL_BUTTON_AZ_DEG = 22.5   # between the 0 deg control fin and the 45 deg fixed fin
RAIL_BUTTON_STANDOFF = 3.0  # printed spacer under each 1010 button

# =============================================================================================
# 2. MATERIALS (g/cm3) -- FDM effective densities at the infill/perimeter settings in the
#    Build Guide (100 % for structure).
# =============================================================================================
DENS = dict(ASAAERO=0.65, ASA=1.07, PETGCF=1.30, PCFR=1.20, AL6061=2.70, STEEL=7.85)
SECTION_MAT = dict(nose="ASAAERO", rb="ASAAERO", ct="ASAAERO", mb="ASAAERO", couplers="PCFR",
                   cassette="PETGCF", plenum="PCFR", mmt="PCFR")

# =============================================================================================
# 3. COTS MASSES (g) and where they sit (station x, mm)
# =============================================================================================
BALLAST_G = float(os.environ.get("WYV_BALLAST", 214.0))  # nose ballast (steel shot in epoxy; may include a <=36 g self-contained camera). Sets the control arm -- see wf_flightsim + Design Overview s.4
BATTERY = dict(name="OVONIC 2S 7.6 V 450 mAh HV LiPo, XT30", mAh=450, V_nom=7.6,
               V_full=8.7, V_cut=6.4, mass_g=27.0, dims=(57, 30, 14))  # dims VERIFY on hand

def _x_ct(z):  # CT-local height above CT aft end -> station
    return X_CT_BOT - z

COTS = [  # name, mass_g, station_mm, length_mm (for inertia; 0 = point)
    ("nose ballast (steel shot + epoxy)", BALLAST_G, 30.0, 30.0),
    ("parachute 24 in rip-stop (Estes)", 30.0, X_RB_TOP + 90.0, 90.0),
    ("Nomex blanket 12x12 in", 14.0, X_RB_TOP + 150.0, 40.0),
    ("aramid shock cord 19 ft + 2 quick links + swivel", 28.0, X_RB_TOP + 175.0, 50.0),
    ("M5 eyebolt on the RB floor (off-axis, beside the bypass exit)", 6.0, X_RB_BOT - 8.0, 0.0),
    # avionics spine around the central bypass tube (all boards from SPINE_BOARDS)
    *[(bd["name"] + " on spine face " + bd["face"], bd["mass"], _x_ct(SPINE_Z0 + bd["z0"] + bd["L"] / 2), bd["L"]) for bd in SPINE_BOARDS],
    ("915 MHz 1/4-wave whip (uFL pigtail)", 3.0, _x_ct(SPINE_Z0 + 50), 78.0),
    ("servo x4 (KST X08 Plus), one ring", 4 * SERVO["mass_g"], X_HINGE, 23.5),
    ("servo horns + M2 hardware x4", 6.0, X_HINGE, 0.0),
    ("harness, connectors, XT30, heat-shrink", 18.0, _x_ct(SPINE_Z0 + 30), 100.0),
    ("heat-set inserts + M3 screws (joints)", 14.0, X_CT_TOP + 0.5 * L_CT, L_TOTAL - 200),
    ("1010 rail buttons x2 + spacers", 6.0, 0.5 * (X_CT_TOP + X_MB_BOT), 300.0),
    ("bypass tube O-rings + RTV", 3.0, X_PLENUM_TOP, 0.0),
]

# =============================================================================================
# 4. MOTORS -- RASP data from thrustcurve.org, renormalised to the certified total impulse.
# =============================================================================================
def _motor(name, t, f, I, m_tot, m_prop, L, delays, note):
    t = np.asarray(t, float); f = np.asarray(f, float)
    if t[0] > 0: t = np.r_[0.0, t]; f = np.r_[0.0, f]
    f = f * (I / _trapz(f, t))
    return dict(name=name, t=t, f=f, I=I, m_tot=m_tot / 1000, m_prop=m_prop / 1000,
                tb=float(t[-1]), L=L, delays=delays, avg=I / float(t[-1]), peak=float(f.max()),
                note=note)

def _eng(fname):
    """Read a RASP .eng file from Simulations/motors/ (downloaded from thrustcurve.org)."""
    t, f, hdr = [], [], None
    for ln in open(os.path.join(HERE, "motors", fname)):
        ln = ln.strip()
        if not ln or ln.startswith(";"): continue
        parts = ln.split()
        if hdr is None: hdr = parts; continue
        t.append(float(parts[0])); f.append(float(parts[1]))
    return hdr, t, f

def _from_eng(key, fname, I_cert, delays, price_note):
    hdr, t, f = _eng(fname)
    return _motor(key, t, f, I_cert, float(hdr[5]) * 1000, float(hdr[4]) * 1000, float(hdr[2]), delays, price_note)

# Budget rule (rev 3): no certification needed (G and below, <= 62.5 g propellant, <= 80 N avg) and
# <= $100 total for the flight motors. All three share the 29 x 83 mm single-use case.
# (rev 3c: the F67-9C was dropped from the trade. Its case is 112 mm long per its own .eng header
#  and thrustcurve.org, so it never fit the 83 mm bay. The Econojet F42-4T replaces it.)
MOTORS = {
    "F67-6W": _from_eng("AeroTech F67-6W", "AeroTech_F67W.eng", 61.1, [4, 6, 9],
        "single-use White Lightning 29x83 mm, 30 g propellant; $49.49 per 2-pack (eRockets, "
        "mailable, no hazmat) -> 4 motors $98.98"),
    "F42-4T": _from_eng("AeroTech F42-4T", "AeroTech_F42T.eng", 52.9, [4, 6, 8],
        "single-use Econojet Blue Thunder 29x83 mm, 27 g propellant; $43.99 per 2-pack "
        "(New Century Rocketry, 2026-10-16) -> 4 motors $87.98"),
    "G74-6W": _from_eng("AeroTech G74-6W", "AeroTech_G74W.eng", 82.75, [4, 6, 9],
        "single-use Economax 29x83 mm, 39.3 g propellant; price not found online (reference only)"),
}
FLIGHT_MOTOR = os.environ.get("WYV_MOTOR", "F42-4T")   # rev 3d: 600 ft cap, cheapest motor that fits

# =============================================================================================
# 5. ATMOSPHERE + DRAG
# =============================================================================================
G0 = 9.80665
RHO0, T0, P0, MU = 1.225, 288.15, 101325.0, 1.81e-5

def rho_at(h):
    T = T0 - 0.0065 * np.asarray(h)
    return P0 * (T / T0) ** 5.2559 / (287.05 * T)

def sound_speed(h):
    return np.sqrt(1.4 * 287.05 * (T0 - 0.0065 * np.asarray(h)))

A_REF = math.pi * (OD / 2000) ** 2          # m^2

def cd_total(v, h=0.0, cfin_H=CFIN_H_NOMINAL, rect_span=RECT_FIN["span"], motor_burning=True):
    """Component drag build-up (Barrowman / OpenRocket-style), referenced to A_REF."""
    v = max(float(v), 0.5)
    L = L_TOTAL / 1000; d = OD / 1000
    Re = rho_at(h) * v * L / MU
    cf = max(0.074 * Re ** -0.2, 1.328 / math.sqrt(max(Re, 1e4)) * 0.0 + 0.0025)
    s_body = math.pi * d * (L - 0.6 * NOSE["L"] / 1000)
    # fins: wetted = 2 sides; thickness form factor
    s_rect = RECT_FIN["n"] * 2 * (RECT_FIN["root"] / 1000) * (rect_span / 1000)
    s_cfin = 4 * 2 * 0.5 * (CFIN["root"] / 1000) * (cfin_H / 1000)
    cd_fric = cf * (s_body * (1 + 1.5 / (L / d) ** 1.5) + 1.12 * (s_rect + s_cfin)) / A_REF
    cd_nose = 0.01  # tangent ogive, subsonic pressure drag ~0
    cd_base = 0.0 if motor_burning else 0.12 * (1 - (MOTOR_D / OD) ** 2) + 0.03
    # blunt fin LE/TE pressure drag (3 mm rounded LE, square TE)
    cd_fin_p = (RECT_FIN["n"] * (RECT_FIN["t"] / 1000) * (rect_span / 1000) * 0.6
                + 4 * 0.0025 * (cfin_H / 1000) * 0.4) / A_REF
    cd_prot = 0.03   # rail buttons, fin root bosses, static ports
    return cd_fric + cd_nose + cd_base + cd_fin_p + cd_prot

# =============================================================================================
# 6. AERO: Barrowman normal force + slender-body interference
# =============================================================================================
def K_WB(tau):
    """Wing-in-presence-of-body factor (slender-body theory, Pitts/Nielsen/Kaattari),
    tau = r / s, s measured from the body axis to the fin tip."""
    tau = min(max(tau, 1e-4), 0.9999)
    t = tau
    num = (1 + t**4) * (0.5 * math.atan(0.5 * (1 / t - t)) + math.pi / 4) \
          - t**2 * ((1 / t - t) + 2 * math.atan(t))
    return (2 / math.pi) * num / (1 - t) ** 2

def barrowman_fin_cna(n, root, tip, span, sweep_le, d=OD):
    """Barrowman CN_alpha of an n-fin set (per rad, ref = body cross-section)."""
    mid_sweep = sweep_le + 0.5 * (tip - root) / 1.0 * 0.0
    lf = math.hypot(span, sweep_le + tip / 2 - root / 2)   # mid-chord line length
    cna = (4 * n * (span / d) ** 2) / (1 + math.sqrt(1 + (2 * lf / (root + tip)) ** 2))
    return cna

def barrowman_fin_xcp(root, tip, span, sweep_le, x_le):
    xr = sweep_le
    return x_le + xr * (root + 2 * tip) / (3 * (root + tip)) + \
        (root + tip - root * tip / (root + tip)) / 6

def cfin_geom(H, root=None):
    """Triangular control fin: LE swept from root LE to the tip, TE normal to the body."""
    c = CFIN["root"] if root is None else root
    return dict(root=c, tip=0.0, span=H, sweep=c, area=0.5 * c * H)

def bl_effectiveness(H, x_m, v, h=0.0):
    """Fraction of the control fin's free-stream normal force that survives the body's
    turbulent boundary layer (1/7-power profile, chord-weighted, q ~ u^2)."""
    v = max(v, 1.0)
    Re = rho_at(h) * v * x_m / MU
    dbl = 0.37 * x_m * Re ** -0.2 * 1000.0      # mm
    y = np.linspace(0, H, 200)
    chord = 1 - y / H                             # triangular planform
    q_ratio = np.where(y < dbl, (np.clip(y, 1e-6, None) / dbl) ** (2 / 7), 1.0)
    return float(_trapz(chord * q_ratio, y) / _trapz(chord, y)), dbl


INTERF_SCALE = float(os.environ.get("WYV_INTERF", 1.0))   # 1.0 = pessimistic single-vortex bound

def vortex_interference(H, rect_span=None, offset_deg=None, bprime=0.70, scale=None):
    """Nielsen-type control-fin -> fixed-fin interference: induced normal force on the 4 fixed
    fins divided by the normal force of the lifting control pair (same direction = +).

    One concentrated trailing vortex per lifting control fin at y_v = (R + gap) + b' H, plus its
    image inside the body (R^2 / y_v); strip theory on each fixed fin with its own per-area lift
    slope. b' ~ 0.70 (between pi/4 elliptic and the VLM centroid). Single-vortex models
    over-predict the near field when the sheet has not rolled up, so treat this as the
    pessimistic bound; the in-flight doublets (RQ3) measure the real value.
    Applies to ANY lift on the pair (angle of attack or deflection)."""
    rs = RECT_FIN["span"] if rect_span is None else rect_span
    off = RECT_FIN["az0_deg"] if offset_deg is None else offset_deg
    Rr = R + CFIN["gap"]; yv = Rr + bprime * H
    vort = [(yv, 0.0, 1.0), (-yv, 0.0, -1.0), (R * R / yv, 0.0, -1.0), (-R * R / yv, 0.0, 1.0)]
    rf = RECT_FIN; S_r = rf["root"] * rs
    a_r = barrowman_fin_cna(1, rf["root"], rf["tip"], rs, 0.0) * 2 * (math.pi * OD ** 2 / 4) / S_r
    rr = np.linspace(R + 0.5, R + rs, 200); F = 0.0
    for ph in np.radians([off, off + 90, off + 180, off + 270]):
        n = np.array([-math.sin(ph), math.cos(ph)])
        py, pz = rr * math.cos(ph), rr * math.sin(ph); wn = np.zeros_like(rr)
        for vy, vz, k in vort:
            dy, dz = py - vy, pz - vz; r2 = np.maximum(dy * dy + dz * dz, 25.0)  # 5 mm viscous core
            wn += (-k * dz / (2 * math.pi * r2)) * n[0] + (k * dy / (2 * math.pi * r2)) * n[1]
        F += float(_trapz(a_r * rf["root"] * wn, rr)) * n[1]
    return (INTERF_SCALE if scale is None else scale) * 0.5 * F / (2 * bprime * H)

def nose_cp():
    L = NOSE["L"]
    return 2.0, (0.466 * L if NOSE["type"] == "tangent_ogive" else 0.333 * L)

def stability(cg_mm, H=CFIN_H_NOMINAL, rect_span=RECT_FIN["span"], interference=True):
    """Static CP / margin with all fins at zero deflection."""
    cna_n, xn = nose_cp()
    rf = RECT_FIN
    k_r = K_WB(R / (R + rect_span))
    cna_r = barrowman_fin_cna(4, rf["root"], rf["tip"], rect_span, 0.0) * k_r
    xr = barrowman_fin_xcp(rf["root"], rf["tip"], rect_span, 0.0, X_RECT_LE)
    g = cfin_geom(H)
    k_c = K_WB(R / (R + H))
    cna_c = barrowman_fin_cna(4, g["root"], 0.0, H, g["sweep"]) * k_c
    # the fin's root LE is 45 % of the root chord ahead of the hinge
    x_le_A = X_HINGE_A - CFIN["hinge_frac"] * g["root"]
    x_le_B = X_HINGE_B - CFIN["hinge_frac"] * g["root"]
    xc = barrowman_fin_xcp(g["root"], 0.0, H, g["sweep"], 0.5 * (x_le_A + x_le_B))
    I = vortex_interference(H, rect_span) if interference else 0.0
    cna_i = I * cna_c                       # load the control fins' downwash induces on the fixed fins
    cna = cna_n + cna_r + cna_c + cna_i
    xcp = (cna_n * xn + cna_r * xr + cna_c * xc + cna_i * xr) / cna
    return dict(cna=cna, xcp=xcp, margin_cal=(xcp - cg_mm) / OD, cna_nose=cna_n, x_nose=xn,
                cna_rect=cna_r, x_rect=xr, cna_cfin=cna_c, x_cfin=xc, K_rect=k_r, K_cfin=k_c,
                interference=I)

# =============================================================================================
# 7. MASS PROPERTIES
# =============================================================================================
def printed_parts():
    """Printed-part masses from the CAD generator (falls back to analytic estimates)."""
    if os.path.exists(MASS_REPORT):
        rep = json.load(open(MASS_REPORT))
        return [(p["name"], p["mass_g"], p["x_cg_mm"], p["length_mm"]) for p in rep["parts"]
                if p.get("flight", True)]
    # analytic fallback (thin tubes), used only before the first CAD run
    def tube_g(L, mat): return math.pi * (R**2 - RI**2) * L / 1000 * DENS[mat]
    return [("nose", 45.0, 0.6 * NOSE["L"], NOSE["L"]),
            ("RB tube", tube_g(L_RB, "ASAAERO"), X_RB_TOP + L_RB / 2, L_RB),
            ("CT tube+ribs", tube_g(L_CT, "ASA") * 1.5, X_CT_TOP + L_CT / 2, L_CT),
            ("MB tube", tube_g(L_MB, "ASA"), X_MB_TOP + L_MB / 2, L_MB),
            ("couplers", 40.0, X_CT_TOP + L_CT / 2, L_CT),
            ("MMT+plenum", 35.0, X_MOTOR_TOP + 60, 124),
            ("rect fins", 4 * 120 * 40 * 3 / 1000 * 1.3, X_RECT_LE + 60, 120),
            ("control fins+hubs", 16.0, 0.5 * (X_HINGE_A + X_HINGE_B), 60)]

def bypass_mass():
    a = math.pi / 4 * (BYPASS["od"] ** 2 - BYPASS["id"] ** 2)
    return a * BYPASS["L"] / 1000 * BYPASS["density"]

def mass_properties(motor=None, t=0.0, H=CFIN_H_NOMINAL, ballast_g=None, rect_span=None):
    """Total mass (kg), CG (mm from nose), pitch inertia about CG (kg m^2) at time t.
    rect_span / H different from the CAD run are handled by scaling the blade masses."""
    motor = motor or FLIGHT_MOTOR
    m = MOTORS[motor]
    items = []
    cad_span = RECT_FIN["span"]
    for it in printed_parts():
        name, mg, x, Lc = it
        if name.startswith("12_rect_fin") and rect_span is not None and rect_span != cad_span:
            blade = 4 * RECT_FIN["root"] * RECT_FIN["t"] * DENS["PETGCF"] / 1000
            mg = mg + blade * (rect_span - cad_span)
        if name.startswith("control fins") and H != CFIN_H_NOMINAL:
            mg = mg * (H / CFIN_H_NOMINAL) ** 1.0
        items.append((name, mg, x, Lc))
    cots = [list(c) for c in COTS]
    if ballast_g is not None: cots[0][1] = ballast_g
    items += [tuple(c) for c in cots]
    items.append(("bypass tube", bypass_mass(), 0.5 * (X_BYPASS_TOP + X_BYPASS_BOT), BYPASS["L"]))
    burn = min(max(t, 0.0), m["tb"])
    # propellant burns out linearly in impulse fraction
    frac_I = 0.0 if t <= 0 else float(_trapz(m["f"][m["t"] <= burn], m["t"][m["t"] <= burn]) / m["I"]) if burn < m["tb"] else 1.0
    m_motor = (m["m_tot"] - m["m_prop"] * frac_I) * 1000
    x_motor_top = X_MOTOR_AFT - m["L"]
    items.append(("motor " + motor, m_motor, x_motor_top + m["L"] / 2, m["L"]))
    M = sum(i[1] for i in items)
    xcg = sum(i[1] * i[2] for i in items) / M
    I = 0.0
    for _, mg, x, Lc in items:
        mk = mg / 1000; dx = (x - xcg) / 1000; Lm = Lc / 1000
        I += mk * (dx * dx + Lm * Lm / 12 + (R / 1000) ** 2 / 4)
    return M / 1000, xcg, I, items

def report():
    out = {}
    for mot in MOTORS:
        M0, cg0, I0, items = mass_properties(mot, 0.0)
        Mb, cgb, Ib, _ = mass_properties(mot, 99.0)
        st0 = stability(cg0); stb = stability(cgb)
        out[mot] = dict(liftoff_g=round(M0 * 1000, 1), burnout_g=round(Mb * 1000, 1),
                        cg_liftoff_mm=round(cg0, 1), cg_burnout_mm=round(cgb, 1),
                        cp_mm=round(st0["xcp"], 1), margin_liftoff_cal=round(st0["margin_cal"], 2),
                        margin_burnout_cal=round(stb["margin_cal"], 2),
                        Iyy_kgm2=round(I0, 5), TW_avg=round(MOTORS[mot]["avg"] / (M0 * G0), 2),
                        TW_peak=round(MOTORS[mot]["peak"] / (M0 * G0), 2),
                        arm_A_mm=round(X_HINGE_A - cg0, 1), arm_B_mm=round(X_HINGE_B - cg0, 1))
    geom = dict(L_total_mm=L_TOTAL, OD_mm=OD, nose_L=NOSE["L"], L_RB=L_RB, L_CT=L_CT, L_MB=L_MB,
                x_hinge_A=X_HINGE_A, x_hinge_B=X_HINGE_B, x_imu=X_IMU,
                x_rect_le=X_RECT_LE, rect_fin=RECT_FIN, cfin=CFIN, cfin_heights=CFIN_HEIGHTS,
                bypass=BYPASS, servo_base_r=round(SERVO_BASE_R, 2), ballast_g=BALLAST_G)
    return dict(geometry=geom, vehicles=out)

if __name__ == "__main__":
    import sys
    r = report()
    print(json.dumps(r["vehicles"], indent=2))
    print("servo base radius", round(SERVO_BASE_R, 2), "mm; hinge A/B", X_HINGE_A, X_HINGE_B,
          "IMU", X_IMU, "L", L_TOTAL)
    print("K_WB tau 0.5/0.64:", round(K_WB(0.5), 3), round(K_WB(R / (R + 20)), 3))
    if "--report" in sys.argv:
        json.dump(r, open(os.path.join(HERE, "canonical_numbers.json"), "w"), indent=2, default=float)
