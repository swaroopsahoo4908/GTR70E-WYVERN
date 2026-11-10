// GENERATED COPY -- edit firmware/wyvern_fin/arming.h and run sync_headers.py
#pragma once
// Pad arming through the wall (rev 4): one 6 mm tactile switch, one 3 mm LED.
//   PAD   : hold >= WYV_ARM_HOLD_MS -> LED goes solid ("let go"). Released -> hands-off settle window
//           (WYV_ARM_SETTLE_MS, rates must stay under WYV_ARM_STILL_DPS) -> caller zeroes the pad
//           attitude -> ARMED. Any check failing -> REFUSED (fast blink for 3 s), back to PAD.
//   ARMED : hold >= WYV_ARM_HOLD_MS -> DISARM (back to PAD).
// The button is ignored from launch detect on (the caller stops ticking this).
#include "fc_config.h"

class ArmButton {
 public:
  enum Event : uint8_t { EV_NONE = 0, EV_ZERO_AND_ARM, EV_DISARM, EV_REFUSED };
  enum Phase : uint8_t { IDLE = 0, HELD, SETTLE, REFUSED_SHOW };
  void begin() { pinMode(WYV_PIN_BUTTON, INPUT_PULLUP); }
  // armed: current arm state. ok_to_arm: all pre-arm checks pass right now. w_dps: |body rate|.
  Event tick(uint32_t now, bool armed, bool ok_to_arm, float w_dps) {
    bool down = debounce_(now, digitalRead(WYV_PIN_BUTTON) == LOW);
    switch (phase_) {
      case IDLE:
        if (down) { if (!t_down_) t_down_ = now; if (now - t_down_ >= WYV_ARM_HOLD_MS) { phase_ = HELD; } }
        else t_down_ = 0;
        break;
      case HELD:                                 // LED solid until the operator lets go
        if (!down) {
          t_down_ = 0;
          if (armed) { phase_ = IDLE; return EV_DISARM; }
          phase_ = SETTLE; t_settle_ = now;
        }
        break;
      case SETTLE:
        if (down || w_dps > WYV_ARM_STILL_DPS || !ok_to_arm) { phase_ = REFUSED_SHOW; t_settle_ = now; return EV_REFUSED; }
        if (now - t_settle_ >= WYV_ARM_SETTLE_MS) { phase_ = IDLE; return EV_ZERO_AND_ARM; }
        break;
      case REFUSED_SHOW:
        if (now - t_settle_ >= 3000 && !down) phase_ = IDLE;
        break;
    }
    return EV_NONE;
  }
  Phase phase() const { return phase_; }
 private:
  bool debounce_(uint32_t now, bool raw) {
    if (raw != raw_) { raw_ = raw; t_edge_ = now; }
    if (now - t_edge_ >= 20) stable_ = raw_;
    return stable_;
  }
  Phase phase_ = IDLE;
  uint32_t t_down_ = 0, t_settle_ = 0, t_edge_ = 0;
  bool raw_ = false, stable_ = false;
};

// LED pattern for the state (rev 4: external 3 mm LED through the wall + onboard LED 13).
//   PAD 1 blink / 2 s   ARMED 2 blinks / 2 s   button held: solid   settling: off
//   refused: 8 Hz for 3 s   FAULT 4 Hz   flight: off (saves the pack, nobody can see it)   LANDED 1 Hz beacon
static inline bool led_pattern(uint32_t now, uint8_t state, ArmButton::Phase ph) {
  if (ph == ArmButton::HELD) return true;
  if (ph == ArmButton::SETTLE) return false;
  if (ph == ArmButton::REFUSED_SHOW) return (now % 125) < 62;
  uint32_t p2 = now % 2000, p1 = now % 1000;
  switch (state) {
    case 2 /*ST_PAD*/:    return p2 < 60;
    case 3 /*ST_ARMED*/:  return p2 < 60 || (p2 > 150 && p2 < 210);
    case 8 /*ST_LANDED*/: return p1 < 300;
    case 9 /*ST_FAULT*/:  return (now % 250) < 125;
    default:              return false;
  }
}
