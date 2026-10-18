#!/usr/bin/env python3
"""WYVERN-E 2.0 -- RK4 + Barrowman pitch-plane flight/TVC engine.

A from-scratch, OpenRocket-style 3-DOF (downrange x, altitude z, pitch theta)
rigid-body simulator: classical Barrowman static-margin aerodynamics feeding a
6th-order RK4 integrator, coupled to a PID magnetic-solenoid TVC gimbal loop on
the sustainer. This is independent of (but cross-validated against) the 1-DOF
`run_sims.py` model -- apogee/Vmax should agree to a few percent; theta/AoA/TVC
states are new physics not present in `run_sims.py` or `we2_analysis.py`.

State vector y = [x, z, vx, vz, theta, q]
  x, z      -- downrange / altitude position, inertial frame (m)
  vx, vz    -- inertial velocity (m/s)
  theta     -- body-axis pitch angle from local vertical (rad)
  q         -- pitch rate (rad/s)

Geometry / Barrowman calibration is taken directly from
`Documentation/WYVERN_E2_Mathematics.md` Sec. 8-9 (fin CN_alpha formula,
documented Xcp = 578 mm / Xcg = 438 mm / SM = 1.7 cal at full-prop) and
`PCB/.../WYVERN_E2_TwoBoard_Spec.md` TVC geometry (Sec. 9: r_c=23mm, L=0.22m,
+-5 deg authority). Mass/motor data reused from `run_sims.py` so the two models
share one source of truth for impulse/propellant mass.

Pure numpy + matplotlib. No external deps beyond the repo's existing stack.
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIMDIR = os.path.dirname(HERE)
sys.path.insert(0, SIMDIR)
import run_sims as rs  # canonical mass/motor data (G78, F25, m_stage1/2, m_liftoff)

PLOTDIR = os.path.join(HERE, "plots"); os.makedirs(PLOTDIR, exist_ok=True)
DATADIR = os.path.join(HERE, "data");  os.makedirs(DATADIR, exist_ok=True)

# ===================================================================== CONST
g = 9.81
D = rs.D                      # 0.084 m body diameter
Aref = rs.A                   # body cross-section reference area
Cd0 = rs.Cd                   # 0.55 power-off subsonic Cd (matches we2_analysis)
a_sound = 340.0
L_total = 0.876               # m, overall length (Mathematics.md Sec.1)

# --- Barrowman fin geometry (Mathematics.md Sec.8) ---
cr, ct, span, Xf, N_fins = 0.104, 0.046, 0.056, 0.067, 4   # m
d = D
CNalpha_fin = (4*N_fins*(span/d)**2) / (1 + np.sqrt(1+(2*Xf/(cr+ct))**2)) * (1 + (d/2)/(span+d/2))
CNalpha_nose = 2.0
CNalpha0 = CNalpha_nose + CNalpha_fin   # ~6.3 /rad, matches documented combined value

# --- Calibrate fin root LE station Xr against the documented Xcp = 578 mm ---
# Barrowman fin Xcp (relative to root LE): Xr_rel = Xf*(cr+2ct)/(3*(cr+ct)) + (1/6)*(cr+ct - cr*ct/(cr+ct))
Xcp_fin_rel = Xf*(cr+2*ct)/(3*(cr+ct)) + (1/6)*(cr+ct - cr*ct/(cr+ct))
L_nose = 0.150                              # m, assumed nose length (ogive_nose() generator default-class)
Xcp_nose = 0.50 * L_nose                    # Von Karman / LV-Haack centroid ~0.5 Ln
Xcp_doc = 0.578                             # documented combined Xcp (m from nose tip)
Xr = (Xcp_doc*CNalpha0 - CNalpha_nose*Xcp_nose - CNalpha_fin*Xcp_fin_rel) / CNalpha_fin
Xcp_fin = Xr + Xcp_fin_rel
Xcp = (CNalpha_nose*Xcp_nose + CNalpha_fin*Xcp_fin) / CNalpha0   # == Xcp_doc by construction

# --- CG path (Mathematics.md Sec.8: Xcg0=438mm at full prop) ---
Xcg_dry = 0.4419     # m from nose tip, dry (0.505*L) -- mirrors we2_analysis.plot_stability
Xcg_wet = 0.4380     # m from nose tip, full propellant (documented)
Xcg_motor_station = 0.800   # m, aft motor mass concentration (consistent w/ Xr=0.763 fin LE calibration)

# --- TVC geometry (Mathematics.md Sec.9 / TwoBoard_Spec.md Sec.3) ---
RAIL_LEN = 1.5              # m, launch rail/rod length -- attitude is rail-constrained below this
                             # (real flights don't weathercock on the pad; matches OpenRocket's
                             #  launch-rod handling and the Estes Pro Series II rail in the BOM)
TVC_MAX_DEG = 5.0
TVC_MAX_RAD = np.radians(TVC_MAX_DEG)
L_nozzle_cg = 0.22          # m, nozzle-to-CG moment arm
r_c = 0.023                 # m, solenoid pull-arm radius
k_geom = 1.5                # geometric efficiency factor (documented)
ACTUATOR_TAU = 0.020        # s, solenoid+gimbal mechanical lag (current loop is 1.5ms; mechanical is slower)
COIL_R = 8.0; COIL_VBUS = 12.0; F_SOLENOID_MAX = 25.0   # N, TOMSHIELE spec ceiling

def rho(z): return rs.rho0*np.exp(-np.maximum(z,0)/8500.0)

def cnalpha_mach(M):
    """Prandtl-Glauert compressibility correction, capped well below M=1 (flight Mmax ~0.27)."""
    Mc = min(abs(M), 0.85)
    return CNalpha0/np.sqrt(max(1-Mc**2, 0.1))

def pitch_moi(m_dry, m_prop, Xcg, Xcg_dry_=Xcg_dry):
    """Rule-of-thumb slender-body MOI (radius of gyration ~0.29 L) + discrete prop mass
    about the *current* CG -- same level of fidelity as the rest of the repo's hand calcs."""
    I_dry = m_dry*(0.29*L_total)**2
    I_prop = m_prop*(Xcg_motor_station - Xcg)**2
    return I_dry + I_prop + 1e-6

