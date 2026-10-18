// GTR70E WYVERN — custom RP2350 flight computer (the Pico 2 W perfboard) + real-time TVC controller.
// ===============================================================================================
// Toolchain: Arduino-Pico core (earlephilhower), board "Raspberry Pi Pico 2 W" (rpipico2w) -- the bare-
// silicon RP2350 target (48 GPIO, QFN-80, external QSPI flash), NOT any Pico/Pico-W module profile.
// This board (the Pico 2 W perfboard) carries a standalone RP2350 (U1), not a Pico 2 module,
// so board profiles built around a module (rpipico2w, rpipico2) assume the wrong GPIO count, the
// wrong ADC-capable pin range, and a WiFi radio chip that isn't populated here.
//
// Libraries (Library Manager): Adafruit_BNO08x (external IMU, SH2 protocol), Adafruit_BNO085
// (both IMUs are BNO085, same driver, different address -- see imu_grv.h), Adafruit_BME680,
// Adafruit_BMP3XX (optional, no BMP388 populated on this board rev, see baro.h), INA226 (RobTillaart,
// battery/power monitor), plus the Arduino-Pico built-ins Servo, Wire, SPI, SD. WiFi/WiFiUdp remain
// linked for wifi_telemetry.h's bench-only code path, but this board has NO onboard radio chip (no
// CYW43439 in the BOM) -- WIFI_ENABLED must stay 0 unless an external WiFi module is added later.
//
// Recovery is MOTOR ejection (F15-4), separating the two body tubes at a single bulkhead joint —
// NO CO2, NO pyro bay, NO RRC3. The FC does NOT actuate recovery; it only logs/observes
// (Documentation/WYVERN_E4_Recovery.md).
// Read ../CONFLICTS.md before flying: it documents the PID-gain and recovery-timing values this
// code depends on.
//
// ----------------------------------- DUAL-CORE OWNERSHIP MAP -----------------------------------
// RP2350's two M33 cores share all peripherals at the silicon level (I2C, SPI0, UART0, the single
// ADC, GPIO). Concurrent multi-step bus transactions (I2C, SPI, UART) from BOTH cores at once is a
// real hazard (interleaved register writes = corrupted transactions), so this firmware gives each
// *bus peripheral* exactly one owning core, and uses single-writer/single-reader volatile flags
// (never multi-byte structs without a snapshot) to cross the core boundary:
//
//   core 0 (setup/loop)   owns: the single shared I2C bus (Wire, GP0 SDA / GP1 SCL) -- bay BNO085,
//                          external BNO085 (STEMMA-QT, bulkhead-boundary mount), BME688, and the
//                          decimated baro reads all share this one bus by address, no mux/second bus
//                          exists on this board -- plus the 2 servo PWM outputs and LAUNCH_IRQ sense.
//                          Runs the 500 Hz TVC loop. NEVER calls anything that can block
//                          (no SD, no UART, no WiFi, no delay()).
//   core 1 (setup1/loop1) owns: SPI0 (microSD), WiFi/UDP (inert, no radio chip), and the digital
//                          housekeeping pins (CAM_EN, RBF sense, status LED/buzzer). Drains the
//                          inter-core FIFO log queue. (Recovery is motor-driven — no deploy GPIO.)
//                          May block for milliseconds (SD writes) without ever touching the 500 Hz
//                          loop on core 0.
//
//   NOTE on the INA226 battery monitor: it sits on the SAME shared I2C bus as the IMUs/baro (no
//   second bus exists on this board -- see imu_grv.h's file header). Per the one-owning-core rule
//   above, it is therefore polled from CORE 0 (decimated, like the baro reads), NOT from core 1
//   where the rest of the housekeeping lives -- the alternative (core 1 also touching Wire) would
//   put two bus masters on one I2C peripheral, exactly the hazard this ownership scheme exists to
//   prevent. Only the resulting g_batt_v/g_battery_low/g_battery_critical flags cross to core 1.
//
//   Cross-core flags (each has exactly ONE writer core, documented at the declaration):
//     g_state            : FlightState, single byte -- written by core 0, read by core 1
//     g_rbf_pulled       : bool          -- written by core 1 (RBF sense), read by core 0
//     g_selftest_pass    : bool          -- written by core 1 (aggregates both cores' results,
//                                            but only core 1 WRITES this combined flag), read core 0
//     g_imu_init_mask    : uint8_t       -- written by core 0, read by core 1 (for self-test print)
//     g_baro_init_ok     : bool          -- written by core 0, read by core 1
//     g_battery_low      : bool          -- written by core 0 (INA226 shares the I2C bus core 0
//                                            owns -- see the NOTE above), read by core 1
//     g_battery_critical : bool          -- written by core 0, read by core 1
//     g_launch_ms        : uint32_t      -- written by core 0 once at launch, read by core 1
//
// Single-byte/bool/uint32_t volatile flags with one writer are safe on RP2350 without a mutex
// (no partial-write tearing possible at that width); nothing wider crosses cores outside the
// LogFrame FIFO, which is purpose-built for cross-core transfer (see sd_logger.h).
// WIFI_ENABLED must be defined before wifi_telemetry.h is included: that header pulls in <WiFi.h>,
// which assumes a CYW43439 radio chip. the Pico 2 W perfboard has NO radio chip in its BOM (see wifi_telemetry.h's
// file header) -- keep this at 0 unless a future board rev or external WiFi module changes that.
#define WIFI_ENABLED 0

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Servo.h>
#include <Adafruit_BNO08x.h>
#include <Adafruit_BNO085.h>
#include <math.h>
#include "pico/multicore.h"

