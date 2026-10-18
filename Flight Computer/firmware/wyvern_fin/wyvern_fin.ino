// =================================================================================================
// GTR70E WYVERN -- fin-controlled ascent, flight firmware.
//
//   core 0 : BNO085 attitude (400 Hz gyro) + ADXL375 high-g axial channel (Wire1), vertical-channel
//            fusion, state machine, 200 Hz control, authority manoeuvre, fin mixer + servo PWM.
//                                                        Never touches SPI, radio, the SD card or Wire.
//   core 1 : BME688 baro (25 Hz, async, Wire), battery, LoRa downlink/uplink,
//            microSD logging, buzzer.                    Never touches the servos or Wire1.
//   Hand-off: seqlocked structs in shared_state.h.
//
// Safety model
//   * Fins only move in flight if the rocket was ARMed over the uplink on the pad. Unarmed, it
//     logs and transmits but holds neutral fins (the airframe is passively stable at >= 0.9 cal).
//   * Fins go neutral and stay neutral on: tilt > 30 deg, IMU stale > 20 ms, battery < 6.4 V,
//     or the authority monitor finding a reversed control derivative right after rail exit.
//   * The uplink is pad-only; it is closed at launch detect.
// =================================================================================================
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_BME680.h>
#include "fc_config.h"
#include "shared_state.h"
#include "attitude.h"
#include "fin_mixer.h"
#include "controller.h"
#include "highg.h"
#include "telemetry.h"
#include "logger.h"

SeqBox<NavState>  g_nav;
SeqBox<CtrlState> g_ctrl;
SeqBox<AuxState>  g_aux;

// ----------------------------------------------------------------------------------- core 0 objects
static Attitude att;
static FinMixer mixer;
static AxisPID pid_a(1.0f), pid_b(WYV_AXIS_B_SCALE);
static AuthorityMonitor auth_a;
static ManeuverSeq man;
static HighG highg;

static FlightState state = ST_BOOT;
static uint32_t t_launch = 0, t_over = 0, t_land = 0;
static bool armed = false, ctrl_enabled = false, auth_abort = false, tilt_abort = false;
static float h = 0, vz = 0;          // fused vertical channel
static float h_ground_baro = NAN;

static float air_density(float alt) { float T = 288.15f - 0.0065f * alt; return 101325.f * powf(T / 288.15f, 5.2559f) / (287.05f * T); }

void setup() {
  Serial.begin(115200);
  WYV_I2C.setSDA(WYV_PIN_SDA); WYV_I2C.setSCL(WYV_PIN_SCL);
  WYV_I2C.begin(); WYV_I2C.setClock(WYV_I2C_HZ);
  mixer.begin(); mixer.neutral(); mixer.update(1.0f);
  state = ST_SELFTEST;
  bool imu_ok = att.begin();
  highg.begin();                                       // optional: without it the BNO's 8 g clip stands
  uint32_t t0 = millis();
  while (millis() - t0 < 1500) att.poll(micros());     // let the GRV settle
  att.zero_pad();
  state = imu_ok ? ST_PAD : ST_FAULT;
}

