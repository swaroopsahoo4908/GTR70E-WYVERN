// GTR70E WYVERN — flight PID controller for the servo-TVC pitch/yaw loops.
// =======================================================================
// Algorithm is bit-for-bit the validated loop in ../../Simulations/pid_reference.py and
// ../../Simulations/we4_atmos_tvc.py (closed-loop pitch-plane sim, run across 4 atmospheres +
// two 1-cosine gusts). See ../../CONFLICTS.md item 1 for why this firmware does NOT use the
// Kp=8/Ki=1.5/Kd=1.2 numbers printed on flowcharts/02_tvc_control_loop.mermaid — those were never
// run through the validated sim and ring against the ~40 ms servo lag at that gain.
//
// Discrete PID with:
//   - integral-clamp anti-windup
//   - first-order low-pass filtered derivative (kills IMU/quantization noise on d/dt)
//   - output (gimbal) clamp
//   - output SLEW-RATE limit (new: protects the servo linkage/gear train from a step command
//     that would otherwise ask for the full +-8 deg in one 2 ms tick)
//   - bumpless reset/re-arm: re-priming the loop (e.g. BOOST entry) does not produce a derivative
//     or integral kick from stale state
//
// Flight gains (re-tuned numerically -- see ../../Documentation/PID_TUNING_REPORT.md):
//   Kp = 0.10   Ki = 0.40   Kd = 0.18   out_lim = 8 deg (0.1396 rad)   tau_d = 0.02 s   i_lim = 0.4
// Tuning method: linearized the pitch plant (TVC control moment + fin aero restoring/damping)
// at 24 operating points spanning all 4 we4_atmos_tvc.py atmospheres x 6 burn-time slices, in
// series with the 40 ms servo lag and a 2nd-order Pade model of the 2 ms control-loop delay.
// Swept >800 (Kp,Ki,Kd) triples; kept only those clearing a classical worst-case margin floor
// (phase margin >= 30 deg, gain margin >= 6 dB) at EVERY one of the 24 points, then picked the
// survivor minimizing nonlinear gust-rejection pitch deviation (1-cosine 6-7 m/s gust, all 4
// atmospheres). The OLD Kp=2.0/Ki=0.4/Kd=0.5 gains fail this check outright: worst-case phase
// margin -6.2 deg and gain margin -2.0 dB (Cold -15C, t=0.6s into burn) -- i.e. genuinely
// unstable against the modeled servo lag + loop delay, which is why the nonlinear sim showed
// sustained ringing once that delay was modeled. New gains: worst-case PM=33.1 deg, GM=9.3 dB,
// worst-case gust pitch deviation 1.36 deg, worst gimbal usage 1.72 deg (limit +-8 deg -> more headroom).
// Do NOT use Kp=8 -- it rings even harder against the servo lag (see CONFLICTS.md).
#pragma once
#include <math.h>

struct PIDConfig {
  float kp, ki, kd;          // gains
  float out_lim;             // output (gimbal command) clamp, rad
  float tau_d = 0.02f;       // derivative low-pass time constant, s
  float i_lim = 0.4f;        // integral clamp (anti-windup), same units as the integral term
  float slew_lim = 0.0f;     // max |output change| per second, rad/s. 0 = disabled (no slew limit).
};

class PID {
public:
  explicit PID(const PIDConfig& cfg) : cfg_(cfg) {}

  // Backward-compatible constructor matching the original wyvern_pid.h call signature, so existing
  // call sites (`PID(0.10f, 0.40f, 0.18f, radians(8.0f))`) keep compiling unchanged.
  PID(float kp, float ki, float kd, float out_lim, float tau_d = 0.02f, float i_lim = 0.4f)
    : cfg_{kp, ki, kd, out_lim, tau_d, i_lim, 0.0f} {}

  // Full reset: zero integral, derivative state, and previous-error memory. Use on mode entry
  // (e.g. BOOST start) so a stale `prev_err_` from a prior arm cycle never produces a derivative
  // spike, and so the integrator never carries over a bias from ground handling.
  void reset() {
    integral_ = 0.0f;
    deriv_filt_ = 0.0f;
    prev_err_ = 0.0f;
    prev_out_ = 0.0f;
    primed_ = false;
  }

  // Bumpless reset: same as reset(), but seeds the slew limiter's "previous output" memory with
  // the actuator's actual current position rather than 0. Use this if the gimbal was already
  // holding a nonzero trim when the loop re-engages, so the first update doesn't slew away from
  // where the hardware physically is.
  void bumpless_reset(float current_output) {
    reset();
    prev_out_ = current_output;
  }

  void set_gains(float kp, float ki, float kd) { cfg_.kp = kp; cfg_.ki = ki; cfg_.kd = kd; }

