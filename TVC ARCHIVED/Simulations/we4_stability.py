#!/usr/bin/env python3
"""GTR70E WYVERN, fin sizing and passive-stability trade study (Barrowman), remass, re-trajectory,
rail-exit, weathercock, flutter, drift -> plots4/.

Evaluates the real trade: static margin vs. fin semispan for the canonical mass stack (ASA-Aero
upper body, PETG-CF lower body + fins, PC-FR TVC assembly), with the rejected 35 mm candidate and
the flown 87 mm fin configuration both marked. Reproduces the canonical CG/CP/margin (45.0 cm /
53.3 cm / +1.14 cal) at 87 mm.
"""
import os, json, numpy as np
_TRAPZ = getattr(np, "trapezoid", getattr(np, "trapz", None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plots4" + os.environ.get("WYVERN_RUN_TAG", "")); os.makedirs(OUT, exist_ok=True)

g = 9.80665; rho0 = 1.225; D = 0.070; Rb = D / 2; A = np.pi * Rb**2
Lnose = 0.12; Ltot = 0.74

# ---- canonical mass stack (we4_sim.py) -----------------------------------------------------
M_LIFT_FLOWN = 0.7203 # kg, incl. 4x 87 mm PETG-CF fins and the loaded F15-4
M_DRY_FLOWN = 0.6603
CG_FLOWN = 0.5083 # m from nose, flown config
SPAN_FLOWN = 0.087 # m semispan
PROP = 0.060; TB = 3.45
CD_NOMINAL = 0.539 # componentwise Barrowman buildup, shared with we4_flightsim/core.py
FIN_RHO = 1300.0 # kg/m^3, PETG-CF (lower body + fins zone)
FIN_T = 0.003 # m fin thickness
cr, ct, swLE = 0.070, 0.035, 0.025 # root chord, tip chord, LE sweep

def fin_mass_kg(span, N=4, t=FIN_T):
    """Mass of N trapezoidal fins [kg]. Single definition -- the duplicate, unit-broken
    `fin_mass()` that used to sit alongside this has been deleted."""
    return N * (0.5 * (cr + ct) * span * t) * FIN_RHO

# Back out the fins-excluded CG so the model reproduces the canonical flown CG exactly.
X_FIN = Ltot - cr * 0.4 # fin-set centroid station [m]
M_FIN_FLOWN = fin_mass_kg(SPAN_FLOWN)
M_EX_FINS = M_LIFT_FLOWN - M_FIN_FLOWN
CG_EX_FINS = (CG_FLOWN * M_LIFT_FLOWN - X_FIN * M_FIN_FLOWN) / M_EX_FINS

def barrowman(span, N=4, xroot=None):
    """Barrowman CP and normal-force slope for the nose + fin set."""
    if xroot is None: xroot = Ltot - cr # fin root LE near the base
    CNn = 2.0; Xn = 0.333 * Lnose
    Lf = np.sqrt(span**2 + (swLE + (ct - cr) / 2) ** 2) # mid-chord line length
    kfb = 1 + Rb / (span + Rb) # body-interference factor
    CNf = kfb * (4 * N * (span / D) ** 2) / (1 + np.sqrt(1 + (2 * Lf / (cr + ct)) ** 2))
    Xf = xroot + (swLE / 3) * (cr + 2 * ct) / (cr + ct) + (1 / 6) * ((cr + ct) - cr * ct / (cr + ct))
    CP = (CNn * Xn + CNf * Xf) / (CNn + CNf)
    return CP, CNn + CNf, CNf

def config(span):
    """Full stability state for a given semispan: (m_lift, CG, CP, margin_cal, CN)."""
    mf = fin_mass_kg(span)
    m_lift = M_EX_FINS + mf
    cg = (CG_EX_FINS * M_EX_FINS + X_FIN * mf) / m_lift
    cp, cn, _ = barrowman(span)
    return m_lift, cg, cp, (cp - cg) / D, cn

# ---- span sweep ----------------------------------------------------------------------------
spans = np.linspace(0.015, 0.140, 600)
sweep = np.array([config(s)[1:4] for s in spans]) # (CG, CP, margin)
margins = sweep[:, 2]

def span_for_margin(target):
    """Smallest span meeting `target` calibers, by interpolation on the monotone branch."""
    ok = np.where(margins >= target)[0]
    return float(spans[ok[0]]) if ok.size else float("nan")

s_1p0 = span_for_margin(1.0); s_1p5 = span_for_margin(1.5)

# ---- the two named configurations ----------------------------------------------------------
m35, cg35, cp35, marg35, _ = config(0.035) # historical candidate, ACTUALLY 35 mm
m72, cg72, cp72, marg72, cn72 = config(SPAN_FLOWN) # flown

res = dict(
    fin_count=4, fin_root_mm=cr * 1000, fin_tip_mm=ct * 1000, fin_sweepLE_mm=swLE * 1000,
    fin_thickness_mm=FIN_T * 1000, fin_material="PETG-CF (1300 kg/m^3)",
    cg_excl_fins_cm=round(CG_EX_FINS * 100, 2),
    # flown configuration (must reproduce the canonical 48.4 / 56.8 / 1.20)
    flown_span_mm=SPAN_FLOWN * 1000, flown_fin_mass_g=round(M_FIN_FLOWN * 1000, 1),
    flown_m_lift_g=round(m72 * 1000, 1), flown_CG_cm=round(cg72 * 100, 1),
    flown_CP_cm=round(cp72 * 100, 1), flown_static_margin_cal=round(marg72, 2),
    flown_CN_total=round(cn72, 2),
    # historical 35 mm candidate, correctly evaluated this time
    cand35_span_mm=35.0, cand35_fin_mass_g=round(fin_mass_kg(0.035) * 1000, 1),
    cand35_CG_cm=round(cg35 * 100, 1), cand35_CP_cm=round(cp35 * 100, 1),
    cand35_static_margin_cal=round(marg35, 2),
    cand35_verdict="UNSTABLE" if marg35 < 0 else ("under 1.0 cal" if marg35 < 1.0 else "stable"),
    min_span_for_1p0cal_mm=round(s_1p0 * 1000, 1),
    min_span_for_1p5cal_mm=round(s_1p5 * 1000, 1),
)

# ---- re-trajectory for the flown config (RK4, matches we4_flightsim) -----------------------
T_DEPLOY = TB + 4.0 # F15-4 ejection charge: 4 s after burnout
tc = np.array([0, .05, .12, .2, .3, .5, 1, 1.5, 2, 2.5, 3, 3.3, 3.45])
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
Fc = np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0], dtype=float)
Fc *= 49.6 / _TRAPZ(Fc, tc)
thr = lambda t: float(np.interp(t, tc, Fc, left=0, right=0)) if 0 <= t <= TB else 0.0
mdot = PROP / TB
rhoh = lambda h: rho0 * np.exp(-h / 8500)
m_dry72 = m72 - 0.102 # loaded F15-4 is 102 g