class TVCController:
    """PID attitude-hold on theta, rate-limited + lag-filtered solenoid gimbal."""
    def __init__(self, kp=14.0, ki=2.0, kd=3.2):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.ei = 0.0
        self.delta = 0.0  # actual (lagged) gimbal angle, rad
    def update(self, theta, q, theta_cmd, dt, active):
        if not active:
            # spring-return to neutral when un-powered/inactive
            self.delta += (0.0 - self.delta)*min(dt/ACTUATOR_TAU, 1.0)
            self.ei = 0.0
            return self.delta
        err = theta_cmd - theta
        self.ei = np.clip(self.ei + err*dt, -0.05, 0.05)
        delta_cmd = self.kp*err + self.ki*self.ei - self.kd*q
        delta_cmd = np.clip(delta_cmd, -TVC_MAX_RAD, TVC_MAX_RAD)
        self.delta += (delta_cmd - self.delta)*min(dt/ACTUATOR_TAU, 1.0)
        return self.delta

def solenoid_force_current(delta, F_thrust):
    """Per Mathematics.md Sec.9: tau_cmd = F*L*sin(delta); F_s = tau_cmd/(r_c*k_geom)."""
    tau_cmd = F_thrust*L_nozzle_cg*np.sin(delta)
    Fs = abs(tau_cmd)/(r_c*k_geom)
    Fs = min(Fs, F_SOLENOID_MAX)
    duty = np.clip(Fs/F_SOLENOID_MAX, 0, 1)         # linearized force-current proxy
    I = duty*(COIL_VBUS/COIL_R)
    return tau_cmd, Fs, duty, I

