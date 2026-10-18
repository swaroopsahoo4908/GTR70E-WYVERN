# Electronics, power and telemetry

_Drawings (generated from `fc_config.h`): `Flight Computer/wiring/W1_wiring.png`, `W2_power_tree.png`, `W3_system.png`, `W4_spine_perfboard.png` (spine face map and the 16 x 62 mm power perfboard)._

## 1. Board choice: two Feather RP2040 RFM95s

The flight computer is the Adafruit Feather RP2040 with the onboard RFM95W 915 MHz LoRa radio (PID 5714). The ground station is a second, identical Feather: same radio, same pins, same RadioLib build and the same frame header, so there is one radio configuration to get right instead of two. It feeds a laptop over USB. There is no GPS (removed in rev 3d); recovery is by the buzzer beacon, the 6.3 m/s descent and the drift the simulator predicts.

- Telemetry range. The link has to cover a 236 m worst slant range from a body that tumbles under the chute. 915 MHz LoRa at +20 dBm closes it with about 57 dB to spare (`plots_link/link_budget.json`), and it keeps working while the rocket is in a field you are walking toward.
- One board, one antenna, no extra module on the bus. The radio, STEMMA QT port, 8 MB flash and uFL connector are all on a 51 x 23 mm board.
- The RP2040's two cores split the work the same way the TVC firmware did: core 0 runs attitude and control, core 1 runs the radio, baro and logging.
- Each core has its own I2C bus (rev 3c). Before, the BNO085 (core 0) and the BME688 (core 1) shared Wire1, and arduino-pico's Wire is not safe to drive from two cores at once. Now core 0 owns Wire1 (STEMMA QT: BNO085 + ADXL375) and core 1 owns Wire on the TX/RX pads (BME688).

The Pico 2 W is spare again (it still serves the tunnel balance DAQ).

## 2. Pin map

| Function | Feather pin | GPIO | Notes |
|---|---|---|---|
| Servo 0, A+ (az 0) | D5 | 5 | PWM 200 Hz, 1 µs resolution; all four servos in one ring |
| Servo 1, A- (az 180) | D6 | 6 | |
| Servo 2, B+ (az 90) | D9 | 9 | |
| Servo 3, B- (az 270) | D11 | 11 | separate PWM slices |
| I2C1 SDA / SCL (core 0) | STEMMA QT | 2 / 3 | Wire1, 400 kHz: BNO085 0x4A → ADXL375 0x53 (STEMMA chain) |
| I2C0 SDA / SCL (core 1) | TX / RX pads | 0 / 1 | Wire, 400 kHz: BME688 0x77 (STEMMA cable with the far end on the pads) |
| BNO085 INT / RST | D24 / D25 | 24 / 25 | data-ready and hard reset |
| microSD CS | D10 | 10 | Adafruit 4682 (3V only) on SPI1, shared with the radio (SCK 14, MOSI 15, MISO 8) |
| Battery sense | A0 | 26 | 100k / 47k divider + 100 nF, on the power perfboard |
| Buzzer | D12 | 12 | piezo through a 2N3904 |
| RFM95W | onboard | CS 16, RST 17, DIO0 21, DIO1 22 | uFL or wire whip |

## 3. Power

```
2S LiPo 450 mAh ──XT30── Pololu 2810 MOSFET switch ──VSW──┬── 4 x KST X08 Plus (HV, direct) + 470 µF
                          CTRL ── screw switch ── GND    ├── Pololu D24V10F5 → 5 V → Feather USB pin → 3V3 LDO → sensors, SD
                                                          └── 100k/47k divider → A0
```

