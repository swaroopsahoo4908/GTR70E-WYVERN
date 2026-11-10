#!/usr/bin/env python3
"""Report-style figures for the research proposal (Documentation/Proposal/figures/).

Same data as the working diagrams in Documentation/diagrams and Simulations/plots_*, redrawn in
one consistent house style: serif type to match the document, black linework, greyscale fills
with a single accent colour, panel letters instead of in-figure titles, and no notes inside the
figure that belong in the caption. Run after the cascade."""
import os, sys, json, math, glob
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, Wedge, FancyBboxPatch, FancyArrowPatch
from matplotlib.collections import PolyCollection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SIM = os.path.join(ROOT, "Simulations"); sys.path.insert(0, SIM)
import wf_core as C
OUT = os.path.join(HERE, "figures"); os.makedirs(OUT, exist_ok=True)
P3D = os.path.join(ROOT, "3D parts")

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 10, "axes.linewidth": 0.7, "axes.edgecolor": "black",
    "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.visible": True, "ytick.minor.visible": True,
    "xtick.minor.width": 0.4, "ytick.minor.width": 0.4, "lines.linewidth": 1.1, "lines.markersize": 4.5,
    "legend.frameon": True, "legend.edgecolor": "black", "legend.fancybox": False, "legend.framealpha": 1.0,
    "legend.fontsize": 8.5, "axes.labelsize": 10, "savefig.dpi": 300,
})
K = "black"; G1 = "#4d4d4d"; G2 = "#8c8c8c"; G3 = "#bfbfbf"; G4 = "#e6e6e6"; ACC = "#9c3d1a"   # one accent (fins)

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", facecolor="white", pad_inches=0.04)
    plt.close(fig); print("wrote", name)

def panel(ax, letter, x=-0.02, y=1.02):
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=10.5, ha="right", va="bottom")

PROF = [("flat_plate", "Flat plate", dict(c=K, ls="-", marker="o", mfc="white")),
        ("double_wedge", "6 % double wedge", dict(c=K, ls="--", marker="s", mfc=K)),
        ("NACA0006", "NACA 0006", dict(c=G2, ls="-", marker="^", mfc=G2)),
        ("NACA0012", "NACA 0012", dict(c=G2, ls="-.", marker="D", mfc="white"))]

# =============================================================================== plots
def fig6_authority():
    d = json.load(open(os.path.join(SIM, "plots_authority", "authority_matrix.json")))
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.3))
    for key, lab, st in PROF:
        rr = sorted([r for r in d["rows"] if r["profile"] == key], key=lambda r: r["H_mm"])
        H = [r["H_mm"] for r in rr]
        ax[0].plot(H, [r["CNa_fin_isolated"] * r["K_WB"] for r in rr], label=lab, **st)
        ax[1].plot(H, [1000 * r["tunnelA_fin_N_at10deg"] for r in rr], label=lab, **st)
        ax[2].plot(H, [r["CN10_nonlin_over_lin"] for r in rr], label=lab, **st)
    for a in ax:
        a.axvspan(20, 40, color=G4, zorder=0, lw=0)
        a.set_xlabel(r"Fin height $H$ (mm)"); a.set_xlim(13, 52)
    ax[0].set_ylabel(r"$C_{N\alpha}$ on body (rad$^{-1}$)")
    ax[1].set_ylabel(r"$N$ at $\delta = 10^\circ$, 11 m/s (mN)")
    ax[2].set_ylabel(r"$C_N / C_{N,\mathrm{linear}}$ at $\delta = 10^\circ$")
    ax[2].axhline(1.0, c=K, lw=0.5)
    ax[0].legend(loc="lower right")
    for a, l in zip(ax, "abc"): panel(a, l)
    fig.tight_layout(w_pad=1.6)
    save(fig, "Fig6_authority_predictions.png")

