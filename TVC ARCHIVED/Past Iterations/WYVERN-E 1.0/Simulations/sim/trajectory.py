"""
Trajectory module -- XRIM-117 WYVERN-E 70mm PTD
=================================================
Two integrators:

  1. point_mass_3dof : ENU point-mass with full drag polar, staging, recovery.
                       Used for performance envelope and dispersion Monte Carlo.
  2. pitch_plane_6dof: planar rigid-body (x, z, u, w, theta, q) with Barrowman
                       aerodynamic moments, pitch damping, rail constraint and
                       wind -- demonstrates static/dynamic stability off the rail.

Integration: RK4 fixed step, dt = 5 ms (boost) / 20 ms (descent).
"""

import numpy as np
from . import common as cm
from . import aero


# ----------------------------------------------------------------------------
# Mass & thrust schedule (two-stage)
# ----------------------------------------------------------------------------

def mass_thrust(t, motors="both"):
    """Returns (m [kg], F_thrust [N], stage_id).
    motors: "both" (full PDR stack) or "booster_only" (test-card flight,
    sustainer inert ballast retained)."""
    if motors == "booster_only":
        if t < cm.T_BURN_BOOST:
            frac = min(t / cm.T_BURN_BOOST, 1.0)
            return cm.M_LIFTOFF - cm.M_PROP_BOOST * frac, float(cm.thrust_booster(t)), 0
        m_ab = cm.M_LIFTOFF - cm.M_PROP_BOOST
        if t < cm.T_SEP:
            return m_ab, 0.0, 0
        return m_ab - cm.M_BOOSTER_DRY, 0.0, 1
    if t < cm.T_BURN_BOOST:
        frac = min(t / cm.T_BURN_BOOST, 1.0)
        m = cm.M_LIFTOFF - cm.M_PROP_BOOST * frac
        return m, float(cm.thrust_booster(t)), 0
    m_after_boost = cm.M_LIFTOFF - cm.M_PROP_BOOST
    if t < cm.T_SEP:
        return m_after_boost, 0.0, 0
    m_sep = m_after_boost - cm.M_BOOSTER_DRY
    if t < cm.T_IGN_SUST:
        return m_sep, 0.0, 1
    tb = t - cm.T_IGN_SUST
    if tb < cm.T_BURN_SUST:
        frac = tb / cm.T_BURN_SUST
        return m_sep - cm.M_PROP_SUST * frac, float(cm.thrust_sustainer(tb)), 1
    return m_sep - cm.M_PROP_SUST, 0.0, 1


# ----------------------------------------------------------------------------
# 1. Point-mass 3-DOF (ENU): state = [x, y, z, vx, vy, vz]
# ----------------------------------------------------------------------------

def _accel_pm(t, s, wind, chute_open):
    m, F, _ = mass_thrust(t)
    v_air = s[3:6] - wind
    V = np.linalg.norm(v_air) + 1e-9
    T, P, rho, a = cm.atmosphere(max(s[2], 0.0))
    M = V / a
    q = 0.5 * rho * V ** 2
    if chute_open:
        D = q * cm.CD_CHUTE * cm.A_CHUTE
        a_vec = -D * v_air / V / m + np.array([0, 0, -cm.G0])
        return np.concatenate([s[3:6], a_vec])
    cd = float(aero.cd0(M, max(s[2], 0.0)))
    D = q * cm.A_REF * cd
    # thrust along velocity vector (gravity-turn assumption)
    u_hat = s[3:6] / (np.linalg.norm(s[3:6]) + 1e-9)
    a_vec = (F * u_hat - D * v_air / V) / m + np.array([0, 0, -cm.G0])
    return np.concatenate([s[3:6], a_vec])


