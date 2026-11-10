# Electronics, power and data logging

_Drawings (generated from `fc_config.h`): `Flight Computer/wiring/W1_wiring.png`, `W2_power_tree.png`, `W3_system.png`, `W4_spine_perfboard.png` (spine face map and the 16 x 62 mm power perfboard). The file keeps its old name so links still work; rev 4 has no telemetry link._

## 1. Board choice: one Pico 2 W, no radio (rev 4b)

The flight computer is a Raspberry Pi Pico 2 W: an RP2350 (two Cortex-M33 cores at 150 MHz with hardware floating point, 520 kB RAM) on a 51 x 21 mm board. Its CYW43 radio is never started. The log goes to an Adafruit 4682 microSD breakout on SPI0. Rev 4 used a Teensy 4.1 with its built-in SDIO socket; rev 4b goes back to the RP2040 family for the same firmware core the project started on, at a quarter of the current draw.

Rev 4 already removed the Feather RP2040 RFM95, the LoRa downlink, the pad uplink, the ground-station Feather and the ADXL375. Those reasons stand:
- The research product is the log on the card. Every number the research question needs is in the 100 Hz binary log and in `MANxxx.TXT`; the radio carried a second copy, not new data.
- A pushbutton through the wall arms the rocket with no RF link to range-test and no second board at the RSO table.
- The whole loop runs on core 0. The control step is a few hundred microseconds at 150 MHz with the FPU; the loop's worst case (a BNO085 burst, a BME688 read and one 512 B SD sector at 24 MHz SPI) stays near 2 ms inside the 5 ms period. Core 1 is free.
- Cost: two Pico 2 Ws and two 4682s ($21) against two Teensy 4.1s ($63).

What it costs:
- No live data. If the rocket lands out of sight the only record is in it. The 6.3 m/s descent and the drift prediction (20 m at apogee in a 4 m/s wind) are what find it.
- No high-g channel. The BNO085's ±8 g accelerometer sits at its clip for the first ~0.2 s of the F42-4T (peak specific force ~8.9 g). Section 5 covers how the firmware handles that.
- Two I2C blocks instead of three, so the two barometers share I2C1 and the BMP388's address jumper has to be closed (0x76).
- SPI to a breakout is slower than the Teensy's SDIO, which is why the ring buffer and pre-allocation matter (section 5).

## 2. Pin map

| Function | Pico 2 W pin | Notes |
|---|---|---|
| Servo 0, A+ (az 0) | GP10 | PWM slice 5 A, 200 Hz, 1 µs steps (analogWriteRange 5000) |
| Servo 1, A- (az 180) | GP11 | slice 5 B |
| Servo 2, B+ (az 90) | GP12 | slice 6 A |
| Servo 3, B- (az 270) | GP13 | slice 6 B |
| BNO085 SDA / SCL | GP4 / GP5 | I2C0 (Wire), 400 kHz, 0x4A, alone on its bus |
| BNO085 INT / RST | GP6 / GP7 | data-ready and hard reset |
| BMP388 SDA / SCL | GP2 / GP3 | I2C1 (Wire1), 400 kHz, 0x76 with the ADDR jumper closed (primary altimeter) |
| BME688 | same bus | I2C1, 0x77 (temperature, humidity), daisy-chained from the BMP388 |
| microSD (4682) CLK / DI / DO / CS | GP18 / GP19 / GP16 / GP17 | SPI0 at 24 MHz; 3 V only, which suits the 3.3 V Pico |
| Arm button | GP14 | 6 mm tactile switch to GND, internal pull-up |
| Arm LED | GP15 | 3 mm red LED through 220 Ω to GND (~6 mA) |
| Battery sense | GP26 / ADC0 | 100k / 47k divider + 100 nF on the perfboard; 8.4 V full pack is 2.69 V at the pin (3.3 V max) |
| Power in | VSYS (pin 39) | 5 V from the logic buck through a 1N5817 Schottky |

The Pico 2 W's own LED is wired to the radio chip, so the firmware leaves it alone and uses only the wall LED.

## 3. Power