def fig7_stabilizer():
    d = json.load(open(os.path.join(SIM, "plots_stabilizer", "stabilizer_sweep.json")))
    sty = {0.0: dict(c=K, ls=":", marker="o", mfc="white", label=r"$0^\circ$ (in line)"),
           22.5: dict(c=G2, ls="--", marker="s", mfc=G2, label=r"$22.5^\circ$"),
           45.0: dict(c=K, ls="-", marker="^", mfc=K, label=r"$45^\circ$ (flown)")}
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.3))
    for off, st in sty.items():
        rr = sorted([r for r in d["rows"] if r["offset_deg"] == off], key=lambda r: r["span_mm"])
        s = [r["span_mm"] for r in rr]
        ax[0].plot(s, [r["SM_liftoff_cal"] for r in rr], **st)
        ax[1].plot(s, [r["interference_ratio"] for r in rr], **st)
        ax[2].plot(s, [r["trim_alpha_per_delta"] for r in rr], **st)
    fl = [r for r in d["rows"] if r["offset_deg"] == 45.0 and r["span_mm"] == C.RECT_FIN["span"]][0]
    for a, k in zip(ax, ("SM_liftoff_cal", "interference_ratio", "trim_alpha_per_delta")):
        a.plot([fl["span_mm"]], [fl[k]], marker="o", ms=11, mfc="none", mec=ACC, mew=1.2, ls="none", zorder=5)
        a.set_xlabel("Stabilizer span (mm)"); a.set_xlim(-3, 63)
    ax[0].axhline(0.9, c=G1, lw=0.6, ls="--"); ax[0].text(61, 0.93, "0.9 cal minimum", ha="right", va="bottom", fontsize=8, color=G1)
    ax[0].set_ylabel("Static margin at liftoff (cal)")
    ax[1].set_ylabel(r"Interference ratio $I$")
    ax[2].set_ylabel(r"Trim $\alpha$ per unit $\delta$"); ax[2].set_ylim(0, 1.6)
    ax[0].legend(loc="upper left", title="Azimuth offset", title_fontsize=8.5)
    for a, l in zip(ax, "abc"): panel(a, l)
    fig.tight_layout(w_pad=1.6)
    save(fig, "Fig7_stabilizer_interference.png")

def fig8_maneuver():
    import wf_flightsim as F
    out, Hs = F.run_maneuver()
    t0 = out["t_man0_s"]
    fig, ax = plt.subplots(3, 1, figsize=(7.2, 7.0), sharex=True)
    for k, c, ls in (("A", K, "-"), ("B", G2, "--")):
        H = Hs[k]
        ax[0].plot(H["t"], H["th"], c=c, ls=ls, label=f"Axis {k}")
        ax[0].plot(H["t"], H["ref"], c=c, ls=":", lw=0.8)
        ax[1].plot(H["t"], H["dl"], c=c, ls=ls, label=f"Axis {k}")
        ax[1].plot(H["t"], H["inj"], c=c, ls=":", lw=0.8)
        ax[2].plot(H["t"], H["q"], c=c, ls=ls, label=f"Axis {k}")
    a2 = ax[2].twinx(); a2.plot(Hs["ref"]["t"], np.array(Hs["ref"]["qbar"]) / 1000, c=ACC, lw=0.9, ls="-.")
    a2.set_ylabel(r"$\bar{q}$ (kPa)", color=ACC); a2.tick_params(axis="y", colors=ACC, direction="in")
    a2.spines["right"].set_color(ACC); a2.set_ylim(0, 2.0); ax[2].tick_params(right=False, which="both")
    for a, yl, l in zip(ax, ("Tilt (deg)", "Fin-pair deflection (deg)", "Pitch rate (deg/s)"), "abc"):
        a.set_ylabel(yl); a.axvline(t0, c=G1, lw=0.5, ls="--"); panel(a, l, x=-0.08, y=0.98)
    ax[0].plot([], [], c=G1, ls=":", lw=0.8, label="Command")
    ax[0].legend(loc="lower right", ncol=3)
    ax[2].set_xlabel("Time from launch (s)"); ax[0].set_xlim(t0 - 0.3, t0 + 2.9)
    ax[0].set_ylim(-1.7, 0.6); ax[2].set_ylim(-11, 8)
    ax[0].text(t0 + 0.02, -1.62, "programme start", va="bottom", fontsize=8, color=G1)
    fig.tight_layout(h_pad=0.6)
    save(fig, "Fig8_authority_manoeuvre.png")

# =============================================================================== mesh renders
def load(path):
    from stl import mesh
    return mesh.Mesh.from_file(path).vectors.copy()