def point_mass_3dof(elev_deg=90.0, azim_deg=0.0, wind=np.zeros(3),
                    deploy_at_apogee=True, t_max=1500.0, dt=0.005,
                    cd_scale=1.0, thrust_scale=1.0, m_scale=1.0,
                    motors="both", stop_at_apogee=False):
    """Integrate full flight. Returns dict of time histories."""
    el, az = np.deg2rad(elev_deg), np.deg2rad(azim_deg)
    u0 = np.array([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)])
    s = np.zeros(6)
    s[2] = 0.1
    hist = {k: [] for k in ("t", "x", "y", "z", "V", "M", "q", "m", "F", "nx")}
    t, chute, apogee_t = 0.0, False, None
    global _scales
    _scales = (cd_scale, thrust_scale, m_scale)

    def deriv(t, s):
        m, F, _ = mass_thrust(t, motors)
        m *= m_scale
        F *= thrust_scale
        v_air = s[3:6] - wind
        V = np.linalg.norm(v_air) + 1e-9
        T_, P_, rho, a_ = cm.atmosphere(max(s[2], 0.0))
        q = 0.5 * rho * V ** 2
        if chute:
            D = q * cm.CD_CHUTE * cm.A_CHUTE
            acc = -D * v_air / V / m + np.array([0, 0, -cm.G0])
        else:
            Mn = V / a_
            cd = float(aero.cd0(Mn, max(s[2], 0.0))) * cd_scale
            D = q * cm.A_REF * cd
            vmag = np.linalg.norm(s[3:6])
            # on rail: constrain to rail direction
            if vmag < 1.0 and t < 1.0 and np.linalg.norm(s[:3] - np.array([0,0,0.1])) < cm.L_RAIL:
                u_hat = u0
            else:
                u_hat = s[3:6] / (vmag + 1e-9) if vmag > 1.0 else u0
            acc = (F * u_hat - D * v_air / V) / m + np.array([0, 0, -cm.G0])
            # rail constraint: project acceleration onto rail while on rail
            dist = np.linalg.norm(s[:3] - np.array([0, 0, 0.1]))
            if dist < cm.L_RAIL:
                acc = np.dot(acc, u0) * u0
                if np.dot(acc, u0) < 0 and vmag < 0.1:
                    acc = np.zeros(3)
        return np.concatenate([s[3:6], acc])

    while t < t_max:
        if s[2] < 0 and t > 5.0:
            break
        # RK4
        k1 = deriv(t, s)
        k2 = deriv(t + dt / 2, s + dt / 2 * k1)
        k3 = deriv(t + dt / 2, s + dt / 2 * k2)
        k4 = deriv(t + dt, s + dt * k3)
        s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        t += dt
        m, F, _ = mass_thrust(t, motors)
        v_air = s[3:6] - wind
        V = np.linalg.norm(v_air)
        T_, P_, rho, a_ = cm.atmosphere(max(s[2], 0.0))
        if apogee_t is None and s[5] < 0 and t > 2.0:
            apogee_t = t
            if stop_at_apogee:
                hist["t"].append(t); hist["x"].append(s[0]); hist["y"].append(s[1])
                hist["z"].append(s[2]); hist["V"].append(V); hist["M"].append(V / a_)
                hist["q"].append(0.5 * rho * V ** 2); hist["m"].append(m)
                hist["F"].append(F); hist["nx"].append(0.0)
                break
            if deploy_at_apogee:
                chute = True
                dt = 0.02
        for k, v in zip(("t", "x", "y", "z", "V", "M", "q", "m", "F"),
                        (t, s[0], s[1], s[2], V, V / a_, 0.5 * rho * V**2, m, F)):
            hist[k].append(v)
        hist["nx"].append((F - 0.5 * rho * V**2 * cm.A_REF * 0.04) / (m * cm.G0))
    out = {k: np.array(v) for k, v in hist.items()}
    out["apogee"] = out["z"].max()
    out["v_max"] = out["V"].max()
    out["M_max"] = out["M"].max()
    out["q_max"] = out["q"].max()
    out["t_apogee"] = apogee_t
    out["landing_xy"] = (out["x"][-1], out["y"][-1])
    return out


# ----------------------------------------------------------------------------
# 2. Pitch-plane rigid-body "6-DOF" : state = [x, z, u, w, theta, q_rate]
#    Body axes: u along longitudinal axis, w normal. Demonstrates weathercock
#    stability, rail departure transient, wind-induced AoA.
# ----------------------------------------------------------------------------

