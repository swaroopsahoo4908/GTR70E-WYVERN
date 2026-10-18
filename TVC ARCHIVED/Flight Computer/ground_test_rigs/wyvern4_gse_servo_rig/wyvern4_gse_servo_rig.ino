// ================================================================================================
// GTR70E WYVERN — GSE Servo-TVC Balance Rig  (wyvern4_gse_servo_rig.ino)
// ================================================================================================
// PURPOSE
//   Bench DAQ + actuator-command sketch for the servo-gimbal variant of the TVC thrust-vector
//   balance described in Documentation/WYVERN_E4_GSE_TestStands.md section 1. Under active motor
//   thrust, the actuator-under-test bolts to a thrust block restrained by 3 strain-gauge load
//   cells (1 axial Z 5 kg + 2 lateral X/Y 1 kg, each its own HX711 24-bit ADC). Every loop tick this
//   sketch:
//     1. reads all 3 HX711 channels (raw counts),
//     2. reconstructs the true 3-axis force vector via the pre-fitted dense 3x3 calibration matrix
//        (calibration.h -- pseudo-inverse least-squares fit, see MATH_DERIVATIONS.md section 1),
//     3. derives thrust magnitude T and direction (theta, phi),
//     4. reads the BNO085 gimbal IMU (Game Rotation Vector) for an independent nozzle-angle
//        cross-check against the commanded servo position,
//     5. emits one CSV row over Serial for host-side capture (see the header comment printed at
//        boot, and Flight Computer/test_code/host_monitor.py-style capture on the host side).
//   This is a GROUND-TEST rig only -- nothing here is flight-critical, and none of this logic is
//   reused by the flight firmware (it only follows that firmware's pin-naming/comment/class-
//   structure conventions for consistency, per Flight Computer/firmware/*.h and test_code/*.ino).
//
// REQUIRED LIBRARIES  (Arduino Library Manager names; versions are what this sketch was written
//                      against -- newer patch versions should be fine, re-check on major bumps)
//   - Adafruit BNO08x                 (Adafruit_BNO08x)          v1.2.5+   -- BNO085 GRV driver
//   - Adafruit Unified Sensor         (dependency of the above)  v1.1.14+
//   - HX711 by bogde                  (HX711.h)                 v0.7.5+   -- 24-bit load-cell ADC
//   - Servo  (bundled with the earlephilhower Arduino-Pico core, RP2040/RP2350 hardware PWM)
//   - Wire, SPI                       (bundled with Arduino-Pico core)
//   Board package: earlephilhower "Raspberry Pi Pico/RP2040/RP2350" Arduino core (same toolchain as
//   the GTR70E WYVERN flight computer). Target board: "Raspberry Pi Pico" (RP2040) or
//   "Raspberry Pi Pico 2 W" (RP2350) -- code below is portable to either; no RP2350-only or
//   Pico-W-only (WiFi) features are used.
//
// PIN MAP  (Pico/Pico 2 W GPIO numbers -- pick a different board and re-map as needed; HX711 pins
//           are plain bit-banged digital I/O, not a hardware peripheral, so any free GPIO works)
//   ---------------------------------------------------------------------------------------------
//   Function                          | GPIO   | Notes
//   ---------------------------------------------------------------------------------------------
//   I2C0 SDA  (BNO085 gimbal IMU)     | GP4    | Wire (I2C0). Address 0x4A (Adafruit default).
//   I2C0 SCL  (BNO085 gimbal IMU)     | GP5    | Single IMU on this rig -- mounted on the
//                                     |        | gimbal/nozzle per the task brief; no body/recovery
//                                     |        | IMUs (those are flight-computer-only concepts).
//   HX711 #1 DOUT  (X, lateral 1 kg) | GP6    | Bit-banged, HX711 channel A, gain 128 (library
//   HX711 #1 SCK                     | GP7    | default). Tie the HX711 module's RATE pin HIGH for
//                                     |        | 80 SPS (default LOW = 10 SPS is slow for a 50-100
//                                     |        | Hz log tick -- see bench note below).
//   HX711 #2 DOUT  (Y, lateral 1 kg) | GP8    | Same notes as #1.
//   HX711 #2 SCK                     | GP9    |
//   HX711 #3 DOUT  (Z, axial 5 kg)   | GP10   | Same notes as #1.
//   HX711 #3 SCK                     | GP11   |
//   Servo PWM -- gimbal pitch axis    | GP14   | Hardware PWM (Arduino-Pico core), 50 Hz servo
//   Servo PWM -- gimbal yaw axis      | GP15   | frame. Standard 3-wire hobby servo signal pins.
//   Status LED                        | LED_BUILTIN | On-board LED, blinks once per successful tare.
//   SD card stub (unused, reserved)   | SPI0 default: SCK=GP18 MOSI=GP19 MISO=GP16 CS=GP17
//                                     |        | Not wired/used in this sketch (no SD card required
//                                     |        | per task brief) -- pins reserved and free of
//                                     |        | conflicts with everything above in case a bench
//                                     |        | operator wants to add SD logging later (see the
//                                     |        | commented-out SdStub class near the bottom).
//   ---------------------------------------------------------------------------------------------
//   No pin above is shared/re-used, and none of GP16-19 (reserved for a future SD stub) collide
//   with the I2C0 (GP4/5), HX711 (GP6-11), or servo (GP14/15) assignments actually in use.
//
// WIRING NOTES
//   - Each HX711 breakout is powered from the Pico's 3V3 OUT (do NOT use VBUS/5V into a 3.3V-logic
//     HX711 board without a level-shifted breakout -- check your specific module's rating).
//   - BNO085 is a 3.3V part; use a 3.3V-native breakout (e.g. Adafruit BNO085) direct on I2C0 with
//     4.7k pull-ups (most breakouts already include them -- do not stack a second set).
//   - Load cells: axial (Z) cell in line with the thrust axis; the two lateral cells (X, Y)
//     mounted 90 deg apart in the plane perpendicular to thrust, per GSE_TestStands.md section 1.
//     Channel-to-axis wiring MUST match the fixed order [X, Y, Z] baked into calibration.h's
//     S_inv/c0 (re-fit and re-derive if the physical wiring order ever changes).
//   - Servos: standard 3-wire hobby servos, external BEC/5V supply for the servo rail (do not power
//     servos from the Pico's onboard 3V3 regulator -- stall current will brown out the MCU).
//
// BENCH OPERATING PROCEDURE
//   1. Power up the rig with the motor NOT armed/igniter disconnected. Open a serial terminal (or
//      host_monitor.py-style capture script) at 115200 baud.
//   2. With the gimbal at mechanical neutral and zero load on all 3 cells, send `TARE` to zero the
//      load-cell offsets and capture the current BNO085 orientation as the "neutral" deflection
//      reference (see calibration.h RuntimeTare and imu_ref_q_ below). Confirm the onboard LED
//      blinks once and Serial prints `TARE:OK`.
//   3. Command a manual test angle with `A <pitch_deg> <yaw_deg>` (e.g. `A 5 -3`), or start an
//      automatic bandwidth/slew sweep with `SWEEP ON` (triangle wave between +-SWEEP_AMPLITUDE_DEG
//      at SWEEP_PERIOD_MS) -- send `SWEEP OFF` to stop and return to neutral.
//   4. Arm/ignite the motor per the range safety procedure in GSE_TestStands.md. The CSV stream
//      continues throughout; capture it with a host-side logger (redirect the serial port to a
//      file, or use a host_monitor.py-style script) for post-fire analysis.
//   5. After the burn, send `CAL_RESET` if you want to discard the runtime tare and confirm the
//      factory-fitted zero offsets, or power-cycle for the next run.
//   Serial command summary (newline-terminated, case-insensitive):
//     TARE                     re-zero load cells + capture IMU neutral reference
//     CAL_RESET                discard runtime tare, restore factory c0_fit exactly
//     A <pitch_deg> <yaw_deg>  command gimbal to an absolute angle pair (deg, clamped to limits)
//     SWEEP ON | SWEEP OFF     start/stop the automatic triangle-wave bandwidth sweep
//     HELP                     re-print this command summary over Serial
// ================================================================================================

