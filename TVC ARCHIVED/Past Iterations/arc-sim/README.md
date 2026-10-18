# arc-sim: OpenRocket engines for ARC, with a desktop GUI

## Quick start: the GUI

Skip the CLI entirely if you'd rather click buttons than remember positional args:

```bash
cd ~/"Library/Mobile Documents/iCloud~md~obsidian/Documents/Skylight/Projects/CSW Aerospace/CSWARC'27/arc-sim"
mvn clean package
java -jar target/arc-sim-1.0.0.jar
```

That launches a desktop window with six engine tabs plus a seventh **Data Viewer** tab, file-picker
Browse buttons, a "Preview combination count & time estimate" button for the full sweep and batch
generator (so you see the number before committing to a multi-hour run), a live log, and a Cancel
button that actually stops a running job partway through -- including Engine 3's Design Solver,
which previously ignored Cancel entirely -- picking up at the next safe checkpoint and using/saving
whatever partial result it had accumulated so far, rather than just hanging until the run finishes
on its own.

**Engines 1, 2, and 3 each show a live leaderboard table** while running: the top 10 "most
favorable conditions seen so far" (Engine 1 / 2) or "closest simulation to target seen so far"
(Engine 3), re-ranked in place every time a new result beats an entry already on the table, so you
can watch the run converge instead of waiting for it to finish before seeing anything.

**Data Viewer tab**: a built-in, read-only browser for this toolkit's three tabular output
formats -- `.xlsx` (Engine 1, with a sheet selector), `.csv` (Engine 4's manifest), and `.parquet`
(Engine 2). Parquet reading/writing uses this project's own dependency-free `MiniParquet` (see
`MiniParquet.java`) rather than pulling in Apache Parquet's full Hadoop-based stack, so there's no
extra dependency weight for it. Point it at any file with Browse, click Open; there's a row cap
(default 20,000, adjustable) so opening a multi-million-row parquet file doesn't try to load it
all into the table at once.

**Every engine names its own output file/folder automatically** -- `<rocketName>_<simType>_<timestamp>`
-- so you never have to type a filename, and re-running an engine (even on the same rocket, even
in the same second) never overwrites a previous result; the output fields in the GUI now just
pick a destination *folder* (optional -- overrides the default below).

**Default output folders** -- leave the GUI's "Output folder" field blank and each engine writes
into its own fixed-name folder, created as a SIBLING of whichever `.ork` file you're running
against (not a fixed project-root location), so outputs stay organized next to the design they
came from no matter where that file lives:

| Engine | Default folder |
|---|---|
| Engine 1 (Monte Carlo sweep) | `Monte Carlo` |
| Engine 2 (full factorial sweep) | `Full Factorial` |
| Engine 3 (design solver) | `OpenRocket Solves` |
| Engine 4 (batch `.ork` generator) | `OpenRocket Solves` (each batch gets its own timestamped subfolder inside it) |
| Engine 5 (geometry export) | `CAD Files` |
| Engine 6 (weather-driven design) | `Engine 6` |

Typing an explicit path into the "Output folder" field bypasses the default entirely.

The CLI still works the same way -- positional args, no filenames to make up:

```bash
java -cp target/arc-sim-1.0.0.jar com.arc.sim.Main sweep CSWARCMOD1D.ork MDRA_SOD_FARM 5000
```

(Output paths in the CLI are all now optional trailing `[outputDir]` args -- omit them to write
next to the input `.ork`, same as the GUI.)

(`java -jar ...` launches the GUI; `java -cp ... com.arc.sim.Main ...` uses the CLI. Both read the
same code, just different entry points.)

Everything below describes what each engine does; the GUI's fields map 1:1 to the CLI args
described here.

---

Three independent engines:

1. **Engine 1 — `EnvironmentSweep`**: holds your rocket design EXACTLY as uploaded (no changes)
   and Monte Carlo samples across the full wind/turbulence/temp/pressure envelope, writing every
   run + a summary/sensitivity sheet to `.xlsx`.
2. **Engine 3 — `DesignSolver`**: holds ONE atmosphere/wind condition fixed (you specify it) plus
   your target apogee and flight-time window, and solves for **ballast mass + fin height + fin
   sweep** to hit those targets.
