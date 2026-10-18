# WYVERN-E 2.0 — Technical Document

### A Skylight Rocketry Venture
##### 84 mm 2-Stage Magnetic Thrust-Vector-Controlled 3D-Printed Research Vehicle
##### Supersedes XRIM-117E PDR-005 Rev C (127 mm finless). Master configuration: PDR-005.

## 1. Overview

WYVERN-E 2.0 is a complete redesign of the WYVERN-E research vehicle around a **84 mm diameter,
two-stage, additively-manufactured airframe** with **active magnetic-solenoid thrust vector
control** on the sustainer. It is a flying testbed for closed-loop TVC, full-envelope flight
data capture, and onboard videography, built almost entirely from desktop-FDM polymers and
COTS hardware. The vehicle retains the WYVERN lineage's RP2350 flight computer and the Rev C
magnetic-solenoid TVC concept, but is built around a two-board avionics stack — a Main Flight Computer (RP2350B) and a dedicated
TVC Actuator board (see *PCB/WYVERN_E2_TwoBoard_Spec.md*) — in a compact 84 mm tube.

2.0 flies with **one fixed fin geometry on the sustainer** for passive backup stability while
the sustainer-mounted magnetic TVC provides active control authority — a belt-and-suspenders
approach appropriate to a research article. Multiple candidate fin geometries are evaluated
one-at-a-time in a custom wind tunnel; only the best flies.

### 1.1 Key specifications

- *Configuration*: 2-stage, fin-stabilized + active magnetic TVC sustainer
- *Body diameter*: 84 mm (OD), 80 mm (ID), 2.0 mm wall
- *Overall length*: ~876 mm (assembled, nose to fin tip plane)
- *Liftoff mass*: 1.44 kg (see Mathematics §2)
- *Booster motor*: AeroTech G78 Mojave Green, 29 mm (110 N·s)
- *Sustainer motor*: AeroTech F25 White Lightning, 29 mm (77.9 N·s)
- *Predicted apogee*: 386 m (1 266 ft); peak Mach 0.20
- *TVC*: 3 × 12 V pull-solenoids on a ±5° gimbaled sustainer cradle, 20 kHz PWM closed-loop
- *Avionics*: two-board 80 mm stack — Board 2 Main FC (RP2350B) + Board 1 TVC Actuator, 9-DOF suite, SD-NAND, camera, USB-C
- *Recovery*: dual-event (booster chute + sustainer/nose main), onboard-controlled (RP2350B pyro channels)
- *Materials*: PETG-CF / ASA / PLA Basic airframe (RQ2 down-select); PC-FR fins + TVC + test stand; PLA wind tunnel

## 2. Airframe & Materials

### 2.1 Material selection (flight airframe)

Three candidate print materials are characterized; the airframe ships in the best performer,
with the down-selection driven by stiffness-to-mass, temperature margin, and print
reliability at 84 mm diameter.

| Material | Density (g/cm³) | Flex. modulus | HDT | Role / rationale |
|---|---|---|---|---|
| *PETG-CF* (carbon-filled PETG) | 1.30 | ~4.5 GPa | ~78 °C | **Primary** — highest stiffness, low warp, matte finish; chosen for booster + structural tubes |
| *ASA (Aero)* | 1.07 | ~2.0 GPa | ~95 °C | Lightest + UV/temp stable; nose cone + fairings (low-load, mass-sensitive) |
| *PC-FR* (flame-retardant PC) | 1.25 | ~2.4 GPa | ~140 °C | **Fins + TVC mechanism + test stand** — heat + flame exposure near the motor/gimbal |

Down-select logic: the primary structure is *stiffness-limited, not strength-limited*
(Mathematics §9, SF > 75), so PETG-CF's modulus wins for the body. Components in the motor
thermal field (fins, TVC cradle, gimbal, test stand) use PC-FR for its 140 °C HDT and self-
extinguishing behavior — standardizing on PC-FR rather than splitting fins onto plain PC
(no PC purchase exists on the procurement tracker; PC-FR is the only polycarbonate actually
stocked). The nose, being mass-sensitive and aerodynamically loaded but cool, uses ASA.