def rot_z(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return v @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T

def view(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Rz

def render(ax, plist, elev, azim, edge=True):
    """Flat-shaded orthographic render with a thin dark silhouette edge, like a CAD shaded view."""
    M = view(elev, azim); L = np.array([0.3, -0.45, 0.85]); L /= np.linalg.norm(L)
    P, Cc, D, E = [], [], [], []
    for v, col in plist:
        p = v @ M.T
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        k = 0.55 + 0.45 * np.abs(n @ L)
        base = np.array(matplotlib.colors.to_rgb(col))
        P.append(p[:, :, [0, 2]]); Cc.append(np.clip(base[None] * k[:, None], 0, 1)); D.append(p[:, :, 1].mean(1))
    P = np.concatenate(P); Cc = np.concatenate(Cc); D = np.concatenate(D); o = np.argsort(-D)
    ax.add_collection(PolyCollection(P[o], facecolors=Cc[o], edgecolors=Cc[o], linewidths=0.2))
    pts = P.reshape(-1, 2); mn, mx = pts.min(0), pts.max(0); pad = 0.04 * (mx - mn).max()
    ax.set_xlim(mn[0] - pad, mx[0] + pad); ax.set_ylim(mn[1] - pad, mx[1] + pad); ax.set_aspect("equal"); ax.axis("off")

def caption_below(ax, text):
    ax.text(0.5, -0.02, text, transform=ax.transAxes, ha="center", va="top", fontsize=9.5)

# realistic-ish material colours
ASA = "#d8d8d4"; ASA2 = "#c9cac6"; CF = "#3b3d40"; PCFR = "#b9b2a0"; SERVO = "#41597d"; ALU = "#9ea3a8"; SPINE = "#55585c"

def fig1_vehicle_renders():
    f = lambda pat, sub="flight": glob.glob(os.path.join(P3D, sub, pat + "*.stl"))[0]
    hub = load(f("06_servo_hub")); rf = load(f("12_rect_fin"))
    cf = load(glob.glob(os.path.join(P3D, "control_fins", "NACA0006", f"cfin_NACA0006_H{int(C.CFIN_H_NOMINAL)}_*.stl"))[0])
    pl = [("nose", load(f("01_nose")), ASA, 3), ("rb", load(f("02_recovery")), ASA2, 2), ("rbc", load(f("03_rb_floor")), PCFR, 2),
          ("ct", load(f("04_control")), ASA, 1), ("imu", load(f("05_spine_deck")), SPINE, 1), ("spine", load(f("05b_avionics_spine")), SPINE, 1),
          ("mb", load(f("07_motor_bay")), ASA2, 0), ("plenum", load(f("08_plenum")), PCFR, 0), ("mmt", load(f("09_motor_mount")), PCFR, 0),
          ("ret", load(f("10_motor_retainer")), PCFR, -1)]
    for a in (0, 90, 180, 270): pl.append(("hub", rot_z(hub, a), CF, 1))
    for i in range(4): pl.append(("rfin", rot_z(rf, 90 * i), CF, 0))
    for a in (0, 90, 180, 270): pl.append(("cfin", rot_z(cf, a), ACC, 1))
    hz = [(n, v[..., [2, 0, 1]].copy(), c, g) for n, v, c, g in pl]
    sv = C.SERVO; zc = C.L_TOTAL - C.X_CT_BOT + C.SERVO_RING_Z
    def box(x0, x1, y0, y1, z0, z1):
        cc = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
        fz = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
        return cc[np.array(fz)]
    def cyl(r, z0, z1, n=36):
        a = np.linspace(0, 2 * np.pi, n + 1); t = []
        for i in range(n):
            p0 = [r * np.cos(a[i]), r * np.sin(a[i])]; p1 = [r * np.cos(a[i + 1]), r * np.sin(a[i + 1])]
            t += [[p0 + [z0], p1 + [z0], p1 + [z1]], [p0 + [z0], p1 + [z1], p0 + [z1]]]
        return np.array(t)
    internals = [("bypass", cyl(C.BYPASS["od"] / 2, C.L_TOTAL - C.X_BYPASS_TOP - C.BYPASS["L"], C.L_TOTAL - C.X_BYPASS_TOP), PCFR, 1)]
    for a in (0, 90, 180, 270):
        internals.append(("servo", rot_z(box(C.SERVO_BASE_R, C.SERVO_TOP_R, -sv["W"] / 2, sv["W"] / 2, zc - sv["L"] / 2, zc + sv["L"] / 2), a), SERVO, 1))

    fig = plt.figure(figsize=(10, 7.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 0.9, 1.7], hspace=0.12)
    a = fig.add_subplot(gs[0, :]); render(a, [(v, c) for _, v, c, _ in hz], 18, 10); caption_below(a, "(a) Assembled vehicle")
    ex = []
    for n, v, c, g in hz:
        w = v.copy(); w[..., 0] += (220 if n == "rbc" else {3: 330, 2: 220, 1: 110}.get(g, 0)); ex.append((w, c))
    a = fig.add_subplot(gs[1, :]); render(a, ex, 18, 10); caption_below(a, "(b) Exploded: retainer, motor bay, control tube, recovery bay, nose")
    keep = ("ct", "imu", "spine", "hub", "cfin", "servo", "bypass"); cut = []
    for n, v, c, g in pl + internals:
        if n not in keep: continue
        if n == "ct": v = v[v[..., 1].min(axis=1) >= -0.5]
        cut.append((v, c))
    a = fig.add_subplot(gs[2, 0]); render(a, cut, 20, 35); caption_below(a, "(c) Control tube, front half removed")
    mb = []
    for n, v, c, g in pl:
        if n not in ("mb", "plenum", "mmt", "ret", "rfin"): continue
        if n in ("mb", "plenum"): v = v[v[..., 1].min(axis=1) >= -0.5]
        mb.append((v, c))
    a = fig.add_subplot(gs[2, 1]); render(a, mb, 20, 35); caption_below(a, "(d) Motor bay, front half removed")
    save(fig, "Fig1_cad_renders.png")

def fig5_tunnel_parts():
    wt = lambda pat: load(glob.glob(os.path.join(P3D, "wind_tunnel", pat + "*.stl"))[0])
    fig = plt.figure(figsize=(10, 6.6))
    gs = fig.add_gridspec(2, 3, hspace=0.18, wspace=0.08)
    a = fig.add_subplot(gs[0, 0]); render(a, [(wt("WTA_reflection_plane_wall_panel"), ASA)], 30, -50); caption_below(a, "(a) Reflection-plane wall panel")
    a = fig.add_subplot(gs[0, 1]); render(a, [(wt("WTA_servo_balance_cradle"), CF)], 25, -55); caption_below(a, "(b) Servo balance cradle")
    mr = wt("WTA_inclined_manometer_ramp"); ml = wt("WTA_inclined_manometer_lid")
    off = np.array([mr[..., 0].min() - ml[..., 0].min() - 10, 0, mr[..., 2].max() - ml[..., 2].min() + 15])
    a = fig.add_subplot(gs[0, 2]); render(a, [(mr, ASA2), (ml + off, G2)], 40, -125); caption_below(a, "(c) Inclined manometer and reservoir lid")
    a = fig.add_subplot(gs[1, 0]); render(a, [(wt("WTA_diffuser_100sq_to_6in_round"), ASA)], 20, -40); caption_below(a, "(d) Transition, 100 mm square to 6 in")
    fins = []; CFD = os.path.join(P3D, "control_fins")
    shade = {"flat_plate": CF, "double_wedge": ACC, "NACA0006": "#5f6b7a", "NACA0012": "#8a8f96"}
    for i, prof in enumerate(["flat_plate", "double_wedge", "NACA0006", "NACA0012"]):
        for j, H in enumerate([20, 30, 40]):
            v = load(glob.glob(os.path.join(CFD, prof, f"cfin_{prof}_H{H}_*.stl"))[0])[..., [2, 1, 0]]
            v -= v.reshape(-1, 3).min(0); fins.append((v + np.array([j * 80, 0, -i * 55]), shade[prof]))
    a = fig.add_subplot(gs[1, 1:]); render(a, fins, 18, -15)
    caption_below(a, "(e) Test fins: rows flat plate, double wedge, NACA 0006, NACA 0012; columns H = 20, 30, 40 mm")
    save(fig, "Fig5_wind_tunnel_parts.png")

# =============================================================================== line drawings
def dim(ax, x0, x1, y, text, fs=8.5, off=-3):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color=K, mutation_scale=7, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="top" if off < 0 else "bottom", fontsize=fs)
    for x in (x0, x1): ax.plot([x, x], [y - 3, y + 3], lw=0.4, color=K)

def balloon(ax, n, xy, xytext, fs=7.5):
    ax.annotate("", xy=xy, xytext=xytext, arrowprops=dict(arrowstyle="-|>", lw=0.5, color=K, mutation_scale=6, shrinkA=8, shrinkB=0))
    ax.add_patch(Circle(xytext, 7.6, fc="white", ec=K, lw=0.6, zorder=20))
    ax.text(*xytext, str(n), ha="center", va="center", fontsize=fs, zorder=21)

def hatch_rect(ax, x, y, w, h, fc="white", hatch=None, lw=0.6, z=2, **kw):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=K, lw=lw, hatch=hatch, zorder=z, **kw))

