#pragma once
// Cross-core state. Core 0 (control) is the only writer of NavState/CtrlState; core 1 (radio,
// logging, baro, battery) is the only writer of AuxState. A seqlock gives core 1 a consistent copy
// without ever blocking core 0.
#include <Arduino.h>

enum FlightState : uint8_t {
  ST_BOOT = 0, ST_SELFTEST, ST_PAD, ST_ARMED, ST_BOOST_RAIL, ST_CONTROL, ST_COAST, ST_DESCENT,
  ST_LANDED, ST_FAULT
};

struct NavState {            // written by core 0 at 200 Hz
  uint32_t t_ms;
  float q[4];                // attitude quaternion (w,x,y,z), world = pad frame (Z up)
  float tilt_a, tilt_b;      // rad: tilt about body X (axis A) and body Y (axis B)
  float tilt_total;          // rad from vertical
  float w[3];                // body rates, rad/s
  float a_body[3];           // specific force, m/s^2
  float alt_m, vz, v_est;    // fused altitude / vertical speed / airspeed estimate
  float qbar;                // Pa
};

// Result of the authority-demonstration manoeuvre (one per axis), filled by core 0 as it runs.
struct ManAxis {
  float qbar_d;              // Pa, mean over the doublet fit window
  float b_fit, b_t;          // M_delta/I fit (1/s^2 per rad, + = fins push the way the PID thinks), t-stat
  float b_ratio;             // b_fit / (WYV_B_PER_Q * qbar_d): measured / model authority
  float qbar_s;              // Pa, mean over the step hold
  float step_sign;           // +1 / -1 (direction chosen to lower fin demand), 0 = step skipped
  float achieved_deg;        // mean attitude change over the last 200 ms of the hold
  float t63_s, overshoot_pct, return63_s;
  float fin_per_deg;         // change in pair deflection per degree achieved (steady part)
  float peak_rate_dps;
};
struct ManResult {
  uint8_t status;            // 0 idle, 1 running, 2 done, 3 skipped (gates), 4 aborted
  uint8_t valid;             // bit0 doublet A, bit1 doublet B, bit2 step A, bit3 step B
  ManAxis ax[2];
};

struct CtrlState {
  float defl_cmd[4];         // deg, per fin after mixing/limits
  float u_a, u_b, u_r;       // axis commands (deg) before mixing
  float ref_a, ref_b;        // attitude references (deg; 0 = hold vertical) -- manoeuvre steps
  float sched;
  float auth_b_a, auth_t_a;  // rail-exit authority monitor: fitted b and t-statistic (axis A)
  float a_axial;             // m/s^2, axial specific force used by the vertical channel
  uint8_t state;
  uint8_t flags;             // bit0 control_enabled, bit1 auth_abort, bit2 tilt_abort, bit3 doublet,
                             // bit4 attitude step, bit5 manoeuvre aborted/skipped, bit6 high-g in use
  uint32_t t_launch_ms;
  ManResult man;
};

struct AuxState {            // written by core 1
  float baro_alt_m, baro_hpa, temp_c, rh;
  float vbat;
  uint8_t sd_ok, radio_ok;
  uint8_t cmd_arm;           // set by a valid ARM uplink
  uint8_t cmd_servo_test;    // counter (incremented per valid uplink)
  uint8_t cmd_zero;          // counter: re-zero pad attitude
};

template <typename T>
class SeqBox {
 public:
  void write(const T& v) { seq_++; mb_(); data_ = v; mb_(); seq_++; }
  bool read(T& out) const {
    for (int i = 0; i < 4; i++) {
      uint32_t s0 = seq_; mb_();
      if (s0 & 1) continue;
      out = data_; mb_();
      if (seq_ == s0) return true;
    }
    return false;
  }
 private:
  volatile uint32_t seq_ = 0;
  T data_{};
  static inline void mb_() { __asm volatile("dmb" ::: "memory"); }
};

extern SeqBox<NavState>  g_nav;
extern SeqBox<CtrlState> g_ctrl;
extern SeqBox<AuxState>  g_aux;