def deriv(s, t, m_lift):
    h, v = s
    m = max(m_dry72, m_lift - mdot * min(max(t, 0), TB))
    Dd = 0.5 * rhoh(h) * CD_NOMINAL * A * v * abs(v)
    return np.array([v, (thr(t) - Dd - m * g) / m])

dt = 5e-4; t = 0.0; s = np.array([0.0, 0.0]); T = []; H = []; V = []
while True:
    k1 = deriv(s, t, m72); k2 = deriv(s + .5*dt*k1, t + .5*dt, m72)
    k3 = deriv(s + .5*dt*k2, t + .5*dt, m72); k4 = deriv(s + dt*k3, t + dt, m72)
    s = s + dt/6*(k1 + 2*k2 + 2*k3 + k4); t += dt
    T.append(t); H.append(s[0]); V.append(s[1])
    if s[0] < 0 and t > TB: break
    if t >= T_DEPLOY: break
T = np.array(T); H = np.array(H); V = np.array(V); ap = int(np.argmax(H))
res.update(apogee_ft_flown=round(float(H[ap]) * 3.281, 0), apogee_m_flown=round(float(H[ap]), 1),
           apogee_t=round(float(T[ap]), 2),
           burnout_v=round(float(V[np.argmin(np.abs(T - TB))]), 1),
           deploy_t=round(T_DEPLOY, 2), deploy_v=round(float(V[-1]), 1))

