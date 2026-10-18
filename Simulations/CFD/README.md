# CFD

- `airfoil_profiles.py`: the four control-fin sections, defined the way they print: flat plate 2.4 mm with round LE/TE, double wedge 6 %, NACA 0006, NACA 0012, each with a 1.0 mm minimum thickness. Exposes unit-chord loops for the solver and dimensional loops for the CAD loft.
- `run_airfoil_cfd.py`: constant-strength vortex-panel method (Kuethe & Chow), validated against thin-airfoil theory (NACA 0012 slope 109 % of 2π, the expected thickness effect). Writes `airfoil_polars.csv`, `cl_alpha.png`, `cp_distribution.png`.
- `vlm.py`: horseshoe vortex lattice for the all-moving triangular fin, mirrored across its root (body wall as a reflection plane). Converged to < 0.5 % at 8 x 24 panels.

- `simscale/`: RANS package for SimScale's free plan. `gen_simscale.py` writes ten ready-to-upload flow regions (seven Phase A tunnel cases, three full-rocket cases), the solid bodies and per-part STLs, `predictions.csv` (what the models above predict for each case) and `manifest.json`. `SIMSCALE_SETUP.md` is the click-by-click set-up: k-ω SST, boundary conditions, mesh sizes, force groups and how to compare.

The tunnel data is the referee for anything RANS cannot settle (transitional Reynolds number, leading-edge vortex shedding).
