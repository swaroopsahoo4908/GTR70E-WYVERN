# wyvern_finsim: simulation & dataset suite (fin control)

The TVC-era `wyvern_datagen` suite rebuilt for the fin-controlled airframe. It has no physics of its own: every flight is `wf_flightsim.simulate()` on a `wf_core` vehicle, so a dataset row, a GUI plot and the single-run engines agree by construction.

Launch: `/opt/homebrew/bin/python3 run_gui.py` (or double-click `launch.command`). Headless: `python3 datagen.py outcomes --n 2000 --out datasets/outcomes.csv`.

| Tab | What it does |
|---|---|
| Datasets | Monte-Carlo outcomes and/or 200 Hz traces over a field envelope (wind, bearing, turbulence, gust, temperature, pressure, site elevation, rod angle) with build dispersions (mass, CG, drag, impulse, fin rigging, servo speed). Process pool, progress, cancel. CSV or Parquet |
| Plots & Analysis | histogram, scatter, hexbin, trajectories, landing map, authority vs wind, correlation heatmap |
| Data Viewer | virtualized table, click a header to sort |
| PID Tuner | kp / ki / kd / q_ref / schedule clamp / deflection limit against a wind + gust case, live; grid-search auto-tune; prints the `fc_config.h` lines |
| Flight Computer SIL | flies the authority manoeuvre and replays it through the firmware's own `controller.h` (compiled for your computer from `Flight Computer/firmware/sil_host/replay.cpp`); sim and firmware metrics side by side, state timeline, emulated ground-station lines, save as a `wyvern_host.py --replay` recording |
| Authority Manoeuvre | the doublet + attitude-step programme: nominal A/B response and the Monte-Carlo spread of the identified authority |
| Fin Authority / SQ1 | plots from `wf_fin_authority`, `wf_stabilizer`, `wf_stabilizer_planform_trade`, `wf_flightsim`, with a re-run button |
| Wind Tunnel Bench | Phase A sweep through two TAL221 cells and NAU7802s, four profiles, raw vs calibrated |
| Static Motor Tester | any `.eng` in `Simulations/motors` on the stand through the HX711 chain |
| Super Combined | live N-flight run: apogee vs wind, landing scatter, tilt rms, authority fits; saves the outcomes |
| Project Engines | runs each `wf_*.py`, the airfoil panel code and the SimScale package generator, streaming output |

Files: `engine.py` (sampling, dispersions, pool, descent), `datagen.py` (writers + CLI), `analysis.py` (plots, carried over), `bench.py` (motor stand + tunnel bench), `sil.py` (firmware replay, telemetry emulation), `gui.py`.

Speed: about 0.4 s per flight per core at dt = 0.002 s (0.8 s at 0.001 s). A 2000-flight outcomes set on an 8-core Mac is roughly 2 minutes.

Limits: pitch plane only (the in-plane wind component flies the rocket; the cross component only drifts the descent), potential-flow fin aerodynamics, and an assumed tunnel-bench noise floor until the first bench run measures it.
