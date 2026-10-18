#!/usr/bin/env python3
"""GTR70E WYVERN -- vehicle drawings generated from wf_core (never hand-edited).

D1_vehicle_layout      side elevation, stations, CG/CP, internal layout, section callouts
D2_cross_sections      four sections: servo ring, IMU deck, avionics spine, motor bay at fins
D3_assembly_stages     the separate tubes and the order they go together
Outputs SVG + PNG next to this script.
"""
import math, os, sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch, Wedge, FancyBboxPatch
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Simulations"))
import wf_core as C

INK = "#1b1f24"; MUTED = "#6b7280"; GRID = "#e5e7eb"
COL = dict(nose="#dbe4ee", rb="#e8eef5", ct="#cfd8e3", mb="#c3ccd8", coupler="#9aa5b4",
           cfin="#c2410c", rfin="#334155", servo="#2563eb", bypass="#a1a1aa", fc="#15803d",
           batt="#ca8a04", motor="#7c3aed", plenum="#b45309", chute="#f59e0b", imu="#db2777")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": INK})

def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), dpi=170 if ext == "png" else None, bbox_inches="tight", facecolor="white")
    plt.close(fig); print("wrote", name)

def ogive_pts(L, R, n=60, x0=0.0):
    rho = (R * R + L * L) / (2 * R)
    xs = np.linspace(0, L, n)
    ys = np.sqrt(np.maximum(rho ** 2 - (L - xs) ** 2, 0)) + R - rho
    return xs + x0, ys

def dim(ax, x0, x1, y, text, above=True, fs=7):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", lw=0.6, color=INK))
    ax.text((x0 + x1) / 2, y + (2.5 if above else -2.5), text, ha="center", va="bottom" if above else "top", fontsize=fs, color=INK)
    for x in (x0, x1): ax.plot([x, x], [y - 2, y + 2], lw=0.5, color=INK)