```
2S LiPo 450 mAh ──XT30── Pololu 2810 MOSFET switch ──VSW──┬── MPM3610 #2 → 5 V → 4 x EMAX ES9251 II + 470 µF
                          (slide flipped through a       ├── MPM3610 #1 → 5 V → 1N5817 → Pico VSYS → RT6150 → 3V3 → sensors, SD
                           4 x 12 mm wall slot)          └── 100k/47k divider → A0
```

- The Pololu 2810 sits in a printed cradle on the control-tube wall at +Y, 76 mm up the spine, component side out. Its slide knob sits 0.3 mm under a 4 x 12 mm slot that runs around the airframe, so the slide moves at right angles to the boost and ejection loads; flip it with a toothpick. Three 22 AWG leads join it to the perfboard. The full servo current goes through its 16 mΩ MOSFETs: 3 A continuous, 12 A peak.
- The ES9251 II is a 4.5-6.0 V servo, so the four run from their own MPM3610 at 5.0 V, never from 2S. Four slewing together stay under the buck's 1.2 A, and the 470 µF on the servo rail covers start-up peaks.
- The Pico runs from a dedicated 5 V buck into VSYS through a 1N5817 Schottky, the external-supply circuit in the Pico datasheet. USB's VBUS reaches VSYS through the Pico's own diode, so the two supplies OR together and a USB lead on the bench can never back-feed the buck.
- The Pico's 3V3 OUT (its RT6150 buck-boost, 300 mA available) feeds the sensors and the 4682. Total load there is ~15 mA plus SD write bursts.

### Battery sizing: 25 min idle + 1 min flight

From `Simulations/wf_power.py` (load table in `plots_power/battery_budget.json`):

| | current at the pack |
|---|---|
| Pad idle (Pico 2 W at 150 MHz, IMU, two baros, SD at 10 Hz, servos holding, LED) | 73 mA |
| Flight (SD at 100 Hz, servos working) | 306 mA |
| Mission charge: 25 min idle + 1 min flight | 35.4 mAh |
| With 80 % depth of discharge, cold derate 0.85 and a 1.25 margin | 65 mAh |
| Pack | 450 mAh: 6.9x margin, about 4 h of pad hold |

The Pico figure is an estimate for the RP2350 at 150 MHz with the radio off (about 30 mA at VSYS); measure it on the bench.

## 4. Arming

A 6 x 6 x 5 mm tactile switch (Adafruit 367) and a 3 mm red LED (SparkFun COM-00533) share one printed cradle on the control-tube wall at -Y, the mirror of the 2810 cradle. The plunger sits 0.3 mm under the skin in a 4.0 mm hole, so it cannot be bumped on the rail but a pen tip reaches it. The LED looks out through a 3.2 mm hole 8 mm above.

| On the pad | What happens | LED |
|---|---|---|
| power on | self-test, IMU settles 1.5 s, SD file opens | solid during self-test, then 1 blink / 2 s (PAD) |
| hold the button 2 s | ready to arm | solid: let go now |
| hands off for 1 s | rates must stay under 3 °/s; then the pad attitude is zeroed and the pad air captured | off while settling |
| armed | fins will fly; log goes from 10 Hz to 100 Hz | 2 blinks / 2 s |
| hold 2 s again | disarm | back to 1 blink |
| any check fails | refused, stays in PAD | 8 Hz flicker for 3 s |

Arming is refused unless the SD log is open, the IMU is live, the BMP388 is live, the pack is at or above 6.8 V, and the body axis is within 20° of the measured gravity vector. From launch detect on, the button is ignored. Nothing can command the rocket in flight because there is no receiver.

## 5. Firmware

`Flight Computer/firmware/wyvern_fin/` (v2.1.0) builds with arduino-pico 6.3 for "Raspberry Pi Pico 2W" at 150 MHz: 365 kB flash, 116 kB RAM. Libraries: Adafruit BNO08x, Adafruit BME680, SdFat - Adafruit Fork.

