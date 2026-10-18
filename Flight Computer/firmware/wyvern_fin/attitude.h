#pragma once
// Attitude for a boosting rocket.
//  * On the pad: BNO085 Game Rotation Vector (6-axis fusion) gives the initial attitude; the pad
//    frame is captured on ZERO so "tilt" is measured from how the rocket sits on the rail.
//  * From launch: the fusion's accelerometer tilt-correction is wrong under thrust (specific force
//    is along the body axis, not "down"), so we propagate our own quaternion from the BNO085's
//    calibrated gyro at 400 Hz. Gyro-only drift over a ~10 s ascent is a fraction of a degree.
// BNO085 accelerometer full scale is +/-8 g; the F42-4T ignition spike (~8.2 g) touches it for a few ms (highg.h covers the axial channel).
#include <Adafruit_BNO08x.h>
#include <math.h>
#include "fc_config.h"

struct Q { float w = 1, x = 0, y = 0, z = 0; };
static inline Q qmul(const Q& a, const Q& b) {
  return { a.w*b.w - a.x*b.x - a.y*b.y - a.z*b.z, a.w*b.x + a.x*b.w + a.y*b.z - a.z*b.y,
           a.w*b.y - a.x*b.z + a.y*b.w + a.z*b.x, a.w*b.z + a.x*b.y - a.y*b.x + a.z*b.w };
}
static inline Q qconj(const Q& a) { return { a.w, -a.x, -a.y, -a.z }; }
static inline void qnorm(Q& a) { float n = sqrtf(a.w*a.w + a.x*a.x + a.y*a.y + a.z*a.z); a.w/=n; a.x/=n; a.y/=n; a.z/=n; }

class Attitude {
 public:
  bool begin() {
    pinMode(WYV_PIN_BNO_INT, INPUT_PULLUP);
    if (!bno_.begin_I2C(WYV_ADDR_BNO085, &WYV_I2C)) return false;
    return enable_reports_();
  }
  // Call as fast as possible on core 0; returns true when a new gyro sample was integrated.
  bool poll(uint32_t now_us) {
    if (bno_.wasReset()) enable_reports_();
    bool got_gyro = false;
    sh2_SensorValue_t v;
    while (bno_.getSensorEvent(&v)) {
      switch (v.sensorId) {
        case SH2_GAME_ROTATION_VECTOR: {
          auto& r = v.un.gameRotationVector; q_grv_ = { r.real, r.i, r.j, r.k }; break; }
        case SH2_GYROSCOPE_CALIBRATED: {
          w_[0] = v.un.gyroscope.x; w_[1] = v.un.gyroscope.y; w_[2] = v.un.gyroscope.z;
          float dt = last_gyro_us_ ? (now_us - last_gyro_us_) * 1e-6f : 0.0f;
          last_gyro_us_ = now_us;
          if (inertial_ && dt > 0 && dt < 0.02f) integrate_(dt);
          got_gyro = true; last_ok_ms_ = millis(); break; }
        case SH2_ACCELEROMETER: {
          a_[0] = v.un.accelerometer.x; a_[1] = v.un.accelerometer.y; a_[2] = v.un.accelerometer.z; break; }
      }
    }
    if (!inertial_) q_ = q_grv_;
    return got_gyro;
  }
  void zero_pad()      { q_pad_inv_ = qconj(q_grv_); }      // pad frame = current attitude
  void go_inertial()   { inertial_ = true; q_ = q_grv_; }   // call at launch detect
  bool stale(uint32_t now_ms) const { return now_ms - last_ok_ms_ > 20; }

  // attitude relative to the pad frame
  Q rel() const { Q r = qmul(q_pad_inv_, q_); qnorm(r); return r; }
  // small-angle tilt components about body X (axis A) and Y (axis B), rad, and total tilt
  void tilts(float& ta, float& tb, float& tt) const {
    Q r = rel();
    // body Z axis expressed in the pad frame
    float zx = 2 * (r.x * r.z + r.w * r.y);
    float zy = 2 * (r.y * r.z - r.w * r.x);
    float zz = 1 - 2 * (r.x * r.x + r.y * r.y);
    tb = atan2f(zx, zz);          // nose toward +X  -> rotation about +Y
    ta = atan2f(zy, zz);          // nose toward +Y  -> axis A
    tt = acosf(fminf(fmaxf(zz, -1.f), 1.f));
  }
  const float* rates() const { return w_; }
  const float* accel() const { return a_; }
  float accel_mag_g() const { return sqrtf(a_[0]*a_[0] + a_[1]*a_[1] + a_[2]*a_[2]) / 9.80665f; }
  Q quat() const { return rel(); }

 private:
  bool enable_reports_() {
    bool ok = bno_.enableReport(SH2_GAME_ROTATION_VECTOR, 5000);   // 200 Hz (pad + pre-launch)
    ok &= bno_.enableReport(SH2_GYROSCOPE_CALIBRATED, 2500);       // 400 Hz (inertial propagation)
    ok &= bno_.enableReport(SH2_ACCELEROMETER, 2500);              // 400 Hz (launch detect, v est)
    return ok;
  }
  void integrate_(float dt) {
    float hx = 0.5f * w_[0] * dt, hy = 0.5f * w_[1] * dt, hz = 0.5f * w_[2] * dt;
    Q dq = { 1.0f, hx, hy, hz }; q_ = qmul(q_, dq); qnorm(q_);
  }
  Adafruit_BNO08x bno_{WYV_PIN_BNO_RST};
  Q q_, q_grv_, q_pad_inv_;
  float w_[3] = {0, 0, 0}, a_[3] = {0, 0, 9.81f};
  uint32_t last_gyro_us_ = 0, last_ok_ms_ = 0;
  bool inertial_ = false;
};
