// GENERATED COPY -- edit firmware/wyvern_fin/fin_mixer.h and run sync_headers.py
#pragma once
// Four independent servos -> pitch (axis A), yaw (axis B), roll.
//   fin 0  A+ (az   0)  = +u_a + u_r      fin 2  B+ (az  90) = +u_b + u_r
//   fin 1  A- (az 180)  = +u_a - u_r      fin 3  B- (az 270) = +u_b - u_r
// u_a, u_b in "force convention" (same-direction normal force on both fins of the pair); u_r is a
// differential that makes a rolling couple. Roll gets a reserved slice of the deflection budget so
// it can never starve pitch/yaw. Mechanical mirror and trim live in fc_config.h.
#include "fc_config.h"

class FinMixer {
 public:
  void begin() {
    analogWriteFreq(WYV_SERVO_HZ);
    analogWriteRange(WYV_SERVO_RANGE);
    for (int i = 0; i < 4; i++) { pinMode(WYV_PIN_SERVO[i], OUTPUT); last_[i] = 0; write_(i, 0); }
  }
  void neutral() { for (int i = 0; i < 4; i++) { target_[i] = 0; } }
  void command(float u_a, float u_b, float u_r) {
    float lim = WYV_DEFL_MAX_DEG;
    u_r = constrain(u_r, -WYV_ROLL_DEFL_MAX, WYV_ROLL_DEFL_MAX);
    float m = lim - fabsf(u_r);
    u_a = constrain(u_a, -m, m); u_b = constrain(u_b, -m, m);
    target_[0] = u_a + u_r; target_[1] = u_a - u_r;
    target_[2] = u_b + u_r; target_[3] = u_b - u_r;
  }
  // rate-limit toward target and output; call at WYV_CTRL_HZ
  void update(float dt) {
    float step = WYV_DEFL_RATE_DPS * dt;
    for (int i = 0; i < 4; i++) {
      float d = constrain(target_[i] - last_[i], -step, step);
      last_[i] += d;
      write_(i, last_[i]);
    }
  }
  float defl(int i) const { return last_[i]; }
  void raw_us(int i, int us) { analogWrite(WYV_PIN_SERVO[i], us); }   // bench calibration only
 private:
  void write_(int i, float deg) {
    float us = WYV_SERVO_CENTER_US + WYV_SERVO_TRIM[i] + WYV_SERVO_SIGN[i] * deg * WYV_SERVO_US_PER_DEG;
    analogWrite(WYV_PIN_SERVO[i], (int)lroundf(us));
  }
  float target_[4] = {0, 0, 0, 0}, last_[4] = {0, 0, 0, 0};
};
