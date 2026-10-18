#pragma once
// ================================================================================================
// Battery monitor, GTR70E WYVERN, Pico 2 W perfboard revision.
//
// The retired PCB1 carried an INA226 across a 10 mOhm shunt. There is no current monitor on the
// perfboard build -- pack health is a plain resistor divider into ADC0, which is enough to gate
// arming and to log the rail through the flight.
//
//   armed pack+ ---[ 100k ]---+---[ 47k ]--- GND
//                             |
//                             +--- GP26 (ADC0), with 100 nF to GND
//
// Vadc = Vpack * 47/147 = Vpack / 3.128
//   8.4 V (2S full)      -> 2.686 V
//   7.4 V (2S nominal)   -> 2.366 V
//   6.4 V (warn)         -> 2.046 V
//   6.0 V (critical)     -> 1.918 V
// All inside the Pico's 3.3 V ADC range with headroom, so no clamping is needed.
//
// The divider taps the ARMED side of the switch, so it reads 0 when disarmed. That is fine: the
// Pico is unpowered then too.
//
// These are true per-cell-pair LiPo thresholds, not the rail-sag proxies the PCB1 firmware used.
// 6.4 V is ~3.20 V/cell and 6.0 V is ~3.00 V/cell.
//
// Divider values, thresholds and the ADC pin all come from wyvern_config.h -- change them there,
// not here.
// ================================================================================================

#include <Arduino.h>
#include "wyvern_config.h"

class Battery {
public:
  void begin() {
    analogReadResolution(12);          // 0..4095 on the RP2350 ADC
    filt_v_ = read_raw_volts();        // seed the filter so the first sample isn't a ramp
  }

  // Call at housekeeping rate (core 1), not in the control loop.
  void poll() {
    float v = read_raw_volts();
    if (isfinite(v) && v > 0.0f) filt_v_ += (v - filt_v_) * 0.1f;   // ~10-sample time constant
  }

  float pack_volts() const { return filt_v_; }
  float cell_volts() const { return filt_v_ * 0.5f; }               // 2S

  bool warn()     const { return filt_v_ < WYV_VBAT_WARN_V; }
  bool critical() const { return filt_v_ < WYV_VBAT_CRIT_V; }

  // Coarse state-of-charge from resting pack voltage. Only meaningful before the servos start
  // drawing -- under load the sag makes this pessimistic, which is the safe direction for a
  // pre-arm check.
  uint8_t percent() const {
    float c = cell_volts();
    if (c >= 4.15f) return 100;
    if (c <= 3.00f) return 0;
    return (uint8_t)((c - 3.00f) / (4.15f - 3.00f) * 100.0f);
  }

private:
  float read_raw_volts() const {
    int raw = analogRead(WYV_PIN_VBAT_ADC);
    float v_adc = (raw / 4095.0f) * WYV_ADC_VREF;
    return v_adc * WYV_VBAT_RATIO;
  }

  float filt_v_ = 0.0f;
};