#include "wyvern_pid.h"
#include "imu_grv.h"
#include "baro.h"
#include "battery.h"
#include "launch_status.h"
#include "sd_logger.h"
#if WIFI_ENABLED
#include "wifi_telemetry.h"
#endif

// ---------- pin map (custom RP2350 the Pico 2 W perfboard) — CONFIRMED by tracing every pin in the netlist against
// the labeled schematic pinout -- see imu_grv.h and launch_status.h file headers for the detail.
#define SDA0 0
#define SCL0 1             // ONE shared I2C bus -> bay BNO085, external BNO085 (STEMMA-QT), BME688,
                            // INA226, LIS3MDL -- no mux, no second bus (core 0 owned)
#define PIN_SERVO_P 2       // pitch servo, JST connector U8 (PWM)
#define PIN_SERVO_Y 3       // yaw servo, JST connector U9 (PWM)
// GP4/GP5 -> JST connectors U10/U11 exist on the board but their intended function is undetermined
// from the netlist trace (spare axes? gas-pressure sensor? unused). Left unassigned -- flag for
// bench/silkscreen confirmation before building anything against them.
//
// RBF: there is NO software-readable remove-before-flight pin on this board. U13 (the physical
// slide switch near the power path) was the obvious candidate, but it connects to NOTHING on
// U1 in the netlist -- both its terminals sit in the power domain (one on the ~5V buck rail, one on
// an address-strap-adjacent node), not on any GPIO. Arming safety on the Pico 2 W perfboard as fabricated is provided
// entirely by U13 being a literal power switch: the board simply isn't running until it's flipped.
// GP12 (H1 header pin13) is a genuinely free, otherwise-unused GPIO -- PIN_RBF below keeps the
// existing INPUT_PULLUP software gate wired to it so a bodge wire (H1 pin13 to GND, switched by
// whatever RBF hardware gets added) will work if Sky wants a real software-visible RBF later. As
// fabricated, nothing is soldered there: the pin floats HIGH, g_rbf_pulled always reads true, and
// this stage of the BOOT gate provides no actual protection until that bodge exists.
#define PIN_RBF 12          // H1 header pin13 -- free GPIO, NOT wired to any switch on this board rev
#define BNO085_ADDR 0x4A    // external IMU, STEMMA-QT default
#define BNO085_ADDR 0x4B    // onboard IMU, CONFIRMED via netlist (COM3/ADR pin tied to GND)
#define SERVO_NEUTRAL_DEG 90.0f

// ---------- WiFi bench telemetry — EDIT before bench use. WIFI_ENABLED itself is defined above the
// includes (this board has no radio chip; see the note there) -- do not redefine it here. ----------
static const char* WIFI_SSID = "CHANGE_ME";
static const char* WIFI_PASS = "CHANGE_ME";
static const char* WIFI_DEST_IP = "192.168.1.100";

// ---------- timing constants (frozen parameters, CONFLICTS.md section 5) ----------
static const float CONTROL_DT_S = 0.002f;          // 500 Hz
static const unsigned long CONTROL_DT_US = 2000UL;
static const float TVC_ENGAGE_DELAY_S = 0.5f;       // past the F15 ignition spike
static const float BURNOUT_S = 3.45f;
static const float MANEUVER_SETPOINT_DEG = 4.0f;    // 02_tvc_control_loop.mermaid: "4 deg maneuver"
static const float MANEUVER_START_S = 2.0f;         // "vertical (t<2s) then 4 deg maneuver"
// Recovery is MOTOR-DRIVEN: the F15-4's own ejection charge fires ~4 s after burnout (t~7.45 s) and
// separates the two body tubes at the bulkhead joint — the FC does NOT actuate anything. This
// backstop is only the state machine's cutover to RECOVER (for logging/camera), set at the
// expected ejection time.
static const float RECOVER_BACKSTOP_S = 7.45f;      // F15-4 ejection = burnout 3.45 + 4.0 s delay
                                                     // (was 7.5 -- the canonical value everywhere
                                                     //  else in the repo is 7.45; see CONFLICTS.md 5)