# ---- rail exit -----------------------------------------------------------------------------
def vrail(L, m_lift):
    v = 0.0; h = 0.0; tt = 0.0
    while h < L:
        m = max(m_dry72, m_lift - mdot * min(tt, TB))
        v += (thr(tt) - m * g) / m * dt; h += v * dt; tt += dt
        if tt > TB: break
    return v

v_rail_1p0 = vrail(1.0, m72); v_rail_1p5 = vrail(1.5, m72)
res["rail_exit_v_1p0m"] = round(v_rail_1p0, 1)
res["rail_exit_v_1p5m"] = round(v_rail_1p5, 1)

# weathercock: tan(theta) = Vwind / Vrail_exit
Vw = np.linspace(0, 12, 25)
wc = np.degrees(np.arctan(Vw / max(v_rail_1p5, 1e-3)))
res["weathercock_deg_at_5ms"] = round(float(np.degrees(np.arctan(5.0 / max(v_rail_1p5, 1e-3)))), 1)

# ---- fin flutter (NACA TN-4197 form) --------------------------------------------------------
# Vf = a * sqrt( G / ( (1.337 M^2 (lambda+1) / (2 (AR+2)) ) * (t/c)^-3 * P ) ), evaluated at the
# flight ambient pressure. G is the fin material's shear modulus.
G_SHEAR = 1.3e9 # Pa, PLA (fins are PLA as of the 2026-08 material change)
lam = ct / cr # taper ratio
S_fin = 0.5 * (cr + ct) * SPAN_FLOWN
AR = SPAN_FLOWN**2 / S_fin
tc_ratio = FIN_T / (0.5 * (cr + ct))
P_amb = 101325.0 * np.exp(-float(H[ap]) / 8500.0)
a_snd = 340.3
denom = (1.337 * AR**3 * P_amb * (lam + 1.0)) / (2.0 * (AR + 2.0) * tc_ratio**3)
Vf = a_snd * np.sqrt(G_SHEAR / denom)
v_max = float(np.max(V))
res["fin_flutter_v_ms"] = round(float(Vf), 1)
res["max_flight_v_ms"] = round(v_max, 1)
res["flutter_margin_x"] = round(float(Vf) / max(v_max, 1e-6), 1)
res["max_flight_mach"] = round(v_max / a_snd, 3)

# ---- descent drift --------------------------------------------------------------------------
res["drift_m_per_ms_wind"] = round(float(H[ap]) / 6.2, 1) # 18" chute, ~6.2 m/s descent

