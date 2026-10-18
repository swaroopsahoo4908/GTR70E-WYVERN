---
source_file: "XRIM117_WYVERN_PitchDeck.pptx"
source_type: "PPTX"
updated_at: 2026-05-26
---
# XRIM117_WYVERN_PitchDeck

*Extracted from [[XRIM117_WYVERN_PitchDeck.pptx]]*

---

### Slide 1

PROTOTYPE TECHNOLOGY DEMONSTRATOR

XRIM-117 WYVERN

Autonomous Guided Demonstrator Platform

70mm · Active mid fins + passive aft stabilizers · Ceramic jetavane TVC · 3-board distributed avionics · 915MHz datalink

Skylight Industries LLC  ·  PDR-002 Rev A  ·  CONFIDENTIAL

### Slide 2

MISSION

Why WYVERN?

A hardware-first approach to validating guided autonomous flight control in a subscale, recoverable, repeatably-flyable platform.

70mm

OD

body diameter

10

srvs

total actuators

915

MHz

datalink range

3

PCBs

avionics stack

OBJECTIVES

Programme Objectives

Validate hybrid control architecture

Demonstrate coordinated aerodynamic fin + ceramic jetavane TVC authority across boost, loiter, and landing burn phases.

Prove distributed avionics concept

Three-board redundant-sensor architecture with independent power domains and fault detection.

Demonstrate powered vertical recovery

Full-profile autonomous flight: rail launch → guided ascent → altitude loiter → propulsive landing.

Generate quantitative flight data

Log 100Hz sensor fusion data via 915MHz LoRa for post-flight control law validation.

### Slide 3

VEHICLE

Vehicle Configuration

Chute bay

ASAM-1 · mid fins

CCM · avionics · LoRa

ASAM-2 · jetavane · sustainer

Booster · eject ring

SCALE

1:2.14 of full system

DIAMETER

70mm OD

LENGTH

~1,170mm

MASS (EST.)

~640g all-up

STRUCTURE

PETG-CF printed

FIN RINGS

1× active + 1× passive

TVC

Ceramic jetavane

PROPULSION

2-stage solid motor

RECOVERY

Computer-triggered chute

DATALINK

915MHz LoRa · ~2km LoS

### Slide 4

CONTROL

Hybrid Control Architecture

WYVERN employs a cascaded PID control system that blends aerodynamic authority from an active mid fin ring (Ring 2) with thrust-vector control from ceramic jetavanes. Passive aft fins (Ring 1) provide baseline stability. Authority allocation shifts with dynamic pressure.

Outer loop — altitude

PID on altitude error → pitch/yaw setpoint

Inner loop — attitude

PID on quaternion error → fin + jetavane commands

TVC mixing

Pitch: jetavane A  ·  Yaw: jetavane B  ·  decoupled

Fin mixing

Pitch ±: top/bottom  ·  Yaw ±: left/right  ·  Roll: Ring 2 collective cant (45° clocking)

Control authority by phase

Boost

85%

Rail clear

60%

Loiter

30%

Descent

50%

Landing burn

80%

Jetavane TVC

Aerodynamic fins

### Slide 5

AVIONICS

3-Board Distributed Avionics Stack

ASAM-1

Mid Ring Controller

STM32F411 · Cortex-M4 100MHz

ICM-42688-P IMU · MS5611 baro

4× servo PWM · 7.4V HV rail

1S 1000mAh independent LiPo

CCM

Central Command Module

RP2040 · dual-core 133MHz

Primary IMU + barometer

3× pyrotechnic MOSFET channels

LoRa 915MHz · ~2km datalink

ASAM-2

TVC + Sustainer Controller

STM32F411 · Cortex-M4 100MHz

ICM-42688-P IMU · MS5611 baro

3× servo PWM (jetavane + slide)

Sustainer ignition relay

All boards: 62mm circular · 2-layer FR4 · ENIG · EasyEDA design · JLCPCB fabrication + SMT assembly  ·  Power fully independent per board  ·  JST-GH 8-pin inter-board ribbon

