#pragma once
// Tilt-hold controller with dynamic-pressure gain scheduling, roll-rate damping, a control-
// effectiveness (authority) monitor, and the authority-demonstration manoeuvre.
#include <math.h>
#include <string.h>
#include "shared_state.h"
#include "fc_config.h"

class AxisPID {
 public:
  explicit AxisPID(float scale) : scale_(scale) {}
  float step(float theta, float omega, float sched, float dt) {
    integ_ = constrain(integ_ + theta * dt, -WYV_INTEG_LIM, WYV_INTEG_LIM);
    float u = sched * scale_ * (WYV_KP * theta + WYV_KI * integ_ + WYV_KD * omega);   // rad
    return u * 57.29578f;                                                            // deg
  }
  void reset() { integ_ = 0; }
 private:
  float scale_, integ_ = 0;
};

// Least-squares fit of angular acceleration against the fin deflection, with the attitude, the rate
// and a constant as nuisance regressors:
//   omega_dot(t) = c + a * theta(t) + m_q * omega(t) + b * delta(t)
// (4x4 normal equations, solved once at the end of the window). b is the control derivative
// M_delta / I in rad/s^2 per rad. Leaving out theta and omega biases b by 20-30 % in the sim,
// because the PID moves delta together with them.
class AuthorityMonitor {
 public:
  void reset() { n_ = 0; memset(S_, 0, sizeof(S_)); memset(Sy_, 0, sizeof(Sy_)); syy_ = 0; sdd_ = 0; last_w_ = NAN; }
  void add(float omega, float theta, float delta_deg, float dt) {
    if (!isnan(last_w_) && dt > 0) {
      float y = (omega - last_w_) / dt;
      float x[4] = { 1.0f, theta, omega, delta_deg * 0.0174533f };
      for (int i = 0; i < 4; i++) { Sy_[i] += x[i] * y; for (int j = i; j < 4; j++) S_[i][j] += x[i] * x[j]; }
      syy_ += y * y; sdd_ += x[3] * x[3]; n_++;
    }
    last_w_ = omega;
  }
  // fitted b (rad/s^2 per rad) and its t-statistic; false if the window is too short / degenerate
  bool fit(float& b, float& t) const {
    b = 0; t = 0;
    if (n_ < 12) return false;
    double A[4][8];
    for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) { A[i][j] = j >= i ? S_[i][j] : S_[j][i]; A[i][j + 4] = (i == j); }
    for (int c = 0; c < 4; c++) {                         // Gauss-Jordan inverse with partial pivoting
      int p = c; for (int r = c + 1; r < 4; r++) if (fabs(A[r][c]) > fabs(A[p][c])) p = r;
      if (fabs(A[p][c]) < 1e-12) return false;
      if (p != c) for (int k = 0; k < 8; k++) { double tmp = A[c][k]; A[c][k] = A[p][k]; A[p][k] = tmp; }
      double d = A[c][c]; for (int k = 0; k < 8; k++) A[c][k] /= d;
      for (int r = 0; r < 4; r++) if (r != c) { double f = A[r][c]; for (int k = 0; k < 8; k++) A[r][k] -= f * A[c][k]; }
    }
    double beta[4] = {0, 0, 0, 0};
    for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) beta[i] += A[i][j + 4] * Sy_[j];
    double ssr = syy_; for (int i = 0; i < 4; i++) ssr -= beta[i] * Sy_[i];
    double s2 = fmax(ssr, 1e-12) / (n_ - 4);
    double se = sqrt(fmax(s2 * A[3][7], 1e-30));
    b = (float)beta[3]; t = (float)(beta[3] / se);
    return true;
  }
  float excitation_rms() const { return n_ ? sqrtf(sdd_ / n_) : 0; }
 private:
  int n_ = 0; double S_[4][4], Sy_[4], syy_ = 0, sdd_ = 0; float last_w_ = NAN;
};

// ------------------------------------------------------------------------------------------------
// Authority-demonstration manoeuvre (see fc_config.h WYV_MAN_*; mirrored by wf_flightsim.MAN).
// Axis convention inside this class: theta = tilt about the axis (rad), thd = d(theta)/dt,
// dpair = mean deflection of the pair (deg). A healthy pair gives d2(theta)/dt2 < 0 for delta > 0,
// so the reported b_fit is the negated regression slope (positive = fins work as designed).
struct ManIn {
  uint32_t tl;                 // ms since launch
  float qbar, tilt_total, alt; // Pa, rad, m
  float th[2], thd[2];         // rad, rad/s   (axis A, axis B)
  float dpair[2];              // deg
};