def vehicle_layout():
    M0, cg0, I0, _ = C.mass_properties(C.FLIGHT_MOTOR, 0.0)
    Mb, cgb, _, _ = C.mass_properties(C.FLIGHT_MOTOR, 99.0)
    st = C.stability(cg0)
    R = C.R
    fig, ax = plt.subplots(figsize=(17, 6.6))
    ax.set_aspect("equal"); ax.axis("off")
    # --- body sections
    xs, ys = ogive_pts(C.NOSE["L"], R)
    ax.fill(np.r_[xs, xs[::-1]], np.r_[ys, -ys[::-1]], color=COL["nose"], ec=INK, lw=0.9)
    for (x0, x1, c, lab) in ((C.X_RB_TOP, C.X_RB_BOT, COL["rb"], "RECOVERY BAY TUBE"),
                             (C.X_CT_TOP, C.X_CT_BOT, COL["ct"], "CONTROL TUBE (avionics spine + servo ring)"),
                             (C.X_MB_TOP, C.X_MB_BOT, COL["mb"], "MOTOR BAY TUBE")):
        ax.add_patch(Rectangle((x0, -R), x1 - x0, 2 * R, fc=c, ec=INK, lw=0.9, zorder=1))
        ax.text((x0 + x1) / 2, R + 104, lab, ha="center", fontsize=8, weight="bold", color=INK)
    # couplers (dashed internal)
    for xj in (C.X_RB_BOT, C.X_CT_BOT):
        ax.add_patch(Rectangle((xj - 20, -C.RI + 0.2), 40, 2 * C.RI - 0.4, fill=False, ec=COL["coupler"], lw=0.8, ls="--", zorder=2))
    ax.add_patch(Rectangle((C.NOSE["L"], -C.RI + 0.2), C.NOSE["shoulder"], 2 * C.RI - 0.4, fill=False, ec=COL["coupler"], lw=0.8, ls="--"))
    # recovery bay floor bulkhead
    ax.add_patch(Rectangle((C.X_RB_BOT - 1.5, -C.RI), 3, 2 * C.RI, fc=COL["plenum"], ec=INK, lw=0.4, zorder=3))
    # chute bundle, nomex, cord
    ax.add_patch(FancyBboxPatch((C.X_RB_TOP + 55, -24), 95, 48, boxstyle="round,pad=2", fc=COL["chute"], ec=INK, lw=0.5, alpha=0.55))
    ax.text(C.X_RB_TOP + 102, 0, "24 in chute\n+ Nomex", ha="center", va="center", fontsize=7)
    tt = np.linspace(C.X_RB_TOP + 165, C.X_RB_BOT - 12, 80)
    ax.plot(tt, 6 * np.sin((tt - tt[0]) / 7), color="#92400e", lw=0.9)
    ax.text(C.X_RB_BOT - 85, 16, "aramid shock cord (nose <-> RB-floor M5 eyebolt)", fontsize=6.5, ha="center")
    # ballast
    ax.add_patch(Polygon([[12, -4], [12, 4], [45, 10], [45, -10]], fc="#525252", ec=INK, lw=0.4))
    ax.text(30, -26, f"ballast {C.BALLAST_G:.0f} g", fontsize=6.5, ha="center")
    # bypass tube on the centreline
    ax.add_patch(Rectangle((C.X_BYPASS_TOP, -C.BYPASS["od"] / 2), C.BYPASS["L"], C.BYPASS["od"], fc=COL["bypass"], ec=INK, lw=0.5, alpha=0.95, zorder=4))
    ax.annotate("ejection bypass tube on the centreline\n3/8 in OD Al, plenum -> RB floor", xy=(C.X_BYPASS_TOP + 30, 4), xytext=(C.X_BYPASS_TOP - 60, R + 62),
                fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5), ha="center")
    zb = C.X_CT_BOT
    xs0 = zb - C.SPINE_Z0 - C.SPINE_L
    ax.add_patch(Rectangle((xs0, -C.SPINE_FLAT), C.SPINE_L, 2 * C.SPINE_FLAT, fc="#bbf7d0", ec=INK, lw=0.5, zorder=3))
    ax.add_patch(Rectangle((xs0 - 1, -C.BYPASS["od"] / 2), C.SPINE_L + 2, C.BYPASS["od"], fc=COL["bypass"], ec=INK, lw=0.5, zorder=4))
    for bd in C.SPINE_BOARDS:
        if bd["face"] not in ("px", "nx"): continue
        sgn = 1 if bd["face"] == "px" else -1; P = C.board_plane(bd)
        th = 14.0 if bd["key"] == "battery" else 1.6
        x0b = zb - C.SPINE_Z0 - bd["z0"] - bd["L"]
        col = COL["batt"] if bd["key"] == "battery" else (COL["imu"] if bd["key"] == "bno085" else COL["fc"])
        ax.add_patch(Rectangle((x0b, sgn * P if sgn > 0 else -P - th), bd["L"], th, fc=col, ec=INK, lw=0.5, zorder=5))
        lab = dict(bno085="BNO085", feather="Feather RFM95", battery="2S 450 mAh", adxl375="ADXL375", gps="GPS", bme688="BME688", microsd="microSD").get(bd["key"], bd["key"])
        ax.text(x0b + bd["L"] / 2, sgn * (P + th + 4) if sgn > 0 else -P - th / 2, lab, fontsize=5.8, ha="center", va="center", color="white" if sgn < 0 else col, weight="bold", zorder=6)
    ax.annotate("avionics spine around the tube:\n+Y power perfboard (switch, buck, screw sw.)\n-Y BME688 + microSD", xy=(xs0 + 35, -5), xytext=(xs0 - 70, -R - 40),
                fontsize=6.5, arrowprops=dict(arrowstyle="-", lw=0.5), ha="center", color="#166534")
    ax.plot([xs0 + 5, xs0 + 70], [C.RI - 3, C.RI - 3], color="#0284c7", lw=1.2)
    ax.text(xs0 + 2, C.RI - 3, "915 MHz whip", fontsize=6, ha="right", va="center", color="#0284c7")
    ax.plot([xs0 + 3, xs0 + 3], [R - 1.6, R], color="red", lw=2)
    ax.annotate("BNO085: lowest board on the spine, right above the servo ring", xy=(C.X_IMU, 12), xytext=(C.X_IMU + 10, R + 40), fontsize=7,
                arrowprops=dict(arrowstyle="-", lw=0.5), ha="center", color=COL["imu"])
    sv = C.SERVO
    zc = C.X_HINGE - (sv["L"] / 2 - sv["shaft_from_end"])
    for sgn in (1, -1):
        y0 = C.SERVO_BASE_R if sgn > 0 else -(C.SERVO_BASE_R + sv["H"])
        ax.add_patch(Rectangle((zc - sv["L"] / 2, y0), sv["L"], sv["H"], fc=COL["servo"], ec=INK, lw=0.5, alpha=0.9, zorder=6))
        ax.add_patch(Rectangle((zc - sv["ear_span"] / 2, sgn * C.PAD_INNER_R - (sv["ear_t"] if sgn > 0 else 0)), sv["ear_span"], sv["ear_t"], fc=COL["servo"], ec=INK, lw=0.4, zorder=6))
    ax.annotate(f"servo ring: 4 x {sv['name']} at ONE station,\nears bolted to wall pads, shafts radial", xy=(zc, -C.SERVO_BASE_R - 10), xytext=(zc - 10, -R - 66),
                fontsize=6.8, color=COL["servo"], arrowprops=dict(arrowstyle="-", lw=0.5, color=COL["servo"]), ha="center")
    # control fins: A pair in plane, B pair edge-on, same station
    H = C.CFIN_H_NOMINAL; c = C.CFIN["root"]; hf = C.CFIN["hinge_frac"]
    xh = C.X_HINGE; xle, xte = xh - hf * c, xh + (1 - hf) * c; r0 = R + C.CFIN["gap"]
    for sgn in (1, -1):
        ax.add_patch(Polygon([[xle, sgn * r0], [xte, sgn * r0], [xte, sgn * (r0 + H)]], fc=COL["cfin"], ec=INK, lw=0.6, zorder=7))
        ax.plot([xh, xh], [sgn * (R - 4), sgn * (r0 + 6)], color=INK, lw=1.4, zorder=8)
    ax.add_patch(Rectangle((xle, -1.5), c, 3, fc=COL["cfin"], ec=INK, lw=0.4, zorder=3, alpha=0.6))
    ax.annotate(f"4 servo-driven triangular control fins, all at x = {xh:.0f}\n(root {c:.0f} mm, H = {H:.0f} mm design point)",
                xy=(xh + 10, R + H * 0.6), xytext=(xh - 60, R + 78), fontsize=7.5, color=COL["cfin"],
                arrowprops=dict(arrowstyle="-", lw=0.5, color=COL["cfin"]), ha="center")
    # rectangular fins at 45 deg (projected span x cos45)
    rf = C.RECT_FIN; sp = rf["span"] * math.cos(math.radians(45))
    for s in (1, -1):
        ax.add_patch(Polygon([[C.X_RECT_LE, s * R], [C.X_RECT_LE + rf["root"], s * R], [C.X_RECT_LE + rf["root"], s * (R + sp)], [C.X_RECT_LE, s * (R + sp)]],
                             fc=COL["rfin"], ec=INK, lw=0.6, alpha=0.85, zorder=7))
    ax.annotate(f"stabilizers x4 at 45 deg\n{rf['root']:.0f} x {rf['span']:.0f} mm, run the motor length",
                xy=(C.X_RECT_LE + 60, R + sp), xytext=(C.X_RECT_LE + 90, R + 52), fontsize=7.5, color=COL["rfin"],
                arrowprops=dict(arrowstyle="-", lw=0.5), ha="center")
    # motor, MMT, plenum, gallery, retainer
    ax.add_patch(Rectangle((C.X_PLENUM_TOP, -C.RI), C.PLENUM_T, 2 * C.RI, fc=COL["plenum"], ec=INK, lw=0.5, zorder=5))
    ax.add_patch(Rectangle((C.X_PLENUM_TOP + C.PLENUM_T, -C.RI), C.GALLERY_H, 2 * C.RI, fc="#fde68a", ec=INK, lw=0.3, zorder=4))
    ax.add_patch(Rectangle((C.X_MOTOR_TOP, -C.MMT_ID / 2 - C.MMT_WALL), C.X_MOTOR_AFT - C.X_MOTOR_TOP, C.MMT_ID + 2 * C.MMT_WALL, fc="#ddd6fe", ec=INK, lw=0.5, zorder=4))
    ax.add_patch(Rectangle((C.X_MOTOR_TOP, -C.MOTOR_D / 2), C.MOTORS[C.FLIGHT_MOTOR]["L"], C.MOTOR_D, fc=COL["motor"], ec=INK, lw=0.5, alpha=0.8, zorder=5))
    ax.text(C.X_MOTOR_TOP + C.MOTORS[C.FLIGHT_MOTOR]["L"] / 2, 0, f"AeroTech {C.FLIGHT_MOTOR}\n29 x {C.MOTORS[C.FLIGHT_MOTOR]['L']:.0f} mm", color="white", fontsize=7, ha="center", va="center", zorder=6, weight="bold")
    ax.annotate(f"plenum + {C.GALLERY_H:.0f} mm gas gallery", xy=(C.X_PLENUM_TOP + 4, -C.RI + 4), xytext=(C.X_PLENUM_TOP + 60, -R - 62), fontsize=7,
                arrowprops=dict(arrowstyle="-", lw=0.5), ha="center", color=COL["plenum"])
    ax.add_patch(Rectangle((C.X_MB_BOT, -R - 2.2), 3, 2 * R + 4.4, fc=COL["plenum"], ec=INK, lw=0.4))
    # CG / CP
    def mark(x, label, color, y):
        ax.add_patch(Circle((x, 0), 5, fc="white", ec=color, lw=1.4, zorder=10))
        ax.add_patch(Wedge((x, 0), 5, 0, 90, fc=color, zorder=11)); ax.add_patch(Wedge((x, 0), 5, 180, 270, fc=color, zorder=11))
        ax.text(x, y, label, ha="center", fontsize=7.5, color=color, weight="bold")
    mark(cg0, f"CG {cg0:.0f}", "#111827", -R - 66)
    ax.plot([st["xcp"], st["xcp"]], [-6, 6], color="#dc2626", lw=2, zorder=10)
    ax.add_patch(Circle((st["xcp"], 0), 5, fc="none", ec="#dc2626", lw=1.4, zorder=10))
    ax.text(st["xcp"], -R - 80, f"CP {st['xcp']:.0f}  (SM {st['margin_cal']:.2f} cal)", ha="center", fontsize=7.5, color="#dc2626", weight="bold")
    # dimensions
    yd = -R - 110
    dim(ax, 0, C.NOSE["L"], yd, f"nose {C.NOSE['L']:.0f}", above=False)
    dim(ax, C.X_RB_TOP, C.X_RB_BOT, yd, f"recovery bay {C.L_RB:.0f}", above=False)
    dim(ax, C.X_CT_TOP, C.X_CT_BOT, yd, f"control tube {C.L_CT:.0f}", above=False)
    dim(ax, C.X_MB_TOP, C.X_MB_BOT, yd, f"motor bay {C.L_MB:.0f}", above=False)
    dim(ax, 0, C.L_TOTAL, yd - 22, f"overall {C.L_TOTAL:.0f} mm   |   OD {C.OD:.0f} mm   |   liftoff {M0*1000:.0f} g ({C.FLIGHT_MOTOR})", above=False, fs=8)
    # separation callout
    ax.annotate("ONLY separation plane\n(nose pops on motor ejection)", xy=(C.NOSE["L"], R), xytext=(C.NOSE["L"] - 40, R + 85),
                fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8, color="#dc2626"), ha="center", color="#dc2626")
    for xj in (C.X_RB_BOT, C.X_CT_BOT):
        ax.text(xj, -R - 98, "screwed joint\n3 x M3 (service)", ha="center", fontsize=6, color=MUTED)
    # station ruler
    for x in range(0, int(C.L_TOTAL) + 1, 50):
        ax.plot([x, x], [R + 120, R + 124 if x % 100 else R + 128], color=MUTED, lw=0.5)
        if x % 100 == 0: ax.text(x, R + 131, f"{x}", fontsize=6, ha="center", color=MUTED)
    ax.plot([0, C.L_TOTAL], [R + 120, R + 120], color=MUTED, lw=0.5)
    ax.text(-8, R + 120, "station (mm from nose tip)", fontsize=6.5, ha="right", va="center", color=MUTED)
    ax.set_xlim(-60, C.L_TOTAL + 30); ax.set_ylim(-R - 150, R + 150)
    ax.set_title(f"GTR70E WYVERN  —  fin-controlled {C.OD:.0f} mm research rocket, side elevation (view along -Y; pitch-pair fins in plane, 45° fins foreshortened)",
                 fontsize=10, loc="left", color=INK)
    save(fig, "D1_vehicle_layout")