3. **Engine 4 — `OrkBatchGenerator`**: takes ONE base `.ork` and a grid of ballast / fin height /
   fin sweep / parachute center-hole values, and writes out **every combination as its own `.ork`
   file** — all landing together in one auto-named subfolder next to the base file, alongside a
   **`manifest.csv`** linking every generated filename to its parameter values. Optionally (via
   the grid config's `simCheck.*` properties) it will ALSO simulate each variant under one fixed
   atmosphere and check it against a target apogee/flight-time window — the same target+atmosphere
   shape Engine 3 takes — so each saved `.ork` carries real simulated flight data and the manifest
   records apogee/flight-time/meets-target per variant.

Engine 2's full-factorial output is `.parquet` (not `.xlsx`) since it routinely produces far more
rows than a spreadsheet can hold; Engine 4's manifest is `.csv`. All three tabular formats open in
this toolkit's own **Data Viewer** GUI tab.

The full factorial grid originally described (every combination of all 7 environmental variables
at fine increments) is ~1.33 trillion points — not runnable on any machine. Engine 1 covers the
same envelope with a statistically meaningful random sample instead.

## Your current file (CSWARCMOD1D.ork), as of this version

- Mass component is now explicitly named **"Ballast"**, 128 g, in the aft body tube — matches
  what you described (100+ g in the lowest section).
- Parachute is the **"Parachute, 18 in., nylon, 6 lines, PN 002261"**, 0.4572 m diameter — Engine
  3 holds this fixed and does not resize it.
- The saved Simulation 1 in the file already shows **apogee 242.98 m, flight time 41.586 s** —
  apogee is basically dead-on your 243 m target already; flight time is running long by
  1.6–4.6 s against your 37–40 s window. That gap is exactly what Engine 3 is for.
- Component lookup is still **structural** (lowest body tube = ballast, first fin set = fins,
  first parachute = recovery), not purely by name, so this keeps working if you rename things
  again later. See `RocketComponents.java`.

## 1. Prerequisites

- Java 17+, Maven
- Your `.ork` file (bundled in this zip)

## 2. Build

```bash
cd arc-sim
mvn clean package
```

Produces `target/arc-sim-1.0.0.jar`.

## 3. *** Verify units before trusting any output ***

`SimRunner.java` converts wind direction to radians, temperature to Kelvin, and pressure to
Pascals before handing them to OpenRocket's `SimulationOptions`. This matches the documented
`info.openrocket.core` API, but core APIs drift between versions. Before trusting real numbers:

1. Run one simulation through this tool with a known condition.
2. Set the same condition manually in the OpenRocket GUI's Simulation Options dialog.
3. Confirm apogee/flight time match within numerical noise (<1%).

## 4. Engine 1 — environment sweep

```bash
java -jar target/arc-sim-1.0.0.jar sweep CSWARCMOD1D.ork MDRA_SOD_FARM 5000
```

Args: `.ork` file (used as-is, unmodified), site, number of Monte Carlo samples, optional output
folder (defaults to a `Monte Carlo` folder next to the `.ork` file). The filename itself is generated automatically
as `CSWARCMOD1D_montecarlo_<timestamp>.xlsx` — every run gets its own file, so nothing is ever
overwritten even if you kick off two runs back to back.
Output `.xlsx` has:
- **Runs** sheet: every sampled condition + apogee/flight-time result
- **Summary** sheet: success rate (% of samples in your 243 m / 37.5-39.5 s window) and Pearson
  correlation of each environmental variable against apogee and flight time

Distributions are uniform across your full stated ranges (0-20 m/s wind, -5-35°C, 980-1020 mbar,
etc.) — swap in a fitted Gaussian/Rayleigh if you have real historical weather data for your
launch date, which will usually give a more realistic (and likely higher) success rate than this
worst-case uniform assumption.

## 4b. Engine 2 — TRUE full-factorial sweep (every combination, no sampling)

```bash
java -jar target/arc-sim-1.0.0.jar fullsweep CSWARCMOD1D.ork sweep_grid.properties
```

Same auto-naming as Engine 1 — output filename is generated as
`CSWARCMOD1D_fullfactorial_<timestamp>.parquet`, written to an optional trailing `[outputDir]` arg
(default: a `Full Factorial` folder next to the `.ork` file). A companion `..._summary.csv` (success rate +
correlations, the old xlsx "Summary" sheet) is written right alongside it.

This runs **every single combination** in the grid defined by `sweep_grid.properties` — no
sampling, nothing skipped. Your originally-requested increments (0.5 m/s wind, 0.1 m/s std dev,
1% turbulence, 0.5 deg direction, 1 deg C, 1 mbar pressure) produce **~388 billion**
combinations — ~369 years on one CPU core, ~23 years even on 16 cores. Not runnable at any
increment that fine, corrected pressure range or not.

`sweep_grid.properties` (bundled, edit freely) defaults to coarser increments that total ~1.63
million combinations — the tool prints the exact count and a rough time estimate **before it
starts**, so check that output before committing to a multi-hour run. If the total exceeds the
`maxCombosSafety` cap in the properties file (default 5,000,000), it refuses to run and tells you
so, rather than silently kicking off a job that'll finish next decade — pass `--force` to
override, or just coarsen the increments.

It's multithreaded (`threads=` in the properties file, defaults to your CPU's core count) — each
thread loads its own copy of the `.ork` so there's no shared-state risk between them. Output is
**Parquet, not xlsx**: a true full-factorial run routinely produces tens of millions of rows,
past Excel's ~1,048,576-rows-per-sheet ceiling the old xlsx writer had to chunk around. Every row
(one per combination) lands in a single `.parquet` file, written via this project's own
dependency-free `MiniParquet` writer (no Hadoop/parquet-mr dependency needed — see
`MiniParquet.java`), streamed in bounded row groups so memory stays flat no matter how many
combinations run. Open it in the GUI's **Data Viewer** tab, or in pandas/DuckDB/any other
Parquet-aware tool. The success-rate + correlation summary is the companion `_summary.csv`.

