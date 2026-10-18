"""
Guidance & engagement Monte Carlo -- XRIM-117 WYVERN-E 70mm PTD
=================================================================
3-D point-mass interceptor with true proportional navigation (N' = 3-5)
against a slow aerial target (Group-1 UAS surrogate, 8-18 m/s, optional
evasive weave). The PTD payload is a capture/proximity demonstrator, so
"kill" is defined as miss distance < capture radius.

Lateral acceleration authority is the physical limit of the airframe:
  a_lat_max = min( q * A_ref * CN_max / m ,  TVC: F_side/m at low q )
with a first-order autopilot lag tau = 0.10 s (servo + airframe).

Outputs: miss-distance distribution, Pk vs capture radius, engagement
envelope (Pk over launch range x target altitude grid), sample 3-D paths.
"""

import numpy as np
from . import common as cm
from . import aero

RNG = np.random.default_rng(117)

TAU_AP   = 0.10        # autopilot + servo lag [s]
N_PN     = 4.0         # PN navigation constant
CN_MAX   = aero.cn_alpha_total() * np.deg2rad(10.0)   # trim limit ~10 deg AoA
SEEKER_SIGMA = np.deg2rad(0.5)   # LOS angle noise (1-sigma per axis)
SEEKER_HZ    = 20.0    # seeker / track-loop update rate
R_BLIND      = 8.0     # terminal blind range -- last metres flown open-loop [m]
GUST_SIGMA   = 0.6     # lateral gust acceleration disturbance (1-sigma) [m/s^2]
T_GUIDE_ON   = 0.8     # guidance active after rail clear + tip-over [s]


def _alat_max(V, h, m):
    T, P, rho, a = cm.atmosphere(h)
    q = 0.5 * rho * V ** 2
    a_aero = q * cm.A_REF * CN_MAX / m
    a_tvc = cm.F_TVC_SIDE / m          # available while sustainer burns
    return max(a_aero, a_tvc)


def target_state(t, kind="crossing", R0=400.0, h0=120.0, Vt=12.0,
                 weave_g=0.3, weave_T=4.0, phase=0.0):
    """Returns target position & velocity at time t (ENU)."""
    if kind == "crossing":
        p0 = np.array([R0, 0.0, h0])
        v = np.array([0.0, Vt, 0.0])
        p = p0 + v * t
    elif kind == "inbound":
        p0 = np.array([R0, 0.0, h0])
        v = np.array([-Vt, 0.0, 0.0])
        p = p0 + v * t
    elif kind == "hover":
        p0 = np.array([R0, 0.0, h0])
        v = np.zeros(3)
        p = p0
    else:  # weave
        p0 = np.array([R0, 0.0, h0])
        v_base = np.array([0.0, Vt, 0.0])
        a_w = weave_g * cm.G0
        om = 2 * np.pi / weave_T
        p = p0 + v_base * t + np.array([a_w / om**2 * (1 - np.cos(om * t + phase)), 0, 0])
        v = v_base + np.array([a_w / om * np.sin(om * t + phase), 0, 0])
    return p, v


