// =================================================================================================
// GTR70E WYVERN -- wind-tunnel balance DAQ. Raspberry Pi Pico 2 W (owned spare).
//   3 x SparkFun Qwiic Scale NAU7802 (fixed 0x2A) behind the Adafruit PCA9548 mux (0x70):
//       mux ch0 = side cell FORE (100 g), ch1 = side cell AFT (100 g), ch2 = axial cell (500 g)
//       Phase A (single fin on the reflection panel): ch0 / ch1 sit under the servo cradle, fore and aft
//       along the chord; ch2 is left unplugged (cell_ok[2] = 0 is fine).
//   Sensirion SDP810-125Pa (0x25) on mux ch3 -> pitot dynamic pressure
// I2C0 on GP4 (SDA) / GP5 (SCL), 400 kHz. Output: CSV on USB serial at ~80 Hz:
//   t_ms,fore_counts,aft_counts,axial_counts,dp_pa,temp_c
// Commands: 't' tare all cells (average 2 s, fins off / fan off), 'k<i>,<grams>' calibrate cell i
// with a known mass hung over the pulley (stores counts-per-gram in RAM; print with 'p').
// Libs: SparkFun Qwiic Scale NAU7802 Arduino Library.
// =================================================================================================
#include <Wire.h>
#include <SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h>

const uint8_t MUX = 0x70, SDP = 0x25;
NAU7802 cell[3];
long zero[3] = {0, 0, 0}; float cpg[3] = {1, 1, 1};
bool cell_ok[3] = {false, false, false}, sdp_ok = false;

void mux(uint8_t ch) { Wire.beginTransmission(MUX); Wire.write(1 << ch); Wire.endTransmission(); }

bool sdp_start() {
  mux(3); Wire.beginTransmission(SDP); Wire.write(0x36); Wire.write(0x15);   // continuous, mass-flow temp comp, averaging
  return Wire.endTransmission() == 0;
}
bool sdp_read(float& dp, float& tc) {
  mux(3); if (Wire.requestFrom(SDP, (uint8_t)9) != 9) return false;
  uint8_t b[9]; for (int i = 0; i < 9; i++) b[i] = Wire.read();
  int16_t p = (b[0] << 8) | b[1]; int16_t t = (b[3] << 8) | b[4]; int16_t sf = (b[6] << 8) | b[7];
  if (sf == 0) return false;
  dp = (float)p / sf; tc = t / 200.0f; return true;
}
long read_cell(int i) { mux(i); return cell[i].available() ? cell[i].getReading() : LONG_MIN; }

void setup() {
  Serial.begin(115200);
  Wire.setSDA(4); Wire.setSCL(5); Wire.begin(); Wire.setClock(400000);
  for (int i = 0; i < 3; i++) {
    mux(i); cell_ok[i] = cell[i].begin(Wire);
    if (cell_ok[i]) { cell[i].setGain(NAU7802_GAIN_128); cell[i].setSampleRate(NAU7802_SPS_320); cell[i].calibrateAFE(); }
  }
  sdp_ok = sdp_start();
  Serial.printf("# cells %d %d %d  sdp %d\n", cell_ok[0], cell_ok[1], cell_ok[2], sdp_ok);
  Serial.println("t_ms,fore_counts,aft_counts,axial_counts,dp_pa,temp_c");
}

void tare() {
  long acc[3] = {0, 0, 0}; int n[3] = {0, 0, 0}; uint32_t t0 = millis();
  while (millis() - t0 < 2000) for (int i = 0; i < 3; i++) { long v = read_cell(i); if (v != LONG_MIN) { acc[i] += v; n[i]++; } }
  for (int i = 0; i < 3; i++) if (n[i]) zero[i] = acc[i] / n[i];
  Serial.printf("# tare %ld %ld %ld\n", zero[0], zero[1], zero[2]);
}

void loop() {
  static long last[3] = {0, 0, 0}; static uint32_t t_out = 0;
  for (int i = 0; i < 3; i++) { long v = read_cell(i); if (v != LONG_MIN) last[i] = v - zero[i]; }
  if (millis() - t_out >= 12) {
    t_out = millis(); float dp = NAN, tc = NAN; if (sdp_ok) sdp_read(dp, tc);
    Serial.printf("%lu,%ld,%ld,%ld,%.3f,%.2f\n", (unsigned long)t_out, last[0], last[1], last[2], dp, tc);
  }
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n'); s.trim();
    if (s == "t") tare();
    else if (s.startsWith("k")) { int i = s.substring(1, 2).toInt(); float g = s.substring(3).toFloat(); if (i >= 0 && i < 3 && g > 0) { cpg[i] = last[i] / g; Serial.printf("# cell %d: %.2f counts/g\n", i, cpg[i]); } }
    else if (s == "p") Serial.printf("# counts/g %.2f %.2f %.2f\n", cpg[0], cpg[1], cpg[2]);
  }
}
