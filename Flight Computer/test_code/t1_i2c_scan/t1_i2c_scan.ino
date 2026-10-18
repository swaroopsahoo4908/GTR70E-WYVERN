// t1 -- I2C bring-up for the flight Feather RP2040 RFM95. Scans both buses, then streams the
// ADXL375 axes next to the BNO-free gravity check so WYV_ADXL_AXIS / WYV_ADXL_SIGN can be set.
//   Wire1 (STEMMA QT, GP2/GP3, core 0 in flight): expect 0x4A BNO085, 0x53 ADXL375
//   Wire  (TX/RX pads, GP0/GP1, core 1 in flight): expect 0x77 BME688
// Stand the rocket (or the spine) nose-up: the ADXL axis that reads about +1 g with the chosen sign
// is the one to put in fc_config.h. Expect a 0-g offset of a few hundred mg; the flight code
// learns it on the pad against the BNO085.
#include <Wire.h>
void scan(TwoWire& w, const char* name) {
  int n = 0;
  for (uint8_t a = 1; a < 127; a++) { w.beginTransmission(a); if (w.endTransmission() == 0) { Serial.printf("%s found 0x%02X\n", name, a); n++; } }
  Serial.printf("%s: %d device(s)\n", name, n);
}
bool adxl = false;
void setup() {
  Serial.begin(115200); while (!Serial && millis() < 4000) {}
  Wire1.setSDA(2); Wire1.setSCL(3); Wire1.begin(); Wire1.setClock(400000);
  Wire.setSDA(0); Wire.setSCL(1); Wire.begin(); Wire.setClock(400000);
  Wire1.beginTransmission(0x53); Wire1.write(0x00); Wire1.endTransmission(false);
  Wire1.requestFrom((uint8_t)0x53, (uint8_t)1); adxl = Wire1.available() && Wire1.read() == 0xE5;
  if (adxl) { Wire1.beginTransmission(0x53); Wire1.write(0x2D); Wire1.write(0x08); Wire1.endTransmission(); }
}
void loop() {
  scan(Wire1, "Wire1/STEMMA"); scan(Wire, "Wire/TX-RX");
  if (adxl) {
    for (int k = 0; k < 10; k++) {
      Wire1.beginTransmission(0x53); Wire1.write(0x32); Wire1.endTransmission(false);
      Wire1.requestFrom((uint8_t)0x53, (uint8_t)6); int16_t v[3];
      for (int i = 0; i < 3; i++) { uint8_t lo = Wire1.read(), hi = Wire1.read(); v[i] = (int16_t)(lo | (hi << 8)); }
      Serial.printf("ADXL375 g: x %+.2f  y %+.2f  z %+.2f\n", v[0] * 0.049f, v[1] * 0.049f, v[2] * 0.049f);
      delay(200);
    }
  }
  Serial.println(); delay(1000);
}