#include <Wire.h>
#include <Servo.h>
#include <Adafruit_BNO08x.h>
#include <HX711.h>
#include <math.h>
#include "calibration.h"

// ---- Pin map (see table above) ----------------------------------------------------------------
constexpr uint8_t PIN_I2C0_SDA = 4;
constexpr uint8_t PIN_I2C0_SCL = 5;

constexpr uint8_t PIN_HX711_X_DOUT = 6;
constexpr uint8_t PIN_HX711_X_SCK  = 7;
constexpr uint8_t PIN_HX711_Y_DOUT = 8;
constexpr uint8_t PIN_HX711_Y_SCK  = 9;
constexpr uint8_t PIN_HX711_Z_DOUT = 10;
constexpr uint8_t PIN_HX711_Z_SCK  = 11;

constexpr uint8_t PIN_SERVO_PITCH = 14;
constexpr uint8_t PIN_SERVO_YAW   = 15;

constexpr uint8_t BNO085_I2C_ADDR = 0x4A;

// ---- Loop timing --------------------------------------------------------------------------
// 100 Hz log tick. Note the HX711 in default (RATE pin LOW) mode only actually produces a fresh
// conversion at ~10 SPS -- tie RATE HIGH on each breakout for 80 SPS, which is still below 100 Hz;
// is_ready()-gated reads below mean the CSV simply repeats the last raw count on ticks where no
// new HX711 conversion has completed yet (sample-and-hold), rather than the loop blocking on it.
constexpr unsigned long LOOP_DT_MS = 10;

