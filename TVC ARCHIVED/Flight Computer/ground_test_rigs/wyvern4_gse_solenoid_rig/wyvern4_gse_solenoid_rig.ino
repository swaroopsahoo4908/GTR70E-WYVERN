// =============================================================================================
// GTR70E WYVERN — Ground-Test TVC-Balance Rig: Magnetic-Solenoid Gimbal Variant
// =============================================================================================
// PURPOSE
//   Bench DAQ + actuation sketch for the solenoid-actuated 2-axis TVC gimbal ground-test stand
//   (WYVERN_E4_GSE_TestStands.md section 1). Under active thrust it measures the full thrust
//   vector (magnitude + direction) from the 3-axis load-cell balance shared with the servo-rig
//   sibling, and reads gimbal attitude from a BNO085 IMU mounted on the gimbal. It also exposes a
//   serial-commanded PWM duty interface to drive the 4 solenoids (2 opposing per axis) through
//   IRF520 MOSFET driver modules. This is a GROUND rig only (bench DAQ) -- not flight-critical.
//   Gimbal deflection is taken from the 3-axis load balance (thrust-vector theta/phi) and cross-
//   checked against the BNO085 attitude; the load-cell calibration math is derived and validated
//   offline (see MATH_DERIVATIONS.md section 1 and phase0_math_constants.json). Firmware here
//   implements those exact constants -- it does not re-derive or re-fit anything on-device.
//
//   NOTE: the earlier VL53L4CD ToF ring + Kalman-fusion tilt estimator has been removed from the
//   design; gimbal deflection now comes from the load balance + BNO085 (no ToF sensors).
//
// REQUIRED LIBRARIES (Arduino Library Manager names; versions this sketch was checked against --
// newer patch releases should be API-compatible)
//   - Arduino-Pico core (earlephilhower/arduino-pico)      >= 4.0   (RP2040 / RP2350 "Pico 2 W")
//   - HX711 (bogde/HX711)                                  >= 0.7.5
//   - Adafruit BNO08x (adafruit/Adafruit_BNO08x)           >= 1.2.4
//   - Adafruit BusIO                                       (BNO08x dependency)
//   - Wire, SPI (bundled with Arduino-Pico core)
//
// PIN MAP (Raspberry Pi Pico / Pico 2 W, Arduino-Pico core, GPxx = RP2040/RP2350 GPIO number)
//   ---------------------------------------------------------------------------------------
//   Function                          | Pin(s)         | Notes
//   ---------------------------------------------------------------------------------------
//   I2C0 (Wire) SDA / SCL             | GP4 / GP5      | BNO085 (0x4A).
//   BNO085 I2C address                | 0x4A           | Game Rotation Vector + gyro reports.
//   HX711 #1 (axial Z, 5 kg cell) DT   | GP10           |
//   HX711 #1 (axial Z, 5 kg cell) SCK  | GP11           |
//   HX711 #2 (lateral X, 1 kg cell) DT | GP12           |
//   HX711 #2 (lateral X, 1 kg cell) SCK| GP13           |
//   HX711 #3 (lateral Y, 1 kg cell) DT | GP14           |
//   HX711 #3 (lateral Y, 1 kg cell) SCK| GP15           |
//   Solenoid PWM: PITCH (+) / IRF520   | GP16           | Pitch-up solenoid gate drive.
//   Solenoid PWM: PITCH (-) / IRF520   | GP17           | Pitch-down solenoid gate drive.
//   Solenoid PWM: YAW (+)   / IRF520   | GP18           | Yaw-positive solenoid gate drive.
//   Solenoid PWM: YAW (-)   / IRF520   | GP19           | Yaw-negative solenoid gate drive.
//   ---------------------------------------------------------------------------------------
//   (GP6/GP7/GP8, formerly the ToF XSHUT lines, are now free/spare.)
//
//   *** FLYBACK DIODE WARNING (real hardware hazard) ***
//   Each of the 4 solenoid coils is an inductive load. A 1N4007 flyback (freewheeling) diode
//   MUST be wired in reverse bias directly across EVERY solenoid coil (cathode to the +12V/coil
//   supply side, anode to the IRF520 drain/coil-return side) -- across the coil itself, as close
//   to the coil terminals as practical. Per the BOM, both the 1N4007s and the IRF520 modules are
//   already stocked; the diode is a passive component this firmware cannot drive or verify, but
//   omitting it lets the coil's collapsing field fly the MOSFET drain voltage to a large negative
//   spike on every PWM turn-off, which reliably kills IRF520s (and can back-feed transient current
//   that disturbs the load-cell/HX711 readings on the same bench supply). Verify all 4 flyback
//   diodes are installed and oriented correctly BEFORE the first PWM command is ever sent -- this
//   is a wiring-inspection step, not something this sketch can self-check.
//
// BENCH OPERATING PROCEDURE
//   1. Power up the rig (Pico USB or bench 5V; solenoid 12V supply switched separately/last).
//      Inspect all 4 flyback diodes before applying 12V to the solenoids -- see warning above.
//   2. Reset/boot the Pico; watch the Serial monitor for the boot-complete line.
//   3. With the gimbal at rest and NO thrust applied, send `TARE` to zero (re-tare) all 3 HX711
//      channels against the current no-load reading.
//   4. With the gimbal held at its known-neutral (zero-deflection) position, send `ZERO` to latch
//      the current BNO085 attitude as the pitch/yaw zero-reference.
//   5. Command a solenoid duty sweep via `SET,<pitch_pct>,<yaw_pct>` (each in [-100, 100]; sign
//      selects which of the two opposing solenoids on that axis is driven, magnitude is PWM duty).
//   6. Capture the CSV stream from Serial at 115200 baud on the host (column header printed once
//      at startup) for post-run analysis -- bandwidth, slew, overshoot, steady-state (theta, phi)
//      vs commanded duty, matching the same host-capture convention as the servo rig.
// =============================================================================================

