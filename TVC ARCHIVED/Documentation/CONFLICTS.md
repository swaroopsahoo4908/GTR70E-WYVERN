# GTR70E WYVERN, Flight Computer Specification & Frozen Parameter Table

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Date:** 2026-08-12  
**Program:** GTR70E WYVERN


This is the single source of truth for the flight computer's firmware parameters, recovery
architecture, avionics wiring, and structural fit checks. The firmware, wiring generators, and CAD
are all written directly against the values below.

## 1. PID gains

The pitch and yaw TVC loops run decoupled, identical gains on each axis: **Kp=0.10, Ki=0.40,
Kd=0.18**, output-clamped to ±8.0° gimbal deflection (`OUT_LIM_DEG=8.0` in `wyvern_pid.h`), with a
derivative filter time constant of 0.02 s and an integral clamp of ±0.4 for anti-windup.

These gains come from a phase/gain-margin sweep across 24 operating points: 4 atmospheres (ISA
T_sl=288.15K, cold=258.15K, hot=313.15K, high-DA=298.15K) × 6 burn-time slices (0.6/1.0/1.7/2.5/
2.9/3.4 s into the 3.45 s burn), with the servo modeled as `TAU_SERVO=0.04 s` plus a ~2 ms Padé-2
transport delay. Kp=0.10/Ki=0.40/Kd=0.18 clears a 30° phase-margin target at every point in the
sweep, with a worst-case **PM=44.1°, GM=12.6 dB**. Full margin tables in
`Documentation/PID_TUNING_REPORT.md`; the search itself is `Simulations/we4_pid_retune.py`. The
mermaid control-loop flowchart (`Flight Computer/flowcharts/02_tvc_control_loop.mermaid`) and
`we4_atmos_tvc.py`'s in-file defaults are both written to this same table.

## 2. Recovery architecture: motor ejection at the bulkhead joint

Recovery is fully passive, driven by the F15-4 motor's own ejection charge. The charge fires 4 s
after burnout (t = 7.45 s, 0.78 s past apogee), pressurizes the Lower BT (TVC bay side), and
separates the two body tubes at the bulkhead joint between Lower BT and Upper BT — a dual-deploy-
style break, not a friction-fit nose pop off a single continuous tube. Full mechanism detail in
`WYVERN_E4_Recovery.md` and the feasibility numbers in `Simulations/we4_ejection_feasibility.py`.

There is no altimeter-triggered deploy, no recovery battery, no e-match/black-powder charge, and no
CO2 system anywhere on the vehicle — the finned airframe (4×87 mm, +1.14 cal, 720 g liftoff) is
stable to apogee, so a single passive event just past apogee is the whole recovery sequence. The
flight computer never drives recovery; the motor does. The Pico only observes: it logs baro/IMU
through the event for apogee/landing reconstruction and streams WiFi telemetry. No deploy-logic
module exists in the firmware.

## 3. Power architecture: 2S LiPo → buck + LDO chain, INA226 battery sense

The entire avionics domain runs off a light 2S LiPo (7.4 V, ~450 mAh; Zeee 4-pk). On PCB1 the pack
feeds a **TPS564201 buck regulator** (U15) down to an intermediate rail, then an **AP2112K-3.3
LDO** (U7) for the 3.3 V logic rail; the four JST servo/expansion connectors (U8-U11) draw off the
buck rail directly rather than the Pico-VSYS-style single-5V-rail arrangement an earlier version of
this document assumed. The servos run fine on this rail (~1.8 kg·cm, >2× the ~0.56 kg·cm demand).

An **INA226** (U4) sits on the shared I2C bus, but tracing every one of its pins through
`Netlist_PCB1_2026-08-11.tel` — not assuming a textbook shunt-monitor hookup — turned up two real
wiring problems, not just addressing trivia:

- **It doesn't read pack voltage.** U4's VBUS (pin 8) and VIN- (pin 9) trace to the VBUCK net — the
  buck's *output* (~5 V, see the R5/R6 estimate below) — not to CN1/the raw 2S input. VIN+ (pin 10)
  traces to GND. The pack voltage itself never reaches this chip. `getBusVoltage()` will report the
  regulated rail, not the battery.
