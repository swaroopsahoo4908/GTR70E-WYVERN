// GTR70E WYVERN · T1 — Pico 2 W perfboard (RP2350) I2C scan. ONE shared bus, GP0 SDA / GP1 SCL, no mux,
// no second controller (see 01_FlightComputer_Spec.md section 3). Confirms every sensor enumerates
// and is the authoritative way to find INA226's real bus address (its A1 strap is not cleanly wired
// to any documented address option, see firmware/wyvern4_tvc/battery.h) -- update INA226_ADDR in
// battery.h to whatever this scan actually finds.
#include <Wire.h>
#define SDA0 0
#define SCL0 1
void setup(){ Serial.begin(115200); while(!Serial&&millis()<3000);
  Wire.setSDA(SDA0); Wire.setSCL(SCL0); Wire.begin();
  Serial.println("\nI2C0 (shared bus, GP0/GP1) scan:");
  for(uint8_t a=1;a<127;a++){ Wire.beginTransmission(a); if(Wire.endTransmission()==0) Serial.printf(" 0x%02X",a); }
  Serial.println("\nexpect: 0x4B bay BNO085, 0x4A external BNO085 (STEMMA-QT), 0x76 BME688, "
                  "plus whatever address INA226 actually enumerates at (bench-confirm, not assumed)\nscan done"); }
void loop(){}
