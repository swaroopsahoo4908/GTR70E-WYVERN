# Flight Computer

See `Documentation/Electronics_Telemetry.md` for the architecture, pin map, power budget and link budget.

| Path | What |
|---|---|
| `firmware/wyvern_fin/` | flight firmware: Feather RP2040 RFM95, arduino-pico, board "Adafruit Feather RP2040 RFM", Flash "8MB (no FS)". Libraries: RadioLib, Adafruit BNO08x, Adafruit BME680, SdFat - Adafruit Fork |
| `ground_station/wyvern_ground/` | second Feather RP2040 RFM95: LoRa receiver + pad uplink, tagged CSV on USB |
| `ground_station/host/wyvern_host.py` | laptop recorder, live plot, uplink commands, SD log decoder |
| `test_code/` | t1 I2C scan · t2 servo trim / sign / tunnel sweep · t3 LoRa range walk |
| `wiring/` | `gen_wiring.py` -> W1 wiring, W2 power tree, W3 system diagram, W4 spine + perfboard, W5 harness build list (pins read from `fc_config.h`) |
| `sync_headers.py` | copies the shared headers into the other sketches after any edit |

Every sketch here compiles with arduino-cli 1.1.1 + rp2040 core 6.3.0 for "Adafruit Feather RP2040 RFM" (flight and ground). Flight build: 132 kB flash, 19 kB RAM. `firmware/sil_host/` builds the manoeuvre code for the desktop.
