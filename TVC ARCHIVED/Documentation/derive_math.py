#!/usr/bin/env python3
"""GTR70E WYVERN ground-test-rig math derivations: reproduces every number in MATH_DERIVATIONS.md.

  1. Load-cell 3x3 cross-axis calibration matrix (both TVC-balance rigs) -- least-squares pinv fit.
     This resolves the full thrust vector (and hence gimbal deflection) directly from the balance.

(The former ToF-ring plane-fit and Kalman-fusion derivations were removed with the ToF sensors.)

Run: python3 derive_math.py -- prints every intermediate result and writes
phase0_math_constants.json (machine-readable).
"""
import json
import numpy as np

np.set_printoptions(precision=6, suppress=True)
g = 9.80665

# ============================================================================
# 1. LOAD-CELL CALIBRATION MATRIX
# ============================================================================
print("="*70, "\n1. LOAD-CELL CALIBRATION MATRIX\n", "="*70)

S_true = np.array([
    [8500.0, 120.0, -80.0],
    [100.0, 8500.0, 60.0],
    [-50.0, 40.0, 42000.0],
])
c0_true = np.array([524288.0, 524288.0, 524288.0])

def counts_from_force(F, S, c0, noise_sigma=None, rng=None):
    c = c0 + S @ F
    if noise_sigma is not None:
        c = c + rng.normal(0, noise_sigma, size=3)
    return c

rng = np.random.default_rng(7)
noise_sigma = 15.0
F_cal = np.array([
    [0.0, 0.0, 0.0],
    [1.0*g, 0.0, 0.0], [2.0*g, 0.0, 0.0],
    [0.0, 1.0*g, 0.0], [0.0, 2.0*g, 0.0],
    [0.0, 0.0, 2.0*g], [0.0, 0.0, 4.0*g],
    [0.5*g, 0.5*g, 2.0*g], [-0.5*g, 0.7*g, 3.0*g],
])
C_cal = np.array([counts_from_force(F, S_true, c0_true, noise_sigma, rng) for F in F_cal])
A_design = np.column_stack([F_cal, np.ones(len(F_cal))])
A_pinv = np.linalg.pinv(A_design)
params = A_pinv @ C_cal
S_fit = params[:3, :].T
c0_fit = params[3, :]
S_inv = np.linalg.inv(S_fit)

print("S_fit (counts/N):\n", S_fit)
print("cond(S_fit) =", np.linalg.cond(S_fit))
print("eig(S_fit) =", np.linalg.eigvals(S_fit))
print("max abs err vs S_true:", np.max(np.abs(S_fit - S_true)))

F_test_true = np.array([0.8*g, -0.6*g, 20.0])
c_test = counts_from_force(F_test_true, S_true, c0_true, noise_sigma, rng)
F_test_hat = S_inv @ (c_test - c0_fit)

def thrust_vector(F):
    Fx, Fy, Fz = F
    T = np.sqrt(Fx**2 + Fy**2 + Fz**2)
    theta = np.arctan2(np.sqrt(Fx**2 + Fy**2), Fz)
    phi = np.arctan2(Fy, Fx)
    return T, theta, phi

T_hat, th_hat, ph_hat = thrust_vector(F_test_hat)
print(f"Test point F_hat={F_test_hat}, T={T_hat:.3f}N theta={np.rad2deg(th_hat):.3f}deg phi={np.rad2deg(ph_hat):.3f}deg")

# ============================================================================
# Save machine-readable constants
# ============================================================================
out = {
    "load_cell_calibration": {
        "S_fit_counts_per_N": S_fit.tolist(), "c0_fit_counts": c0_fit.tolist(),
        "S_inv_N_per_count": S_inv.tolist(), "cond_S_fit": float(np.linalg.cond(S_fit)),
    },
}
with open("phase0_math_constants.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nWrote phase0_math_constants.json")

