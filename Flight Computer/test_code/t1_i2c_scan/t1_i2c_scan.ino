// t1 -- I2C bring-up for the flight Pico 2 W (rev 4b). Scans both buses, then streams the BMP388
// pressure next to the BME688 so you can see both barometers agree before the first flight.
//   Wire  (I2C0, GP4 SDA / GP5 SCL): expect 0x4A BNO085
//   Wire1 (I2C1, GP2 SDA / GP3 SCL): expect 0x76 BMP388 (ADDR jumper closed; chip id 0x50, or 0x60 for a
//                                     BMP390) and 0x77 BME688. Only 0x77 twice-over = the jumper is still open.
// A missing device: check the STEMMA QT lead's colour order at the Pico end (black GND, red 3V3,
// blue SDA, yellow SCL) and that the board's own 3V3 is not back-fed from another rail.
#include <Wire.h>
#include "fc_config.h"
#include "baro.h"
void scan(TwoWire& w, const char* name) {
  int n = 0;
  for (uint8_t a = 1; a < 127; a++) { w.beginTransmission(a); if (w.endTransmission() == 0) { Serial.printf("%s found 0x%02X\n", name, a); n++; } }
  Serial.printf("%s: %d device(s)\n", name, n);
}
BMP388 bmp; EnvSensor env;
void setup() {
  Serial.begin(115200); while (!Serial && millis() < 4000) {}
  Wire.setSDA(WYV_PIN_SDA);   Wire.setSCL(WYV_PIN_SCL);   Wire.begin();  Wire.setClock(400000);
  Wire1.setSDA(WYV_PIN_SDA1); Wire1.setSCL(WYV_PIN_SCL1); Wire1.begin(); Wire1.setClock(400000);
  scan(Wire, "Wire  (BNO085)"); scan(Wire1, "Wire1 (BMP388 + BME688)");
  Serial.printf("BMP388 init %d   BME688 init %d\n", bmp.begin(Wire1, WYV_ADDR_BMP388), env.begin());
  Serial.println("bmp388_hPa,bme688_hPa,diff_Pa,bmp_alt_m,bme_T_C,bme_RH");
}
void loop() {
  uint32_t now = millis();
  bmp.poll(now); env.poll(now);
  static uint32_t t = 0;
  if (now - t >= 200) { t = now;
    float pb = bmp.pressure_pa(), pe = env.hpa() * 100.f;
    Serial.printf("%.2f,%.2f,%.1f,%.2f,%.1f,%.0f\n", pb / 100.f, pe / 100.f, pb - pe, pressure_alt_m(pb), env.temp_c(), env.rh()); }
}