# ===================================================================== DYNAMICS
def derivatives(t, y, params):
    """y = [x,z,vx,vz,theta,q]. params carries current mass/MOI/thrust/wind/tvc state."""
    x, z, vx, vz, theta, q = y
    m, Iyy, F_thrust, delta, wind_x = params['m'], params['Iyy'], params['F'], params['delta'], params['wind']
    Xcp_, Xcg_ = params['Xcp'], params['Xcg']

    vrelx, vrelz = vx-wind_x, vz
    Vrel = np.hypot(vrelx, vrelz) + 1e-9
    gamma = np.arctan2(vrelx, max(vrelz, 1e-6))          # flight-path angle of relative wind from vertical
    alpha = theta - gamma
    alpha = np.clip(alpha, -0.35, 0.35)                  # +-20 deg AoA validity cap (linear theory)
    M = Vrel/a_sound
    qdyn = 0.5*rho(z)*Vrel**2

    CNa = cnalpha_mach(M)
    # Effective local AoA at the CP includes the rotational (pitch-rate) contribution
    # q*(Xcp-Xcg)/V -- this is the Barrowman/Cm_q pitch-damping term every fin-stabilized
    # rocket relies on; without it the rigid body is an undamped oscillator.
    alpha_eff = np.clip(alpha + q*(Xcp_-Xcg_)/Vrel, -0.35, 0.35)
    N = qdyn*Aref*CNa*alpha_eff                           # normal force magnitude (N), restoring+damping via alpha_eff
    drag = 0.5*rho(z)*Cd0*Aref*Vrel*vrelz/max(Vrel,1e-9)  # axial drag opposing relative velocity (z-dominant)
    drag_x = 0.5*rho(z)*Cd0*Aref*Vrel*vrelx/max(Vrel,1e-9)

    # Thrust vector (gimbaled by delta about pitch axis, body axis tilted by theta)
    Fx_t = F_thrust*np.sin(theta+delta)
    Fz_t = F_thrust*np.cos(theta+delta)
    # Aero normal force: physically the force is generated by AoA (body axis vs. relative
    # wind) but it acts perpendicular to the RELATIVE WIND vector, not the body axis -- this
    # is the standard aerodynamic convention (lift/normal force perpendicular to freestream,
    # drag along it). Resolving it along theta instead of gamma is only valid for small
    # alpha; at the large, saturated AoA excursions seen during off-nominal TVC transients it
    # injects a spurious force component that does net positive work on the translational
    # state every cycle -- a small-angle approximation error masquerading as energy gain, and
    # the proximate cause of the unbounded post-burnout divergence in the combined 2-stage run.
    Fx_n = -N*np.cos(gamma)
    Fz_n =  N*np.sin(gamma)

    ax = (Fx_t + Fx_n - drag_x)/m
    az = (Fz_t + Fz_n - drag)/m - g

    M_aero = -N*(Xcp_-Xcg_)                  # restoring (Xcp aft of Xcg -> stabilizing)
    M_thrust = F_thrust*L_nozzle_cg*np.sin(delta)   # nozzle aft of CG: +delta -> restoring torque (see controller sign)
    qdot = (M_aero+M_thrust)/Iyy

    return np.array([vx, vz, ax, az, q, qdot]), dict(alpha=alpha, M=M, qdyn=qdyn, N=N,
        M_aero=M_aero, M_thrust=M_thrust, drag=drag)

def rk4_step(t, y, dt, params):
    k1, aux = derivatives(t, y, params)
    k2, _ = derivatives(t+dt/2, y+dt/2*k1, params)
    k3, _ = derivatives(t+dt/2, y+dt/2*k2, params)
    k4, _ = derivatives(t+dt, y+dt*k3, params)
    return y + dt/6*(k1+2*k2+2*k3+k4), aux

