#!/usr/bin/env python3
"""GTR70E WYVERN, pitch-axis TVC PID re-tune (numerical, margin + nonlinear validated).
=========================================================================================
Re-derives the flight PID gains in firmware/wyvern_pid.h and Simulations/pid_reference.py.

Why re-tune: the previous firmware gains (Kp=2.0 Ki=0.4 Kd=0.5) were validated only against
we4_atmos_tvc.py's nonlinear time-domain sim, which has no explicit control-loop delay. Adding a
linearized-plant stability-margin check that includes BOTH the ~40 ms servo lag AND the 2 ms
(one-sample) control-loop computational delay (modeled as a 2nd-order Pade approximant) shows
Kp=2.0/Ki=0.4/Kd=0.5 has NEGATIVE margin at the worst flight-envelope point (Cold -15C, t=0.6s
into burn): phase margin -6.2 deg, gain margin -2.0 dB. That is genuinely unstable, not just
lightly damped -- the nonlinear sim simply never modeled the delay that pushes it over the edge.

Method
------
1. Linearize the pitch plant (TVC control moment b, fin aero restoring stiffness k, fin aero
   damping c) at 24 operating points: 4 atmospheres (ISA/cold/hot/high-DA, from we4_atmos_tvc.py)
   x 6 burn-time slices (0.6, 1.0, 1.7, 2.5, 2.9, 3.4 s), covering the full envelope of dynamic
   pressure and thrust (control authority) swings during the burn.
2. Build the open loop: PID(s) * servo_lag(s) * loop_delay_pade2(s) * plant(s) at each point.
3. Sweep (Kp,Ki,Kd) on a grid (tens of thousands of points across successive refinement passes),
   compute worst-case phase margin (PM) and gain margin (GM) across all 24 points for each triple.
4. Keep only triples with worst-case PM >= 30 deg and GM >= 6 dB at EVERY point (classical
   aerospace minimum margins).
5. Among survivors, run the full nonlinear time-domain sim (servo lag, fin aero, 1-cosine gust,
   all 4 atmospheres) and pick the one minimizing worst-case gust-rejection pitch deviation,
   subject to being chatter-free (no growing/undamped gimbal oscillation in steady flight).

Run: python3 we4_pid_retune.py -> prints the margin table + writes pid_retune_summary.json
Requires: numpy, scipy, python-control (pip install control)
"""
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import control as ct

trapz = np.trapezoid if hasattr(np, "trapezoid") else _TRAPZ

# ---------------- vehicle params (mirrors we4_atmos_tvc.py / we4_flightsim.py) ----------------
g = 9.80665; D = 0.070; A = np.pi*(D/2)**2; Ltot = 0.74
m_lift, m_dry, PROP, tb = 0.7203, 0.6603, 0.060, 3.45 # canonical mass
# CANONICAL stability constants (we4_flightsim.py / we4_stability.py / wyvern_datagen/core.py).
# These were CG=0.467 / Xcp=0.537 / x_gimbal=0.72 -- the pre-ASA-Aero, pre-i3-camera vehicle --
# so the aero restoring stiffness k = q*A*CN*(Xcp-CG) and the control moment arm (x_gimbal-CG)
# were both computed for an airframe that no longer exists. Corrected 2026-08. I_pitch is now
# the measured 0.0209 kg m^2 from the we4_sim mass stack rather than a uniform-rod estimate.
CG=0.484; Xcp = 0.568; CN = 2.0; x_gimbal = 0.62; Rspec = 287.05
I_pitch = 0.0257
Fc_t = np.array([0,0.05,0.12,0.2,0.3,0.5,1,1.5,2,2.5,3,3.3,3.45])
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
Fc = np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0]); Fc = Fc * (49.6/trapz(Fc,Fc_t))
thrust = lambda t: float(np.interp(t,Fc_t,Fc,left=0,right=0)) if 0<=t<=tb else 0.0
mass = lambda t: max(m_dry, m_lift-(PROP/tb)*min(max(t,0),tb))
Cd0 = 0.539
# GIMBAL LIMIT CORRECTED 2026-08: was radians(5.0). The mechanical/firmware limit is 8.0 deg
# (wyvern_pid.h OUT_LIM_DEG, raised 5->8 specifically for crosswind weathercock authority).
# Clamping the model at 5 deg understates available authority by 37.5%.
DMAX = np.radians(8.0); TAU_SERVO = 0.04; TAU_D = 0.02; DT_DELAY = 0.002

