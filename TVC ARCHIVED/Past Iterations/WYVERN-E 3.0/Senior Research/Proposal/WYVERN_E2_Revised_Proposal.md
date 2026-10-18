# WYVERN-E 2.0 — Revised Project Proposal

### A Skylight Rocketry Venture
##### 84 mm 2-Stage Magnetic-TVC 3D-Printed Research Vehicle
##### Revision of the WYVERN-E program · PDR-005 baseline

## 1. Abstract

WYVERN-E 2.0 is a complete architectural pivot of the WYVERN-E research program toward a
small, low-cost, **fully 3D-printed two-stage rocket** that demonstrates **closed-loop magnetic
thrust vector control**, comprehensive flight-data acquisition, and onboard videography. The
vehicle is 84 mm in diameter, flies on commercial 29 mm composite motors (F-class booster, long-burn G25W sustainer), and carries an off-the-shelf Raspberry Pi 5 flight computer driving an interchangeable solenoid- or servo-
solenoids on a gimbaled sustainer motor. The program also delivers the full ground-support
ecosystem: a wind tunnel for fin characterization, a load-cell motor test stand, and complete
build/launch procedures. Every structural part is printable on a desktop FDM machine.

## 2. Motivation & Objectives

The prior WYVERN-E (Rev C) grew to a 127 mm finless airframe with a two-board avionics stack.
2.0 reverses course toward a *smaller, cheaper, faster-to-iterate* platform that still proves
the hard technology — active TVC — while being launchable on common F/G motors at a local
field. Objectives:

1. *Demonstrate closed-loop TVC and compare two actuators* — tri-solenoid vs servo-gimbal (±5°, 2-axis)
   on a flying vehicle, with the sustainer motor gimbaled.
2. *Capture every measurable flight parameter* — attitude, rates, acceleration, altitude,
   pressure, temperature, humidity, magnetic field, vibration, power — to onboard NAND with
   microSD backup; all flight data is retrieved post-flight from onboard storage (no radio link).
3. *Record flight video* from an onboard camera.
4. *Use an off-the-shelf Raspberry Pi 5 flight computer* — Linux SBC + COTS sensor harness, replacing the
   dedicated TVC Actuator board, joined by a 20-pin board-to-board connector.
5. *Validate the design* through wind-tunnel fin testing and static motor-stand
   characterization before flight.
6. *Keep it printable and affordable* — desktop FDM polymers + COTS parts.

## 3. Scope of Work / Deliverables

| # | Deliverable | Format |
|---|---|---|
| 1 | Off-the-shelf Raspberry Pi 5 flight computer + COTS sensor harness | wiring `.kicad_sch` (solenoid + servo harnesses) + integration `.md` |
| 2 | Revised proposal (this document) | `.md` |
| 3 | Technical document | `.md` |
| 4 | Mathematics & performance | `.md` (+ reproducible `sim/we2_traj.py`) |
| 5 | Bill of materials | `.xlsx` + `.md` |
| 6 | Build & launch procedures | `.md` |
| 7 | 3D-printable parts (whole + subcomponents) | `.stl` + `.step` |

3DP coverage: outer rocket shell, stage 1 (booster), stage 2 (sustainer), nose cone, fins,
TVC mechanism, PCB internal mount, plus the wind-tunnel fin mount and the motor test stand —
each as an individual printable part and as a full assembly, in both STL (print) and STEP
(CAD) form.

## 4. Technical Approach (summary)

- *Airframe*: 84 mm OD / 80 mm ID printed tube sections, threaded/coupler-joined; material
  down-select among PETG-CF (primary) and ASA Aero; fins + TVC + test stand in PC-FR.
- *Propulsion*: F-class booster → AeroTech **G25W** (117 N·s, 4.7 s) sustainer; two-stage, no-waiver (≤1500 g, ≤125 g propellant);
  predicted apogee 386 m / 1 266 ft at Mach 0.20.
