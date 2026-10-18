// GTR70E WYVERN — launch detect, camera gate, status LED/buzzer.
// =================================================================
#pragma once
#include <Arduino.h>
#include <math.h>
#include "imu_grv.h"

// ---------------------------------------------------------------------------------------------
// Launch detect: |a| > 2g sustained for >= 50 ms on the body IMU's accelerometer, per
// flowcharts/01_flight_state_machine.mermaid ("ARMED --> BOOST: |a|>2g"). The body sensor is a
// Bosch BNO085 (imu_grv.h), read via getEvent(VECTOR_ACCELEROMETER) rather than an SH2 report. A
// hardware inertial switch on GP37 (LAUNCH_IRQ) is OR'd in as a redundant trigger.
//
// H1 is a 14-pin debug/expansion connector, netlist-traced pin-by-pin: pin1/5=3V3,
// pin2/6/11/14=GND, pin3/4=QSPI flash signals (U1 pins 34/33, not general-purpose GPIO -- shared
// with the external flash chip, not usable here), pin7=GPIO37, pin8=GPIO36, pin9=GPIO35,
// pin10=GPIO34, pin12=VBUCK (the ~5V buck rail, power not signal), pin13=GPIO12. That leaves
// exactly 4 confirmed-usable general-purpose GPIOs on H1: 37, 36, 35, 34 (plus 12, spare -- see
// the RBF note below).
// LAUNCH_IRQ/CAM_EN/STATUS_LED/BUZZ below are assigned across GPIO37/36/35/34 in that order. Which
// signal rides which of the 4 pins is a firmware-side choice (the schematic doesn't name a
// function per pin); which 4 GPIOs are actually present and usable is netlist-confirmed.
// ---------------------------------------------------------------------------------------------
class LaunchDetect {
public:
  // 2.0 g / 50 ms sustain is chosen with margin against the vehicle's peak specific force
  // (3.70 g at 720 g liftoff, CONFLICTS.md section 5) -- comfortable headroom against
  // accelerometer noise, a slightly weak motor, or extra build mass, without being so low that
  // ground handling could falsely trigger launch detect.
  static constexpr float THRESHOLD_G = 2.0f;
  static constexpr unsigned long SUSTAIN_MS = 50;
  static constexpr uint8_t PIN_LAUNCH_IRQ = 37;  // H1 header pin7, confirmed-usable GPIO -- see file header

  void begin() {
    pinMode(PIN_LAUNCH_IRQ, INPUT_PULLUP);   // assumption: active-low inertial switch closes to GND
  }

  // accel_mag_g: |a| in g, sampled from the body IMU's accelerometer report. Call once per control
  // tick from core 0 (cheap: a comparison + a timer, no I2C/blocking work itself -- the accel
  // sample is collected by the existing IMU poll).
  bool update(float accel_mag_g, unsigned long now_ms) {
    if (latched_) return true;
    bool irq_active = (digitalRead(PIN_LAUNCH_IRQ) == LOW);
    if (accel_mag_g > THRESHOLD_G) {
      if (over_thresh_since_ms_ == 0) over_thresh_since_ms_ = now_ms;
      if (now_ms - over_thresh_since_ms_ >= SUSTAIN_MS) latched_ = true;
    } else {
      over_thresh_since_ms_ = 0;
    }
    if (irq_active) latched_ = true;   // redundant hardware trigger bypasses the software sustain window
    // FIXED 2026-08: this was `if (latched_) launch_ms_ = now_ms;` -- which re-stamped the launch
    // time on EVERY tick after the latch, so launch_time_ms() always returned "now" and any
    // t_flight computed from it would have been ~0 for the whole flight. The flight sketch happens
    // to latch its own g_launch_ms at the transition, which is why this never surfaced; it is still
    // wrong, and the accessor is public.
    if (latched_ && launch_ms_ == 0) launch_ms_ = now_ms;
    return latched_;
  }

  bool launched() const { return latched_; }
  unsigned long launch_time_ms() const { return launch_ms_; }
  void reset() { latched_ = false; over_thresh_since_ms_ = 0; launch_ms_ = 0; }

private:
  bool latched_ = false;
  unsigned long over_thresh_since_ms_ = 0;
  unsigned long launch_ms_ = 0;
};