- **VIN+/VIN- don't span a real shunt.** R10 (10 mΩ, 2512, the part that reads like a current shunt
  on the BOM) sits in parallel with the power switch U13, both bridging VBUCK to a floating-ish
  node — not in series with pack current. `getCurrent()`/`getPower()` have nothing real to measure
  through this path; `battery.h` no longer calls `setMaxCurrentShunt()` or exposes a current reading
  for that reason.
- **The address strap looks wrong too.** A0 (pin 2) ties cleanly to GND. A1 (pin 1) ties to the same
  node as R10/U13, which sits at roughly VBUCK (~5 V) — not one of the INA226's four valid
  address-strap levels (GND/VS+/SDA/SCL), and higher than this chip's own VS+ (3.3 V, pin 6). The
  resulting address is not reliably predictable from the datasheet's strap table, and pushing ~5 V
  into an address pin on a 3.3 V-rail part is worth checking against absolute-max ratings before
  repeated power-cycling, not just an inconvenience to work around in software.

None of this is a firmware bug — it's how U4 is wired on PCB1. The real fix is a board revision:
route VIN+/VIN- across a shunt actually in series with pack current, tie A1 to a valid strap level,
and give VBUS its own trace to the pack side of the switch. Until then, `battery.h`'s
`BatteryMonitor` reports rail-sag thresholds (provisional, ~4.85 V warn / ~4.60 V critical, reasoned
from the buck's typical dropout margin, not bench-measured) rather than the 6.4 V/6.0 V
LiPo-per-cell thresholds a true pack monitor would use — and those rail-sag thresholds will trip
*after* the pack is already well past a safe per-cell floor, not before. Treat this reading as
rail-health telemetry, not the vehicle's LiPo protection; keep charging and checking the pack
separately with a cell-voltage checker before every flight. Full pin-by-pin trace and address-strap
concern in `Flight Computer/firmware/gtr70e_wyvern_tvc/battery.h`'s file header.

The buck's own output is estimated at **Vout ≈ 0.768 V × (1 + R5/R6) = 0.768 × (1 + 56 kΩ/10.2 kΩ)
≈ 4.98 V**, using the TPS564201 family's typical 0.768 V feedback reference — R5/R6 values are
netlist-confirmed, the 0.768 V reference is a typical-family value, not read off this exact part's
datasheet, so bench-verify the actual rail with a multimeter rather than trusting the estimate to
the millivolt.

The earlier GP26/ADC0, 100kΩ/62kΩ-divider description of this section was never physically correct
for PCB1: RP2350B's ADC-capable pins are GPIO40-47, not GPIO26-29 (that pin range only exists on the
RP2350A/Pico-2-module silicon), and no matching divider circuit exists anywhere in the real BOM or
netlist.

## 4. Frozen parameter table

Every row below is drawn from the real PCB1 fabrication package, traced pin-by-pin against
`PCB/Netlist_PCB1_2026-08-11.tel` and cross-checked against the labeled pin names in
`PCB/SCH_Schematic1_1-P1_2026-08-11.svg` (the vector schematic — its embedded text carries real
pin-position data, unlike the earlier pass's PDF text-extraction, which read out of visual order and
produced two wrong claims: an invented SWDIO/SWCLK pair on H1, and an unverified BNO055 address).
That second pass is what put this table in its current state — **confirmed** rows are read directly
off the netlist and its exact position-matched pin labels; **best-effort** rows remain open because
the schematic genuinely doesn't specify them (e.g. which H1 GPIO carries which firmware signal is
our own choice, not something a schematic would ever encode).