**Tuning tip:** time a small run first (e.g. set every `.step` larger to get ~10,000 combos,
confirm it finishes in a minute or two) to calibrate the real per-simulation time on your machine
before dialing in a bigger grid for your actual time budget.

## 5. Engine 3 — solve ballast + fin height + fin sweep

```bash
java -jar target/arc-sim-1.0.0.jar design CSWARCMOD1D.ork 243.0 37.5 39.5 MDRA_SOD_FARM \
    3.8 0.6 13.4 270 7.06 999.76
```

Args, in order: `.ork` file, target apogee (m), target flight-time min/max (s), site, wind avg
(m/s), wind std dev (m/s), turbulence intensity (%), wind direction (deg), temperature (°C),
pressure (mbar). The example values above match the atmosphere from your original Simulation 2
(3.8 m/s wind, 13.4% turbulence, ~7°C, ~1000 mbar).

**How it splits the 3 unknowns across 2 targets** (see full explanation in `DesignSolver.java`):
- **Ballast mass** is the primary lever for **total flight time** — heavier rocket descends
  faster under the same fixed parachute.
- **Fin height** is the primary lever for **apogee** — bigger fins add drag during ascent,
  lowering apogee. Its effect on total flight time is small since descent time is dominated by
  the parachute.
- **Fin sweep** is a weak last-resort trim, only touched if apogee still has residual error after
  ballast/fin-height converge. Sweep mostly affects **stability margin** (CP location), not
  apogee/time — after this solver runs, open the saved file in the OpenRocket GUI and check the
  stability margin (calibers) is still in a safe range (typically 1-2 cal) before you commit to
  flying with a changed sweep.

Output: prints the solved ballast/fin height/fin sweep and saves
`<orkName>_solved_<timestamp>.ork` into an `OpenRocket Solves` folder next to your input file (GUI:
override via the "Output folder" field) — never overwrites a previous solve, so
you can re-run with different targets/bounds and keep every attempt. If it can't converge both
targets, the tool tells you which bound (max ballast, max fin height) it hit — at that point your
options are a different motor (you already have F15, F25W, F26FJ, F20W/L, and a second F15 delay
variant configured) or accepting a compromise on one target.

