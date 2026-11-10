// =================================================================================================
// GTR70E WYVERN -- fin-controlled ascent, flight firmware. Rev 4b: Raspberry Pi Pico 2 W, single loop on core 0.
//
//   Every pass of loop():  BNO085 poll (Wire, 400 Hz gyro) | BMP388 read when due (Wire1, 50 Hz) |
//                          BME688 start/collect (Wire1, 10 Hz) | battery (10 Hz) | arm button |
//                          SD ring-buffer service (one 512 B sector when the card is idle)
//   Every 5 ms (200 Hz):   vertical channel, state machine, control law, authority monitor,
//                          manoeuvre, fin mixer + PWM, log record (100 Hz armed / 10 Hz on the pad)
//   The 150 MHz M33 runs the control step in a few hundred us; the loop's worst case is a BNO085
//   burst plus a BME688 read, ~1.5 ms, inside the 5 ms period.
//
// Safety model
//   * Fins only move in flight if the rocket was ARMED with the wall button on the pad (hold 2 s,
//     let go, 1 s hands-off while the IMU zeroes). Unarmed, it logs but holds neutral fins (the
//     airframe is passively stable at >= 1.3 cal).
//   * Arming is refused unless the SD log is open, the IMU is live, the barometer is live, the pack
//     is above 6.8 V and the rocket stands within 20 deg of vertical.
//   * Fins go neutral and stay neutral on: tilt > 30 deg, IMU stale > 20 ms, battery < 6.4 V,
//     or the authority monitor finding a reversed control derivative right after rail exit.
//   * The button is ignored from launch detect on. There is no radio, so nothing can command the
//     rocket in flight.
// =================================================================================================
#include <Wire.h>
#include "fc_config.h"
#include "shared_state.h"
#include "attitude.h"
#include "baro.h"
#include "fin_mixer.h"
#include "controller.h"
#include "arming.h"
#include "logger.h"

static Attitude att;
static BMP388 bmp;
static EnvSensor env;
static FinMixer mixer;
static AxisPID pid_a(1.0f), pid_b(WYV_AXIS_B_SCALE);
static AuthorityMonitor auth_a;
static ManeuverSeq man;
static ArmButton button;
static Logger logger;

static AuxState aux{};
static NavState nav{};
static CtrlState ctl{};
static FlightState state = ST_BOOT;
static uint32_t t_launch = 0, t_over = 0, t_land = 0;
static bool armed = false, ctrl_enabled = false, auth_abort = false, tilt_abort = false;
static float h = 0, vz = 0;                  // fused vertical channel
static float h_ground_baro = NAN, h_ground_lp = NAN, p_pad = NAN, tk_pad = NAN;
static float imp_cum[WYV_THRUST_NPTS];       // cumulative impulse at each thrust-table point

// ISA density, only used if the BMP388 is down
static float isa_density(float alt) { float T = 288.15f - 0.0065f * alt; return 101325.f * powf(T / 288.15f, 5.2559f) / (287.05f * T); }

// Specific force the motor should be producing t seconds after ignition (thrust-curve model)
static float model_specific_force(float t, float qbar) {
  if (t <= 0 || t >= WYV_THRUST_T[WYV_THRUST_NPTS - 1]) return 0;
  int i = 1; while (i < WYV_THRUST_NPTS - 1 && WYV_THRUST_T[i] < t) i++;
  float f = (t - WYV_THRUST_T[i - 1]) / (WYV_THRUST_T[i] - WYV_THRUST_T[i - 1]);
  float T = WYV_THRUST_N[i - 1] + f * (WYV_THRUST_N[i] - WYV_THRUST_N[i - 1]);
  float I = imp_cum[i - 1] + 0.5f * (WYV_THRUST_N[i - 1] + T) * (t - WYV_THRUST_T[i - 1]);
  float m = WYV_M_LIFTOFF_KG - WYV_M_PROP_KG * fminf(I / WYV_IMPULSE_NS, 1.f);
  return (T - qbar * WYV_CDA_M2) / m;
}

