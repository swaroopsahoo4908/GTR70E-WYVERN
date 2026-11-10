// t3 -- bench test of the arming button, the wall LED and the 4682 microSD logger (rev 4b, Pico 2 W).
// Replaces the rev 3 LoRa range test (no radio any more).
//   1. Hold the button 2 s: the LED goes solid. Let go and keep hands off for 1 s: two blinks = ARMED.
//      Shake the board during that second instead: fast blink = REFUSED. Hold 2 s again to disarm.
//   2. Meanwhile 96 B records go to the card at 100 Hz through the same ring buffer as flight, and the
//      sketch reports, every 5 s, the worst loop time and the records it had to drop (must stay 0).
//      Run it for 30 min with the card you will fly: a card that ever drops records is not a flight card.
#include "fc_config.h"
#include "shared_state.h"
#include "arming.h"
#include "logger.h"
ArmButton btn; Logger lg; bool armed = false;
void setup() {
  Serial.begin(115200); while (!Serial && millis() < 3000) {}
  pinMode(WYV_PIN_LED, OUTPUT); pinMode(WYV_PIN_LED_EXT, OUTPUT);
  btn.begin();
  Serial.printf("sd %d\n", lg.begin_sd());
}
void loop() {
  static uint32_t t_rec = 0, t_rep = 0, worst_us = 0, n = 0; static uint32_t last_us = micros();
  uint32_t now = millis(), us = micros();
  if (us - last_us > worst_us) worst_us = us - last_us;
  last_us = us;
  float shake = (Serial.available() && Serial.peek() == 's') ? (Serial.read(), 50.f) : 0.f;   // type 's' = movement
  switch (btn.tick(now, armed, lg.sd_ok(), shake)) {
    case ArmButton::EV_ZERO_AND_ARM: armed = true;  Serial.println("ARMED"); break;
    case ArmButton::EV_DISARM:       armed = false; Serial.println("DISARMED"); break;
    case ArmButton::EV_REFUSED:      Serial.println("REFUSED"); break;
    default: break;
  }
  if (now - t_rec >= 10) { t_rec = now; NavState ns{}; ns.t_ms = now; CtrlState c{}; c.state = armed ? 3 : 2; AuxState a{}; lg.write(Logger::pack(ns, c, a)); n++; }
  lg.service();
  bool on = led_pattern(now, armed ? 3 : 2, btn.phase());
  digitalWrite(WYV_PIN_LED, on); digitalWrite(WYV_PIN_LED_EXT, on);
  if (now - t_rep >= 5000) { t_rep = now; Serial.printf("records %lu  dropped %lu  worst loop %lu us\n", (unsigned long)n, (unsigned long)lg.dropped(), (unsigned long)worst_us); worst_us = 0; }
}