def fig2_layout():
    plt.rcParams["hatch.linewidth"] = 0.35
    M0, cg0, _, _ = C.mass_properties(C.FLIGHT_MOTOR, 0.0); st = C.stability(cg0); R = C.R
    fig, ax = plt.subplots(figsize=(10.5, 4.6)); ax.set_aspect("equal"); ax.axis("off")
    rho = (R * R + C.NOSE["L"] ** 2) / (2 * R); xs = np.linspace(0, C.NOSE["L"], 80)
    ys = np.sqrt(np.maximum(rho ** 2 - (C.NOSE["L"] - xs) ** 2, 0)) + R - rho
    ax.fill(np.r_[xs, xs[::-1]], np.r_[ys, -ys[::-1]], fc="white", ec=K, lw=0.8, zorder=1)
    for x0, x1 in ((C.X_RB_TOP, C.X_RB_BOT), (C.X_CT_TOP, C.X_CT_BOT), (C.X_MB_TOP, C.X_MB_BOT)):
        hatch_rect(ax, x0, -R, x1 - x0, 2 * R, lw=0.8, z=1)
    for xj in (C.X_RB_BOT, C.X_CT_BOT):
        ax.add_patch(Rectangle((xj - 20, -C.RI + 0.3), 40, 2 * C.RI - 0.6, fill=False, ec=G2, lw=0.5, ls=(0, (3, 2)), zorder=2))
    ax.add_patch(Rectangle((C.NOSE["L"], -C.RI + 0.3), C.NOSE["shoulder"], 2 * C.RI - 0.6, fill=False, ec=G2, lw=0.5, ls=(0, (3, 2))))
    ax.add_patch(Polygon([[12, -4], [12, 4], [45, 10], [45, -10]], fc=G3, ec=K, lw=0.5, hatch="xxxx", zorder=3))          # ballast
    hatch_rect(ax, C.X_RB_BOT - 1.5, -C.RI, 3, 2 * C.RI, fc=G2, lw=0.4, z=3)                                                  # RB floor
    ax.add_patch(FancyBboxPatch((C.X_RB_TOP + 55, -24), 95, 48, boxstyle="round,pad=2", fc=G4, ec=K, lw=0.5, zorder=3))      # chute
    tt = np.linspace(C.X_RB_TOP + 165, C.X_RB_BOT - 12, 80); ax.plot(tt, 6 * np.sin((tt - tt[0]) / 7), color=G1, lw=0.7, zorder=3)
    hatch_rect(ax, C.X_BYPASS_TOP, -C.BYPASS["od"] / 2, C.BYPASS["L"], C.BYPASS["od"], fc=G4, lw=0.5, z=4)                    # bypass
    zb = C.X_CT_BOT; xs0 = zb - C.SPINE_Z0 - C.SPINE_L
    hatch_rect(ax, xs0, -C.SPINE_FLAT, C.SPINE_L, 2 * C.SPINE_FLAT, fc="white", hatch="////", lw=0.5, z=3)
    for bd in C.SPINE_BOARDS:
        if bd["face"] not in ("px", "nx"): continue
        sgn = 1 if bd["face"] == "px" else -1; Pp = C.board_plane(bd); th = 14.0 if bd["key"] == "battery" else 1.6
        x0b = zb - C.SPINE_Z0 - bd["z0"] - bd["L"]
        hatch_rect(ax, x0b, Pp if sgn > 0 else -Pp - th, bd["L"], th, fc=G3 if bd["key"] == "battery" else G1, lw=0.4, z=5)
    sv = C.SERVO; zc = C.X_HINGE - (sv["L"] / 2 - sv["shaft_from_end"])
    for sgn in (1, -1):
        y0 = C.SERVO_BASE_R if sgn > 0 else -(C.SERVO_BASE_R + sv["H"])
        hatch_rect(ax, zc - sv["L"] / 2, y0, sv["L"], sv["H"], fc=G2, lw=0.5, z=6)
    H = C.CFIN_H_NOMINAL; c = C.CFIN["root"]; hf = C.CFIN["hinge_frac"]; xh = C.X_HINGE
    xle, xte = xh - hf * c, xh + (1 - hf) * c; r0 = R + C.CFIN["gap"]
    for sgn in (1, -1):
        ax.add_patch(Polygon([[xle, sgn * r0], [xte, sgn * r0], [xte, sgn * (r0 + H)]], fc=ACC, ec=K, lw=0.6, zorder=7))
        ax.plot([xh, xh], [sgn * (R - 4), sgn * (r0 + 6)], color=K, lw=0.6, ls=(0, (6, 2, 1, 2)), zorder=8)
    rf = C.RECT_FIN; sp = rf["span"] * math.cos(math.radians(45))
    for s in (1, -1):
        ax.add_patch(Polygon([[C.X_RECT_LE, s * R], [C.X_RECT_LE + rf["root"], s * R], [C.X_RECT_LE + rf["root"], s * (R + sp)], [C.X_RECT_LE, s * (R + sp)]],
                             fc=G1, ec=K, lw=0.6, zorder=7))
    hatch_rect(ax, C.X_PLENUM_TOP, -C.RI, C.PLENUM_T, 2 * C.RI, fc=G2, lw=0.5, z=5)
    hatch_rect(ax, C.X_MOTOR_TOP, -C.MMT_ID / 2 - C.MMT_WALL, C.X_MOTOR_AFT - C.X_MOTOR_TOP, C.MMT_ID + 2 * C.MMT_WALL, fc="white", lw=0.5, z=4)
    hatch_rect(ax, C.X_MOTOR_TOP, -C.MOTOR_D / 2, C.MOTORS[C.FLIGHT_MOTOR]["L"], C.MOTOR_D, fc=G4, hatch="....", lw=0.5, z=5)
    hatch_rect(ax, C.X_MB_BOT, -R - 2.2, 3, 2 * R + 4.4, fc=G2, lw=0.4, z=5)
    # centreline
    ax.plot([-15, C.L_TOTAL + 15], [0, 0], color=K, lw=0.4, ls=(0, (12, 3, 2, 3)), zorder=0)
    # CG (standard quartered circle) and CP (circle with cross)
    ax.add_patch(Circle((cg0, 0), 5.5, fc="white", ec=K, lw=0.8, zorder=10))
    ax.add_patch(Wedge((cg0, 0), 5.5, 0, 90, fc=K, zorder=11)); ax.add_patch(Wedge((cg0, 0), 5.5, 180, 270, fc=K, zorder=11))
    ax.add_patch(Circle((st["xcp"], 0), 5.5, fc="white", ec=K, lw=0.8, zorder=10))
    ax.plot([st["xcp"] - 5.5, st["xcp"] + 5.5], [0, 0], c=K, lw=0.8, zorder=11); ax.plot([st["xcp"]] * 2, [-5.5, 5.5], c=K, lw=0.8, zorder=11)
    ax.text(cg0, -R - 12, f"CG {cg0:.0f}", ha="center", va="top", fontsize=8.5)
    ax.text(st["xcp"], -R - 12, f"CP {st['xcp']:.0f}", ha="center", va="top", fontsize=8.5)
    # balloons
    up, dn = R + 52, -R - 46
    items = [((25, 0), (25, up), f"Ballast, {C.BALLAST_G:.0f} g"), ((C.NOSE["L"], R), (C.NOSE["L"] + 20, up), "Nose shoulder (separation joint)"),
             ((C.X_RB_TOP + 100, 20), (C.X_RB_TOP + 100, up), "Parachute, 24 in"),
             ((C.X_RB_TOP + 172, 5), (C.X_RB_TOP + 172, up), "Aramid shock cord"),
             ((C.X_RB_BOT, C.RI - 4), (C.X_RB_BOT - 10, up), "Recovery-bay floor, PC-FR"),
             ((C.X_BYPASS_TOP + 40, 3), (C.X_BYPASS_TOP + 40, dn), "Ejection bypass tube, PC-FR"),
             ((xs0 + 30, C.SPINE_FLAT + 8), (xs0 + 25, up), "Flight computer and IMU on avionics spine"),
             ((xs0 + 45, -C.SPINE_FLAT - 8), (xs0 + 55, dn), "2S 450 mAh LiPo"),
             ((zc, -C.SERVO_BASE_R - 5), (zc - 15, dn), "EMAX ES9251 II servos (4)"),
             ((xh - 5, R + 12), (xh - 45, up), "Control fins (4), H = 45 mm"),
             ((C.X_PLENUM_TOP + 3, -C.RI + 6), (C.X_PLENUM_TOP - 5, dn), "Plenum bulkhead and gas gallery"),
             ((C.X_RECT_LE + 40, R + sp), (C.X_RECT_LE + 40, up), "Stabilizers (4), 81 × 20 mm at 45°"),
             ((C.X_MOTOR_TOP + 40, -4), (C.X_MOTOR_TOP + 40, dn), f"AeroTech {C.FLIGHT_MOTOR}, 29 × 83 mm")]
    for i, (xy, xt, _) in enumerate(items, 1): balloon(ax, i, xy, xt)
    # dimensions
    yd = -R - 72
    for x0, x1 in ((0, C.NOSE["L"]), (C.X_RB_TOP, C.X_RB_BOT), (C.X_CT_TOP, C.X_CT_BOT), (C.X_MB_TOP, C.X_MB_BOT)):
        dim(ax, x0, x1, yd, f"{x1 - x0:.0f}")
    dim(ax, 0, C.L_TOTAL, yd - 22, f"{C.L_TOTAL:.0f}")
    ax.annotate("", xy=(C.L_TOTAL + 22, R), xytext=(C.L_TOTAL + 22, -R), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color=K, mutation_scale=7, shrinkA=0, shrinkB=0))
    ax.text(C.L_TOTAL + 27, 0, f"Ø{C.OD:.0f}", va="center", fontsize=8.5, rotation=90)
    for y in (R, -R): ax.plot([C.L_TOTAL + 3, C.L_TOTAL + 26], [y, y], lw=0.4, c=K)
    # parts key
    col_w = 3; rows = math.ceil(len(items) / col_w)
    for i, (_, _, txt) in enumerate(items):
        cx = -10 + (i // rows) * 245; cy = -R - 128 - (i % rows) * 13
        ax.add_patch(Circle((cx, cy), 5.8, fc="white", ec=K, lw=0.5)); ax.text(cx, cy, str(i + 1), ha="center", va="center", fontsize=6.8)
        ax.text(cx + 9, cy, txt, va="center", fontsize=8.5)
    ax.text(C.L_TOTAL + 30, -R - 128 - (rows - 1) * 13, "Dimensions in mm, stations from nose tip", ha="right", va="center", fontsize=8, style="italic")
    ax.set_xlim(-25, C.L_TOTAL + 40); ax.set_ylim(-R - 128 - rows * 13, up + 10)
    save(fig, "Fig2_vehicle_layout.png")

def duct(ax, x, L, h_in, h_out, y0=0, fc="white", hatch=None, lw=0.7):
    ax.add_patch(Polygon([[x, y0 - h_in / 2], [x + L, y0 - h_out / 2], [x + L, y0 + h_out / 2], [x, y0 + h_in / 2]], fc=fc, ec=K, lw=lw, hatch=hatch))

def fig4_tunnel():
    plt.rcParams["hatch.linewidth"] = 0.35
    fig, ax = plt.subplots(figsize=(10.5, 7.6)); ax.set_aspect("equal"); ax.axis("off")
    up = [(75, 202, 202, "white", "||||"), (75, 202, 202, "white", "...."), (75, 202, 202, "white", "....")]
    def label(x, y, t, **kw): ax.text(x, y, t, ha="center", fontsize=8.2, **kw)
    def flow(x, y): ax.annotate("", xy=(x + 55, y), xytext=(x, y), arrowprops=dict(arrowstyle="-|>", lw=0.8, color=K, mutation_scale=9)); ax.text(x + 27, y + 8, "Flow", ha="center", fontsize=8, style="italic")
    def row(y, segs, tag):
        x = 0
        for L, a_, b_, fc, hatch in segs:
            duct(ax, x, L, a_, b_, y, fc=fc, hatch=hatch); x += L
        ax.text(-140, y, tag, fontsize=10, va="center")
        flow(-110, y - 60)
        return x
    # (a) stock
    y = 760
    xe = row(y, up + [(250, 202, 100, "white", None), (175, 100, 100, G4, None), (175, 100, 140, "white", None), (180, 140, 140, "white", None), (25, 140, 140, G2, None)], "(a)")
    label(37, y - 122, "Honeycomb", va="top"); label(150, y + 108, "Screens, 40 and 80 mesh")
    label(350, y + 92, "4:1 contraction"); label(562, y + 6, "Test section"); label(562, y - 14, "100 × 100 × 175")
    label(737, y + 80, "Diffuser"); label(895, y + 80, "Extension"); label(1050, y + 80, "140 mm fan", ha="left") if False else ax.text(1045, y, "140 mm fan", va="center", fontsize=8.2)
    # (b) phase A
    y = 400
    xe = row(y, up + [(250, 202, 100, "white", None), (175, 100, 100, G4, None), (190, 100, 152, "white", None), (240, 152, 152, G3, "xx")], "(b)")
    label(37, y - 122, "Honeycomb", va="top"); label(150, y + 108, "Screens, 40 and 80 mesh")
    label(350, y + 92, "4:1 contraction"); label(562, y + 60, "Test section")
    label(795, y + 92, "Printed transition"); label(1010, y + 92, "6 in EC inline fan")
    xs = 475; ax.add_patch(Rectangle((xs, y - 50), 175, 4, fc=G1, ec=K, lw=0.5)); xh = xs + 87
    ax.add_patch(Polygon([[xh - 27, y - 46], [xh + 33, y - 46], [xh + 33, y - 6]], fc=ACC, ec=K, lw=0.5))
    ax.add_patch(Rectangle((xh - 12, y - 85), 24, 30, fc=G2, ec=K, lw=0.5))
    for dx in (-30, 30): ax.add_patch(Rectangle((xh + dx - 9, y - 100), 18, 10, fc="white", ec=K, lw=0.5, hatch="////"))
    ax.plot([xh - 45, xh + 45], [y - 102, y - 102], c=K, lw=1.0)
    label(xh, y - 138, "Servo cradle on two 1 kg load cells"); label(xh - 140, y - 10, "Wall panel", ha="right") if False else ax.annotate("Wall panel", xy=(xs + 20, y - 48), xytext=(xs - 50, y - 95), fontsize=8.2, ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=K))
    ax.text(xh + 40, y - 22, "Fin", fontsize=8.2)
    ax.plot([505, 545], [y + 22, y + 22], c=K, lw=1.4); ax.plot([505, 505], [y + 22, y + 15], c=K, lw=1.0)
    ax.text(525, y + 30, "Pitot", fontsize=8.2, ha="center")
    # (c) phase B
    y = 0
    segs = up + [(12, 228, 228, G3, None), (750, 200, 200, G4, None), (12, 228, 228, G3, None), (150, 200, 203, "white", None), (290, 203, 203, G3, "xx")]
    xe = row(y, segs, "(c)")
    label(37, y - 122, "Honeycomb", va="top"); label(150, y + 118, "Screens, 40 and 80 mesh")
    label(612, y + 110, "Acrylic test section 200 × 200 × 750"); label(1310, y + 112, "8 in inline fan")
    x0 = 75 * 3 + 12 + 128; Lct = C.L_CT; Lst = (C.X_RECT_LE + C.RECT_FIN["root"]) - C.X_CT_BOT + 4
    ax.add_patch(Polygon([[x0, 0], [x0 + 100, 29], [x0 + 100, -29]], fc="white", ec=K, lw=0.6))
    ax.add_patch(Rectangle((x0 + 100, -29), Lct, 58, fc=G3, ec=K, lw=0.6))
    ax.add_patch(Rectangle((x0 + 100 + Lct, -29), Lst, 58, fc="white", ec=K, lw=0.6))
    xt = x0 + 100 + Lct + Lst
    ax.add_patch(Polygon([[xt, 29], [xt + 80, 12], [xt + 80, -12], [xt, -29]], fc="white", ec=K, lw=0.6))
    xc = x0 + 100 + (C.X_HINGE - C.X_CT_TOP)
    for sg in (1, -1): ax.add_patch(Polygon([[xc - 27, sg * 30], [xc + 33, sg * 30], [xc + 33, sg * 75]], fc=ACC, ec=K, lw=0.5))
    xr = x0 + 100 + (C.X_RECT_LE - C.X_CT_TOP); spn = C.RECT_FIN["span"] * 0.707
    for sg in (1, -1): ax.add_patch(Rectangle((xr, 29 if sg > 0 else -29 - spn), C.RECT_FIN["root"], spn, fc=G1, ec=K, lw=0.5))
    ax.add_patch(Rectangle((xt + 30, -100), 10, 71, fc=G2, ec=K, lw=0.5))
    ax.add_patch(Rectangle((xt + 5, -128), 60, 20, fc="white", ec=K, lw=0.5, hatch="////"))
    label(xt + 35, -150, "Three-cell strut balance")
    ax.annotate("Control tube", xy=(x0 + 150, 29), xytext=(x0 + 150, 80), fontsize=8.2, ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=K))
    ax.annotate("Stabilizer tail", xy=(xr + 40, 29 + spn), xytext=(xr + 110, 80), fontsize=8.2, ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=K))
    ax.set_xlim(-150, 1520); ax.set_ylim(-175, 900)
    save(fig, "Fig4_wind_tunnel_adaptation.png")

