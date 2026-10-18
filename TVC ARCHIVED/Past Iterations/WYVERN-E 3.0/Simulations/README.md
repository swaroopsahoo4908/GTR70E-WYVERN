# Simulations

## WYVERN-E 3.0 OpenRocket files (current)

- `WYVERN_E3_Combined.ork` — two-stage F40W booster + G25W TVC sustainer (the mission).
- `WYVERN_E3_Booster.ork` — F40W booster with the sustainer inert (rod-clearance / staging check).
- `WYVERN_E3_Sustainer_TVC.ork` — G25W sustainer standalone (TVC-demo trajectory).

Open in OpenRocket 23.09 (motors match the built-in AeroTech thrust curves by designation; the
sims are saved `outdated` so OpenRocket recomputes on open). The legacy `WYVERN_E2_*.ork` files
are superseded.

## WYVERN-E 3.0 suite (current — Pi-5, F40W booster + G25W sustainer, oversized fins)

- `we3_power_mass.py` — power & mass budget for the 3.0 config.
- `we3_analysis.py` → `plots3/` — `01_flight_path`, `02_stability`, `03_tvc_comparison`,
  `04_power_budget`, `05_dispersion` + `results_summary.json` (apogee 1015 ft, staging 42 ft,
  v_max 58 m/s, liftoff 1289 g, TVC burn 4.7 s, margin 1.9–2.3 cal).
- `we3_control.py` → `plots3/` — `06_fin_apogee_sweep` (oversized fins cap apogee ≤1100 ft),
  `07_control_authority` (TVC restoring moment vs aero disturbance over the burn — positive
  margin throughout, min ≈5.7 mN·m), `08_tvc_step_response` (solenoid bang-bang vs servo).
- `CFD/run_airfoil_cfd.py` — RQ1 airfoil polars (NACA0006/0012/double-wedge/flat-plate),
  validated to thin-airfoil theory.

Run: `python3 we3_analysis.py && python3 we3_control.py && (cd CFD && python3 run_airfoil_cfd.py)`.

---

## Legacy 2.0 files (below) — superseded

Flight simulations for the two-stage 84 mm vehicle.

- `WYVERN_E2_Combined.ork` — 2-stage G78 → F25 (the mission), fins on the sustainer (PDR-005).
- `WYVERN_E2_Booster.ork` — G78 only (full stack, sustainer inert).
- `WYVERN_E2_Sustainer_TVC.ork` — F25 only (stage-2 standalone).
- `run_sims.py` — reproducible RK4 point-mass simulator (this report's numbers).
- `we2_traj.py` — companion trajectory script.
- `we2_analysis.py` — engineering-analysis suite → `plots/` (drag buildup, stability,
  structural loads, flight path, thermal soak, Monte-Carlo dispersion, sensitivity tornado).
- `WYVERN_E2_Simulation_Results.md` — results summary + plots.
- `WYVERN_E2_sim_plots.png` — altitude & velocity vs time.

Open the `.ork` files in OpenRocket 23.09, or run `python3 run_sims.py` and
`python3 we2_analysis.py`.

## `plots/` — 2.0 analysis figures

Re-derived for the 84 mm 2-stage TVC architecture from the 1.0 (XRIM-117E) analysis set,
using the canonical `run_sims.py` integrator (apogee reconciles to 386 m):

`01_drag_buildup` · `02_aero_stability` (≈1.7 cal) · `03_fea_loads` (min SF ≈17) ·
`04_flight_paths` · `08_thermal` (PC-FR bay peak ≈73 °C) · `09_dispersion` (CEP ≈112 m) ·
`10_sensitivity_tornado` · `results_summary.json`.

> The 1.0 interceptor-specific figures — `05_engagement_paths_3d`, `06_pk_curves`,
> `07_pk_envelope` — are intentionally **not** reproduced: WYVERN-E 2.0 is a research /
> TVC-demonstration vehicle, not a guided interceptor, so probability-of-kill and
> engagement geometry have no 2.0 analogue.

## Subfolders

- `CFD/` — 2D vortex-panel-method airfoil solver for the fin profiles (RQ1), with polars, Cp plots, and a workbook.
- `Flight_Atmospherics/` — ISA-1976 atmosphere model + expanded flight-state dataset derived from the trajectory, with CSVs, a figure, and a workbook.
- `make_spreadsheets.py` — builds the formatted `.xlsx` workbooks from the CSVs (run the CFD + flight scripts first).