def pitch_plane_6dof(elev_deg=85.0, wind_x=3.0, t_max=18.0, dt=0.002):
    th0 = np.deg2rad(elev_deg)
    s = np.array([0.0, 0.1, 0.0, 0.0, th0, 0.0])   # x,z,u,w,theta,q
    hist = {k: [] for k in ("t", "x", "z", "V", "alpha_deg", "theta_deg",
                            "q_dps", "M", "sm")}
    t = 0.0
    bw = aero.barrowman()

    def deriv(t, s):
        """Standard pitch-plane convention: body x forward, body z DOWN.
        u = axial velocity, w = normal velocity (down +), theta = pitch above
        horizon, qr = pitch rate. World: x East, z Up."""
        x, z, u, w, th, qr = s
        m, F, stage = mass_thrust(t)
        burn_frac = 1.0 - (m - cm.M_SUSTAINER_BO) / (cm.M_LIFTOFF - cm.M_SUSTAINER_BO)
        xcg = cm.XCG_ALLUP + (cm.XCG_BURNOUT - cm.XCG_ALLUP) * np.clip(burn_frac, 0, 1)
        I = cm.I_PITCH * (m / cm.M_LIFTOFF)
        # inertial velocity (world frame, z up)
        vx = u * np.cos(th) + w * np.sin(th)
        vz = u * np.sin(th) - w * np.cos(th)
        # air-relative velocity, rotated into body frame
        vax, vaz_up = vx - wind_x, vz
        ua = vax * np.cos(th) + vaz_up * np.sin(th)
        wa = vax * np.sin(th) - vaz_up * np.cos(th)        # body z (down)
        V = np.hypot(ua, wa) + 1e-9
        alpha = np.arctan2(wa, ua)                          # + alpha = nose above velocity
        T_, P_, rho, a_ = cm.atmosphere(max(z, 0.0))
        Mn, qd = V / a_, 0.5 * rho * V ** 2
        on_rail = np.hypot(x, z - 0.1) < cm.L_RAIL
        ca, cn_ = aero.ca_cn_body(Mn, alpha, max(z, 0.0))
        Fx_b = F - qd * cm.A_REF * float(ca)
        Fz_b = -qd * cm.A_REF * float(cn_)                  # normal force opposes alpha
        # restoring moment (xcg < xn -> statically stable) + pitch damping
        Cm = -float(cn_) * (bw["xn"] - xcg) / cm.D_REF
        Cmq = aero.pitch_damping(xcg)
        Mom = qd * cm.A_REF * cm.D_REF * (Cm + Cmq * qr * cm.D_REF / (2 * V))
        ax_b = Fx_b / m - cm.G0 * np.sin(th) - qr * w
        az_b = Fz_b / m + cm.G0 * np.cos(th) + qr * u
        qdot = Mom / I
        if on_rail:
            az_b, qdot = 0.0, 0.0
            ax_b = max(ax_b, 0.0) if u < 0.5 else ax_b
        return np.array([vx, vz, ax_b, az_b, qr, qdot]), alpha, Mn, xcg

    while t < t_max and s[1] >= 0:
        d1, alpha, Mn, xcg = deriv(t, s)
        d2, *_ = deriv(t + dt / 2, s + dt / 2 * d1)
        d3, *_ = deriv(t + dt / 2, s + dt / 2 * d2)
        d4, *_ = deriv(t + dt, s + dt * d3)
        s = s + dt / 6 * (d1 + 2 * d2 + 2 * d3 + d4)
        t += dt
        V = np.hypot(s[2], s[3])
        for k, v in zip(("t", "x", "z", "V", "alpha_deg", "theta_deg", "q_dps", "M", "sm"),
                        (t, s[0], s[1], V, np.rad2deg(alpha), np.rad2deg(s[4]),
                         np.rad2deg(s[5]), Mn, (aero.neutral_point() - xcg) / cm.D_REF)):
            hist[k].append(v)
    return {k: np.array(v) for k, v in hist.items()}
