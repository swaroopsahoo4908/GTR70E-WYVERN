#pragma once
// =================================================================================================
// WYVERN-E FC-100 rev 3 (JLCPCBA release) -- board pin map for arduino-pico (earlephilhower core).
// GENERATED from the KiCad netlist by tools/gen_fwpins.py. Do not hand-edit: re-run after any schematic change.
// Target: RP2350B QFN-80. 16 MB W25Q128 on QMI CS0, 8 MB APS6404L PSRAM on QMI CS1.
// Board menu: "Generic RP2350", Flash 16MB, PSRAM 8MB, PSRAM CS = 47 (or -DRP2350_PSRAM_CS=47).
// =================================================================================================

// ---- I2C0: sensor bus
#define FC_I2C0_SDA        12
#define FC_I2C0_SCL        13      // 4.7k pull-ups R36/R37
#define FC_ADDR_LIS3MDL    0x1C    // SA1 = GND
#define FC_ADDR_LSM9DS1_M  0x1E    // SDO_M = 3V3
#define FC_ADDR_BNO055     0x28    // COM3 = GND
#define FC_ADDR_LPS22HB    0x5C    // SA0 = GND
#define FC_ADDR_LSM9DS1_AG 0x6A    // SDO_A/G = GND
#define FC_ADDR_BME680     0x76    // SDO = GND

// ---- I2C1: system bus
#define FC_I2C1_SDA        14
#define FC_I2C1_SCL        15      // 4.7k pull-ups R38/R39
#define FC_ADDR_MCP23008   0x20    // A2..A0 = GND
#define FC_ADDR_ADAU1450   0x38    // ADDR1/0 = GND, SELFBOOT = GND (host loads program over I2C)
#define FC_ADDR_INA_BATT   0x40    // U8, 10 mOhm R3 in the pack lead
#define FC_ADDR_INA_SERVO  0x41    // U9, A0 = VS, 10 mOhm R7 in VSERVO
#define FC_ADDR_BQ25798    0x6B    // charger
#define FC_INA_SHUNT_OHM   0.010f

// ---- microSD on SPI0
#define FC_SD_MISO         16      // SPI0 RX
#define FC_SD_CS           17
#define FC_SD_SCK          18
#define FC_SD_MOSI         19      // SPI0 TX
#define FC_SD_CD           23      // card detect, 20k pull-up R6

// ---- servo / actuator outputs, JST-XH 3P (SIG, VSERVO 5.0 V, GND). Order = connector reference order.
// U19, U23, U24, U25, U26, U27, U28, U29, U30. Every RP2350 GPIO has a PWM channel.
static const uint8_t FC_SERVO_PINS[9] = {10, 5, 4, 2, 7, 1, 6, 8, 3};
#define FC_SERVO_PITCH     10      // U19
#define FC_SERVO_YAW       5      // U23

// ---- H1 1x14 header: pins 1..12 = GPIO below, pin 13 = 3V3, pin 14 = SWDIO. SWCLK on test pad TP1.
static const uint8_t FC_HDR_PINS[12] = {42, 41, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30};  // H1 pin 1..12
// U20 1x4: GPIO27, GPIO28, 3V3, GND
#define FC_AUX1            27
#define FC_AUX2            28
// U31 1x4: GPIO43 (ADC3), GPIO44 (ADC4), 3V3, GND
// U32 1x4: GPIO45 (ADC5), GPIO46 (ADC6), GPIO40 (ADC0), GND

// ---- status, interrupts, audio
#define FC_LED1            22      // active HIGH, 330R
#define FC_MCP_INT         20
#define FC_DSP_RESET       29      // ADAU1450 RESET, active LOW
#define FC_PDM_CLK         24      // IM63D135 CLK + ADAU1450 BCLK_IN0 (PIO-driven)
#define FC_PDM_DATA        25      // IM63D135 DATA (L/R = GND) + ADAU1450 SDATA_IN0
#define FC_DSP_LRCLK       26      // ADAU1450 LRCLK_IN0
#define FC_LSM9DS1_INT1    11
#define FC_BNO055_INT      21
#define FC_BQ_INT          0      // open drain: enable the internal pull-up
#define FC_PSRAM_CS        47      // QMI CS1n (only GPIO0/8/19/47 can carry it)

// ---- MCP23008 pyro channels (recovery is motor ejection; keep disarmed unless deliberately used)
#define FC_MCP_PYRO1_DRV   0       // GP0 -> 1k -> AO3400A Q1 gate, 10k pull-down
#define FC_MCP_PYRO2_DRV   1
#define FC_MCP_PYRO1_CONT  2       // GP2 <- 33k/10k divider from channel output, 3V3 zener clamp
#define FC_MCP_PYRO2_CONT  3

// ---- power (rev 3): USB-C 5 V (5.1k Rd, no PD) or 2S pack (XT30) -> BQ25798 (PROG 8.2k: 2S, 750 kHz)
//      -> VSYS -> TPS563201 3V3 (EN tied to VSYS) and TPS54202 VSERVO 5.0 V; AMS1117-1.2 for ADAU1450 DVDD.
#define FC_VBAT_WARN_V     6.4f
#define FC_VBAT_CRIT_V     6.0f
