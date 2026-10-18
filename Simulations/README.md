# Simulations

`wf_core.py` is the single source of truth: geometry, materials, COTS masses and stations, motor curves (RASP data from thrustcurve.org), atmosphere, drag build-up, Barrowman normal force, slender-body interference K_W(B), the body boundary-layer loss, and the control-fin → fixed-fin vortex-interference model. Everything else imports it.

| Script | Output |
|---|---|
| `wf_core.py --report` | `canonical_numbers.json` |
| `wf_flightsim.py [--retune]` | `plots_flight/`: motor trade (F67-6W, F42-4T, G74-6W), tuned gains, authority manoeuvre, flight_summary.json |
| `wf_fin_authority.py` | `plots_authority/`: authority matrix (4 profiles x 8 heights), isolated vs installed authority, closed-loop sweep, Phase A single-fin and Phase B pair tunnel predictions, H* selection |
| `wf_stabilizer.py` | `plots_stabilizer/`: SQ1 sweep of stabilizer span (0-60 mm) x azimuth offset (0 / 22.5 / 45°): margin, interference ratio, installed / isolated authority, closed-loop gust case with fins active and locked, tunnel Phase B load predictions |
| `wf_bypass.py` | `plots_bypass/`: ejection-gas lumped model, tube diameter trade |
| `wf_power.py` | `plots_power/`: 25 min idle + 1 min flight battery budget |
| `wf_link_budget.py` | `plots_link/`: LoRa time-on-air, sensitivity, range |
| `CFD/run_airfoil_cfd.py` | 2D vortex-panel polars for the four sections (method carried over from the TVC revision) |
| `CFD/vlm.py` | 3D horseshoe vortex-lattice model of the triangular fin (CNα, CP, hinge arm) |

Model limits worth keeping in mind: the 2D and 3D CFD here is potential flow, so it has no stall, separation or low-Re bubbles (the tunnel covers those). The vortex-interference model is a single rolled-up vortex, which makes it a pessimistic bound; `WYV_INTERF=0.5 python3 wf_fin_authority.py` runs the half-strength case. The flight sim is 3-DOF, pitch plane only, so roll is not simulated.

## Rev 3c additions

| Path | What |
|---|---|
| `wf_flightsim.py` | now also flies the authority manoeuvre (`MAN`, `MAN_GATE`, `maneuver_events`, `maneuver_metrics`, `run_maneuver`, `maneuver_monte_carlo`) and writes `plots_flight/B_authority_maneuver.png` + `maneuver_prediction.json`. `ctrl_until="firmware"` reproduces the firmware's end-of-control rule (burnout and climb rate under 15 m/s). Vehicle dispersion hooks (`cd_scale`, `imp_scale`, `rho_scale`, `fin_bias_deg`, `servo_scale`) default to nominal |
| `wyvern_finsim/` | the rebuilt GUI suite (datasets, plots, viewer, PID tuner, firmware SIL, manoeuvre, authority / SQ1, tunnel bench, motor stand, super-combined, engines). See its README |
| `CFD/simscale/` | SimScale RANS package (ten cases) with predictions to compare against |
| `../Flight Computer/firmware/sil_host/` | desktop build of the firmware's manoeuvre code; `sil_check.py` compares it with the simulator (they agree to three decimals) |