| Parameter | Value | Confidence | Source |
|---|---|---|---|
| MCU / board | RP2350B (U1), bare QFN-80 chip on a custom board, NOT a Pico 2 module — Arduino-Pico board target `weact_rp2350b` | confirmed | PCB BOM, imu_grv.h header |
| Control loop rate | 500 Hz (dt = 2.0 ms) on core 0 | confirmed | 01_FlightComputer_Spec.md, flowcharts/02 |
| TVC engage delay | t ≥ 0.5 s after launch detect (past F15 ignition spike) | confirmed | we4_atmos_tvc.py |
| Burnout / TVC cutoff | t = 3.45 s | confirmed | we4_flightsim.py, we4_atmos_tvc.py |
| PID gains (pitch = yaw, decoupled) | Kp=0.10, Ki=0.40, Kd=0.18 | confirmed | wyvern_pid.h; margin-verified 24-point sweep, PID_TUNING_REPORT.md (PM=44.1°, GM=12.6 dB worst case) |
| Derivative filter time constant | tau_d = 0.02 s | confirmed | wyvern_pid.h, pid_reference.py |
| Integral clamp | ±0.4 (anti-windup) | confirmed | wyvern_pid.h, pid_reference.py |
| Output (gimbal) limit | ±8.0° (0.1396 rad) | confirmed | wyvern_pid.h `OUT_LIM_DEG=8.0`, sized for wind/weathercock authority |
| Servo lag (model) | tau_servo ≈ 0.04 s | confirmed | we4_atmos_tvc.py |
| Launch detect | \|a\| > 2 g sustained ≥ 50 ms, onboard BNO055 accelerometer event | confirmed | flowcharts/01_flight_state_machine.mermaid, launch_status.h, imu_grv.h |
| I2C bus (single, shared) | GP0 SDA / GP1 SCL — carries body BNO055, external BNO085 (STEMMA-QT), BME680, INA226, LIS3MDL; no mux, no second bus | confirmed | PCB netlist trace, imu_grv.h header |
| Onboard IMU | Bosch BNO055 (U2), address **0x28** | confirmed (COM3/ADR pin traces to GND; I2C mode confirmed via PS1/PS0; no ext 32kHz crystal populated) | PCB netlist trace, imu_grv.h |
| External IMU | Adafruit BNO085 breakout via STEMMA-QT (CN2), address 0x4A, mounted at the TVC-bay/electronics boundary near the bulkhead joint, not on the gimbal | confirmed mount point, confirmed address (Adafruit default; CN2 is a plain GND/3V3/SDA/SCL passthrough) | WYVERN_E4_Recovery.md §1, imu_grv.h |
| Barometer | BME680 (U3), address **0x76** | confirmed (SDO pin traces to GND, CSB traces to 3V3 selecting I2C mode) | PCB netlist trace, baro.h |
| Magnetometer | LIS3MDL (U5), address **0x1C** | confirmed (SDO/SA1 pin traces to GND); present on the board, still unused by any firmware module | PCB netlist trace |
| Battery/power monitor | INA226 (U4) — reads the ~5V buck output rail, NOT pack voltage; VIN+/VIN- don't span a real current shunt; A1 address-strap ties to a non-standard ~5V node | **real wiring problems found, not just an unread address** — see §3 above and battery.h's file header | PCB netlist trace, battery.h |
| SPI (microSD, CARD1/TF-01A) | MISO GP8 / CS GP9 / SCK GP10 / MOSI GP11 | confirmed (all four pins traced; corrected a MOSI/CS swap from an earlier pass) | PCB netlist trace, sd_logger.h |
| microSD power | CARD1 pin 4 (the position a standard TF-01A pinout calls VDD) traces to GND in the netlist, not 3V3 | **flagged, possible board defect** — bench-check with a multimeter before assuming SD logging works | PCB netlist trace, sd_logger.h |
| Servos | GP2 pitch (JST U8) / GP3 yaw (JST U9), neutral=90°, travel ±8°, powered from the ~5V buck rail (not the 3V3 logic rail) | confirmed pins and power rail; servo assignment to U8/U9 is our choice not a schematic label | PCB netlist trace, wyvern4_tvc.ino |
| Spare JST connectors | GP4 (U10) / GP5 (U11), function undetermined | unassigned/open | PCB netlist trace |
| H1 debug/expansion header (14-pin) | pin1/5=3V3, pin2/6/11/14=GND, pin3/4=QSPI flash signals (not usable GPIO), pin7=GPIO37, pin8=GPIO36, pin9=GPIO35, pin10=GPIO34, pin12=~5V buck rail, pin13=GPIO12 | confirmed (corrects an earlier pass's wrong claim of SWDIO/SWCLK on this header — that never existed) | PCB netlist trace |
| LAUNCH_IRQ | GPIO37 (H1 pin7) | confirmed pin exists and is usable; which of the 4 usable H1 GPIOs carries this specific signal is our choice | PCB netlist trace, launch_status.h |
| CAM_EN | GPIO36 (H1 pin8) | confirmed pin exists and is usable; function assignment is our choice | PCB netlist trace, launch_status.h |
| Status LED | GPIO35 (H1 pin9) | confirmed pin exists and is usable; function assignment is our choice | PCB netlist trace, launch_status.h |
| Buzzer | GPIO34 (H1 pin10) | confirmed pin exists and is usable; function assignment is our choice | PCB netlist trace, launch_status.h |
| RBF (remove-before-flight) sense | **No such pin exists on PCB1.** U13 (the physical switch) has zero GPIO connection — both its terminals sit in the power domain. GPIO12 (H1 pin13) is reserved and bodge-wire-ready in firmware but nothing is soldered there as fabricated | confirmed absent; arming safety is currently just "the board is off until the power switch is flipped" | PCB netlist trace, wyvern4_tvc.ino |
| WiFi/BLE | NONE — no CYW43439 or any radio chip in PCB1's BOM. `wifi_telemetry.h` is compiled only when `WIFI_ENABLED` is set, and stays 0 by default on this board rev | confirmed absent | PCB BOM |
| Recovery sequencing | F15-4 motor ejection charge separating the two body tubes at the bulkhead joint, t ≈ 7.45 s (1.18 s past apogee); no electronic deploy; FC only observes/logs | confirmed | WYVERN_E4_Recovery.md |

All firmware modules are written to this table. The two rows marked with real wiring/board problems
(INA226's rail/shunt/address wiring, CARD1's possible missing VDD) are the load-bearing open items —
resolve those with a multimeter and, if confirmed, a board revision, before trusting battery
protection or SD logging on this hardware rev. The lighter "confirmed pin, function assignment is
our choice" rows just mean: if a bench check ever shows a *different* GPIO is more convenient to
wire externally, swap the `#define` and this table together, same as always.

## 5. Sensor and DAQ notes

`Documentation/COMPATIBILITY.md` carries the full I2C/SPI/PWM/ADC/power audit across every
component and both ground-test rigs. Sensor detail worth keeping close to the parameter table:

- Gimbal deflection on the solenoid balance is read from the 3-axis load balance plus an external
  BNO085 — no time-of-flight ranging hardware anywhere on the vehicle or either ground rig.
- Ground-rig DAQ is a Raspberry Pi Pico on both the servo rig (`wyvern4_gse_servo_rig.ino`) and the
  solenoid rig (`wyvern4_gse_solenoid_rig.ino`), matching `GSE_TestStands.md` and `gen_wiring4.py`.

## 6. Wind tunnel + aerofoil testing

The program runs the full five-research-question set, including a physical wind tunnel for aerofoil
performance testing. The bench rig lives at `Wind Tunnel/` (a purchased/adapted STL+3MF kit) and is
documented as test stand #4 in `WYVERN_E4_GSE_TestStands.md` §4.

Research questions: RQ1 actuator class (magnetic vs. servo TVC, tested on two separate physical
stands, `WYVERN_E4_GSE_TestStands.md` §2–3), RQ2 zoned AM materials (PC-FR/ASA-Aero/ABS coupon
program plus jetvane testing, §1), RQ3 fin aerofoil (tunnel-measured lift/drag/stall), RQ4
wind-tunnel-vs-flight calibration (tunnel-measured coefficients vs. flight-telemetry-derived static
margin and coast-phase drag), RQ5 closed-loop PID gain sensitivity.

`Simulations/CFD/` holds the vortex-panel solver, airfoil profile library, `airfoil_polars.csv`,
`WYVERN_E2_airfoil_polars.xlsx`, `cl_alpha.png`, and `cp_distribution.png` supporting RQ3/RQ4; the
solver's validation line reproduces the documented NACA0012 dCl/dα ≈ 109.6% of thin-airfoil ideal.
Tunnel data doesn't exist yet as of this writing — cite predicted coefficients as predicted until a
real run is on record.

## 7. Custom flight computer PCB

The custom RP2350B flight computer PCB is a **circular Ø62 mm board**. Fabrication package (Gerber,
schematic PDF, BOM, pick-and-place, netlist, Altium/PADS exports, 3D render) lives in `PCB/`.

Fit check against the Upper BT (70 mm OD airframe, 1.6 mm wall per `WYVERN_E4_FEA_Structural.md`
§4 → ~66.8 mm ID): Ø62 mm leaves **~4.8 mm diametral clearance (~2.4 mm radial per side)**. Carry
this into the build guide's Upper BT fit-check step rather than assuming clearance is obvious.

The board carries **one** external STEMMA-QT port (one external BNO085, mounted at the TVC-bay/
electronics boundary — see `WYVERN_E4_Recovery.md` §1, not on the gimbal) plus one onboard BNO055
(a different Bosch chip family from the external unit, see §4 and `imu_grv.h`): two physical IMUs
total, voted against each other for attitude, sharing one I2C bus with the BME680 baro, INA226
battery monitor, and LIS3MDL magnetometer — no mux chip on this board.

## 8. Vehicle CAD

`3D parts/_generator/gen_rocket4.py` generates the full printable vehicle:

- **Architecture:** Upper BT (ASA-Aero, nose + recovery wadding/FC bay) + Lower BT (PETG-CF, chute/
  wadding + TVC bay, one continuous tube) + one bulkhead joint (PETG-CF, wiring pass-throughs only,
  not gas-sealed).
- **Materials:** ASA-Aero 0.65 g/cm³ (upper body), PETG-CF 1.30 g/cm³ (lower body + fins), PC-FR
  1.20 g/cm³ (motor mount + gimbal only).
- **Fins:** 87 mm span, root 70 / tip 35 / LE-sweep 25 / thickness 3, matching
  `WYVERN_E4_Stability_FinSizing.md`.
- **Wall:** uniform 1.6 mm across all materials.

Every part carries real fastener geometry, not proof-of-concept boolean shapes. `wcad.py` provides
named DFM primitives (`insert_boss`, `hole_cutter`, `bolt_circle`) that every part in `3D parts/`,
the servo TVC test stand, and the static thrust stand build from:

- **Explicit fit tolerances**, named once (`FIT_SLIP=0.20mm` radial clearance for sliding/insert
  fits, `FIT_PRESS=-0.10mm` radial interference for friction-hold fits like centering rings on the
  motor tube).
- **M3 heat-set insert bosses** (4.2mm pilot, 8mm boss OD, standard knurled-brass-insert specs) at
  every bolted joint: TVC balance base/thrust-block corners, static-stand base plate, HX711 mounts.
- **Retention screws** (M3 clearance, radial) holding the bulkhead captive in the Upper BT and the
  motor mount's aft centering ring captive in the Lower BT.
- **Real through-holes for the gimbal's pivot pins** (3.2mm, slip fit for a 3mm steel dowel or M3
  shoulder screw).