void loop() {
  static uint32_t last_ctrl_us = 0;
  uint32_t now_us = micros(), now = millis();
  att.poll(now_us);
  if (now_us - last_ctrl_us < 1000000UL / WYV_CTRL_HZ) return;
  float dt = (now_us - last_ctrl_us) * 1e-6f; last_ctrl_us = now_us;
  if (dt > 0.05f) dt = 0.005f;

  AuxState aux; g_aux.read(aux);
  static uint8_t last_zero = 0;
  if (aux.cmd_zero != last_zero) { last_zero = aux.cmd_zero; if (state == ST_PAD) att.zero_pad(); }
  armed = aux.cmd_arm && (state == ST_PAD || state == ST_ARMED);

  // ---- attitude, rates, specific force
  float ta, tb, tt; att.tilts(ta, tb, tt);
  const float* w = att.rates(); const float* a = att.accel();
  Q q = att.quat();

  // ---- vertical channel: world-frame accel from the body specific force, complementary w/ baro
  // Axial specific force: BNO085 below ~7 g, ADXL375 above (the BNO clips at 8 g; the F42-4T
  // ignition spike reaches ~8.2 g, an F67-6W would hold 11-12 g). The ADXL's offset is learned against the BNO on the pad.
  float a_ax = a[2], a_hg = NAN; bool use_hg = false;
  if (highg.read(a_hg)) {
    if (state <= ST_ARMED && fabsf(a[2]) > 7.0f && fabsf(a[2]) < 12.0f) highg.learn_bias(a[2]);   // standing on the rail
    if (fabsf(a[2]) > WYV_HIGHG_SWITCH_G * 9.80665f || att.accel_mag_g() > WYV_HIGHG_SWITCH_G) { a_ax = a_hg; use_hg = true; }
  }
  float r20 = 2 * (q.x * q.z - q.w * q.y), r21 = 2 * (q.y * q.z + q.w * q.x), r22 = 1 - 2 * (q.x * q.x + q.y * q.y);
  float az_world = r20 * a[0] + r21 * a[1] + r22 * a_ax - 9.80665f;
  if (state < ST_BOOST_RAIL) az_world = 0;                       // pad: hold zero, kill drift
  vz += az_world * dt; h += vz * dt;
  if (!isnan(aux.baro_alt_m)) {
    if (isnan(h_ground_baro)) h_ground_baro = aux.baro_alt_m;
    float hb = aux.baro_alt_m - h_ground_baro;
    float kh = (state == ST_BOOST_RAIL || state == ST_CONTROL) ? 0.5f : 2.0f;  // trust IMU under thrust
    float e = hb - h; h += kh * e * dt; vz += 0.5f * kh * kh * e * dt;
  }
  float v_air = fabsf(vz) / fmaxf(cosf(tt), 0.3f);
  float qbar = 0.5f * air_density(h) * v_air * v_air;

  // ---- state machine
  switch (state) {
    case ST_PAD:
    case ST_ARMED:
      state = armed ? ST_ARMED : ST_PAD;
      if (att.accel_mag_g() > WYV_LAUNCH_G) { if (!t_over) t_over = now; if (now - t_over >= WYV_LAUNCH_SUSTAIN_MS) {
          t_launch = now - WYV_LAUNCH_SUSTAIN_MS; att.go_inertial(); state = ST_BOOST_RAIL; ctrl_enabled = armed; vz = 0; h = 0; } }
      else t_over = 0;
      break;
    case ST_BOOST_RAIL:
      if (now - t_launch >= WYV_RAIL_CLEAR_MS) { state = ST_CONTROL; pid_a.reset(); pid_b.reset(); auth_a.reset(); }
      break;
    case ST_CONTROL:
      if (now - t_launch > WYV_BURN_MS && qbar < WYV_CTRL_END_QBAR) state = ST_COAST;
      break;
    case ST_COAST:
      if (vz < 0 && now - t_launch > WYV_BURN_MS) state = ST_DESCENT;
      break;
    case ST_DESCENT:
      if (fabsf(vz) < 0.5f && h < 15.f) { if (!t_land) t_land = now; if (now - t_land > 5000) state = ST_LANDED; } else t_land = 0;
      break;
    default: break;
  }

  // ---- control
  CtrlState cs{}; cs.state = state; cs.t_launch_ms = t_launch;
  bool fault = att.stale(now) || aux.vbat < WYV_VBAT_CRIT;
  if (tt > WYV_ABORT_TILT_DEG * 0.0174533f && state >= ST_CONTROL) tilt_abort = true;
  float u_a = 0, u_b = 0, u_r = 0, sched = gain_schedule(qbar);
  if (state == ST_CONTROL && ctrl_enabled && !auth_abort && !tilt_abort && !fault) {
    // restoring sense: +tilt toward +Y about X -> +delta (force toward +Y at the aft fins)
    // d(ta)/dt = -w_x (nose toward +Y is a rotation about -X); d(tb)/dt = +w_y
    // authority-demonstration manoeuvre (doublets, then 1 deg attitude steps), early coast.
    // It shifts the attitude reference the PIDs hold and adds the doublet on top of their output.
    ManIn mi{}; mi.tl = now - t_launch; mi.qbar = qbar; mi.tilt_total = tt; mi.alt = h;
    mi.th[0] = ta; mi.th[1] = tb; mi.thd[0] = -w[0]; mi.thd[1] = w[1];
    mi.dpair[0] = 0.5f * (mixer.defl(0) + mixer.defl(1)); mi.dpair[1] = 0.5f * (mixer.defl(2) + mixer.defl(3));
    float ref[2], inj[2]; man.tick(mi, dt, ref, inj, cs.flags);
    cs.ref_a = ref[0] * 57.29578f; cs.ref_b = ref[1] * 57.29578f;
    u_a = pid_a.step(ta - ref[0], -w[0], sched, dt);
    u_b = pid_b.step(tb - ref[1], w[1], sched, dt);
    u_r = constrain(-WYV_ROLL_KD * w[2] * 57.29578f * sched, -WYV_ROLL_DEFL_MAX, WYV_ROLL_DEFL_MAX);
    uint32_t tc = now - t_launch - WYV_RAIL_CLEAR_MS;
    if (tc < WYV_AUTH_WINDOW_MS) {
      // regress -d(ta)/dt' = w_x' on the fin-0 deflection: a healthy (restoring) loop gives b > 0
      auth_a.add(w[0], ta, mixer.defl(0), dt);
    } else if (tc < WYV_AUTH_WINDOW_MS + 10) {
      float b, t; auth_a.fit(b, t); cs.auth_b_a = b; cs.auth_t_a = t;
      if (auth_a.excitation_rms() > WYV_AUTH_MIN_EXCITE && t < WYV_AUTH_TSTAT_ABORT) auth_abort = true;
    }
    u_a += inj[0]; u_b += inj[1];
    mixer.command(u_a, u_b, u_r);
  } else {
    mixer.neutral();
  }
  mixer.update(dt);

  // ---- publish
  NavState ns{}; ns.t_ms = now; ns.q[0] = q.w; ns.q[1] = q.x; ns.q[2] = q.y; ns.q[3] = q.z;
  ns.tilt_a = ta; ns.tilt_b = tb; ns.tilt_total = tt;
  for (int i = 0; i < 3; i++) { ns.w[i] = w[i]; ns.a_body[i] = a[i]; }
  ns.alt_m = h; ns.vz = vz; ns.v_est = v_air; ns.qbar = qbar;
  g_nav.write(ns);
  for (int i = 0; i < 4; i++) cs.defl_cmd[i] = mixer.defl(i);
  cs.u_a = u_a; cs.u_b = u_b; cs.u_r = u_r; cs.sched = sched;
  cs.flags |= (ctrl_enabled ? 1 : 0) | (auth_abort ? 2 : 0) | (tilt_abort ? 4 : 0) | (use_hg ? 0x40 : 0);
  cs.a_axial = a_ax; cs.man = man.R;
  if (cs.auth_t_a == 0) { float b, t; auth_a.fit(b, t); cs.auth_b_a = b; cs.auth_t_a = t; }
  g_ctrl.write(cs);
}