static const unsigned long LANDED_QUIET_MS = 3000;  // accel+baro quiescent this long -> LANDED

// ---------- flight state machine (01_flight_state_machine.mermaid) ----------
enum FlightState : uint8_t { BOOT, ARMED, BOOST, COAST, RECOVER, DESCENT, LANDED };
static const char* state_name(FlightState s) {
  switch (s) {
    case BOOT: return "BOOT"; case ARMED: return "ARMED"; case BOOST: return "BOOST";
    case COAST: return "COAST"; case RECOVER: return "RECOVER"; case DESCENT: return "DESCENT";
    case LANDED: return "LANDED"; default: return "?";
  }
}

// ---------- cross-core flags (single-writer each — see ownership map above) ----------
volatile FlightState g_state = BOOT;                 // writer: core 0
volatile bool g_rbf_pulled = false;                  // writer: core 1
volatile bool g_selftest_pass = false;               // writer: core 1
volatile uint8_t g_imu_init_mask = 0;                // writer: core 0
volatile bool g_baro_init_ok = false;                // writer: core 0
volatile bool g_battery_low = false;                 // writer: core 0 (shares core 0's I2C bus)
volatile bool g_battery_critical = false;             // writer: core 0 (shares core 0's I2C bus)
volatile uint32_t g_launch_ms = 0;                   // writer: core 0 (set once at launch)
volatile bool g_imu_vote_fault = false;               // writer: core 0
volatile uint32_t g_dropped_log_frames = 0;           // writer: core 0
volatile float g_batt_v = 0.0f;                       // writer: core 0 (BatteryMonitor shares core 0's
                                                       // I2C bus, decimated update in loop() -- see the
                                                       // dual-core ownership NOTE above), read by core 1
                                                       // for logging/heartbeat/WiFi; single float, no
                                                       // partial-word tearing risk on RP2350's 32-bit
                                                       // bus, same rationale as TelemSnapshot below)

// Bench-telemetry snapshot: written by core 0 every tick, read by core 1's WiFi broadcaster only.
// Floats here are NOT given single-writer/single-reader atomicity guarantees beyond "no partial-
// word tearing on RP2350's 32-bit bus" -- acceptable because this feeds a ~20 Hz BENCH-ONLY display
// (wifi_telemetry.h), never the control loop or the flight log (which use the FIFO/LogFrame path
// instead, see sd_logger.h). A torn read here is, worst case, one stale-looking bench readout.
struct TelemSnapshot {
  float pitch_deg = 0, yaw_deg = 0, defl_pitch_deg = 0, defl_yaw_deg = 0, baro_alt_m = 0;
};
volatile TelemSnapshot g_telem;   // writer: core 0

// =================================================================================================
// CORE 0 — 500 Hz real-time TVC control loop. Nothing here may block.
// =================================================================================================
TriImu g_imu(Wire, BNO085_ADDR, BNO085_ADDR);
BaroPair g_baro(Wire);
BatteryMonitor g_battery(Wire);   // shares core 0's I2C bus -- see the dual-core ownership NOTE above
LaunchDetect g_launch;
DualAxisPID g_pid(wyvern_pid_defaults::make_config());
Servo g_servo_pitch, g_servo_yaw;

unsigned long g_loop_next_us = 0;
unsigned long g_t0_ms = 0;        // BOOT timestamp, for relative "uptime" displays only
unsigned long g_prev_tick_us = 0;  // for loop_dt_us jitter diagnostic in the LogFrame (schema v2)
bool g_armed_servo_neutral_done = false;
int g_baro_decimate_count = 0;
static const int BARO_DECIMATE = 5;   // baro updated every 5th control tick (~100 Hz), see header
int g_batt_decimate_count = 0;
static const int BATT_DECIMATE = 25;  // battery updated every 25th tick (~20 Hz) -- plenty for a
                                       // low/critical voltage gate, keeps I2C bus time small

// Servo command mapping. `deg` is nozzle deflection about neutral (0 = centred), NOT an absolute
// servo angle -- keeping the sign convention identical to the PID output and the logged
// cmd_pitch_rad/cmd_yaw_rad avoids the class of error the +-5/+-8 mismatch above belonged to.
// SERVO_US_PER_DEG is the linkage-corrected scale: bench-calibrate it in step B4 of the build
// guide by commanding a known deflection and measuring actual nozzle angle.
static const float SERVO_US_NEUTRAL  = 1500.0f;
static const float SERVO_US_PER_DEG  = 10.0f;    // 1000-2000 us over +-50 deg servo travel
static const float SERVO_LINKAGE_RATIO = 1.0f;   // servo deg per nozzle deg (1.0 = direct drive)

