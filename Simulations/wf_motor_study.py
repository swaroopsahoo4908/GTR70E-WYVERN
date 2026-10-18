#!/usr/bin/env python3
"""Rev 3d motor question: would a slow-burning F27R-4 or F20W-4 / F20W-7 beat the F42-4T?

All four motors are flown on the rev 3d airframe (H45 control fins, 81 x 20 mm stabilizers at 45 deg,
214 g ballast) off a 6, 8 and 10 ft rail, in the standard gust case (4 m/s wind, 4 m/s 1-cos gust,
1 m/s turbulence) and, for the authority manoeuvre, in the 4 m/s nominal case. Control ends at
q < 15 Pa after burnout (firmware rule). Authority terms as in wf_apogee_cap_trade.py.

    python3 wf_motor_study.py   -> plots_flight/D_motor_study.png, motor_study.json
"""
import json, math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C
import wf_flightsim as F

OUT = os.path.join(C.HERE, "plots_flight")
FT = 0.3048
MOTORS = {   # key: (.eng, certified impulse, delay flown, price for 4)
    "F42-4T": ("AeroTech_F42T.eng", 52.9, 4, 87.98),
    "F27R-4": ("AeroTech_F27R.eng", 49.6, 4, 98.98),
    "F20W-4": ("AeroTech_F20W.eng", 51.75, 4, 98.98),
    "F20W-7": ("AeroTech_F20W.eng", 51.75, 7, 98.98),
}
for k, (fn, I, d, _) in MOTORS.items():
    if k not in C.MOTORS: C.MOTORS[k] = C._from_eng("AeroTech " + k, fn, I, [d], "")
RAILS_FT = [6, 8, 10]

def fly(motor, rail_ft):
    C.RAIL_LEN_M = rail_ft * FT
    v = F.Vehicle(motor); tb = v.motor["tb"]; delay = MOTORS[motor][2]
    on, H = F.simulate(v, gains=F.GAINS_FLIGHT, ctrl_until=("q", F.CTRL_END_QBAR))
    off, _ = F.simulate(v, gains=F.GAINS_FLIGHT, control=False)
    t = H["t"]; act = (t >= on["rail_exit_t"]) & (t <= on["t_apogee"]) & ((t <= tb) | (H["qbar"] >= F.CTRL_END_QBAR))
    b = H["bq"] * H["qbar"]
    # where is the rocket when the motor's ejection fires
    te = tb + delay; vz_e = None
    if te <= t[-1]:
        i = np.searchsorted(t, te); vz_e = float(np.gradient(H["z"], t)[min(i, len(t) - 1)])
    man, _ = F.run_maneuver(veh=v)
    dA = man["A"].get("doublet", {}); sA = man["A"].get("step", {})
    early = (t >= on["rail_exit_t"]) & (t <= on["rail_exit_t"] + 1.0)
    return dict(motor=motor, rail_ft=rail_ft, burn_s=tb, rail_exit_v=round(on["rail_exit_v"], 2), rail_exit_t=round(on["rail_exit_t"], 3),
                apogee_ft=round(on["apogee_m"] / FT), t_apogee=round(on["t_apogee"], 2), ctrl_s=round(on["ctrl_time_s"], 2),
                powered_ctrl_s=round(max(tb - on["rail_exit_t"], 0), 2), max_q=round(on["max_q_Pa"]),
                b_peak=round(float(b[act].max()), 1), B_int=round(float(np.trapezoid(b[act], t[act])), 1),
                tilt_rms_on=round(on["tilt_rms_deg"], 2), tilt_rms_off=round(off["tilt_rms_deg"], 2),
                tilt_max_on=round(on["tilt_max_deg"], 2), tilt_max_first_s=round(float(np.max(np.abs(H["th"][early]))), 2),
                defl_sat_first_s=round(float(np.mean(np.abs(H["dl"][early]) > 14.5)), 2),
                eject_minus_apogee_s=round(te - on["t_apogee"], 2), vz_at_eject=None if vz_e is None else round(vz_e, 1),
                man_qbar_doublet=round(dA.get("qbar_Pa", 0)), man_b_ratio=dA.get("b_ratio"), man_step_skipped=man["A"].get("step_skipped"),
                man_t63=sA.get("t63_s"), man_skipped=man["A"]["skipped"], price_4=MOTORS[motor][3])

if __name__ == "__main__":
    rows = []
    for m in MOTORS:
        for r in RAILS_FT:
            x = fly(m, r); rows.append(x)
            print(f"{m:7s} {r:2d} ft  rail {x['rail_exit_v']:5.1f} m/s  apo {x['apogee_ft']:4d} ft  t_apo {x['t_apogee']:.2f}  ctrl {x['ctrl_s']:.2f} "
                  f"(pwr {x['powered_ctrl_s']:.2f})  b_peak {x['b_peak']:5.1f}  B_int {x['B_int']:6.1f}  tilt {x['tilt_rms_on']}/{x['tilt_rms_off']} "
                  f"max1s {x['tilt_max_first_s']}  sat1s {x['defl_sat_first_s']}  eject {x['eject_minus_apogee_s']:+.2f} s (vz {x['vz_at_eject']})  "
                  f"man q {x['man_qbar_doublet']} skip {x['man_skipped']} stepskip {x['man_step_skipped']}")
    C.RAIL_LEN_M = 6 * FT
    json.dump(rows, open(os.path.join(OUT, "motor_study.json"), "w"), indent=1, default=float)
    fig, ax = plt.subplots(1, 4, figsize=(18, 4.6))
    cols = {"F42-4T": "#2a6f97", "F27R-4": "#386641", "F20W-4": "#e09f3e", "F20W-7": "#bc4749"}
    for m in MOTORS:
        rr = [x for x in rows if x["motor"] == m]; rl = [x["rail_ft"] for x in rr]
        for a, k in zip(ax, ("rail_exit_v", "ctrl_s", "B_int", "tilt_rms_on")):
            a.plot(rl, [x[k] for x in rr], "o-", c=cols[m], label=m)
    ax[0].axhline(15, c="k", ls="--", lw=0.8)
    for a, t_ in zip(ax, ("rail exit speed (m/s), 15 m/s guideline dashed", "time with fins flying the rocket (s)",
                          "integrated authority (1/s per rad)", "gust-case RMS tilt, fins active (deg)")):
        a.set_title(t_, fontsize=9); a.set_xlabel("rail length (ft)"); a.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    fig.suptitle("Slow-burn motors on the rev 3d airframe (H45, 20 mm stabilizers, 214 g)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "D_motor_study.png"), dpi=130)