// ----------------------------------------------------------------------------------- core 1
static Adafruit_BME680 bme(&WYV_I2C_AUX);
static Telemetry tlm;
static Logger logger;

void setup1() {
  delay(200);                                    // core 0 owns I2C bring-up first
  AuxState aux{}; aux.baro_alt_m = NAN; aux.vbat = 7.6f;
  analogReadResolution(12);
  pinMode(WYV_PIN_BUZZER, OUTPUT);
  WYV_I2C_AUX.setSDA(WYV_PIN_SDA_AUX); WYV_I2C_AUX.setSCL(WYV_PIN_SCL_AUX);
  WYV_I2C_AUX.begin(); WYV_I2C_AUX.setClock(WYV_I2C_HZ);
  aux.radio_ok = tlm.begin();
  aux.sd_ok = logger.begin_sd();
  if (bme.begin(WYV_ADDR_BME688)) {
    bme.setTemperatureOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setHumidityOversampling(BME680_OS_1X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(0, 0);                      // gas heater off: not needed, saves ~12 mA
  }
  g_aux.write(aux);
}

void loop1() {
  static uint32_t t_baro = 0, t_bat = 0, t_tlm = 0, t_sd = 0, t_beep = 0, n_slot = 0;
  static uint8_t man_sent = 0;
  static bool baro_pending = false;
  static AuxState aux{}; static bool init = false;
  if (!init) { g_aux.read(aux); init = true; }
  uint32_t now = millis();
  NavState n{}; CtrlState c{}; g_nav.read(n); g_ctrl.read(c);

  // baro: async begin/end so we never block for the conversion time
  if (!baro_pending && now - t_baro >= 40) { if (bme.beginReading()) { baro_pending = true; t_baro = now; } }
  if (baro_pending && now - t_baro >= 25) {
    if (bme.endReading()) {
      aux.baro_hpa = bme.pressure / 100.0f; aux.temp_c = bme.temperature; aux.rh = bme.humidity;
      aux.baro_alt_m = 44330.0f * (1.0f - powf(aux.baro_hpa / 1013.25f, 0.1903f));
    }
    baro_pending = false;
  }
  if (now - t_bat >= 100) { t_bat = now; aux.vbat = analogRead(WYV_PIN_VBAT) * (3.3f / 4095.f) * WYV_VBAT_RATIO; }

  // telemetry: 2 Hz on the pad (with uplink windows), 20 Hz from launch, 2 Hz after landing.
  // When the manoeuvre ends its result frame goes out in 5 of the next slots.
  bool pad = c.state <= ST_ARMED, landed = c.state == ST_LANDED;
  uint32_t per = 1000UL / ((pad || landed) ? WYV_TLM_HZ_PAD : WYV_TLM_HZ_FLIGHT);
  if (now - t_tlm >= per && !tlm.busy()) {
    t_tlm = now; n_slot++;
    bool man_done = c.man.status >= 2;
    if (man_done && man_sent < 5 && (n_slot % 4 == 0)) { tlm.send_man(c.man); man_sent++; }
    else tlm.send(n, c, aux);
  }
  tlm.service(pad, aux);

  // logging (microSD only)
  if (now - t_sd >= 1000UL / WYV_LOG_HZ_SD) { t_sd = now; logger.write_sd(Logger::pack(n, c, aux)); }
  { static bool man_written = false; if (!man_written && c.man.status >= 2) { logger.write_man(c.man); man_written = true; } }
  if (c.state == ST_LANDED) { static bool closed = false; if (!closed) { logger.close(); closed = true; } }

  // buzzer: 1 chirp/2 s pad, 2 chirps armed, continuous slow beacon after landing
  uint32_t bp = c.state == ST_LANDED ? 1000 : 2000;
  if (now - t_beep >= bp) { t_beep = now; }
  uint32_t ph = now - t_beep;
  bool on = (c.state == ST_PAD && ph < 60) || (c.state == ST_ARMED && (ph < 60 || (ph > 150 && ph < 210))) ||
            (c.state == ST_LANDED && ph < 300) || (c.state == ST_FAULT && (ph % 250) < 125);
  digitalWrite(WYV_PIN_BUZZER, on);

  aux.sd_ok = logger.sd_ok(); aux.radio_ok = tlm.ok();
  g_aux.write(aux);
}
