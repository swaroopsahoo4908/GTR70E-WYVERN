# GTR70E WYVERN, Flight Computer Specification

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN

### Raspberry Pi Pico 2 W on a 20 × 24 perfboard, flight computer *and* real-time TVC controller

Numbers here follow `Documentation/CANONICAL_NUMBERS.md`. Wiring is drawn hole-by-hole in
`wiring/wyvern_perfboard_wiring.svg`; physical placement and the separation-joint cabling are in
`wiring/wyvern_bay_layout.svg`.

## 1. Architecture

A Raspberry Pi Pico 2 W carries the entire avionics load: attitude estimation, the 500 Hz TVC
control law, servo commanding, and logging. It sits on a generic 20 × 24 (50 × 70 mm) perfboard
mounted as an axial card in the Upper BT, held in two slotted carrier disks
(`3D parts/02b_fc_card_carrier_{fwd,aft}_ASAAero`). The 70 mm board length will not fit across the
66.8 mm bore, so it stands on edge; the LiPo straps to its back face and the components stand off
the front.

The RP2350's two cores are partitioned the same way the earlier custom-board design intended:

- **Core 0** runs the control loop exclusively — read IMUs, evaluate PID, command the gimbal
  servos. No blocking operations.
- **Core 1** drains a log ring buffer to microSD over SPI1, keeping storage latency off the
  control path.

Unlike the retired PCB1, the Pico 2 W has a CYW43439 radio. Flight still logs to microSD as the
data of record; WiFi telemetry is enabled only on the ground test stand
(`WYV_WIFI_ENABLED`, defaults to the value of `WYVERN_GROUND_TEST`).

## 2. Sensing

Four Adafruit STEMMA-QT breakouts share one I²C bus on GP0/GP1. No mux, no second bus.

| Device | Role | Address | Strap |
|---|---|---|---|
| BNO085 | Bay attitude, primary control source | 0x4B | DI wired to 3V3 |
| BNO085 | Gimbal-mounted, deflection sensing | 0x4A | DI unconnected (default) |
| BME688 | Primary barometric altitude | 0x76 | SDO wired to GND |
| BMP388 | Backup barometric altitude | 0x77 | SDO unconnected (default) |

Both IMUs run Game Rotation Vector mode — accelerometer/gyro fusion with the magnetometer
disabled, because the gimbal servos sit inches away and would corrupt a magnetically-referenced
heading. The two units vote against each other for attitude fault detection.

Unlike the PCB1 design, the second IMU **is** gimbal-mounted on the flight vehicle, so
gimbal-relative deflection is directly measurable in flight rather than only on the ground rigs.

No external I²C pull-ups are fitted. Each Adafruit breakout carries 10 kΩ; four in parallel give
roughly 2.5 kΩ, which is correct for 400 kHz.

## 3. Pin map

| Pico pin | GPIO | Function |
|---|---|---|
| 1 | GP0 | I²C0 SDA, all four sensors |
| 2 | GP1 | I²C0 SCL, all four sensors |
| 4 | GP2 | Servo 1 signal (pitch) |
| 5 | GP3 | Servo 2 signal (yaw) |
| 11 | GP8 | microSD MISO |
| 12 | GP9 | microSD CS |
| 14 | GP10 | microSD SCK |
| 15 | GP11 | microSD MOSI |
| 31 | GP26 | Battery sense (ADC0) |
| 36 | 3V3 OUT | Sensor rail |
| 39 | VSYS | 5 V from UBEC |
| 3, 8, 13, 18, 23, 28, 33, 38 | GND | Common ground |

Defined once in `firmware/wyvern4_tvc/wyvern_config.h`.

## 4. Power

2S LiPo (7.4 V nominal, 8.4 V full) → PPTC 2.6 A → arming switch → 5 V 3 A switching UBEC.

The UBEC output is the single 5 V rail: Pico VSYS, the microSD breakout, and both servos. Sensors
run off the Pico's own 3V3 regulator. A 470 µF electrolytic sits at the servo feed — without it a
simultaneous servo stall browns out the Pico.

The arming switch is reached by pulling the nose cone, so there is no hole in the Upper BT and no
switch cutout in the CAD. It carries full pack current (about 1.9 A worst case at the 6.0 V
cutoff) plus inrush into the UBEC and bulk capacitance, which is why it is a 20 A-class switch
rather than a micro slide switch.

