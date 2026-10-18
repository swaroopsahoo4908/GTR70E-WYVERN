// GTR70E WYVERN · T3 — TVC servo sweep to the FULL +-8 deg gimbal limit (Pico 2 W perfboard/RP2350, GP2 pitch / GP3 yaw).
// ================================================================================================
// REWRITTEN 2026-08 to exercise the SAME signal path the flight firmware uses.
//
// The previous version called Servo::write(90 +- 8) -- absolute servo degrees, whole-degree
// quantized. The flight sketch commands nozzle deflection through writeMicroseconds() with a
// linkage scale. A bench test that drives a different path than flight cannot validate flight, and
// this one previously "passed" while wyvern4_tvc.ino was silently clamping to +-5 deg.
//
// Keep SERVO_US_* IDENTICAL to the block in wyvern4_tvc.ino. If you change one, change both.
//
// PROCEDURE (build guide step B4):
//   1. Flash, open Serial Monitor at 115200.
//   2. Type 'c' to centre. Set the linkage so the nozzle is mechanically centred at 1500 us.
//   3. Type 'p' / 'y' to step pitch / yaw to +8, 0, -8 and HOLD 3 s at each.
//   4. Measure ACTUAL nozzle angle at the +8 and -8 holds with a digital protractor.
//   5. If measured != 8.0 deg, set SERVO_LINKAGE_RATIO = 8.0 / measured_deg, reflash, repeat.
//      Record the final value in the build log AND copy it into wyvern4_tvc.ino.
//   6. Type 's' for the continuous sweep and watch/listen for binding or buzz at the extremes.
#include <Servo.h>

static const int   PIN_SERVO_P = 2, PIN_SERVO_Y = 3;   // matches wyvern4_tvc.ino's PIN_SERVO_P/PIN_SERVO_Y
static const float OUT_LIM_DEG          = 8.0f;    // MUST match wyvern_pid.h OUT_LIM_DEG
static const float SERVO_US_NEUTRAL     = 1500.0f;
static const float SERVO_US_PER_DEG     = 10.0f;
static const float SERVO_LINKAGE_RATIO  = 1.0f;    // <-- calibrate in step 5, then copy to flight sketch

Servo sp, sy;

static int us_from_deg(float nozzle_deg) {
  float us = SERVO_US_NEUTRAL + nozzle_deg * SERVO_LINKAGE_RATIO * SERVO_US_PER_DEG;
  if (us < 1000.0f) us = 1000.0f;
  if (us > 2000.0f) us = 2000.0f;
  return (int)lroundf(us);
}
static void centre() { sp.writeMicroseconds((int)SERVO_US_NEUTRAL); sy.writeMicroseconds((int)SERVO_US_NEUTRAL); }

static void hold_axis(Servo& s, const char* name) {
  const float pts[3] = { OUT_LIM_DEG, 0.0f, -OUT_LIM_DEG };
  for (int i = 0; i < 3; i++) {
    int us = us_from_deg(pts[i]);
    s.writeMicroseconds(us);
    Serial.printf("%s -> %+.1f deg (%d us) -- HOLD, measure now\n", name, pts[i], us);
    delay(3000);
  }
  centre();
  Serial.printf("%s centred\n", name);
}

void setup() {
  Serial.begin(115200);
  unsigned long t = millis(); while (!Serial && millis() - t < 3000) {}
  sp.attach(PIN_SERVO_P); sy.attach(PIN_SERVO_Y);
  centre(); delay(500);
  Serial.printf("T3 servo sweep -- limit +-%.1f deg, neutral %d us, %.1f us/deg, linkage %.3f\n",
                OUT_LIM_DEG, (int)SERVO_US_NEUTRAL, SERVO_US_PER_DEG, SERVO_LINKAGE_RATIO);
  Serial.println("commands: c=centre  p=pitch hold test  y=yaw hold test  s=continuous sweep");
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  if (c == 'c') { centre(); Serial.println("centred"); }
  else if (c == 'p') hold_axis(sp, "PITCH");
  else if (c == 'y') hold_axis(sy, "YAW");
  else if (c == 's') {
    Serial.println("continuous sweep, both axes -- listen for binding/buzz at the extremes");
    for (int rep = 0; rep < 3; rep++) {
      for (float a = -OUT_LIM_DEG; a <= OUT_LIM_DEG; a += 0.5f) { sp.writeMicroseconds(us_from_deg(a)); delay(30); }
      for (float a = OUT_LIM_DEG; a >= -OUT_LIM_DEG; a -= 0.5f) { sp.writeMicroseconds(us_from_deg(a)); delay(30); }
      centre(); delay(300);
      for (float a = -OUT_LIM_DEG; a <= OUT_LIM_DEG; a += 0.5f) { sy.writeMicroseconds(us_from_deg(a)); delay(30); }
      for (float a = OUT_LIM_DEG; a >= -OUT_LIM_DEG; a -= 0.5f) { sy.writeMicroseconds(us_from_deg(a)); delay(30); }
      centre(); delay(300);
    }
    Serial.println("sweep done");
  }
}