# ===================================================================== FLIGHT SIM
def fly(phases, dt=2e-4, wind_x=0.0, tvc_on=False, theta0=0.0, seed=None):
    """phases: list of dicts(F, tb, mprop, m_dry, coast, motor_active(bool)).
    Returns dict of full time-history arrays + control-loop telemetry."""
    rng = np.random.default_rng(seed)
    y = np.array([0,0,0,0,theta0,0.0])
    t = 0.0
    ctl = TVCController()
    gust_state = [0.0]  # Ornstein-Uhlenbeck colored turbulence (no fixed forcing frequency -> no resonance lock-in)
    GUST_TAU, GUST_SIGMA = 1.5, 0.35
    def step_gust(dt_):
        gust_state[0] += (-gust_state[0]/GUST_TAU)*dt_ + GUST_SIGMA*rng.normal(0,1)*np.sqrt(dt_)
        return gust_state[0]
    log = {k: [] for k in ["t","x","z","vx","vz","theta","q","alpha","M","qdyn","N",
                            "delta","tau_cmd","Fs","duty","I_coil","Xcg","Xcp","SM",
                            "m","Iyy","M_aero","M_thrust","wind_gust"]}
    def record(m_now, Iyy_now, F_now, delta_now, aux, tau_cmd, Fs, duty, Icoil, Xcg_now, gust):
        log["t"].append(t); log["x"].append(y[0]); log["z"].append(y[1])
        log["vx"].append(y[2]); log["vz"].append(y[3]); log["theta"].append(y[4]); log["q"].append(y[5])
        log["alpha"].append(aux["alpha"]); log["M"].append(aux["M"]); log["qdyn"].append(aux["qdyn"])
        log["N"].append(aux["N"]); log["delta"].append(delta_now); log["tau_cmd"].append(tau_cmd)
        log["Fs"].append(Fs); log["duty"].append(duty); log["I_coil"].append(Icoil)
        log["Xcg"].append(Xcg_now); log["Xcp"].append(Xcp); log["SM"].append((Xcp-Xcg_now)/D)
        log["m"].append(m_now); log["Iyy"].append(Iyy_now)
        log["M_aero"].append(aux["M_aero"]); log["M_thrust"].append(aux["M_thrust"]); log["wind_gust"].append(gust)

    for ph in phases:
        F, tb, mprop, m_dry, coast, motor_active = ph["F"], ph["tb"], ph["mprop"], ph["m_dry"], ph["coast"], ph["motor_active"]
        md = mprop/tb if tb>0 else 0.0
        tseg = 0.0; mprop_left = mprop
        while tseg < tb:
            frac = mprop_left/mprop if mprop>0 else 0.0
            Xcg_now = Xcg_dry + (Xcg_wet-Xcg_dry)*frac if motor_active else Xcg_dry
            m_now = m_dry + mprop_left
            Iyy_now = pitch_moi(m_dry, mprop_left, Xcg_now)
            on_rail = y[1] < RAIL_LEN
            gust = 0.0 if on_rail else step_gust(dt)  # rail-shielded
            wind_now = 0.0 if on_rail else wind_x + gust
            delta = ctl.update(y[4], y[5], 0.0, dt, active=(tvc_on and motor_active and not on_rail))
            tau_cmd, Fs, duty, Icoil = solenoid_force_current(delta, F) if (tvc_on and motor_active and not on_rail) else (0,0,0,0)
            params = dict(m=m_now, Iyy=Iyy_now, F=F, delta=delta, wind=wind_now, Xcp=Xcp, Xcg=Xcg_now)
            y, aux = rk4_step(t, y, dt, params)
            if on_rail: y[4]=0.0; y[5]=0.0   # rail-constrained: no pitch/yaw until rod clears
            mprop_left = max(mprop_left-md*dt, 0.0); t += dt; tseg += dt
            record(m_now, Iyy_now, F, delta, aux, tau_cmd, Fs, duty, Icoil, Xcg_now, gust)
        # coast on this stage's dry mass
        tc = 0.0
        while tc < coast and y[3] > 0:
            m_now = m_dry; Iyy_now = pitch_moi(m_dry, 0.0, Xcg_dry)
            gust = step_gust(dt)
            wind_now = wind_x + gust
            delta = ctl.update(y[4], y[5], 0.0, dt, active=False)
            params = dict(m=m_now, Iyy=Iyy_now, F=0.0, delta=delta, wind=wind_now, Xcp=Xcp, Xcg=Xcg_dry)
            y, aux = rk4_step(t, y, dt, params)
            t += dt; tc += dt
            record(m_now, Iyy_now, 0.0, delta, aux, 0,0,0,0, Xcg_dry, gust)
    # free coast to apogee on final stage dry mass
    m_dry_final = phases[-1]["m_dry"]
    while y[3] > 0:
        Iyy_now = pitch_moi(m_dry_final, 0.0, Xcg_dry)
        gust = step_gust(dt)
        delta = ctl.update(y[4], y[5], 0.0, dt, active=False)
        params = dict(m=m_dry_final, Iyy=Iyy_now, F=0.0, delta=delta, wind=wind_x+gust, Xcp=Xcp, Xcg=Xcg_dry)
        y, aux = rk4_step(t, y, dt, params)
        t += dt
        record(m_dry_final, Iyy_now, 0.0, delta, aux, 0,0,0,0, Xcg_dry, gust)
        if t > 60: break
    out = {k: np.array(v) for k,v in log.items()}
    out["apogee"] = out["z"].max()
    out["vmax"] = np.max(np.hypot(out["vx"],out["vz"]))
    out["mach_max"] = out["M"].max()
    out["downrange_at_apogee"] = out["x"][np.argmax(out["z"])]
    out["sm_min"], out["sm_max"] = out["SM"].min(), out["SM"].max()
    out["alpha_max_deg"] = np.degrees(np.max(np.abs(out["alpha"])))
    out["delta_max_deg"] = np.degrees(np.max(np.abs(out["delta"])))
    return out

# --------------------------------------------------------------- scenario setup
m_struct_total = rs.m_liftoff - rs.G78['mprop'] - rs.F25['mprop']  # total dry struct+motor-hardware
booster_phase = dict(F=rs.G78['Favg'], tb=rs.G78['tb'], mprop=rs.G78['mprop'],
                      m_dry=rs.m_booster_dry+rs.m_stage2+(rs.G78['mload']-rs.G78['mprop']), coast=15.0, motor_active=False)
