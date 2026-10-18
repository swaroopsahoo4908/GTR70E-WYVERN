#pragma once
// ADXL375 (+/-200 g, Adafruit 5374) on Wire1 next to the BNO085, read by core 0.
// Why: the F42-4T ignition spike reaches ~8.2 g and the F67-6W holds 11-12 g; the BNO085
// accelerometer tops out at 8 g, so the integrated climb rate (and with it qbar and the gain
// schedule) would come out low at burnout (about 20 m/s low on the F67-6W). Only the axial
// component is used, and only while |a| from the BNO is near its limit.
// Register map is the ADXL345 family's (ADXL375 datasheet rev. B, Table 19).
#include <Wire.h>
#include "fc_config.h"

class HighG {
 public:
  bool begin() {
    if (rd8_(0x00) != 0xE5) return false;           // DEVID
    wr8_(0x2C, 0x0D);                                 // BW_RATE: 800 Hz output (400 Hz bandwidth)
    wr8_(0x31, 0x0B);                                 // DATA_FORMAT: right-justified, 4-wire off
    wr8_(0x38, 0x00);                                 // FIFO bypass
    wr8_(0x2D, 0x08);                                 // POWER_CTL: measure
    ok_ = true; return true;
  }
  // axial specific force in m/s^2 (rocket axis, + toward the nose), bias-corrected
  bool read(float& a_axial) {
    if (!ok_) return false;
    uint8_t b[6];
    WYV_I2C.beginTransmission(WYV_ADDR_ADXL375); WYV_I2C.write(0x32);
    if (WYV_I2C.endTransmission(false) != 0) return false;
    if (WYV_I2C.requestFrom((uint8_t)WYV_ADDR_ADXL375, (uint8_t)6) != 6) return false;
    for (int i = 0; i < 6; i++) b[i] = WYV_I2C.read();
    int16_t v = (int16_t)(b[2 * WYV_ADXL_AXIS] | (b[2 * WYV_ADXL_AXIS + 1] << 8));
    raw_g_ = WYV_ADXL_SIGN * v * WYV_ADXL_LSB_G;
    a_axial = (raw_g_ - bias_g_) * 9.80665f;
    return true;
  }
  // on the pad: learn the offset against the BNO085's axial reading (0-g offset is +/-0.4 g class)
  void learn_bias(float bno_axial_ms2) { bias_acc_ += raw_g_ - bno_axial_ms2 / 9.80665f; n_++; bias_g_ = bias_acc_ / n_; }
  void reset_bias() { bias_acc_ = 0; n_ = 0; }
  float bias_g() const { return bias_g_; }
  bool ok() const { return ok_; }
 private:
  uint8_t rd8_(uint8_t r) {
    WYV_I2C.beginTransmission(WYV_ADDR_ADXL375); WYV_I2C.write(r); WYV_I2C.endTransmission(false);
    WYV_I2C.requestFrom((uint8_t)WYV_ADDR_ADXL375, (uint8_t)1); return WYV_I2C.available() ? WYV_I2C.read() : 0;
  }
  void wr8_(uint8_t r, uint8_t v) { WYV_I2C.beginTransmission(WYV_ADDR_ADXL375); WYV_I2C.write(r); WYV_I2C.write(v); WYV_I2C.endTransmission(); }
  bool ok_ = false; float raw_g_ = 0, bias_g_ = 0, bias_acc_ = 0; uint32_t n_ = 0;
};
