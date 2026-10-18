#!/usr/bin/env python3
"""U.S. Standard Atmosphere 1976 (ISA) model for WYVERN-E 2.0.

Piecewise geopotential-layer model (0-86 km) returning the full thermodynamic
state plus derived transport/aero properties at any altitude. Used by
`expand_flight.py` to enrich the trajectory with a "crap ton" of atmospheric
data and by the CFD/wind-tunnel Reynolds-matching work.

References: U.S. Standard Atmosphere 1976 (NOAA/NASA/USAF); Sutherland (1893)
viscosity law; ideal-gas + perfect-gas acoustics.
"""
import numpy as np

# --- physical constants ---
g0   = 9.80665      # m/s^2  standard gravity
R    = 287.05287    # J/kg/K specific gas constant for air
gamma= 1.4          # ratio of specific heats
P0   = 101325.0     # Pa     sea-level pressure
T0   = 288.15       # K      sea-level temperature
RHO0 = 1.225        # kg/m^3 sea-level density
Re_E = 6356766.0    # m      Earth radius for geopotential conversion
# Sutherland's law constants (air)
S_mu = 1.458e-6     # kg/(m s sqrt(K))
S_T  = 110.4        # K

# ISA base layers: (base geopotential alt h_b [m], base temp T_b [K], lapse L_b [K/m])
LAYERS = [
    (    0.0, 288.15, -0.0065),
    (11000.0, 216.65,  0.0   ),
    (20000.0, 216.65,  0.0010),
    (32000.0, 228.65,  0.0028),
    (47000.0, 270.65,  0.0   ),
    (51000.0, 270.65, -0.0028),
    (71000.0, 214.65, -0.0020),
]

def _base_pressures():
    """Precompute base pressure at the bottom of each layer."""
    pb = [P0]
    for i in range(len(LAYERS)-1):
        h_b, T_b, L = LAYERS[i]
        h_t = LAYERS[i+1][0]
        if abs(L) < 1e-12:
            p = pb[i]*np.exp(-g0*(h_t-h_b)/(R*T_b))
        else:
            T_t = T_b + L*(h_t-h_b)
            p = pb[i]*(T_t/T_b)**(-g0/(R*L))
        pb.append(p)
    return pb
_PB = _base_pressures()

def geopotential(z_geometric):
    """Geometric altitude z [m] -> geopotential altitude h [m]."""
    return Re_E*z_geometric/(Re_E+z_geometric)

def viscosity(T):
    """Dynamic viscosity mu [Pa s] via Sutherland's law."""
    return S_mu*T**1.5/(T+S_T)

def state(z):
    """Full atmospheric state at geometric altitude z [m].

    Returns dict with T,p,rho,a,mu,nu,theta,delta,sigma and altitude info.
    """
    h = geopotential(z)
    h = min(max(h, 0.0), 86000.0)
    # find layer
    i = 0
    for k in range(len(LAYERS)):
        if h >= LAYERS[k][0]:
            i = k
    h_b, T_b, L = LAYERS[i]
    T = T_b + L*(h-h_b)
    if abs(L) < 1e-12:
        p = _PB[i]*np.exp(-g0*(h-h_b)/(R*T_b))
    else:
        p = _PB[i]*(T/T_b)**(-g0/(R*L))
    rho = p/(R*T)
    a   = np.sqrt(gamma*R*T)
    mu  = viscosity(T)
    nu  = mu/rho
    return dict(z=z, h=h, T=T, T_C=T-273.15, p=p, rho=rho, a=a, mu=mu, nu=nu,
                theta=T/T0, delta=p/P0, sigma=rho/RHO0,
                p_atm=p/101325.0, p_kPa=p/1000.0)

def column(name, zs):
    return np.array([state(z)[name] for z in zs])

if __name__ == "__main__":
    # quick sanity print: classic ISA checkpoints
    for z in (0, 1000, 5000, 11000, 20000):
        s = state(z)
        print(f"z={z:6d} m  T={s['T']:7.2f}K  p={s['p']:9.1f}Pa  "
              f"rho={s['rho']:.4f}  a={s['a']:6.2f}  nu={s['nu']:.3e}")