### 2.2 Main body — print & assembly

- *Outer diameter*: 84.0 mm (80 mm ID); *wall*: 2.0 mm (4 perimeters @ 0.5 mm, ~35% gyroid infill on solids)
- *Sections* (printed separately, threaded/coupler-joined): nose, recovery bay, avionics bay,
  sustainer/TVC bay, interstage coupler, booster body. Each ≤ 232 mm to fit a 250 mm bed.
- *Couplers*: 65.4 mm OD male stubs, 2.2 mm wall, into the 80 mm ID female tubes; 22–28 mm
  engagement; the interstage coupler carries the separation joint and the 2nd-stage igniter
  channel.
- *Surface*: as-printed matte (PETG-CF); optional 2-coat epoxy skin-fill + sand for the
  wind-tunnel reference body to remove layer lines (drag fidelity).

### 2.3 Nose cone

- *Profile*: tangent-ogive, base 84 mm, length 168 mm (fineness 2.4), 2.0 mm wall (ASA)
- *Generated*: `3DP/_generator/gen_rocket.py → ogive_nose()`; STL+STEP at `3DP/Rocket/01_nose_cone.*`
- *Retention*: 28 mm shoulder coupler + forward eyebolt bulkhead for the shock cord

### 2.4 Fins (fixed, single geometry — multiple tested)

- *Planform*: trapezoidal, root 104 mm, tip 46 mm, span 56 mm, sweep 66 mm, 4.5 mm thick (PC-FR)
- *Count*: 4, on the **sustainer** (moved from the booster per PDR-005), surface-mounted with a 6 mm root tab
- *Static margin*: ~1.7 cal (Mathematics §7), within the 1.0–2.0 cal band
- *Test article*: `3DP/Rocket/08_fin_single.*` — one fin printed at a time, fitted to the
  wind-tunnel mount; airfoil/geometry candidates compared at matched Reynolds number

## 3. Thrust Vector Control (Magnetic Solenoid)

### 3.1 Mechanism

The sustainer 29 mm motor sits in a **gimbaled cradle** (`3DP/Rocket/06_tvc_gimbal_mech`,
PC-FR) supported by a 2-axis pivot, giving ±5° pitch/yaw authority. Three pull-solenoids at
120° act on the cradle's upper arm ring; differential pull vectors the nozzle. Springs return
the gimbal to neutral on power loss (fail-safe).

- *Actuators*: 3 × TOMSHIELE 12 V mini push-pull electromagnets (10–25 N at small air-gap)
- *Geometry*: cradle Ø75 mm gimbal, pull-arm radius ~23 mm; gimbal pivots on X and Y trunnions (Ø5 mm)
- *Authority*: τ_cmd = 0.491 N·m at ±5°; disturbance τ = 0.089 N·m at 1° (Mathematics §8)

### 3.2 Drive & control

Each solenoid is driven by a low-side AO3400A N-FET at **20 kHz PWM** from the RP2350B PWM
slices, with an SS34 freewheel diode and a 20 mΩ shunt for **closed-loop current control** via
the 8-channel ADC. The control architecture is two nested loops on two axes:

1. *Inner current loop* (≥4 kHz): shunt → RC → ADC → PWM duty per coil.
2. *Outer attitude loop*: pitch/yaw error from the ICM-42688-P + BNO055 fusion → 3-coil mixing
   → per-coil current setpoints.

This is the "2 × 2-axis closed-loop control system": pitch and yaw, each with current + attitude
loops. See FCM PCB doc §2.3.

## 4. Avionics — FCM (summary)

The two-board avionics stack (Board 1 TVC Actuator + Board 2 Main Flight Computer) is documented
fully in *PCB/WYVERN_E2_TwoBoard_Spec.md* (+ *WYVERN_E2_Survivability.md*). Headline content:

