// WYVERN-E FC-100 rev 3 -- first-power bring-up. Flash over USB (hold BOOTSEL U35, tap RUN U16).
// Prints PASS/FAIL per subsystem on USB serial. Run this before the flight firmware.
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include "fc100_board.h"

static bool probe(TwoWire &w, uint8_t a) { w.beginTransmission(a); return w.endTransmission() == 0; }
static void wr16(uint8_t reg, uint16_t v) { Wire1.beginTransmission(FC_ADDR_BQ25798); Wire1.write(reg); Wire1.write(v >> 8); Wire1.write(v & 0xFF); Wire1.endTransmission(); }
static void wr8(uint8_t reg, uint8_t v)  { Wire1.beginTransmission(FC_ADDR_BQ25798); Wire1.write(reg); Wire1.write(v); Wire1.endTransmission(); }
static uint16_t rd16(uint8_t dev, uint8_t reg) {
  Wire1.beginTransmission(dev); Wire1.write(reg); Wire1.endTransmission(false);
  Wire1.requestFrom(dev, (uint8_t)2); uint16_t v = Wire1.read() << 8; return v | Wire1.read();
}
static uint8_t rd8(uint8_t dev, uint8_t reg) {
  Wire1.beginTransmission(dev); Wire1.write(reg); Wire1.endTransmission(false);
  Wire1.requestFrom(dev, (uint8_t)1); return Wire1.read();
}

void setup() {
  pinMode(FC_LED1, OUTPUT); digitalWrite(FC_LED1, HIGH);
  pinMode(FC_DSP_RESET, OUTPUT); digitalWrite(FC_DSP_RESET, HIGH);   // release ADAU1450
  pinMode(FC_BQ_INT, INPUT_PULLUP); pinMode(FC_MCP_INT, INPUT_PULLUP);
  Serial.begin(115200); while (!Serial && millis() < 4000) {}

  Wire.setSDA(FC_I2C0_SDA);  Wire.setSCL(FC_I2C0_SCL);  Wire.begin();  Wire.setClock(400000);
  Wire1.setSDA(FC_I2C1_SDA); Wire1.setSCL(FC_I2C1_SCL); Wire1.begin(); Wire1.setClock(400000);
  Wire.setTimeout(2); Wire1.setTimeout(2);

  const struct { TwoWire *w; uint8_t a; const char *n; } dev[] = {
    {&Wire, FC_ADDR_LIS3MDL, "LIS3MDL"}, {&Wire, FC_ADDR_LSM9DS1_M, "LSM9DS1-M"}, {&Wire, FC_ADDR_BNO055, "BNO055"},
    {&Wire, FC_ADDR_LPS22HB, "LPS22HB"}, {&Wire, FC_ADDR_LSM9DS1_AG, "LSM9DS1-AG"}, {&Wire, FC_ADDR_BME680, "BME680"},
    {&Wire1, FC_ADDR_MCP23008, "MCP23008"}, {&Wire1, FC_ADDR_ADAU1450, "ADAU1450"}, {&Wire1, FC_ADDR_INA_BATT, "INA226-BATT"},
    {&Wire1, FC_ADDR_INA_SERVO, "INA226-SERVO"}, {&Wire1, FC_ADDR_BQ25798, "BQ25798"} };
  for (auto &d : dev) Serial.printf("I2C %-13s 0x%02X %s\n", d.n, d.a, probe(*d.w, d.a) ? "PASS" : "FAIL");

  // Register map: BQ25798 datasheet section 9.5. Check addresses/bits there before the first powered run.
  // BQ25798: watchdog off (else registers revert every 40 s), 1.0 A charge, 1.5 A input limit, ADC on.
  // VREG (8.40 V) and cell count come from PROG = 8.2k (2S, 750 kHz) at power-up.
  if (probe(Wire1, FC_ADDR_BQ25798)) {
    wr8(0x10, rd8(FC_ADDR_BQ25798, 0x10) & ~0x07);   // REG10 WATCHDOG[2:0] = 0
    wr8(0x11, rd8(FC_ADDR_BQ25798, 0x11) & ~0x40);   // REG11 AUTO_INDET_EN = 0 (D+/D- are not connected on rev 3)
    wr16(0x03, 100);                                  // REG03 ICHG, 10 mA/LSB -> 1.00 A
    wr16(0x06, 150);                                  // REG06 IINDPM, 10 mA/LSB -> 1.50 A (5 V USB-C, Rd only)
    wr8(0x2E, 0x80);                                  // REG2E ADC_EN
    delay(50);
    Serial.printf("BQ25798 part 0x%02X VBUS %u mV VBAT %u mV VSYS %u mV\n", rd8(FC_ADDR_BQ25798, 0x48),
                  rd16(FC_ADDR_BQ25798, 0x35), rd16(FC_ADDR_BQ25798, 0x3B), rd16(FC_ADDR_BQ25798, 0x3D));
  }
  // INA226 bus voltage: 1.25 mV/LSB
  if (probe(Wire1, FC_ADDR_INA_BATT))  Serial.printf("VBAT (INA)   %.3f V\n", rd16(FC_ADDR_INA_BATT, 0x02) * 1.25e-3f);
  if (probe(Wire1, FC_ADDR_INA_SERVO)) Serial.printf("VSERVO (INA) %.3f V\n", rd16(FC_ADDR_INA_SERVO, 0x02) * 1.25e-3f);

  // PSRAM on QMI CS1 (GPIO47)
  size_t ps = rp2040.getPSRAMSize();
  Serial.printf("PSRAM %u bytes %s\n", (unsigned)ps, ps >= 8u * 1024 * 1024 ? "PASS" : "FAIL (check RP2350_PSRAM_CS=47)");

  // microSD on SPI0
  SPI.setRX(FC_SD_MISO); SPI.setTX(FC_SD_MOSI); SPI.setSCK(FC_SD_SCK);
  pinMode(FC_SD_CD, INPUT_PULLUP);
  Serial.printf("SD card-detect %s, init %s\n", digitalRead(FC_SD_CD) ? "open" : "closed", SD.begin(FC_SD_CS) ? "PASS" : "FAIL");
}

void loop() { digitalWrite(FC_LED1, !digitalRead(FC_LED1)); delay(500); }