- **Static-stand parts** `TS_base_plate`, `TS_motor_tower`, and `TS_loadcell_bracket`, built against
  the 5kg load cell + HX711 + RP2350B PCB instrumentation chain in `WYVERN_E4_GSE_TestStands.md`.
- **Servo-stand part** `TVC_balance_hx711_mount`.

The magnetic TVC stand (`3D parts/MTVC/`) and the wind tunnel (`Wind Tunnel/`) are separate CAD
scopes, not covered by `gen_rocket4.py`.

**Open items, flagged rather than guessed:**
1. Upper BT / Lower BT tube lengths are scaled to hit `core.py`'s LTOT=672 mm total (Upper BT
   ≈198 mm / Lower BT ≈422 mm) rather than pinned down by a dedicated bay-layout pass. Treat as a
   first-pass placeholder for fit/mass checks until that pass exists.
2. Bulkhead joint release geometry isn't modeled yet. The friction-fit/shear-pin sizing for the
   50–150 N release target (`WYVERN_E4_Recovery.md` §4, `WYVERN_E4_FEA_Structural.md` §4.1) is an
   open engineering decision; the CAD bulkhead is a plain disk with two wiring pass-through holes.
3. Rail-button material is an assumption (PETG-CF, matching the lower body it mounts to); no doc
   specifies it independently.