## 5b. Engine 4 — batch `.ork` design-variant generator

```bash
java -jar target/arc-sim-1.0.0.jar batch CSWARCMOD1D.ork batch_grid.properties
```

Takes ONE base `.ork` and writes out **every combination** of the design-parameter grid in
`batch_grid.properties` as its own standalone `.ork` file. The same four physical knobs Engine 3
solves for are available to sweep: ballast mass (kg), fin height (m), fin sweep (m), and
parachute center spill-hole radius (inches). Leave an axis's `.min`/`.max`/`.step` trio out of the
config entirely to leave that parameter untouched (exactly as loaded from the base file) in every
generated file — so you can sweep just ballast, or all four at once. The bundled config sweeps
ballast + fin height + hole radius (a small ±1 in tolerance band) by default, leaving fin sweep
untouched, matching the current design-of-experiments plan.

All generated files land together in one new timestamped subfolder created inside an
`OpenRocket Solves` folder next to the base `.ork` (or inside an optional trailing
`[outputParentDir]` arg, which overrides that default): `CSWARCMOD1D_batch_<timestamp>/`. Each file inside
is individually named with its varied parameter value(s) baked in, e.g.
`CSWARCMOD1D_ballast150g_finH80mm.ork`, so the batch is self-describing and nothing — inside this
batch, a previous batch, or any other engine's output — can ever collide or get overwritten.

**`manifest.csv`** also lands in that subfolder, with one row per generated file linking its exact
filename (`ork_filename` column) to the parameter value(s) that produced it — open it in the GUI's
Data Viewer tab, or any spreadsheet, to browse or filter the whole batch without opening 100s of
individual `.ork` files.

**Optional: simulate + check against a target, same idea as Engine 1 but per design variant.**
By default no simulation runs here — pure design-variant generation. Fill in the grid config's
`simCheck.*` properties (all 10, or none — see the commented-out block in `batch_grid.properties`)
to also simulate every variant under one fixed atmosphere and check it against a target
apogee/flight-time window, the same target+atmosphere shape Engine 3 takes. When enabled:
- Each saved `.ork`'s own Simulation 1 gets the real simulated flight data cached into it — open
  it in the OpenRocket GUI and the apogee/flight-time are already there, rather than a design
  nobody's actually checked yet.
- `manifest.csv` gains `apogee_m`, `flight_time_s`, `meets_apogee`, `meets_time`, and `meets_both`
  columns, so sorting/filtering the manifest tells you which design variants actually hit the
  target without opening anything else.

Like Engine 2, it prints the total file count up front and refuses to run past a
`maxFilesSafety` cap (default 5,000) unless you pass `--force` — a typo in the grid step can't
silently ask for a million files.

Useful for: handing a batch of concrete design candidates to teammates, loading a handful
side-by-side in the OpenRocket GUI to eyeball, checking (via `simCheck.*`) which design variants
meet your target before you even open OpenRocket, or feeding each variant into Engine 1/2
separately for a fuller design-space sweep than Engine 3's single-atmosphere solve.

## 5c. Engine 5 — geometry export (`.ork` -> STL/OBJ)

GUI-only (no CLI command). Load any `.ork` in the "Engine 5: Geometry Export" tab, pick STL and/or
OBJ, and export a triangle mesh built from `RocketGeometryExtractor`'s nose-cone/body-tube/
transition radii-by-station plus each trapezoidal fin set's planform (root chord/tip chord/sweep/
height/fin count/base rotation). Written by this project's own dependency-free `MeshExporter` —
no CAD/mesh library dependency needed.