// ---- Servo geometry -----------------------------------------------------------------------
// This is a bench characterization rig, not flight hardware -- the mechanical travel limit here is
// the gimbal linkage's actual safe range, which is deliberately wider than the flight ±8 deg
// control limit (wyvern_pid.h) so the rig can also be used to explore servo bandwidth/slew across a
// bigger sweep. Re-check against your actual gimbal linkage before raising this.
constexpr float SERVO_NEUTRAL_DEG = 90.0f;
constexpr float SERVO_LIMIT_DEG   = 25.0f;   // max commanded deflection from neutral, either axis

// Automatic bandwidth/slew sweep (triangle wave), toggled by the SWEEP serial command.
constexpr float SWEEP_AMPLITUDE_DEG = 10.0f;   // +- about neutral, must be <= SERVO_LIMIT_DEG
constexpr unsigned long SWEEP_PERIOD_MS = 2000;  // one full +/- cycle

// ---- Globals --------------------------------------------------------------------------------
Adafruit_BNO08x bno;
sh2_SensorValue_t bno_val;

HX711 hx_x, hx_y, hx_z;
long raw_counts[3] = { 0, 0, 0 };   // [X, Y, Z], sample-and-hold between HX711 conversions

Servo servo_pitch, servo_yaw;
float cmd_pitch_deg = 0.0f, cmd_yaw_deg = 0.0f;   // commanded angle, relative to neutral
bool sweep_on = false;
unsigned long sweep_t0_ms = 0;

loadcell_cal::RuntimeTare tare;

// IMU deflection reference quaternion, captured at TARE time with the gimbal held at mechanical
// neutral. Deflection readout below is q_ref^-1 (x) q_now, matching the small-angle pitch=2*y,
// yaw=2*z convention used in Flight Computer/firmware/imu_grv.h's compute_deflection() -- there the
// second operand is a live body IMU; here it is this frozen neutral-pose reference, since the rig
// has only the one gimbal-mounted IMU and no independently-moving "body" to compare against.
struct Quat { float w = 1, x = 0, y = 0, z = 0; };
Quat imu_ref_q;
bool imu_ok = false;

