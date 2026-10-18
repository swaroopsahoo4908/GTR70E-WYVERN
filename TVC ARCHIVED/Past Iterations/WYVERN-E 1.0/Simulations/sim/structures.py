"""
FEA-lite structural module -- XRIM-117 WYVERN-E 70mm PTD
==========================================================
Closed-form structural verification replicating the PDR load cases plus a
discretized beam model:

  1. Axial g-load vs Euler column & Timoshenko shell buckling (FDM knockdown)
  2. Body bending under max-q maneuver (discretized Euler-Bernoulli beam)
  3. Fin root bending at full canard deflection
  4. Free-free first bending mode (modal)
  5. Fin flutter velocity (NACA TN-4197 / Martin's method)
  6. Servo hinge moment margin

All material properties from common.py (PETG-CF + phenolic liner layup).
"""

import numpy as np
from . import common as cm
from . import aero


# ----------------------------------------------------------------------------
# 1. Axial load cases
# ----------------------------------------------------------------------------

def axial_buckling(n_g=18.0, m=cm.M_LIFTOFF):
    F_axial = m * n_g * cm.G0
    # Euler column, K=0.7 both-ends-restrained
    L_eff = 0.7 * cm.L_TOTAL
    P_euler = np.pi ** 2 * cm.EI_COMPOSITE / L_eff ** 2
    # Timoshenko shell
    t = cm.T_WALL_PETG + cm.T_WALL_PHEN
    sigma_cr = 0.605 * cm.E_PETG_CF * t / (cm.R_BODY * np.sqrt(1 - cm.NU_PETG ** 2))
    sigma_cr *= cm.FDM_KNOCKDOWN
    A_wall = 2 * np.pi * cm.R_BODY * t
    P_shell = sigma_cr * A_wall
    return dict(F_axial=F_axial, P_euler=P_euler, SF_euler=P_euler / F_axial,
                sigma_cr_shell=sigma_cr, P_shell=P_shell, SF_shell=P_shell / F_axial)


# ----------------------------------------------------------------------------
# 2. Body bending -- discretized beam under maneuver airload
# ----------------------------------------------------------------------------

def body_bending(q_dyn=17200.0, alpha=np.deg2rad(8.0), n_nodes=118):
    """Distribute Barrowman component normal forces along a beam, integrate
    shear & moment, return max bending stress in the composite wall."""
    bw = aero.barrowman()
    x = np.linspace(0, cm.L_TOTAL, n_nodes)
    w = np.zeros_like(x)                      # distributed load [N/m]
    comps = [
        (bw["cna_nose"], bw["xcp_nose"], 0.10),
        (bw["cna_r2"],  bw["xcp_r2"],  0.05),
        (bw["cna_r1"],  bw["xcp_r1"],  0.05),
    ]
    for cna, xcp, spread in comps:
        F = q_dyn * cm.A_REF * cna * alpha
        mask = np.abs(x - xcp) <= spread
        if mask.sum():
            w[mask] += F / (x[mask][-1] - x[mask][0] + 1e-9)
    # inertia relief: uniform mass reaction so net force = 0 (free-free)
    F_total = np.trapezoid(w, x)
    w -= F_total / cm.L_TOTAL
    shear = np.concatenate([[0], np.cumsum(0.5 * (w[1:] + w[:-1]) * np.diff(x))])
    moment = np.concatenate([[0], np.cumsum(0.5 * (shear[1:] + shear[:-1]) * np.diff(x))])
    M_max = np.max(np.abs(moment))
    # composite wall: stress in outer PETG fiber via modulus-weighted section
    I_total = cm.EI_COMPOSITE / cm.E_PETG_CF      # effective I in PETG units
    sigma = M_max * cm.R_BODY / I_total
    return dict(x=x, shear=shear, moment=moment, M_max=M_max,
                sigma_max=sigma, SF=cm.SIGMA_ALLOW_PETG / sigma)


# ----------------------------------------------------------------------------
# 3. Fin root bending (canard full throw at max q)
# ----------------------------------------------------------------------------

def fin_root_bending(q_dyn=16733.0, ring=cm.FIN_RING_1, delta=np.deg2rad(25.0)):
    cr, ct, b, tc = ring["cr"], ring["ct"], ring["b"], ring["tc"]
    AR = 2 * b / (cr + ct)
    cl_a = 2 * np.pi / (1 + 2 / AR)              # lifting-line
    cl = cl_a * delta
    S = 0.5 * (cr + ct) * b
    Fn = q_dyn * S * cl
    M = Fn * b / 2
    t_root = tc * cr
    I = cr * t_root ** 3 / 12
    sigma = M * (t_root / 2) / I
    return dict(Fn=Fn, M_bend=M, sigma=sigma, SF=cm.SIGMA_ALLOW_PETG / sigma)


# ----------------------------------------------------------------------------
# 4. Free-free first bending mode
# ----------------------------------------------------------------------------

def first_bending_mode():
    mu = cm.M_LIFTOFF / cm.L_TOTAL               # kg/m
    lam1 = 4.7300                                 # free-free beam, 1st mode (beta*L)
    omega = lam1 ** 2 * np.sqrt(cm.EI_COMPOSITE / (mu * cm.L_TOTAL ** 4))
    return omega / (2 * np.pi)                    # Hz


# ----------------------------------------------------------------------------
# 5. Fin flutter (NACA TN-4197 simplified, Martin's equation)
# ----------------------------------------------------------------------------

def flutter_velocity(ring=cm.FIN_RING_1, h=100.0):
    T, P, rho, a = cm.atmosphere(h)
    cr, ct, b, tc = ring["cr"], ring["ct"], ring["b"], ring["tc"]
    AR = b ** 2 / (0.5 * (cr + ct) * b)           # span^2/area
    lam = ct / cr
    GE = cm.G_PETG_CF
    denom = 1.337 * AR ** 3 * P * (lam + 1.0)
    num = GE * 2.0 * (AR + 2.0) * tc ** 3
    Vf = a * np.sqrt(num / denom)
    return Vf


# ----------------------------------------------------------------------------
# 6. Servo hinge moment margin
# ----------------------------------------------------------------------------

def servo_margin(q_dyn=16733.0):
    ring = cm.FIN_RING_2
    S = 0.5 * (ring["cr"] + ring["ct"]) * ring["b"]
    M_hinge = q_dyn * S * ring["cr"] * 0.020 * 0.436     # PDR empirical CHM
    T_servo = 4.5 * 0.0981                                # KST X08 Plus HV [N m]
    return dict(M_hinge=M_hinge, T_servo=T_servo, margin=T_servo / M_hinge)


def run_all_cases():
    return dict(
        axial=axial_buckling(),
        bending=body_bending(),
        fin_r1=fin_root_bending(ring=cm.FIN_RING_1),
        fin_r2=fin_root_bending(ring=cm.FIN_RING_2, q_dyn=16733.0),
        f1_hz=first_bending_mode(),
        Vf_r1=flutter_velocity(cm.FIN_RING_1),
        Vf_r2=flutter_velocity(cm.FIN_RING_2),
        servo=servo_margin(),
    )
