"""
XRIM-117 WYVERN-E (PDR-002, 70mm PTD) -- common physical models & vehicle database
====================================================================================
All values sourced from vault documents:
  - WYVERN_Simulator.md  (Full Mathematical Derivations)
  - XRIM117_PTD_PDR002_RevA_70mm.docx
  - WYVERN_Engineering_Analysis.pdf

Units: SI throughout (m, kg, s, N, Pa, K) unless suffixed.
"""

import numpy as np

# ----------------------------------------------------------------------------
# 1. ISA ATMOSPHERE (troposphere model, h < 11 km)
# ----------------------------------------------------------------------------
G0      = 9.80665          # m/s^2
R_AIR   = 287.05           # J/(kg K)
GAMMA   = 1.4
T0_ISA  = 288.15           # K
P0_ISA  = 101325.0         # Pa
LAPSE   = 0.0065           # K/m


def atmosphere(h):
    """ISA troposphere. Returns (T [K], P [Pa], rho [kg/m^3], a [m/s])."""
    h = np.clip(h, 0.0, 11000.0)
    T = T0_ISA - LAPSE * h
    P = P0_ISA * (T / T0_ISA) ** (G0 / (LAPSE * R_AIR))
    rho = P / (R_AIR * T)
    a = np.sqrt(GAMMA * R_AIR * T)
    return T, P, rho, a


def viscosity(T):
    """Sutherland's law, mu [Pa s]."""
    return 1.458e-6 * T ** 1.5 / (T + 110.4)


# ----------------------------------------------------------------------------
# 2. VEHICLE GEOMETRY  (PDR-002 Rev A)
# ----------------------------------------------------------------------------
D_REF      = 0.070                      # body diameter [m]
R_BODY     = D_REF / 2.0
A_REF      = np.pi * R_BODY ** 2        # 3.848e-3 m^2
L_TOTAL    = 1.170                      # overall length [m]
L_NOSE     = 0.234                      # Von Karman ogive nose [m]
FINENESS   = L_TOTAL / D_REF            # 16.71
S_WET_RATIO = 3.5                       # wetted area / A_ref multiplier (body+fins)

# Fin ring geometry  {root chord, tip chord, semispan, x leading edge @ root}
FIN_RING_1 = dict(cr=0.093, ct=0.047, b=0.070, x_le=0.820, n=4, tc=0.04)  # aft stabilizers
FIN_RING_2 = dict(cr=0.047, ct=0.023, b=0.035, x_le=0.420, n=4, tc=0.04)  # mid canards (all-moving)

# ----------------------------------------------------------------------------
# 3. MASS PROPERTIES
# ----------------------------------------------------------------------------
M_LIFTOFF      = 0.640      # kg, all-up
M_BOOSTER_DRY  = 0.062      # kg, jettisoned hardware (casing, interstage, fins)
M_PROP_BOOST   = 0.038      # kg, F39-6T propellant
M_PROP_SUST    = 0.075      # kg, G76-10G propellant (PDR estimate)
M_SUSTAINER_BO = M_LIFTOFF - M_PROP_BOOST - M_BOOSTER_DRY - M_PROP_SUST  # 0.465 kg

XCG_ALLUP   = 0.6084        # m from nose tip (motor full)
XCG_BURNOUT = 0.5616        # m from nose tip (empty)
I_PITCH     = 0.0369        # kg m^2  (PDR cylinder approximation, all-up)

# ----------------------------------------------------------------------------
# 4. MOTOR THRUST CURVES (synthesized to match PDR integrals)
#    F39-6T : I=126 N s, Fpk=58 N, Favg=42.6 N, tb=3.0 s   (booster)
#    G76-10G: I=730 N s, Fpk=95 N, Favg=73.4 N, tb=10.0 s  (sustainer)
#    Regressive APCP profiles: fast ramp, plateau, linear regression, tail-off.
# ----------------------------------------------------------------------------

def _regressive_curve(t, t_burn, f_peak, impulse, t_ramp):
    """Piecewise thrust: linear ramp to peak, then linear regression to f_end,
    with f_end chosen so the integral equals the published total impulse."""
    # integral = 0.5*f_peak*t_ramp + 0.5*(f_peak+f_end)*(t_burn-t_ramp)
    f_end = 2.0 * (impulse - 0.5 * f_peak * t_ramp) / (t_burn - t_ramp) - f_peak
    t = np.asarray(t, dtype=float)
    f = np.where(
        t < t_ramp,
        f_peak * t / t_ramp,
        f_peak + (f_end - f_peak) * (t - t_ramp) / (t_burn - t_ramp),
    )
    return np.where((t < 0) | (t > t_burn), 0.0, f)


def thrust_booster(t):
    """Cesaroni F39-6T (PDR values)."""
    return _regressive_curve(t, t_burn=3.0, f_peak=58.0, impulse=126.0, t_ramp=0.15)


def thrust_sustainer(t):
    """AeroTech G76-10G long-burn (PDR values)."""
    return _regressive_curve(t, t_burn=10.0, f_peak=95.0, impulse=730.0, t_ramp=0.30)


T_BURN_BOOST   = 3.0
T_BURN_SUST    = 10.0
T_SEP          = 3.2        # booster separation
T_IGN_SUST     = 3.5        # sustainer ignition (interstage coast)

# ----------------------------------------------------------------------------
# 5. STRUCTURE / MATERIALS  (PETG-CF over phenolic liner)
# ----------------------------------------------------------------------------
E_PETG_CF   = 3.8e9        # Pa
E_PHENOLIC  = 7.5e9        # Pa
G_PETG_CF   = 1.4e9        # Pa (shear, FDM XY)
SIGMA_ALLOW_PETG = 48e6    # Pa (XY allowable)
NU_PETG     = 0.35
T_WALL_PETG = 2.4e-3       # m
T_WALL_PHEN = 1.0e-3       # m
EI_COMPOSITE = 1887.0      # N m^2 (PDR corrected value)
FDM_KNOCKDOWN = 0.25       # shell buckling imperfection factor

# ----------------------------------------------------------------------------
# 6. RECOVERY
# ----------------------------------------------------------------------------
D_CHUTE   = 0.610          # m (24 in)
CD_CHUTE  = 1.5
A_CHUTE   = np.pi * (D_CHUTE / 2) ** 2

# ----------------------------------------------------------------------------
# 7. LAUNCH RAIL
# ----------------------------------------------------------------------------
L_RAIL = 1.83              # m (6 ft 1010 rail)

# ----------------------------------------------------------------------------
# 8. CONTROL / TVC AUTHORITY
# ----------------------------------------------------------------------------
F_TVC_SIDE   = 25.1        # N at 45 deg jetavane (20 deg effective plume deflection)
ARM_TVC      = 0.585       # m, nozzle exit to CG
DELTA_FIN_MAX = np.deg2rad(25.0)   # all-moving canard throw
SERVO_TAU    = 0.045       # s, first-order servo lag
SERVO_RATE   = np.deg2rad(60.0 / 0.09)  # rad/s slew
