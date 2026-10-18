#pragma once
// ================================================================================================
// GTR70E WYVERN, build configuration for the Pico 2 W perfboard flight computer.
//
// One firmware image serves two roles. Flight uses both IMUs; the ground TVC/servo test stand
// reuses the identical electronics stack bolted to a bench, where the bay IMU measures nothing
// useful and its absence must not fail the self-test.
//
// Select the role by defining WYVERN_GROUND_TEST at build time (Arduino IDE: add
// `-DWYVERN_GROUND_TEST=1` to the build flags, or just flip the default below before flashing
// the bench unit).
//
// Hardware: Raspberry Pi Pico 2 W on a 20x24 (50x70 mm) perfboard. All four sensors are Adafruit
// STEMMA-QT breakouts landing on one shared I2C bus. See
// `Flight Computer/wiring/wyvern_perfboard_wiring.svg` for the hole-by-hole wiring.
// ================================================================================================

#ifndef WYVERN_GROUND_TEST
#define WYVERN_GROUND_TEST 0   // 0 = flight vehicle, 1 = ground TVC/servo test stand
#endif

// ---------------------------------------------------------------------------- I2C bus + addresses
// Both IMUs are BNO085 on the same bus, separated by the DI/address pin:
//   gimbal unit  -- DI unconnected (breakout default)      -> 0x4A
//   bay unit     -- DI wired to 3V3 on the perfboard        -> 0x4B
// Baros are separated by their SDO straps:
//   BME688       -- SDO wired to GND                        -> 0x76
//   BMP388       -- SDO unconnected (breakout default)       -> 0x77
#define WYV_PIN_SDA        0    // GP0, Pico physical pin 1
#define WYV_PIN_SCL        1    // GP1, Pico physical pin 2
#define WYV_I2C_HZ         400000UL

#define WYV_ADDR_IMU_GIMBAL 0x4A  // BNO085 on the TVC gimbal, via STEMMA-QT cable
#define WYV_ADDR_IMU_BAY    0x4B  // BNO085 in the electronics bay (flight only)
#define WYV_ADDR_BME688     0x76
#define WYV_ADDR_BMP388     0x77

// ---------------------------------------------------------------------------------- servo outputs
#define WYV_PIN_SERVO_PITCH 2   // GP2, Pico physical pin 4
#define WYV_PIN_SERVO_YAW   3   // GP3, Pico physical pin 5

// ------------------------------------------------------------------------------- microSD on SPI1
#define WYV_PIN_SD_MISO     8   // GP8,  physical 11
#define WYV_PIN_SD_CS       9   // GP9,  physical 12
#define WYV_PIN_SD_SCK     10   // GP10, physical 14
#define WYV_PIN_SD_MOSI    11   // GP11, physical 15

// ------------------------------------------------------------------------------- battery monitor
// 100k / 47k divider from the armed pack rail to GP26 (ADC0), 100 nF to GND on the tap.
// Vadc = Vpack * 47/147 -> 2.686 V at 8.4 V full charge, 1.918 V at the 6.0 V cutoff.
#define WYV_PIN_VBAT_ADC   26
#define WYV_VBAT_DIV_TOP   100000.0f
#define WYV_VBAT_DIV_BOT    47000.0f
#define WYV_VBAT_RATIO     ((WYV_VBAT_DIV_TOP + WYV_VBAT_DIV_BOT) / WYV_VBAT_DIV_BOT) // 3.128
#define WYV_ADC_VREF       3.3f
#define WYV_VBAT_WARN_V    6.4f   // 2S, ~3.20 V/cell
#define WYV_VBAT_CRIT_V    6.0f   // 2S, ~3.00 V/cell

// ------------------------------------------------------------------------------------ role gating
#if WYVERN_GROUND_TEST
  // Bench stand: the board is bolted down, so the bay IMU is not populated and not required.
  // Attitude comes solely from the gimbal unit, which is what the stand is measuring.
  #define WYV_REQUIRE_BAY_IMU   0
  #define WYV_ENABLE_LAUNCH_DET 0   // no launch to detect on a bench
  #define WYV_ENABLE_RECOVERY   0   // no deployment logic
  #define WYV_ROLE_NAME         "GROUND-TVC-STAND"
#else
  #define WYV_REQUIRE_BAY_IMU   1
  #define WYV_ENABLE_LAUNCH_DET 1
  #define WYV_ENABLE_RECOVERY   1
  #define WYV_ROLE_NAME         "FLIGHT"
#endif

// ------------------------------------------------------------------------------ separation event
// The Upper BT and Lower BT part at the bulkhead when the F15-4 ejection charge fires. Everything
// in the TVC bay -- both servos and the gimbal BNO085 (0x4A) -- crosses that joint on dupont
// male-female extension leads, which simply pull apart. Only the aramid shock cord stays attached.
//
// So after DEPLOY_T the gimbal IMU dropping off the bus and the servos going dead are EXPECTED,
// not faults. Attitude for the descent comes from the bay unit (0x4B), which never crosses the
// joint. The I2C driver must have a real timeout, or a read to the now-absent 0x4A will block the
// control loop exactly when descent logging matters.
#define WYV_DEPLOY_T_MS       7450UL   // ejection: burnout 3.45 s + F15-4's 4 s delay
#define WYV_I2C_TIMEOUT_US    2000UL   // per-transaction ceiling; a missing device must NACK, not hang

// PCB1 is retired. There is no onboard radio question on the Pico 2 W: it has CYW43439, so
// bench telemetry over WiFi is available on the ground stand. Flight still logs to microSD as
// the data of record; set WYV_WIFI_ENABLED to 1 only on the bench unit.
#ifndef WYV_WIFI_ENABLED
#define WYV_WIFI_ENABLED WYVERN_GROUND_TEST
#endif
