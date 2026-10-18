# GTR70E WYVERN

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


A single-stage, 70 mm, finned active-TVC sustainer built around a **Raspberry Pi Pico 2 W** on a
20 x 24 (50 x 70 mm) perfboard, mounted as an axial card in the avionics bay, powered by an
**Estes F15-4**.

The vehicle answers five research questions, run across computational simulation, ground-based
instrumented testing, and powered flight:

- **RQ1, actuator class.** Magnetic-solenoid vs. servo thrust-vector control, compared on two
  physically separate, instrumentally identical three-axis load balances. The vehicle flies servo.
- **RQ2, zoned materials.** ASA-Aero, PETG-CF, and PC-FR allocated by section (upper body, lower
  body/fins, TVC assembly), justified by bend-to-fracture and thermal data, plus a blast-shield
  materials screen on the static-fire stand.
- **RQ3, fin aerofoil selection.** Bench wind-tunnel measurement of candidate fin sections,
  cross-checked against a 2D vortex-panel CFD solver.
- **RQ4, wind-tunnel-vs-flight calibration.** Barrowman-predicted stability checked against both
  tunnel measurement and reconstructed flight telemetry.
- **RQ5, control-gain sensitivity.** Closed-loop PID gain sets compared across repeated flights on
  the single-controller avionics architecture.

## Vehicle summary

Single stage, one Pico 2 W as flight computer and real-time controller: dual-core RP2350, one core
dedicated to the 500 Hz TVC loop, no Linux, native hardware PWM. Telemetry is logged to microSD as
the data of record; the onboard CYW43439 radio is used for bench telemetry on the ground stand. The magnetic-vs-servo comparison
runs on the ground (two matched three-axis load balances) rather than in flight, since that gives a
repeatable, directly-measured thrust vector instead of a single noisy flight-to-flight data point.

**Materials.** ASA-Aero forms the upper body that houses avionics (nose, recovery bay tube, FC bay
tube) and the lower body tube (chute/TVC bay); PETG-CF forms the fins and the bulkhead joint; PC-FR
forms the TVC assembly proper (motor mount, gimbal). Zoning follows thermal exposure and structural
role, not a single blanket material.

## Key numbers (see `Simulations/we4_sim.py` → `plots4/`)

| | value |
|---|---|
| Liftoff / dry mass | **720 g / 660 g** (finned 87 mm, no ballast) |
| T/W | 2.04 avg / 3.58 peak |
| Overall length | **672 mm** (Upper BT 198.4 · bulkhead 4 · Lower BT 350 · nose 120) |
| CG / CP / margin | 45.0 cm / 53.3 cm / **+1.14 cal** |
| Gimbal pivot / control arm | 54.8 cm / 9.9 cm from nose |
| Pitch inertia Iyy | 0.0201 kg·m² |
| Pitch authority | 17.2 rad/s² at the ±8° limit |
| Burnout | 3.45 s · 70.1 m · 34.4 m/s |
| Apogee | ~409 ft / 124.6 m @ 6.72 s (RK4+Barrowman) |
| Recovery | F15-4 motor ejection; deploys t≈7.45 s (+0.71 s past apogee) @ ~7.1 m/s; 24″ chute → 4.8 m/s descent |
| TVC | gimbal stays within ±8°; control authority positive throughout the burn |
| FAA class | Class 1, no waiver (720 g < 1500 g, F-class motor) |
| Flight computer | Pico 2 W on a 20×24 (50×70 mm) perfboard, axial card in the Upper BT |
| Sensors | BNO085 ×2 (bay 0x4B, gimbal 0x4A) · BME688 0x76 · BMP388 0x77 · microSD on SPI1 |
| Power | 2S 450 mAh LiPo → PPTC → arming switch → 5 V 3 A switching UBEC |
| Launch window | Nov 7–8 2026 primary, Nov 14–15 contingency; data close-out Dec 1 |

## Repository structure

```
GTR70E WYVERN/
├── README.md ← this file
├── .gitignore
├── Documentation/ ← all engineering docs, BOM, and build readiness
│ ├── README.md ← documentation index
│ ├── WYVERN_E4_BUILD_READINESS.md ← GO/NO-GO reconciliation report
│ ├── WYVERN_E4_Mathematics.md ← mass/CG/inertia, T/W, trajectory, TVC, recovery
│ ├── WYVERN_E4_Stability_FinSizing.md
│ ├── WYVERN_E4_FEA_Structural.md
│ ├── WYVERN_E4_Recovery.md
│ ├── WYVERN_E4_Camera_Solution.md
│ ├── WYVERN_E4_GSE_TestStands.md
│ ├── WYVERN_E4_PID_AUTOTUNE_REPORT.md
│ ├── WYVERN_E4_BOM.xlsx ← master BOM + purchase links
│ ├── WYVERN_E4_Timeline_3Month.md ← build-to-flight schedule
│ ├── WYVERN_E4_Build_Guide.md ← print/bench/assembly/ground-test/range procedures
│ ├── CANONICAL_NUMBERS.md ← single source of truth for every vehicle number
│ ├── FLIGHT_READINESS.md
│ ├── COMPATIBILITY.md
│ └── CONFLICTS.md ← defect log and design-decision record
├── Flight Computer/ ← Pico 2 W spec, firmware, perfboard wiring, GSE test rigs
│ ├── README.md
│ ├── 01_FlightComputer_Spec.md ← architecture, pin map, power, separation
│ ├── firmware/wyvern4_tvc/ ← flight + ground-stand firmware (one image, role flag)
│ └── wiring/ ← perfboard wiring + bay layout diagrams
├── Simulations/ ← Python RK4 suite, OpenRocket, dataset generator
│ ├── we4_flight_reduce.py ← post-flight SD log → RQ3/RQ4 results (--selftest first)
│ ├── README.md
│ └── wyvern_datagen/ ← Monte Carlo atmospheric dataset generator + GUI
│ └── README.md
├── 3D parts/ ← airframe + gimbal STL/STEP
├── Motor Test Stand/ ← static thrust stand + 3-axis TVC balances
├── Wind Tunnel/ ← bench aerofoil rig
├── Senior Research/ ← standalone research proposal (MD / DOCX / PDF)
├── Data/ ← flight and motor data (populated during testing)
└── Paper/ ← final research paper
```

## Ground test program

Four purpose-built stands: a static-fire stand (thrust-curve calibration, engine-bay thermal
verification, and the RQ2 jetvane blast-shield screen), a servo TVC stand, a physically separate
magnetic TVC stand, and a bench wind tunnel for RQ3/RQ4 aerofoil work. See
`Documentation/WYVERN_E4_GSE_TestStands.md` for the full build-out and instrumentation. The ground
rigs' load-cell DAQ runs on separate off-the-shelf boards. The TVC balance, however, reuses the
*same* Pico 2 W avionics stack and the *same* firmware image as the flight vehicle, built with
`-DWYVERN_GROUND_TEST=1` so the bay IMU is not required and launch-detect and recovery compile
out — the gimbal IMU is the sensor the stand exists to measure.

Design and decision history, including why specific numbers or scope changed, lives in
`Documentation/CONFLICTS.md` rather than here.

## References

Raspberry Pi Ltd. (2024). *RP2350 datasheet*. https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

Estes Industries. (n.d.). *F15-4 engines* [Product specification]. Retrieved August 12, 2026, from https://estesrockets.com/products/f15-4-engines