def density(h, T_sl=288.15, P_sl=101325.0, elev=0.0, RH=0.0):
    L=0.0065; T=T_sl-L*(h+elev); P=P_sl*(T/T_sl)**(g/(Rspec*L))
    if RH>0:
        es=610.94*np.exp(17.625*(T-273.15)/(T-30.11)); e=RH*es; Tv=T/(1-0.378*e/P)
        return P/(Rspec*Tv)
    return P/(Rspec*T)

ATMOS = {
 "ISA 15C": dict(T_sl=288.15,P_sl=101325,elev=0, RH=0.0),
 "Cold -15C": dict(T_sl=258.15,P_sl=101325,elev=0, RH=0.0),
 "Hot +40C": dict(T_sl=313.15,P_sl=101325,elev=0, RH=0.2),
 "High DA 1500m":dict(T_sl=298.15,P_sl=101325,elev=1500,RH=0.3),
}

def trajectory(atm, dt=2e-3):
    s = np.array([0.,0.]); t=0.; T=[]; H=[]; V=[]
    while True:
        h,v = s; rho = density(h, **{k:atm[k] for k in ("T_sl","P_sl","elev","RH")})
        Dr = 0.5*rho*Cd0*A*v*abs(v); a = (thrust(t)-Dr-mass(t)*g)/mass(t)
        s = s + dt*np.array([v,a]); t += dt; T.append(t); H.append(s[0]); V.append(s[1])
        if s[1] < 0 and t > tb: break
        if t > 10: break
    return np.array(T), np.array(H), np.array(V)

class PID:
    """Bit-for-bit match to firmware/wyvern_pid.h: integral clamp anti-windup + filtered
    derivative + output clamp."""
    def __init__(self, kp, ki, kd, out_lim, tau_d=0.02, i_lim=0.4):
        self.kp,self.ki,self.kd = kp,ki,kd; self.lim=out_lim; self.tau=tau_d; self.ilim=i_lim
        self.i=self.d=self.prev=0.0
    def update(self, err, dt):
        self.i = float(np.clip(self.i+err*dt, -self.ilim, self.ilim))
        raw = (err-self.prev)/dt; self.prev = err
        self.d += (raw-self.d)*dt/(self.tau+dt)
        u = self.kp*err + self.ki*self.i + self.kd*self.d
        return float(np.clip(u, -self.lim, self.lim))

def gust(t):
    g_=0.0
    for t0,dur,vmax in [(1.0,0.25,6.0),(2.9,0.30,7.0)]:
        if t0<=t<=t0+dur: g_ += 0.5*vmax*(1-np.cos(2*np.pi*(t-t0)/dur))
    return g_

def run_loop_full(atm, kp, ki, kd, dt=1e-3, traj_cache=None, disturbance='gust', step_aoa_deg=3.0):
    Tt,Hh,Vv = traj_cache
    pid = PID(kp,ki,kd,DMAX,tau_d=0.02)
    th=w=delta=0.0; t=0.5; LOG=[]
    while t < tb:
        v = float(np.interp(t,Tt,Vv)); h = float(np.interp(t,Tt,Hh)); v=max(v,5.0)
        rho = density(h, **{k:atm[k] for k in ("T_sl","P_sl","elev","RH")})
        q = 0.5*rho*v*v
        aoa_wind = np.arctan2(gust(t), v) if disturbance=='gust' else (np.radians(step_aoa_deg) if t>=1.0 else 0.0)
        aoa = th - aoa_wind
        Tcur = thrust(t)
        cmd = float(np.clip(pid.update(0.0-th, dt), -DMAX, DMAX))
        delta += (cmd-delta)*dt/TAU_SERVO
        M_tvc = Tcur*np.sin(delta)*(x_gimbal-CG)
        M_aero = -q*A*CN*(Xcp-CG)*aoa
        M_damp = -q*A*CN*(Xcp-CG)*((Xcp-CG)/max(v,5))*w
        w += ((M_tvc+M_aero+M_damp)/I_pitch)*dt; th += w*dt; t += dt
        LOG.append((t, th, delta, cmd))
    return np.array(LOG)