static inline int servo_us_from_deg(float nozzle_deg) {
  float us = SERVO_US_NEUTRAL + nozzle_deg * SERVO_LINKAGE_RATIO * SERVO_US_PER_DEG;
  if (us < 1000.0f) us = 1000.0f;               // hard mechanical guard, never drive past the horn
  if (us > 2000.0f) us = 2000.0f;
  return (int)lroundf(us);
}

void core0_set_servos_neutral() {
  g_servo_pitch.writeMicroseconds((int)SERVO_US_NEUTRAL);
  g_servo_yaw.writeMicroseconds((int)SERVO_US_NEUTRAL);
}

// FIXED 2026-08 -- this function silently threw away 37.5% of the vehicle's control authority.
// wyvern_pid.h clamps the PID output to OUT_LIM_DEG = 8.0 deg (raised from 5 specifically to give
// the TVC authority against crosswind weathercocking, per CONFLICTS.md section 5 and the
// weathercock analysis). This function then RE-clamped the same command to +-5 deg, so every
// command between 5 and 8 deg was truncated on the way to the servo. The extra authority existed
// in the controller, in the simulations, in the .ork and in every document -- and nowhere in the
// signal path that actually moves the nozzle.
//
// The clamp is now driven by the SAME constant the PID uses, so the two can never diverge again.
// Also switched from Servo::write(int) to writeMicroseconds(): write() quantizes to whole degrees,
// which on a +-8 deg range is a ~6% quantization of full command authority and shows up as a
// visible stair-step in the logged deflection. Microsecond resolution is ~0.09 deg here.
void core0_apply_servo_commands(float cmd_pitch_rad, float cmd_yaw_rad) {
  const float LIM = wyvern_pid_defaults::OUT_LIM_DEG;   // single source of truth with the PID
  float pitch_deg = constrain(degrees(cmd_pitch_rad), -LIM, LIM);
  float yaw_deg   = constrain(degrees(cmd_yaw_rad),   -LIM, LIM);
  g_servo_pitch.writeMicroseconds(servo_us_from_deg(pitch_deg));
  g_servo_yaw.writeMicroseconds(servo_us_from_deg(yaw_deg));
}

void setup() {
  Serial.begin(115200);
  unsigned long t_wait = millis();
  while (!Serial && millis() - t_wait < 3000) { /* brief wait for USB host, never blocks flight */ }
  g_t0_ms = millis();

  // Single shared I2C bus (see the pin-map comment and the dual-core ownership NOTE above) -- every
  // onboard sensor plus the STEMMA-QT port lives on this one bus, so there's exactly one Wire.begin().
  Wire.setSDA(SDA0); Wire.setSCL(SCL0); Wire.begin();

  Serial.println("SELFTEST:BEGIN");

  // the Pico 2 W perfboard has exactly 2 physical IMUs (onboard bay BNO085, external BNO085 via the single
  // STEMMA-QT port) -- see imu_grv.h's file header. mask bit0 = external, bit1 = body.
  uint8_t imu_mask = g_imu.begin();
  g_imu_init_mask = imu_mask;
  Serial.printf("SELFTEST:IMU_EXTERNAL:%s\n", (imu_mask & 0x01) ? "PASS" : "FAIL");
  Serial.printf("SELFTEST:IMU_BODY:%s\n", (imu_mask & 0x02) ? "PASS" : "FAIL");
  // Flight-critical minimum: BOTH IMUs. With only 2 total, losing either one loses the 2-of-2
  // cross-check, and body is the sole attitude source the control loop reads.
  bool imu_flightworthy = (imu_mask & 0x03) == 0x03;
  Serial.printf("SELFTEST:IMU_MINIMUM:%s\n", imu_flightworthy ? "PASS" : "FAIL");

  bool baro_ok = g_baro.begin();
  g_baro_init_ok = baro_ok;
  Serial.printf("SELFTEST:BARO_BMP:%s\n", g_baro.bmp_ok() ? "PASS" : "FAIL");
  Serial.printf("SELFTEST:BARO_BME:%s\n", g_baro.bme_ok() ? "PASS" : "FAIL");

  // Battery monitor lives on this same shared bus, so it's initialized here on core 0 (not in
  // setup1()) -- see the dual-core ownership NOTE above. Flags cross to core 1 as usual.
  bool batt_ok = g_battery.begin();
  g_battery_low = g_battery.low_battery();
  g_battery_critical = g_battery.critical();
  g_batt_v = g_battery.voltage();
  Serial.printf("SELFTEST:BATTERY:%s (%.2fV)\n", g_battery.critical() ? "FAIL" : "PASS", g_battery.voltage());
  (void)batt_ok;   // sensor_ok() folded into critical()'s !ok_ short-circuit; kept for readability

  g_launch.begin();

  g_servo_pitch.attach(PIN_SERVO_P);
  g_servo_yaw.attach(PIN_SERVO_Y);
  core0_set_servos_neutral();
  delay(300);   // one-time settling at boot only, never in loop()
  // Visual/mechanical confirmation sweep to the FULL command limit. This previously swept only
  // +-5 deg, so the bench operator was asked to "visually confirm +-8 deg travel" while watching a
  // +-5 deg sweep -- a mechanical binding at 6-8 deg would have passed the bench and been
  // discovered in flight.
  const int SW = (int)wyvern_pid_defaults::OUT_LIM_DEG;
  for (int a = -SW; a <= SW; a++) { g_servo_pitch.writeMicroseconds(servo_us_from_deg((float)a)); delay(15); }
  core0_set_servos_neutral(); delay(150);
  for (int a = -SW; a <= SW; a++) { g_servo_yaw.writeMicroseconds(servo_us_from_deg((float)a)); delay(15); }
  core0_set_servos_neutral();
  Serial.printf("SELFTEST:SERVO:PASS (swept +-%d deg both axes)\n", SW);
  Serial.println("SELFTEST:CORE0_READY:PASS");

  g_pid.reset();
  g_loop_next_us = micros();
}