- *TVC*: 3 × 12 V solenoids at 120° on a ±5° gimbaled sustainer cradle; AO3400A low-side 20 kHz
  PWM with 20 mΩ shunt closed-loop current control; spring-return fail-safe neutral.
- *Avionics*: off-the-shelf **Raspberry Pi 5 (4 GB)** + Camera Module 3 + dual 32 GB microSD;
  sensors: 3× BNO085 (gimbal/FC/nose), LSM6DSO32 (±32 g), LIS2MDL, BMP280, BME688; RRC3+ for
  2nd-stage ignition + dual-deploy recovery; interchangeable solenoid- or servo-driven TVC gimbal;
  remove-before-flight pull-pin arms the stack.
- *Recovery*: dual-event (booster chute + sustainer/nose main) under onboard FCM control; staging
  interlock prevents under-thrust chute deployment.
- *GSE*: Printables modular wind tunnel + 120 mm fan adapter + custom single-fin mount;
  PC-FR motor test stand with Wishiot 10 kg load cell + HX711 on a Metro M4.

See *WYVERN_E2_Technical_Document.md* for full detail and *WYVERN_E2_Mathematics.md* for the
quantitative basis.

## 5. Test & Verification Plan

1. *Bench bring-up* of the FCM over USB-C; verify all sensors, storage, and camera.
2. *Solenoid loop test*: characterize each coil's current loop and the gimbal authority
   on the bench (no motor).
3. *Wind-tunnel campaign*: test candidate fins one at a time; down-select the single geometry
   on measured normal force / center-of-pressure at matched Reynolds number.
4. *Motor static fires*: characterize the F booster and G25W thrust curves on the staked PC-FR stand
   (calibrated with E16-4); confirm impulse vs. published values; use the 20 kg cell to avoid clipping at the G-motor peak.
5. *Ground ejection test*: validate black-powder charge sizing for both recovery events.
6. *Low-and-slow first flight*: single-stage (booster only) shakedown before two-stage TVC.
7. *Full two-stage TVC flight* at MDRA with RSO approval.

## 6. Risk Register (top items)

| Risk | Severity | Mitigation |
|---|---|---|
| Marginal rail-exit velocity (10.0 m/s) | High | Lighter infill (→1.05 kg) or rail extension; active TVC from ignition |
| 4-layer Main FC routing density | Med | Board 2 is 4-layer (Sig/GND/GND/Sig); freerouting pass on the user machine |
| Load cell clipping at G-motor peak (>98 N) | Med | 20 kg cell fitted for G-class static fires |
| Under-thrust chute deployment at staging | High | Firmware arm-gate on the onboard drogue channel keyed to the staging state machine |
| Descent rate 10.0 m/s on printed airframe | Low | Upsize to 24″ chute (→7.5 m/s); land on sod |
| Heat at gimbal/nozzle | Med | PC-FR (140 °C HDT) for TVC + test stand |

## 7. Budget Summary

Full line-item costing is in *WYVERN_E2_BOM.xlsx*. The design intent is low unit cost: the
airframe is FDM polymer (grams of filament), and the electronics are COTS modules plus a
single fabricated PCB. Consumables (motors, igniters, black powder, chute) dominate per-flight
cost.

## 8. Schedule (indicative)

1. Print + post-process airframe; fabricate FCM (order PCB + parts).
2. FCM bench bring-up + firmware.
3. Wind-tunnel fin down-select.
4. Motor static fires.
5. Ground ejection + shakedown flight.
6. Full two-stage TVC flight at MDRA.

## 9. References

AeroTech/RCS data sheets (F booster, G25W); ThrustCurve.org; Raspberry Pi 5 documentation; Bosch BNO085;
BME688/BMP280; ST LSM6DSO32; ST LIS2MDL; Bosch BNO085 (×3); Raspberry Pi 5 + Camera Module 3;
MDRA (mdrocketry.org); Barrowman (1966). Source CAD + wiring generators are included for
full reproducibility.