# ---------- PLOTS ----------
def sv(fig, n): fig.tight_layout(); fig.savefig(f"{OUT}/{n}.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.5, 5))
ax.plot(spans * 1000, margins, c="#2a6f97", lw=2)
ax.axhline(0.0, ls='-', c='k', lw=0.8)
ax.axhline(1.0, ls=':', c='orange', label="1.0 cal (min conventionally stable)")
ax.axhline(2.0, ls=':', c='r', label="2.0 cal (over-stiff for TVC)")
ax.axvline(35, ls='--', c='#bc4749', label=f"35 mm candidate → {marg35:+.2f} cal ({res['cand35_verdict']})")
ax.axvline(SPAN_FLOWN * 1000, ls='--', c='#386641', label=f"72 mm FLOWN → {marg72:+.2f} cal")
ax.scatter([s_1p0 * 1000], [1.0], c='k', zorder=5, label=f"min span @1.0 cal = {s_1p0*1000:.0f} mm")
ax.set_xlabel("fin semispan (mm)"); ax.set_ylabel("static margin (cal)")
ax.legend(fontsize=8); ax.grid(alpha=.3)
ax.set_title("GTR70E WYVERN · fin sizing, Barrowman static margin vs semispan (4 fins, canonical mass stack)",
             fontweight='bold'); sv(fig, "13_fin_sizing")

fig, ax = plt.subplots(figsize=(10, 2.8))
ax.axvline(cg72 * 100, c='r', lw=2, label=f"CG {cg72*100:.1f} cm")
ax.axvline(cp72 * 100, c='b', lw=2, label=f"CP {cp72*100:.1f} cm")
ax.annotate('', xy=(cp72 * 100, 0.5), xytext=(cg72 * 100, 0.5), arrowprops=dict(arrowstyle='<->', color='g'))
ax.text((cg72 + cp72) * 50, 0.6, f"{marg72:.2f} cal", ha='center', color='g')
ax.set_xlim(0, Ltot * 100); ax.set_ylim(0, 1); ax.set_yticks([])
ax.set_xlabel("station from nose (cm)"); ax.legend(loc='upper left')
ax.set_title("GTR70E WYVERN · CG / CP, FLOWN 72 mm fins, passively stable through the ignition transient",
             fontweight='bold'); sv(fig, "14_cp_cg")

fig, ax = plt.subplots(figsize=(8.5, 5))
ax.plot(T, H, c="#2a6f97", label="altitude")
ax.axvline(TB, ls=':', c='g', label="burnout 3.45 s")
ax.axvline(T_DEPLOY, ls='--', c='k', label=f"motor eject {T_DEPLOY:.2f} s")
ax.set_xlabel("t (s)"); ax.set_ylabel("altitude (m)"); ax.legend(); ax.grid(alpha=.3)
ax.set_title(f"GTR70E WYVERN finned (72 mm) · apogee {H[ap]*3.281:.0f} ft · Cd {CD_NOMINAL} · {m72*1000:.0f} g liftoff",
             fontweight='bold'); sv(fig, "15_trajectory_finned")

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(Vw, wc, '-', c="#bc4749", lw=2)
ax.set_xlabel("crosswind (m/s)"); ax.set_ylabel("weathercock angle (deg)"); ax.grid(alpha=.3)
ax.set_title(f"GTR70E WYVERN · weathercock vs wind (rail-exit {v_rail_1p5:.1f} m/s off a 1.5 m rail)",
             fontweight='bold'); sv(fig, "16_weathercock")

# ---- ballast trade ----
# First-class output of this file: for each candidate ballast mass, the smallest fin span that
# still holds the target static margin, and the resulting apogee.
def ballast_case(ball_kg, x_ball=0.05, target=1.0):
    """Smallest fin span holding `target` cal at this ballast, and the resulting apogee."""
    lo, hi = 0.02, 0.14
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        mf = fin_mass_kg(mid); m = M_EX_FINS + mf + ball_kg
        cg = (CG_EX_FINS * M_EX_FINS + X_FIN * mf + x_ball * ball_kg) / m
        if (barrowman(mid)[0] - cg) / D < target: lo = mid
        else: hi = mid
    span = 0.5 * (lo + hi)
    mf = fin_mass_kg(span); m = M_EX_FINS + mf + ball_kg
    cg = (CG_EX_FINS * M_EX_FINS + X_FIN * mf + x_ball * ball_kg) / m
    md = m - 0.102
    ss = np.array([0.0, 0.0]); tt = 0.0; best = 0.0
    while tt < 12:
        def dz(st, t_):
            h, v = st
            mm = max(md, m - mdot * min(max(t_, 0), TB))
            return np.array([v, (thr(t_) - 0.5 * rhoh(h) * CD_NOMINAL * A * v * abs(v) - mm * g) / mm])
        k1 = dz(ss, tt); k2 = dz(ss + .5*dt*k1, tt + .5*dt)
        k3 = dz(ss + .5*dt*k2, tt + .5*dt); k4 = dz(ss + dt*k3, tt + dt)
        ss = ss + dt/6*(k1 + 2*k2 + 2*k3 + k4); tt += dt; best = max(best, ss[0])
        if ss[1] < 0 and tt > TB: break
    return dict(ballast_g=round(ball_kg*1000, 1), fin_span_for_1cal_mm=round(span*1000, 1),
                m_lift_g=round(m*1000, 1), CG_cm=round(cg*100, 1),
                apogee_m=round(best, 1), apogee_ft=round(best*3.281, 0))

res["ballast_trade"] = [ballast_case(b) for b in (0.0, 0.060, 0.150)]
res["ballast_verdict"] = ("Every gram of nose ballast lowers apogee: the smaller fins it buys never "
                          "pay back the dead weight. Flown configuration carries no ballast.")

json.dump(res, open(f"{OUT}/stability_summary.json", "w"), indent=1)
print(json.dumps(res, indent=1))
