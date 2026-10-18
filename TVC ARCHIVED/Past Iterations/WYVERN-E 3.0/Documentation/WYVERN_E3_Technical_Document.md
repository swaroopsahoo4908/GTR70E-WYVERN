# WYVERN-E 3.0 — Technical Document

### A Skylight Rocketry Venture
##### 84 mm two-stage thrust-vector-controlled research vehicle · off-the-shelf Raspberry Pi 5 avionics
##### Supersedes WYVERN-E 2.0 (custom two-board PCB stack). Master configuration: PDR-006.

## 1. Overview

WYVERN-E 3.0 is a redesign of the WYVERN-E research vehicle around a **completely off-the-shelf
flight computer** built on a **Raspberry Pi 5**, replacing the 2.0 custom two-board PCB stack.
It remains an **84 mm two-stage** additively-manufactured vehicle whose sustainer carries fixed
fins (passive backup) and an **active thrust-vector-control (TVC) gimbal**. 3.0 exists to fly a
direct **A/B comparison of two TVC actuation methods** — a tri-solenoid system and a servo-gimbal
system — across instrumented flights, with full onboard data + video capture.

### 1.1 Key specifications

- *Configuration*: 2-stage, fin-stabilized + active-TVC sustainer
- *Body diameter*: 84 mm OD / 80 mm ID, all-**PC-FR** construction (1.25 g/cm³)
- *Liftoff mass*: ≈ 1.29 kg (solenoid TVC) / 1.39 kg (servo TVC)
- *Booster motor*: AeroTech F32-class 29 mm (rod clearance, T/W 5.3)
- *Sustainer motor*: **AeroTech G25W** 29 mm — **4.7 s** burn (the TVC demonstration window)
- *Predicted apogee*: ~1050–1100 ft (oversized fins, Cd ≈ 0.9, hold it under the cap)
- *Flight computer*: **Raspberry Pi 5 (4 GB)** + Camera Module 3
- *Attitude/inertial*: 3× **BNO085** (gimbal, central FC, nose) + **LSM6DSO32** (±32 g) + **LIS2MDL** mag
- *Environment*: **BMP280** baro + **BME688** gas/T/P/RH
- *Storage*: dual microSD (32 GB video + 32 GB flight log) — no radio; retrieved post-flight
- *Recovery / 2nd-stage ignition*: **RRC3+** (sustainer ignition + drogue/main)
- *Arming*: remove-before-flight jumper pin; launch detected by accelerometer threshold
- *Power*: 3S 3000 mAh USB-C-rechargeable; 5 flights + 2 h+ idle
- *No FAA waiver / no Level-1 cert*: ≤ 1500 g liftoff, ≤ 125 g propellant, both motors ≤ G

### 1.2 Why off-the-shelf

The custom PCBs of 1.0/2.0 were high-effort and single-purpose. A Raspberry Pi 5 gives a
Linux flight computer with native camera, USB-C, ample compute for sensor fusion + video
encode, and a fully COTS sensor harness — at the cost of mass (~340 g avionics + power), which
drives the propulsion and no-waiver analysis in §5 and `WYVERN_E3_Power_Mass_Motor.md`.

## 2. Airframe & Structure

### 2.1 Material — all PC-FR

3.0 standardizes on **flame-retardant polycarbonate (PC-FR)** throughout (ρ ≈ 1.25 g/cm³,
HDT ≈ 140 °C, self-extinguishing): primary structure, the FC and TVC bays, the bulkhead, and
the fins. A single material simplifies procurement and gives uniform heat/flame tolerance near
the motor and gimbal. ASA is retained only for the nose cone (mass-sensitive, cool).

### 2.2 Bay architecture — FC bay / bulkhead / TVC bay

The sustainer is split into two sealed bays by a **structural bulkhead**:

- *Central flight-computer bay* — houses the Raspberry Pi 5, the power pack + electronics, the
  central BNO085, LSM6DSO32, LIS2MDL, BMP280, BME688, dual microSD, and the RRC3+.
- *TVC bay* (aft) — the gimbaled sustainer-motor cradle, the gimbal-mounted BNO085, and the
  actuators (solenoids or servos depending on the test article).