4. Hardware interface dimensions (EMAX ES08MA II servo mounting flange, Adafruit 5kg/1kg
   strain-gauge cell body/hole spacing, HX711 breakout hole pattern) are catalog-typical figures for
   those specific parts, not calipers-verified against bench hardware. Every such block in
   `gen_rocket4.py` is tagged `VERIFY-WITH-CALIPERS` — confirm before the final print run.
5. The gimbal's pitch-axis trunnion mount into the flight airframe isn't modeled (the servo test
   stand's `TVC_balance_thrust_block` models the equivalent bench-rig mount, which is pinned down;
   the flight-vehicle version, how the gimbal's outer ring anchors into the Lower BT wall, is the
   same class of open decision as item 2).
6. Print-orientation/support notes aren't embedded in the CAD. Wall thickness (1.6mm, FEA-verified)
   and the fin's flat-print/100%-infill callout (`WYVERN_E4_Build_Guide.md`) are the only
   orientation-relevant facts on record.

Re-run with `cd "3D parts/_generator" && python3 gen_rocket4.py` after any geometry change, per the
project's generate-then-render convention — don't hand-edit the STEP/STL.

## 9. Firmware verification

**2026-08-11 PCB reconciliation pass.** Every prior compile check in this section (and every prior
version of `imu_grv.h`/`baro.h`/`battery.h`/`launch_status.h`/`wyvern4_tvc.ino`) had been written
against the *documented, never-fabricated* board architecture — PCA9548A mux, dual I2C bus, 2-3x
BNO085, GP26 ADC battery divider, Pico 2 W module. The real, physically fabricated PCB1 was traced
pin-by-pin from its own netlist/BOM/schematic (`PCB/Netlist_PCB1_2026-08-11.tel`,
`PCB/BOM_Board1_PCB1_2026-08-11.xlsx`, `PCB/SCH_Schematic1_2026-08-11.pdf`) and found to differ on
nearly every point: bare RP2350B silicon (not a Pico module), one shared I2C bus (not a mux + second
bus), an onboard BNO055 (not a second BNO085), a real INA226 power monitor (not an ADC divider), an
unused LIS3MDL magnetometer, no WiFi radio chip, and a different pin map end to end. Every firmware
module was rewritten against the netlist-verified architecture; the corrected pin/address table is
§4 above, with each row flagged confirmed vs. best-effort. This is a hardware-reality correction, not
a design change — nothing about the control loop, PID gains, recovery sequencing, or flight
mathematics in §1/§2/§8 moved.