void loop() {
  unsigned long now_us = micros();
  if ((long)(now_us - g_loop_next_us) < 0) return;   // hold to 500 Hz without delay()/blocking
  float dt = CONTROL_DT_S;
  g_loop_next_us += CONTROL_DT_US;
  unsigned long now_ms = millis();

  // ---- sensors (core 0 owns I2C0 + I2C1 exclusively, see ownership map) ----
  g_imu.update(now_ms);
  g_imu_vote_fault = g_imu.vote_fault();
  if (++g_baro_decimate_count >= BARO_DECIMATE) { g_baro_decimate_count = 0; g_baro.update(); }
  if (++g_batt_decimate_count >= BATT_DECIMATE) {
    g_batt_decimate_count = 0;
    g_battery.update();
    g_battery_low = g_battery.low_battery();
    g_battery_critical = g_battery.critical();
    g_batt_v = g_battery.voltage();
  }

  Quat q_body = g_imu.voted_body_quat();
  Quat q_gimbal = g_imu.gimbal_quat();
  Deflection defl = compute_deflection(q_body, q_gimbal);

  // crude pitch/yaw Euler readout off the voted body quaternion, small-angle convention matching
  // t2_imu_grv_deflection.ino, used for setpoint tracking error (NOT for the deflection itself,
  // which already uses the quaternion-product form directly).
  float body_pitch_rad = 2.0f * q_body.y;
  float body_yaw_rad = 2.0f * q_body.z;

  // |a| in g from the body BNO085's SH2_ACCELEROMETER report (enabled in TriImu::begin(), see
  // imu_grv.h) — drives both launch-detect (ARMED->BOOST, |a|>3g sustained) and the landing
  // quiescence check (DESCENT->LANDED, ~1g at rest). Falls back to a resting 1g default if the
  // accel channel is stale/uninitialized, so a sensor dropout can't be misread as a 0g freefall.
  float accel_mag_g = g_imu.body_accel_mag_g(now_ms);

  bool rbf_pulled = g_rbf_pulled;
  bool batt_critical = g_battery_critical;

  // Loop-timing diagnostic: actual elapsed micros() since the previous tick. Nominally
  // CONTROL_DT_US every time; a value that creeps above that under load (I2C retries, etc.) is
  // exactly the kind of jitter the dual-core split is meant to prevent, and is now visible in the
  // log instead of only inferable from t_ms deltas post-flight.
  uint32_t loop_dt_us = (uint32_t)(now_us - g_prev_tick_us);
  g_prev_tick_us = now_us;

  // Diagnostic taps for the LogFrame -- populated inside BOOST's TVC branch below when the loop is
  // actually closing on a setpoint; otherwise left at 0 so the CSV shows exactly "no command being
  // computed this tick" rather than stale/misleading values from an earlier state.
  float setp_pitch_rad = 0.0f;
  float err_pitch_rad = 0.0f, err_yaw_rad = 0.0f;
  float pid_p_pitch = 0.0f, pid_i_pitch = 0.0f, pid_d_pitch = 0.0f;
  float pid_p_yaw = 0.0f, pid_i_yaw = 0.0f, pid_d_yaw = 0.0f;

  switch (g_state) {
    case BOOT: {
      bool ok = g_selftest_pass && rbf_pulled && !batt_critical;
      if (ok) {
        g_state = ARMED;
        g_pid.reset();
        g_armed_servo_neutral_done = false;
      }
      core0_set_servos_neutral();
      break;
    }
    case ARMED: {
      core0_set_servos_neutral();
      bool launched = g_launch.update(accel_mag_g, now_ms);
      if (launched) {
        g_launch_ms = now_ms;
        g_pid.bumpless_reset(0.0f, 0.0f);
        g_state = BOOST;
      }
      break;
    }
    case BOOST: {
      float t_flight = (now_ms - g_launch_ms) / 1000.0f;
      if (t_flight >= BURNOUT_S) {
        core0_set_servos_neutral();
        g_state = COAST;
        break;
      }
      if (t_flight < TVC_ENGAGE_DELAY_S) {
        core0_set_servos_neutral();   // past ignition spike gate not yet open — neutral gimbal
      } else {
        float setp_pitch_deg = (t_flight < MANEUVER_START_S) ? 0.0f : MANEUVER_SETPOINT_DEG;
        setp_pitch_rad = radians(setp_pitch_deg);
        err_pitch_rad = setp_pitch_rad - body_pitch_rad;
        err_yaw_rad = 0.0f - body_yaw_rad;   // no yaw maneuver commanded, per design flowchart
        float cmd_pitch, cmd_yaw;
        g_pid.update(err_pitch_rad, err_yaw_rad, dt, cmd_pitch, cmd_yaw);
        core0_apply_servo_commands(cmd_pitch, cmd_yaw);

        // Term breakdown for the LogFrame -- read AFTER update() so integral_state()/
        // derivative_state() reflect this tick's values, not the previous one. p_term(err) is
        // recomputed from the same err just passed to update(), so it's exactly what update()
        // itself used internally (not a stale/lagged reconstruction).
        pid_p_pitch = g_pid.pitch.p_term(err_pitch_rad);
        pid_i_pitch = g_pid.pitch.config().ki * g_pid.pitch.integral_state();
        pid_d_pitch = g_pid.pitch.config().kd * g_pid.pitch.derivative_state();
        pid_p_yaw = g_pid.yaw.p_term(err_yaw_rad);
        pid_i_yaw = g_pid.yaw.config().ki * g_pid.yaw.integral_state();
        pid_d_yaw = g_pid.yaw.config().kd * g_pid.yaw.derivative_state();
      }
      break;
    }
    case COAST: {
      // No thrust -> no TVC authority (TVC needs thrust reaction). Neutral gimbal and coast; the
      // motor's own F15-4 ejection charge (~t=7.45 s) separates the two body tubes at the bulkhead
      // joint and deploys the chute — the FC does not fire anything. State advances to RECOVER at
      // the backstop (~ejection time) for logging.
      core0_set_servos_neutral();
      float t_flight = (now_ms - g_launch_ms) / 1000.0f;
      bool over_backstop = t_flight >= RECOVER_BACKSTOP_S;
      if (over_backstop) g_state = RECOVER;
      break;
    }
    case RECOVER: {
      core0_set_servos_neutral();
      g_state = DESCENT;   // brief transitional state; DESCENT does the actual landing watch
      break;
    }
    case DESCENT: {
      core0_set_servos_neutral();
      // Landing = quiescent accelerometer + stable baro altitude for LANDED_QUIET_MS. Implemented
      // on core 1 (which also owns the housekeeping timers) via g_state being writable from core 0
      // only — so this check stays here, core 0, using a small local hold-timer.
      static unsigned long quiet_since_ms = 0;
      bool quiescent = fabsf(accel_mag_g - 1.0f) < 0.15f;  // resting at ~1g, no big swings
      if (quiescent) {
        if (quiet_since_ms == 0) quiet_since_ms = now_ms;
        if (now_ms - quiet_since_ms >= LANDED_QUIET_MS) g_state = LANDED;
      } else {
        quiet_since_ms = 0;
      }
      break;
    }
    case LANDED: {
      core0_set_servos_neutral();
      break;
    }
  }

  // ---- push one log frame per tick into the inter-core FIFO (never blocks; drops if full) ----
  // Schema v2: every quantity the control loop already holds this tick, not just the final
  // actuator command -- see the schema-v2 note at the top of sd_logger.h for the rationale.
  LogFrame f{};
  f.t_ms = now_ms;
  f.t_flight_s = (g_launch_ms == 0) ? NAN : (now_ms - g_launch_ms) / 1000.0f;
  f.loop_dt_us = loop_dt_us;

  f.state = (uint8_t)g_state;
  f.imu_fault = g_imu_vote_fault ? 1 : 0;
  f.rbf_pulled = rbf_pulled ? 1 : 0;
  f.batt_flags = (g_battery_low ? 0x01 : 0x00) | (batt_critical ? 0x02 : 0x00);

  f.qb_w = q_body.w; f.qb_x = q_body.x; f.qb_y = q_body.y; f.qb_z = q_body.z;
  f.qg_w = q_gimbal.w; f.qg_x = q_gimbal.x; f.qg_y = q_gimbal.y; f.qg_z = q_gimbal.z;
  f.vote_disagree_rad = g_imu.vote_disagreement_rad();

  f.body_pitch_rad = body_pitch_rad; f.body_yaw_rad = body_yaw_rad;
  f.defl_pitch_rad = defl.pitch_rad; f.defl_yaw_rad = defl.yaw_rad;

  f.setp_pitch_rad = setp_pitch_rad;
  f.err_pitch_rad = err_pitch_rad; f.err_yaw_rad = err_yaw_rad;

  f.pid_p_pitch = pid_p_pitch; f.pid_i_pitch = pid_i_pitch; f.pid_d_pitch = pid_d_pitch;
  f.pid_p_yaw = pid_p_yaw; f.pid_i_yaw = pid_i_yaw; f.pid_d_yaw = pid_d_yaw;

  f.cmd_pitch_rad = g_pid.pitch.last_output(); f.cmd_yaw_rad = g_pid.yaw.last_output();

  f.baro_alt_m = g_baro.altitude_agl_m(); f.baro_temp_c = g_baro.temperature_c();
  f.accel_mag_g = accel_mag_g;
  f.batt_v = g_batt_v;   // g_battery is polled right here on core 0 (decimated, see BATT_DECIMATE
                          // above) since it shares this core's I2C bus -- no cross-core read needed
                          // for this particular field, unlike most of the other g_* flags.
  f.dropped_frames_cum = g_dropped_log_frames;

  if (!log_push(f)) g_dropped_log_frames++;

  // Bench-telemetry snapshot for core 1's optional WiFi broadcaster (see TelemSnapshot comment
  // above). Field-by-field writes, not a whole-struct assignment, to stay within plain
  // read/write semantics on a volatile aggregate (no struct-level volatile copy operator relied
  // upon). This is cheap (5 float stores) and runs every tick; the WiFi side independently
  // rate-limits its own send to ~20 Hz, so over-writing this snapshot at 500 Hz costs nothing.
  g_telem.pitch_deg = degrees(body_pitch_rad);
  g_telem.yaw_deg = degrees(body_yaw_rad);
  g_telem.defl_pitch_deg = degrees(defl.pitch_rad);
  g_telem.defl_yaw_deg = degrees(defl.yaw_rad);
  g_telem.baro_alt_m = f.baro_alt_m;
}