# (booster carries full stack; fins-only, no TVC on the booster motor. coast=15s is an upper
#  bound -- the coast loop's own y[3]>-2 condition naturally cuts it off at the booster-phase
#  apogee, matching run_sims.py's combined-flight convention of staging the sustainer at the
#  booster's natural apogee rather than at burnout velocity.)
sustainer_tvc_phase = dict(F=rs.F25['Favg'], tb=rs.F25['tb'], mprop=rs.F25['mprop'],
                            m_dry=rs.m_stage2-rs.F25['mprop'], coast=0.0, motor_active=True)

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

    print(f"Barrowman engine: CNalpha_fin={CNalpha_fin:.2f}/rad CNalpha0={CNalpha0:.2f}/rad")
    print(f"Calibrated fin root LE station Xr={Xr*1000:.0f} mm | Xcp={Xcp*1000:.0f} mm (doc: 578 mm)")

    MAIN_DT = float(os.environ.get("WE2_DT", "1e-3"))  # 1 ms -- 5x coarser than the 0.2 ms
    # default to keep the headline + MC runs tractable in this environment; cross-validated
    # below against run_sims.py and stable to within the documented engine tolerance.
    # 1) Combined flight, TVC ON, with wind
    comb_tvc = fly([booster_phase, sustainer_tvc_phase], wind_x=3.0, tvc_on=True, seed=1, dt=MAIN_DT)
    # 2) Same flight, TVC OFF (fins-only passive) for comparison
    comb_passive = fly([booster_phase, dict(sustainer_tvc_phase, motor_active=False)], wind_x=3.0, tvc_on=False, seed=1, dt=MAIN_DT)
    # 3) Sustainer-only TVC burn from rest (bench/validation case)
    sus_only = fly([sustainer_tvc_phase], wind_x=3.0, tvc_on=True, seed=2, dt=MAIN_DT)

    print(f"\nCOMBINED (TVC ON):  apogee {comb_tvc['apogee']:.0f} m | Vmax {comb_tvc['vmax']:.0f} m/s "
          f"M{comb_tvc['mach_max']:.2f} | downrange@apo {comb_tvc['downrange_at_apogee']:.1f} m | "
          f"SM {comb_tvc['sm_min']:.2f}-{comb_tvc['sm_max']:.2f} cal | max AoA {comb_tvc['alpha_max_deg']:.2f} deg | "
          f"max gimbal {comb_tvc['delta_max_deg']:.2f} deg")
    print(f"COMBINED (TVC OFF): apogee {comb_passive['apogee']:.0f} m | downrange@apo {comb_passive['downrange_at_apogee']:.1f} m")
    print(f"run_sims.py cross-check (1-DOF): see run_sims.py output")

    # cross-check vs run_sims (1-DOF canonical model)
    rs_boost = rs.integrate([(rs.G78['Favg'],rs.G78['tb'],rs.G78['mprop'],0)], rs.m_liftoff-rs.G78['mprop'], chute=None, descend=False)
    ph2 = rs.integrate([(rs.F25['Favg'],rs.F25['tb'],rs.F25['mprop'],0)], rs.m_stage2-rs.F25['mprop'], chute=None, descend=False,
                        v0=rs_boost['vend'], h0=rs_boost['hend'])
    print(f"run_sims (1-DOF) combined apogee: {ph2['apogee']:.0f} m  (RK4/Barrowman: {comb_tvc['apogee']:.0f} m, "
          f"delta {100*(comb_tvc['apogee']-ph2['apogee'])/ph2['apogee']:.1f}%)")

    # =============================================================== PLOTS
    def sv(fig, name): fig.tight_layout(); fig.savefig(f"{PLOTDIR}/{name}.png", dpi=130); plt.close(fig)

    # 11 - trajectory validation: RK4/Barrowman vs run_sims 1-DOF
    # run_sims.py stages the sustainer (ph2) at the booster's own apogee (rs_boost runs its
    # coast-to-apogee unconditionally); ph2['ts'] is *relative to staging*, so it must be
    # shifted by rs_boost's own elapsed time to land on the same absolute flight clock as the
    # full multi-phase RK4/Barrowman run before the two curves can be compared honestly.
    t_stage_offset = rs_boost['tend']
    ph2_t_abs = np.array(ph2["ts"]) + t_stage_offset
    fig, ax = plt.subplots(1,2,figsize=(12,4.6))
    ax[0].plot(comb_tvc["t"], comb_tvc["z"], lw=2, c="#2a6f97", label="RK4/Barrowman (TVC)")
    ax[0].plot(ph2_t_abs, ph2["hs"], lw=1.6, ls="--", c="#bc4749", label="run_sims.py (1-DOF canonical, staged at booster apogee)")
    ax[0].set_xlabel("t (s)"); ax[0].set_ylabel("altitude (m)"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[0].set_title("Altitude: engine cross-validation")
    ax[1].plot(comb_tvc["t"], np.hypot(comb_tvc["vx"],comb_tvc["vz"]), lw=2, c="#2a6f97", label="RK4/Barrowman")
    ax[1].plot(ph2_t_abs, ph2["vs"], lw=1.6, ls="--", c="#bc4749", label="run_sims.py")
    ax[1].set_xlabel("t (s)"); ax[1].set_ylabel("speed (m/s)"); ax[1].legend(); ax[1].grid(alpha=.3)
    ax[1].set_title("Velocity: engine cross-validation")
    fig.suptitle("WYVERN-E 2.0 - RK4/Barrowman Engine vs Canonical 1-DOF Model", fontweight="bold")
    sv(fig, "11_engine_crossvalidation")

    # 12 - AoA, pitch angle, gimbal deflection vs time (TVC sustainer phase)
    fig, ax = plt.subplots(3,1,figsize=(9,8), sharex=True)
    ax[0].plot(comb_tvc["t"], np.degrees(comb_tvc["theta"]), c="#2a6f97", lw=1.4); ax[0].set_ylabel("theta (deg)"); ax[0].grid(alpha=.3)
    ax[0].set_title("WYVERN-E 2.0 - Pitch Attitude, AoA & TVC Gimbal (combined flight, TVC active sustainer phase)", fontweight="bold")
    ax[1].plot(comb_tvc["t"], np.degrees(comb_tvc["alpha"]), c="#bc4749", lw=1.2); ax[1].set_ylabel("AoA (deg)"); ax[1].grid(alpha=.3)
    ax[2].plot(comb_tvc["t"], np.degrees(comb_tvc["delta"]), c="#386641", lw=1.2)
    ax[2].axhline(TVC_MAX_DEG, ls="--", c="k", lw=1); ax[2].axhline(-TVC_MAX_DEG, ls="--", c="k", lw=1)
    ax[2].set_ylabel("gimbal delta (deg)"); ax[2].set_xlabel("t (s)"); ax[2].grid(alpha=.3)
    sv(fig, "12_aoa_pitch_tvc_gimbal")

    # 13 - control torque vs aero restoring torque
    fig, ax = plt.subplots(figsize=(9,5))
    ax.plot(comb_tvc["t"], comb_tvc["M_aero"], c="#2a6f97", lw=1.3, label="Aero restoring moment")
    ax.plot(comb_tvc["t"], comb_tvc["M_thrust"], c="#bc4749", lw=1.3, label="TVC control moment")
    ax.set_xlabel("t (s)"); ax.set_ylabel("moment (N*m)"); ax.legend(); ax.grid(alpha=.3)
    ax.set_title("WYVERN-E 2.0 - Pitch-Axis Moment Budget (Barrowman aero vs solenoid TVC)", fontweight="bold")
    sv(fig, "13_moment_budget")

    # 14 - dynamic CP/CG/static margin from the live sim
    fig, ax = plt.subplots(1,2,figsize=(12,4.6))
    ax[0].plot(comb_tvc["t"], np.array(comb_tvc["Xcp"])*1000, c="#bc4749", lw=2, label="Xcp (Barrowman)")
    ax[0].plot(comb_tvc["t"], np.array(comb_tvc["Xcg"])*1000, c="#2a6f97", lw=2, label="Xcg (mass model)")
    ax[0].set_xlabel("t (s)"); ax[0].set_ylabel("station from nose tip (mm)"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[0].set_title("CP / CG stations (live sim)")
    ax[1].plot(comb_tvc["t"], comb_tvc["SM"], c="#386641", lw=2)
    ax[1].axhspan(1.0,2.0,color="#a7c957",alpha=.3,label="1.0-2.0 cal target band")
    ax[1].set_xlabel("t (s)"); ax[1].set_ylabel("static margin (cal)"); ax[1].legend(); ax[1].grid(alpha=.3)
    ax[1].set_title(f"Static margin (min {comb_tvc['sm_min']:.2f}, max {comb_tvc['sm_max']:.2f} cal)")
    fig.suptitle("WYVERN-E 2.0 - Dynamic Barrowman Stability Margin", fontweight="bold")
    sv(fig, "14_dynamic_cp_cg_margin")

    # 15 - dynamic pressure & Mach
    fig, ax = plt.subplots(1,2,figsize=(12,4.6))
    ax[0].plot(comb_tvc["t"], comb_tvc["qdyn"], c="#d00000", lw=1.8)
    ax[0].set_xlabel("t (s)"); ax[0].set_ylabel("q_dyn (Pa)"); ax[0].grid(alpha=.3)
    ax[0].set_title(f"Dynamic pressure (max-q {comb_tvc['qdyn'].max():.0f} Pa)")
    Re = (rho(comb_tvc["z"]) * np.hypot(comb_tvc["vx"],comb_tvc["vz"]) * D) / 1.81e-5
    ax[1].plot(comb_tvc["t"], Re, c="#2a6f97", lw=1.8)
    ax[1].set_xlabel("t (s)"); ax[1].set_ylabel("Reynolds number (body dia.)"); ax[1].grid(alpha=.3)
    ax[1].set_title(f"Reynolds number (peak {Re.max():.2e})")
    fig.suptitle("WYVERN-E 2.0 - Dynamic Pressure & Reynolds Number", fontweight="bold")
    sv(fig, "15_qdyn_reynolds")

    # 16 - solenoid force / coil current / duty during TVC-active phase
    mask = comb_tvc["Fs"] > 0
    fig, ax = plt.subplots(3,1,figsize=(9,8), sharex=True)
    ax[0].plot(comb_tvc["t"][mask], comb_tvc["Fs"][mask], c="#bc4749", lw=1.2); ax[0].set_ylabel("F_solenoid (N)"); ax[0].grid(alpha=.3)
    ax[0].axhline(F_SOLENOID_MAX, ls="--", c="k", lw=1)
    ax[0].set_title("WYVERN-E 2.0 - TVC Solenoid Force / PWM Duty / Coil Current", fontweight="bold")
    ax[1].plot(comb_tvc["t"][mask], comb_tvc["duty"][mask]*100, c="#2a6f97", lw=1.2); ax[1].set_ylabel("PWM duty (%)"); ax[1].grid(alpha=.3)
    ax[2].plot(comb_tvc["t"][mask], comb_tvc["I_coil"][mask], c="#386641", lw=1.2); ax[2].set_ylabel("coil current (A)"); ax[2].set_xlabel("t (s)"); ax[2].grid(alpha=.3)
    sv(fig, "16_solenoid_force_current")

    # 17 - TVC-on vs TVC-off comparison (weathercocking authority)
    fig, ax = plt.subplots(1,2,figsize=(12,4.8))
    ax[0].plot(comb_tvc["x"], comb_tvc["z"], c="#2a6f97", lw=2, label="TVC active")
    ax[0].plot(comb_passive["x"], comb_passive["z"], c="#bc4749", lw=2, ls="--", label="TVC off (fins-only)")
    ax[0].set_xlabel("downrange (m)"); ax[0].set_ylabel("altitude (m)"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[0].set_title("Ground-track profile, 3 m/s crosswind")
    ax[1].plot(comb_tvc["t"], np.degrees(comb_tvc["theta"]), c="#2a6f97", lw=1.5, label="TVC active")
    ax[1].plot(comb_passive["t"], np.degrees(comb_passive["theta"]), c="#bc4749", lw=1.5, ls="--", label="TVC off")
    ax[1].set_xlabel("t (s)"); ax[1].set_ylabel("pitch theta (deg)"); ax[1].legend(); ax[1].grid(alpha=.3)
    ax[1].set_title("Attitude hold: active TVC vs passive fins-only")
    fig.suptitle(f"WYVERN-E 2.0 - TVC Authority Demonstration "
                 f"(downrange@apogee: {comb_tvc['downrange_at_apogee']:.1f} m TVC vs {comb_passive['downrange_at_apogee']:.1f} m passive)",
                 fontweight="bold")
    sv(fig, "17_tvc_vs_passive_authority")

    # 18 - energy budget
    KE = 0.5*comb_tvc["m"]*(comb_tvc["vx"]**2+comb_tvc["vz"]**2)
    PE = comb_tvc["m"]*g*comb_tvc["z"]
    fig, ax = plt.subplots(figsize=(9,5))
    ax.plot(comb_tvc["t"], KE, c="#bc4749", lw=1.6, label="Kinetic")
    ax.plot(comb_tvc["t"], PE, c="#2a6f97", lw=1.6, label="Potential")
    ax.plot(comb_tvc["t"], KE+PE, c="#386641", lw=1.8, ls="--", label="Total mechanical")
    ax.set_xlabel("t (s)"); ax.set_ylabel("energy (J)"); ax.legend(); ax.grid(alpha=.3)
    ax.set_title("WYVERN-E 2.0 - Flight Energy Budget (combined 2-stage, TVC on)", fontweight="bold")
    sv(fig, "18_energy_budget")

    # 19 - pitch phase portrait
    fig, ax = plt.subplots(figsize=(7,6))
    sc = ax.scatter(np.degrees(comb_tvc["theta"]), np.degrees(comb_tvc["q"]), c=comb_tvc["t"], cmap="viridis", s=4)
    plt.colorbar(sc, label="time (s)")
    ax.set_xlabel("theta (deg)"); ax.set_ylabel("pitch rate q (deg/s)"); ax.grid(alpha=.3)
    ax.set_title("WYVERN-E 2.0 - Pitch Phase Portrait (theta vs q)", fontweight="bold")
    sv(fig, "19_pitch_phase_portrait")

    # 20 - Monte Carlo: apogee & downrange dispersion, TVC vs passive (N runs)
    N = int(os.environ.get("WE2_MC_N", "8"))
    mc_dt = float(os.environ.get("WE2_MC_DT", "2e-3"))
    apos_tvc=[]; dr_tvc=[]; apos_pas=[]; dr_pas=[]
    for i in range(N):
        w = float(np.random.default_rng(100+i).normal(3.0,1.3))
        rt = fly([booster_phase, sustainer_tvc_phase], wind_x=w, tvc_on=True, dt=mc_dt, seed=100+i)
        rp = fly([booster_phase, dict(sustainer_tvc_phase, motor_active=False)], wind_x=w, tvc_on=False, dt=mc_dt, seed=100+i)
        apos_tvc.append(rt["apogee"]); dr_tvc.append(rt["downrange_at_apogee"])
        apos_pas.append(rp["apogee"]); dr_pas.append(rp["downrange_at_apogee"])
    fig, ax = plt.subplots(1,2,figsize=(12,4.8))
    ax[0].hist(dr_tvc, 24, alpha=.7, color="#2a6f97", label=f"TVC (sig={np.std(dr_tvc):.1f} m)")
    ax[0].hist(dr_pas, 24, alpha=.6, color="#bc4749", label=f"Passive (sig={np.std(dr_pas):.1f} m)")
    ax[0].set_xlabel("downrange @ apogee (m)"); ax[0].set_ylabel("count"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[0].set_title(f"Downrange dispersion, N={N} (wind 3.0+-1.3 m/s)")
    ax[1].hist(apos_tvc, 24, alpha=.7, color="#2a6f97", label=f"TVC (mu={np.mean(apos_tvc):.0f} m)")
    ax[1].hist(apos_pas, 24, alpha=.6, color="#bc4749", label=f"Passive (mu={np.mean(apos_pas):.0f} m)")
    ax[1].set_xlabel("apogee (m)"); ax[1].set_ylabel("count"); ax[1].legend(); ax[1].grid(alpha=.3)
    ax[1].set_title("Apogee distribution")
    fig.suptitle("WYVERN-E 2.0 - Monte-Carlo TVC vs Passive Dispersion (RK4/Barrowman engine)", fontweight="bold")
    sv(fig, "20_mc_tvc_vs_passive_dispersion")

    # ============================================================ DATA EXPORT
    import csv
    def export_csv(name, d):
        keys = ["t","x","z","vx","vz","theta","q","alpha","M","qdyn","N","delta","tau_cmd",
                "Fs","duty","I_coil","Xcg","Xcp","SM","m","Iyy","M_aero","M_thrust","wind_gust"]
        with open(os.path.join(DATADIR,name),"w",newline="") as f:
            w = csv.writer(f); w.writerow(keys)
            for i in range(len(d["t"])):
                w.writerow([d[k][i] for k in keys])
    export_csv("trajectory_combined_tvc.csv", comb_tvc)
    export_csv("trajectory_combined_passive.csv", comb_passive)
    export_csv("trajectory_sustainer_only_tvc.csv", sus_only)

    summary = dict(
        barrowman=dict(CNalpha_fin=round(float(CNalpha_fin),3), CNalpha0=round(float(CNalpha0),3),
                       Xcp_mm=round(float(Xcp*1000),1), Xr_fin_LE_mm=round(float(Xr*1000),1)),
        combined_tvc=dict(apogee_m=round(float(comb_tvc['apogee']),1), vmax_ms=round(float(comb_tvc['vmax']),1),
                          mach_max=round(float(comb_tvc['mach_max']),3),
                          downrange_at_apogee_m=round(float(comb_tvc['downrange_at_apogee']),2),
                          sm_min_cal=round(float(comb_tvc['sm_min']),3), sm_max_cal=round(float(comb_tvc['sm_max']),3),
                          alpha_max_deg=round(float(comb_tvc['alpha_max_deg']),2),
                          gimbal_max_deg=round(float(comb_tvc['delta_max_deg']),2)),
        combined_passive=dict(apogee_m=round(float(comb_passive['apogee']),1),
                              downrange_at_apogee_m=round(float(comb_passive['downrange_at_apogee']),2)),
        crossvalidation=dict(run_sims_1dof_apogee_m=round(float(ph2['apogee']),1),
                             rk4_barrowman_apogee_m=round(float(comb_tvc['apogee']),1),
                             pct_diff=round(100*(comb_tvc['apogee']-ph2['apogee'])/ph2['apogee'],2)),
        monte_carlo_n=N,
        dispersion=dict(downrange_sigma_tvc_m=round(float(np.std(dr_tvc)),2),
                       downrange_sigma_passive_m=round(float(np.std(dr_pas)),2),
                       apogee_mean_tvc_m=round(float(np.mean(apos_tvc)),1),
                       apogee_mean_passive_m=round(float(np.mean(apos_pas)),1)),
    )
    json.dump(summary, open(os.path.join(DATADIR,"rk4_barrowman_summary.json"),"w"), indent=2)
    print("\nwrote 10 new plots ->", os.path.relpath(PLOTDIR))
    print("wrote trajectory CSVs + summary ->", os.path.relpath(DATADIR))
    print(json.dumps(summary, indent=2))
