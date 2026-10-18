"""
CFD-lite aerodynamics module -- XRIM-117 WYVERN-E 70mm PTD
============================================================
Engineering-level coefficient buildup (Missile-DATCOM-style methods), exactly
following the derivation chain in WYVERN_Simulator.md:

  CD0(M,h) = CD_friction + CD_base + CD_fin_profile + CD_wave
  CN(alpha) = CN_alpha_linear * alpha + crossflow term (Allen-Perkins)
  XCP via Barrowman with body-fin interference

Methods:
  - Schlichting turbulent flat plate skin friction + compressibility correction
  - Hoerner base drag
  - Double-wedge fin profile drag (Prandtl-Glauert / Ackeret)
  - Sears-Haack / transonic ramp wave drag (VK ogive)
  - Barrowman CN_alpha & CP, Kt body-fin interference
  - Allen & Perkins viscous crossflow for high alpha
"""

import numpy as np
from . import common as cm


# ----------------------------------------------------------------------------
# Zero-lift drag buildup
# ----------------------------------------------------------------------------

def cd_friction(M, h=100.0, V=None):
    T, P, rho, a = cm.atmosphere(h)
    if V is None:
        V = np.maximum(M * a, 1.0)
    mu = cm.viscosity(T)
    Re = rho * V * cm.L_TOTAL / mu
    cf = 0.074 / Re ** 0.2                       # Schlichting turbulent
    cf = cf * (1.0 + 0.18 * M ** 2) ** (-0.12)   # compressibility
    return cf * cm.S_WET_RATIO


def cd_base(M):
    M = np.asarray(M, dtype=float)
    sub = 0.12 * (1.0 - np.minimum(M, 0.95) ** 2) ** (-0.5) * 0.02 + 0.02
    sup = 0.25 / np.maximum(M, 1.001) ** 2 + 0.012      # supersonic falloff
    return np.where(M < 0.95, sub, np.where(M < 1.05, sub, sup))


def cd_fin_profile(M):
    tc = 0.04
    S1 = 0.5 * (cm.FIN_RING_1["cr"] + cm.FIN_RING_1["ct"]) * cm.FIN_RING_1["b"]
    S2 = 0.5 * (cm.FIN_RING_2["cr"] + cm.FIN_RING_2["ct"]) * cm.FIN_RING_2["b"]
    s_fins = 4 * S1 + 4 * S2                      # 2.445e-2 m^2
    M = np.asarray(M, dtype=float)
    beta_sub = np.sqrt(np.clip(1.0 - M ** 2, 0.05, None))
    cd_sub = 2.0 * tc * (1.0 + tc) / beta_sub * 0.01
    beta_sup = np.sqrt(np.clip(M ** 2 - 1.0, 0.05, None))
    cd_sup = 4.0 * tc ** 2 / beta_sup
    cd_prof = np.where(M < 1.0, cd_sub, cd_sup)
    return cd_prof * s_fins / cm.A_REF


def cd_wave(M):
    """VK ogive wave drag: zero below M=0.8 (PDR), quadratic transonic ramp to
    CD_wave=0.03 at M=1 (PDR), then smooth rise toward an 0.06 asymptote.
    NOTE: the PDR's Sears-Haack expression is dimensionally inconsistent
    (yields CD~57); replaced supersonic branch with slender-body scaling.
    Validity: engineering accuracy M<0.9; transonic band indicative only."""
    M = np.asarray(M, dtype=float)
    ramp = 0.03 * ((M - 0.8) / 0.2) ** 2
    sup = 0.03 + 0.03 * (1.0 - np.exp(-(M - 1.0) / 0.15))
    return np.where(M < 0.8, 0.0, np.where(M <= 1.0, ramp, sup))


def cd0(M, h=100.0):
    """Total zero-lift drag coefficient (ref: body cross-section)."""
    return cd_friction(M, h) + cd_base(M) + cd_fin_profile(M) + cd_wave(M)


# ----------------------------------------------------------------------------
# Barrowman normal force & center of pressure
# ----------------------------------------------------------------------------

