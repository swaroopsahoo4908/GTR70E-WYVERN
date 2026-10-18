# TVC ARCHIVED

Everything from the thrust-vector-control revision that the fin-control vehicle does not reuse, moved here on 2026-10-15 with its folder structure intact:

- `Documentation/`: E4 docs, BOMs, FEA, PID reports, presentation deck, `MATH_DERIVATIONS.md` (still holds the ToF-ring math)
- `Flight Computer/`: the Pico 2 W perfboard firmware `wyvern4_tvc`, TVC/solenoid ground rigs, perfboard wiring generators, flowcharts
- `Simulations/`: `we4_*` engines, the `wyvern_datagen` GUI suite, `.ork`, plots; `CFD_outputs_TVC/` keeps the TVC-era polars
- `3D parts/`: E4 airframe, gimbal, MTVC, superseded parts, `gen_rocket4.py`
- `Motor Test Stand/TVC Thrust-Vector Balance/`, `Data/TVC (vector + control)/`
- `Senior Research/`: the TVC proposal (md/docx/pdf)
- `Past Iterations/`: WYVERN-E 1.0 / 3.0, KiCad and EasyEDA PCB history, arc-sim
- `README_TVC.md`, `_All Files.md`

Carried forward (copied or adapted, not moved): the vortex-panel CFD method and section families, `wcad.py`, the Jerrod H tunnel STLs, the static thrust stand, the F15 thrust data, the Pico 2 W (now the ground station), and the firmware's dual-core / seqlock / logging patterns.