- *Bulkhead* — a sealed PC-FR disc that isolates the electronics from the motor/gimbal thermal
  and pressure environment, penetrated only by **a few slotted pass-throughs for the
  servo/solenoid wires** (and the gimbal BNO085 lead). Keeps pyro gas and motor heat out of the
  FC bay.

### 2.3 Fins (oversized, fixed)

Enlarged trapezoidal fins on the sustainer raise drag (Cd ≈ 0.9) to hold apogee under ~1100 ft
despite the long sustainer burn (§5). Four fins, surface-mounted, PC-FR, with a root tab; the
RQ1/RQ2 wind-tunnel campaign still down-selects the profile/coating one geometry at a time.

## 3. Flight Computer (off-the-shelf)

### 3.1 Compute & sensing

- *MCU/SBC*: Raspberry Pi 5 (4 GB) + active cooler; runs the C/Python flight + TVC control loop
- *Camera*: Raspberry Pi Camera Module 3 (flight video to a dedicated microSD)
- *3× BNO085 9-DOF* (fused quaternion): **gimbal-mounted** (measures actual thrust-vector
  attitude), **central FC**, and **nose cone** — three reference points along the body for
  structural-flex and attitude cross-checks. Shared I²C address resolved via a TCA9548A mux.
- *LSM6DSO32*: ±32 g accelerometer + gyro (high-g boost/landing capture + launch detection)
- *LIS2MDL*: 3-axis magnetometer
- *BMP280*: barometric altitude; *BME688*: temperature/pressure/humidity/VOC
- *Storage*: two microSD breakouts (SPI) — one for H.264 video, one for the full-rate sensor log

### 3.2 Arming & launch detection

A **remove-before-flight jumper pin** on the rod gates the flight-computer arm state: while
inserted, the pyro/ignition outputs are held safe and the FC is in standby. Pulling the pin at
the pad transitions the FC to **armed**. **Launch is detected** by an accelerometer threshold
(LSM6DSO32 / BNO085, e.g. > 3 g sustained) so the control loop and event timers start only on
real liftoff — no pyro can fire on the pad.

## 4. Thrust Vector Control — two systems compared

The sustainer motor sits in a **±5° gimbaled cradle**. Two interchangeable actuator systems are
built and flown head-to-head (3 flights each):

### 4.1 System A — Tri-solenoid

Three 12 V pull-solenoids at 120° act on the cradle ring; differential pull vectors the nozzle,
springs return to neutral on power loss (fail-safe). Each coil is a low-side MOSFET-switched
PWM channel (logic-level gate) with a freewheel diode and a current-sense shunt. Bang-bang/PWM
mixing — fast, simple, no proportional position feedback.

### 4.2 System B — Servo gimbal (BPS-style, up-rated)

Three high-torque digital servos drive the gimbal via linkages — proportional angular position,
smoother control, gear backlash + slower slew the trade. BPS Space's TVC mounts use ~9 g micro
servos (~2 kg·cm) for ~10 N D/E motors; the G25W's gimbal-axis torque is **≈ 0.63 N·m at ±5°**
(100 N peak) → **~16 kg·cm required (SF 2.5)**, so 3.0 uses **~35 kg·cm metal-gear digital
servos** — about 8× the BPS micro-servo torque — driven from a PCA9685 PWM expander.

> Comparison metrics (ground rig + flight): control bandwidth, slew rate, deadband/backlash,
> power draw, mass, settling time and overshoot on a commanded maneuver. See
> `WYVERN_E3_TVC_Comparison.md`.

## 5. Propulsion, Flight Sequence & Feasibility

### 5.1 Motors (two-stage, no-waiver)