#include <Arduino.h>
#include <Wire.h>
#include <HX711.h>
#include <Adafruit_BNO08x.h>
#include <string.h>  // strcmp/strncmp, used by handle_command()
#include <stdio.h>   // sscanf, used by handle_command() to parse SET,<pitch_pct>,<yaw_pct>
#include <math.h>    // asinf/atan2f for the quaternion -> pitch/yaw conversion

#include "calibration.h"

// ---------------------------------------------------------------------------------------------
// Pin map (see top-of-file table)
// ---------------------------------------------------------------------------------------------
static constexpr uint8_t PIN_I2C0_SDA = 4;
static constexpr uint8_t PIN_I2C0_SCL = 5;

static constexpr uint8_t PIN_HX711_DT[3] = { 10, 12, 14 };   // {Z, X, Y}, matches calibration.h order
static constexpr uint8_t PIN_HX711_SCK[3] = { 11, 13, 15 };  // {Z, X, Y}

static constexpr uint8_t PIN_SOLENOID_PITCH_POS = 16;
static constexpr uint8_t PIN_SOLENOID_PITCH_NEG = 17;
static constexpr uint8_t PIN_SOLENOID_YAW_POS = 18;
static constexpr uint8_t PIN_SOLENOID_YAW_NEG = 19;

static constexpr uint8_t BNO085_I2C_ADDR = 0x4A;

// PWM carrier frequency for the solenoid drive. Kept well below the audible-whine range some
// solenoids exhibit at high PWM frequencies, and low enough that IRF520 switching losses stay
// small, while still being fast enough for smooth average-force control over the sweep.
static constexpr uint32_t SOLENOID_PWM_HZ = 1000;
static constexpr int PWM_RESOLUTION_BITS = 8;  // analogWrite range 0-255
static constexpr int PWM_MAX = (1 << PWM_RESOLUTION_BITS) - 1;

// 50 Hz DAQ tick.
static constexpr uint32_t TICK_PERIOD_MS = 20;

// ---------------------------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------------------------
HX711 hx711[3];            // {Z, X, Y}
Adafruit_BNO08x bno08x;

