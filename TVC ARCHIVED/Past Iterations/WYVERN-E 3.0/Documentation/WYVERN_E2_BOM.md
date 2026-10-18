# WYVERN-E 2.0 — Bill of Materials

### A Skylight Rocketry Venture
##### 84 mm 2-Stage Magnetic-TVC 3D-Printed Research Vehicle
##### Companion to `WYVERN_E2_BOM.xlsx` (live formulas). Prices in USD; component-level costs are estimates where no public single-unit price exists. Electronics costs reconcile to the JLCPCB PCBA package (`PCB/.../WYVERN_E2_B{1,2}_BOM_PCBA.csv`).

## Avionics — Two-Board Stack (Board 1 TVC Actuator + Board 2 Main FC)

| Item | Part No. / Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| RP2350B flight MCU (sole processor) | Raspberry Pi QFN-80 (C42415655) | 1 | 1.20 | 1.20 |
| W25Q32JV QSPI boot flash | Winbond SOIC-8 (C82344) | 1 | 0.45 | 0.45 |
| SD-NAND data recorder (4 GB) | XTX XTSD04G LGA-8 (C558839) | 1 | 5.30 | 5.30 |
| microSD card socket (J7, edge push-pull) | Attend/Hanbo | 1 | 0.90 | 0.90 |
| ICM-42688-P 6-axis IMU | TDK (C1850418) | 1 | 6.50 | 6.50 |
| BME688 gas/T/RH (Main FC) | Bosch (C3664478) | 2 | 3.50 | 7.00 |
| BMP280 barometer (TVC board) | Bosch (C83291) | 1 | 2.00 | 2.00 |
| LIS3MDL magnetometer | ST (C478483) | 1 | 2.20 | 2.20 |
| BNO055 9-DOF (onboard, 1 per board) | Bosch LGA-28 (C93216) | 2 | 7.10 | 14.20 |
| INA219 bus current monitor (1 per board) | TI (C87469) | 2 | 1.80 | 3.60 |
| MAX713ESE+ NiCd fast-charge controller | ADI/Maxim SOIC-16 (narrow SO; *not* EPE/PDIP) | 1 | 4.50 | 4.50 |
| TPS54202 buck (3V3 & 5V, per board) | TI (C191884) | 4 | 0.70 | 2.80 |
| AO3400A N-FETs (3 solenoid + 3 pyro low-side) | AOS SOT-23 (C20917) | 7 | 0.10 | 0.70 |
| NTR4171P reverse-polarity P-FET (±20 V Vgs, 10S NiCd bus) | onsemi SOT-23 (C146715) | 1 | 0.11 | 0.11 |
| MMBT3906 PNP (NiCd charger pass transistor, B2 Q3) | onsemi SOT-23 (C2145) | 1 | 0.05 | 0.05 |
| SS34 freewheel/boost diode | SMA (C8678) | 4 | 0.12 | 0.48 |
| USBLC6 + SMF05C ESD arrays | ST/onsemi (C7519/C558425) | 3 | 0.10 | 0.30 |
| SMBJ16A TVS + PPTC fuse (per board front-end) | (C135050) | 4 | 0.20 | 0.80 |
| Arducam/OV parallel camera module + header | OV-series | 1 | 9.00 | 9.00 |
| USB-C 2.0 receptacle | GCT (C165948) | 1 | 0.60 | 0.60 |
| 12 MHz crystal (10 pF load) | 3225 4-pad (C518157) | 1 | 0.40 | 0.40 |
| 470 µF 25 V bulk cap (B1 C1, B2 C16) | radial | 2 | 0.30 | 0.60 |
| 100 µF 25 V bulk cap (B2 C24) | radial | 1 | 0.35 | 0.35 |
| 2512 shunts (0.01 Ω ×2 + 0.5 Ω ×1) | 1% | 3 | 0.22 | 0.66 |
| RBF pull-pin + headers / screw term / XT30 | assorted | 1 | 5.00 | 5.00 |
| Passives lot (0603 R/C, crystal caps, LED) | assorted | 1 | 4.00 | 4.00 |
| PCB fabrication — Board 1 (2-layer) + Board 2 (4-layer ENIG) | JLCPCB | 1 | 30.00 | 30.00 |
| **Subtotal** | | | | **103.70** |

