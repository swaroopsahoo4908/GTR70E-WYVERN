# Documentation

Engineering documentation for the WYVERN-E 3.0 vehicle (PDR-006) — off-the-shelf Raspberry Pi 5
TVC research rocket. *The `WYVERN_E2_*` files are the superseded 2.0 docs (kept until deleted).*

## 3.0 documents

- `WYVERN_E3_Technical_Document.md` — full system technical description (master spec).
- `WYVERN_E3_Power_Mass_Motor.md` — power budget, mass budget, F25W verdict, motor selection.
- `WYVERN_E3_Mathematics.md` — T/W, apogee, stability, recovery, power, servo sizing, no-waiver gates.
- `WYVERN_E3_TVC_Comparison.md` — solenoid vs servo A/B (sizing, metrics, 6-flight matrix).
- `WYVERN_E3_BOM.md` — bill of materials (Pi 5 + sensors + both TVC systems + motors + GSE).
- `WYVERN_E3_Build_and_Launch_Procedures.md` — assembly, arming, test, and launch procedures.
- `WYVERN_E3_GSE_TestEquipment.md` — static stand, TVC thrust-vector balance, Hofferth wind tunnel
  (fan trade study: AC Infinity A8 recommended), and the full 3D-print manifest.
- `WYVERN_E3_BOM.xlsx` — master BOM (vehicle + avionics + harness + tools) + `GSE & Test Equip`
  sheet (wind tunnel + TVC balance) + full Purchase Links. *Canonical for prices/links.*

Simulations and plots: `../Simulations/we3_analysis.py` + `../Simulations/we3_control.py`
(trajectory, stability, TVC A/B, power, dispersion, fin/apogee sweep, control authority, step
response) → `../Simulations/plots3/`; airfoil CFD in `../Simulations/CFD/`.
Flight computer + wiring diagrams: `../PCB/WYVERN_E3_FlightComputer_Spec.md`, `../PCB/wiring/`.
CAD: `../3D parts/` (regenerate via `../3D parts/_generator/gen_rocket.py`).
