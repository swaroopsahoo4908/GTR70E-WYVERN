#!/usr/bin/env python3
"""D4 wind-tunnel adaptation (stock vs modified) and D5 research plan / test matrix."""
import os, sys, json, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Simulations")); import wf_core as C
INK = "#111827"; MUTED = "#6b7280"

def save(fig, name):
    for e in ("png", "svg"): fig.savefig(os.path.join(HERE, f"{name}.{e}"), dpi=165 if e == "png" else None, bbox_inches="tight", facecolor="white")
    plt.close(fig); print("wrote", name)

def tunnel():
    fig = plt.figure(figsize=(17, 13))
    ax = fig.add_axes([0.02, 0.40, 0.96, 0.56]); ax.set_aspect("equal"); ax.axis("off")
    cnt = [0]
    def duct(x, L, h_in, h_out, fc, lab, y0=0, fs=7):
        ax.add_patch(Polygon([[x, y0 - h_in / 2], [x + L, y0 - h_out / 2], [x + L, y0 + h_out / 2], [x, y0 + h_in / 2]], fc=fc, ec=INK, lw=0.8))
        if L < 100 and lab:
            ax.text(x + L / 2, y0 + (cnt[0] % 2) * 18 - 8, lab, ha="center", va="center", fontsize=6.3, rotation=90)
        elif lab:
            ax.text(x + L / 2, y0 + max(h_in, h_out) / 2 + 12, lab, ha="center", fontsize=fs)
        cnt[0] += 1
    up = ((75, 202, 202, "#e0f2fe", "honeycomb\n75"), (75, 202, 202, "#f1f5f9", "screen\n40 mesh"), (75, 202, 202, "#f1f5f9", "screen\n80 mesh"))
    # ---- stock
    y = 720
    ax.text(-10, y + 150, "STOCK (Jerrod H 'STEM tunnel', measured from the STLs)", fontsize=9, weight="bold")
    x = 0
    for L, a_, b_, fc, lab in up + ((250, 202, 100, "#fef3c7", "contraction 4:1\n202 -> 100 sq, 250"), (175, 100, 100, "#dcfce7", "test section\n100 x 100 x 175"),
                                    (175, 100, 140, "#f1f5f9", "diffuser"), (180, 140, 140, "#f1f5f9", "diffuser ext."), (25, 140, 140, "#e5e7eb", "Noctua\nNF-A14")):
        duct(x, L, a_, b_, fc, lab, y); x += L
    ax.text(x + 20, y, "->  ~2-4 m/s\n(140 mm PC fan)", fontsize=8, va="center")
    # ---- phase A
    y = 380
    ax.text(-10, y + 150, "PHASE A — main RQ: one fin on a reflection-plane wall panel in the stock section, Cloudline T8", fontsize=9, weight="bold", color="#9a3412")
    x = 0
    for L, a_, b_, fc, lab in up + ((250, 202, 100, "#fef3c7", "stock contraction"), (175, 100, 100, "#ffedd5", "stock section\n+ WTA wall panel"),
                                    (250, 100, 203, "#fef3c7", "WTA 100 sq -> 8 in"), (290, 203, 203, "#e5e7eb", "Cloudline PRO T8")):
        duct(x, L, a_, b_, fc, lab, y); x += L
    ax.text(x + 20, y, "->  ~12 m/s\n(measure)", fontsize=8, va="center")
    xs = 75 * 3 + 250
    ax.add_patch(Rectangle((xs, y - 50), 175, 4, fc="#64748b", ec=INK, lw=0.5))
    xh = xs + 87
    ax.add_patch(Polygon([[xh - 27, y - 46], [xh + 33, y - 46], [xh + 33, y - 46 + 40]], fc="#c2410c", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((xh - 12, y - 85), 24, 30, fc="#2563eb", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((xh - 45, y - 100), 90, 8, fc="#fde68a", ec=INK, lw=0.5))
    ax.text(xh, y - 118, "X08 Plus on the cradle, 2 x 100 g cells (N + CP)", ha="center", fontsize=6.8)
    ax.text(xh + 120, y - 30, "fin root 1 mm off the panel,\nspline 4 mm behind it (as in flight)", fontsize=6.5)
    # ---- phase B
    y = 0
    ax.text(-10, y + 150, "PHASE B — SQ1 + SQ2: full four-fin control tube + removable stabilizer tail, 200 x 200 x 750 section", fontsize=9, weight="bold", color="#0f766e")
    x = 0
    for L, a_, b_, fc, lab in up + ((12, 228, 228, "#a7f3d0", ""), (750, 200, 200, "#dcfce7", "NEW test section 200 x 200 x 750 (2020 corners + 3 mm acrylic)"),
                                    (12, 228, 228, "#a7f3d0", ""), (150, 200, 203, "#fef3c7", "200 sq->8 in"), (290, 203, 203, "#e5e7eb", "Cloudline PRO T8")):
        duct(x, L, a_, b_, fc, lab, y); x += L
    ax.text(x + 20, y, "->  ~6-8 m/s\n(measure)", fontsize=8, va="center")
    x0 = 75 * 3 + 12 + 128
    Lct = C.L_CT; Lst = (C.X_RECT_LE + C.RECT_FIN["root"]) - C.X_CT_BOT + 4
    ax.add_patch(Polygon([[x0, 0], [x0 + 100, 35], [x0 + 100, -35]], fc="#e5e7eb", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((x0 + 100, -35), Lct, 70, fc="#94a3b8", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((x0 + 100 + Lct, -35), Lst, 70, fc="#cbd5e1", ec=INK, lw=0.6))
    xt = x0 + 100 + Lct + Lst
    ax.add_patch(Polygon([[xt, 35], [xt + 80, 15], [xt + 80, -15], [xt, -35]], fc="#e5e7eb", ec=INK, lw=0.6))
    xc = x0 + 100 + (C.X_HINGE - C.X_CT_TOP)
    for sg in (1, -1):
        ax.add_patch(Polygon([[xc - 27, sg * 36], [xc + 33, sg * 36], [xc + 33, sg * 76]], fc="#c2410c", ec=INK, lw=0.5))
    xr = x0 + 100 + (C.X_RECT_LE - C.X_CT_TOP); sp = C.RECT_FIN["span"] * 0.707
    for sg in (1, -1):
        ax.add_patch(Rectangle((xr, sg * 35 if sg > 0 else -35 - sp), C.RECT_FIN["root"], sp, fc="#334155", ec=INK, lw=0.5, alpha=0.85))
    ax.text(xr + 60, 35 + sp + 8, "stabilizers: off (plugs) / 30 / 50 mm", ha="center", fontsize=6.8, color="#334155")
    ax.add_patch(Rectangle((xt + 30, -100), 12, 85, fc="#64748b", ec=INK, lw=0.5))
    ax.add_patch(Rectangle((xt, -150), 80, 40, fc="#fde68a", ec=INK, lw=0.6)); ax.text(xt + 40, -170, "3-cell strut balance (rotates for yaw sweep)", ha="center", fontsize=6.8)
    ax.plot([x0 - 60, x0 - 20], [60, 60], color="#0284c7", lw=2); ax.text(x0 - 40, 70, "pitot", ha="center", fontsize=6.8, color="#0284c7")
    ax.text(x0 + 100 + Lct / 2, 0, "REAL control tube", ha="center", va="center", fontsize=7, color="white", weight="bold")
    ax.set_xlim(-30, 1700); ax.set_ylim(-190, 900)
    # ---- predictions
    tx = fig.add_axes([0.03, 0.02, 0.94, 0.34]); tx.axis("off")
    d = json.load(open(os.path.join(ROOT, "Simulations", "plots_authority", "authority_matrix.json")))
    rows = [r for r in d["rows"] if r["H_mm"] in C.CFIN_HEIGHTS]
    txt = "PHASE A  expected normal force on ONE fin at 10° deflection, 12 m/s (model, mN)  [scale x (V/12)^2]\n\n"
    txt += "H (mm)        " + "  ".join(f"{h:>6.0f}" for h in C.CFIN_HEIGHTS) + "\n"
    for p in C.CFIN_PROFILES:
        txt += f"{p:13s} " + "  ".join(f"{1000*[r for r in rows if r['profile']==p and r['H_mm']==h][0]['tunnelA_fin_N_at10deg']:6.1f}" for h in C.CFIN_HEIGHTS) + "\n"
    txt += f"\nblockage ~2-3 % · semi-span / width 0.40 at H = 40 · {len(C.CFIN_PROFILES)} x {len(C.CFIN_HEIGHTS)} configs x 61 angles x 2 = {len(C.CFIN_PROFILES)*len(C.CFIN_HEIGHTS)*61*2} points\n"
    sj = json.load(open(os.path.join(ROOT, "Simulations", "plots_stabilizer", "stabilizer_sweep.json")))
    tb = sj["tunnel_phase_b"]
    txt += f"\nPHASE B  expected pair side force at 10°, {sj['V_tunnel_B']:g} m/s (pessimistic vortex model, mN)\n\n"
    txt += "H (mm)        off      " + "  ".join(f"{k:>8s}" for k in tb) + f"     I ({C.RECT_FIN['span']:.0f} mm)\n"
    for i, r in enumerate(tb[next(iter(tb))]):
        _k = "span%d" % int(C.RECT_FIN["span"])
        txt += f"{r['H_mm']:<13.0f} {r['N_off_mN']:6.1f}   " + "  ".join(f"{tb[k][i]['N_on_mN']:8.1f}" for k in tb) + f"     {tb[_k][i]['I']:+.3f}\n"
    y_ = sj["tunnel_yaw_slope_mN_per_deg"]
    txt += "\nyaw sweep ±6°, fins at 0: side-force slope " + " / ".join(f"{v:.1f}" for v in y_.values()) + " mN/deg (stabilizers " + " / ".join("off" if k == "span0" else k.replace("span", "") + " mm" for k in y_) + ")\n"
    txt += "blockage ~11-12 % (corrected, Barlow-Rae-Pope ch. 9); dN/N_off between stabilizers on and off measures I directly"
    tx.text(0, 0.98, txt, va="top", family="DejaVu Sans Mono", fontsize=8.3)
    fig.suptitle("D4  Adapting Jerrod H's tunnel: Phase A single fin, Phase B full finset + stabilizers", fontsize=12, x=0.02, ha="left", y=0.995)
    save(fig, "D4_wind_tunnel_adaptation")

def research_plan():
    fig, ax = plt.subplots(figsize=(17, 9)); ax.set_xlim(0, 34); ax.set_ylim(0, 18); ax.axis("off")
    def b(x, y, w, h, t, s, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.2", fc=fc, ec=INK, lw=1.1))
        ax.text(x + w / 2, y + h - 0.3, t, ha="center", va="top", fontsize=9.5, weight="bold")
        ax.text(x + w / 2, y + h - 0.9, s, ha="center", va="top", fontsize=7.6, color="#374151", linespacing=1.35)
    def arr(x0, y0, x1, y1, t="", dy=0.3):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.5, color=INK))
        if t: ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, t, ha="center", fontsize=8, weight="bold")
    ax.add_patch(FancyBboxPatch((0.4, 15.4), 33.2, 2.2, boxstyle="round,pad=0.02,rounding_size=0.2", fc="#fff7ed", ec="#9a3412", lw=1.6))
    ax.text(17, 16.9, "MAIN RQ: how do aerofoil section and fin height set the control authority of a servo-actuated triangular fin, and which combination gives the most?", ha="center", fontsize=10, weight="bold", color="#9a3412")
    ax.text(17, 16.0, "SQ1: how much do the rectangular stabilizers take away (span, azimuth)?     SQ2: how well do the sims predict the tunnel, and how far does that carry to flight?", ha="center", fontsize=8.8, color="#374151")
    short = dict(flat_plate="FP", double_wedge="DW", NACA0006="N06", NACA0012="N12")
    ax.text(0.4, 14.6, "Phase A matrix: 4 sections x 5 heights (one fin each)", fontsize=8.5, weight="bold")
    for i, p in enumerate(C.CFIN_PROFILES):
        for j, h in enumerate(C.CFIN_HEIGHTS):
            ax.add_patch(Rectangle((3.0 + j * 1.25, 13.4 - i * 0.75), 1.2, 0.7, fc="#fef3c7" if h == 40 else "#f8fafc", ec="#9ca3af", lw=0.6))
            ax.text(3.6 + j * 1.25, 13.75 - i * 0.75, f"{short[p]}-{int(h)}", ha="center", va="center", fontsize=6.5)
        ax.text(2.9, 13.75 - i * 0.75, p, ha="right", va="center", fontsize=7.5)
    b(0.4, 5.4, 9.0, 5.0, "Simulation", "panel CFD -> VLM -> slender body + BL\n-> vortex interference -> 3-DOF closed loop\nmain RQ: 4 sections x H 15-50\nSQ1: wf_stabilizer.py, span 0-60 x offset 0/22.5/45\n-> predictions for Phase A and Phase B", "#eff6ff")
    b(11.0, 9.0, 10.4, 4.4, "Tunnel Phase A  (main RQ)", "one fin on a reflection-plane panel, stock 100 sq\nX08 Plus cradle on 2 cells: N, CP\n20 configs, ±15° in 0.5° steps, 2 repeats\n-> P* = most OBSERVED authority", "#fff7ed")
    b(11.0, 3.6, 10.4, 4.6, "Tunnel Phase B  (SQ1 + SQ2)", "full control tube + stabilizer tail, 200 x 200 x 750\nP* at H 35 / 40 / 45, stabilizers off / 30 / 50\ndN/N_off = interference ratio I\nyaw sweep: restoring slope; body carry-over", "#f0fdf4")
    b(23.2, 9.6, 10.4, 3.8, "Selection rule", "H* = height with the most SIMULATED authority\nfly P* at H* - 5, H*, H* + 5 mm\ncurrent prediction: H* = 40 -> 35 / 40 / 45", "#fef3c7")
    b(23.2, 3.6, 10.4, 5.0, "Three flights (a little extra)", f"{C.FLIGHT_MOTOR}, only the fins change\nrail-exit fit + coast doublets -> flight Cmδ\none installed point per flight vs the\ntunnel-calibrated prediction (SQ2)\nRMS tilt vs simulated", "#fdf2f8")
    b(11.0, 0.2, 10.4, 2.8, "Analysis", "blockage + reflection-plane corrections; slopes with 95 % CI;\nANOVA section x height; Spearman sim vs tunnel; fit WYV_INTERF", "#f5f3ff")
    arr(10.2, 11.0, 11.0, 11.0, "", 0.3); ax.text(9.9, 8.6, "predict", fontsize=8, weight="bold", rotation=90)
    arr(9.4, 6.5, 11.0, 6.0, "predict", 0.3)
    arr(16.2, 9.0, 16.2, 8.2, "P*", 0.0)
    arr(21.4, 11.2, 23.2, 11.4, "P*", 0.3)
    ax.plot([9.4, 10.2, 10.2, 28.4], [10.0, 10.0, 14.6, 14.6], color=INK, lw=1.5)
    arr(28.4, 14.6, 28.4, 13.45); ax.text(19.0, 14.75, "H* (most simulated authority)", ha="center", fontsize=8, weight="bold")
    arr(28.4, 9.6, 28.4, 8.6)
    arr(16.2, 3.6, 16.2, 3.0)
    arr(23.2, 4.4, 21.4, 2.2, "flight data", 0.4)
    ax.set_title("D5  Research plan: one main question, two sub-questions; tunnel + simulation first, flight as a check", fontsize=11, loc="left")
    save(fig, "D5_research_plan")

if __name__ == "__main__":
    tunnel(); research_plan()
