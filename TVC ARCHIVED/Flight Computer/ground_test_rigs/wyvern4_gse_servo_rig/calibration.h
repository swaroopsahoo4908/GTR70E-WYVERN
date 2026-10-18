// GTR70E WYVERN GSE — servo-TVC balance load-cell calibration + thrust-vector reconstruction.
// ============================================================================================
// Implements the pseudo-inverse least-squares calibration derived in
// `MATH_DERIVATIONS.md` section 1 (project artifact `ve7dc4cad_MATH_DERIVATIONS.md`) and the
// exact fitted numbers in `phase0_math_constants.json` (project artifact
// `v95988317_phase0_math_constants.json`). Do NOT re-derive or hand-tweak these numbers here --
// if the physical rig is re-calibrated, re-run the project's `derive_math.py` and paste the new
// S_fit / c0_fit / S_inv values into this file (keep the source-of-truth in one place).
//
// Measurement model (see MATH_DERIVATIONS.md 1.2): c = c0 + S*F, where c = [c_x, c_y, c_z] are the
// three HX711 raw 24-bit counts (lateral X, lateral Y, axial Z, in that fixed order throughout this
// file and the .ino), F = [Fx, Fy, Fz] is the true force vector in Newtons, S is the fitted dense
// 3x3 sensitivity matrix (counts/N) that captures cross-axis flexure coupling, and c0 is the
// per-channel zero-load tare offset (counts).
//
// Runtime reconstruction (MATH_DERIVATIONS.md 1.4): F_hat = S_inv * (c - c0), where S_inv is the
// pre-computed inverse of S_fit (N/count) -- inverted once offline, not on the MCU, since a 3x3
// inverse is cheap but there is no reason to burn flash/cycles re-deriving a constant.
//
// NOTE on "tare" vs. "calibration": the TARE serial command (see thrust_rig_tare() below) only
// re-zeros the c0 offset vector against whatever the load cells currently read with no load applied
// (corrects HX711 zero-drift between bench sessions, e.g. after a cold power-up or a thermal
// change). It does NOT re-fit S -- that requires the full N>=4 known-mass calibration procedure and
// re-running derive_math.py on the bench. A CAL_RESET command restores the factory-fitted c0_fit
// tare exactly, discarding any runtime tare.
#pragma once
#include <math.h>

namespace loadcell_cal {

// Channel order used throughout this file, the .ino, and the CSV log: 0=X (lateral), 1=Y
// (lateral), 2=Z (axial). Matches the row/column order of S_fit / S_inv / c0_fit below exactly as
// fitted in phase0_math_constants.json -- do not reorder without re-deriving.
enum Axis : uint8_t { AX_X = 0, AX_Y = 1, AX_Z = 2 };

// S_inv_N_per_count -- inverse of the fitted 3x3 sensitivity matrix S_fit (counts/N), from
// phase0_math_constants.json "load_cell_calibration.S_inv_N_per_count". Units: N per raw count.
constexpr float S_INV[3][3] = {
  { 1.176718380966e-04f, -1.663285178710e-06f,  2.272995971103e-07f },
  { -1.390722788386e-06f, 1.176722739771e-04f, -1.693902893517e-07f },
  { 1.413389922791e-07f, -1.148509232056e-07f,  2.381029045843e-05f }
};

// c0_fit_counts -- factory zero-load tare offset per channel (raw HX711 24-bit counts), from
// phase0_math_constants.json "load_cell_calibration.c0_fit_counts". These are large (~524288 =
// 2^19, i.e. near HX711 raw-count mid-scale for a bridge sitting close to its electrical zero) --
// expected and correct, not a bug.
constexpr float C0_FIT[3] = { 524287.656585f, 524288.627338f, 524283.691810f };

// cond(S_fit) = 5.006 (MATH_DERIVATIONS.md 1.3) -- well-conditioned, kept here only as a documented
// provenance breadcrumb; firmware does not need to check it at runtime.
constexpr float COND_S_FIT = 5.006342488338312f;

// Result of thrust_vector(): magnitude + direction of the reconstructed force vector, per
// GSE_TestStands.md section 1 / MATH_DERIVATIONS.md 1.4:
//   T     = sqrt(Fx^2+Fy^2+Fz^2)                          thrust magnitude, N
//   theta = atan2(sqrt(Fx^2+Fy^2), Fz)                     deflection off the Z (axial) axis, rad
//   phi   = atan2(Fy, Fx)                                  azimuth of the lateral component, rad
// atan2 form used for theta (rather than a bare atan) so it stays well-defined as Fz -> 0, matching
// MATH_DERIVATIONS.md 1.4 exactly.
struct ThrustVector {
  float T_N;
  float theta_rad;
  float phi_rad;
};

// Force reconstruction: F_hat = S_inv * (c - c0). `counts` and `c0` are both in fixed [X,Y,Z]
// channel order. Writes Fx,Fy,Fz (N) into out_F[3].
inline void reconstruct_force(const long counts[3], const float c0[3], float out_F[3]) {
  float d[3] = {
    (float)counts[0] - c0[0],
    (float)counts[1] - c0[1],
    (float)counts[2] - c0[2]
  };
  for (int i = 0; i < 3; i++) {
    out_F[i] = S_INV[i][0] * d[0] + S_INV[i][1] * d[1] + S_INV[i][2] * d[2];
  }
}

// Thrust magnitude + direction from a reconstructed force vector Fx,Fy,Fz (N).
inline ThrustVector thrust_vector(float Fx, float Fy, float Fz) {
  ThrustVector v;
  v.T_N = sqrtf(Fx * Fx + Fy * Fy + Fz * Fz);
  v.theta_rad = atan2f(sqrtf(Fx * Fx + Fy * Fy), Fz);
  v.phi_rad = atan2f(Fy, Fx);
  return v;
}

// ---------------------------------------------------------------------------------------------
// Runtime tare state. c0_runtime[] starts at the factory C0_FIT values and can be overwritten by
// the bench TARE command (see t4_gse_servo_rig-style tare() call in the .ino) to correct zero-load
// drift without touching the fitted S_inv matrix. CAL_RESET restores C0_FIT exactly.
// ---------------------------------------------------------------------------------------------
class RuntimeTare {
public:
  void reset_to_factory() {
    for (int i = 0; i < 3; i++) c0_[i] = C0_FIT[i];
  }

  // Call with the mean of several raw-count samples taken with the rig unloaded (no thrust, gimbal
  // at rest) to re-zero. Overwrites the effective c0 used by reconstruct_force().
  void set_from_samples(const float mean_counts[3]) {
    for (int i = 0; i < 3; i++) c0_[i] = mean_counts[i];
  }

  const float* c0() const { return c0_; }

private:
  float c0_[3] = { C0_FIT[0], C0_FIT[1], C0_FIT[2] };
};

}  // namespace loadcell_cal
