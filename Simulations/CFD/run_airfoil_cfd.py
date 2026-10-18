#!/usr/bin/env python3
"""GTR70E WYVERN (fin control) -- 2D section CFD: constant-strength vortex-panel method.

Carried over unchanged in method from the TVC revision (Kuethe & Chow, *Foundations of
Aerodynamics*, vortex panels + Kutta condition, validated against thin-airfoil theory). What
changed is the input: the four control-fin sections are now the printable definitions in
airfoil_profiles.py at the 60 mm ROOT chord, and the Reynolds numbers are the fin-chord values for
the adapted tunnel (8 m/s) and for G40 flight (25-80 m/s).

The 2D lift slope from here feeds the 3D vortex-lattice model (vlm.py) through the Helmbold
low-aspect-ratio correction, which is how section shape enters the fin-authority prediction.

Outputs: airfoil_polars.csv, cl_alpha.png, cp_distribution.png
Inviscid caveat: no separation, no stall, no laminar bubble -- exactly the things the tunnel is
for. Profile drag is a flat-plate skin-friction x thickness form-factor estimate.
"""
import os, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from airfoil_profiles import PROFILES

HERE = os.path.dirname(os.path.abspath(__file__))
NU = 1.5e-5
C_ROOT = 0.060
RE_TUNNEL = 8.0 * C_ROOT / NU      # 3.2e4
RE_FLIGHT = 60.0 * C_ROOT / NU     # 2.4e5

def solve_panels(XB, YB, alpha):
    M = len(XB) - 1
    X = 0.5 * (XB[:-1] + XB[1:]); Y = 0.5 * (YB[:-1] + YB[1:])
    dx = XB[1:] - XB[:-1]; dy = YB[1:] - YB[:-1]
    S = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    sn, cs = np.sin(th), np.cos(th)
    Xi = X[:, None]; Yi = Y[:, None]; XBj = XB[:-1][None, :]; YBj = YB[:-1][None, :]
    thi = th[:, None]; thj = th[None, :]; Sj = S[None, :]; snj = sn[None, :]; csj = cs[None, :]
    A = -(Xi - XBj) * csj - (Yi - YBj) * snj
    B = (Xi - XBj) ** 2 + (Yi - YBj) ** 2
    Cc = np.sin(thi - thj); Dd = np.cos(thi - thj)
    E = (Xi - XBj) * snj - (Yi - YBj) * csj
    np.fill_diagonal(B, 1.0)
    F = np.log(1.0 + (Sj ** 2 + 2 * A * Sj) / B)
    G = np.arctan2(E * Sj, B + A * Sj)
    P = (Xi - XBj) * np.sin(thi - 2 * thj) + (Yi - YBj) * np.cos(thi - 2 * thj)
    Q = (Xi - XBj) * np.cos(thi - 2 * thj) - (Yi - YBj) * np.sin(thi - 2 * thj)
    CN2 = Dd + 0.5 * Q * F / Sj - (A * Cc + Dd * E) * G / Sj
    CN1 = 0.5 * Dd * F + Cc * G - CN2
    CT2 = Cc + 0.5 * P * F / Sj + (A * Dd - Cc * E) * G / Sj
    CT1 = 0.5 * Cc * F - Dd * G - CT2
    di = np.diag_indices(M)
    CN1[di] = -1.0; CN2[di] = 1.0; CT1[di] = 0.5 * np.pi; CT2[di] = 0.5 * np.pi
    AN = np.zeros((M + 1, M + 1)); AT = np.zeros((M, M + 1))
    AN[:M, 0] = CN1[:, 0]; AN[:M, M] = CN2[:, M - 1]; AN[:M, 1:M] = CN1[:, 1:M] + CN2[:, 0:M - 1]
    AT[:, 0] = CT1[:, 0]; AT[:, M] = CT2[:, M - 1]; AT[:, 1:M] = CT1[:, 1:M] + CT2[:, 0:M - 1]
    AN[M, 0] = AN[M, M] = 1.0
    RHS = np.zeros(M + 1); RHS[:M] = np.sin(th - alpha)
    gamma = np.linalg.solve(AN, RHS)
    V = np.cos(th - alpha) + AT @ gamma
    Cp = 1.0 - V ** 2
    Cl = 2.0 * np.sum(V * S)
    return Cl, Cp, X, S

def viscous_cd(Re, tc):
    Cf = 1.328 / np.sqrt(Re) if Re < 5e5 else 0.074 / Re ** 0.2
    FF = 1.0 + 2.0 * tc + 60.0 * tc ** 4
    return 2.0 * Cf * FF

def cl_alpha_2d(name):
    """Inviscid 2D lift slope (per rad) from a 0-4 deg fit."""
    XB, YB = PROFILES[name]()
    a = np.radians([0, 1, 2, 3, 4])
    cl = [solve_panels(XB, YB, ai)[0] for ai in a]
    return float(np.polyfit(a, cl, 1)[0])

def sweep(alphas_deg=np.arange(0.0, 15.01, 0.5)):
    rows = []; curves = {}
    for name, fn in PROFILES.items():
        XB, YB = fn(); tc = float(2 * YB.max())
        curves[name] = []
        for ad in alphas_deg:
            Cl, _, _, _ = solve_panels(XB, YB, np.radians(ad))
            cdt = viscous_cd(RE_TUNNEL, tc); cdf = viscous_cd(RE_FLIGHT, tc)
            rows.append(dict(profile=name, alpha_deg=round(float(ad), 2), tc_root=round(tc, 4),
                             Cl_panel=round(float(Cl), 4), Cl_thin=round(float(2 * np.pi * np.radians(ad)), 4),
                             Cd_tunnel=round(float(cdt), 5), Cd_flight=round(float(cdf), 5)))
            curves[name].append(float(Cl))
    return rows, alphas_deg, curves

def validate():
    XB, YB = PROFILES["NACA0012"]()
    a = np.radians([0, 2, 4, 6]); cl = [solve_panels(XB, YB, ai)[0] for ai in a]
    return np.polyfit(a, cl, 1)[0], 2 * np.pi

if __name__ == "__main__":
    slope, ref = validate()
    print(f"validation: NACA0012 dCl/dalpha = {slope:.3f}/rad vs 2pi = {ref:.3f} ({100*slope/ref:.1f} %)")
    rows, alphas, curves = sweep()
    with open(os.path.join(HERE, "airfoil_polars.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, cl in curves.items(): ax.plot(alphas, cl, marker=".", ms=3, label=name)
    ax.plot(alphas, 2 * np.pi * np.radians(alphas), "k--", lw=1, label="thin-airfoil 2πα")
    ax.set(title="Control-fin sections at the 60 mm root (vortex panel, inviscid)",
           xlabel="deflection / angle of attack (deg)", ylabel="Cl"); ax.grid(alpha=.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "cl_alpha.png"), dpi=120); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, fn in PROFILES.items():
        XB, YB = fn(); Cl, Cp, X, S = solve_panels(XB, YB, np.radians(5))
        ax.plot(X, Cp, lw=1.2, label=f"{name} (Cl={Cl:.2f})")
    ax.invert_yaxis(); ax.set(title="Surface Cp at 5 deg", xlabel="x/c", ylabel="Cp"); ax.grid(alpha=.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "cp_distribution.png"), dpi=120); plt.close(fig)
    for n in PROFILES: print(f"  {n:13s} Cl_alpha = {cl_alpha_2d(n):.3f}/rad")