Battery sense is a 100 kΩ / 47 kΩ divider from the armed pack rail to GP26, with 100 nF on the
tap: 2.686 V at 8.4 V, 1.918 V at the 6.0 V cutoff, both inside the ADC range. Firmware thresholds
are 6.4 V warn / 6.0 V critical.

## 5. Separation

The Upper BT and Lower BT part at the bulkhead when the F15-4 ejection charge fires at t = 7.45 s.
Seven leads cross that joint on dupont male-female extensions and simply pull apart:

SERVO1_SIG · SERVO2_SIG · +5V · GND · SDA · SCL · 3V3

Only the aramid shock cord is retained. Bulkhead pass-throughs (4.5 mm and 4.0 mm) are sized for
the wire bundles, not the connector shells — the dupont housings sit either side so they part
freely.

Consequences the firmware handles explicitly:

- TVC is finished at burnout (3.45 s), four seconds before separation, so losing servo power costs
  nothing.
- The gimbal IMU leaves with the Lower BT. `TriImu::mark_separated()` stops reporting its absence
  as a fault after `WYV_DEPLOY_T_MS`; before that point it is still a genuine fault.
- Descent attitude comes from the bay unit, which never crosses the joint.
- `WYV_I2C_TIMEOUT_US` bounds every transaction. A read to the now-absent 0x4A must NACK, not
  block — otherwise the loop stalls exactly when descent logging matters.

## 6. Dual role, flight and ground stand

The same board and the same firmware image serve the ground TVC/servo test stand. Set
`WYVERN_GROUND_TEST` to 1 and:

- The bay IMU is not required — `begin()` reports it present so the 2-of-2 gate passes on a stand
  that physically has one IMU
- `body_accel_mag_g()` returns a resting 1 g, so launch-detect and landing-quiescence cannot trip
- Launch detection and recovery logic compile out
- WiFi telemetry enables, since a bench has no reason to log blind

Attitude on the stand comes solely from the gimbal unit, which is the thing the stand exists to
measure.

## 7. Control law

Discrete PID per axis with integral anti-windup clamping and a first-order low-pass-filtered
derivative, at 500 Hz, output clipped to ±8° gimbal deflection.

Flight gains: Kp = 0.10, Ki = 0.40, Kd = 0.18, τ_d = 0.02 s. Selected by a 24-point phase/gain
margin sweep (phase margin ≈ 33°, gain margin ≈ 12.6 dB) and confirmed by a time-domain
multi-wind auto-tune. The TVC loop is inhibited for the first 0.5 s, after which it stabilises to
vertical and executes a commanded maneuver.

## 8. Why the Pico 2 W

The custom PCB1 (Ø62 mm, bare RP2350B QFN-80) was retired on schedule and cost grounds: a 0.4 mm
pitch QFN needs a 4-layer board with a solid ground plane, and the layout work plus fab turnaround
did not fit the November launch window.

| | PCB1 (retired) | Pico 2 W perfboard |
|---|---|---|
| MCU | Bare RP2350B, QFN-80 | Pico 2 W module (RP2350) |
| Cores | 2 × 150 MHz M33 | 2 × 150 MHz M33 |
| Radio | None populated | CYW43439, bench use |
| Assembly | 4-layer PCB fab + reflow | Perfboard, hand-soldered |
| Bring-up risk | Whole board, one shot | Per-breakout, incremental |
| Mass | ~14 g board | ~11 g board + 4 g Pico |
| Lead time | Fab turnaround | On hand |

Control-loop capability is identical — same silicon, same core split, same 500 Hz. What was lost
is board density and the INA226 current monitor; battery monitoring is now a resistor divider on
GP26.

## References

Bosch Sensortec. (n.d.). *BNO085 9-axis absolute orientation IMU, datasheet.*

Bosch Sensortec. (n.d.). *BME688 gas, pressure, humidity, temperature sensor, datasheet.*

Bosch Sensortec. (n.d.). *BMP388 digital pressure sensor, datasheet.*

Raspberry Pi Ltd. (2024). *Raspberry Pi Pico 2 W datasheet.*

Raspberry Pi Ltd. (2024). *RP2350 datasheet.*
