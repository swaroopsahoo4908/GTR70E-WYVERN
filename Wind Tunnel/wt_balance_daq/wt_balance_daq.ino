// =================================================================================================
// GTR70E WYVERN -- wind-tunnel Phase A controller, v3.1. ONE board: Adafruit Metro M4 Express
// (ATSAMD51, 3.3 V logic), programmed from the Arduino IDE. It drives the cradle servo, reads the
// two-cell balance (two 1 kg bar cells + HX711 modules), the measured fin angle and the room air state, and streams CSV over USB.
//
// v3.1: fin deflection is MEASURED, not just commanded. A 40-tooth gear printed into the tunnel hub
// (WTA_hub_gear40_m1) drives a 20-tooth sensor gear (WTA_sensor_gear20_m1) at 2:1; a 6 x 2.5 mm
// diametric magnet in the sensor gear spins over an Adafruit AS5600 (12 bit, 0.088 deg per count), so
// the fin resolves to 0.044 deg. Everything rides on the balance cradle, so it adds no load path to
// ground. A rubber band on the sensor gear's preload pin keeps the mesh on one flank (no backlash).
// The AS5600 sits downstream of the servo's plastic gear train, so it sees the servo's own backlash
// and compliance under aerodynamic hinge load, which the commanded angle cannot.
//
// Arduino IDE setup
//   Boards Manager: "Adafruit SAMD Boards" (add the Adafruit board-index URL in Preferences), then
//   Tools > Board > "Adafruit Metro M4 (SAMD51)". Libraries: "Adafruit BME680 Library" (pulls in
//   Adafruit BusIO + Unified Sensor) and "Servo" (built into the IDE).
//
// Wiring (Metro M4 header labels)
//   fore HX711   VCC -> 3.3V, GND -> GND, DT -> D2, SCK -> D3
//   aft  HX711   VCC -> 3.3V, GND -> GND, DT -> D4, SCK -> D5
//                (HX711 boards with a separate VDD pin: tie VDD to 3.3V too, so DT stays 3.3 V logic)
//   servo        EMAX ES9251 II (4.5-6.0 V; rev 3f). Signal -> D9. Power from a 5 V 2 A wall supply through
//                a barrel-jack terminal: +5 V -> servo red, GND -> servo brown AND Metro GND.
//                Never power the servo from the Metro, and never from a 2S LiPo (8.4 V would kill it).
//   BME688       SDA -> SDA, SCL -> SCL, VIN -> 3.3V, GND -> GND (the I2C pins by AREF)
//   AS5600       daisy-chained on the BME688's second STEMMA QT port (I2C 0x36; BME688 at 0x77)
//   USB          micro-USB to the laptop, 115200 baud
//
// Airspeed: pitot-static tube + the printed 1:10 inclined water manometer. Read the column travel
// along the tube (fan on minus fan off) and type it in: m<mm>. q = rho_w g L sin(theta) (1 + At/Ac).
//
// Output (115200 baud):
//   D,<ms>,<deg_cmd>,<deg_meas>,<fore_cnt>,<aft_cnt>,<fore_g>,<aft_g>,<T_C>,<p_Pa>,<RH>   every HX711 sample (~10 Hz)
//   WT,<ms>,<deg>                                                               at each sweep step
//   R,<deg_cmd>,<deg_meas>,<fore_g>,<aft_g>,<N_mN>,<xcp_mm>,<q_Pa>,<V_ms>,<CN>   last 2 s of each dwell
//   (CN is plotted against deg_meas; deg_meas is the 2 s mean of the AS5600)
// Commands (newline-terminated):
//   t            tare both cells (fan off, fin on, 2 s average)
//   k<i>,<g>     calibrate cell i (0 fore, 1 aft) with a known mass hung over the pulley
//   a<deg>       set the fin deflection (clamped to +/-15)
//   s / r        sweep -15..+15 (s) or +15..-15 (r) in 0.5 deg steps, 1 s settle + 2 s average, R line per
//                step. Run both and average: the 1 kg cells' hysteresis cancels between the two directions
//   m<mm>        manometer travel along the tube for the current fan setting (mm)
//   h<mm>        fin height H (root chord fixed at 60 mm) for CN
//   z            zero the angle sensor (fin held at 0 deg by the printed WTA_fin_zero_jig)
//   g<deg>       optional angle calibration point against an external reference; after 3+ points the
//                scale is refit by least squares. Not needed normally: the 40:20 tooth count fixes the scale
//   p            print the calibration and settings
// No printf with %f anywhere: SAMD's newlib-nano does not format floats by default, so every
// number goes out through Serial.print(value, digits).
// =================================================================================================
#include <Wire.h>
#include <Servo.h>
#include <Adafruit_BME680.h>

