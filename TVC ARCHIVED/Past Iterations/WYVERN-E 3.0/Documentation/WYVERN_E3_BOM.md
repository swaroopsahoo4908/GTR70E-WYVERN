# WYVERN-E 3.0 — Bill of Materials

### A Skylight Rocketry Venture
##### 84 mm two-stage Raspberry Pi 5 TVC research vehicle · off-the-shelf, no custom PCBs
##### Two TVC systems built for A/B comparison (solenoid vs servo); 3 flights each + ground tests.

> **The fully costed, live-linked, in-stock version of this BOM is `WYVERN_E3_BOM.xlsx`** (verified
> June 2026; every line has a working purchase link + stock status). Grand total **$1,505.63**.
> This Markdown copy is the human-readable summary; the spreadsheet is canonical for prices/links.
## 1. Flight Computer (off-the-shelf)

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| Raspberry Pi 5 (4 GB) | Raspberry Pi | 1 | 60.00 | 60.00 |
| Active cooler (heatsink + fan) | Raspberry Pi | 1 | 5.00 | 5.00 |
| Camera Module 3 (wide, NoIR optional) | Raspberry Pi | 1 | 25.00 | 25.00 |
| BNO085 9-DOF (TVC gimbal-mounted) | Adafruit 4754 | 1 | 24.95 | 24.95 |
| BNO085 9-DOF (central FC module) | Adafruit 4754 | 1 | 24.95 | 24.95 |
| BNO085 9-DOF (nose cone) | Adafruit 4754 | 1 | 24.95 | 24.95 |
| LSM6DSO32 6-axis IMU (±32 g accel + gyro) | Adafruit 4692 | 1 | 11.95 | 11.95 |
| LIS2MDL 3-axis magnetometer | Adafruit 4488 | 1 | 4.95 | 4.95 |
| BMP280 barometer | Adafruit 2651 | 1 | 9.95 | 9.95 |
| BME688 gas/T/P/RH (VOC) | Adafruit 5046 | 1 | 22.50 | 22.50 |
| microSD breakout (SPI) + 32 GB card — video | Adafruit 4682 + card | 1 | 12.95 | 12.95 |
| microSD breakout (SPI) + 32 GB card — flight log | Adafruit 4682 + card | 1 | 12.95 | 12.95 |
| TCA9548A I²C multiplexer (3× BNO085 same-addr) | Adafruit 2717 | 1 | 6.95 | 6.95 |
| Pull-pin arming jumper + keyed connector | assorted | 1 | 5.00 | 5.00 |
| GPIO breakout/proto HAT + harness | assorted | 1 | 18.00 | 18.00 |
| **Subtotal** | | | | **270.05** |
## 2. Power System (USB-C rechargeable)

Sized for 5 flights + 2 h+ idle (≈ 24 Wh w/ margin → 33 Wh pack, 1.9× margin). 11.1 V feeds
solenoids directly; bucks supply 5 V/5 A (Pi 5) and 6 V (servos). See *Power_Mass_Motor* §1.

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| 3S Li-ion pack, 11.1 V 3000 mAh (33 Wh) | 18650 ×3 | 1 | 30.00 | 30.00 |
| 3S BMS + USB-C PD charge board (12.6 V) | IP2368-class | 1 | 16.00 | 16.00 |
| 5 V / 5 A buck (Raspberry Pi 5 rail) | module | 1 | 10.00 | 10.00 |
| 6 V / 5 A buck/UBEC (servo rail) | module | 1 | 8.00 | 8.00 |
| Power switch + distribution + fuse | assorted | 1 | 8.00 | 8.00 |
| **Subtotal** | | | | **72.00** |
## 3. Recovery & Pyro

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| RRC3+ dual-deploy altimeter (apogee → drogue/main) | MissileWorks | 1 | 79.95 | 79.95 |
| 24″ elliptical main chute | Apogee | 1 | 16.95 | 16.95 |
| 1/8″ tubular Kevlar shock cord (8 ft) | BuyRocketMotors | 8 | 1.50 | 12.00 |
| MJG Firewire initiators (recovery charges) | MJG | 4 | 3.50 | 14.00 |
| E-Match Mate bulkhead canister | Apogee | 1 | 7.95 | 7.95 |
| FFFFg black powder (per-flight lot) | — | 1 | 4.00 | 4.00 |
| **Subtotal** | | | | **134.85** |
## 4. TVC — Solenoid System (A)

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| 12 V mini pull-solenoid (TVC actuator) | TOMSHIELE | 3 | 9.99 | 29.97 |
| 3-channel low-side MOSFET driver board (logic-level, PWM) | generic | 1 | 12.00 | 12.00 |
| SS34 freewheel diodes + 0.02 Ω shunts (current sense) | assorted | 1 | 6.00 | 6.00 |
| Gimbal mechanism (PC-FR cradle, pivots, return springs) | printed + hw | 1 | 22.00 | 22.00 |
| **Subtotal** | | | | **69.97** |
## 5. TVC — Servo System (B, BPS-style, up-rated)

