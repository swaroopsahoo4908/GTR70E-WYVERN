// GTR70E WYVERN — PCA9548A I2C mux driver. NOT INCLUDED BY ANY ACTIVE FIRMWARE FILE.
// =====================================================================================================
// The custom RP2350B PCB1 has no PCA9548A on it -- verified against the netlist/BOM. Every onboard
// I2C device (BNO055, BME680, INA226, LIS3MDL) plus the external STEMMA-QT port share ONE bus
// (GP0 SDA / GP1 SCL), differentiated purely by I2C address -- no channel switching, no mux fault
// domain to isolate. `imu_grv.h` and `baro.h` talk directly to Wire and do not include this file.
// Kept in the tree in case a future board revision adds a mux and this becomes useful.
#pragma once
#include <Wire.h>

class I2CMux {
public:
  static constexpr uint8_t ADDR = 0x70;
  static constexpr uint8_t CH_BODY = 0;
  static constexpr uint8_t CH_RECOVERY = 1;
  static constexpr uint8_t CH_BME680 = 2;
  static constexpr uint8_t CH_BMP388 = 3;
  static constexpr uint8_t CH_SPARE = 4;

  explicit I2CMux(TwoWire& bus) : bus_(bus) {}

  // Returns true if the mux ACKs at its base address (bench/self-test check).
  bool present() {
    bus_.beginTransmission(ADDR);
    return bus_.endTransmission() == 0;
  }

  // Select exactly one channel (0-7). Channel 0xFF deselects all (safe idle state) — useful
  // before talking to a device that should NOT also be exposed to whatever device is currently
  // selected on another channel sharing the same address (both BNO085s sit at 0x4A).
  bool select(uint8_t ch) {
    if (ch == last_ch_) return last_ok_;       // skip redundant bus traffic if unchanged
    uint8_t mask = (ch <= 7) ? (uint8_t)(1u << ch) : 0x00;
    bus_.beginTransmission(ADDR);
    bus_.write(mask);
    last_ok_ = (bus_.endTransmission() == 0);
    last_ch_ = ch;
    return last_ok_;
  }

  // Bus-recovery: if a device left SDA stuck low (a common I2C lockup mode), toggling SCL
  // manually for up to 9 clocks lets a stuck slave finish its current byte and release the bus.
  // Call this from a fault handler if select()/transactions start failing repeatedly -- NOT from
  // the 500 Hz core-0 loop (this bit-bangs and is slow/blocking; logging/health-check context only).
  void recover_bus(uint8_t sda_pin, uint8_t scl_pin) {
    pinMode(scl_pin, OUTPUT);
    pinMode(sda_pin, INPUT_PULLUP);
    for (int i = 0; i < 9; i++) {
      digitalWrite(scl_pin, LOW); delayMicroseconds(5);
      digitalWrite(scl_pin, HIGH); delayMicroseconds(5);
      if (digitalRead(sda_pin)) break;          // SDA released -> bus is free again
    }
    last_ch_ = 0xFE;                            // force re-select next time (cache invalidated)
  }

  // Force the next select() to re-issue the bus write even if `ch` matches the cache -- use after
  // recover_bus() or any suspected bus glitch.
  void invalidate_cache() { last_ch_ = 0xFE; }

private:
  TwoWire& bus_;
  uint8_t last_ch_ = 0xFE;   // sentinel: "no channel selected yet"
  bool last_ok_ = false;
};