// ---------------------------------------------------------------- pins and geometry
const uint8_t PIN_DOUT[2] = {2, 4}, PIN_SCK[2] = {3, 5};
const uint8_t PIN_SERVO = 9;
const float SERVO_CENTER_US = 1500.0f, SERVO_US_PER_DEG = 10.0f;   // EMAX neutral; copy the t2 bench values here
const int8_t SERVO_SIGN = +1;
const float CELL_PITCH_MM = 60.0f;               // fore-aft cell spacing along the chord
const float ROOT_MM = 60.0f;                     // control-fin root chord
const float MANO_SIN = 0.0995037f;               // sin(atan(0.1)): the printed 1:10 ramp
const float MANO_AREA_RATIO = 1.0f + (3.175f * 3.175f) / (40.0f * 40.0f);  // 1/8 in bore vs 40 mm cup
const float RHO_WATER = 998.0f, G0 = 9.80665f;

Servo servo;
Adafruit_BME680 bme(&Wire);
bool bme_ok = false;
float T_C = NAN, p_Pa = NAN, RH = NAN;

long zero_cnt[2] = {0, 0};
float cnt_per_g[2] = {-400.0f, -400.0f};         // placeholder; set with k<i>,<g> before every session
long last_cnt[2] = {0, 0};
float deg_cmd = 0.0f, mano_mm = NAN, H_mm = 40.0f;

// ---------------------------------------------------------------- AS5600 fin-angle sensor (raw I2C)
const uint8_t AS5600_ADDR = 0x36;
const float GEAR_RATIO = 2.0f;                   // 40 T hub gear : 20 T sensor gear
float ang_sign = -1.0f;                          // the sensor gear turns opposite to the hub; flip if g<deg> fits negative
float ang_scale = 1.0f;                          // refit by g<deg> points (gear pitch error, magnet offset)
int as_zero = 0; bool as_ok = false;
float deg_meas = NAN;
double cal_x[16], cal_y[16]; int n_cal = 0;
int as_read_raw() {                              // 12-bit RAW ANGLE (0x0C/0x0D), -1 on failure
  Wire.beginTransmission(AS5600_ADDR); Wire.write(0x0C);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom(AS5600_ADDR, (uint8_t)2) != 2) return -1;
  int hi = Wire.read(), lo = Wire.read();
  return ((hi & 0x0F) << 8) | lo;
}
uint8_t as_status() {                            // bit5 MD magnet detected, bit4 ML too weak, bit3 MH too strong
  Wire.beginTransmission(AS5600_ADDR); Wire.write(0x0B);
  if (Wire.endTransmission(false) != 0) return 0;
  Wire.requestFrom(AS5600_ADDR, (uint8_t)1); return Wire.available() ? Wire.read() : 0;
}
float sensor_deg(int raw) {                      // sensor-gear angle from zero, wrapped to +/-180
  int d = raw - as_zero; if (d > 2047) d -= 4096; if (d < -2048) d += 4096;
  return d * (360.0f / 4096.0f);
}
float read_fin_deg() {
  int raw = as_read_raw(); if (raw < 0) return NAN;
  return ang_sign * ang_scale * sensor_deg(raw) / GEAR_RATIO;
}

// ---------------------------------------------------------------- CSV helpers (no float printf)
void f(float v, int d) { Serial.print(','); if (isnan(v)) Serial.print("nan"); else Serial.print(v, d); }
void l(long v) { Serial.print(','); Serial.print(v); }

// ---------------------------------------------------------------- HX711 (bit-banged, gain 128 ch A)
bool hx_ready(int i) { return digitalRead(PIN_DOUT[i]) == LOW; }
long hx_read(int i) {
  uint32_t v = 0;
  noInterrupts();
  for (int b = 0; b < 24; b++) {
    digitalWrite(PIN_SCK[i], HIGH); delayMicroseconds(1);
    v = (v << 1) | (digitalRead(PIN_DOUT[i]) ? 1u : 0u);
    digitalWrite(PIN_SCK[i], LOW); delayMicroseconds(1);
  }
  digitalWrite(PIN_SCK[i], HIGH); delayMicroseconds(1); digitalWrite(PIN_SCK[i], LOW);   // 25th pulse: A, x128
  interrupts();
  if (v & 0x800000UL) v |= 0xFF000000UL;      // sign-extend
  return (long)(int32_t)v;
}
float grams(int i, long c) { return (c - zero_cnt[i]) / cnt_per_g[i]; }

// ---------------------------------------------------------------- air
float rho_air() {
  if (!bme_ok || isnan(T_C) || isnan(p_Pa)) return 1.204f;
  float Tk = T_C + 273.15f;
  float psat = 610.94f * expf(17.625f * T_C / (T_C + 243.04f));            // Magnus
  float pv = (isnan(RH) ? 0.0f : RH / 100.0f) * psat;
  return (p_Pa - pv) / (287.058f * Tk) + pv / (461.495f * Tk);
}
float q_Pa() { return isnan(mano_mm) ? NAN : RHO_WATER * G0 * (mano_mm / 1000.0f) * MANO_SIN * MANO_AREA_RATIO; }

