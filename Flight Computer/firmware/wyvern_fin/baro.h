#pragma once
// Barometers (rev 4).
//  * BMP388 (Wire1, 0x76): primary altimeter. Register-level driver so nothing ever waits on a conversion:
//    the part free-runs in NORMAL mode at 50 Hz (pressure x8, temperature x1, IIR coefficient 3) and
//    we just read the six data bytes when 20 ms have passed. Compensation is the floating-point form
//    in the Bosch BMP388 datasheet (BST-BMP388-DS001, s.9.2-9.3).
//    Datasheet relative accuracy is +/-0.08 hPa (+/-0.66 m); sample-to-sample noise here is a few cm.
//  * BME688 (Wire1, shared with the BMP388 at 0x76): temperature and humidity for the air density used in qbar, and a second pressure
//    for a cross-check. Forced mode through the Adafruit library, started and collected 30 ms apart.
#include <Wire.h>
#include <Adafruit_BME680.h>
#include "fc_config.h"

class BMP388 {
 public:
  bool begin(TwoWire& w, uint8_t addr) {
    w_ = &w; a_ = addr;
    uint8_t id = 0;
    if (!rd_(0x00, &id, 1) || (id != 0x50 && id != 0x60)) return false;   // 0x50 BMP388, 0x60 BMP390
    wr_(0x7E, 0xB6); delay(10);                                           // soft reset
    uint8_t c[21];
    if (!rd_(0x31, c, 21)) return false;
    auto u16 = [&](int i) { return (uint16_t)(c[i] | (c[i + 1] << 8)); };
    auto s16 = [&](int i) { return (int16_t)u16(i); };
    t1_ = u16(0) * 256.0;                 // / 2^-8
    t2_ = u16(2) / 1073741824.0;          // / 2^30
    t3_ = (int8_t)c[4] / 281474976710656.0;   // / 2^48
    p1_ = (s16(5) - 16384) / 1048576.0;   // (P1 - 2^14) / 2^20
    p2_ = (s16(7) - 16384) / 536870912.0; // (P2 - 2^14) / 2^29
    p3_ = (int8_t)c[9]  / 4294967296.0;   // / 2^32
    p4_ = (int8_t)c[10] / 137438953472.0; // / 2^37
    p5_ = u16(11) * 8.0;                  // / 2^-3
    p6_ = u16(13) / 64.0;                 // / 2^6
    p7_ = (int8_t)c[15] / 256.0;          // / 2^8
    p8_ = (int8_t)c[16] / 32768.0;        // / 2^15
    p9_ = s16(17) / 281474976710656.0;    // / 2^48
    p10_ = (int8_t)c[19] / 281474976710656.0;
    p11_ = (int8_t)c[20] / 36893488147419103232.0;   // / 2^65
    wr_(0x1C, 0x03);                      // OSR: pressure x8, temperature x1
    wr_(0x1D, 0x02);                      // ODR 50 Hz (200 / 2^2)
    wr_(0x1F, 0x04);                      // IIR coefficient 3
    wr_(0x1B, 0x33);                      // press + temp enabled, NORMAL mode
    ok_ = true; return true;
  }
  // Call every loop; returns true when a fresh sample was read.
  bool poll(uint32_t now_ms) {
    if (!ok_ || now_ms - t_last_ < 20) return false;
    t_last_ = now_ms;
    uint8_t d[6];
    if (!rd_(0x04, d, 6)) { if (++fails_ > 10) ok_ = false; return false; }
    fails_ = 0;
    double up = d[0] | (d[1] << 8) | ((uint32_t)d[2] << 16);
    double ut = d[3] | (d[4] << 8) | ((uint32_t)d[5] << 16);
    double pd1 = ut - t1_, pd2 = pd1 * t2_;
    double t = pd2 + pd1 * pd1 * t3_;
    double o1 = p5_ + p6_ * t + p7_ * t * t + p8_ * t * t * t;
    double o2 = up * (p1_ + p2_ * t + p3_ * t * t + p4_ * t * t * t);
    double o3 = up * up * (p9_ + p10_ * t) + up * up * up * p11_;
    pa_ = (float)(o1 + o2 + o3); tc_ = (float)t;
    return true;
  }
  float pressure_pa() const { return pa_; }
  float temp_c() const { return tc_; }
  bool ok() const { return ok_; }
 private:
  bool rd_(uint8_t reg, uint8_t* b, uint8_t n) {
    w_->beginTransmission(a_); w_->write(reg);
    if (w_->endTransmission(false) != 0) return false;
    if (w_->requestFrom(a_, n) != n) return false;
    for (uint8_t i = 0; i < n; i++) b[i] = w_->read();
    return true;
  }
  void wr_(uint8_t reg, uint8_t v) { w_->beginTransmission(a_); w_->write(reg); w_->write(v); w_->endTransmission(); }
  TwoWire* w_ = nullptr; uint8_t a_ = 0x77;
  double t1_, t2_, t3_, p1_, p2_, p3_, p4_, p5_, p6_, p7_, p8_, p9_, p10_, p11_;
  float pa_ = NAN, tc_ = NAN; uint32_t t_last_ = 0; uint8_t fails_ = 0; bool ok_ = false;
};

class EnvSensor {          // BME688, async forced mode
 public:
  bool begin() {
    ok_ = bme_.begin(WYV_ADDR_BME688);
    if (!ok_) return false;
    bme_.setTemperatureOversampling(BME680_OS_2X);
    bme_.setPressureOversampling(BME680_OS_4X);
    bme_.setHumidityOversampling(BME680_OS_1X);
    bme_.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme_.setGasHeater(0, 0);                       // gas heater off: not needed, saves ~12 mA
    return true;
  }
  bool poll(uint32_t now_ms) {                     // 10 Hz
    if (!ok_) return false;
    if (!pending_ && now_ms - t0_ >= 100) { if (bme_.beginReading()) { pending_ = true; t0_ = now_ms; } return false; }
    if (pending_ && now_ms - t0_ >= 30) {
      pending_ = false;
      if (bme_.endReading()) { hpa_ = bme_.pressure / 100.0f; tc_ = bme_.temperature; rh_ = bme_.humidity; return true; }
    }
    return false;
  }
  float hpa() const { return hpa_; }
  float temp_c() const { return tc_; }
  float rh() const { return rh_; }
  bool ok() const { return ok_; }
 private:
  Adafruit_BME680 bme_{&WYV_I2C_ENV};
  float hpa_ = NAN, tc_ = NAN, rh_ = NAN; uint32_t t0_ = 0; bool pending_ = false, ok_ = false;
};

// Moist-air density (CIPM-2007 simplified): rho = (p - 0.378 e) / (R_d T), e from the Magnus formula.
static inline float moist_air_density(float p_pa, float t_c, float rh_pct) {
  float es = 611.2f * expf(17.62f * t_c / (243.12f + t_c));
  float e = constrain(rh_pct, 0.f, 100.f) * 0.01f * es;
  return (p_pa - 0.378f * e) / (287.058f * (t_c + 273.15f));
}
// Pressure altitude (ISA), m
static inline float pressure_alt_m(float p_pa) { return 44330.0f * (1.0f - powf(p_pa / 101325.0f, 0.190263f)); }