// ---------------------------------------------------------------------------------------------
// Camera gate: drives CAM_EN (GP36, H1 header pin8, confirmed-usable GPIO -- see file header above)
// high to power the action camera, per Documentation/WYVERN_E4_Camera_Solution.md ("Power the i3
// cam ... gated by the FC arming switch so recording starts at power-on/arm" -- here gated by
// entry into ARMED instead of raw power-on, so the flight computer logs a precise timestamp of
// when the camera was told to start, for post-flight video/sensor-log alignment, exactly as the
// doc specifies).
// ---------------------------------------------------------------------------------------------
class CameraGate {
public:
  static constexpr uint8_t PIN_CAM_EN = 36;  // H1 header pin8, confirmed-usable GPIO -- see file header
  void begin() { pinMode(PIN_CAM_EN, OUTPUT); digitalWrite(PIN_CAM_EN, LOW); }
  void enable(unsigned long now_ms) {
    if (!enabled_) { digitalWrite(PIN_CAM_EN, HIGH); enabled_ = true; enabled_at_ms_ = now_ms; }
  }
  void disable() { digitalWrite(PIN_CAM_EN, LOW); enabled_ = false; }
  bool enabled() const { return enabled_; }
  unsigned long enabled_at_ms() const { return enabled_at_ms_; }
private:
  bool enabled_ = false;
  unsigned long enabled_at_ms_ = 0;
};

// ---------------------------------------------------------------------------------------------
// Status LED + buzzer: non-blocking pattern player (core 1 only -- must never call delay() since
// core 1 also services SD/WiFi; all patterns are driven from millis() comparisons).
// Patterns chosen to be distinguishable by ear/eye on the pad without a laptop:
//   BOOT_SELFTEST : slow single blink/beep (1 Hz)        -- self-test running
//   SELFTEST_FAIL : fast triple blink/beep burst (5 Hz)  -- do not arm
//   ARMED         : solid LED, no buzzer                 -- safe to leave the pad area
//   LOW_BATTERY   : double-blink/beep every 2 s          -- land/replace battery before next flight
//   FAULT         : continuous tone + solid LED          -- IMU vote fault or sensor dropout latched
// ---------------------------------------------------------------------------------------------
class StatusIndicator {
public:
  enum Pattern { BOOT_SELFTEST, SELFTEST_FAIL, ARMED, LOW_BATTERY, FAULT, OFF };
  // Named PIN_STATUS_LED, not PIN_LED: every Arduino-Pico board profile's pins_arduino.h #defines
  // PIN_LED as a preprocessor macro (e.g. 25u on rpipico2w, 64u on rpipico2w), not a constant.
  // A class member literally named PIN_LED gets textually replaced by the preprocessor before the
  // compiler ever sees it, producing a nonsensical redefinition and a hard compile error. GP35/GP34
  // below are discrete status LED/buzzer pins on the H1 debug/expansion header -- best-effort
  // assignment, unrelated to any board-profile onboard-LED macro.
  static constexpr uint8_t PIN_STATUS_LED = 35;  // H1 header pin9, confirmed-usable GPIO
  static constexpr uint8_t PIN_BUZZ = 34;        // H1 header pin10, confirmed-usable GPIO

  void begin() {
    pinMode(PIN_STATUS_LED, OUTPUT); pinMode(PIN_BUZZ, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW); digitalWrite(PIN_BUZZ, LOW);
  }
  void set(Pattern p) { if (p != pattern_) { pattern_ = p; phase_start_ms_ = millis(); } }

  // Call every loop1() iteration on core 1; non-blocking.
  void service(unsigned long now_ms) {
    unsigned long t = now_ms - phase_start_ms_;
    switch (pattern_) {
      case BOOT_SELFTEST: blink_(t, 500, 500); break;
      case SELFTEST_FAIL: blink_(t, 100, 100); break;
      case ARMED: digitalWrite(PIN_STATUS_LED, HIGH); digitalWrite(PIN_BUZZ, LOW); break;
      case LOW_BATTERY: double_blink_(t); break;
      case FAULT: digitalWrite(PIN_STATUS_LED, HIGH); digitalWrite(PIN_BUZZ, HIGH); break;
      case OFF: default: digitalWrite(PIN_STATUS_LED, LOW); digitalWrite(PIN_BUZZ, LOW); break;
    }
  }

private:
  void blink_(unsigned long t, unsigned long on_ms, unsigned long off_ms) {
    bool on = (t % (on_ms + off_ms)) < on_ms;
    digitalWrite(PIN_STATUS_LED, on); digitalWrite(PIN_BUZZ, on);
  }
  void double_blink_(unsigned long t) {
    unsigned long m = t % 2000;
    bool on = (m < 100) || (m >= 250 && m < 350);
    digitalWrite(PIN_STATUS_LED, on); digitalWrite(PIN_BUZZ, on);
  }
  Pattern pattern_ = OFF;
  unsigned long phase_start_ms_ = 0;
};