**Second pass, same day.** The first reconciliation pass above got the big architectural facts right
(bare RP2350B, single I2C bus, BNO055 not a second BNO085, real INA226) but several of its finer
details were read off a PDF text extraction that came out of visual order, not off the netlist
directly — which produced two wrong claims (an invented SWDIO/SWCLK pair on the H1 header; an
"unverified, could be 0x28 or 0x29" hedge on the BNO055 address) and left several real pins as
unresolved "best-effort" guesses that the netlist actually answers outright. A second pass traced
every relevant component pin-by-pin through `Netlist_PCB1_2026-08-11.tel`, cross-checked against the
exact pin-position text in `PCB/SCH_Schematic1_1-P1_2026-08-11.svg` (vector text, position-matched
programmatically — not read off a flattened PDF). Net result: BNO055 (0x28), BME680 (0x76), and
LIS3MDL (0x1C) addresses are now confirmed, not guessed; the SD interface's four pins are all
confirmed, and a real MOSI/CS swap bug from the first pass got fixed; H1's real pinout replaced the
invented SWDIO/SWCLK claim; and RBF turned out to have no GPIO connection at all on this board rev.
The INA226 didn't get a clean resolution — tracing it turned up two real wiring problems (it reads
the buck's regulated output rail, not pack voltage, and its address-select pin isn't strapped to a
valid level) that firmware can't correct, only work around and flag. Full detail in §3 and §4 above,
and in `battery.h`'s and `sd_logger.h`'s file headers.

