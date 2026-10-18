// GTR70E WYVERN · T4 — BME688 (shared I2C bus, no mux) -> SPI microSD CSV @100Hz, Pico 2 W perfboard.
// Matches the flight baro (baro.h): BME688 only, address 0x76 -- no BMP388 is populated on this
// board rev, so that code path is left out here rather than logging a sensor that isn't present.
// SD pins match sd_logger.h's netlist-confirmed CARD1 trace (MISO=8, CS=9, SCK=10, MOSI=11).
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_BME680.h>
#define SDA0 0
#define SCL0 1
#define SD_MISO 8
#define SD_CS   9
#define SD_SCK  10
#define SD_MOSI 11
Adafruit_BME680 bme(&Wire); File f;
void setup(){ Serial.begin(115200);
  Wire.setSDA(SDA0); Wire.setSCL(SCL0); Wire.begin();
  SPI.setSCK(SD_SCK); SPI.setTX(SD_MOSI); SPI.setRX(SD_MISO);
  if(!SD.begin(SD_CS)) Serial.println("SD FAIL (SPI)");
  if(!bme.begin(0x76)) Serial.println("BME688 FAIL (0x76)");
  f=SD.open("WYV4_T4.csv",FILE_WRITE); f.println("t_ms,bme_hPa,bme_C,bme_RH,bme_gas"); Serial.println("logging..."); }
void loop(){
  if(bme.performReading()){ f.printf("%lu,%.2f,%.2f,%.1f,%lu\n",millis(),
   bme.pressure/100.0,bme.temperature,bme.humidity,bme.gas_resistance); f.flush(); }
  delay(10); }
