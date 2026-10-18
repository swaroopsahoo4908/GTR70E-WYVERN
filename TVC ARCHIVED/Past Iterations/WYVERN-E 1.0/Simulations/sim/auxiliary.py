"""
Auxiliary simulations -- thermal, landing dispersion, Monte Carlo sensitivity
==============================================================================
1. Aerothermal: stagnation & recovery temperature vs Mach, flat-plate
   convective film coefficient and skin temperature rise over the flight.
2. Landing dispersion: 3-DOF Monte Carlo over wind, thrust misalignment,
   CD/impulse/mass tolerances -> drift ellipse & CEP under 24" chute.
3. Sensitivity: one-at-a-time + Monte Carlo on apogee / max-q drivers.
"""

import numpy as np
from . import common as cm
from . import aero
from . import trajectory as tj

RNG = np.random.default_rng(2026)
R_RECOVERY = 0.89          # turbulent recovery factor Pr^(1/3)


# ----------------------------------------------------------------------------
# 1. Aerothermal
# ----------------------------------------------------------------------------

def stagnation_temp(M, h=100.0):
    T, *_ = cm.atmosphere(h)
    return T * (1 + (cm.GAMMA - 1) / 2 * np.asarray(M) ** 2)


def recovery_temp(M, h=100.0):
    T, *_ = cm.atmosphere(h)
    return T * (1 + R_RECOVERY * (cm.GAMMA - 1) / 2 * np.asarray(M) ** 2)


def film_coefficient(V, h, x=0.5):
    """Turbulent flat-plate: Nu_x = 0.0296 Re_x^0.8 Pr^(1/3)."""
    T, P, rho, a = cm.atmosphere(h)
    mu = cm.viscosity(T)
    k_air = 0.0241 * (T / 273.15) ** 0.9       # W/m K approx
    Re_x = rho * np.maximum(V, 1.0) * x / mu
    Nu = 0.0296 * Re_x ** 0.8 * 0.7 ** (1 / 3)
    return Nu * k_air / x


def skin_temp_history(traj, x=0.5, t_skin=2.4e-3,
                      rho_skin=1300.0, cp_skin=1200.0):
    """Lumped-capacitance PETG-CF skin node driven by recovery temperature."""
    t, V, z, M = traj["t"], traj["V"], traj["z"], traj["M"]
    Tw = np.empty_like(t)
    Tw[0] = 288.15
    C = rho_skin * cp_skin * t_skin           # J/m^2 K
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        Tr = recovery_temp(M[i], z[i])
        hc = film_coefficient(V[i], z[i], x)
        Tw[i] = Tw[i - 1] + hc * (Tr - Tw[i - 1]) / C * dt
    return Tw


# ----------------------------------------------------------------------------
# 2. Landing dispersion Monte Carlo
# ----------------------------------------------------------------------------

def dispersion_mc(n=200, elev_deg=88.0, wind_mean=4.0):
    """Returns (n,2) landing coordinates [m] and apogee array.
    Boost/coast integrated numerically (stop at apogee); chute descent treated
    analytically -- canopy descends at terminal velocity and rides the wind."""
    pts, apo = np.empty((n, 2)), np.empty(n)
    for i in range(n):
        wdir = RNG.uniform(0, 2 * np.pi)
        wmag = max(RNG.normal(wind_mean, 1.5), 0.0)
        wind = wmag * np.array([np.sin(wdir), np.cos(wdir), 0.0])
        m_sc = 1 + RNG.normal(0, 0.03)
        out = tj.point_mass_3dof(
            elev_deg=elev_deg + RNG.normal(0, 0.5),
            azim_deg=RNG.uniform(0, 360),
            wind=wind,
            cd_scale=1 + RNG.normal(0, 0.10),
            thrust_scale=1 + RNG.normal(0, 0.05),
            m_scale=m_sc,
            dt=0.01, motors="booster_only", stop_at_apogee=True,
        )
        m_desc = (cm.M_LIFTOFF - cm.M_PROP_BOOST - cm.M_BOOSTER_DRY) * m_sc
        _, _, rho, _ = cm.atmosphere(out["apogee"] / 2)
        v_term = np.sqrt(2 * m_desc * cm.G0 / (rho * cm.CD_CHUTE * cm.A_CHUTE))
        t_desc = out["apogee"] / v_term
        pts[i] = (out["x"][-1] + wind[0] * t_desc, out["y"][-1] + wind[1] * t_desc)
        apo[i] = out["apogee"]
    return pts, apo


def cep(pts):
    r = np.linalg.norm(pts - pts.mean(axis=0), axis=1)
    return np.percentile(r, 50)


# ----------------------------------------------------------------------------
# 3. Sensitivity (tornado + MC)
# ----------------------------------------------------------------------------

def tornado_apogee():
    kw0 = dict(dt=0.01, stop_at_apogee=True)
    base = tj.point_mass_3dof(**kw0)["apogee"]
    rows = []
    for name, kw_lo, kw_hi in [
        ("CD +/-10%",      dict(cd_scale=1.10), dict(cd_scale=0.90)),
        ("Impulse +/-5%",  dict(thrust_scale=0.95), dict(thrust_scale=1.05)),
        ("Mass +/-3%",     dict(m_scale=1.03), dict(m_scale=0.97)),
        ("Rail elev 85 deg", dict(elev_deg=85.0), dict(elev_deg=90.0)),
    ]:
        lo = tj.point_mass_3dof(**kw0, **kw_lo)["apogee"]
        hi = tj.point_mass_3dof(**kw0, **kw_hi)["apogee"]
        rows.append((name, lo - base, hi - base))
    return base, rows


def mc_apogee(n=150):
    out = np.empty((n, 3))   # apogee, vmax, qmax
    for i in range(n):
        r = tj.point_mass_3dof(
            dt=0.01, stop_at_apogee=True,
            cd_scale=1 + RNG.normal(0, 0.10),
            thrust_scale=1 + RNG.normal(0, 0.05),
            m_scale=1 + RNG.normal(0, 0.03),
        )
        out[i] = (r["apogee"], r["v_max"], r["q_max"])
    return out
