# WYVERN-E 3.0 — Power, Mass & Motor Feasibility

### Skylight Rocketry · Off-the-shelf Raspberry Pi 5 TVC vehicle
##### Two-stage, slimmed all-PC-FR, no-waiver. Supersedes the 2.0 custom two-board architecture.
## 0. Headline result

The Raspberry Pi 5 flight computer is **heavy** (~340 g of avionics + power), which drives the
whole design:

1. *The F25W is unflyable.* At ~1 kg the F25W (25.6 N avg) gives **T/W ≈ 2.0** — far below the
   ≥5 needed to leave the rod. Thrust, not burn time, is the binding limit.
2. *Two-stage stays no-waiver only if slimmed hard.* The FAA/NAR Class-1 gates are **≤1500 g
   liftoff and ≤125 g total propellant**. An all-PC-FR slim build lands at **1.22 kg / ~80 g
   propellant** — both inside the gates, so **no waiver and no Level-1 cert**.
3. *Long TVC burn ⇒ a long-burn sustainer.* A low-thrust long-burn **G25W (4.7 s)** is ideal as
   a sustainer (the vehicle is already moving at staging, so it needs no high T/W). Oversized
   fins hold the apogee to **~1050–1100 ft** under the long burn.
## 1. Power budget

Continuous electronics load (the Pi 5 dominates; all sensors together < 0.5 W):

| Load | Idle (W) | Active (W) |
|---|---|---|
| Raspberry Pi 5 (4 GB) + active cooler | 3.50 | 6.50 |
| Camera Module 3 (recording) | 0.05 | 0.30 |
| 3× BNO085 | 0.12 | 0.12 |
| LSM6DSO32 + LIS2MDL + BMP280 + BME688 | 0.05 | 0.07 |
| 2× microSD breakout (writing) | 0.10 | 0.70 |
| RRC3+ | 0.02 | 0.05 |
| Buck/PD/BMS power electronics | 0.40 | 0.60 |
| **Total continuous** | **4.23** | **8.33** |

TVC is intermittent (burn only): solenoid ~33 W peak / servo ~22 W peak for ~1.8 s — energy
negligible, but it sets the discharge-current and buck rating.

### Energy & battery

$E = 4.2\,\text{W}\cdot 2.5\,\text{h (idle)} + 8.3\,\text{W}\cdot\frac{10\,\text{min}}{60}\cdot 5\,\text{flights} = 17.7\,\text{Wh}$ → **23.8 Wh with 35 % margin.**

A **3S Li-ion 3000 mAh (33.3 Wh)** pack gives **1.9× margin** — comfortably 5 flights + 2 h+
idle. 11.1 V feeds the solenoids directly; bucks supply 5 V/5 A (Pi 5) and 6 V (servos).
USB-C PD charge board (3S, 12.6 V) recharges in ~1 h.
## 2. Mass budget (two-stage, slimmed all-PC-FR)

| Group | Mass (g) |
|---|---|
| Sustainer avionics (Pi 5, camera, 3× BNO085, LSM6DSO32, LIS2MDL, BMP280, BME688, 2× µSD, RRC3+, harness) | 189 |
| Sustainer power (3S 3000 mAh pack + BMS/PD + bucks) | 190 |
| Sustainer structure (PC-FR: FC bay, bulkhead, TVC bay, nose, fins) | 300 |
| Sustainer recovery + nose BNO085 | 116 |
| Sustainer TVC mechanism — **solenoid** / **servo** | 120 / 220 |
| Sustainer motor (G25W loaded) | 124 |
| **Sustainer all-up** | **≈ 1039 / 1139 g** |
| Booster structure (PC-FR fins + body + interstage) | 180 |
| Booster motor (F32 loaded) | 70 |
| **LIFTOFF total (solenoid / servo)** | **≈ 1289 / 1389 g** |

Both under the **1500 g** ceiling; propellant F32 (~16 g) + G25W (62 g) = **~78 g < 125 g**. ✓
## 3. Motor selection (two-stage, 29 mm, ≤ G class)

| Stage | Motor | Itot (N·s) | Favg (N) | Burn (s) | Role |
|---|---|---|---|---|---|
| Booster | **AeroTech F32-class** | ~30 | 32 | ~1.0 | clears the rod (T/W 5.3), then stages |
| Sustainer | **AeroTech G25W** | 117 | 25 | **4.7** | the long TVC demonstration burn |

Why this pair: the booster gives rod-clearance T/W ≥ 5 for the stack; the **G25W's 4.7 s
low-thrust burn** is the TVC window (post-staging the vehicle is already at ~30 m/s, so low
T/W is fine). **Oversized fins (Cd ≈ 0.9)** hold apogee to **~1050–1100 ft** despite the long
burn (a bigger booster would push past 1800 ft). Static-fire peaks exceed the old 10 kg
(98 N) load cell → **20 kg cell** for the stand (BOM §8).

*Apogee/burn trade locked:* long ~4.7 s TVC burn + apogee ≤ ~1100 ft are prioritized over a
high booster-staging altitude. Staging is low (~40–60 ft); TVC stabilizes the sustainer from
ignition (fins are passive backup), which is acceptable for an actively-controlled testbed.
## 4. What changed vs 2.0

- *Off-the-shelf* — no custom PCBs. Raspberry Pi 5 + breakout sensors on an I²C/SPI harness.
- *Two-stage retained* — F32 booster + long-burn G25W TVC sustainer; slimmed all-PC-FR to stay
  under 1500 g / 125 g propellant (no waiver, no L1).
- *RRC3+* — fires the sustainer (2nd-stage) ignition after booster separation, and the
  recovery charges (drogue/main).
- *Arming* — a pulled jumper pin on the rod arms the flight computer; launch is detected by an
  accelerometer threshold (LSM6DSO32 / BNO085) so no pyro can fire on the pad.
- *TVC A/B* — tri-solenoid **and** servo-gimbal (BPS-style, up-rated) systems both built and
  compared: 3 flights each + 2 ground static fires per motor.
