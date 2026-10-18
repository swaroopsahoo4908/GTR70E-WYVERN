# WYVERN-E 3.0

An open-source, two-stage, 84 mm, 3D-printed research rocket demonstrating closed-loop
*thrust-vector control (TVC)* on an **off-the-shelf Raspberry Pi 5 flight computer**, flying a
direct **A/B comparison of two TVC actuation methods** (tri-solenoid vs servo-gimbal), with a
full ground-support ecosystem (wind tunnel + motor test stand).

A Skylight Rocketry venture by Allison Hong, Chris Liu, and Swaroop K. Sahoo. Architecture
revision PDR-006. *Supersedes 2.0 (custom RP2350B two-board PCB stack).*

## Overview

3.0 replaces the custom PCBs with a **Raspberry Pi 5** + COTS sensor harness: 3× BNO085
(gimbal/FC/nose), LSM6DSO32, LIS2MDL, BMP280, BME688, Camera Module 3, and dual 32 GB microSD
(no radio — data retrieved post-flight). The sustainer carries oversized fixed fins and a ±5°
TVC gimbal driven by **either** a tri-solenoid system **or** a servo system (BPS-style, up-rated
~8× for the G-motor thrust) — flown head-to-head. A long-burn **AeroTech G25W (4.7 s)** sustainer
gives the TVC demonstration window; an F-class booster clears the rod. The whole vehicle stays
**under the FAA/NAR no-waiver limits** (≤ 1500 g, ≤ 125 g propellant, ≤ G class).

## Research questions

1. Fin aerofoil profile and deflection aerodynamics (wind tunnel, 0.5° sweeps).
2. Print material and surface coating performance for fins (PC-FR, PETG-CF, ASA, PLA + coatings).
3. Motor thrust characterization and material erosion as jetvane candidates (test stand).
4. **TVC actuation A/B** — tri-solenoid vs servo-gimbal closed-loop control authority over a
   long sustainer burn (3 flights each).

## Repository structure

| Folder | Contents |
|---|---|
| `Senior Research/Proposal/` | Research proposal (Markdown / DOCX / PDF) |
| `Documentation/` | Technical document, mathematics, power/mass/motor analysis, TVC comparison, BOM, build/launch |
| `PCB/` | Off-the-shelf **flight-computer integration spec** + wiring diagrams (`.sch`) for the two TVC harnesses (no custom boards) |
| `3D parts/` | Rocket STL/STEP parts + parametric CAD generator (`_generator/`) |
| `Wind Tunnel/` | Fin-test mount + fan collar |
| `Motor Test Stand/` | Load-cell thrust-stand parts (20 kg cell for G-motors) |
| `Simulations/` | RK4 trajectory simulator, `we3_analysis.py`, plots (`plots3/`) |
| `Data/` | Flight, tunnel, motor, erosion data (populated during testing) |
| `Paper/` | Final research paper |

> The 3.0 flight computer is fully off-the-shelf. The legacy custom-board files inside `PCB/`
> (`FCM_KiCAD/`, `generator/`, `WYVERN_E2_*`) are superseded — delete them on your Mac (see
> `PCB/README.md`); the sandbox can't delete on the iCloud volume.

## Key specs

84 mm OD all-PC-FR · liftoff ≈ 1.29–1.39 kg · F booster + **G25W-10A** sustainer (RMS-29/120
casing) · apogee ~1015 ft · 3S 3000 mAh USB-C · Pi 5 + 3× BNO085 + LSM6DSO32 + LIS2MDL + BMP280
+ BME688 + Camera Module 3 + dual 32 GB µSD · RRC3+ recovery + 2nd-stage ignition · no waiver,
no L1 cert. Full numbers in `Documentation/WYVERN_E3_*`.
