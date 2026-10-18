# CFD — Fin Airfoil Aerodynamics (RQ1)

A 2D vortex-panel-method solver for the four candidate fin cross-sections, in pure
Python/numpy. Supports the wind-tunnel campaign (RQ1) by predicting the lift curve
and surface pressure of each profile through the 0.5° deflection sweep, giving a
computational baseline to validate the tunnel measurements against.

## Files
- `airfoil_profiles.py` — geometry for NACA 0006, NACA 0012, double-wedge, flat-plate (unit chord, cosine-spaced, clockwise loops).
- `run_airfoil_cfd.py` — constant-strength vortex-panel method (Kuethe & Chow) → Cl and Cp; flat-plate skin-friction model for a viscous Cd estimate; AoA/deflection sweep in 0.5° steps at tunnel (Re 2e5) and flight (Re 3.4e5) Reynolds numbers.
- `airfoil_polars.csv` — Cl, Cd, L/D vs deflection for every profile.
- `cl_alpha.png`, `cp_distribution.png` — lift curves and Cp distributions.
- `WYVERN_E2_airfoil_polars.xlsx` — formatted workbook (Summary + Polars), formula-driven Cl-slope / Cl@5° / best-L/D.

## Run
```
python3 run_airfoil_cfd.py        # prints a validation line, writes CSV + plots
```

## Validation & caveats
The method is validated against thin-airfoil theory: NACA0012 returns dCl/dα ≈ 0.120/deg
(≈110% of the 2π/rad ideal — the expected inviscid thickness over-prediction); the thin
flat-plate returns ≈0.112/deg. The solver is *inviscid*: it captures Cl and the pressure
distribution but not viscous separation, stall, or pressure drag. Real Cd and stall onset
come from the RQ1/RQ2 wind tunnel — which is exactly what this code is built to be checked
against. For full-vehicle 3D RANS, the program uses SimFlow/OpenFOAM separately.
