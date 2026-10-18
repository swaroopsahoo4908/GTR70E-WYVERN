# GTR70E WYVERN, Test Programs

**Raspberry Pi Pico 2 W perfboard** Arduino sketches + host monitor. Build with the
**Arduino-Pico core** (earlephilhower), board **"Raspberry Pi Pico 2 W"** (`rpipico2w`). NOT any
Pico/Pico 2 W module profile. Flash each, watch USB serial at 115200.

| File | Tests |
|---|---|
| `t1_i2c_scan.ino` | single shared I²C bus (GP0/GP1, no mux), every sensor enumerates, including bench-confirming INA226's real address |
| `t2_imu_grv_deflection.ino` | bay BNO085 0x4B vs. gimbal BNO085 0x4A (**Game Rotation Vector**) attitude agreement, and gimbal-relative deflection |
| `t3_servo_sweep.ino` | RP2350 hardware-PWM ±8° gimbal sweep (GP2/GP3) |
| `t4_sensors_sdlog.ino` | BME688 (no BMP388 populated on this board rev) → SPI microSD CSV @100 Hz |
| `host_monitor.py` | reads the flight computer's USB serial, tabulates preflight PASS/FAIL |
| `selftest.py` | preflight checklist |

**Libraries (Library Manager):** Adafruit_BNO08x, Adafruit_BNO085, Adafruit_BME680, plus the
Arduino-Pico built-ins `Servo`, `Wire`, `SPI`, `SD`.
**Pins:** I²C0 (single shared bus) GP0/GP1, SPI0 microSD MISO/CS/SCK/MOSI = GP8/GP9/GP10/GP11,
servos GP2/GP3, see `../01_FlightComputer_Spec.md` §3.