| File | Job |
|---|---|
| `fc_config.h` | every pin, gain and limit, copied from the sim outputs; the F42T thrust table for the axial channel |
| `attitude.h` | BNO085 game rotation vector on the pad; own gyro-quaternion propagation from launch, because accel tilt-correction is wrong under thrust |
| `baro.h` | register-level BMP388 driver (normal mode, 50 Hz, pressure x8, IIR 3; Bosch floating-point compensation), BME688 in async forced mode at 10 Hz, moist-air density |
| `arming.h` | button debounce and hold logic, LED patterns |
| `controller.h` | q-scheduled PID per axis, roll-rate damping, 4-regressor authority monitor, the authority-demonstration manoeuvre (`ManeuverSeq`) |
| `fin_mixer.h` | pitch / yaw / roll to four fins, roll gets a reserved 5° budget, slew limit, trims and signs, PWM output |
| `logger.h` | 96 B records into a 32 kB RAM ring buffer, written to a pre-allocated file one 512 B sector at a time only when the card is idle; `MANxxx.TXT` after the manoeuvre |
| `shared_state.h` | the state structs (also built by the SIL host) |
| `wyvern_fin.ino` | the single loop: sensors and SD service every pass, control at 200 Hz, log at 100 Hz armed / 10 Hz unarmed |

### Vertical channel and q̄ without a high-g accelerometer

The vertical channel integrates the world-frame specific force and is pulled toward the BMP388 altitude by a complementary filter (gain 0.5 under thrust, 2.0 after). The BNO085 clips at 8 g; the F42-4T sits above that for roughly the first 0.2 s. While the axial reading is at the clip, the firmware takes the larger of the measurement and a thrust-curve model, (T(t) − q̄·C_D A)/m(t), using the AeroTech F42T curve and propellant burned in proportion to impulse. Left uncorrected, the clip would bias the climb rate about 1 m/s low (2 to 4 % of q̄ at max-q) until the baro pulled it back. With the model the bias goes and what remains is the motor's own scatter, about 0.17 m/s per 1 % of thrust deviation over the clipped window. Flag bit 6 marks the samples where the model was used, so the log shows exactly where it happened.

Air density now comes from measurement instead of the ISA table. On the pad, until arming, the firmware keeps refreshing ρ from the BMP388 pressure and the BME688 temperature and humidity (CIPM simplified moist-air form). At arming it freezes ρ_pad, p_pad and T_pad; in flight ρ = ρ_pad · (p/p_pad) · (T_pad/T) with T from the ISA lapse. On a hot, humid day that is a few percent of q̄ the gain schedule no longer has to absorb. While the rocket waits armed, the ground reference for altitude tracks the baro with a 2 s low-pass, so weather drift during a long hold (about 8 m per hPa) does not end up in the flight altitude.

### Logging

The card in the 4682 is the only record, and SPI is slower than the Teensy's SDIO was, so the buffering matters more. The logger pre-allocates 128 MB contiguously when it opens `WYFnnn.BIN`, so a write never has to allocate clusters mid-flight, and writes one sector at a time only when `isBusy()` says the card is idle. A slow card's housekeeping pause (up to ~100 ms on cheap cards) then costs buffer space, not loop time: the 32 kB ring holds 3.4 s of records. At 10 Hz unarmed and 100 Hz armed, 128 MB is about 38 h on the pad or 3.8 h armed. On landing the buffer is drained and the file truncated. `MANxxx.TXT` is only written once the rocket is descending, so its file open cannot land in the control phase. The record layout is the same 96 B as rev 3; `host/wyvern_host.py --decode` reads both.

Soak-test the flight card with `t3_arm_log` for 30 minutes before trusting it: the sketch logs at 100 Hz through the same ring buffer and reports dropped records, which must stay at zero.

### State machine and safety

BOOT → SELFTEST → PAD ⇄ ARMED → BOOST (rail) → CONTROL → COAST → DESCENT → LANDED, with FAULT from any state. CONTROL lasts until q̄ falls below 15 Pa after burnout.