def cross_sections():
    R, RI = C.R, C.RI
    fig, axs = plt.subplots(1, 4, figsize=(17, 5))
    sv = C.SERVO; H = C.CFIN_H_NOMINAL
    def body(ax, title):
        ax.set_aspect("equal"); ax.axis("off")
        ax.add_patch(Circle((0, 0), R, fc="#e5e7eb", ec=INK, lw=1)); ax.add_patch(Circle((0, 0), RI, fc="white", ec=INK, lw=0.6))
        ax.set_title(title, fontsize=9, color=INK); ax.set_xlim(-R - 52, R + 52); ax.set_ylim(-R - 52, R + 52)
        ax.plot([-R - 45, R + 45], [0, 0], color=GRID, lw=0.5, zorder=0); ax.plot([0, 0], [-R - 45, R + 45], color=GRID, lw=0.5, zorder=0)
        ax.text(R + 46, 2, "+X", fontsize=7, color=MUTED); ax.text(2, R + 44, "+Y", fontsize=7, color=MUTED)
    def bypass(ax):
        ax.add_patch(Circle((0, 0), C.BYPASS["od"] / 2, fc=COL["bypass"], ec=INK, lw=0.6, zorder=5))
        ax.add_patch(Circle((0, 0), C.BYPASS["id"] / 2, fc="white", ec=INK, lw=0.3, zorder=6))
    def rot(pts, az):
        a = math.radians(az); ca, sa = math.cos(a), math.sin(a)
        return [(x * ca - y * sa, x * ca * 0 + x * sa + y * ca) for (x, y) in pts]
    def rect(ax, x0, x1, w, az, **kw):
        ax.add_patch(Polygon(rot([(x0, -w / 2), (x1, -w / 2), (x1, w / 2), (x0, w / 2)], az), **kw))
    # A-A servo ring
    ax = axs[0]; body(ax, f"A–A  servo ring, all four fins  x = {C.X_HINGE:.0f}")
    for az in (0, 90, 180, 270):
        rect(ax, C.PAD_INNER_R, RI + 0.3, 16, az, fc="#cbd5e1", ec=INK, lw=0.3, zorder=2)
        rect(ax, C.SERVO_BASE_R, C.SERVO_TOP_R, sv["W"], az, fc=COL["servo"], ec=INK, lw=0.5, zorder=3)
        rect(ax, C.SERVO_TOP_R, C.SPLINE_TOP_R, 5, az, fc=INK, zorder=4)
        rect(ax, C.SPLINE_TOP_R, 42, C.CFIN["hub_d"], az, fc="#94a3b8", ec=INK, lw=0.4, zorder=4)
        rect(ax, R + C.CFIN["gap"], R + C.CFIN["gap"] + H, 2.4, az, fc=COL["cfin"], ec=INK, lw=0.5, zorder=4)
    bypass(ax)
    ax.annotate(f"servo bases at r = {C.SERVO_BASE_R:.1f} mm, {C.SERVO_BASE_R - C.BYPASS['od']/2:.2f} mm\nclear of the 3/8 in tube; leads run up the diagonal gaps", xy=(-6, -6), xytext=(-55, -72), fontsize=6.5, arrowprops=dict(arrowstyle="-", lw=0.4), ha="center")
    ax.annotate(f"{sv['name']}\n{sv['L']:.1f} x {sv['W']:.0f} x {sv['H']:.1f} mm", xy=(18, 3), xytext=(30, 44), fontsize=6.5, arrowprops=dict(arrowstyle="-", lw=0.4), color=COL["servo"])
    ax.annotate("wall pad: ears bolt to its inner face,\nservo top through the window", xy=(27, -7), xytext=(30, -66), fontsize=6.3, arrowprops=dict(arrowstyle="-", lw=0.4))
    def spine_slab(ax, zrel, title):
        body(ax, title)
        f = C.SPINE_FLAT
        ax.add_patch(Rectangle((-f, -f), 2 * f, 2 * f, fc="#bbf7d0", ec=INK, lw=0.5, zorder=3))
        bypass(ax)
        for bd in C.SPINE_BOARDS:
            if not (bd["z0"] <= zrel <= bd["z0"] + bd["L"]): continue
            P = C.board_plane(bd); th = 14.0 if bd["key"] == "battery" else 1.6
            comp = 0 if bd["key"] == "battery" else (3.5 if bd["key"] != "perfboard" else 6.0)
            off = bd.get("offset", 0.0)
            col = dict(battery=COL["batt"], bno085=COL["imu"], feather=COL["fc"], perfboard="#7c2d12").get(bd["key"], "#0891b2")
            az = dict(px=0, py=90, nx=180, ny=270)[bd["face"]]
            rect(ax, P, P + th, bd["W"], az, fc=col, ec=INK, lw=0.5, zorder=4) if off == 0 else None
            if off:
                a_ = math.radians(az); ca, sa = math.cos(a_), math.sin(a_)
                pts = [(P, off - bd["W"] / 2), (P + th, off - bd["W"] / 2), (P + th, off + bd["W"] / 2), (P, off + bd["W"] / 2)]
                ax.add_patch(Polygon([(x * ca - y * sa, x * sa + y * ca) for x, y in pts], fc=col, ec=INK, lw=0.5, zorder=4))
            if comp:
                cw = bd["W"] * 0.7
                a_ = math.radians(az); ca, sa = math.cos(a_), math.sin(a_)
                pts = [(P + th, off - cw / 2), (P + th + comp, off - cw / 2), (P + th + comp, off + cw / 2), (P + th, off + cw / 2)]
                ax.add_patch(Polygon([(x * ca - y * sa, x * sa + y * ca) for x, y in pts], fc=col, ec=INK, lw=0.3, alpha=0.35, zorder=4))
            name = dict(battery="2S LiPo", bno085="BNO085", feather="Feather RFM95", perfboard="perfboard", bme688="BME688", microsd="microSD", gps="GPS", adxl375="ADXL375")[bd["key"]]
            lx, ly = {0: (44, 8), 90: (0, R + 20), 180: (-46, 8), 270: (0, -R - 20)}[az]
            ax.text(lx, ly, name, fontsize=6.5, ha="center", color=col, weight="bold")
        ax.text(0, -R - 40, "board positions from wf_core.SPINE_BOARDS;\nvendor-model check in D6", fontsize=6, ha="center", color=MUTED)
    zz0 = C.X_CT_BOT - C.SPINE_Z0
    spine_slab(axs[1], 18.0, f"B–B  spine, low  x ≈ {zz0 - 18:.0f}")
    spine_slab(axs[2], 55.0, f"C–C  spine, high  x ≈ {zz0 - 55:.0f}")
    for ax in (axs[1], axs[2]):
        for az in (20, 110, 200, 290):
            a = math.radians(az); ax.plot([RI * math.cos(a), R * math.cos(a)], [RI * math.sin(a), R * math.sin(a)], color="red", lw=1.0, alpha=0.5)
    # D-D motor bay
    ax = axs[3]; body(ax, f"D–D  motor bay at the stabilizers  x ≈ {C.X_RECT_LE + 60:.0f}")
    ax.add_patch(Circle((0, 0), C.MMT_ID / 2 + C.MMT_WALL, fc="#ddd6fe", ec=INK, lw=0.6))
    ax.add_patch(Circle((0, 0), C.MOTOR_D / 2, fc=COL["motor"], ec=INK, lw=0.5, alpha=0.8))
    rf = C.RECT_FIN
    for i in range(4):
        a = math.radians(rf["az0_deg"] + 90 * i)
        n = np.array([math.cos(a), math.sin(a)]); t = np.array([-math.sin(a), math.cos(a)]) * rf["t"] / 2
        r_in = C.MMT_ID / 2 + C.MMT_WALL
        ax.add_patch(Polygon([n * r_in + t, n * (R + rf["span"]) + t, n * (R + rf["span"]) - t, n * r_in - t], fc=COL["rfin"], ec=INK, lw=0.5))
    for i in range(4):
        a = math.radians(90 * i)
        ax.plot([R * math.cos(a), (R + 1 + H) * math.cos(a)], [R * math.sin(a), (R + 1 + H) * math.sin(a)], color=COL["cfin"], lw=1.2, ls=":", alpha=0.8)
    ax.text(0, -R - 46, "control fins (dotted, upstream) at 0/90/180/270;\nstabilizers at 45° with through-the-wall tabs bonded to the MMT", fontsize=6.5, ha="center")
    a = math.radians(C.RAIL_BUTTON_AZ_DEG); ax.add_patch(Circle(((R + 4) * math.cos(a), (R + 4) * math.sin(a)), 4, fc="#facc15", ec=INK, lw=0.5))
    ax.text((R + 12) * math.cos(a), (R + 12) * math.sin(a) - 9, "1010 button\n(az 22.5°)", fontsize=6)
    fig.suptitle("Cross-sections, viewed from the nose looking aft (+Z toward the viewer).  Grey ring at the centre = ejection bypass tube on the vehicle axis.", fontsize=9, x=0.02, ha="left")
    save(fig, "D2_cross_sections")