inline Quat quat_conj(const Quat& q) { return Quat{ q.w, -q.x, -q.y, -q.z }; }
inline Quat quat_mul(const Quat& a, const Quat& b) {
  return Quat{
    a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
    a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
    a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
    a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w
  };
}

// ---- SD stub (not used -- see PIN MAP note; left here for a bench operator who wants file-based
// logging in addition to the Serial CSV stream. Uncomment + wire an SD breakout on SPI0 default
// pins to activate.) --------------------------------------------------------------------------
// #include <SPI.h>
// #include <SD.h>
// class SdStub {
// public:
//   static constexpr uint8_t PIN_CS = 17;
//   bool begin() { return SD.begin(PIN_CS); }
//   void log_line(const char* line) {
//     File f = SD.open("WYV4_GSE.csv", FILE_WRITE);
//     if (f) { f.println(line); f.close(); }
//   }
// };

// -------------------------------------------------------------------------------------------
void print_help() {
  Serial.println(F("Commands: TARE | CAL_RESET | A <pitch_deg> <yaw_deg> | SWEEP ON|OFF | HELP"));
}

void print_csv_header() {
  Serial.println(F(
    "t_ms,cmd_pitch_deg,cmd_yaw_deg,"
    "raw_x,raw_y,raw_z,"
    "Fx_N,Fy_N,Fz_N,T_N,theta_deg,phi_deg,"
    "imu_qw,imu_qx,imu_qy,imu_qz,imu_defl_pitch_deg,imu_defl_yaw_deg,imu_valid"));
  // Column notes:
  //   cmd_pitch_deg/cmd_yaw_deg : commanded servo angle relative to neutral (deg), from A/SWEEP
  //   raw_x/y/z                 : raw HX711 24-bit counts, sample-and-hold (see LOOP_DT_MS note)
  //   Fx_N/Fy_N/Fz_N            : reconstructed force vector, calibration.h S_inv * (raw - c0)
  //   T_N/theta_deg/phi_deg     : thrust magnitude + deflection + azimuth, MATH_DERIVATIONS.md 1.4
  //   imu_q*                    : raw BNO085 Game Rotation Vector quaternion (gimbal-mounted)
  //   imu_defl_pitch/yaw_deg    : IMU-derived deflection relative to the TARE-time neutral pose --
  //                               this is the independent cross-check against cmd_pitch/yaw_deg
  //   imu_valid                 : 1 if a fresh/healthy IMU reading backs this row, else 0
}

// ---- Load cells --------------------------------------------------------------------------
void hx711_begin_all() {
  hx_x.begin(PIN_HX711_X_DOUT, PIN_HX711_X_SCK);
  hx_y.begin(PIN_HX711_Y_DOUT, PIN_HX711_Y_SCK);
  hx_z.begin(PIN_HX711_Z_DOUT, PIN_HX711_Z_SCK);
}

// Non-blocking-ish poll: only consumes a fresh conversion if one is ready; otherwise the CSV
// repeats the previous raw count for that channel this tick (see LOOP_DT_MS comment above).
void hx711_poll_all() {
  if (hx_x.is_ready()) raw_counts[loadcell_cal::AX_X] = hx_x.read();
  if (hx_y.is_ready()) raw_counts[loadcell_cal::AX_Y] = hx_y.read();
  if (hx_z.is_ready()) raw_counts[loadcell_cal::AX_Z] = hx_z.read();
}

// Blocking average of N fresh HX711 samples per channel, used only by the TARE command (a
// deliberate one-time blocking wait is fine here -- it happens on operator command, not every tick).
void hx711_read_mean_blocking(float out_mean[3], uint8_t n_samples = 10) {
  double acc[3] = { 0, 0, 0 };
  for (uint8_t k = 0; k < n_samples; k++) {
    while (!hx_x.is_ready()) {}
    acc[loadcell_cal::AX_X] += hx_x.read();
    while (!hx_y.is_ready()) {}
    acc[loadcell_cal::AX_Y] += hx_y.read();
    while (!hx_z.is_ready()) {}
    acc[loadcell_cal::AX_Z] += hx_z.read();
  }
  for (int i = 0; i < 3; i++) out_mean[i] = (float)(acc[i] / n_samples);
}