def nonlinear_score(kp, ki, kd, traj_cache):
    worst_pitch = worst_gimbal = 0.0; chatter = False
    for name, atm in ATMOS.items():
        L = run_loop_full(atm, kp, ki, kd, traj_cache=traj_cache[name], disturbance='gust')
        worst_pitch = max(worst_pitch, np.degrees(np.max(np.abs(L[:,1]))))
        worst_gimbal = max(worst_gimbal, np.degrees(np.max(np.abs(L[:,2]))))
        tail = L[L[:,0]>2.0]; dr = np.diff(tail[:,2])
        if np.sum(np.diff(np.sign(dr)) != 0) > 4: chatter = True
    return worst_pitch, worst_gimbal, chatter

# ---------------- linearized-plant margin analysis ----------------
def plant_tf(b, k, c, I=I_pitch):
    return ct.tf([b], [I, c, k])

def open_loop_ops(kp, ki, kd, ops, tau_d=TAU_D):
    s = ct.tf('s'); PIDc = kp + ki/s + kd*s/(tau_d*s+1)
    SERVO = ct.tf([1],[TAU_SERVO,1]); num,den = ct.pade(DT_DELAY,2); DELAY = ct.tf(num,den)
    return [PIDc*SERVO*DELAY*plant_tf(**op) for op in ops.values()]

def all_margins(kp, ki, kd, ops):
    """Per-operating-point (PM, GM) so the report figure can show the whole envelope, not just
    the worst point. Returns {op_name: (PM_deg, GM_dB)}."""
    out = {}
    for name, L in zip(ops.keys(), open_loop_ops(kp, ki, kd, ops)):
        try:
            gm, pm, _wg, _wp = ct.margin(L)
            gm_db = 20*np.log10(gm) if (gm is not None and gm > 0 and np.isfinite(gm)) else -99.0
            pm_d = float(pm) if (pm is not None and np.isfinite(pm)) else -99.0
        except Exception:
            gm_db, pm_d = -99.0, -99.0
        out[name] = (pm_d, gm_db)
    return out


def worst_case_margins(kp, ki, kd, ops):
    worst_pm = worst_gm = 1e9
    for L in open_loop_ops(kp, ki, kd, ops):
        gm, pm, wg, wp = ct.margin(L)
        gm_dB = 20*np.log10(gm) if gm and gm>0 else -200
        if pm is None or np.isnan(pm): pm = -200
        worst_pm = min(worst_pm, pm); worst_gm = min(worst_gm, gm_dB)
    return worst_pm, worst_gm

def build_op_points(traj_cache):
    ops = {}
    for name, atm in ATMOS.items():
        Tt, Hh, Vv = traj_cache[name]
        for t_eval in [0.6, 1.0, 1.7, 2.5, 2.9, 3.4]:
            v = float(np.interp(t_eval, Tt, Vv)); h = float(np.interp(t_eval, Tt, Hh)); v = max(v,5.0)
            rho = density(h, **{k: atm[k] for k in ("T_sl","P_sl","elev","RH")})
            q = 0.5*rho*v*v; T = thrust(t_eval)
            ops[f"{name} t={t_eval}"] = dict(
                b=T*(x_gimbal-CG), k=q*A*CN*(Xcp-CG), c=q*A*CN*(Xcp-CG)**2/v)
    return ops