// Last-known-good sensor caches (held between updates so a single dropped/late reading doesn't
// zero out the whole CSV row).
float last_gyro_pitch_rad_s = 0.0f, last_gyro_yaw_rad_s = 0.0f;
float last_quat_w = 1.0f, last_quat_x = 0.0f, last_quat_y = 0.0f, last_quat_z = 0.0f;

// BNO085 attitude zero reference (latched by the `ZERO` serial command per the bench procedure).
float att_zero_pitch_rad = 0.0f;
float att_zero_yaw_rad = 0.0f;

// Commanded solenoid duty, percent in [-100, 100]; sign selects which of the axis' two opposing
// solenoids is driven, magnitude is PWM duty. Updated by the `SET,<pitch_pct>,<yaw_pct>` command.
float cmd_pitch_pct = 0.0f;
float cmd_yaw_pct = 0.0f;

uint32_t next_tick_ms = 0;
uint32_t tick_count = 0;

char serial_buf[64];
uint8_t serial_len = 0;

// ---------------------------------------------------------------------------------------------
// Quaternion -> gimbal pitch/yaw (radians). Standard aerospace intrinsic decomposition of the
// Game Rotation Vector quaternion; pitch about the sensor +X (local pitch) axis, yaw about +Y.
// Re-map here if the physical BNO085 mount on the gimbal differs.
// ---------------------------------------------------------------------------------------------
void quat_to_pitch_yaw(float w, float x, float y, float z, float& pitch_rad, float& yaw_rad) {
  float sp = 2.0f * (w * y - z * x);
  sp = constrain(sp, -1.0f, 1.0f);
  pitch_rad = asinf(sp);
  yaw_rad = atan2f(2.0f * (w * z + x * y), 1.0f - 2.0f * (y * y + z * z));
}

// ---------------------------------------------------------------------------------------------
// Solenoid drive: apply a signed percent command to the pair of opposing PWM pins on one axis.
// Only one of the pair is ever driven at a time (the other held at 0) -- these are single-
// direction pull solenoids, not a push-pull H-bridge, so there is no "both on" case to guard.
// ---------------------------------------------------------------------------------------------
void drive_axis(float pct, uint8_t pin_pos, uint8_t pin_neg) {
  pct = constrain(pct, -100.0f, 100.0f);
  int duty_pos = 0, duty_neg = 0;
  if (pct >= 0.0f) {
    duty_pos = (int)(pct * 0.01f * PWM_MAX + 0.5f);
  } else {
    duty_neg = (int)((-pct) * 0.01f * PWM_MAX + 0.5f);
  }
  analogWrite(pin_pos, duty_pos);
  analogWrite(pin_neg, duty_neg);
}

// ---------------------------------------------------------------------------------------------
// Serial command handling: TARE, ZERO, SET,<pitch_pct>,<yaw_pct>
// ---------------------------------------------------------------------------------------------
void handle_command(char* line) {
  if (strcmp(line, "TARE") == 0) {
    for (int i = 0; i < 3; i++) hx711[i].tare(10);
    Serial.println(F("# TARE done"));
    return;
  }
  if (strcmp(line, "ZERO") == 0) {
    float p, y;
    quat_to_pitch_yaw(last_quat_w, last_quat_x, last_quat_y, last_quat_z, p, y);
    att_zero_pitch_rad = p;
    att_zero_yaw_rad = y;
    Serial.println(F("# ZERO done (BNO085 attitude reference latched)"));
    return;
  }
  if (strncmp(line, "SET,", 4) == 0) {
    float p = 0.0f, y = 0.0f;
    if (sscanf(line + 4, "%f,%f", &p, &y) == 2) {
      cmd_pitch_pct = constrain(p, -100.0f, 100.0f);
      cmd_yaw_pct = constrain(y, -100.0f, 100.0f);
      Serial.print(F("# SET pitch="));
      Serial.print(cmd_pitch_pct);
      Serial.print(F(" yaw="));
      Serial.println(cmd_yaw_pct);
    } else {
      Serial.println(F("# SET parse error, expected SET,<pitch_pct>,<yaw_pct>"));
    }
    return;
  }
  Serial.print(F("# unrecognized command: "));
  Serial.println(line);
}