- Fins only move in flight if the rocket was armed on the pad. Unarmed, it still logs (at 10 Hz until launch detect, then 100 Hz).
- Fins go to neutral and stay there on: tilt > 30°, IMU stale > 20 ms, battery < 6.4 V, or the authority monitor finding a reversed control derivative (t < −3) right after rail exit. The airframe is passively stable at 1.44 cal with the fins centred.
- Gains: δ[rad] = S(q)·(4.5·θ + 1.0·∫θ + 0.8·ω), with S = clamp(1500 Pa / q, 0.15, 4.0); the rev 4 retune keeps them. Both pairs sit at one station, so axis B uses the same gains.

## 6. Authority-demonstration manoeuvre

One programme per flight, in early coast, so authority is measured rather than inferred. On the F42-4T it starts 250 ms after burnout (1.72 s) and runs 2.6 s. Predicted values are for the rev 4 airframe in a 4 m/s wind (`Simulations/plots_flight/maneuver_prediction.json`); spreads are 1 sd over 40 flights in 0 to 7 m/s wind.

| ms after start | Axis | What happens | What it measures | Predicted |
|---|---|---|---|---|
| 0 | A | ±5° doublet added to the PID output, 120 ms per half | M_δ/I by least squares (ω̇ = c + aθ + m_q ω + bδ), its t-statistic, and the ratio to the model's 0.0355 · q̄ | 46 1/s² at 1.3 kPa; fit/model 0.94 ± 0.12 |
| 400 | B | same doublet | same | 39 1/s² at 1.1 kPa; fit/model 0.93 ± 0.14 |
| 800 | A | attitude reference stepped 1° for 500 ms, then back to vertical hold for 400 ms | achieved angle, t63, overshoot, fin per degree, return time | t63 0.14 ± 0.01 s; 0.99 ± 0.13° achieved at 825 Pa |
| 1700 | B | same step | same | t63 0.15 ± 0.01 s; 0.91 ± 0.09° at 444 Pa |

Gates, checked once at the start: q̄ ≥ 800 Pa, tilt ≤ 10°, altitude ≥ 30 m, control armed and healthy. Each step goes in whichever direction lowers the pair's current deflection, and a step is skipped if the pair is already past 14°. If the attitude wanders more than 8° from where the programme started, the programme is dropped and plain tilt-hold resumes. In the Monte Carlo no step was skipped and 26 of 80 axis-runs aborted, all in the windiest cases.

Results go to the flags in every log record (bit 3 doublet, bit 4 step, bit 5 skipped or aborted) and to `MANxxx.TXT` on the card. The firmware's manoeuvre code is also built for the desktop (`firmware/sil_host/`); `sil_check.py` replays simulated flights through it and its metrics agree with the simulator's to three decimals.

## 7. Host tool and test sketches (all compile for the Pico 2 W)

- `host/wyvern_host.py --decode WYFnnn.BIN`: the 96 B records to CSV. `--port`: live plot of the 10 Hz USB CSV the Pico prints on the pad, faulted or landed (never in flight, and only when the USB buffer has room). `--replay` re-plots a recording.
- `test_code/t1_i2c_scan`: scans both buses (expect 0x4A on I2C0; 0x76 and 0x77 on I2C1), then streams BMP388 and BME688 pressure side by side; they should agree within a few pascals once both have settled.
- `test_code/t2_servo_cal`: trim, sign, µs per degree, tunnel sweep.
- `test_code/t3_arm_log`: button, LED and SD soak test (replaces the LoRa range walk).
- `sync_headers.py` copies the shared headers into the test sketches; Arduino builds each sketch from a copy of its own folder, so includes into a sibling sketch break.

## 8. Electronics build sheet (rev 4)

Anything that changes from here goes into `fc_config.h` first, then `gen_wiring.py` (W1 to W5) and `sync_headers.py`.

### Boards and where they sit