*Cross-checked 2026-06-20 against the final `WYVERN_E2_B{1,2}_BOM_PCBA.csv` (post-gerber).
Corrections vs. the prior revision: BNO055 is mounted on **both** boards (B1 U1 + B2 U7), not
one — qty corrected 1→2. The radial-cap line was 3× 470 µF, but the final gerber places only
2× 470 µF (B1 C1, B2 C16) plus a separate 1× 100 µF (B2 C24) — split into two lines. The 2512
shunt count is 3 (0.01 Ω ×2 + 0.5 Ω ×1 across both boards), not 5. Added the MMBT3906 NiCd
charger pass transistor (B2 Q3), which was present in the final BOM but missing from the prior
revision. All other quantities (TPS54202 ×4, AO3400A ×7, SS34 ×4, SMBJ16A+PPTC ×4,
USBLC6+SMF05C ×3, INA219 ×2) were verified correct against the gerber BOM and left unchanged.*

## External Modules

| Item | Part No. / Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| BNO055 9-DOF breakout (gimbal-mounted) | [Adafruit 2472](https://www.adafruit.com/product/2472) | 1 | 34.95 | 34.95 |
| Piezo vibration sensor | film, analog → ADC | 1 | 1.50 | 1.50 |
| **Subtotal** | | | | **36.45** |

*(No external RRC3+ altimeter — dual-deploy and 2nd-stage ignition are handled onboard by the RP2350B pyro channels with hardware continuity + the RBF arm-gate. The camera is now an onboard module on the Main FC.)*

## Actuators & Power

| Item | Part No. / Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| 12 V mini electromagnet (TVC solenoid) | [TOMSHIELE](https://www.amazon.com/dp/B0CTG4X882) | 3 | 9.99 | 29.97 |
| 12 V 1300 mAh NiCd 10S1P pack | [Tenergy](https://power.tenergy.com) | 1 | 24.99 | 24.99 |
| **Subtotal** | | | | **54.96** |

## Propulsion (per flight)

| Item | Part No. / Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| AeroTech G78-4 Mojave Green 29 mm (booster) | [BuyRocketMotors](https://www.buyrocketmotors.com) | 1 | 31.19 | 31.19 |
| AeroTech F25-4 White Lightning 29 mm (sustainer) | [BuyRocketMotors](https://www.buyrocketmotors.com) | 1 | 27.00 | 27.00 |
| First Fire Jr starters (3-pack) | AeroTech | 1 | 9.99 | 9.99 |
| MJG Firewire Initiator (3 ft leads) | MJG | 2 | 3.50 | 7.00 |
| E-Match Mate bulkhead canister (2 pk) | Apogee | 1 | 7.95 | 7.95 |
| FFFFg black powder (per-flight lot) | — | 1 | 1.00 | 1.00 |
| **Subtotal** | | | | **84.13** |

*Motor pricing corrected 2026-06-20 to actual procurement prices (was a stale lower estimate):
G78-4 $31.19, F25-4 $27.00 — both confirmed against the Procurement Log.*

## Recovery

| Item | Part No. / Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| 18″ elliptical chute (booster, 6.0 m/s) | Apogee | 1 | 12.95 | 12.95 |
| 24″ elliptical chute (sustainer main, 7.5 m/s, carries avionics) | Apogee | 1 | 16.95 | 16.95 |
| 1/8″ tubular Kevlar shock cord | [BuyRocketMotors](https://www.buyrocketmotors.com) (6 ft) | 6 | 1.50 | 9.00 |
| **Subtotal** | | | | **38.90** |

## Airframe & Mechanism (filament, by mass)

RQ2 down-selects among PETG-CF / ASA / PLA Basic; the flight airframe ships in the best performer (PETG-CF primary basis below). Fins, TVC, and the test stand all ship in PC-FR — no plain (non-FR) PC is stocked, so PC-FR stands in across every high-heat/impact role.

| Item | Source | Qty (kg) | Unit ($/kg) | Line ($) |
|---|---|---:|---:|---:|
| PETG-CF (primary structure) | Bambu Labs, Procurement Log | 0.450 | 25.99 | 11.70 |
| PLA Basic (RQ2 candidate / fin test articles) | Bambu Labs, Procurement Log | 0.060 | 19.99 | 1.20 |
| ASA Aero (nose / fairings) | Bambu Labs, Procurement Log | 0.080 | 45.99 | 3.68 |
| PC-FR (fins) | Bambu Labs, Procurement Log | 0.070 | 43.99 | 3.08 |
| PC-FR (TVC + test stand) | Bambu Labs, Procurement Log | 0.250 | 43.99 | 11.00 |
| **Subtotal** | | | | **30.65** |

*Updated 2026-06-20 to actual per-kilogram spool prices from the Procurement Log (replacing
the prior $/kg estimates: PETG-CF was guessed at $40/kg, actual $25.99/kg; ASA was guessed at
$30/kg, actual $45.99/kg; PC-FR was guessed at $80/kg, actual $43.99/kg). The fins line was
also swapped from plain PC (never purchased, $50/kg estimate) to PC-FR at the actual $43.99/kg
spool price — no non-FR PC exists on the procurement tracker, so PC-FR now covers every
high-heat/impact role (fins, TVC, test stand) with real pricing instead of a guess.*

## Ground Support Equipment (one-time)

| Item | Source | Qty | Unit ($) | Line ($) |
|---|---|---:|---:|---:|
| Estes Pro Series II Launch Controller | Estes | 1 | 43.99 | 43.99 |
| Estes Pro Series II Launch Rail | Estes | 1 | 179.99 | 179.99 |
| Wishiot 10 kg load cell + HX711 | [Amazon](https://www.amazon.com/dp/B0CRCY863F) | 1 | 11.99 | 11.99 |
| Adafruit Metro M4 | Adafruit | 1 | 27.50 | 27.50 |
| microSD breakout | Adafruit/SparkFun | 1 | 7.50 | 7.50 |
| PLA filament (wind tunnel) | est | 800 | 0.020 | 16.00 |
| **Subtotal** | | | | **286.97** |

*Correction (2026-06-20): the launch controller and launch rail are billed separately by Estes
— the controller alone is $43.99; the rail is its own $179.99 line. The prior single
"rail + controller" line at $79.99 understated this category by $143.99.*

## Procurement Log (Actual Purchases — Skylight Rocketry Budget Tracker)

The engineering BOM above prices a *single flight stack* component-by-component. The table
below is the actual running procurement ledger (CSW Aerospace Budget tracker, reconciled
2026-06-19): bulk filament spools, spares, and one-time tooling bought across the build, not
divided per-unit. Two AeroTech motor line items appeared twice in the source tracker (status
updated from "On Hold" → "Requisitioned" as a new row instead of in place); they are
deduplicated to one line each here. **The PCB line below substitutes the estimated landed
PCBA cost (~$481 for 5 complete two-board stacks, `WYVERN_E2_JLCPCB_Cost_Analysis.md` §4/§6)
for the $600.00 figure in the source tracker**, since $600 was a placeholder/quoted figure
recorded before the JLCPCB cost model was built out.

| Type | Item | Qty | Unit ($) | Line ($) | Status |
|---|---|---:|---:|---:|---|
| 3D Printing | Bambu PETG-CF filament (1 kg) | 2 | 25.99 | 51.98 | Acquired |
| 3D Printing | Bambu PLA Basic filament (1 kg) | 3 | 19.99 | 59.97 | Acquired |
| 3D Printing | Bambu ASA Aero filament w/ spool (1 kg) | 3 | 45.99 | 137.97 | Requisitioned |
| 3D Printing | Bambu PC-FR filament w/ spool (1 kg) | 4 | 43.99 | 175.96 | Requisitioned |
| Rocketry | Estes Pro Series II launch controller | 1 | 43.99 | 43.99 | Aero Budget |
| Rocketry | Estes Pro Series II launch rail *(separate line from controller — added 2026-06-20)* | 1 | 179.99 | 179.99 | Aero Budget |
| Rocketry | AeroTech F25-4 motor (29 mm) | 3 | 27.00 | 81.00 | Requisitioned |
| Rocketry | AeroTech G78-4 motor (29 mm) | 3 | 31.19 | 93.57 | Requisitioned |
| Rocketry | 24″ rip-stop nylon parachute | 6 | 10.25 | 61.50 | Requisitioned |
| Electronics | Jolly Logic Altimeter 2 | 1 | 79.95 | 79.95 | Aero Budget |
| Electronics | 24 AWG flexible silicone wire | 1 | 15.99 | 15.99 | Aero Budget |
| Electronics | Arduino Nano V3 ATmega328P (3-pack) | 1 | 15.99 | 15.99 | Aero Budget |
| Electronics | Adafruit BNO085 9-DOF IMU breakout | 2 | 24.99 | 49.98 | Aero Budget |
| Electronics | STEMMA QT/Qwiic cable, female | 3 | 0.95 | 2.85 | Aero Budget |
| Electronics | STEMMA QT/Qwiic cable, male | 3 | 0.95 | 2.85 | Aero Budget |
| Electronics | Tenergy 12 V 1300 mAh NiCd pack (10S1P) | 4 | 71.99 | 287.96 | Requisitioned |
| Electronics | 50 N 12 V micro lifting solenoid | 3 | 10.99 | 32.97 | Order In-Progress |
| Electronics | Breadboard jumper wire kit | 1 | 14.99 | 14.99 | Order In-Progress |
| Electronics | N52 rare-earth magnets (20 ct) | 1 | 25.00 | 25.00 | Order In-Progress |
| Electronics | IRF520 MOSFET driver (4 ct) | 1 | 6.99 | 6.99 | Order In-Progress |
| Electronics | 1N4007 rectifier diode (125 ct) | 1 | 5.99 | 5.99 | Order In-Progress |
| Electronics | 12 V 2 A power supply adapter | 1 | 11.99 | 11.99 | Order In-Progress |
| Electronics | 5-pack IDC 2×10 20P female connector | 1 | 9.75 | 9.75 | Requisitioned |
| Electronics | **WYVERN-E custom PCBs (2 boards, 5 of each) — *estimated landed PCBA, not the $600 placeholder*** | 1 | **481.00** | **481.00** | Requisitioned (est.) |
| Hand Tools | Kapton high-temp tape | 1 | 9.99 | 9.99 | Aero Budget |
| Hand Tools | J-B Weld twin-tube epoxy | 1 | 21.39 | 21.39 | Order In-Progress |
| Hand Tools | Super Lube PTFE grease | 1 | 10.99 | 10.99 | Order In-Progress |
| **TOTAL (27 deduplicated line items + launch rail, PCB at estimate)** | | | | **1,972.55** | |

*Source tracker total (59 rows incl. the 2 duplicate motor-status rows, $600 PCB placeholder):
$2,086.13. With duplicates removed and the PCB line at the $481 JLCPCB estimate: $1,792.56 —
a $293.57 reduction (duplicate motor rows: $174.57; PCB placeholder→estimate: $119.00). The
Estes launch rail ($179.99) was billed as its own line separate from the launch controller and
is added on top of the source-tracker reconciliation, bringing the corrected total to
**$1,972.55**. (No radio/telemetry module: the rocket carries no downlink — all flight data is logged onboard and retrieved post-flight.)*

## Totals

| Category | Subtotal ($) |
|---|---:|
| Avionics — two-board stack | 103.70 |
| External Modules | 36.45 |
| Actuators & Power | 54.96 |
| Propulsion (per flight) | 84.13 |
| Recovery | 38.90 |
| Airframe & Mechanism (filament) | 30.65 |
| Ground Support Equipment (one-time) | 286.97 |
| **GRAND TOTAL (per-unit engineering BOM)** | **635.76** |
| **Actual procurement to date (dedup. + launch rail, PCB at JLCPCB estimate)** | **1,972.55** |

*The two totals answer different questions: the per-unit engineering BOM (§1–7) prices what
one flight-ready stack costs to build from scratch at unit prices; the procurement log prices
what has actually been bought — bulk filament spools, 4× battery packs, 6× spares motors/chutes,
one-time GSE and tooling — which naturally runs higher since it covers spares and multiple
build cycles, not one stack.*

*Per-flight consumables* (propulsion: motors, igniters, BP) ≈ **$84.13**; the chutes and
shock cord are reusable. The remainder is non-recurring (PCBs, modules, GSE) or reusable
(airframe). The electronics subtotal rose ~$30 vs the
single-board intermediate rev: the architecture split into a 2-layer TVC Actuator + a 4-layer
Main FC, and the onboard camera, SD-NAND recorder, and MAX713 charger were added — while the
external $70 RRC3+ altimeter was eliminated by moving dual-deploy onboard. Estimated unit costs
are used where a single-unit public price is unavailable; update against quotes in the `.xlsx`
(formulas recompute automatically; regenerate it from this table to stay in sync).
