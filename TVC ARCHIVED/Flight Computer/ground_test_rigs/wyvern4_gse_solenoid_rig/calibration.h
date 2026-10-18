// GTR70E WYVERN — TVC-balance load-cell calibration (shared model, servo rig & solenoid rig).
// =============================================================================================
// Three strain-gauge load cells (1x axial Z 5 kg, 2x lateral X/Y 1 kg) restrain the thrust block
// through flexures (GSE_TestStands.md section 1). No physical flexure is a perfect single-DOF
// joint, so a dense 3x3 sensitivity matrix is fit instead of three independent per-axis gains --
// see MATH_DERIVATIONS.md section 1 for the full least-squares derivation. This header only
// implements the runtime side: invert once (done offline, baked in below as S_inv), then every
// sample is F_hat = S_inv @ (c - c0).
//
// S_fit, c0_fit, S_inv below are reproduced EXACTLY from phase0_math_constants.json --
// do not hand-edit; re-run derive_math.py and re-paste if the bench calibration changes.
#pragma once
#include <math.h>

namespace calib {

// Raw HX711 tare/zero-load offsets (24-bit counts), one per channel, order {Z, X, Y}.
static constexpr double C0_COUNTS[3] = {
  524287.6565849357, 524288.6273381851, 524283.6918101103
};

// S^-1 (N per count), so that F = S_inv * (c - c0). Order/rows/cols {Z, X, Y}.
static constexpr double S_INV_N_PER_COUNT[3][3] = {
  { 0.00011767183809664447, -1.6632851787095515e-06,  2.272995971103288e-07 },
  {-1.3907227883856875e-06,  0.000117672273977086,   -1.6939028935167252e-07 },
  { 1.4133899227911556e-07, -1.1485092320561173e-07,  2.3810290458428143e-05 }
};

// Force reconstruction: raw signed 24-bit HX711 counts {Z, X, Y} -> force {Fz, Fx, Fy} in Newtons.
// NOTE ordering: this rig follows the same {Z,X,Y} channel order as the servo rig's calibration.h
// throughout (matches the row/col order the calibration matrix above was fit in) -- keep this
// order consistent end-to-end (HX711 read order, F[] order, CSV column order) or the cross-axis
// coupling terms silently apply to the wrong channel.
inline void counts_to_force(const long c[3], float F_out[3]) {
  double dc[3] = {
    (double)c[0] - C0_COUNTS[0],
    (double)c[1] - C0_COUNTS[1],
    (double)c[2] - C0_COUNTS[2]
  };
  for (int i = 0; i < 3; i++) {
    double f = 0.0;
    for (int j = 0; j < 3; j++) f += S_INV_N_PER_COUNT[i][j] * dc[j];
    F_out[i] = (float)f;
  }
}

// Thrust vector magnitude/direction from reconstructed force, per GSE_TestStands.md section 1
// and MATH_DERIVATIONS.md section 1.4. F_in order {Fz, Fx, Fy} (matches counts_to_force output).
// atan2 form used for theta (not bare atan) so it stays well-defined as Fz -> 0.
struct ThrustVector {
  float T_N;        // total thrust magnitude
  float theta_deg;  // off-axis (cone) angle from +Z
  float phi_deg;     // azimuth of the off-axis component, atan2(Fy, Fx)
};

inline ThrustVector thrust_vector(const float F[3]) {
  float Fz = F[0], Fx = F[1], Fy = F[2];
  ThrustVector tv;
  tv.T_N = sqrtf(Fx * Fx + Fy * Fy + Fz * Fz);
  tv.theta_deg = degrees(atan2f(sqrtf(Fx * Fx + Fy * Fy), Fz));
  tv.phi_deg = degrees(atan2f(Fy, Fx));
  return tv;
}

}  // namespace calib