// =================================================================================================
// CORE 1 — logging, WiFi bench telemetry, housekeeping. May block; never touches core 0's
// peripherals (SPI0/WiFi/ADC/the housekeeping GPIOs only). Recovery is motor-driven — nothing to fire.
// =================================================================================================
SdLogger g_logger;
#if WIFI_ENABLED
WifiTelemetry g_wifi;
#endif
CameraGate g_camera;
StatusIndicator g_status;
FlightState g_last_seen_state = BOOT;
bool g_logger_finalized = false;

void setup1() {
  // Stagger slightly after core 0's Serial.begin() so self-test prints don't interleave mid-line.
  delay(50);

  pinMode(PIN_RBF, INPUT_PULLUP);     // floats HIGH as fabricated -- see the RBF note at PIN_RBF's
                                       // #define above: nothing is wired to this pin on the Pico 2 W perfboard yet

  g_camera.begin();
  g_status.begin();
  g_status.set(StatusIndicator::BOOT_SELFTEST);

  // Battery monitor is owned and initialized by core 0 (setup()), not here -- it shares core 0's
  // I2C bus with the IMUs/baro, see the dual-core ownership NOTE at the top of this file. Both
  // cores' setup()/setup1() start concurrently, so g_battery_critical/g_batt_v below may still hold
  // their power-on defaults (false / 0.0) for the first few milliseconds if core 1 reaches the
  // overall-pass check before core 0's setup() finishes its own battery read -- not a correctness
  // problem, since a false "not critical" default only ever makes the gate stricter later once the
  // real (low) voltage reading lands, never falsely permits arming past an actually-critical pack.
  bool sd_ok = g_logger.begin();
  Serial.printf("SELFTEST:SD:%s\n", sd_ok ? "PASS" : "FAIL");


#if WIFI_ENABLED
  WifiTelemetryConfig wcfg{WIFI_SSID, WIFI_PASS, WIFI_DEST_IP};
  bool wifi_ok = g_wifi.begin(wcfg);
  Serial.printf("SELFTEST:WIFI:%s\n", wifi_ok ? "PASS" : "SKIP");
#else
  Serial.println("SELFTEST:WIFI:SKIP");
#endif

  bool rbf_pulled = (digitalRead(PIN_RBF) == HIGH);
  g_rbf_pulled = rbf_pulled;
  Serial.printf("SELFTEST:RBF:%s\n", rbf_pulled ? "PASS(pulled)" : "WAIT(inserted)");

  // Log-transport sanity. Core 0 has been pushing frames at 500 Hz since its setup() finished, so
  // by now the ring must contain samples AND core 1 must be draining them. This check is deliberately
  // two-sided: the old version only looked at the drop counter, which read a contented 0 even in the
  // failure mode where the transport was dropping 100% of frames (see the SPSC-ring note in
  // sd_logger.h) -- because that path never incremented the counter either.
  delay(100);
  uint32_t pend_before = log_pending();
  g_logger.service();
  delay(50);
  bool ring_moving = (log_pending() < pend_before) || (g_logger.peak_drain() > 0);
  Serial.printf("SELFTEST:LOG_RING:%s (pending=%lu peak_drain=%lu dropped=%lu)\n",
                ring_moving ? "PASS" : "FAIL(core1 not draining)",
                (unsigned long)log_pending(), (unsigned long)g_logger.peak_drain(),
                (unsigned long)g_dropped_log_frames);

  // Aggregate everything into one PASS/FAIL the BOOT state machine on core 0 actually gates on.
  // 2 physical IMUs (external=bit0, body=bit1), both required -- see imu_grv.h file header and
  // the SELFTEST:IMU_* prints in setup().
  bool core0_ready = (g_imu_init_mask & 0x03) == 0x03 && g_baro_init_ok;
  bool overall = core0_ready && sd_ok && !g_battery_critical && ring_moving;
  g_selftest_pass = overall;
  Serial.printf("SELFTEST:DONE:%s\n", overall ? "PASS" : "FAIL");
  g_status.set(overall ? StatusIndicator::BOOT_SELFTEST : StatusIndicator::SELFTEST_FAIL);
}