class ManeuverSeq {
 public:
  // returns attitude references (rad) and doublet injections (deg); flags OR'ed into fl
  void tick(const ManIn& in, float dt, float ref[2], float inj[2], uint8_t& fl) {
    ref[0] = ref[1] = 0; inj[0] = inj[1] = 0;
    for (int i = 0; i < 2; i++) dema_[i] += (in.dpair[i] - dema_[i]) * fminf(dt / 0.05f, 1.0f);   // 50 ms EMA
    if (!WYV_MAN_ENABLE || in.tl < WYV_MAN_T0_MS) return;
    if (R.status == 0) {                                   // gates, once
      bool ok = in.qbar >= WYV_MAN_QBAR_MIN && in.tilt_total <= WYV_MAN_TILT_MAX_DEG * D2R_ && in.alt >= WYV_MAN_ALT_MIN_M;
      R.status = ok ? 1 : 3; th0_[0] = in.th[0]; th0_[1] = in.th[1];
      for (int i = 0; i < 2; i++) { mon_[i].reset(); qsum_[i] = 0; nq_[i] = 0; R.ax[i] = ManAxis{}; }
    }
    if (R.status != 1) { if (R.status >= 3) fl |= 0x20; return; }
    if (hypotf(in.th[0] - th0_[0], in.th[1] - th0_[1]) > WYV_MAN_DEV_ABORT_DEG * D2R_) { R.status = 4; fl |= 0x20; return; }
    uint32_t tm = in.tl - WYV_MAN_T0_MS;
    const uint32_t offD[2] = { WYV_MAN_OFF_DA, WYV_MAN_OFF_DB }, offS[2] = { WYV_MAN_OFF_SA, WYV_MAN_OFF_SB };
    for (int i = 0; i < 2; i++) {
      // ---- doublet + fit window
      uint32_t d0 = offD[i], dE = d0 + 2 * WYV_MAN_DOUBLET_HALF, fE = dE + WYV_MAN_FIT_TAIL_MS;
      if (tm >= d0 && tm < dE) { inj[i] = tm < d0 + WYV_MAN_DOUBLET_HALF ? WYV_MAN_DOUBLET_DEG : -WYV_MAN_DOUBLET_DEG; fl |= 0x08; }
      if (tm >= d0 && tm < fE) { mon_[i].add(in.thd[i], in.th[i], in.dpair[i], dt); qsum_[i] += in.qbar; nq_[i]++; }
      if (tm >= fE && !(R.valid & (1 << i))) {
        float b, t; ManAxis& A = R.ax[i];
        if (mon_[i].fit(b, t)) {
          A.b_fit = -b; A.b_t = -t; A.qbar_d = nq_[i] ? qsum_[i] / nq_[i] : 0;
          A.b_ratio = A.qbar_d > 0 ? A.b_fit / (WYV_B_PER_Q * A.qbar_d) : 0;
        }
        R.valid |= 1 << i;
      }
      // ---- attitude step
      uint32_t s0 = offS[i], sH = s0 + WYV_MAN_HOLD_MS, sE = sH + WYV_MAN_REST_MS;
      ManAxis& A = R.ax[i];
      if (tm >= s0 && tm < sH) {
        if (step_ax_ != i) {                                  // step start
          step_ax_ = i; n_ = 0; sth0_ = in.th[i]; sd0_ = dema_[i]; ys_ = 0; ds_ = 0; nl_ = 0; qs_ = 0; pk_ = 0;
          A.step_sign = fabsf(sd0_) > WYV_MAN_HEADROOM_DEG ? 0.0f : (sd0_ < -0.5f ? -1.0f : 1.0f);
        }
        if (A.step_sign != 0) {
          ref[i] = sth0_ + A.step_sign * WYV_MAN_STEP_DEG * D2R_; fl |= 0x10;
          float y = A.step_sign * (in.th[i] - sth0_) * R2D_;
          if (n_ < NBUF) { yb_[n_] = y; tb_[n_] = (uint16_t)(tm - s0); n_++; }
          qs_ += in.qbar; pk_ = fmaxf(pk_, fabsf(in.thd[i]) * R2D_);
          if (tm - s0 >= WYV_MAN_HOLD_MS - 200) { ys_ += y; ds_ += in.dpair[i]; nl_++; }
        }
      }
      if (tm >= sH && step_ax_ == i && A.step_sign != 0 && !(R.valid & (4 << i))) {   // hold ended
        float ach = nl_ ? ys_ / nl_ : 0;
        A.achieved_deg = ach; A.qbar_s = n_ ? qs_ / n_ : 0; A.peak_rate_dps = pk_;
        A.t63_s = -1; A.overshoot_pct = 0; A.return63_s = -1;
        if (ach > 0.05f) {
          float ymax = 0;
          for (int k = 0; k < n_; k++) { ymax = fmaxf(ymax, yb_[k]); if (A.t63_s < 0 && yb_[k] >= 0.63f * ach) A.t63_s = tb_[k] * 1e-3f; }
          A.overshoot_pct = fmaxf(0, (ymax - ach) / ach * 100.f);
          A.fin_per_deg = fabsf((nl_ ? ds_ / nl_ : 0) - sd0_) / ach;
        }
        R.valid |= 4 << i;
      }
      if (tm >= sH && tm < sE && step_ax_ == i && A.step_sign != 0 && A.return63_s < 0 && A.achieved_deg > 0.05f) {
        float y = A.step_sign * (in.th[i] - sth0_) * R2D_;
        if (y <= 0.37f * A.achieved_deg) A.return63_s = (tm - sH) * 1e-3f;
      }
    }
    if (tm >= WYV_MAN_OFF_SB + WYV_MAN_HOLD_MS + WYV_MAN_REST_MS) R.status = 2;
  }
  ManResult R{};
 private:
  static constexpr float D2R_ = 0.0174533f, R2D_ = 57.29578f;
  static const int NBUF = 128;
  AuthorityMonitor mon_[2];
  float th0_[2] = {0, 0}, dema_[2] = {0, 0}, qsum_[2] = {0, 0}; int nq_[2] = {0, 0};
  int step_ax_ = -1, n_ = 0, nl_ = 0; float sth0_ = 0, sd0_ = 0, ys_ = 0, ds_ = 0, qs_ = 0, pk_ = 0;
  float yb_[NBUF]; uint16_t tb_[NBUF];
};

static inline float gain_schedule(float qbar) {
  return constrain(WYV_Q_REF_PA / fmaxf(qbar, 1.0f), WYV_SCHED_MIN, WYV_SCHED_MAX);
}
