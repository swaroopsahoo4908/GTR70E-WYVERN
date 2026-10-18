// GTR70E WYVERN — barometric altitude driver: BME688 (0x76) on the shared I2C bus, BMP388 optional.
// =================================================================================================
// There is no PCA9548A mux and no second I2C bus on this board. BME688 (U3) shares the single
// GP0/GP1 bus with everything else (see imu_grv.h's file header for the full trace). The BOM has
// NO BMP388 -- only BME688 is physically populated on this board rev. The BMP388 code path is left
// in place rather than deleted: it fails closed (begin_I2C() returns false, bmp_ok_ stays false)
// and every accessor below already degrades gracefully to "use whichever sensor is healthy," so
// this class works correctly whether or not a BMP388 is ever added on a future rev or plugged in
// externally via the STEMMA-QT port.
//
// Address 0x76 is CONFIRMED, not a datasheet-default guess: tracing U3's pins against the netlist
// shows CSB (pin2) tied to the 3V3 net (selects I2C mode over SPI) and SDO (pin5) tied to the GND
// net (the SDO level sets the low address bit -- GND gives 0x76, VDDIO would give 0x77). SDI/SCK
// (pins 3/4) carry SDA0/SCL0, the same shared bus as everything else.
//
// Both are read every cycle on core 1 (baro is not control-loop-critical at 500 Hz; it's used for:
// ground datum at BOOT, launch-detect cross-check, apogee/landing detection during DESCENT, and the
// on-board altitude of record for post-flight reconstruction). Recovery is fully passive motor
// ejection with no altimeter-triggered deploy hardware on the vehicle, so BME688 alone is the
// altitude record on this board rev -- there is no second-sensor redundancy unless a BMP388 is
// added externally.
#pragma once
#include <Wire.h>
#include <Adafruit_BMP3XX.h>     // BMP388 (Adafruit 3966) -- not populated on this board rev, see above
#include <Adafruit_BME680.h>

class BaroPair {
public:
  explicit BaroPair(TwoWire& wire) : wire_(wire), bmp_(), bme_(&wire) {}

  bool begin() {
    bmp_ok_ = bmp_.begin_I2C(0x77, &wire_);
    if (bmp_ok_) {                                   // BMP388 needs oversampling/filter/ODR set up
      bmp_.setTemperatureOversampling(BMP3_OVERSAMPLING_2X);
      bmp_.setPressureOversampling(BMP3_OVERSAMPLING_4X);
      bmp_.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
      bmp_.setOutputDataRate(BMP3_ODR_50_HZ);
    }
    bme_ok_ = bme_.begin(0x76);
    if (bmp_ok_ || bme_ok_) {
      // Take the ground-level pressure datum now (called once at BOOT, vehicle stationary on the
      // pad) so altitude-above-ground can be computed without depending on a fixed sea-level
      // pressure constant that drifts with weather.
      read_();
      datum_hpa_ = pressure_hpa();
    }
    return bmp_ok_ || bme_ok_;
  }

  // Re-take the ground datum (e.g. if BOOT is re-entered after a long pad hold and weather drifted).
  void set_datum() { datum_hpa_ = pressure_hpa(); }

  void update() { read_(); }

  bool bmp_ok() const { return bmp_ok_; }
  bool bme_ok() const { return bme_ok_; }

  // Combined pressure (hPa), averaging whichever sensors are healthy.
  float pressure_hpa() const {
    if (bmp_ok_ && bme_ok_) return 0.5f * (bmp_p_ + bme_p_);
    if (bmp_ok_) return bmp_p_;
    if (bme_ok_) return bme_p_;
    return NAN;
  }
  float temperature_c() const {
    if (bmp_ok_ && bme_ok_) return 0.5f * (bmp_t_ + bme_t_);
    if (bmp_ok_) return bmp_t_;
    if (bme_ok_) return bme_t_;
    return NAN;
  }
  float gas_resistance_ohm() const { return bme_ok_ ? bme_gas_ : NAN; }  // BME688 only

  // Barometric altitude above the BOOT-time pad datum, meters. Standard hypsometric approximation
  // (ISA, valid for the few-hundred-meter altitudes this vehicle flies -- see we4_flightsim.py,
  // apogee ~397 ft / 121.1 m).
  float altitude_agl_m() const {
    float p = pressure_hpa();
    if (!isfinite(p) || !isfinite(datum_hpa_) || datum_hpa_ <= 0.0f) return NAN;
    return 44330.0f * (1.0f - powf(p / datum_hpa_, 0.1903f));
  }

  // raw per-sensor accessors, for logging both channels independently (catches one sensor drifting)
  float bmp_pressure_hpa() const { return bmp_p_; }
  float bme_pressure_hpa() const { return bme_p_; }

private:
  void read_() {
    if (bmp_ok_) {
      if (bmp_.performReading()) {          // BMP3XX populates .pressure (Pa) and .temperature (C)
        bmp_p_ = bmp_.pressure / 100.0f;
        bmp_t_ = bmp_.temperature;
      }
    }
    if (bme_ok_) {
      if (bme_.performReading()) {
        bme_p_ = bme_.pressure / 100.0f;
        bme_t_ = bme_.temperature;
        bme_gas_ = bme_.gas_resistance;
      }
    }
  }

  TwoWire& wire_;
  Adafruit_BMP3XX bmp_;
  Adafruit_BME680 bme_;
  bool bmp_ok_ = false, bme_ok_ = false;
  float bmp_p_ = NAN, bmp_t_ = NAN;
  float bme_p_ = NAN, bme_t_ = NAN, bme_gas_ = NAN;
  float datum_hpa_ = NAN;
};
