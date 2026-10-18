# GTR70E WYVERN, Component Compatibility Audit

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


**Scope:** Every I2C, SPI, PWM, ADC, and power pairing across the flight computer (**Raspberry Pi
Pico 2 W** on a 20 x 24 perfboard, `wyvern4_tvc.ino` + headers) and the ground-test rig (3-axis TVC
balance harness + static thrust stand), cross-checked against the BOM part list and the pin map in
`Flight Computer/firmware/wyvern4_tvc/wyvern_config.h`.

**Sources examined:** `Flight Computer/firmware/wyvern4_tvc/*.{ino,h}`, `Flight Computer/wiring/wyvern_perfboard_wiring.svg` + `wyvern_bay_layout.svg`, `Flight Computer/test_code/*`, `Flight Computer/flowcharts/*.mermaid`, `Flight Computer/01_FlightComputer_Spec.md`, `Documentation/CANONICAL_NUMBERS.md`, and all files under `Documentation/`.

Every pairing below is traced against the perfboard wiring diagram and `wyvern_config.h`.

**Architecture note.** The Pico 2 W perfboard (Ø62 mm, bare RP2350 QFN-80) is retired; it lives in
`Past Iterations/the perfboard (retired)/`. The flight computer is now a Pico 2 W carrying four Adafruit
STEMMA-QT breakouts on one shared I2C bus: BNO085 bay (0x4B), BNO085 gimbal (0x4A), BME688 (0x76),
BMP388 (0x77), plus a microSD breakout on SPI1. Power is 2S LiPo -> PPTC -> arming switch -> 5 V
switching UBEC.

**What this audit can and cannot verify:** the audit is a *static* review of source, wiring generators, and documentation, it confirms what is wired, coded, and internally consistent, and flags what is not. It cannot confirm bench-measured current draw, actual signal levels on a physical harness, or I2C bus electrical margin (capacitance, pull-up value, rise time), those require a meter and an oscilloscope on real hardware. Every current-draw figure below is a **datasheet/vendor-typical estimate**, explicitly labeled, not a measurement.

---

## Summary Table

| # | Pairing | Verdict | One-line reason |
|---|---|---|---|
| 1a | I2C0 shared bus, address map (no mux) | **PASS** | No address collisions; bay BNO085 (0x4B), external BNO085 (0x4A), BME688 (0x76) coexist on one bus by address |
| 1b | INA226 (U4) power monitor | **DEFECT, bench-confirm before trusting** | Reads the buck's VBUCK output, not pack voltage; address strap not cleanly wired to a documented option |
| 1c | I2C bus speed vs. device max rate | **PASS** (default Wire.begin() clock, see note) | Arduino-Pico default 100 kHz is within all device families' rated range |
| 1d | VL53L4CD ToF ranging | **N/A, not part of the design** | Gimbal deflection is measured by the 3-axis load balance; no ToF hardware, driver, or XSHUT plan is needed |
| 2 | SPI0 microSD (GP8/9/10/11) | **PASS** | Dedicated 4-wire bus, no sharing, no conflicting CS |
| 2b | HX711 (ground rig) mislabeled as SPI | **CAUTION, terminology** | HX711 uses a proprietary 2-wire DT/SCK protocol, not SPI |
| 3 | PWM servo outputs (GP2/GP3) | **PASS** | Two independent PWM slices, standard hobby-servo timing, travel-limited in software |
| 3b | Ground-rig solenoid PWM via IRF520 | **CAUTION** | No PWM frequency/flyback-diode spec found in provided docs |
| 4 | RBF sense (GP12) | **OPEN, not wired to any switch** | GP12 floats HIGH as fabricated; arming safety is currently the U13 power switch alone |
| 4b | Load cells (ground rig) vs. the perfboard ADC | **PASS (non-issue)** | HX711 has its own 24-bit ADC; consumes 0 RP2350 ADC channels |
| 5a | Recovery = F15-4 motor ejection separating the two BTs at the bulkhead joint | **PASS, no recovery electronics** | Motor's own charge; no UART tap, no recovery battery, no pyro driven by the FC |
| 5b | BSS138 level shifter | **N/A, not needed** | No 5 V→3.3 V UART line in this design; drop from BOM if still listed |
| 5c | 2S LiPo → onboard UBEC buck → shared 5 V rail (servos + camera), no discrete UBEC | **PASS w/ decoupling** | Onboard buck drives the servo/camera rail; 3.3 V logic comes off the board's LDO stage |
| 6a | Ground-rig DAQ board | **PASS** | Both rig wiring blocks specify a Raspberry Pi Pico / Pico 2 W DAQ — separate bench hardware, not the flight computer |
| 6b | Ground-rig GPIO budget (Pico substitution scenario) | **PASS, comfortable margin** | 10 of 26 GPIO pins consumed |