def fly_engagement(kind="crossing", R0=400.0, h0=120.0, Vt=12.0,
                   seeker_noise=True, heading_err_deg=0.0, t_max=30.0,
                   dt=0.005, record=False, phase=0.0):
    """Boost vertically off rail, tip toward predicted intercept, PN terminal.
    Returns miss distance [m] (and history if record)."""
    # interceptor state
    p = np.array([0.0, 0.0, 0.1])
    v = np.array([0.0, 0.0, 0.5])
    a_cmd_f = np.zeros(3)            # filtered (lagged) command
    t = 0.0
    miss = np.inf
    hist = {k: [] for k in ("t", "px", "py", "pz", "tx", "ty", "tz", "V", "alat")}
    closing = False
    seeker_frame = -1
    noise_held = np.zeros(2)
    gust = np.zeros(3)
    los_meas_prev = None
    omega_filt = np.zeros(3)
    TAU_TRACK = 0.20          # LOS-rate track filter time constant [s]
    while t < t_max:
        m, F, stage = mass_thrust_local(t)
        pt, vt = target_state(t, kind, R0, h0, Vt, phase=phase)
        r_rel = pt - p
        rng = np.linalg.norm(r_rel)
        # sub-step closest approach (linear interpolation within dt)
        v_rel_now = vt - v
        vr2 = np.dot(v_rel_now, v_rel_now)
        if vr2 > 1e-9:
            t_star = np.clip(-np.dot(r_rel, v_rel_now) / vr2, 0.0, dt)
            rng_star = np.linalg.norm(r_rel + v_rel_now * t_star)
        else:
            rng_star = rng
        miss = min(miss, rng, rng_star)
        if rng < 0.05 or (closing and np.dot(r_rel, vt - v) > 0 and rng < 5.0):
            break
        if rng < 50.0:
            closing = True
        V = np.linalg.norm(v) + 1e-9
        u_v = v / V
        # --- guidance ---
        if t < T_GUIDE_ON:
            a_cmd = np.zeros(3)      # rail + vertical boost
        elif rng < R_BLIND:
            a_cmd = a_cmd_f          # seeker blind -- hold last command
        else:
            los = r_rel / rng
            if seeker_noise:
                # 20 Hz track loop: noisy LOS measurement held between frames;
                # LOS rate ESTIMATED by differencing successive measurements
                # through a first-order track filter (this is where seeker
                # noise actually corrupts PN). Glint-like growth inside 30 m.
                frame = int(t * SEEKER_HZ)
                if frame != seeker_frame:
                    seeker_frame = frame
                    glint = 1.0 + 3.0 * max(0.0, (30.0 - rng) / 30.0)
                    noise_held = RNG.normal(0, SEEKER_SIGMA * glint, 2)
                    e1 = np.cross(los, [0, 0, 1.0]); e1 /= np.linalg.norm(e1) + 1e-9
                    e2 = np.cross(los, e1)
                    los_meas = los + noise_held[0] * e1 + noise_held[1] * e2
                    los_meas /= np.linalg.norm(los_meas)
                    if los_meas_prev is not None:
                        omega_raw = np.cross(los_meas_prev, los_meas) * SEEKER_HZ
                        k = min((1.0 / SEEKER_HZ) / TAU_TRACK, 1.0)
                        omega_filt = omega_filt + (omega_raw - omega_filt) * k
                    los_meas_prev = los_meas
                los = los_meas_prev if los_meas_prev is not None else los
            v_rel = vt - v
            vc = -np.dot(v_rel, los)                  # closing speed
            lim = _alat_max(V, p[2], m)
            # midcourse: lead-pursuit tip-over toward predicted intercept point
            t_go = rng / max(vc, 15.0)
            aim = (pt + vt * min(t_go, 8.0)) - p
            u_aim = aim / (np.linalg.norm(aim) + 1e-9)
            angle_err = np.arccos(np.clip(np.dot(u_v, u_aim), -1, 1))
            if angle_err > np.deg2rad(15.0):
                e_perp = u_aim - np.dot(u_aim, u_v) * u_v
                e_perp /= np.linalg.norm(e_perp) + 1e-9
                a_cmd = e_perp * min(lim, 3.0 * V * angle_err)  # omega_cmd ~ 3*err rad/s
                a_cmd += np.array([0, 0, cm.G0])
            else:
                if seeker_noise:
                    omega = omega_filt                      # estimated LOS rate
                else:
                    omega = np.cross(r_rel, v_rel) / rng ** 2  # geometric truth
                a_cmd = N_PN * vc * np.cross(omega, u_v)   # true PN terminal
                a_cmd += np.array([0, 0, cm.G0])           # gravity compensation
            a_perp = a_cmd - np.dot(a_cmd, u_v) * u_v
            if np.linalg.norm(a_perp) > lim:
                a_perp *= lim / np.linalg.norm(a_perp)
            a_cmd = a_perp
        # autopilot lag
        a_cmd_f += (a_cmd - a_cmd_f) * dt / TAU_AP
        # --- dynamics ---
        T_, P_, rho, a_s = cm.atmosphere(max(p[2], 0.0))
        Mn = V / a_s
        q = 0.5 * rho * V ** 2
        # drag: zero-lift + induced from commanded lateral g
        cn_req = np.linalg.norm(a_cmd_f) * m / max(q * cm.A_REF, 1e-6)
        alpha_eq = cn_req / aero.cn_alpha_total()
        cd = float(aero.cd0(Mn, max(p[2], 0.0))) + cn_req * np.sin(min(alpha_eq, 0.3))
        D = q * cm.A_REF * cd
        if t < T_GUIDE_ON:
            u_thrust = np.array([0, 0, 1.0])
            # initial heading error (rail mis-aim)
            he = np.deg2rad(heading_err_deg)
            u_thrust = np.array([np.sin(he), 0, np.cos(he)])
        else:
            u_thrust = u_v
        # gust disturbance: first-order Markov lateral acceleration
        if seeker_noise:
            gust += (-gust / 1.5 + RNG.normal(0, GUST_SIGMA, 3) / np.sqrt(dt)) * dt
        acc = (F * u_thrust - D * u_v) / m + np.array([0, 0, -cm.G0]) + a_cmd_f + gust
        v = v + acc * dt
        p = p + v * dt
        t += dt
        if p[2] < 0:
            break
        if record and int(t / dt) % 10 == 0:
            for k, val in zip(("t","px","py","pz","tx","ty","tz","V","alat"),
                              (t, *p, *pt, V, np.linalg.norm(a_cmd_f) / cm.G0)):
                hist[k].append(val)
    if record:
        return miss, {k: np.array(val) for k, val in hist.items()}
    return miss


def mass_thrust_local(t):
    from .trajectory import mass_thrust
    return mass_thrust(t)


# ----------------------------------------------------------------------------
# Monte Carlo campaigns
# ----------------------------------------------------------------------------

def monte_carlo(n=400, kind="crossing", R0=400.0, h0=120.0, Vt=12.0):
    misses = np.empty(n)
    for i in range(n):
        he = RNG.normal(0, 1.0)                 # rail aim error [deg]
        vt = Vt * (1 + RNG.normal(0, 0.10))
        r0 = R0 * (1 + RNG.normal(0, 0.05))
        ph = RNG.uniform(0, 2 * np.pi)
        misses[i] = fly_engagement(kind, r0, h0, vt, heading_err_deg=he, phase=ph)
    return misses


def pk_vs_radius(misses, radii):
    return np.array([(misses <= r).mean() for r in radii])


def engagement_envelope(ranges, alts, n=60, kind="crossing", Vt=12.0, r_capture=2.0):
    pk = np.zeros((len(alts), len(ranges)))
    for i, h in enumerate(alts):
        for j, R in enumerate(ranges):
            m = np.array([fly_engagement(kind, R * (1 + RNG.normal(0, .03)), h,
                                         Vt * (1 + RNG.normal(0, .1)),
                                         heading_err_deg=RNG.normal(0, 1.0),
                                         phase=RNG.uniform(0, 6.28))
                          for _ in range(n)])
            pk[i, j] = (m <= r_capture).mean()
    return pk
