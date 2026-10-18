# GTR70E WYVERN, Simulations

- `we4_flightsim.py` → `plots4/01_trajectory.png` + `flightsim_summary.json`, **unified RK4(2e-4) + Barrowman engine** (apogee 397 ft @ 6.67 s, motor-ejection deploy at t=7.45 s / 7.7 m/s, finned margin +1.14 cal).
- `we4_sim.py` → `plots4/`, mass/CG/inertia, F15-4 trajectory, TVC pitch control + authority,
  recovery, dispersion (`01`–`06`) + `results_summary.json`.
- `we4_analysis.py` → `plots4/`, drag buildup (`07`), first-order structural/FEA margins (`08`),
  engine-bay thermal soak (`09`), power budget (`10`), apogee sensitivity tornado (`11`), gimbal/
  servo sizing (`12`).
- `build_ork4.py` → `WYVERN_E4_F15-4.ork` (open in OpenRocket 23.09 for an independent cross-check
  of the Barrowman CP/CG and trajectory; OpenRocket cannot model the active-TVC contribution, so the
  TVC results here are the authority).

Run: `python3 we4_flightsim.py && python3 we4_sim.py && python3 we4_analysis.py && python3 build_ork4.py`.

Key results: liftoff 729 g · T/W 2.01/3.54 · CG 45.0 cm / CP 53.3 cm (+1.14 cal) · Iyy 0.0257 kg·m² ·
apogee 397 ft @ 6.67 s · v_max 34.5 m/s (Mach 0.101) · rail exit pending re-verify against the
zoned-material mass stack · min SF ~340× · engine wall ~47 °C · gimbal torque ~0.56 kg·cm (±8°) ·
battery 450 mAh → ~40 flights/charge.

## Flight-validation suite (`we4_validation.py` → `plots_val/`)
Eight independent simulations with hard PASS/FAIL gates → `plots_val/validation_summary.json` +
`01_trajectory` `02_stability_margin` `03_rail_departure` `04_tvc_authority` `05_wind_weathercock`
`06_montecarlo` `07_landing_scatter` `08_recovery` `09_verdict`. Run `python3 we4_validation.py`.
Result: **10/13 gates pass**. The 3 flags share one root cause, the F15 is underpowered for the
729 g vehicle (rail-exit and weathercock margins per we4_stability.py). Mitigated by active
TVC (63.2x the required maneuver moment, airspeed-independent, engages t=0.5 s) + low-wind launch.

## Deep sim batch (`we4_deepsim.py` → `plots_deep/`)
Second-tier engineering checks for the F15-4 single-stage servo-TVC config (`deepsim_summary.json`):
A fin flutter/divergence (NACA TN-4197; PETG-CF fin margin 21.1× over v_max, PLA 13.8×, at Mach 0.087) · B aero heating (peak skin
≪ ASA/PETG-CF Tg, low-speed flight) · C servo torque (**2.3× margin** vs 0.20 N·m stall at the full ±8° limit, FLAGGED) · D CG-tolerance
(0.81 cal at 20 mm aft build error; 1.0 cal holds to 7 mm aft) · E rod-angle×wind dispersion grid · F TVC step response
(rise 0.36 s, ~0% overshoot, settle 0.46 s) · G drag ±25% (stays <1000 ft) · H battery endurance.
**Result: 7/8 pass.** The one flag is **C servo torque: 2.3x margin against stall, below the 3.0x
gate.** That number moved because the hinge moment is now evaluated at the FULL +-8 deg gimbal
limit rather than at a mid-range 5 deg, which had understated worst-case load by 1.6x. It is a
real finding, not a regression, and it is directly measurable on the TVC balance during the RQ1
ground campaign -- see `Documentation/WYVERN_E4_Timeline_14Day.md` Day 9.
Run `python3 we4_deepsim.py`.

## Motor decision
`we4_motor_tradestudy.py` is the record of the F15 motor-class choice: it is the only motor holding both the
<1000 ft ceiling (397 ft / 121.1 m) and the long 2.95 s TVC window (the three-way trade is documented).

## Atmospheric TVC + PID (`we4_atmos_tvc.py` → `plots_atmos/`, `pid_reference.py`)
Closed-loop pitch-plane TVC through 4 atmospheres (cold/ISA/hot/high-DA + humidity) with mid- and
late-burn gusts. Key results: dynamic pressure q (and thus gust forcing + fin damping) both scale
with density and partly cancel. Tuning revealed the old Kp=8 gains RING against the 40 ms servo
lag, and a follow-up margin analysis (`Documentation/PID_TUNING_REPORT.md`) that adds the 2 ms
control-loop delay on top of the servo lag showed the next-tried Kp=2.0/Ki=0.4/Kd=0.5 gains are
*also* unstable in the worst case (negative phase/gain margin, Cold −15°C early-burn). Final,
margin-validated gains: **Kp=0.10 / Ki=0.40 / Kd=0.18**, worst-case phase margin 44.7°, gain
margin 12.6 dB, gust pitch deviation 1.96° / gimbal 2.35° (limit ±8°) across all 4 atmospheres.
`pid_reference.py` is the Python twin of `firmware/wyvern_pid.h`. Gain-scheduling adds <1% ⇒ a
simple fixed-gain PID is used. Run `python3 we4_atmos_tvc.py`.
