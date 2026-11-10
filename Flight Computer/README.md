# Flight Computer

See `Documentation/Electronics_Telemetry.md` for the architecture, pin map and power budget.

| Path | What |
|---|---|
| `firmware/wyvern_fin/` | flight firmware (rev 4b): Raspberry Pi Pico 2 W (RP2350, radio unused), arduino-pico, board "Raspberry Pi Pico 2W". Libraries: Adafruit BNO08x, Adafruit BME680, SdFat - Adafruit Fork. BMP388 driver is `baro.h`; log goes to an Adafruit 4682 microSD on SPI0 |
| `firmware/sil_host/` | builds the controller + manoeuvre code for the desktop and replays simulated flights through it (`sil_check.py`) |
| `host/wyvern_host.py` | SD log decoder (`--decode WYFnnn.BIN`), USB live plot on the bench / pad (`--port`), replay |
| `test_code/` | t1 I2C scan (2 buses) + barometer agreement · t2 servo trim / sign / tunnel sweep · t3 arming button, LED and SD-logger soak test |
| `wiring/` | `gen_wiring.py` -> W1 wiring, W2 power tree, W3 system diagram, W4 spine + perfboard, W5 harness build list (pins read from `fc_config.h`) |
| `sync_headers.py` | copies the shared headers into the test sketches after any edit |

Every sketch here compiles with arduino-cli 1.1.1 + arduino-pico 6.3.0 for "Raspberry Pi Pico 2W". Flight build: 365 kB flash, 116 kB RAM. Rev 4 removed the LoRa link, the ground-station Feather and the ADXL375; rev 4b swapped the Teensy 4.1 for a Pico 2 W and an Adafruit 4682 microSD breakout.