// ---------------------------------------------------------------- servo
void set_deg(float d) {
  d = constrain(d, -15.0f, 15.0f); deg_cmd = d;
  servo.writeMicroseconds((int)lroundf(SERVO_CENTER_US + SERVO_SIGN * d * SERVO_US_PER_DEG));
}

// ---------------------------------------------------------------- sampling
bool sample(float& fg, float& ag) {     // true when both cells have a new reading
  static bool got[2] = {false, false};
  for (int i = 0; i < 2; i++) if (hx_ready(i)) { last_cnt[i] = hx_read(i); got[i] = true; }
  if (!(got[0] && got[1])) return false;
  got[0] = got[1] = false;
  fg = grams(0, last_cnt[0]); ag = grams(1, last_cnt[1]);
  static uint32_t t_air = 0;
  if (bme_ok && millis() - t_air > 1000) { t_air = millis(); if (bme.performReading()) { T_C = bme.temperature; p_Pa = bme.pressure; RH = bme.humidity; } }
  if (as_ok) deg_meas = read_fin_deg();
  Serial.print("D"); l(millis()); f(deg_cmd, 2); f(deg_meas, 3); l(last_cnt[0]); l(last_cnt[1]);
  f(fg, 4); f(ag, 4); f(T_C, 2); f(p_Pa, 1); f(RH, 1); Serial.println();
  return true;
}

double avg_meas = NAN;
void average(uint32_t ms, double& fo, double& ao, long* raw = nullptr) {
  double sf = 0, sa = 0, rf = 0, ra = 0, sm = 0; int n = 0, nm = 0; uint32_t t0 = millis();
  while (millis() - t0 < ms) { float fg, ag; if (sample(fg, ag)) { sf += fg; sa += ag; rf += last_cnt[0]; ra += last_cnt[1]; n++; if (!isnan(deg_meas)) { sm += deg_meas; nm++; } } }
  fo = n ? sf / n : NAN; ao = n ? sa / n : NAN; avg_meas = nm ? sm / nm : NAN;
  if (raw && n) { raw[0] = lround(rf / n); raw[1] = lround(ra / n); }
}

void result_line(float deg, double fo, double ao) {
  double N = (fo + ao) * G0;                                // mN (grams x g -> mN)
  double xcp = (fo + ao) != 0 ? 0.5 * CELL_PITCH_MM * (ao - fo) / (fo + ao) : NAN;   // mm aft of the cradle centre
  float q = q_Pa(), rho = rho_air();
  float V = isnan(q) ? NAN : sqrtf(2.0f * q / rho);
  float S = ROOT_MM * H_mm / 2.0f * 1e-6f;                  // m^2, triangular fin
  float CN = isnan(q) ? NAN : (N / 1000.0) / (q * S);
  Serial.print("R"); f(deg, 1); f(avg_meas, 3); f(fo, 4); f(ao, 4); f(N, 3); f(xcp, 2); f(q, 2); f(V, 2); f(CN, 4); Serial.println();
}

void tare() {
  long raw[2] = {0, 0}; double fo, ao;
  average(2000, fo, ao, raw);
  zero_cnt[0] = raw[0]; zero_cnt[1] = raw[1];
  Serial.print("# tare"); l(zero_cnt[0]); l(zero_cnt[1]); Serial.println();
}

void sweep(int dir) {                                         // dir +1: -15 -> +15, -1: +15 -> -15
  for (int j = 0; j <= 60; j++) {
    int k = dir > 0 ? j - 30 : 30 - j;
    float d = 0.5f * k; set_deg(d);
    Serial.print("WT"); l(millis()); f(d, 1); Serial.println();
    double fo, ao; average(1000, fo, ao);                    // settle 1 s (servo + flow)
    average(2000, fo, ao);                                    // keep the last 2 s
    result_line(d, fo, ao);
  }
  set_deg(0.0f);
}

void print_settings() {
  Serial.print("# counts/g"); f(cnt_per_g[0], 2); f(cnt_per_g[1], 2);
  Serial.print(" zero"); l(zero_cnt[0]); l(zero_cnt[1]);
  Serial.print(" mano_mm"); f(mano_mm, 1); Serial.print(" q_Pa"); f(q_Pa(), 2);
  Serial.print(" H_mm"); f(H_mm, 1); Serial.print(" rho"); f(rho_air(), 4);
  Serial.print(" as5600"); Serial.print(as_ok ? 1 : 0); Serial.print(" status 0x"); Serial.print(as_status(), HEX);
  Serial.print(" zero"); l(as_zero); Serial.print(" sign"); f(ang_sign, 0); Serial.print(" scale"); f(ang_scale, 4); Serial.println();
}