### Slide 6

FLIGHT PROFILE

Autonomous 8-Phase Flight Profile

0

Safe

Pre-arm · servos neutral

1

Armed

IMU cal · GCS link · pyro continuity

2

Boost

Booster ignites · rail exit

3

Rail clear

Fins active · attitude hold

4

Staging

Booster eject · sustainer ignition

5

Loiter

Altitude hold · jetavane + fins

6

Descent

Thrust-modulated landing burn

7

Touchdown

Impact detect · disarm

Phase 8 — ABORT

GCS abort command OR attitude error >45° for >0.5s OR altitude runaway → ejection charge fires → nose cone separates → 24in parachute deploys → ballistic recovery

~120m

target altitude (nominal)

10–20s

loiter duration

<1 m/s

touchdown velocity

100Hz

sensor log rate

### Slide 7

TVC

Ceramic
Jetavane TVC

Two Macor ceramic vanes sit in the nozzle exhaust stream on titanium shafts. Each vane rotates ±45° to simultaneously deflect the thrust vector and partially occlude the nozzle exit — providing both attitude control and analogue thrust modulation from a single actuator per axis.

Vane material

Macor / ZTA ceramic

Vane rotation

±45° per axis

Thrust range

~35–100% of rated

Actuator

KST X08 Plus HV

Axes

Pitch + Yaw independent

Fail-safe

Spring return → full thrust

HOW IT WORKS

How jetavane TVC works

1

Vane at 0° — full thrust, neutral vector

Vane aligned with flow. Minimal blockage. Motor delivers rated thrust. No deflection.

2

Vane rotated — vectored exhaust

Rotation deflects exhaust stream up to ~20° from motor axis. Generates corrective torque on vehicle without moving the motor.

3

Vane near 90° — thrust reduction

Vane near-perpendicular to flow. Exit area partially blocked. Effective thrust reduced to ~35% for landing burn deceleration.

Historical precedent: V-2 rocket (1942) and early surface-to-air systems used graphite jetavanes on identical principles. WYVERN applies this to a hobby-scale platform with ceramic materials and closed-loop digital control.

### Slide 8

PROGRAMME

Build & Test Programme

Phase 1

Design & Fabrication

Wks 1–3

OpenRocket model + stability verification

PETG-CF parts CAD (nose, fin cans, TVC frame)

PCB design in EasyEDA — 62mm circular

Phase 2

Print & Mechanical

Wks 3–5

Print all PETG-CF structural parts

Jetavane shaft + ceramic vane assembly

Booster ejection ring + spring test

Phase 3

Electronics

Wks 5–7

Receive JLCPCB SMT boards

Firmware flash + IMU/baro calibration

Full 6-servo bench sweep test

Phase 4

Integration & Ground Test

Wks 7–8

Ejection charge ground test

Jetavane static fire test

Full GCS datalink verification

Phase 5

Flight Test Campaign

Wk 9+

Flight 1: booster only · recovery verify

Flight 2: two-stage · no landing burn

Flight 3+: full profile · progressive altitude

### Slide 9

BUDGET

Programme Budget Overview

~$660

estimated build cost — single vehicle

$145

One-time PCB setup

Subsequent builds ~$280 total

2

Flights per motor set

$124 recurring cost

wks

Months to first flight

5-phase structured programme

All components sourced from commercial hobby and COTS electronics suppliers. No custom tooling required.

### Slide 10

XRIM-117 WYVERN

Let's talk.

Skylight Industries LLC  ·  PDR-002 Rev A

XRIM-117 WYVERN Prototype Technology Demonstrator

Autonomous guided demonstrator platform · 70mm · active mid fins + passive aft stabilizers · ceramic jetavane TVC · 3-board distributed avionics

CONFIDENTIAL · FOR DISCUSSION PURPOSES ONLY · NOT FOR DISTRIBUTION