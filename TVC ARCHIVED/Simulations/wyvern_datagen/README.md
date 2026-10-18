# GTR70E WYVERN, Simulation & Dataset Suite

Start from loaded:
cd ~/"Library/Mobile Documents/iCloud~md~obsidian/Documents/Skylight/Projects/Skylight/WYVERN/GTR70E WYVERN/Simulations/wyvern_datagen"
/opt/homebrew/bin/python3 run_gui.py

One Python GUI + engine that generates **millions of atmospheric datapoints** for the GTR70E WYVERN
rocket, and links the project's existing single-run simulation engines under the same window.

This replaces the old Java/OpenRocket `arc-sim` tool (which was wired to the CSW project, its
`CSWARCMOD*.ork` files have been removed). The physics here matches the project's canonical engine
`../we4_flightsim.py` (nominal apogee **98.9 m / 324 ft @ ~6.27 s**), so datasets are consistent
with the rest of the WYVERN sim suite.

## Quick start

Use **one** interpreter that has both a modern Tk (for the GUI) and the packages. On macOS that's
Homebrew's Python: `/opt/homebrew/bin/python3` (Apple Silicon) or `/usr/local/bin/python3` (Intel).

**One-time setup** (installs the toolkit + packages into that interpreter):

```bash
brew install python-tk # modern Tk 8.6 for the GUI
/opt/homebrew/bin/python3 -m pip install numpy pyarrow matplotlib # (add --break-system-packages if pip refuses)
```

**Open the GUI**, pick either:

```bash
# a) double-click launch.command in Finder (auto-picks a working Python), OR
# b) from a terminal:
cd ~/"Library/Mobile Documents/iCloud~md~obsidian/Documents/Skylight/Projects/WYVERN/GTR70E WYVERN/Simulations/wyvern_datagen"
/opt/homebrew/bin/python3 run_gui.py
```

If a dependency is missing, `run_gui.py` prints the exact install command for *that* interpreter
instead of a traceback. Sanity check anytime:

```bash
/opt/homebrew/bin/python3 -c "import numpy, pyarrow, matplotlib, tkinter; print('deps OK')"
```

**Headless / scriptable** (recommended for multi-million-row runs), run from this folder. Each run
writes a new `*_YYYYMMDD_HHMMSS` file; add `--no-timestamp` to overwrite a fixed name instead:

```bash
/opt/homebrew/bin/python3 datagen.py outcomes --n 2000000 --out datasets/outcomes.parquet
/opt/homebrew/bin/python3 datagen.py timeseries --flights 50000 --stride 10 --out datasets/ts.parquet
/opt/homebrew/bin/python3 datagen.py tvc --n 1000000 --out datasets/tvc.parquet
/opt/homebrew/bin/python3 datagen.py combined --flights 25000 --out datasets/combined.parquet # closed-loop SIL batch
```

## GUI at a glance

Opens maximized (fill screen); **F11** toggles true fullscreen, **Esc** exits it.

- **Atmospheric Datasets**, choose type, N flights, seed, format; one-click envelope **presets**
  (Calm / Typical field / High wind / Hot & high / Full envelope); Preview count + real ETA;
  progress bar, live log, working Cancel; "Quick nominal flight ▶" plots a single reference flight.
  Every run writes a **new timestamped file** (arc-sim style, never overwrites); untick "New file
  each run" to reuse a fixed name.