def _fin_ring(ring):
    cr, ct, b, n = ring["cr"], ring["ct"], ring["b"], ring["n"]
    AR = 2 * b / (cr + ct)
    cna = (4 * n * (b / cm.D_REF) ** 2) / (1 + np.sqrt(1 + (2 * b / (cr + ct)) ** 2))
    kt = 1 + (cm.D_REF / 2) / (b + cm.D_REF / 2)
    cna *= kt
    # MAC and CP location (Barrowman)
    mac = (2.0 / 3.0) * (cr + ct - cr * ct / (cr + ct))
    y_mac = (b / 3.0) * (cr + 2 * ct) / (cr + ct)
    x_le_mac = ring["x_le"] + y_mac * (cr - ct) / b * 0.5  # LE sweep of trapezoid
    xcp = ring["x_le"] + 0.25 * mac + (cr - ct) / 6.0 * (cr + 2 * ct) / (cr + ct) \
          + (1.0 / 6.0) * (cr + ct - cr * ct / (cr + ct))
    return cna, xcp, AR


def barrowman():
    """Returns dict with per-component CN_alpha [/rad] and XCP [m from nose]."""
    cna_nose, xcp_nose = 2.0, (2.0 / 3.0) * cm.L_NOSE
    cna_r1, xcp_r1, ar1 = _fin_ring(cm.FIN_RING_1)
    cna_r2, xcp_r2, ar2 = _fin_ring(cm.FIN_RING_2)
    cna_tot = cna_nose + cna_r1 + cna_r2
    xn = (cna_nose * xcp_nose + cna_r1 * xcp_r1 + cna_r2 * xcp_r2) / cna_tot
    return dict(
        cna_nose=cna_nose, xcp_nose=xcp_nose,
        cna_r1=cna_r1, xcp_r1=xcp_r1, AR1=ar1,
        cna_r2=cna_r2, xcp_r2=xcp_r2, AR2=ar2,
        cna_total=cna_tot, xn=xn,
    )


BW = None  # populated on first use


def cn_alpha_total():
    global BW
    if BW is None:
        BW = barrowman()
    return BW["cna_total"]


def neutral_point():
    global BW
    if BW is None:
        BW = barrowman()
    return BW["xn"]


def stability_margin(xcg):
    return (neutral_point() - xcg) / cm.D_REF


# ----------------------------------------------------------------------------
# Force coefficients vs angle of attack (Allen-Perkins crossflow augmentation)
# ----------------------------------------------------------------------------
CDC_CROSSFLOW = 1.2          # crossflow drag coefficient of cylinder
A_PLAN = cm.D_REF * (cm.L_TOTAL - cm.L_NOSE) + 0.667 * cm.D_REF * cm.L_NOSE


def cn(alpha):
    """Normal force coefficient: linear Barrowman + viscous crossflow."""
    a = np.asarray(alpha, dtype=float)
    lin = cn_alpha_total() * a
    cross = CDC_CROSSFLOW * (A_PLAN / cm.A_REF) * np.sin(a) ** 2 * np.sign(a)
    return lin + cross


def cd_total(M, alpha, h=100.0):
    """Drag polar: CD = CD0 + induced (CN * sin alpha)."""
    return cd0(M, h) + np.abs(cn(alpha) * np.sin(alpha))


def ca_cn_body(M, alpha, h=100.0):
    """Axial & normal force coefficients in body axes."""
    cnv = cn(alpha)
    cdv = cd0(M, h)
    ca = cdv * np.cos(alpha)            # axial ~ zero-lift drag at small alpha
    return ca, cnv


# Canard control effectiveness (Ring 2 all-moving)
def cn_delta():
    global BW
    if BW is None:
        BW = barrowman()
    return BW["cna_r2"]                  # /rad of canard deflection


def pitch_damping(xcg):
    """Cmq estimate: sum CNa_i * ((xcp_i - xcg)/D)^2  [per rad/(rad/s) nondim]."""
    global BW
    if BW is None:
        BW = barrowman()
    terms = [
        (BW["cna_nose"], BW["xcp_nose"]),
        (BW["cna_r1"], BW["xcp_r1"]),
        (BW["cna_r2"], BW["xcp_r2"]),
    ]
    return -sum(c * ((x - xcg) / cm.D_REF) ** 2 for c, x in terms)
