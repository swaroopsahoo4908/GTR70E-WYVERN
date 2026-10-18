# WYVERN-E 3.0 — TVC Actuation A/B Comparison (RQ4)

### Skylight Rocketry · tri-solenoid vs servo-gimbal thrust vector control
##### Both systems fly the same Pi-5 airframe on a G25W sustainer; 3 flights each + ground rig.
## 1. Why two systems

The 1.0/2.0 program used a magnetic-solenoid gimbal. 3.0 directly benchmarks that approach
against the servo-gimbal architecture popularized by BPS Space — but **up-rated for a real G
motor** instead of the small D/E motors BPS flies. The deliverable is a quantitative answer to
"which actuator gives better closed-loop control authority for an amateur TVC rocket at this
thrust class," across identical airframe, sensors, control loop, and flight profile.
## 2. Gimbal load & actuator sizing

The sustainer sits in a ±5° gimbaled cradle. At the **G25W peak (~100 N)** the gimbal-axis
torque to hold ±5° (thrust-offset + friction + dynamic term) is:

$$\tau_{gimbal} \approx F_{pk}\,d_{pivot}\,\sin\theta \times 1.6 = 100 \times 0.045 \times \sin 5° \times 1.6 \approx 0.63\ \text{N·m}$$

| System | Actuator | Required (SF 2.5) | Selected | vs BPS |
|---|---|---|---|---|
| A — solenoid | 3× 12 V pull-solenoids (10–25 N) | n/a (force, PWM) | TOMSHIELE 12 V | — |
| B — servo | 3× digital metal-gear servo | **~16 kg·cm** | **~35 kg·cm (DS3235-class)** | ~8× BPS's 2 kg·cm micro |

BPS Space TVC mounts use ~9 g micro servos (~2 kg·cm) on ~10 N D/E motors; the G25W is ~8–10×
that thrust, so System B needs high-torque digital servos, not micro servos. This up-rating is
the core of the "compensate for the much higher thrust" requirement.
## 3. Architectural comparison

| Attribute | A — Tri-solenoid | B — Servo gimbal |
|---|---|---|
| Control type | on/off + PWM, 3-coil mixing (bang-bang) | proportional angular position |
| Position feedback | none (open-loop force; current-sensed) | servo internal pot/encoder |
| Bandwidth | high (electrical, ~hundreds Hz) | limited by servo slew (~0.1 s/60°) |
| Deadband/backlash | none mechanical | gear backlash present |
| Smoothness | coarse (discrete pulls) | smooth |
| Peak power | ~33 W (3×1 A @ 11.1 V) | ~22 W (3×1.2 A @ 6 V) |
| Mass (mechanism) | ~120 g | ~220 g |
| Failure mode | spring return to neutral | servo holds last / centers on signal loss |
| Complexity | MOSFET driver + springs | servos + linkages + PWM expander |
## 4. Common test conditions (controlled variables)

Identical across both systems so the actuator is the *only* independent variable:

- Same airframe, mass-matched with ballast (servo build is ~100 g heavier → solenoid build
  ballasted to match for like-for-like flight dynamics).
- Same Pi-5 flight computer, sensor suite, and control-loop gains structure (re-tuned per
  actuator, but same architecture + reference trajectory).
- Same motor (G25W), same launch site/rail, same nominal weather window.
- Same data capture: 3× BNO085 + LSM6DSO32 + LIS2MDL at full loop rate to dual microSD.
## 5. Measured metrics

Ground rig (bench gimbal + dummy load) **and** flight:

1. *Step response* — settling time, overshoot, steady-state error to a commanded gimbal step.
2. *Slew rate* — max deg/s the gimbal achieves under load.
3. *Bandwidth* — frequency at which command-to-response gain falls 3 dB.
4. *Deadband / backlash* — minimum effective command; hysteresis.
5. *Disturbance rejection* — attitude error vs the gimbal-mounted BNO085 during the burn.
6. *Stabilize-then-maneuver* — time to stabilize after staging, then tracking error on a
   commanded attitude maneuver within the 4.7 s window.
7. *Power & thermal* — current draw, coil/servo temperature rise.
## 6. Flight test matrix

| Flight | TVC | Objective |
|---|---|---|
| F1 | solenoid | shakedown — arm/launch-detect, logging, recovery, stabilize-only |
| F2 | solenoid | stabilize + commanded pitch maneuver |
| F3 | solenoid | repeat maneuver (repeatability) |
| F4 | servo | shakedown — same profile as F1 |
| F5 | servo | stabilize + commanded pitch maneuver |
| F6 | servo | repeat maneuver (repeatability) |

Plus 2 ground static fires each of the F32 booster and G25W sustainer (thrust curves), and the
bench TVC characterization of both systems before any flight.
## 7. Hypothesis

The servo gimbal is expected to give *smoother, lower-steady-state-error* proportional control
but with *lower bandwidth* and gear backlash; the solenoid system is expected to be *faster and
lighter* but *coarser* (limit-cycle around neutral). The long 4.7 s G25W burn gives enough
window to characterize both stabilization and a deliberate maneuver for each — the data
decides which is the better amateur-TVC actuator at the G-motor thrust class.