void setup() {
  Serial.begin(115200);
  pinMode(WYV_PIN_LED, OUTPUT); pinMode(WYV_PIN_LED_EXT, OUTPUT);
  digitalWrite(WYV_PIN_LED, HIGH); digitalWrite(WYV_PIN_LED_EXT, HIGH);   // solid during self-test
  mixer.begin(); mixer.neutral(); mixer.update(1.0f);
  analogReadResolution(12);
  imp_cum[0] = 0;
  for (int i = 1; i < WYV_THRUST_NPTS; i++)
    imp_cum[i] = imp_cum[i - 1] + 0.5f * (WYV_THRUST_N[i] + WYV_THRUST_N[i - 1]) * (WYV_THRUST_T[i] - WYV_THRUST_T[i - 1]);
  state = ST_SELFTEST;
  WYV_I2C.setSDA(WYV_PIN_SDA);       WYV_I2C.setSCL(WYV_PIN_SCL);
  WYV_I2C.begin();      WYV_I2C.setClock(WYV_I2C_HZ);
  WYV_I2C_BARO.setSDA(WYV_PIN_SDA1); WYV_I2C_BARO.setSCL(WYV_PIN_SCL1);
  WYV_I2C_BARO.begin(); WYV_I2C_BARO.setClock(WYV_I2C_HZ);        // BMP388 0x76 + BME688 0x77 share I2C1
  aux.baro_alt_m = NAN; aux.vbat = 7.6f; aux.rho_pad = NAN;
  aux.sd_ok = logger.begin_sd();
  aux.baro_ok = bmp.begin(WYV_I2C_BARO, WYV_ADDR_BMP388);
  aux.env_ok = env.begin();
  bool imu_ok = att.begin();
  button.begin();
  uint32_t t0 = millis();
  while (millis() - t0 < 1500) { att.poll(micros()); bmp.poll(millis()); env.poll(millis()); }   // let the GRV settle
  att.zero_pad();
  state = imu_ok ? ST_PAD : ST_FAULT;
  if (Serial) {
    Serial.printf("# %s  imu %d  sd %d  bmp388 %d  bme688 %d\n", WYV_FW_VERSION, imu_ok, aux.sd_ok, aux.baro_ok, aux.env_ok);
    Serial.println("# T,t_ms,state,seq,alt_m,vz,tilt_a,tilt_b,wx,wy,wz,ax_g,ay_g,az_g,d0,d1,d2,d3,qbar,vbat,temp,flags,auth_t,baro_hpa,rho");
  }
}

static void sensors_and_housekeeping(uint32_t now) {
  if (bmp.poll(now)) {
    aux.baro_hpa = bmp.pressure_pa() / 100.0f;
    aux.baro_alt_m = pressure_alt_m(bmp.pressure_pa());
  }
  aux.baro_ok = bmp.ok();
  if (env.poll(now)) { aux.env_hpa = env.hpa(); aux.temp_c = env.temp_c(); aux.rh = env.rh(); }
  static uint32_t t_bat = 0;
  if (now - t_bat >= 100) { t_bat = now; aux.vbat = analogRead(WYV_PIN_VBAT) * (3.3f / 4095.f) * WYV_VBAT_RATIO; }
  logger.service();
  aux.sd_ok = logger.sd_ok();
}

// Pad reference for density: BME688 temperature + humidity with the BMP388 pressure, refreshed on the
// pad and frozen at arming. In flight rho = rho_pad * (p / p_pad) * (T_pad / T), T from the ISA lapse.
static void capture_pad_air() {
  if (!aux.baro_ok || isnan(aux.baro_alt_m)) return;
  float p = aux.baro_hpa * 100.f;
  float tc = isnan(aux.temp_c) ? 15.f : aux.temp_c, rh = isnan(aux.rh) ? 50.f : aux.rh;
  p_pad = p; tk_pad = tc + 273.15f; aux.temp_pad_c = tc;
  aux.rho_pad = moist_air_density(p, tc, rh);
  h_ground_baro = h_ground_lp = aux.baro_alt_m;
}
static float air_density(float h_agl) {
  if (isnan(aux.rho_pad) || !aux.baro_ok) return isa_density(h_agl);
  float tk = tk_pad - 0.0065f * h_agl;
  return aux.rho_pad * (aux.baro_hpa * 100.f / p_pad) * (tk_pad / tk);
}