| Board | Bus / pins | Spine face (bottom to top) | Mount |
|---|---|---|---|
| BNO085 (4754) | I2C0 0x4A, INT GP6, RST GP7 | +X, lowest board | 2 mm standoffs |
| Pico 2 W | everything | +X, upper (31-82 mm), USB down | 2 mm standoffs on its four 2.1 mm holes; leads soldered into the pads, no headers |
| BME688 (5046) | I2C1 0x77 | -Y, bottom (5-30 mm) | 9 mm pillars, one screw line |
| BMP388 (3966), ADDR jumper closed | I2C1 0x76 | -Y, middle (33-58 mm) | 9 mm pillars, one screw line |
| microSD (4682) + 32 GB card | SPI0, CS GP17 | -Y, top (62-87 mm), 14 mm plane so the card clears the button cradle | 7 mm pillars, one screw line; a strip of Kapton over the card |
| Arm button + LED | GP14 / GP15 | -Y wall cradle, 76 mm up | hot glue in the printed cradle |
| Power perfboard 16 x 62 mm | 2 x MPM3610, 1N5817, divider → ADC0, 470 µF | +Y | 9 mm pillars |
| Pololu 2810 switch | VIN / VOUT / GND to the perfboard | +Y wall cradle | hot glue, slide under the wall slot |
| 2S 450 mAh LiPo | XT30 to the perfboard | -X, 3-60 mm (moved down 11 mm so the 4682 clears it) | foam tape + 2 straps |
| 4 x EMAX ES9251 II | PWM GP10 / 11 / 12 / 13, SRV 5 V | servo ring below the spine | ears bolted to the wall pads |

The fit check (`3D parts/assembly/FIT_REPORT.md`) passes with the Pico, the 4682 (vendor model) and the button cradle in place: 0 faults.

### Harness

`Flight Computer/wiring/W5_harness.md` (and `.csv`) lists every connection with gauge, cut length and routing. There is one removable power joint (the XT30). The BNO085 and the BMP388 reach the Pico on STEMMA QT to male header cables (Adafruit 4209) with the header pins soldered into its holes; the BME688 hangs off the BMP388's second QT port on a 100 mm cable.

### Electronics cost (to buy)

| Group | Cost |
|---|---|
| Avionics: 2 Pico 2 W (flight + spare; out of stock at Adafruit and SparkFun on 2026-11-02, Amazon has them at $13.99), 2 Adafruit 4682, BNO085, BMP388, BME688, 3 QT-to-header + 1 QT cable | $84.20 |
| Actuation: 2 x EMAX ES9251 II 4-packs (no angle gauge: the printed zero jig and the tunnel AS5600 replace it) | $57.20 |
| Power: 2S 450 mAh 2-pack, charger, MPM3610 x3, Pololu 2810 x2, 1N5817 diodes, resistor kit | $92.17 |
| Total | $233.57 |

Already owned and off the list: wire, solder, heat-shrink, capacitors, LEDs, 6 mm buttons, perfboard, XT30s, microSD cards, screws and the hand tools. Every line in `WYVERN_BOM.xlsx` (Rocket section) carries a vendor link; checked 2026-11-02.

### Values to set on the bench before the first flight

| Setting | How |
|---|---|
| `WYV_SERVO_TRIM[4]` | t2: each fin trimmed until the printed `15_fin_zero_jig` slides on and off freely |
| `WYV_SERVO_US_PER_DEG` | each servo in the tunnel cradle: `a±10` on the Metro vs the AS5600's measured angle |
| `WYV_SERVO_SIGN[4]` | the SIGN CHECK in Build_and_Test §3 |
| `WYV_SERVO_HZ` | t2: if a servo buzzes or jitters at 200 Hz, drop to 50 |

### Bring-up order

1. Close the BMP388's ADDR jumper with a solder blob. Perfboard alone on a bench supply at 7.6 V, 0.5 A limit: the 2810 slide switches VSW, both bucks give 5.0-5.1 V, A0 reads VBAT × 47/147.
2. Pico on the perfboard: flash t1; I2C0 shows 0x4A, I2C1 shows 0x76 and 0x77, and the two pressures agree.
3. Servos: t2 with the pack through the switch. Set trims, µs per degree and signs.
4. t3 for 30 minutes with the flight card: zero dropped records, button and LED behave as in section 4.
5. Flight firmware: USB CSV at 10 Hz with `wyvern_host.py --port`, arm and disarm with the button, a `WYF*.BIN` file appears on the card and decodes.
6. SIGN CHECK and the manoeuvre dry run (Build_and_Test §3).
7. 25 minute pad soak. Expect about 35 mAh drawn.