# ============================================================================
# Validation figure (regenerates phase0_math_validation.png)
# ============================================================================
# This PNG was previously a hand-made orphan with no generating script, so it could not be kept in
# step with the derivation. It is now a reproducible output of this file.
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
rng2 = np.random.default_rng(11)
N_MC = 4000
# Monte-Carlo the whole calibrate-then-resolve pipeline: draw a random true thrust vector inside
# the balance's envelope, synthesize noisy counts, invert with the FITTED matrix, and score the
# error in resolved magnitude and direction. This is the quantity the RQ1 actuator comparison
# actually depends on -- it sets the smallest gimbal-angle difference the stand can distinguish.
T_err = np.zeros(N_MC); th_err = np.zeros(N_MC); th_true_all = np.zeros(N_MC)
for i in range(N_MC):
    th = np.deg2rad(rng2.uniform(0, 10)); ph = rng2.uniform(-np.pi, np.pi)
    Tm = rng2.uniform(5.0, 25.3)
    Ft = np.array([Tm*np.sin(th)*np.cos(ph), Tm*np.sin(th)*np.sin(ph), Tm*np.cos(th)])
    c = counts_from_force(Ft, S_true, c0_true, noise_sigma, rng2)
    Fh = S_inv @ (c - c0_fit)
    Th_, thh, _ = thrust_vector(Fh)
    T_err[i] = Th_ - Tm
    th_err[i] = np.rad2deg(thh - th)
    th_true_all[i] = np.rad2deg(th)

fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].imshow(np.abs(S_fit - S_true), cmap="viridis")
for r in range(3):
    for cc in range(3):
        ax[0].text(cc, r, f"{abs(S_fit-S_true)[r,cc]:.2f}", ha="center", va="center",
                   color="w", fontsize=9)
ax[0].set_xticks(range(3), ["Fx", "Fy", "Fz"]); ax[0].set_yticks(range(3), ["ch X", "ch Y", "ch Z"])
ax[0].set_title(f"Calibration-matrix fit error (counts/N)\nmax {np.max(np.abs(S_fit-S_true)):.2f}, "
                f"cond={np.linalg.cond(S_fit):.2f}", fontsize=10)

ax[1].hist(T_err, bins=60, color="#2a6f97", alpha=.85)
ax[1].axvline(0, c="k", lw=.8)
ax[1].set_xlabel("resolved thrust error (N)"); ax[1].set_ylabel("count")
ax[1].set_title(f"Thrust magnitude\nbias {T_err.mean():+.4f} N, 1σ {T_err.std():.4f} N", fontsize=10)
ax[1].grid(alpha=.3)

ax[2].scatter(th_true_all, th_err, s=3, alpha=.25, color="#bc4749")
ax[2].axhline(0, c="k", lw=.8)
ax[2].set_xlabel("true gimbal deflection θ (deg)"); ax[2].set_ylabel("θ error (deg)")
ax[2].set_title(f"Deflection-angle resolution\n1σ {th_err.std():.4f}° (N={N_MC})", fontsize=10)
ax[2].grid(alpha=.3)

fig.suptitle("GTR70E WYVERN, 3-axis balance calibration validation (least-squares fit + Monte-Carlo resolve)",
             fontweight="bold")
fig.tight_layout()
_p = os.path.join(HERE, "phase0_math_validation.png")
fig.savefig(_p, dpi=130); plt.close(fig)
print(f"Wrote {_p}")
print(f" resolved thrust bias {T_err.mean():+.4f} N, 1-sigma {T_err.std():.4f} N")
print(f" resolved theta 1-sigma {th_err.std():.4f} deg")

out["balance_resolution"] = {
    "thrust_bias_N": float(T_err.mean()), "thrust_sigma_N": float(T_err.std()),
    "theta_sigma_deg": float(th_err.std()), "n_monte_carlo": N_MC,
}
with open("phase0_math_constants.json", "w") as f:
    json.dump(out, f, indent=2)