- *MCU*: RP2350B (QFN-80, 48 GPIO, 8 ADC, dual M33)
- *Storage*: W25Q32 QSPI boot + SD-NAND (XTSD04G, 4 GB) data log + edge microSD backup
- *Sensors*: ICM-42688-P (6-axis), 2× BME688 + BMP280 (gas/T/P/RH/baro), LIS3MDL (mag),
  INA219 (power), piezo vibration, + 2× BNO055 (onboard + gimbal breakout) 9-DOF
- *Data/IO*: USB-C 2.0, OV camera 2×9 header (no radio link — all data is logged onboard and retrieved post-flight)
- *Pyro*: onboard RP2350B pyro channels (drogue/main + hardware continuity) + 2nd-stage ignition FET
- *Power*: 12 V Tenergy NiCd → dual TPS54202 buck (3.3 V + 5 V); 12 V coil bus, INA219 monitored

### 4.1 Sensor suite — data captured

Altitude (baro), 3-axis position/orientation (BNO055 quaternion + IMU integration), 3-axis
gyro, 3-axis acceleration (high-g ICM-42688-P), temperature, pressure, humidity (BME688/BMP280),
magnetic field (LIS3MDL + BNO055), vibration (piezo → ADC), bus voltage/current (INA219), and
pyro continuity — logged to SD-NAND (4 GB) at full loop rate with edge-mounted microSD backup, and retrieved post-flight from onboard storage (no radio downlink).

### 4.2 Camera

OV-series parallel-interface module on the 2×9 header (D0-7 on contiguous GPIO2-9 for PIO
capture). Mounted in the camera pod fairing (`3DP/Rocket/10_camera_pod_fairing`, ASA) with a
side window in the avionics bay; footage recorded to NAND/microSD for post-flight retrieval.

## 5. Propulsion & Staging

| Stage | Motor | Role |
|---|---|---|
| 1 (Booster) | AeroTech G78 Mojave Green 29 mm | Liftoff + initial boost (110 N·s) |
| 2 (Sustainer) | AeroTech F25 White Lightning 29 mm | TVC-controlled sustain phase (77.9 N·s) |

### 5.1 Staging sequence & interlock

1. *Liftoff* on G78 (booster). Fixed fins + TVC neutral.
2. *Booster burnout* (t≈1.40 s). Flight computer detects thrust drop (accel < threshold).
3. *Sustainer ignition*: onboard FET (Q4) fires the First Fire Jr. igniter → F25 lights.
   TVC active from ignition.
4. *Booster separation*: the interstage coupler releases (drag separation aided if needed).
   **The booster ejection charge (drogue) is inhibited until sustainer ignition + separation
   are confirmed** so the chute is never deployed under thrust — implemented as a firmware
   arm-gate on the onboard drogue pyro channel keyed to the staging state machine.
5. *Booster recovery*: small chute deploys on the onboard drogue event after separation.
6. *Sustainer apogee*: the onboard main event deploys the nose/main chute; nose and parachute joined
   by 6 ft of 1/8″ tubular Kevlar shock cord.

### 5.2 Pyrotechnics

- *Initiators*: MJG Firewire Initiator (3 ft stripped leads) — 2 ejection events
- *Ejection charge*: FFFFg black powder in E-Match Mate bulkhead canisters
- *2nd-stage igniter*: AeroTech First Fire Jr. (for D–G composite motors)

## 6. Recovery

- *Booster chute*: Apogee 18″ elliptical → 6.0 m/s at 0.36 kg booster descent mass
- *Sustainer/nose main*: Apogee 24″ elliptical → 7.5 m/s at ~1.0 kg descent mass (carries the avionics + pack; Math §6)
- *Shock cord*: 6 ft, 1/8″ tubular Kevlar, nose ↔ recovery bay bulkhead
- *Controller*: onboard RP2350B dual-deploy — drogue/main fired from the FCM pyro channels with hardware continuity sense + the RBF arm-gate (no external altimeter)

## 7. Ground Support Equipment

### 7.1 Wind tunnel (fin characterization)