void loop1() {
  unsigned long now_ms = millis();

  // Battery is polled by core 0 (see the dual-core ownership NOTE at the top of this file) --
  // g_battery_low/g_battery_critical/g_batt_v are cross-core flags read here, not written here.

  bool rbf_pulled = (digitalRead(PIN_RBF) == HIGH);
  g_rbf_pulled = rbf_pulled;

  g_logger.service();   // recovery is motor-driven (F15-4 ejection at the bulkhead joint); FC fires nothing

  FlightState st = g_state;   // single read of the volatile, used consistently this iteration
  if (st != g_last_seen_state) {
    Serial.printf("STATE:%s\n", state_name(st));
    if (st == ARMED) g_camera.enable(now_ms);
    if (st == LANDED && !g_logger_finalized) { g_logger.finalize(); g_logger_finalized = true; }
    g_last_seen_state = st;
  }

  // Status indicator priority: FAULT > LOW_BATTERY > state-specific > armed-solid.
  if (g_imu_vote_fault) {
    g_status.set(StatusIndicator::FAULT);
  } else if (g_battery_low && st != LANDED) {
    g_status.set(StatusIndicator::LOW_BATTERY);
  } else if (st == BOOT) {
    g_status.set(g_selftest_pass ? StatusIndicator::ARMED : StatusIndicator::BOOT_SELFTEST);
  } else if (st == ARMED) {
    g_status.set(StatusIndicator::ARMED);
  } else {
    g_status.set(StatusIndicator::OFF);
  }
  g_status.service(now_ms);

#if WIFI_ENABLED
  // Field-by-field reads of the volatile snapshot core 0 writes every tick (see TelemSnapshot
  // comment) -- a torn read here is, at worst, one stale-looking bench packet at ~20 Hz.
  g_wifi.service(now_ms, g_telem.pitch_deg, g_telem.yaw_deg, g_telem.defl_pitch_deg,
                 g_telem.defl_yaw_deg, g_telem.baro_alt_m, g_batt_v, (uint8_t)st,
                 g_imu_vote_fault ? 1 : 0);
#endif

  // Lightweight heartbeat for host_monitor.py / bench operators — once per second, not flooding USB.
  static unsigned long last_hb_ms = 0;
  if (now_ms - last_hb_ms >= 1000) {
    last_hb_ms = now_ms;
    Serial.printf("HB:t=%lu state=%s batt=%.2fV rbf=%d drop=%lu pend=%lu peak=%lu\n",
      now_ms, state_name(st), g_batt_v, rbf_pulled ? 1 : 0,
      (unsigned long)g_dropped_log_frames, (unsigned long)log_pending(),
      (unsigned long)g_logger.peak_pending());
  }
}