- The internal switch is a screw switch reached with a hex key through a 3 mm hole in the control-tube wall (the hole lines up with the power perfboard on the spine's +Y face). The screw switch only carries the MOSFET board's control line, so its contact current is microamps and its contact resistance does not matter. The full servo current goes through the 2810's 16 mΩ MOSFETs: 3 A continuous at 55 °C, 12 A peak.
- Servos run straight off 2S. The X08 Plus is rated 3.8-8.4 V, which covers a full 8.4 V pack. Two caveats: Pololu says the 2810 is not meant as an emergency cutoff, and the 2S packs listed as "7.6 V HV" charge to 8.7 V, slightly above the servo's 8.4 V rating. Charge those packs to a standard 8.40 V (LiPo, not LiHV, mode on the charger).
- Logic runs from a dedicated 5 V buck feeding the Feather's USB pin. A servo stall can sag VSW, but the buck's 5.1 V minimum input keeps the RP2040 up until the pack itself is nearly flat.

### Battery sizing: 25 min idle + 1 min flight

From `Simulations/wf_power.py` (load table in `plots_power/battery_budget.json`):

| | current at the pack |
|---|---|
| Pad idle (RP2040, radio at 2 Hz, IMU, high-g, baro, SD, servos holding) | 103 mA |
| Flight (radio at 20 Hz, servos working) | 817 mA |
| Mission charge: 25 min idle + 1 min flight | 56.7 mAh |
| With 80 % depth of discharge, cold derate 0.85 and a 1.25 margin | 104 mAh |
| Pack | 450 mAh (owned): 4.3x margin, about 2 h 50 min of pad hold |

A 300 mAh 2S would also pass. The 450 stays because it is already owned and its mass sits on the forward side of the CG, where the vehicle wants mass anyway.

## 4. Telemetry link

| | |
|---|---|
| Band / modulation | 915 MHz LoRa, SF7, 500 kHz BW, CR 4/5, sync 0x57 |
| Frames | 'W' 42 B flight state (state, altitude, vertical speed, two tilts, three rates, three accelerations, four fins, q, battery, temperature, flags, authority t-statistic); 'M' 54 B manoeuvre result (per axis: doublet q, M_δ/I fit, t-statistic, measured/model ratio, step q, sign, achieved angle, t63, overshoot, return time, fin per degree, peak rate). Both CRC-16 |
| Schedule | pad: 2 Hz. Flight: 20 Hz. Manoeuvre result: 5 slots after the programme ends. Landed: 2 Hz |
| Time on air | 21.8 ms for the 42 B frame → 20 Hz in flight (44 % duty) |
| Budget | +20 dBm, 2.1 dBi whip in the rocket, 1.2 dBi Linx whip on the ground, 10 dB orientation null, 1 dB cable → 51.7 dB margin at 236 m |
| Uplink | pad only, in a 120 ms receive window after each pad frame: ARM, DISARM, ZERO, PING; keyed + CRC + replay guard; closed at launch detect |

The 500 kHz bandwidth keeps each frame short enough for 20 Hz. Check that your use fits FCC Part 15.247 for the 902-928 MHz band (or operate under an amateur licence) before flying.

## 5. Firmware

`Flight Computer/firmware/wyvern_fin/` builds with arduino-pico 6.x for "Adafruit Feather RP2040 RFM" (Flash Size "8MB (no FS)"). It compiles at 132 kB.

Logging is microSD only from rev 3c. The 8 MB QSPI chip still holds the program; it just no longer carries a LittleFS copy of the log. The card sits in a push-push socket on the spine, the vehicle lands at about 6 m/s, and the 20 Hz downlink is already a second record of every flight channel that matters.

| File | Job |
|---|---|
| `fc_config.h` | every pin, gain and limit, copied from the sim outputs |
| `attitude.h` | BNO085 game rotation vector on the pad; own gyro-quaternion propagation from launch, because accel tilt-correction is wrong under thrust |
| `highg.h` | ADXL375 ±200 g axial channel. The BNO085 accelerometer clips at 8 g; the F42-4T ignition spike reaches 8.2 g (an F67-6W would hold 11 to 12 g for 0.65 s). Above 7 g the vertical channel switches to the ADXL375, whose offset is learned against the BNO on the pad, so q̄ and the gain schedule stay right through boost |
| `controller.h` | q-scheduled PID per axis, roll-rate damping, 4-regressor authority monitor, the authority-demonstration manoeuvre (`ManeuverSeq`) |
| `fin_mixer.h` | pitch / yaw / roll to four fins, roll gets a reserved 5 deg budget, slew limit, trims and signs |
| `telemetry.h` | RadioLib SX1276, non-blocking TX, the three downlink frames, pad uplink parser |
| `logger.h` | 96 B records at 100 Hz to microSD (adds the attitude references and the axial channel), plus `MANxxx.TXT`, a one-line-per-axis summary of the manoeuvre |
| `wyvern_fin.ino` | core 0 control at 200 Hz, core 1 baro / radio / logging, seqlock hand-off |

State machine: BOOT → SELFTEST → PAD ⇄ ARMED → BOOST (rail) → CONTROL → COAST → DESCENT → LANDED, with FAULT from any state. Rev 3d keeps CONTROL until q̄ falls below 15 Pa after burnout (about 0.7 s before apogee); it used to stop at a 15 m/s climb rate, about 1.5 s before apogee.

Safety logic:
- Fins only move in flight if the rocket was ARMed on the pad. Unarmed, it still logs and transmits.
- Fins go to neutral and stay there on: tilt > 30 deg, IMU stale > 20 ms, battery < 6.4 V, or the authority monitor finding a reversed control derivative (t < -3) right after rail exit. The airframe is passively stable at 1.01 cal with the fins centred.
- Gains: δ[rad] = S(q)·(4.5·θ + 1.0·∫θ + 0.8·ω), with S = clamp(1500 Pa / q, 0.15, 4.0), re-tuned for the rev 3d airframe on the F42-4T (the grid search keeps the same gains). Both pairs sit at one station, so axis B uses the same gains (scale 1.0).

## 6. Authority-demonstration manoeuvre

One programme per flight, in early coast, so authority is measured rather than inferred. On the F42-4T it starts 250 ms after burnout (1.72 s) and runs 2.6 s. The predicted values below are for the rev 3d airframe in a 4 m/s wind (`Simulations/plots_flight/maneuver_prediction.json`); spreads are 1 sd over 40 flights in 0 to 7 m/s wind.

| ms after start | Axis | What happens | What it measures | Predicted |
|---|---|---|---|---|
| 0 | A | ±5° doublet added to the PID output, 120 ms per half | M_δ/I by least squares (ω̇ = c + aθ + m_q ω + bδ), its t-statistic, and the ratio to the model's 0.0322 · q̄ | 40 1/s² at 1.2 kPa; fit/model 0.95 ± 0.10 |
| 400 | B | same doublet | same | 32 1/s² at 1.0 kPa; fit/model 0.95 ± 0.12 |
| 800 | A | attitude reference stepped 1° for 500 ms, then back to vertical hold for 400 ms | achieved angle, t63, overshoot, fin per degree, return time | t63 0.15 ± 0.01 s; 0.98 ± 0.11° achieved at 760 Pa |
| 1700 | B | same step | same | t63 0.16 ± 0.01 s; 0.93 ± 0.07° at 400 Pa |

Gates, checked once at the start: q̄ ≥ 800 Pa, tilt ≤ 10°, altitude ≥ 30 m, control armed and healthy. Each step goes in whichever direction lowers the pair's current deflection, and a step is skipped if the pair is already past 14°. If the attitude wanders more than 8° from where the programme started, it is dropped and plain tilt-hold resumes. On the rev 3d airframe no step was skipped in the Monte Carlo and 10 of 80 axis-runs aborted, all in the windiest cases. The doublet fit is three times tighter than on rev 3c (±0.10 against ±0.31) because the stiffer, steadier airframe leaves less unmodelled motion in the window.

Results go three places: flags in every frame (bit 3 doublet, bit 4 step, bit 5 skipped or aborted, bit 6 high-g channel in use), the 'M' frame five times after the programme ends, and `MANxxx.TXT` on the card.

The firmware's manoeuvre code is also built for the desktop (`firmware/sil_host/`). `sil_check.py` replays simulated flights through it and compares its metrics with the simulator's; they agree to three decimals.

## 7. Ground station and test sketches (all compile)

- `ground_station/wyvern_ground/`: second Feather RP2040 RFM95. Decodes both frames and prints tagged CSV lines on USB (T and M). Uplink commands: ARM / DISARM (retried until the downlinked state shows them), SERVO / ZERO / PING (sent once).
- `ground_station/host/wyvern_host.py`: records each line type to its own CSV, live plot, prints the manoeuvre result, decodes the 96 B SD records.
- `test_code/t1_i2c_scan` scans both buses and streams the ADXL375 axes so `WYV_ADXL_AXIS` / `WYV_ADXL_SIGN` can be set with the rocket standing nose-up; `t2_servo_cal` (trim, sign, µs-per-degree, tunnel sweep); `t3_lora_range`.
- `sync_headers.py` copies the shared headers into the other sketches. Arduino builds each sketch from a copy of its own folder, so includes that reach into a sibling sketch break.

## 8. Final electronics build sheet (rev 3d, frozen)

The pin map, buses and parts below are frozen for the build. Anything that changes from here goes into `fc_config.h` first, then `gen_wiring.py` (W1 to W5) and `sync_headers.py`.

### Boards and where they sit

| Board | Bus / address | Core | Spine face (bottom to top) | Mount |
|---|---|---|---|---|
| Feather RP2040 RFM95 (5714) | SPI1 radio CS GP16 | both | +X, upper | 2 mm standoffs |
| BNO085 (4754) | Wire1 0x4A, INT GP24, RST GP25 | 0 | +X, lowest board | 2 mm standoffs |
| ADXL375 (5374) | Wire1 0x53 | 0 | -Y, top | 9 mm pillars, one screw line |
| BME688 (5046) | Wire 0x77 (TX / RX pads) | 1 | -Y, bottom | 9 mm pillars, one screw line |
| microSD 3V (4682) + 32 GB card | SPI1, CS GP10 | 1 | -Y, middle | 9 mm pillars, one screw line |
| Power perfboard 16 x 62 mm | 2810 switch, D24V10F5 buck, divider → A0, NPN buzzer on GP12, 470 µF | — | +Y | 9 mm pillars |
| 2S 450 mAh LiPo | XT30 to the perfboard | — | -X | foam tape + 2 straps |
| 4 x KST X08 Plus | PWM GP5 / GP6 / GP9 / GP11, VSW direct | 0 | servo ring below the spine | ears bolted to the wall pads |

Ground station: a second Feather RP2040 RFM95, uFL → SMA pigtail → Linx ANT-916-CW-HW-SMA whip (the Yagi was dropped: no verifiable SMA listing, and the whip still leaves 51.7 dB of margin), USB-C to the laptop. Nothing else is wired to it.

### Harness

`Flight Computer/wiring/W5_harness.md` (and `.csv`) lists all 25 connections: from, to, signal, wire gauge, cut length and routing. There is one removable power joint (the XT30). The servo power leads are soldered to the perfboard's VSW / GND bus. The servo signals go straight to the Feather pins. Both I2C buses use STEMMA QT cables, and the BME688 reaches the TX / RX pads through a QT-to-header cable.

### Electronics cost (to buy)

| Group | Cost |
|---|---|
| Avionics: 3 Feathers (flight, ground, spare), ADXL375, microSD x2, cables, ground whip, solderable board, buzzer parts | $155.05 |
| Actuation: 5 x X08 Plus (1 spare), Wixey WR300 angle gauge | $259.99 |
| Power: buck x2, MOSFET switch x2, screw switch, XT30 pigtails with 470 µF | $55.87 |
| Total | $470.91 |

Every line in `WYVERN_FIN_BOM.xlsx` carries a vendor product link checked on 2026-10-16.

The BNO085, BME688, LiPo, charger, wire and passives are already owned.

### Values to set on the bench before the first flight

| Setting | How |
|---|---|
| `WYV_ADXL_AXIS`, `WYV_ADXL_SIGN` | t1 sketch with the rocket nose-up: the axis that reads about +1 g with that sign |
| `WYV_SERVO_TRIM[4]` | t2: each fin to 0.0 ± 0.2° on the angle gauge |
| `WYV_SERVO_US_PER_DEG` | t2: µs for ±10° on the gauge |
| `WYV_SERVO_SIGN[4]` | the SIGN CHECK in Build_and_Test §3 |
| `WYV_UPLINK_KEY` | change from the default; the ground station gets the same value through `sync_headers.py` |

### Bring-up order

1. Perfboard alone on a bench supply at 7.6 V with a 0.5 A limit. Check that the screw switch turns VSW on and off and that the buck gives 5.0–5.1 V. Check A0 against a meter: VBAT × 47/147.
2. Feather alone on USB: flash t1 and confirm both buses show only their expected addresses (Wire1: 0x4A, 0x53; Wire: 0x77).
3. Servos: run t2 with the pack connected through the switch. Set trims, µs per degree and signs.
4. Radio: run t3 between the two Feathers, then a range walk to 300 m with the airframe on its side.
5. Flight firmware on the pad: 2 Hz frames, ARM / DISARM / ZERO from the laptop, a `WYF*.BIN` file appears on the card, buzzer chirps.
6. SIGN CHECK and the manoeuvre dry run (Build_and_Test §3).
7. 25 minute pad soak. Expect about 57 mAh drawn.