- **Plots & Analysis**, load any dataset (or "Load last generated") and build **histograms,
  scatter, density hexbin, altitude-trajectory overlays, and correlation heatmaps** in an embedded
  matplotlib canvas with the standard zoom/pan/**save-PNG** toolbar; per-column statistics panel.
  Large sets are auto-subsampled so plotting stays responsive.
- **Data Viewer**, a tabular **Parquet/CSV viewer** with a **dark grid** (white text on a dark
  background, white row/column outlines, rows drawn a touch thicker). Full column headers, numeric
  formatting + right-alignment, horizontal & vertical scrolling, **click-a-header-to-sort**, and a
  start-row / row-count window (**default 10,000 rows**). The grid is drawn on a virtualized canvas,
  so only on-screen rows render and it stays fast even on multi-million-row files. Also opens the
  last generated file.
- **PID Tuner**, live closed-loop TVC tuning: drag **Kp / Ki / Kd** (plus gimbal limit, wind,
  turbulence, and disturbance type) and watch the pitch θ(t) and gimbal δ(t) response redraw in
  real time, with tuning metrics (peak overshoot, settle time, steady-state error, RMS gimbal,
  saturation %) and the firmware-default gains overlaid for comparison. **Auto-tune** runs a robust
  multi-wind gain search (~10 s) and "Apply best" loads it; "Reset to firmware" restores Kp0.10/Ki0.40/Kd0.18.
- **Flight Computer SIL**, a software-in-the-loop *digital twin*: runs the FC's own processes
  (state machine BOOT→…→LANDED, 500 Hz PID on **noisy** simulated sensors, motor-ejection recovery)
  against a simulated flight with altitude-varying wind, and streams the **simulated Wi-Fi telemetry**
  (`HB:` heartbeat lines) to a live console while plotting altitude/pitch/gimbal. Shows true-vs-baro
  altitude, boost-phase control, and the apogee nose-over.
- **Super Combined**, batch-runs the full closed-loop SIL over **N random-condition flights**
  (default **25,000**), building a **live scatter** (wind vs boost-phase peak pitch, coloured by
  gimbal saturation) as flights complete, with progress + ETA + Cancel. Saves **two** timestamped
  files: the full time-series `*_log` and a compact per-flight `*_flights` summary. ~14 flights/s
  (25,000 ≈ 30 min); Cancel keeps whatever was written.
- **Static Motor Tester**, pick a motor (Estes C6/D12/E12/E16/F15) and see its thrust curve plus the
  **axial load-cell trace** the static stand would log (DAQ rate + sensor noise), with total impulse,
  avg/peak thrust, burn time, and a load-cell headroom/under-range check.
- **Jetvane Suitability**, **RETIRED 2026-08.** Jetvane TVC was dropped from the program; the
  tab still opens for reference but its output is not used by any research question and no jetvane
  hardware is built or fired. Kept only so the earlier trade study stays reproducible.

- **Ground TVC + PID**, the **3-axis thrust-vector balance** reading (Fz axial, Fx/Fy lateral) while
  the firmware PID gimbals the nozzle through a bench maneuver (step / sweep / PID disturbance-reject),
  including servo lag; shows commanded-vs-measured δ, the resolved vector, saturation, and cell headroom.
- **Project Engines**, run the existing `we4_*.py` engines; each run archives its plots to a fresh
  `plots*_<timestamp>/` folder (set via the `WYVERN_RUN_TAG` env var) so nothing is overwritten.
- **About**, canonical specs + the headless CLI reference.

## Dataset types

| Type | Rows | Columns | Use |
|---|---|---|---|
| `outcomes` | 1 per flight | sampled atmosphere → `apogee_m/ft`, `apogee_t`, `max_speed_ms`, `max_mach`, `max_q_pa`, `max_accel_g`, `burnout_*`, `deploy_*`, `descent_rate_ms`, `flight_time_s`, `landing_x_m`, `drift_from_pad_m` | dispersion / robustness statistics |
| `timeseries` | ~149 per flight (dt 5 ms, stride 10) | `flight_id, t, x, z, vx, vz, accel_g, mach, q` + per-row conditions | ML training / trajectory learning |
| `tvc` | 1 per flight | `peak_pitch_err_deg`, `rms_gimbal_deg`, `gimbal_saturation_pct`, `settle_time_s` + conditions | closed-loop TVC control performance |
| `flightlog` | SIL time-series | `state_id, alt, vz, pitch, gimbal, baro, batt` + conditions | closed-loop digital-twin logs (state machine + sensor noise) |
| `combined` | log + per-flight summary | full SIL log **plus** `apogee, peak_pitch_boost, rms_gimbal, gimbal_sat, deployed` per flight | the Super Combined batch (default 25,000 flights) |

Every flight samples an atmosphere/launch condition uniformly over a tunable envelope (wind speed &
bearing, turbulence, surface temperature, pressure, launch-rod tilt, field elevation). The GUI
exposes every envelope bound; the defaults cover a realistic small-field F-class envelope.

## Physics (vectorized)

`core.py` integrates **N flights in lock-step as NumPy arrays**, that vectorization is what makes
million-flight datasets tractable in pure Python. It reuses the canonical WYVERN model:

- F15-4 thrust curve (49.6 N·s / 3.45 s), linear propellant burn, `m_lift 792 g → m_dry 690 g`.
- Barrowman drag build-up (Cd ≈ 0.54), ISA atmosphere with sampled temperature/pressure perturbation.
- 2-D point mass with wind drift; analytic 24″-parachute descent (terminal ≈ 6 m/s) after the
  F15-4 ejection at t = 7.45 s.
- **TVC**: reduced-order closed-loop pitch plant (aerodynamic angle-of-attack spring + damping +
  the firmware PID `Kp0.10/Ki0.40/Kd0.18`, ±8° gimbal, 500 Hz, anti-windup), held straight on the
  1 m rail then released. Peak pitch error scales with wind (≈0° calm → ≈19° at 10 m/s), consistent
  with the documented low-speed weathercocking of this low-T/W vehicle.

Nominal check: `python3 core.py` → `98.9 m / 324 ft @ 6.27 s` (matches `we4_flightsim.py`).

## Throughput & scale

Measured on this dev machine (single core, NumPy):

| Dataset | Rate | 1 M rows | 10 M rows |
|---|---|---|---|
| outcomes (dt 5 ms) | ~8,600 flights/s | ~2 min | ~20 min |
| tvc (dt 2 ms, 500 Hz) | ~5,000 flights/s | ~3.5 min | ~35 min |
| timeseries (dt 5 ms) | ~90,000 rows/s | ~11 s | ~2 min |

Data is **streamed to disk in chunks**, so memory stays flat no matter how large the dataset. There
is no practical row cap, pick the row count you want and let it run.

## Output format

**Parquet** by default (compact, columnar, snappy-compressed, ideal for the huge time-series set and
loads directly into pandas/DuckDB/Polars). Falls back to **gzip-CSV** if `pyarrow` isn't installed.
Note: `.xlsx` is *not* used, it caps at ~1.05 M rows, well below "millions."

```python
import pyarrow.parquet as pq
df = pq.read_table("datasets/outcomes.parquet").to_pandas()
```

## Files

```
wyvern_datagen/
  core.py vectorized flight physics (outcomes / trace / TVC)
  datagen.py chunked Monte-Carlo writers + CLI
  analysis.py dataset loading + plot builders (histogram/scatter/hexbin/trajectory/corr)
  fc_sil.py flight-computer software-in-the-loop digital twin (state machine + sensors + telemetry)
  pid_autotune.py robust multi-wind PID gain search
  gui.py Tkinter GUI, 8 tabs: Atmospheric Datasets, Plots & Analysis, Data Viewer, PID Tuner, Flight Computer SIL, Super Combined, Project Engines, About
  run_gui.py GUI launcher (preflight dependency check)
  launch.command double-click launcher (Finder), auto-selects a working Python
  README.md this file
  datasets/ generated output (sample *_test.parquet included)
```

## Dependencies

`numpy` (required), `matplotlib` (GUI plots), `pyarrow` (optional, for Parquet), `tkinter` (GUI only,
ships with a Tk-enabled Python). No Java, no Maven, no OpenRocket.