void poll_serial_commands() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (serial_len > 0) {
        serial_buf[serial_len] = '\0';
        handle_command(serial_buf);
        serial_len = 0;
      }
    } else if (serial_len < sizeof(serial_buf) - 1) {
      serial_buf[serial_len++] = c;
    }
  }
}

// ---------------------------------------------------------------------------------------------
// setup()
// ---------------------------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  uint32_t t_wait = millis();
  while (!Serial && (millis() - t_wait) < 3000) { delay(10); }  // don't hang forever if no host

  Wire.setSDA(PIN_I2C0_SDA);
  Wire.setSCL(PIN_I2C0_SCL);
  Wire.begin();
  Wire.setClock(400000);

  analogWriteFreq(SOLENOID_PWM_HZ);
  analogWriteRange(PWM_MAX);
  pinMode(PIN_SOLENOID_PITCH_POS, OUTPUT);
  pinMode(PIN_SOLENOID_PITCH_NEG, OUTPUT);
  pinMode(PIN_SOLENOID_YAW_POS, OUTPUT);
  pinMode(PIN_SOLENOID_YAW_NEG, OUTPUT);
  analogWrite(PIN_SOLENOID_PITCH_POS, 0);
  analogWrite(PIN_SOLENOID_PITCH_NEG, 0);
  analogWrite(PIN_SOLENOID_YAW_POS, 0);
  analogWrite(PIN_SOLENOID_YAW_NEG, 0);

  for (int i = 0; i < 3; i++) {
    hx711[i].begin(PIN_HX711_DT[i], PIN_HX711_SCK[i]);
  }

  if (!bno08x.begin_I2C(BNO085_I2C_ADDR, &Wire)) {
    Serial.println(F("# BNO085 begin_I2C FAILED"));
  } else {
    // Game Rotation Vector (gyro+accel fusion, no magnetometer -- same rationale as the flight
    // computer's imu_grv.h: a rocket motor's fields make raw magnetic heading unusable) plus a
    // calibrated gyroscope report for the rate columns.
    bno08x.enableReport(SH2_GAME_ROTATION_VECTOR, 5000);   // 5000 us ~= 200 Hz sensor-side
    bno08x.enableReport(SH2_GYROSCOPE_CALIBRATED, 5000);
  }

  Serial.println(F("# GTR70E WYVERN solenoid TVC-balance rig -- boot complete."));
  Serial.println(F("# Commands: TARE | ZERO | SET,<pitch_pct>,<yaw_pct>"));
  Serial.println(
    F("t_ms,raw_z_counts,raw_x_counts,raw_y_counts,Fz_N,Fx_N,Fy_N,thrust_N,theta_deg,phi_deg,"
      "gyro_pitch_dps,gyro_yaw_dps,bno_pitch_deg,bno_yaw_deg,"
      "quat_w,quat_x,quat_y,quat_z,cmd_pitch_pct,cmd_yaw_pct"));

  next_tick_ms = millis();
}

// ---------------------------------------------------------------------------------------------
// Per-tick sensor polling helper
// ---------------------------------------------------------------------------------------------
void poll_bno085() {
  sh2_SensorValue_t v;
  // Drain whatever reports are queued; keep the most recent of each type this tick.
  while (bno08x.getSensorEvent(&v)) {
    if (v.sensorId == SH2_GAME_ROTATION_VECTOR) {
      auto& r = v.un.gameRotationVector;
      last_quat_w = r.real;
      last_quat_x = r.i;
      last_quat_y = r.j;
      last_quat_z = r.k;
    } else if (v.sensorId == SH2_GYROSCOPE_CALIBRATED) {
      auto& g = v.un.gyroscope;
      // Mounting assumption (verify against the physical BNO085 orientation on the gimbal):
      // sensor +X axis = gimbal local pitch axis, sensor +Y axis = local yaw axis. Re-map if the
      // physical mount differs.
      last_gyro_pitch_rad_s = g.x;
      last_gyro_yaw_rad_s = g.y;
    }
  }
}