void setup() {
  Serial.begin(115200);
  uint32_t t0 = millis(); while (!Serial && millis() - t0 < 3000) {}   // native USB: wait briefly for the port
  for (int i = 0; i < 2; i++) { pinMode(PIN_DOUT[i], INPUT); pinMode(PIN_SCK[i], OUTPUT); digitalWrite(PIN_SCK[i], LOW); }
  servo.attach(PIN_SERVO, 900, 2100); set_deg(0.0f);
  Wire.begin();
  bme_ok = bme.begin(0x77) || bme.begin(0x76);
  if (bme_ok) { bme.setTemperatureOversampling(BME680_OS_8X); bme.setPressureOversampling(BME680_OS_4X); bme.setHumidityOversampling(BME680_OS_2X); bme.setGasHeater(0, 0); }
  delay(500);
  as_ok = as_read_raw() >= 0;
  if (as_ok) { uint8_t st = as_status(); if (!(st & 0x20)) Serial.println("# AS5600: no magnet detected, check the 1-2 mm gap"); else if (st & 0x18) Serial.println("# AS5600: field too weak/strong, adjust the gap"); }
  Serial.print("# wt_balance_daq 3.1 (Metro M4)  bme688 "); Serial.print(bme_ok ? 1 : 0); Serial.print("  as5600 "); Serial.println(as_ok ? 1 : 0);
  Serial.println("# D,ms,deg_cmd,deg_meas,fore_cnt,aft_cnt,fore_g,aft_g,T_C,p_Pa,RH");
}

void loop() {
  float fg, ag; sample(fg, ag);
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n'); s.trim();
    if (s == "t") tare();
    else if (s.startsWith("k")) {
      int c = s.indexOf(','); int i = s.substring(1, c).toInt(); float g = s.substring(c + 1).toFloat();
      if ((i == 0 || i == 1) && g > 0) {
        long raw[2] = {0, 0}; double fo, ao; average(2000, fo, ao, raw);
        cnt_per_g[i] = (raw[i] - zero_cnt[i]) / g;
        Serial.print("# cell "); Serial.print(i); Serial.print(" counts/g"); f(cnt_per_g[i], 2); Serial.println();
      }
    }
    else if (s.startsWith("a")) { set_deg(s.substring(1).toFloat()); Serial.print("# deflection"); f(deg_cmd, 1); Serial.println(); }
    else if (s == "s") sweep(+1);
    else if (s == "r") sweep(-1);
    else if (s.startsWith("m")) {
      mano_mm = s.substring(1).toFloat();
      Serial.print("# q_Pa"); f(q_Pa(), 2); Serial.print(" rho"); f(rho_air(), 4);
      Serial.print(" V_ms"); f(sqrtf(2 * q_Pa() / rho_air()), 2); Serial.println();
    }
    else if (s.startsWith("h")) { H_mm = s.substring(1).toFloat(); Serial.print("# fin H_mm"); f(H_mm, 1); Serial.println(); }
    else if (s == "z" && as_ok) {
      long acc = 0; int k = 0; for (int i = 0; i < 32; i++) { int r = as_read_raw(); if (r >= 0) { acc += r; k++; } delay(5); }
      if (k) as_zero = (int)lround((double)acc / k);
      n_cal = 0; Serial.print("# angle zero"); l(as_zero); Serial.println();
    }
    else if (s.startsWith("g") && as_ok && n_cal < 16) {
      float gauge = s.substring(1).toFloat(); double acc = 0; int k = 0;
      for (int i = 0; i < 32; i++) { int r = as_read_raw(); if (r >= 0) { acc += sensor_deg(r) / GEAR_RATIO; k++; } delay(5); }
      cal_x[n_cal] = acc / k; cal_y[n_cal] = gauge; n_cal++;
      if (n_cal >= 3) {                       // least squares through the origin: gauge = c * x
        double sxy = 0, sxx = 0; for (int i = 0; i < n_cal; i++) { sxy += cal_x[i] * cal_y[i]; sxx += cal_x[i] * cal_x[i]; }
        double c = sxx > 0 ? sxy / sxx : 1.0; ang_sign = c < 0 ? -1.0f : 1.0f; ang_scale = fabs(c);
        double ss = 0; for (int i = 0; i < n_cal; i++) { double e = cal_y[i] - c * cal_x[i]; ss += e * e; }
        Serial.print("# angle fit n"); l(n_cal); Serial.print(" sign"); f(ang_sign, 0); Serial.print(" scale"); f(ang_scale, 4);
        Serial.print(" rms_deg"); f(sqrt(ss / n_cal), 3); Serial.println();
      } else { Serial.print("# angle point"); l(n_cal); Serial.println(); }
    }
    else if (s == "p") print_settings();
  }
}