def fig3_plan():
    fig, ax = plt.subplots(figsize=(10.5, 6.4)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 64)
    def box(x, y, w, h, head, lines, fc="white", lw=0.8):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=K, lw=lw))
        ax.text(x + w / 2, y + h - 1.6, head, ha="center", va="top", fontsize=10, weight="bold")
        ax.text(x + w / 2, y + h - 4.8, "\n".join(lines), ha="center", va="top", fontsize=8.6, linespacing=1.4)
    def arr(pts, txt=None, at=None, ha="center"):
        xs_, ys_ = zip(*pts)
        if len(pts) > 2: ax.plot(xs_[:-1], ys_[:-1], c=K, lw=0.7)
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", lw=0.7, color=K, mutation_scale=9, shrinkA=0, shrinkB=0))
        if txt: ax.text(*at, txt, ha=ha, fontsize=8.4, style="italic")
    box(2, 56, 96, 7, "Main research question",
        ["How do aerofoil section and fin height set the control authority of a servo-actuated triangular fin?"], fc=G4, lw=1.0)
    box(2, 30, 28, 20, "Simulation", ["2D panel method", "Vortex lattice and slender body", "Boundary-layer effectiveness", "Vortex interference", "3-DOF closed-loop flight model"])
    box(36, 34, 28, 16, "Wind tunnel, Phase A", ["One fin on a reflection plane", "4 sections × 5 heights", "−15° to +15°, two repeats"])
    box(70, 34, 28, 16, "Selection", ["P*: most measured authority", "H*: most simulated authority", "Flights at H* − 5, H*, H* + 5"])
    box(36, 13, 28, 16, "Wind tunnel, Phase B", ["Full control tube", "Stabilizers off, 20, 30, 40 mm", "Sub-RQ1"])
    box(70, 13, 28, 16, "Flight tests (3)", ["Doublets and 1° steps", "Measured $M_\\delta/I$ per axis", "Sub-RQ2"])
    box(2, 1, 96, 7, "Analysis", ["Blockage corrections · slopes with 95 % CI · two-way ANOVA · Spearman rank, simulation vs tunnel vs flight"])
    arr([(30, 42), (36, 42)], "predicts", (33, 42.8))
    arr([(16, 30), (16, 21), (36, 21)], "predicts", (26, 21.8))
    arr([(64, 42), (70, 42)], "P*", (67, 42.8))
    arr([(50, 34), (50, 29)], "P*", (51, 31), ha="left")
    arr([(84, 34), (84, 29)])
    arr([(22, 50), (22, 53), (92, 53), (92, 50)], "H*", (57, 53.6))
    arr([(9, 30), (9, 8)]); arr([(50, 13), (50, 8)]); arr([(84, 13), (84, 8)])
    save(fig, "Fig3_research_plan.png")

if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2", "3", "4", "5", "6", "7", "8"]
    F = {"1": fig1_vehicle_renders, "2": fig2_layout, "3": fig3_plan, "4": fig4_tunnel, "5": fig5_tunnel_parts,
         "6": fig6_authority, "7": fig7_stabilizer, "8": fig8_maneuver}
    for w in which: F[w]()
