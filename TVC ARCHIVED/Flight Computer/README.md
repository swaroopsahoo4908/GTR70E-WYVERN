# GTR70E WYVERN, Flight Computer

*Raspberry Pi Pico 2 W on a 20 x 24 perfboard, flight computer and real-time TVC controller.*

See `01_FlightComputer_Spec.md` for the full architecture writeup, and
`Documentation/CANONICAL_NUMBERS.md` for the vehicle numbers every doc should agree with.

---

## Architecture summary

Dual-core RP2350 split for determinism:

- *Core 0, real-time control.* 500 Hz TVC loop only: read both BNO085 units (Game Rotation
  Vector), vote attitude, run PID, command servos. Nothing on core 0 blocks.
- *Core 1, logging + comms.* Drains the inter-core ring buffer to microSD over SPI1, services
  WiFi telemetry (bench only -- the Pico 2 W does have a CYW43439 radio, but flight logs to card
  as the data of record), handles housekeeping.

Four sensors on one shared I2C bus, no mux:

| Device | Address | Strap |
|---|---|---|
| BNO085, bay | 0x4B | DI wired to 3V3 |
| BNO085, gimbal | 0x4A | DI unconnected |
| BME688 | 0x76 | SDO wired to GND |
| BMP388 | 0x77 | SDO unconnected |

Two body tubes, one bulkhead joint:

| Bay | Contents |
|---|---|
| Upper BT (FC bay) | Perfboard card: Pico 2 W, bay BNO085, BME688, BMP388, microSD breakout, LiPo, UBEC, arming switch, i3 4K Thumb camera |
| Bulkhead joint | Motor-ejection separation point; seven dupont leads part here |
| Lower BT | 24" chute, Nomex, aramid cord, then the TVC bay: F15-4, 2-axis gimbal, 2x ES08MA II, gimbal BNO085 |

The arming switch is reached by pulling the nose cone. The gimbal BNO085 IS gimbal-mounted on the
flight vehicle, so deflection is directly measurable in flight, not just on the ground rigs.

PID gains: *Kp* 0.10 / *Ki* 0.40 / *Kd* 0.18, +-8 deg gimbal authority, 500 Hz.

## Dual role

The same board and firmware image run the ground TVC/servo stand. Build with
`-DWYVERN_GROUND_TEST=1` and the bay IMU stops being required, launch detect and recovery compile
out, and WiFi telemetry turns on. See `firmware/wyvern4_tvc/wyvern_config.h`.

---

## Folder structure

```
Flight Computer/
├── README.md ← this file
├── 01_FlightComputer_Spec.md ← full architecture + sensor config
├── firmware/
│ └── wyvern4_tvc/
│ ├── wyvern4_tvc.ino ← main flight firmware (Arduino-Pico core, board "Raspberry Pi Pico 2 W")
│ ├── wyvern_config.h ← pin map, I2C addresses, flight/ground-stand role switch
│ ├── wyvern_pid.h ← PID controller
│ ├── imu_grv.h ← BNO085 Game Rotation Vector driver (both units)
│ ├── sd_logger.h ← microSD ring-buffer logger (SPI1)
│ ├── wifi_telemetry.h ← WiFi bench telemetry (ground stand only)
│ ├── baro.h ← BME688 + BMP388 barometric driver
│ ├── battery.h ← GP26 divider battery monitor
│ └── launch_status.h ← launch detect / flight state
├── flowcharts/ ← Mermaid state/logic diagrams
│ ├── 01_flight_state_machine.mermaid ← BOOT→ARMED→BOOST→COAST→RECOVER→LANDED
│ ├── 02_tvc_control_loop.mermaid ← 500 Hz PID loop flowchart
│ ├── 03_recovery_logic.mermaid ← motor-ejection separation logic
│ └── 04_power_tree.mermaid ← power distribution diagram
├── ground_test_rigs/ ← standalone bench DAQ sketches (load cells, HX711)
│ ├── wyvern4_gse_servo_rig/
│ └── wyvern4_gse_solenoid_rig/
├── test_code/
│ ├── t1_i2c_scan.ino ← I²C bus scan (expect 0x4A, 0x4B, 0x76, 0x77)
│ ├── t2_imu_grv_deflection.ino ← GRV deflection read + servo command check
│ ├── t3_servo_sweep.ino ← full ±8° gimbal sweep test
│ ├── t4_sensors_sdlog.ino ← all sensors → microSD log verification
│ ├── host_monitor.py ← WiFi telemetry monitor (run on laptop)
│ └── selftest.py ← automated bench self-test sequence
└── wiring/
    ├── wyvern_perfboard_wiring.svg ← hole-by-hole perfboard wiring + power chain
    ├── wyvern_bay_layout.svg ← bay layout + separation-joint cabling
    ├── gen_perfboard_diagram.py ← regenerates the wiring diagram
    └── gen_bay_layout.py ← regenerates the layout diagram
```

---

## Bench test sequence

Run these in order before any motor firing:

1. `test_code/t1_i2c_scan.ino`, confirm both BNO085s respond on their expected addresses.
2. `test_code/t2_imu_grv_deflection.ino`, manually tilt the airframe, verify body/external
   quaternions agree and servo commands track.
3. `test_code/t3_servo_sweep.ino`, full ±8° sweep, check for binding and correct direction.
4. `test_code/t4_sensors_sdlog.ino`, all sensors write to microSD; verify file on SD card.
5. `test_code/selftest.py` + `host_monitor.py` (laptop), USB-serial bench self-test verification.

Upload firmware via Arduino IDE 2.x with the [Arduino-Pico core](https://github.com/earlephilhower/arduino-pico) installed, board **"Raspberry Pi Pico 2 W"** (`rpipico2w`).

---

## Flight state machine

```
BOOT → ARMED → BOOST (F15-4 burn, 3.45 s, 500 Hz TVC) → COAST (brief)
     → RECOVER (motor ejection ~t=7.5 s, bulkhead joint separates) → DESCENT → LANDED
```

See `flowcharts/01_flight_state_machine.mermaid` for the full Mermaid diagram.

---

## Related

- `../Documentation/WYVERN_E4_BUILD_READINESS.md`, GO/NO-GO checklist
- `../Documentation/WYVERN_E4_PID_AUTOTUNE_REPORT.md`, PID gain derivation
- `../Simulations/we4_atmos_tvc.py`, closed-loop TVC atmospheric simulation