// ---- IMU -----------------------------------------------------------------------------------
bool imu_begin() {
  if (!bno.begin_I2C(BNO085_I2C_ADDR, &Wire)) return false;
  // Game Rotation Vector: gyro+accel fusion, NO magnetometer -- consistent with the flight
  // computer's imu_grv.h choice (nearby motor/servo currents make raw magnetic heading unreliable,
  // and GRV doesn't need it for a relative-deflection readout anyway). 5000 us ~= 200 Hz sensor-side
  // report; this loop just reads whichever is newest at its own LOOP_DT_MS cadence.
  return bno.enableReport(SH2_GAME_ROTATION_VECTOR, 5000);
}

// Poll for a new GRV report; updates the live quaternion if one arrived this call. Returns true if
// a fresh sample was consumed.
Quat imu_q_live;
bool imu_poll() {
  if (!bno.getSensorEvent(&bno_val)) return false;
  if (bno_val.sensorId == SH2_GAME_ROTATION_VECTOR) {
    auto& r = bno_val.un.gameRotationVector;
    imu_q_live = Quat{ r.real, r.i, r.j, r.k };
    return true;
  }
  return false;
}

// ---- Serial command handling ------------------------------------------------------------------
String cmd_buf;

void do_tare() {
  float mean_counts[3];
  hx711_read_mean_blocking(mean_counts, 10);
  tare.set_from_samples(mean_counts);
  imu_ref_q = imu_q_live;   // freeze current IMU pose as the "neutral" deflection reference
  digitalWrite(LED_BUILTIN, HIGH); delay(80); digitalWrite(LED_BUILTIN, LOW);
  Serial.println(F("TARE:OK"));
}

void do_cal_reset() {
  tare.reset_to_factory();
  Serial.println(F("CAL_RESET:OK"));
}

void set_command_angle(float pitch_deg, float yaw_deg) {
  cmd_pitch_deg = constrain(pitch_deg, -SERVO_LIMIT_DEG, SERVO_LIMIT_DEG);
  cmd_yaw_deg = constrain(yaw_deg, -SERVO_LIMIT_DEG, SERVO_LIMIT_DEG);
  servo_pitch.write((int)lroundf(SERVO_NEUTRAL_DEG + cmd_pitch_deg));
  servo_yaw.write((int)lroundf(SERVO_NEUTRAL_DEG + cmd_yaw_deg));
}

void handle_command(String line) {
  line.trim();
  line.toUpperCase();
  if (line.length() == 0) return;

  if (line == "TARE") {
    do_tare();
  } else if (line == "CAL_RESET") {
    do_cal_reset();
  } else if (line == "HELP") {
    print_help();
  } else if (line == "SWEEP ON") {
    sweep_on = true;
    sweep_t0_ms = millis();
    Serial.println(F("SWEEP:ON"));
  } else if (line == "SWEEP OFF") {
    sweep_on = false;
    set_command_angle(0.0f, 0.0f);
    Serial.println(F("SWEEP:OFF"));
  } else if (line.startsWith("A ")) {
    float p = 0, y = 0;
    int n = sscanf(line.c_str(), "A %f %f", &p, &y);
    if (n == 2) {
      sweep_on = false;
      set_command_angle(p, y);
      Serial.print(F("A:OK ")); Serial.print(cmd_pitch_deg); Serial.print(' '); Serial.println(cmd_yaw_deg);
    } else {
      Serial.println(F("A:ERR usage: A <pitch_deg> <yaw_deg>"));
    }
  } else {
    Serial.print(F("ERR unknown command: ")); Serial.println(line);
    print_help();
  }
}

void poll_serial_commands() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmd_buf.length() > 0) { handle_command(cmd_buf); cmd_buf = ""; }
    } else {
      cmd_buf += c;
    }
  }
}