Base platform: the Printables *Modular Wind Tunnel for STEM Education* + the *120 mm Fan
Adapter v1*, both printed in PLA. A **custom fin test mount** (`3DP/WindTunnel/WT_fin_test_mount`,
PLA) seats in the test-section floor and holds **one fin at a time** upright with a 15°-indexed
turntable (AoA sweep) and a balance/cable pass-through. A companion 120 mm fan → 100 mm tunnel
collar (`WT_120mm_fan_collar`) mates the fan adapter. The mount accepts the flight fin geometry
(root 92 mm × span 46 mm) with margin in the test section. Candidate geometries/airfoils are
compared at matched Reynolds number to down-select the single fixed fin.

### 7.2 Motor test stand

A vertical thrust stand (`3DP/TestStand/*`, PC-FR) characterizes the 29 mm motors. The motor
cradle transmits axial thrust into a Wishiot bar load cell (10 kg configuration, HX711
amplifier) read by an Adafruit Metro M4 logging to a microSD breakout. Calibrated with Estes
E16-4 motors (Math §10). The base plate stakes into dirt at the test site for reaction.

- *TS_base_plate* — staked ground plate (4 × Ø60 mm stake sockets)
- *TS_motor_tower* — vertical cradle + load-cell seat pocket (80 × 12.7 mm bar cell)
- *TS_loadcell_bracket* — bar-cell mounting bracket

> *Caution*: the 10 kg (98 N) cell is below the G78 peak (101.9 N). Re-zero before each test
> and watch for clipping at peak; swap to a 20 kg cell if clipping is observed (Math §10).

### 7.3 Launch system

COTS Estes Pro Series II launch rail + controller combo. *Note*: rail-exit velocity is
marginal at 10.0 m/s (Math §4) — use the rail extension or reduce print mass to raise it.

## 8. Test & Launch Site

*Maryland & Delaware Rocketry Association (MDRA)* — the nearest TRA/NAR club to Wilmington, DE.
Primary site: **Coverdale Farm area / Higgs Farm (Price, MD)** and the **Central Sod Farm
(Centreville, MD)**; club calendar at mdrocketry.org. These sites support the F/G impulse class
and the soft sod is well-suited to the 3D-printed airframe's 10.0 m/s descent. Confirm a
launch date, waiver, and that two-stage + onboard-energetics operations are cleared with the
RSO before travel. For motor static-fire testing, the staked PC-FR stand may be used at a
private rural site with appropriate fire precautions and local approval.

## 9. File Manifest

| Deliverable | Path |
|---|---|
| Board 1 TVC Actuator (sch/pcb/pro) | `PCB/FCM_KiCAD/WYVERN_E2_B1.*` |
| Board 2 Main FC (sch/pcb/pro) | `PCB/FCM_KiCAD/WYVERN_E2_B2.*` |
| PCB documentation | `PCB/WYVERN_E2_TwoBoard_Spec.md`, `PCB/WYVERN_E2_Survivability.md`, `PCB/FCM_KiCAD/gerbers/WYVERN_E2_PCBA_Sourcing.md` |
| Revised proposal | `Docs/WYVERN_E2_Revised_Proposal.md` |
| This technical document | `Docs/WYVERN_E2_Technical_Document.md` |
| Mathematics | `Docs/WYVERN_E2_Mathematics.md` (+ `Docs/sim/we2_traj.py`) |
| Build & launch procedures | `Docs/WYVERN_E2_Build_and_Launch_Procedures.md` |
| BOM | `Docs/WYVERN_E2_BOM.xlsx` / `.md` |
| 3DP — rocket | `3DP/Rocket/*.stl` + `*.step` (12 parts + assembly) |
| 3DP — wind tunnel | `3DP/WindTunnel/*` |
| 3DP — test stand | `3DP/TestStand/*` |
| Parametric CAD source | `3DP/_generator/{wcad,gen_rocket}.py` |

## 10. Heritage & Citations

AeroTech/RCS G78 & F25 data sheets; ThrustCurve.org; Raspberry Pi RP2350 datasheet; Bosch
BME688/BMP280; TDK ICM-42688-P; ST LIS3MDL; TI INA219 / TPS54202; Adafruit 2472
(BNO055); Barrowman (1966) CP method; MDRA (mdrocketry.org). Reuses the verified XRIM-117E Rev
B/C electrical audit.