static void control_step(uint32_t now, float dt) {
  // ---- attitude, rates, specific force
  float ta, tb, tt; att.tilts(ta, tb, tt);
  const float* w = att.rates(); const float* a = att.accel();
  Q q = att.quat();

  // ---- arming (pad only)
  if (state == ST_PAD || state == ST_ARMED) {
    if (!armed) capture_pad_air();                       // keep the pad reference fresh until arming
    bool ok = aux.sd_ok && aux.baro_ok && !att.stale(now) && aux.vbat >= WYV_VBAT_WARN && att.grav_tilt_deg() <= WYV_ARM_TILT_MAX_DEG;
    switch (button.tick(now, armed, ok, att.rate_dps())) {
      case ArmButton::EV_ZERO_AND_ARM: att.zero_pad(); capture_pad_air(); h = 0; vz = 0; armed = true; break;
      case ArmButton::EV_DISARM: armed = false; break;
      default: break;
    }
    // armed and waiting: weather moves the baro ~1 hPa (8 m) an hour, so track the ground reference
    // with a 2 s low-pass and hand it to the vertical channel at launch detect
    if (armed && aux.baro_ok && !isnan(aux.baro_alt_m)) { h_ground_lp += (aux.baro_alt_m - h_ground_lp) * fminf(dt / 2.0f, 1.f); h_ground_baro = h_ground_lp; }
  }

  // ---- vertical channel: world-frame accel from the body specific force, complementary w/ baro
  float qbar_prev = nav.qbar;
  float a_ax = a[2]; bool clipped = false;
  if ((state == ST_BOOST_RAIL || state == ST_CONTROL) && a[2] >= WYV_ACCEL_CLIP_G * 9.80665f) {
    float am = model_specific_force((now - t_launch) * 1e-3f, qbar_prev);
    if (am > a_ax) { a_ax = am; clipped = true; }
  }
  float r20 = 2 * (q.x * q.z - q.w * q.y), r21 = 2 * (q.y * q.z + q.w * q.x), r22 = 1 - 2 * (q.x * q.x + q.y * q.y);
  float az_world = r20 * a[0] + r21 * a[1] + r22 * a_ax - 9.80665f;
  if (state < ST_BOOST_RAIL) az_world = 0;                       // pad: hold zero, kill drift
  vz += az_world * dt; h += vz * dt;
  if (aux.baro_ok && !isnan(aux.baro_alt_m) && !isnan(h_ground_baro)) {
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
  nav = ns;
  for (int i = 0; i < 4; i++) cs.defl_cmd[i] = mixer.defl(i);
  cs.u_a = u_a; cs.u_b = u_b; cs.u_r = u_r; cs.sched = sched;
  cs.flags |= (ctrl_enabled ? 1 : 0) | (auth_abort ? 2 : 0) | (tilt_abort ? 4 : 0) | (clipped ? 0x40 : 0);
  cs.a_axial = a_ax; cs.man = man.R;
  if (cs.auth_t_a == 0) { float b, t; auth_a.fit(b, t); cs.auth_b_a = b; cs.auth_t_a = t; }
  ctl = cs;
}

// Tagged CSV for wyvern_host.py --port (bench / pad check over USB). Never in flight, and only when
// the USB buffer has room, so a stalled host can never hold up the loop.
static void usb_tlm(uint32_t now) {
  static uint32_t t_last = 0, seq = 0;
  if (now - t_last < 1000UL / WYV_USB_TLM_HZ) return;
  t_last = now;
  if (!Serial || Serial.availableForWrite() < 256) return;
  if (!(state <= ST_ARMED || state == ST_LANDED || state == ST_FAULT)) return;
  const float R2D = 57.29578f, G = 9.80665f;
  Serial.printf("T,%lu,%u,%lu,%.1f,%.2f,%.2f,%.2f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.1f,%.1f,%.1f,%.1f,%.0f,%.2f,%.1f,%u,%.2f,%.2f,%.4f\n",
                (unsigned long)now, state, (unsigned long)seq++, nav.alt_m, nav.vz, nav.tilt_a * R2D, nav.tilt_b * R2D,
                nav.w[0] * R2D, nav.w[1] * R2D, nav.w[2] * R2D, nav.a_body[0] / G, nav.a_body[1] / G, nav.a_body[2] / G,
                ctl.defl_cmd[0], ctl.defl_cmd[1], ctl.defl_cmd[2], ctl.defl_cmd[3], nav.qbar, aux.vbat, aux.temp_c,
                ctl.flags, ctl.auth_t_a, aux.baro_hpa, aux.rho_pad);
}

void loop() {
  static uint32_t last_ctrl_us = 0, n_tick = 0;
  uint32_t now_us = micros(), now = millis();
  att.poll(now_us);
  sensors_and_housekeeping(now);
  if (now_us - last_ctrl_us < 1000000UL / WYV_CTRL_HZ) return;
  float dt = (now_us - last_ctrl_us) * 1e-6f; last_ctrl_us = now_us;
  if (dt > 0.05f) dt = 0.005f;
  control_step(now, dt);
  n_tick++;

  // log: every tick/2 (100 Hz) once armed or in flight, every 20th tick (10 Hz) unarmed on the pad
  uint32_t div = (state == ST_PAD) ? (WYV_CTRL_HZ / 10) : (WYV_CTRL_HZ / WYV_LOG_HZ_SD);
  if (n_tick % div == 0) logger.write(Logger::pack(nav, ctl, aux));
  // manoeuvre summary file: written once descending (a blocking file open must not hit the control phase)
  { static bool man_written = false; if (!man_written && ctl.man.status >= 2 && state >= ST_DESCENT) { logger.write_man(ctl.man); man_written = true; } }
  if (state == ST_LANDED) logger.close();

  bool on = led_pattern(now, state, button.phase());
  digitalWrite(WYV_PIN_LED_EXT, on); digitalWrite(WYV_PIN_LED, on);
  usb_tlm(now);
}
