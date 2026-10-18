# GTR70E WYVERN, Documentation

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


Five research questions, each addressed by at least two independent methods: RQ1 magnetic-vs-servo
TVC (two separate physical test stands), RQ2 zoned materials and jetvane blast-shield screen, RQ3
fin aerofoil selection (wind tunnel + CFD), RQ4 wind-tunnel-vs-flight stability calibration, RQ5 PID
gain sensitivity. `WYVERN_E4_Timeline_3Month.md` has the build-to-flight schedule, two launch
weekends around Thanksgiving, all data collected by Dec 1.

- `WYVERN_E4_Mathematics.md`, mass/CG/inertia, T/W, trajectory, TVC, recovery, no-waiver.
- `WYVERN_E4_Stability_FinSizing.md`, Barrowman fin sizing: flown 87 mm fins give +1.14 cal, no ballast.
- `WYVERN_E4_FEA_Structural.md`, first-order structural + thermal margins.
- `WYVERN_E4_Camera_Solution.md`, i3 4K Thumb Action Camera offload solution (OV2640 SPI can't do 720p30).
- `WYVERN_E4_Recovery.md`, F15-4 motor-ejection recovery via two-body-tube separation at the bulkhead joint (finned vehicle, custom PCB in the upper BT).
- `WYVERN_E4_GSE_TestStands.md`, the four ground-test rigs: static-fire stand (calibration, thrust curves, jetvane blast-shield screen), servo TVC stand, magnetic TVC stand, wind tunnel (RQ3/RQ4 aerofoil testing).
- `WYVERN_E4_Timeline_3Month.md`, build-to-flight schedule at 3 man-hrs/week (excludes print time, includes CAD/post-processing), two launch weekends bracketing Thanksgiving, all data by Dec 1.
- `WYVERN_E4_Timeline_14Day.md`, day-by-day procedure-level reference for what happens inside each build session.
- `WYVERN_E4_Build_Guide.md`, print / bench / assembly / ground-test / range procedures with go-no-go cards.
- `WYVERN_E4_BOM.xlsx`, master BOM with purchase links against the live Amazon/Adafruit/Estes/Bambu carts. The custom PCB fab line is retired; the flight computer is a Pico 2 W on a generic perfboard, and power is a discrete 5 V switching UBEC. Line-by-line notes live in the sheet itself.
- `WYVERN_E4_Cart_Gap_Analysis.md`, what the current cart is missing vs. the BOM and the design.
- Flight computer: `../Flight Computer/01_FlightComputer_Spec.md`, `firmware/`, `wiring/`, `flowcharts/`.
- Sims/plots: `../Simulations/we4_sim.py` + `we4_analysis.py` → `../Simulations/plots4/`.
- Datasets: `../Simulations/wyvern_datagen/` (Monte-Carlo + SIL generator, sharded ≤80 MB/file).

Design-decision history and defect records, why specific numbers changed and when, live in
`CONFLICTS.md`, not in this index.