---

## 1. I2C, Address Collisions & Bus Loading

### 1a. I2C0, single shared bus (GP0 SDA / GP1 SCL, no mux), PASS

This board carries **no PCA9548A** and **no second I2C controller**. Every I2C device shares one
bus, differentiated purely by address:

- body **BNO085** (U2), `0x4B` — COM3/ADR pin traces to GND
- external **BNO085** (STEMMA-QT, CN2), `0x4A` — Adafruit breakout default
- **BME688** (U3), `0x76` — CSB tied 3V3 (I2C mode), SDO tied GND (address-select)
- **INA226** (U4), address strap not cleanly wired — see §1b
- **LIS3MDL** magnetometer part is present in the BOM/schematic device list but is not currently
  driven by any firmware file; not a collision risk, just unused hardware

No address collisions: BNO085 (0x4B), BNO085 (0x4A), and BME688 (0x76) are all distinct, and none
overlaps INA226's likely range. **Verdict PASS.**

### 1b. INA226 (U4) power monitor, DEFECT — bench-confirm before trusting

Two real hardware findings, traced pin-by-pin against the netlist (not firmware bugs — see
`firmware/wyvern4_tvc/battery.h`'s file header for the full derivation):

- **Wrong node.** VBUS/VIN- trace to VBUCK (the UBEC's output, ~4.98 V calculated), not the raw
  2S pack input. `getBusVoltage()` reads the regulated rail, not the 6.0–8.4 V pack range, so the
  project brief's 6.4 V/6.0 V pack cutoffs don't apply as wired. VIN+/VIN- also don't span a real
  series shunt, so current/power readings aren't physically meaningful.
- **Ambiguous address strap.** A1 sees ~5 V (off VBUCK through R10), which is neither GND nor this
  chip's own VS+ (tied to 3V3) — not one of the INA226's four documented address options. `0x40` is
  the current bench-scan candidate (`test_code/t1_i2c_scan.ino`), not a confirmed address.

**Neither finding is firmware-fixable** — the real fix is a board revision routing U4 across an
actual pack-current shunt. `battery.h` uses rail-sag thresholds as an interim software workaround.
**Verdict: DEFECT, tracked, do not treat `battery.h`'s output as a true pack-voltage reading until
bench-confirmed.** See `CONFLICTS.md` §3.

### 1c. I2C bus clock speed, PASS

`wyvern4_tvc.ino` initializes the bus with `Wire.setSDA(SDA0); Wire.setSCL(SCL0); Wire.begin();`,
**no explicit `setClock()` call is present**, so the bus runs at the Arduino-Pico core's default of
100 kHz (standard mode). BNO085, BNO085, BME688, and INA226 all support both 100 kHz and 400 kHz per
their datasheets, so 100 kHz is safely within spec, **PASS**, though the single shared bus carries
every sensor's traffic (2 IMUs + baro + power monitor) at only 100 kHz — a design headroom choice,
not a defect. If bench timing margin ever becomes tight at 500 Hz control-loop rate, an explicit
`Wire.setClock(400000)` is the lever to pull.

### 1d. VL53L4CD ToF ranging, N/A

Time-of-Flight ranging is not part of this design. Gimbal deflection on the solenoid balance rig is
taken from the 3-axis load balance (thrust vector) plus the gimbal BNO085, so no ToF ring, driver,
or XSHUT/address plan is required, and none exists anywhere in the repo.

---

## 2. SPI

### 2. SPI0 microSD (GP8 MISO / GP9 CS / GP10 SCK / GP11 MOSI), PASS

`sd_logger.h` pins are unambiguous and confirmed against CARD1's actual pinout: MISO=GP8 (DAT0/D0),
CS=GP9 (DAT3), SCK=GP10 (CLK), MOSI=GP11 (CMD/DI). This is the sole SPI0 device on the flight
computer, no bus sharing, no second CS line to arbitrate, and core-1's FIFO-drain/burst-write
architecture is built specifically so SD writes can stall for milliseconds without ever jittering
the control loop on core 0. **Verdict PASS.**

### 2b. HX711 (ground rig), CAUTION, terminology only

The BOM lists three NOYITO HX711 load-cell amplifiers on the balance rig (5 kg axial + 2x1 kg
lateral) and a fourth on the separate static-thrust stand. The HX711 is **not an SPI device**, it
uses a proprietary 2-wire synchronous serial protocol (one `DT` data-out pin, one `SCK` clock-in pin
per channel), read by bit-banging. `gen_wiring4.py`'s own labels reflect this correctly. **No fix
required; documentation precision only:** each HX711 channel consumes **2 GPIOs** (DT + SCK), not a
shared SPI bus.

---

## 3. PWM

### 3. Flight TVC servos (GP2 pitch / GP3 yaw), PASS

`wyvern4_tvc.ino`: `#define PIN_SERVO_P 2 // pitch servo, JST connector U8`, `#define PIN_SERVO_Y 3
// yaw servo, JST connector U9`, driven through the Arduino-Pico `Servo` library, with commands
clamped to `±8.0 deg` (via `wyvern_pid.h OUT_LIM_DEG=8.0`) before being written, matching the
CONFLICTS.md frozen value and the EMAX ES08MA II's mechanical/electrical rating as a standard-PWM
analog micro servo (~1.8 kg·cm at 5 V, well above the ~0.56 kg·cm gimbal demand). Two independent
RP2350 PWM slices, no pin sharing, no conflict. **Verdict PASS.**

### 3b. Ground-rig solenoid actuator (50N 12V solenoids x2 via IRF520, "Actuator A" swap-in), CAUTION

`gen_wiring4.py`'s balance-harness block lists the alternate actuator driven over IRF520 MOSFET
modules on PWM-capable pins. `WYVERN_E4_GSE_TestStands.md` documents the rig's load-cell/mechanical
design in detail but **does not specify** a PWM switching frequency for the solenoid drive, nor call
out flyback-diode protection explicitly. **Recommendation:** before energizing, confirm (a) the
IRF520 module's onboard flyback diode is rated for the solenoid's stored energy at 12 V, and (b) a
PWM frequency is chosen and documented — a **documentation and pre-bench-test gap**, not a wiring
error.

---

## 4. GPIO / Arming

### 4. RBF sense (GP12, H1 pin13), OPEN — not wired to any switch

There is **no software-readable remove-before-flight pin on the perfboard as fabricated**. U13 (the physical
slide switch near the power path) traces to nothing on U1 in the netlist — both its terminals sit in
the power domain, not on any GPIO. GP12 is kept wired to an `INPUT_PULLUP` software gate as a hook
for a future bodge wire (H1 pin13 to GND), but as fabricated nothing is soldered there, so it floats
HIGH and `g_rbf_pulled` always reads true. **Arming safety today is entirely U13 being a literal
power switch.** **Verdict: OPEN, action item, not a PASS** — see `FLIGHT_READINESS.md` §4 item 4.

### 4b. Ground-rig load cells vs. the perfboard ADC, PASS (non-issue, worth stating explicitly)

The HX711 modules each carry their **own onboard 24-bit ADC** for the strain-gauge bridge and
consume **zero** channels of RP2350's onboard ADC. There is no shared/contended ADC resource
between flight and ground-rig hardware, and battery monitoring on the flight side runs through the
INA226 on the shared I2C bus (§1b), not the ADC.

---

## 5. Power

### 5a. Recovery = F15-4 motor ejection separating the two BTs at the bulkhead joint, PASS (no recovery electronics)

Recovery is the F15-4 motor's own ejection charge, fired 4 s after burnout (t ≈ 7.45 s),
pressurizing the Lower BT and separating the two body tubes at the bulkhead joint (see
`WYVERN_E4_Recovery.md`, `Simulations/we4_ejection_feasibility.py`). The flight computer drives **no**
pyro or deploy hardware whatsoever, it only logs baro/IMU; telemetry is log-only, not streamed.
**Verdict: PASS.**

### 5b. BSS138 level shifter, N/A

The BSS138 has no function in this design — there is no 5 V→3.3 V UART line anywhere in the
architecture to shift. Drop it from the BOM if still listed. **N/A.**

### 5c. 2S LiPo → onboard UBEC buck → shared 5 V rail, no discrete UBEC, PASS with required decoupling

The power tree is a **2S LiPo (7.4 V, ~450 mAh) → the perfboard's XT30 input → onboard UBEC buck (U15,
~5 V output) → servo/camera rail**, with 3.3 V logic coming off the board's own LDO stage. There is
**no discrete UBEC module** in this design — the project brief's "one 5 V UBEC" language describes
this onboard buck, not an added part.

- **Shared-rail decoupling is the real design trade** of driving servos and logic off one onboard
  rail: bulk capacitance and hold-up protection at the servo feed and the logic feed are needed so a
  ~1 A servo-stall transient can't sag the board's own supply enough to reset the MCU — confirm the
  actual bulk-cap/Schottky placement against the fabricated board.
- Recovery carries no isolated battery or deploy rail of its own, since it is entirely motor-driven.

**Verdict PASS**, contingent on bench-confirming the onboard decoupling is adequate.

### Power budget, datasheet estimates only (explicitly not bench-measured)

The following are vendor/datasheet-typical figures, not measurements on this hardware, provided only
to sanity-check that the buck/pack are not obviously undersized:

| Load on the 5 V rail | Detail | Typical draw (datasheet/vendor, estimated) |
|---|---|---|
| Logic + sensors + camera | Custom the perfboard (RP2350, no radio active) + bay BNO085 + external BNO085 + BME688 + i3 4K Thumb Action Camera | RP2350 logic on the order of tens of mA; each IMU on the order of 10–15 mA typical fusion-mode; BME688 low single-digit mA; camera vendor-quoted around 100–150 mA recording |
| 2× servos (run at 5 V) | 2× EMAX ES08MA II (analog, as purchased) | Vendor-quoted no-load current in the tens of mA per servo, with stall current on the order of roughly 1 A per servo possible under load — two servos stalling simultaneously is the design corner case the onboard bulk cap/hold-up is sized to ride out |

A 2S 450 mAh pack covers this aggregate draw with comfortable pad + flight endurance. **This audit
cannot certify actual current draw or brown-out margin** — that requires a bench multimeter/current-
clamp session under worst-case simultaneous load (servos slewing + camera recording + SD burst
write), watching the 5 V rail on a scope during a servo stall to confirm it holds above brown-out.

---

## 6. Ground-Test Rig GPIO Budget & DAQ Board

### 6a. Ground-rig DAQ board, PASS: Raspberry Pi Pico / Pico 2 W

Both ground-rig wiring blocks in `gen_wiring4.py` specify a **Raspberry Pi Pico / Pico 2 W** DAQ,
matching `WYVERN_E4_GSE_TestStands.md` and the BOM — this is separate, off-the-shelf bench hardware
running the ground rigs' DAQ, entirely distinct from the flight computer (Pico 2 W perfboard). All rig DAQ
boards are 3.3 V-logic RP2040/RP2350 parts, native-compatible with the HX711 DT/SCK lines and
STEMMA-QT I2C at 3.3 V; there is no 5 V↔3.3 V level-shift needed. **Verdict PASS.**

### 6b. Ground-rig GPIO budget, PASS

A GPIO budget for the Pico/Pico 2 W-based ground rig (26 usable GPIO pins):

| Function | GPIO pins consumed |
|---|---|
| 3× HX711 (axial Z, lateral X, lateral Y), 2 pins each (DT+SCK) | 6 |
| Gimbal-feedback BNO085 (I2C) | 2 |
| IRF520 solenoid PWM drive x2 (Actuator-A variant only) | 2 |
| Servo PWM x2 (Actuator-B variant only, mutually exclusive with the 2 solenoid PWM above) | 2 |
| **Subtotal** | **10 of 26** |

Fits with wide GPIO margin. **Verdict PASS.**

---

## Findings Requiring Resolution Before Flight/Bench Use

1. **INA226 (U4) wiring defect.** Reads VBUCK, not pack voltage; address strap ambiguous. Needs a
   board revision for a true fix; `battery.h`'s rail-sag workaround is interim only. See §1b.
2. **RBF sense (GP12) is not wired to any switch.** Arming safety is currently the U13 power switch
   alone. See §4.
3. **IRF520 solenoid drive (ground rig) has no documented PWM frequency or confirmed flyback-diode
   adequacy** for the 50N/12V solenoid's inductive turn-off transient in the provided documentation.
4. **All power-budget figures in Section 5 are datasheet/vendor estimates, not bench measurements.**
   A current-clamp/multimeter session per rail under worst-case simultaneous load is required.
5. **LIS3MDL is present in the BOM/schematic but not driven by any firmware file.** Decide whether
   it's a future-use part or should be dropped, and update the BOM/notes accordingly.

---

*Audit compiled from static review of the GTR70E WYVERN firmware/wiring/documentation bundle and the BOM. No physical hardware was measured; all "PASS" verdicts reflect internal design/documentation consistency, not bench validation.*

## References

CEVA, Inc. (2023). *BNO08X datasheet* (Rev. 1.17). https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf

EMAX. (n.d.). *ES08MA II 12 g mini metal gear analog servo* [Product specification]. Retrieved August 12, 2026, from https://www.getfpv.com/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model.html

Estes Industries. (n.d.). *F15-4 engines* [Product specification]. Retrieved August 12, 2026, from https://estesrockets.com/products/f15-4-engines

Federal Aviation Administration. (n.d.). *14 CFR Part 101 — Moored balloons, kites, amateur rockets, and unmanned free balloons*. Electronic Code of Federal Regulations. https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101

National Fire Protection Association. (2018). *NFPA 1122: Code for model rocketry*. https://www.nfpa.org/product/nfpa-1122-code/p1122code

Raspberry Pi Ltd. (2024). *RP2350 datasheet*. https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

Texas Instruments. (n.d.). *UBEC: 4.5-V to 17-V input, 4-A synchronous step-down voltage regulator* (SLVSFB5) [Datasheet]. https://www.ti.com/lit/ds/symlink/tps564201.pdf