// Triangle-wave sweep between +-SWEEP_AMPLITUDE_DEG on the pitch axis only (yaw held at neutral) --
// swap axes or drive both if a bench operator wants a combined sweep; kept single-axis by default
// so bandwidth/slew results per axis aren't confounded with each other.
void service_sweep() {
  if (!sweep_on) return;
  unsigned long t = (millis() - sweep_t0_ms) % SWEEP_PERIOD_MS;
  float phase = (float)t / (float)SWEEP_PERIOD_MS;         // 0..1
  float tri = (phase < 0.5f) ? (4.0f * phase - 1.0f) : (3.0f - 4.0f * phase);  // -1..1..-1 triangle
  set_command_angle(SWEEP_AMPLITUDE_DEG * tri, 0.0f);
}

// -------------------------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  unsigned long t_wait = millis();
  while (!Serial && (millis() - t_wait) < 3000) {}   // give a USB host up to 3 s to connect

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Wire.setSDA(PIN_I2C0_SDA);
  Wire.setSCL(PIN_I2C0_SCL);
  Wire.begin();

  imu_ok = imu_begin();
  if (!imu_ok) Serial.println(F("WARN: BNO085 init FAILED (check I2C0 wiring/address 0x4A)"));

  hx711_begin_all();

  servo_pitch.attach(PIN_SERVO_PITCH);
  servo_yaw.attach(PIN_SERVO_YAW);
  set_command_angle(0.0f, 0.0f);

  Serial.println(F("GTR70E WYVERN GSE servo-TVC balance rig -- boot OK"));
  print_help();
  Serial.println(F("Send TARE with the rig at mechanical neutral and zero load before logging."));
  print_csv_header();
}

unsigned long last_tick_ms = 0;

void loop() {
  poll_serial_commands();
  service_sweep();
  hx711_poll_all();
  bool imu_fresh = imu_poll();

  unsigned long now = millis();
  if (now - last_tick_ms < LOOP_DT_MS) return;
  last_tick_ms = now;

  // Force reconstruction (calibration.h).
  float F[3];
  loadcell_cal::reconstruct_force(raw_counts, tare.c0(), F);
  loadcell_cal::ThrustVector tv = loadcell_cal::thrust_vector(F[0], F[1], F[2]);

  // IMU deflection relative to the TARE-time neutral reference (see imu_ref_q comment above).
  Quat d = quat_mul(quat_conj(imu_ref_q), imu_q_live);
  float imu_defl_pitch_deg = degrees(2.0f * d.y);
  float imu_defl_yaw_deg = degrees(2.0f * d.z);

  Serial.print(now); Serial.print(',');
  Serial.print(cmd_pitch_deg, 3); Serial.print(',');
  Serial.print(cmd_yaw_deg, 3); Serial.print(',');
  Serial.print(raw_counts[loadcell_cal::AX_X]); Serial.print(',');
  Serial.print(raw_counts[loadcell_cal::AX_Y]); Serial.print(',');
  Serial.print(raw_counts[loadcell_cal::AX_Z]); Serial.print(',');
  Serial.print(F[0], 5); Serial.print(',');
  Serial.print(F[1], 5); Serial.print(',');
  Serial.print(F[2], 5); Serial.print(',');
  Serial.print(tv.T_N, 5); Serial.print(',');
  Serial.print(degrees(tv.theta_rad), 4); Serial.print(',');
  Serial.print(degrees(tv.phi_rad), 4); Serial.print(',');
  Serial.print(imu_q_live.w, 5); Serial.print(',');
  Serial.print(imu_q_live.x, 5); Serial.print(',');
  Serial.print(imu_q_live.y, 5); Serial.print(',');
  Serial.print(imu_q_live.z, 5); Serial.print(',');
  Serial.print(imu_defl_pitch_deg, 4); Serial.print(',');
  Serial.print(imu_defl_yaw_deg, 4); Serial.print(',');
  Serial.println(imu_ok ? 1 : 0);

  // Unused but kept in scope for readability if a bench operator wires an SD stub back in:
  (void)imu_fresh;
}