def assembly_stages():
    R = C.R
    fig, ax = plt.subplots(figsize=(17, 6.8)); ax.set_aspect("equal"); ax.axis("off")
    gap = 70
    parts = [("Nose cone", 0, C.NOSE["L"] + C.NOSE["shoulder"], COL["nose"], "ballast bay, shock-cord bar,\nonly part that separates"),
             ("Recovery bay tube", C.X_RB_TOP, C.L_RB, COL["rb"], "chute, Nomex, cord;\nRB-floor coupler bonded in its aft end"),
             ("Control tube", C.X_CT_TOP, C.L_CT, COL["ct"], "servo-ring pads printed in;\nspine above, 4 servos + hubs at one station"),
             ("Motor bay tube", C.X_MB_TOP - 20, C.L_MB + 20, COL["mb"], "integral shoulder, plenum + gallery,\nMMT, 4 stabilizers, retainer")]
    x = 0
    for i, (name, _, L, col, note) in enumerate(parts):
        ax.add_patch(Rectangle((x, -R), L, 2 * R, fc=col, ec=INK, lw=0.9))
        ax.text(x + L / 2, R + 14, f"{i+1}. {name}", ha="center", fontsize=8.5, weight="bold")
        ax.text(x + L / 2, -R - 10, note, ha="center", va="top", fontsize=7, color=MUTED)
        if i < 3:
            ax.annotate("", xy=(x + L + gap - 8, 0), xytext=(x + L + 8, 0), arrowprops=dict(arrowstyle="<->", lw=1.0, color=INK))
        x += L + gap
    # bypass tube drawn separately
    ax.add_patch(Rectangle((C.NOSE["L"] + 50, R + 60), C.BYPASS["L"], 12, fc=COL["bypass"], ec=INK, lw=0.6))
    ax.text(C.NOSE["L"] + 50 + C.BYPASS["L"] / 2, R + 78, f"5. bypass tube ({C.BYPASS['L']:.0f} mm, O-ring both ends) — goes in LAST from the top, before the chute is packed",
            ha="center", fontsize=7.5)
    steps = ["STAGE 1  Motor bay: bond MMT + stabilizers (TTW tabs) + plenum skirt (central socket); inserts in aft ring",
             "STAGE 2  Control tube: servos out through the pad windows, ears screwed; hubs on; IMU deck; avionics spine (wired on the bench)",
             "STAGE 3  Join control tube <- motor bay shoulder (3 x M3); servo leads already up through the IMU deck slots",
             "STAGE 4  Join recovery bay (with RB-floor coupler) -> control tube (3 x M3)",
             "STAGE 5  Drop the bypass tube down the axis: RB floor -> spine -> IMU deck -> plenum socket; RTV the top land",
             "STAGE 6  Fit control fins on the hubs (M2 cross-pins) — swappable per test configuration",
             "STAGE 7  Pack Nomex + chute + cord, fit nose (2 x #2-56 nylon shear pins), install motor + retainer at the pad"]
    for i, s in enumerate(steps):
        ax.text(0, -R - 70 - i * 14, s, fontsize=7.8, family="DejaVu Sans Mono", color=INK)
    ax.set_xlim(-20, x); ax.set_ylim(-R - 180, R + 95)
    ax.set_title("Assembly stages — single-stage vehicle, four separate printed sections; only the nose separates in flight", fontsize=10, loc="left")
    save(fig, "D3_assembly_stages")

if __name__ == "__main__":
    vehicle_layout(); cross_sections(); assembly_stages()
