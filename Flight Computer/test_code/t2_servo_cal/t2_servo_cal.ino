// t2 -- servo trim / sign / us-per-degree calibration, and the bench SIGN CHECK.
// Serial commands:  f<i>        select fin i (0 A+, 1 A-, 2 B+, 3 B-)
//                   u<us>       raw pulse to the selected fin (e.g. u1520)
//                   d<deg>      command the selected fin through the flight mixer convention
//                   s           sweep all four fins -15..+15 deg slowly
//                   c           centre all
//                   w<pair>     wind-tunnel sweep of pair 0 (A) or 1 (B): -15..+15 deg, 0.5 deg steps,
//                               3 s dwell, prints 'WT,<ms>,<deg>' at each step for balance-log sync
// Procedure (Documentation/Build_and_Test.md s.5): clamp the printed protractor jig on each fin,
// find the us that squares the fin to the body (-> WYV_SERVO_TRIM), measure us per 10 deg
// (-> WYV_SERVO_US_PER_DEG), then confirm that +delta on each pair makes the trailing edge move so
// that the fin's force points toward +Y (pair A) / +X (pair B). Flip WYV_SERVO_SIGN where it doesn't.
#include "fc_config.h"
#include "fin_mixer.h"
FinMixer mx; int sel = 0; float d[4] = {0,0,0,0};
void setup() { Serial.begin(115200); mx.begin(); }
void loop() {
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n'); s.trim(); if (!s.length()) return;
    char c = s[0]; float v = s.substring(1).toFloat();
    if (c == 'f') sel = constrain((int)v, 0, 3);
    else if (c == 'u') { mx.raw_us(sel, (int)v); Serial.printf("fin %d raw %d us\n", sel, (int)v); return; }
    else if (c == 'd') { d[sel] = v; }
    else if (c == 'c') { for (auto& x : d) x = 0; }
    else if (c == 'w') {
      int p = constrain((int)v, 0, 1);
      for (float a = -15; a <= 15.01f; a += 0.5f) {
        for (auto& x : d) x = 0; d[2 * p] = a; d[2 * p + 1] = a;
        uint32_t t0 = millis(); Serial.printf("WT,%lu,%.1f\n", (unsigned long)t0, a);
        while (millis() - t0 < 3000) { for (int i = 0; i < 4; i++) { float us = WYV_SERVO_CENTER_US + WYV_SERVO_TRIM[i] + WYV_SERVO_SIGN[i] * d[i] * WYV_SERVO_US_PER_DEG; mx.raw_us(i, (int)us); } delay(5); }
      }
      for (auto& x : d) x = 0; Serial.println("WT,END");
    }
    else if (c == 's') { for (float a = -15; a <= 15; a += 0.5f) { for (int i = 0; i < 4; i++) d[i] = a; mx.command(a, a, 0); mx.update(1); delay(40); } for (auto& x : d) x = 0; }
    Serial.printf("fin %d  defl %+.1f %+.1f %+.1f %+.1f\n", sel, d[0], d[1], d[2], d[3]);
  }
  // drive each fin individually in force convention (bypasses pair mixing on purpose)
  static uint32_t t = 0; if (millis() - t > 5) { t = millis();
    for (int i = 0; i < 4; i++) { float us = WYV_SERVO_CENTER_US + WYV_SERVO_TRIM[i] + WYV_SERVO_SIGN[i] * d[i] * WYV_SERVO_US_PER_DEG; mx.raw_us(i, (int)us); } }
}