The flight firmware (`wyvern4_tvc.ino` plus its headers) compiles clean against
`rp2040:rp2040:weact_rp2350b` (arduino-cli 1.5.1, rp2040 core 6.0.0) — the bare-RP2350B board
target matching PCB1's actual silicon: 130,080 B flash (0.8%), 54,224 B RAM (10%), re-verified after
the second pass's corrections. Both ground-test rig sketches (`wyvern4_gse_servo_rig.ino`,
`wyvern4_gse_solenoid_rig.ino`) are separate, generic-Pico bench hardware, unaffected by the PCB1
reconciliation, and remain compiled/verified against `rp2040:rp2040:rpipico2w`: ~330 KB flash
(7-8%), ~78 KB RAM (14%).

The attitude vote in `imu_grv.h` runs body (BNO055) vs. external (BNO085), matching the two-IMU PCB
described in §7 — two different chip families, two different drivers (`Adafruit_BNO055` register
protocol vs. `Adafruit_BNO08x` SH2 protocol), sharing one I2C bus. `compute_deflection()` returns NaN
(there's no gimbal-mounted IMU on the flight vehicle to derive a deflection angle from); the
BOOST-phase PID loop only ever consumes `body_pitch_rad`/`body_yaw_rad`, never a deflection value,
and `we4_flight_reduce.py` tolerates an all-NaN `defl_pitch_deg` column.

`launch_status.h`'s status-LED/buzzer pin constant is named `PIN_STATUS_LED` (GP35), not `PIN_LED` —
every Arduino-Pico board profile's `pins_arduino.h` defines `PIN_LED` as a macro for that board's
own onboard LED (25u on `weact_rp2350b`, 64u on `rpipico2w`), and a same-named class member would
collide with it at the preprocessor level regardless of which board target is active.

**2026-08-12 mass recompute.** All four flight-math validation suites (`we4_flightsim.py`,
`we4_validation.py`, `we4_deepsim.py`, `we4_atmos_tvc.py`, plus `we4_pid_retune.py`) were re-run
against a bottom-up mass rebuild, 0.7203 kg liftoff / 0.6603 kg dry — down from the prior 0.7203 kg /
0.6603 kg pass, driven by three real changes: the Lower BT tube moved from PETG-CF to ASA-Aero
(hoop-stress-checked at SF ~6–10× under the 140 kPa ejection pulse, §4.1 of
`WYVERN_E4_FEA_Structural.md`), the discrete "5V UBEC" line was dropped since the onboard TPS564201
buck already does that job (no second physical regulator to weigh), and the recovery consumables
were re-itemized to 70 g (chute+cord+swivel 58 g, Nomex 6 g, wadding 6 g) instead of the older
137 g bay-lump this document had already flagged as an overstatement. Full breakdown in
`WYVERN_E4_Mathematics.md` §1 and `Simulations/we4_sim.py`'s `ITEMS` table.

- `we4_flightsim.py` / `we4_validation.py`: apogee 124.6 m / 409 ft @ 6.72 s, consistent across both
  engines. Validation still clears 10/13 gates; the same three flagged (rail-exit velocity,
  thrust-to-weight peak against the >=5 rule-of-thumb, weathercock angle) are known design
  tradeoffs — TVC authority is what compensates for the low static T/W, per §1 and §4.
- `we4_deepsim.py`: 7/8 deep checks pass; the one flagged item is servo torque margin (check C).
- `we4_atmos_tvc.py`: worst-case pitch deviation 2.45° across all 4 atmospheres, comfortably inside
  the ±8° gimbal limit.
- `we4_pid_retune.py`: the 24-point phase/gain-margin sweep gives PM=44.1° / GM=12.6 dB worst-case,
  clearing the 30°/6 dB floor with room to spare.

Sensor library: the BME680 is read through the `Adafruit_BME680` driver in `baro.h` — matched part,
matched library, no compatibility question.

**Open items, flagged rather than guessed:**
- **INA226 (U4) wiring — highest priority, real hardware problem, not a firmware gap.** It reads the
  ~5V buck output rail instead of pack voltage, has no true current shunt in its VIN+/VIN- path, and
  its A1 address-select pin ties to a node that isn't a valid GND/VS+/SDA/SCL strap. All three are
  netlist-confirmed findings, not guesses. Firmware works around this with rail-sag thresholds
  (`battery.h`) instead of real LiPo-cell protection. Root cause and exact net-by-net fix in
  `PCB1_ECO-1.md`: R10 (the shunt) sits in parallel with U13 (the power switch) instead of in series
  with pack current — one layout mistake causing all three symptoms at once.
- **CARD1 pin4 — possible SD-power defect.** Traces to GND in the netlist where a standard TF-01A
  pinout expects VDD. If accurate, the microSD socket has no power pin wired and `SD.begin()` will
  never succeed regardless of which GPIOs the SPI lines use. Bench-check with a multimeter (pin4 to
  3V3 rail vs. to GND) before spending time debugging this as a firmware or wiring-generator problem
  — exact fix (route pin4 to 3V3) also in `PCB1_ECO-1.md`.
- `COMPATIBILITY.md`'s BSS138 level shifter is orphaned in the BOM: not routed in any schematic,
  wiring generator, or firmware comment. Either every net that needs it is already 3.3V-native (in
  which case drop it from the BOM) or a real level-shifted net was designed but never wired (in
  which case identify which net and route it).
- Upper/Lower body-tube lengths in the CAD are scaled placeholders (§8, item 1), not a dimensioned
  bay-layout result.
- Which of the 4 confirmed-usable H1 GPIOs (37/36/35/34) carries LAUNCH_IRQ vs. CAM_EN vs. the
  status LED vs. the buzzer is a firmware-side choice, not something the schematic specifies —
  re-labeling the `#define`s is enough if a different assignment is ever more convenient to wire.
- The LIS3MDL magnetometer (U5, address 0x1C, confirmed) is present on PCB1 but unused by any
  firmware module. Either wire it into a future sensor-fusion pass or note it as deliberately unused
  ballast for this board rev.
- The GP4/GP5 spare JST connector pins (U10/U11) have no assigned function. Determine their purpose
  (spare servo channel, sensor, unused) before designing anything against them.

## References

CEVA, Inc. (2023). *BNO08X datasheet* (Rev. 1.17). https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf

EMAX. (n.d.). *ES08MA II 12 g mini metal gear analog servo* [Product specification]. Retrieved August 12, 2026, from https://www.getfpv.com/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model.html

Estes Industries. (n.d.). *F15-4 engines* [Product specification]. Retrieved August 12, 2026, from https://estesrockets.com/products/f15-4-engines

Federal Aviation Administration. (n.d.). *14 CFR Part 101 — Moored balloons, kites, amateur rockets, and unmanned free balloons*. Electronic Code of Federal Regulations. https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101

National Fire Protection Association. (2018). *NFPA 1122: Code for model rocketry*. https://www.nfpa.org/product/nfpa-1122-code/p1122code

Raspberry Pi Ltd. (2024). *RP2350 datasheet*. https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

Texas Instruments. (n.d.). *TPS564201: 4.5-V to 17-V input, 4-A synchronous step-down voltage regulator* (SLVSFB5) [Datasheet]. https://www.ti.com/lit/ds/symlink/tps564201.pdf