**This is a basic outer-mold-line converter, not CAD-fidelity geometry**: body sections are a
solid-of-revolution surface only (no wall thickness, no internal components, no fillets); fins are
flat extruded trapezoidal panels (a few mm of constant thickness, purely to make them a closed
solid) rather than real airfoil sections; multi-body stacking assumes serial nose-to-tail stacking
with no gaps (same assumption `RocketPreviewPanel` uses), so side-by-side staging (boosters/pods)
isn't rendered. Good for a quick 3D-print or CAD-import sanity check of the outer shape; not a
substitute for real CAD if you need dimensional precision. Output units are **millimeters**
(the de facto STL/CAD convention). Every run gets its own new `<rocketName>_geometry_<timestamp>/`
subfolder (same pattern Engine 4's batch generator uses) inside a `CAD Files` folder next to the
`.ork` file by default (override via the "Output folder" field) — so re-exporting the same rocket
never overwrites a previous run and both files from one export stay grouped together.

## 5d. Engine 6 — weather-driven design (live weather → Engine 3 → CAD → local sweep → margin fins)

GUI-only (no CLI command). Pulls real current conditions from weatherapi.com for whatever launch
site you pick, then chains together in one click: Engine 3's solve against that pulled atmosphere,
a full CAD export of the solved design, a Monte Carlo check of that solved design across a
realistic day-of range of conditions, and four spare fin-only CAD files sized for likely wind-speed
variance around the forecast. All of it -- the solved `.ork`, both CAD exports, the local sweep
`.xlsx`, and all four margin fin CAD pairs -- lands in one `Engine 6` folder next to the `.ork`
file by default; override via the "Output folder" field.

**Weather pull**: fetched once when the tab is built and at most once an hour after that — there's
no way to bypass the cooldown, so this can never hammer the API regardless of how many times you
click Fetch or Run. Wind speed/gust, direction, temperature, and pressure come straight from the
API; wind std dev does NOT (the API only reports a gust, not a variance) and is estimated as
`(gust - avg) / 2.5` — a rough turbulence rule of thumb, pre-filled into an editable field so you
can override it with better local knowledge. Turbulence intensity isn't reported at all and
defaults to 10%, also editable.

**Step 1 — main solve**: identical to running Engine 3 by hand with the pulled wind
average/direction, temperature, and pressure (plus the estimated/overridden std dev and
turbulence) as the fixed atmosphere. Saves `<rocketName>_solved_<timestamp>.ork` exactly like
Engine 3 does, with a live "closest simulation to target" leaderboard.

**Step 2 — main CAD**: exports the solved design as `<rocketName>_weatherdesign_<timestamp>.stl`
/ `.obj`, same converter as Engine 5.

**Step 3 — local-conditions sweep**: runs the SAME solved design (ballast/fin height/hole radius
unchanged) across a narrow envelope centered on the pulled reading — wind speed within ±2 std
devs, direction ±20°, temperature ±3°C, pressure ±5 mbar — answering "how much does ordinary
day-of variability move my already-chosen design's result," as opposed to Engine 1's wide
worst-case envelope. Writes `<rocketName>_localweather_<timestamp>.xlsx` (same Runs+Summary shape
as Engine 1) with its own live "most favorable local conditions" leaderboard.

**Step 4 — margin fin sets**: re-solves fin height ONLY (ballast and hole radius stay exactly as
solved in step 1) at four wind speeds — the pulled average ± 0.5 and ± 1.0 standard deviations —
and exports each as a standalone fin-set-only STL/OBJ (e.g. `..._finset_wind4_50ms_....stl`).
Example: a 5 m/s average with a 0.5 m/s std dev produces spare fin sets solved for 4.5, 4.75, 5.25,
and 5.5 m/s, so a team has a physical fin set ready to swap in if launch-day wind lands on one of
those margins instead of dead-center on the forecast.

Everything is written by this project's own dependency-free `MiniJson` (a small hand-rolled JSON
parser, matching `MiniParquet`'s existing dependency-free convention) and `WeatherClient` (built on
the JDK's own `java.net.http.HttpClient` — no HTTP library dependency needed).

## 6. Recovery speed heads-up (still relevant)

Your file's saved Simulation 1 shows a ~19.7 m/s deployment velocity — still on the fast side for
a chute opening (comfortable is usually under ~10-15 m/s), worth a look independent of anything
this tool outputs, since it's a recovery-hardware risk (shock cord snap, chute damage).

## 7. Launch site data

Coordinates live in `LaunchSite.java`. MDRA Central Sod Farm's lat/long come from MDRA's own
published field GPS marker; elevation is an unverified estimate. SPAAR Lancaster is geocoded from
a public address and not verified — confirm both against a GPS reading before relying on them.