| Stage | Motor | Itot | Favg | Burn | Role |
|---|---|---|---|---|---|
| Booster | AeroTech F32-class | ~30 N·s | 32 N | ~1.0 s | rod clearance (T/W 5.3), then stage |
| Sustainer | **AeroTech G25W-10A** (#072510) | 117 N·s | 25 N | **4.7 s** | the long TVC demonstration burn |

Hardware: the G25W-10A reload uses the **AeroTech RMS-29/120** casing + closures (sold
separately, reusable); the F booster uses an **RMS-29/40** casing.

*The F25W (2.0's sustainer) is unflyable here* — at ~1.2 kg it gives T/W ≈ 2.0. The Pi-5 mass
forces this analysis; full derivation in `WYVERN_E3_Power_Mass_Motor.md`.

### 5.2 Sequence

1. *Pad*: RBF pin inserted → FC standby, pyro safe.
2. *Arm*: pull RBF pin on the rod → FC armed, sensors logging.
3. *Liftoff*: booster F32 lights (launch controller); accelerometer threshold starts the flight
   state machine. Fins stabilize the booster phase (TVC is on the sustainer, not yet lit).
4. *Booster burnout + separation*: drag separation; RRC3+ arm-gate keyed to the flight state.
5. *Sustainer ignition*: RRC3+ fires the G25W; **TVC active from ignition** — stabilize, then
   command a maneuver across the 4.7 s burn.
6. *Apogee*: RRC3+ deploys drogue → main; recover; pull both microSD cards for data + video.

### 5.3 No-waiver compliance

Liftoff 1.29–1.39 kg < 1500 g; total propellant ≈ 78 g < 125 g; both motors ≤ G. **No FAA
waiver, no Level-1 certification.** Apogee held to ~1050–1100 ft by the oversized fins.

## 6. Power System

3S Li-ion 3000 mAh (33 Wh, 11.1 V) with a USB-C **PD charge board** (recharge ~1 h). Continuous
load 4.2 W idle / 8.3 W active (Pi 5 dominates). Rails: **5 V/5 A buck** (Pi 5), **6 V buck/UBEC**
(servos), **11.1 V direct** (solenoids). Energy budget ≈ 24 Wh w/ margin → **1.9× margin** for
5 flights + 2 h+ idle. No radio — all data is logged onboard to the dual microSD and retrieved
post-flight.

## 7. Recovery

RRC3+ dual-deploy (apogee → drogue, then main). 24″ elliptical main; 1/8″ tubular Kevlar shock
cord; MJG initiators + black-powder ejection in a bulkhead canister.

## 8. Ground Support Equipment

- *Motor test stand* (PC-FR) — now with a **20 kg load cell** (G-motor static-fire peaks exceed
  the old 10 kg cell). Characterizes the F32 + G25W and runs the RQ3 jetvane erosion test.
- *Servo TVC ground rig* — bench gimbal + dummy thrust load to characterize System B (and a
  side-by-side bench comparison vs the solenoid system) before flight.
- *Wind tunnel* — fin profile/coating campaign (RQ1/RQ2), unchanged from 2.0.

## 9. Test Plan

- **6 instrumented flights**: 3 with solenoid TVC + 3 with servo TVC (the A/B comparison).
- **Ground static fires**: 2 each of the F32 booster and the G25W sustainer on the stand.
- **Jetvane erosion** (RQ3): E-class plume on PC-FR / PETG-CF / ASA / PLA coupons.
- **Wind tunnel** (RQ1/RQ2): fin profile + coating down-select.

## 10. Research Questions (3.0)

- *RQ1* — fin aerofoil profile + deflection aerodynamics (wind tunnel + panel-method CFD)
- *RQ2* — print material + surface-coating performance for fins
- *RQ3* — motor thrust characterization + material erosion as jetvane candidates
- *RQ4* — **TVC actuation A/B**: tri-solenoid vs servo-gimbal closed-loop control authority,
  bandwidth, and maneuver performance over a long (4.7 s) sustainer burn

## 11. What changed vs 2.0

Custom two-board PCB stack → off-the-shelf Pi 5 + COTS sensors; magnetic-only TVC →
solenoid **and** servo A/B; F/G two-stage with onboard dual-deploy → F32 + long-burn G25W with
RRC3+ ignition/recovery; PETG-CF/PC/ASA mix → all PC-FR; added the FC-bay/bulkhead/TVC-bay
split; no radio (already removed in late 2.0). Mass up (~1.3 kg vs ~1.0 kg) from the Pi 5;
apogee down (~1100 ft vs 1266 ft) by design for a controlled, recoverable TVC testbed.
