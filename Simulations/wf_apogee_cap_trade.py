#!/usr/bin/env python3
"""Rev 3d trade: cap apogee at 600 ft (182.9 m), lengthen the time the fins are actively flying the
rocket, and do not lose control authority. Also looks for a cheaper motor.

Candidates: every AeroTech single-use motor that fits the 29 x 83 mm bay (F67-6W, F42-4T, F27R-6,
F20W-7), each with nose ballast 110 to 300 g. Ballast is the cheap apogee knob that also moves
the CG forward, which lengthens the control-fin arm.

Authority is reported three ways, because "authority" can mean the airframe or the flight:
  b/q      control derivative per unit dynamic pressure, M_delta / (I q)  [1/s^2 per rad per Pa]
           (airframe property: arm, fin size, inertia; motor-independent except through mass)
  b_peak   b/q x the largest q seen while the fins are active          [1/s^2 per rad]
  B_int    integral of b over the controlled flight                     [1/s per rad]
           (how much steering the fins get to do over the whole flight)
plus the gust-case RMS tilt with the fins active and locked, which is the closed-loop answer.

    python3 wf_apogee_cap_trade.py   -> plots_flight/C_apogee_cap_trade.png, apogee_cap_trade.json
"""
import json, math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C
import wf_flightsim as F

OUT = os.path.join(C.HERE, "plots_flight")
CAP_M = 600 * 0.3048
CAND = {   # key: (.eng, certified impulse, delays, price for 4 motors, note)
    "F67-6W": ("AeroTech_F67W.eng", 61.1, [4, 6, 9], 98.98, "$49.49 per 2-pack"),
    "F42-4T": ("AeroTech_F42T.eng", 52.9, [4, 6, 8], 87.98, "$43.99 per 2-pack (Econojet)"),
    "F27R-6": ("AeroTech_F27R.eng", 49.6, [4, 6, 8], 98.98, "$49.49 per 2-pack"),
    "F20W-7": ("AeroTech_F20W.eng", 51.75, [4, 7], 98.98, "$49.49 per 2-pack"),
}
for k, (fn, I, d, price, note) in CAND.items():
    if k not in C.MOTORS: C.MOTORS[k] = C._from_eng("AeroTech " + k, fn, I, d, note)
BALLASTS = [110, 140, 170, 200, 240, 280]
RAIL_MIN = 14.0     # m/s; below this the trade rejects the case (club practice is ~15 m/s, 50 ft/s)

def case(motor, ballast, rule=("q", 15.0), H=40.0, span=40.0):
    v = F.Vehicle(motor, H=H, rect_span=span, ballast_g=ballast)
    tb = v.motor["tb"]
    on, Hh = F.simulate(v, gains=F.GAINS_FLIGHT, ctrl_until=rule)
    off, _ = F.simulate(v, gains=F.GAINS_FLIGHT, control=False)
    st = C.stability(v.cg0, H=H, rect_span=span)
    t = Hh["t"]; act = (t >= (on["rail_exit_t"] or 0)) & ((t <= tb) | (Hh["qbar"] >= rule[1])) & (t <= on["t_apogee"])
    b = Hh["bq"] * Hh["qbar"]
    i_burn = np.searchsorted(t, tb)
    delay = min(C.MOTORS[motor]["delays"], key=lambda d: abs(d - (on["t_apogee"] - tb)))
    return dict(motor=motor, H=H, stab_span=span, ballast_g=ballast, liftoff_g=round(v.M0 * 1000, 1), margin_cal=round(st["margin_cal"], 3),
                arm_mm=round(v.x_cA - v.cg0, 1), rail_exit_v=round(on["rail_exit_v"], 2), apogee_m=round(on["apogee_m"], 1),
                apogee_ft=round(on["apogee_m"] / 0.3048), t_apogee=round(on["t_apogee"], 2), burn_s=tb,
                ctrl_time_s=round(on["ctrl_time_s"], 2), powered_ctrl_s=round(max(tb - (on["rail_exit_t"] or 0), 0), 2),
                b_per_q=float(np.mean(Hh["bq"][act])), b_peak=float(b[act].max()), B_int=float(np.trapezoid(b[act], t[act])),
                max_q=round(on["max_q_Pa"]), tilt_rms_on=round(on["tilt_rms_deg"], 2), tilt_rms_off=round(off["tilt_rms_deg"], 2),
                delay_s=delay, eject_minus_apogee_s=round(tb + delay - on["t_apogee"], 2),
                price_4=CAND[motor][3], under_cap=on["apogee_m"] <= CAP_M, rail_ok=on["rail_exit_v"] >= RAIL_MIN)

if __name__ == "__main__":
    # rev 3c baseline (F67-6W, H40 fins, 40 mm stabilizers, 110 g) against the rev 3d pick and the
    # ways of getting under 600 ft that keep the old fin layout (ballast only, motor only).
    base = case("F67-6W", 110, H=40.0, span=40.0)
    cases = [("rev 3c baseline", base),
             ("F67-6W + 280 g ballast (old fins)", case("F67-6W", 280, H=40.0, span=40.0)),
             ("F42-4T, old fins, 140 g", case("F42-4T", 140, H=40.0, span=40.0)),
             ("F42-4T, H45, 25 mm stabs, 195 g", case("F42-4T", 195, H=45.0, span=25.0)),
             ("rev 3d: F42-4T, H45, 20 mm stabs, 214 g", case("F42-4T", C.BALLAST_G, H=45.0, span=20.0))]
    for name, r in cases:
        print(f"{name:42s} {r['liftoff_g']:6.1f} g  apo {r['apogee_ft']:4d} ft  rail {r['rail_exit_v']:5.1f}  margin {r['margin_cal']:.2f}  "
              f"ctrl {r['ctrl_time_s']:.2f} s (powered {r['powered_ctrl_s']:.2f})  b/q {r['b_per_q']:.4f}  b_peak {r['b_peak']:5.1f}  "
              f"B_int {r['B_int']:6.1f}  tilt {r['tilt_rms_on']}/{r['tilt_rms_off']}")
    json.dump(dict(cap_m=CAP_M, cases=[dict(name=n, **r) for n, r in cases]), open(os.path.join(OUT, "apogee_cap_trade.json"), "w"), indent=1, default=float)
    fig, ax = plt.subplots(1, 4, figsize=(18, 4.6))
    names = [n.replace(", ", ",\n", 1) for n, _ in cases]; cols = ["#94a3b8", "#cbd5e1", "#e09f3e", "#386641", "#2a6f97"]
    for a, (k, lbl) in zip(ax, (("apogee_ft", "apogee (ft)"), ("b_peak", "peak control accel b (1/s² per rad)"),
                                  ("B_int", "integrated authority (1/s per rad)"), ("tilt_rms_on", "gust-case RMS tilt, fins active (deg)"))):
        a.bar(range(len(cases)), [r[k] for _, r in cases], color=cols)
        a.set_xticks(range(len(cases))); a.set_xticklabels(names, fontsize=6.5, rotation=30, ha="right"); a.set_title(lbl, fontsize=9); a.grid(alpha=0.3, axis="y")
    ax[0].axhline(600, c="k", ls="--", lw=0.8)
    for a, k in zip(ax[1:3], ("b_peak", "B_int")): a.axhline(base[k], c="k", ls="--", lw=0.8)
    fig.suptitle("600 ft cap without losing authority: smaller stabilizers + H45 fins + ballast on the F42-4T (dashed: cap / rev 3c authority)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "C_apogee_cap_trade.png"), dpi=130)