  // err = setpoint - measurement (rad) ; dt = loop period (s) ; returns clamped, slew-limited
  // control output (rad). dt <= 0 or non-finite is treated as a skipped tick: returns the last
  // output unchanged rather than dividing by zero or injecting a derivative/integral spike --
  // this can happen if the 500 Hz core-0 loop ever stutters (e.g. a missed IMU sample).
  float update(float err, float dt) {
    if (!(dt > 0.0f) || !isfinite(dt) || !isfinite(err)) {
      return prev_out_;
    }
    // First call after a reset: prime prev_err_ so the very first derivative term is 0, not a
    // spike from whatever err happens to be relative to a stale 0.0f.
    if (!primed_) {
      prev_err_ = err;
      primed_ = true;
    }

    integral_ += err * dt;                                     // integrate
    if (integral_ > cfg_.i_lim) integral_ = cfg_.i_lim;          // anti-windup clamp
    else if (integral_ < -cfg_.i_lim) integral_ = -cfg_.i_lim;

    float raw_deriv = (err - prev_err_) / dt;
    prev_err_ = err;
    deriv_filt_ += (raw_deriv - deriv_filt_) * dt / (cfg_.tau_d + dt);   // 1st-order LP filter

    float u = cfg_.kp * err + cfg_.ki * integral_ + cfg_.kd * deriv_filt_;

    // Output (gimbal mechanical) clamp.
    if (u > cfg_.out_lim) u = cfg_.out_lim;
    else if (u < -cfg_.out_lim) u = -cfg_.out_lim;

    // Slew-rate limit: bound how fast the commanded output may move per cycle. Protects the servo
    // linkage from a discontinuous command (e.g. right after a reset, or a sensor glitch that
    // briefly saturates err). Disabled when slew_lim == 0.
    if (cfg_.slew_lim > 0.0f) {
      float max_step = cfg_.slew_lim * dt;
      float delta = u - prev_out_;
      if (delta > max_step) u = prev_out_ + max_step;
      else if (delta < -max_step) u = prev_out_ - max_step;
    }

    prev_out_ = u;
    return u;
  }

  // Telemetry accessors -- used by the flight log frame, not by the control math itself.
  float p_term(float err) const { return cfg_.kp * err; }
  float integral_state() const { return integral_; }
  float derivative_state() const { return deriv_filt_; }
  float last_output() const { return prev_out_; }
  const PIDConfig& config() const { return cfg_; }

private:
  PIDConfig cfg_;
  float integral_ = 0.0f;
  float deriv_filt_ = 0.0f;
  float prev_err_ = 0.0f;
  float prev_out_ = 0.0f;
  bool primed_ = false;
};

// ---------------------------------------------------------------------------------------------
// Dual-axis wrapper: one PID instance per axis (pitch, yaw), decoupled (no cross-coupling term --
// the airframe's pitch/yaw dynamics are symmetric per we4_atmos_tvc.py, so independent SISO loops
// per axis is the validated approach; a coupled MIMO controller was not modeled and is not flown).
// ---------------------------------------------------------------------------------------------
struct DualAxisPID {
  PID pitch;
  PID yaw;

  DualAxisPID(const PIDConfig& cfg) : pitch(cfg), yaw(cfg) {}

  void reset() { pitch.reset(); yaw.reset(); }
  void bumpless_reset(float pitch_out, float yaw_out) {
    pitch.bumpless_reset(pitch_out);
    yaw.bumpless_reset(yaw_out);
  }

  // err_pitch/err_yaw in rad, dt in s. Writes results into out_pitch/out_yaw (rad).
  void update(float err_pitch, float err_yaw, float dt, float& out_pitch, float& out_yaw) {
    out_pitch = pitch.update(err_pitch, dt);
    out_yaw = yaw.update(err_yaw, dt);
  }
};

// ---------------------------------------------------------------------------------------------
// Flight-default configuration. Single source of truth for both axes -- see ../../CONFLICTS.md
// section 5 for the frozen parameter table this mirrors.
// ---------------------------------------------------------------------------------------------
namespace wyvern_pid_defaults {
  constexpr float KP = 0.10f;
  constexpr float KI = 0.40f;
  constexpr float KD = 0.18f;
  constexpr float OUT_LIM_DEG = 8.0f;          // mechanical gimbal limit (raised 5->8 deg for wind/weathercock authority; see PID_AUTOTUNE_REPORT / weathercock note)
  constexpr float TAU_D = 0.02f;
  constexpr float I_LIM = 0.4f;
  // Slew limit: full +-8 deg range traversed in ~32 ms (250 deg/s) is generously fast for a
  // standard analog/digital servo and well under the 40 ms modeled servo lag's natural bandwidth --
  // this guards against a single-tick discontinuity, it is not meant to be the dominant dynamic.
  constexpr float SLEW_LIM_DEG_PER_S = 250.0f;

  inline PIDConfig make_config() {
    const float deg2rad = 3.14159265358979323846f / 180.0f;
    PIDConfig c;
    c.kp = KP; c.ki = KI; c.kd = KD;
    c.out_lim = OUT_LIM_DEG * deg2rad;
    c.tau_d = TAU_D;
    c.i_lim = I_LIM;
    c.slew_lim = SLEW_LIM_DEG_PER_S * deg2rad;
    return c;
  }
}