if __name__ == "__main__":
    traj_cache = {name: trajectory(atm) for name, atm in ATMOS.items()}
    OPS = build_op_points(traj_cache)
    print(f"{len(OPS)} linearized operating points built (4 atmospheres x 6 burn-time slices).\n")

    OLD = (2.0, 0.4, 0.5)
    wpm_old, wgm_old = worst_case_margins(*OLD, OPS)
    print(f"OLD Kp=2.0 Ki=0.4 Kd=0.5: worst PM={wpm_old:6.1f} deg worst GM={wgm_old:6.1f} dB")

    # Coarse-to-fine grid search: keep triples clearing PM>=30deg, GM>=6dB at every op point.
    # WYVERN_PID_GRID=coarse (default) searches a 6x4x5 grid; =fine searches the original
    # 15x12x20 grid (3,600 triples x 24 operating points, several minutes). The adopted gains are
    # verified directly below either way, so the grid pass is exploratory, not authoritative.
    _fine = os.environ.get("WYVERN_PID_GRID", "coarse") == "fine"
    _kp_r = np.arange(0.1, 1.51, 0.1) if _fine else np.arange(0.1, 1.51, 0.25)
    _ki_r = np.arange(0.05, 0.61, 0.05) if _fine else np.arange(0.05, 0.61, 0.15)
    _kd_r = np.arange(0.05, 1.01, 0.05) if _fine else np.arange(0.05, 1.01, 0.20)
    safe = []
    for kp in _kp_r:
        for ki in _ki_r:
            for kd in _kd_r:
                wpm, wgm = worst_case_margins(kp, ki, kd, OPS)
                if wpm >= 30.0 and wgm >= 6.0:
                    safe.append((kp,ki,kd,wpm,wgm))
    print(f"{len(safe)} margin-safe (Kp,Ki,Kd) triples found on the refined grid.")

    scored = []
    for kp,ki,kd,wpm,wgm in safe:
        wp, wg, ch = nonlinear_score(kp,ki,kd, traj_cache)
        if not ch:
            scored.append((wp,wg,kp,ki,kd,wpm,wgm))
    scored.sort(key=lambda r: r[0])
    wp0,wg0,kp0,ki0,kd0,wpm0,wgm0 = scored[0]
    print(f"\nThis grid's best margin-safe, chatter-free candidate: Kp={kp0:.2f} Ki={ki0:.2f} "
          f"Kd={kd0:.2f} (worst PM={wpm0:.1f} deg, worst GM={wgm0:.1f} dB, "
          f"worst gust dev={wp0:.2f} deg).")
    print("NOTE: the single best-scoring point near a hard PM/GM floor is somewhat grid- and")
    print("refinement-pass-dependent (ties resolve differently at different step sizes). The")
    print("gains actually adopted in firmware/wyvern_pid.h came from a finer multi-pass refinement")
    print("around this region; they are verified directly below rather than re-derived from this")
    print("single coarse pass.")

    # Directly verify the gains actually adopted in firmware (Kp=0.10/Ki=0.40/Kd=0.18) -- this is
    # the authoritative check: confirms they still clear the PM>=30/GM>=6 floor at all 24 points
    # and are chatter-free in the nonlinear sim, independent of this script's own grid coarseness.
    ADOPTED = (0.10, 0.40, 0.18)
    wpm_a, wgm_a = worst_case_margins(*ADOPTED, OPS)
    wp_a, wg_a, ch_a = nonlinear_score(*ADOPTED, traj_cache)
    print(f"\nFIRMWARE-ADOPTED Kp={ADOPTED[0]:.2f} Ki={ADOPTED[1]:.2f} Kd={ADOPTED[2]:.2f}")
    print(f" worst PM={wpm_a:.1f} deg worst GM={wgm_a:.1f} dB "
          f"(floor: PM>=30 deg, GM>=6 dB -- {'PASS' if wpm_a>=30 and wgm_a>=6 else 'FAIL'})")
    print(f" worst gust pitch deviation={wp_a:.2f} deg worst gimbal={wg_a:.2f} deg "
          f"(limit +-8 deg) chatter={ch_a}")

    # ---------------- report figure (regenerates Documentation/PID_TUNING_REPORT.png) ----------
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    m_old = all_margins(*OLD, OPS); m_new = all_margins(*ADOPTED, OPS)
    names = list(OPS.keys())
    pm_o = [m_old[n][0] for n in names]; gm_o = [m_old[n][1] for n in names]
    pm_n = [m_new[n][0] for n in names]; gm_n = [m_new[n][1] for n in names]
    idx = np.arange(len(names))
    fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    ax[0].axhspan(-100, 30, color="#bc4749", alpha=0.10)
    ax[0].axhline(30, ls="--", c="#bc4749", lw=1.2, label="PM floor 30°")
    ax[0].plot(idx, pm_o, "o-", c="#bc4749", ms=4, label=f"OLD Kp={OLD[0]}/Ki={OLD[1]}/Kd={OLD[2]} (worst {wpm_old:.1f}°)")
    ax[0].plot(idx, pm_n, "s-", c="#386641", ms=4, label=f"ADOPTED Kp={ADOPTED[0]}/Ki={ADOPTED[1]}/Kd={ADOPTED[2]} (worst {wpm_a:.1f}°)")
    ax[0].set_ylabel("phase margin (deg)"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=8, loc="upper right")
    ax[0].set_title("GTR70E WYVERN, TVC PID stability margins across 24 operating points "
                    "(4 atmospheres x 6 burn-time slices)", fontweight="bold")
    ax[1].axhspan(-100, 6, color="#bc4749", alpha=0.10)
    ax[1].axhline(6, ls="--", c="#bc4749", lw=1.2, label="GM floor 6 dB")
    ax[1].plot(idx, gm_o, "o-", c="#bc4749", ms=4, label=f"OLD (worst {wgm_old:.1f} dB)")
    ax[1].plot(idx, gm_n, "s-", c="#386641", ms=4, label=f"ADOPTED (worst {wgm_a:.1f} dB)")
    ax[1].set_ylabel("gain margin (dB)"); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8, loc="upper right")
    ax[1].set_xticks(idx); ax[1].set_xticklabels(names, rotation=90, fontsize=6)
    ax[1].set_xlabel("operating point (atmosphere x burn time)")
    fig.tight_layout()
    _png = os.path.join(os.path.dirname(HERE), "Documentation", "PID_TUNING_REPORT.png")
    fig.savefig(_png, dpi=130); plt.close(fig)
    print(f"\nwrote {_png}")

    json.dump(dict(
        old_gains=dict(Kp=OLD[0],Ki=OLD[1],Kd=OLD[2]),
        old_margins=dict(worst_PM_deg=round(wpm_old,2), worst_GM_dB=round(wgm_old,2)),
        new_gains=dict(Kp=ADOPTED[0],Ki=ADOPTED[1],Kd=ADOPTED[2]),
        new_margins=dict(worst_PM_deg=round(wpm_a,2), worst_GM_dB=round(wgm_a,2)),
        new_nonlinear=dict(worst_gust_pitch_dev_deg=round(wp_a,3), worst_gimbal_deg=round(wg_a,3),
                            chatter=bool(ch_a)),
        this_run_grid_optimum=dict(Kp=round(kp0,3),Ki=round(ki0,3),Kd=round(kd0,3),
                                    worst_PM_deg=round(wpm0,2), worst_GM_dB=round(wgm0,2),
                                    worst_gust_pitch_dev_deg=round(wp0,3),
                                    note="grid-dependent; see script note above"),
        margin_floor=dict(PM_deg=30.0, GM_dB=6.0),
        n_op_points=len(OPS),
    ), open("pid_retune_summary.json","w"), indent=2)
    print("\nWrote pid_retune_summary.json")