Sized for the G64W: gimbal-axis torque ≈ 0.63 N·m at ±5°/100 N peak → **~16 kg·cm** required
(SF 2.5); BPS's 9 g micro servos (~2 kg·cm, for ~10 N motors) are ~8× too weak, so high-torque
digital metal-gear servos are used. See *Power_Mass_Motor* §3 + *TVC_Comparison*.

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| High-torque digital servo (~35 kg·cm, metal gear, DS3235) | ANNIMOS | 3 | 18.99 | 56.97 |
| PCA9685 16-ch PWM servo driver (I²C) | Adafruit 815 | 1 | 8.95 | 8.95 |
| Servo gimbal linkage + ball-links + mount (PC-FR) | printed + hw | 1 | 25.00 | 25.00 |
| **Subtotal** | | | | **90.92** |
## 6. Propulsion (motors — A/B test plan)

3 flights × 2 TVC methods = **6 flights** (each = 1 booster + 1 sustainer); **2 ground static
fires per motor type**; plus the RQ3 jetvane erosion campaign on E-class motors.

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| **AeroTech G25W-10A** sustainer reload (#072510) — 6 flights + 2 ground | AeroTech | 8 | 30.99 | 247.92 |
| **AeroTech F40-7W** booster reload (#64007) — 6 flights + 2 ground | AeroTech | 8 | 14.99 | 119.92 |
| **RMS-29/40-120 hardware set** (#91291) — covers *both* stages; ×2 (one per stage, flown together) | AeroTech | 2 | 86.99 | 173.98 |
| First Fire Jr igniters (3-pk; spares/2nd-stage — reloads ship with their own) | AeroTech | 2 | 9.99 | 19.98 |
| E-class motors — jetvane erosion test (RQ3) | Estes E12-0 | 6 | 10.00 | 60.00 |
| **Subtotal** | | | | **621.80** |
## 7. Airframe & Mechanism (filament, by mass)

RQ2 down-selects among PETG-CF / ASA / PLA Basic; PC-FR for fins + TVC + bulkhead (heat/flame).

| Item | Source | Qty (kg) | Unit ($/kg) | Line ($) |
|---|---|---:|---:|---:|
| PETG-CF (primary structure + FC bay) | Bambu Labs | 0.380 | 25.99 | 9.88 |
| ASA Aero (nose / fairings) | Bambu Labs | 0.080 | 45.99 | 3.68 |
| PC-FR (fins + TVC bay + bulkhead) | Bambu Labs | 0.280 | 43.99 | 12.32 |
| PLA Basic (RQ2 fin test articles) | Bambu Labs | 0.060 | 19.99 | 1.20 |
| **Subtotal** | | | | **27.08** |
## 8. Ground Support Equipment (one-time)

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| Static stand 20 kg load cell + HX711 (G64W peak ~100 N > old 10 kg cell) | Amazon | 1 | 14.99 | 14.99 |
| Adafruit Metro M4 + microSD (stand DAQ) | Adafruit | 1 | 35.00 | 35.00 |
| Servo TVC ground test rig (bench gimbal + dummy load) | printed + hw | 1 | 25.00 | 25.00 |
| Estes Pro Series II launch rail + controller | Estes | 1 | 124.00 | 124.00 |
| PLA filament (wind tunnel) | est | 0.800 | 19.99 | 15.99 |
| **Subtotal** | | | | **214.97** |
## 9. Totals

| Category | Subtotal ($) |
|---|---:|
| 1. Flight Computer | 270.05 |
| 2. Power System | 72.00 |
| 3. Recovery & Pyro | 134.85 |
| 4. TVC — Solenoid System (A) | 69.97 |
| 5. TVC — Servo System (B) | 90.92 |
| 6. Propulsion (6 flights × booster+sustainer + 2 ground each + erosion) | 621.80 |
| 7. Airframe (filament) | 27.08 |
| 8. Ground Support Equipment (one-time) | 214.97 |
| **GRAND TOTAL** | **1,505.63** |

*Per-flight consumables* (F40-7W booster + G25W-10A sustainer reloads + spare igniter + BP ≈ $46/flight;
the single RMS-29/40-120 case family covers both stages — 2 sets so a 2-stage flight has one case per
stage — and is fully reusable). AeroTech reloads ship with their own igniter.
The flight computer, both TVC systems, power pack, RRC3+, casings, and GSE are non-recurring or
reusable. Both TVC systems are built once and swapped between the 6 flights (3 each).

> *No custom PCBs, no LoRa/radio (data logged onboard to dual microSD, retrieved post-flight),
> two-stage but no FAA waiver / no Level-1 cert: liftoff ≈ 1.29–1.39 kg < 1500 g, total
> propellant ≈ 78 g < 125 g, both motors ≤ G class.*
