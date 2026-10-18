# Flight Atmospherics — Expanded Trajectory + Atmosphere Dataset

Enriches the base flight of the rocket with a large derived atmospheric/flight dataset,
using the project's combined two-stage trajectory and a full U.S. Standard Atmosphere 1976
model.

## Files
- `atmosphere_isa.py` — U.S. Standard Atmosphere 1976 (0–86 km): T, p, ρ, speed of sound, Sutherland viscosity, kinematic viscosity, and the θ/δ/σ ratios at any altitude.
- `expand_flight.py` — reuses `../run_sims.py`'s exact combined trajectory (so apogee/Mach reconcile with the OpenRocket `.ork` and the Mathematics doc) and derives, at every ascent point: Mach, dynamic pressure, body & fin Reynolds numbers, the full atmospheric state, and the thrust/drag/weight balance.
- `flight_state.csv` — ascent time history, 25 derived columns.
- `isa_reference.csv` — standalone atmosphere table (fine 0–2 km + coarse to 30 km).
- `flight_atmospherics.png` — 6-panel flight + atmosphere figure.
- `WYVERN_E2_atmospherics.xlsx` — formatted workbook (Summary + Flight State + ISA Reference) with formula-driven peak values.

## Run
```
python3 expand_flight.py          # writes both CSVs + the figure
```

## Baseline (reconciles with run_sims / the .ork)
Apogee 386 m, Vmax 68 m/s (Mach 0.20), max-q ~2.85 kPa, max accel 5.1 g, fin Reynolds peaking
~3.4e5 — the same numbers as the combined `.ork` configuration, now resolved against the ISA
atmosphere so the Reynolds-matching for the wind tunnel (RQ4) and the dynamic-pressure
structural loads are explicit.