// ---------------------------------------------------------------------------------------------
// loop()
// ---------------------------------------------------------------------------------------------
void loop() {
  poll_serial_commands();
  poll_bno085();

  uint32_t now = millis();
  if ((int32_t)(now - next_tick_ms) < 0) return;  // not yet time for the next 50 Hz tick
  next_tick_ms += TICK_PERIOD_MS;
  tick_count++;

  // 1. Load cells: raw counts -> force -> thrust vector (calibration.h, shared model with the
  // servo rig). hx711[i].read() blocks briefly until that channel's HX711 has a fresh 24-bit
  // conversion; at the 3 channels' native ~10-80 SPS this is well within the 20 ms tick budget.
  // The thrust-vector theta/phi IS the gimbal-deflection measurement of record for this rig.
  long raw_counts[3];
  for (int i = 0; i < 3; i++) {
    raw_counts[i] = hx711[i].is_ready() ? hx711[i].read() : 0;
  }
  float F_N[3];  // reconstructed force {Fz, Fx, Fy} in Newtons; named F_N (not F) to avoid any
                 // visual confusion with Arduino's F() flash-string macro used elsewhere in this file
  calib::counts_to_force(raw_counts, F_N);
  calib::ThrustVector tv = calib::thrust_vector(F_N);

  // 2. BNO085 attitude -> gimbal pitch/yaw, zero-referenced per the ZERO command. This is the
  // independent cross-check on the load-balance deflection above (no ToF ring in the design).
  float bno_pitch_rad, bno_yaw_rad;
  quat_to_pitch_yaw(last_quat_w, last_quat_x, last_quat_y, last_quat_z, bno_pitch_rad, bno_yaw_rad);
  bno_pitch_rad -= att_zero_pitch_rad;
  bno_yaw_rad -= att_zero_yaw_rad;

  // 3. Solenoid drive: apply the currently commanded duty every tick (re-applying a steady
  // command is harmless and keeps drive state immune to a single missed command line).
  drive_axis(cmd_pitch_pct, PIN_SOLENOID_PITCH_POS, PIN_SOLENOID_PITCH_NEG);
  drive_axis(cmd_yaw_pct, PIN_SOLENOID_YAW_POS, PIN_SOLENOID_YAW_NEG);

  // 4. CSV log line -- column order matches the header printed once in setup().
  Serial.print(now); Serial.print(',');
  Serial.print(raw_counts[0]); Serial.print(',');
  Serial.print(raw_counts[1]); Serial.print(',');
  Serial.print(raw_counts[2]); Serial.print(',');
  Serial.print(F_N[0], 4); Serial.print(',');
  Serial.print(F_N[1], 4); Serial.print(',');
  Serial.print(F_N[2], 4); Serial.print(',');
  Serial.print(tv.T_N, 4); Serial.print(',');
  Serial.print(tv.theta_deg, 4); Serial.print(',');
  Serial.print(tv.phi_deg, 4); Serial.print(',');
  Serial.print(degrees(last_gyro_pitch_rad_s), 4); Serial.print(',');
  Serial.print(degrees(last_gyro_yaw_rad_s), 4); Serial.print(',');
  Serial.print(degrees(bno_pitch_rad), 4); Serial.print(',');
  Serial.print(degrees(bno_yaw_rad), 4); Serial.print(',');
  Serial.print(last_quat_w, 5); Serial.print(',');
  Serial.print(last_quat_x, 5); Serial.print(',');
  Serial.print(last_quat_y, 5); Serial.print(',');
  Serial.print(last_quat_z, 5); Serial.print(',');
  Serial.print(cmd_pitch_pct, 2); Serial.print(',');
  Serial.println(cmd_yaw_pct, 2);

  // ---------------------------------------------------------------------------------------
  // STUB: optional on-board SD logging (ground rig has no card by default; host-side Serial
  // CSV capture, per the bench operating procedure, is the primary data path). If a card is
  // added later, mirror the flight computer's sd_logger.h pattern here: buffer LogFrame-style
  // rows and flush in bursts rather than every tick.
  // ---------------------------------------------------------------------------------------
}
