#!/usr/bin/env python3
"""GTR70E WYVERN (fin control), Monte-Carlo engine for the simulation suite.

This module does not carry its own physics. Every flight is `wf_flightsim.simulate()` on a
`wf_flightsim.Vehicle` built from `wf_core.py`, so a dataset row and the single-flight engines
can never disagree. What it adds:

  * a sampling envelope for the field (wind, turbulence, temperature, pressure, site elevation,
    rod angle, wind bearing) and per-flight build dispersions (mass, CG, drag, impulse, fin
    rigging, servo speed);
  * a process pool (one nominal Vehicle per worker, dispersions applied by copy), so ~1 flight
    per 0.4-0.8 s per core;
  * the descent leg (main chute at motor ejection, ~6.3 m/s, drifting with the wind profile) for
    the landing point;
  * the authority manoeuvre on every flight, so the dataset carries its predicted metrics.

The 3-DOF model is pitch-plane only: the in-plane wind component (wind * cos(bearing - rod
azimuth)) drives the flight, the cross component only drifts the descent.
"""
from __future__ import annotations
import copy, math, os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
if SIM not in sys.path: sys.path.insert(0, SIM)
import wf_core as C            # noqa: E402
import wf_flightsim as F      # noqa: E402

D2R = math.pi / 180
DESCENT_MS = 6.3              # under the 24 in chute (canonical)
ISA_T0, ISA_P0, R_AIR, LAPSE, G0 = 288.15, 101325.0, 287.05, 0.0065, 9.80665

ENVELOPE = dict(
    wind_ms=(0.0, 8.0),          # 10 m reference wind
    wind_dir_deg=(0.0, 360.0),   # bearing the wind blows toward, relative to the rod's lean
    turb_ms=(0.0, 1.5),          # Dryden-like turbulence intensity (m/s rms)
    gust_ms=(0.0, 4.0),          # 1-cos discrete gust amplitude
    temp_C=(5.0, 35.0),
    pressure_mbar=(990.0, 1025.0),
    site_alt_m=(0.0, 1500.0),
    launch_tilt_deg=(0.0, 5.0),
)
PRESETS = {
    "Typical field": dict(ENVELOPE),
    "Calm": dict(ENVELOPE, wind_ms=(0, 2), turb_ms=(0, 0.3), gust_ms=(0, 0.5), launch_tilt_deg=(0, 2)),
    "Club limit (20 mph)": dict(ENVELOPE, wind_ms=(6, 9), turb_ms=(0.5, 1.5), gust_ms=(2, 5)),
    "Hot & high": dict(ENVELOPE, temp_C=(30, 40), pressure_mbar=(985, 1000), site_alt_m=(1200, 1600)),
    "Full envelope": dict(ENVELOPE, wind_ms=(0, 9), turb_ms=(0, 2), gust_ms=(0, 6), temp_C=(-5, 40),
                          pressure_mbar=(985, 1030), site_alt_m=(0, 1600), launch_tilt_deg=(0, 8)),
}
DISPERSION = dict(               # 1-sigma build / lot tolerances
    mass_frac=0.02,              # print density, adhesive, wiring
    cg_mm=5.0,                   # ballast placement, battery position
    cd_frac=0.08,                # finish, fin alignment
    impulse_frac=0.03,           # AeroTech lot-to-lot
    fin_bias_deg=0.3,            # rigging / trim residual after the t2 calibration
    servo_frac=0.10,             # servo speed spread (voltage sag, unit-to-unit)
)
OUTCOME_COLS = ["flight", "wind_ms", "wind_dir_deg", "wind_inplane_ms", "turb_ms", "gust_ms", "temp_C",
                "pressure_mbar", "site_alt_m", "rho_ratio", "launch_tilt_deg", "mass_g", "cg_mm",
                "margin_cal", "cd_scale", "impulse_scale", "fin_bias_deg", "servo_scale", "control",
                "rail_exit_v", "apogee_m", "t_apogee_s", "max_q_Pa", "tilt_rms_deg", "tilt_max_deg",
                "defl_max_deg", "servo_sat_s", "max_hinge_mNm", "drift_apogee_m", "land_x_m", "land_y_m",
                "land_r_m", "ejection_vs_apogee_s", "man_status", "man_b_ratio_A", "man_b_t_A",
                "man_b_ratio_B", "man_achieved_A", "man_t63_A", "man_fin_per_deg_A", "man_achieved_B",
                "man_t63_B"]
TRACE_COLS = ["flight", "t", "x", "z", "v", "th", "q", "dl", "dc", "alpha", "qbar", "hm", "u", "ref", "inj"]

def isa_density_ratio(temp_C, p_mbar, site_alt_m):
    """Surface density at the site relative to ISA sea level (the model's rho_at(z) shape is kept)."""
    T0 = temp_C + 273.15
    T = T0 - LAPSE * site_alt_m
    P = p_mbar * 100.0 * (T / T0) ** (G0 / (R_AIR * LAPSE))
    return (P / (R_AIR * T)) / (ISA_P0 / (R_AIR * ISA_T0))

def sample_conditions(rng, n, envelope=None, disperse=True):
    e = dict(ENVELOPE); e.update(envelope or {})
    u = lambda k: rng.uniform(*e[k], n) if e[k][1] > e[k][0] else np.full(n, float(e[k][0]))
    c = {k: u(k) for k in ENVELOPE}
    d = DISPERSION; z = (lambda s: rng.normal(0, s, n)) if disperse else (lambda s: np.zeros(n))
    c["mass_frac"] = z(d["mass_frac"]); c["cg_mm"] = z(d["cg_mm"]); c["cd_scale"] = 1 + z(d["cd_frac"])
    c["impulse_scale"] = 1 + z(d["impulse_frac"]); c["fin_bias_deg"] = z(d["fin_bias_deg"])
    c["servo_scale"] = 1 + z(d["servo_frac"])
    return [{k: float(v[i]) for k, v in c.items()} for i in range(n)]

# ------------------------------------------------------------------------------- per-worker state
_VEH = None
_GAINS = None
def _init(gains=None, motor=None):
    global _VEH, _GAINS
    _VEH = F.Vehicle(motor or C.FLIGHT_MOTOR)
    _GAINS = dict(gains or F.GAINS_FLIGHT)

def make_vehicle(cond, base=None):
    v = copy.copy(base or _VEH)
    k = 1.0 + cond.get("mass_frac", 0.0)
    v.M0, v.Mb = v.M0 * k, v.Mb * k
    v.cg0, v.cgb = v.cg0 + cond.get("cg_mm", 0.0), v.cgb + cond.get("cg_mm", 0.0)
    v.cd_scale = cond.get("cd_scale", 1.0); v.imp_scale = cond.get("impulse_scale", 1.0)
    v.fin_bias_deg = cond.get("fin_bias_deg", 0.0); v.servo_scale = cond.get("servo_scale", 1.0)
    v.rho_scale = isa_density_ratio(cond.get("temp_C", 15), cond.get("pressure_mbar", 1013.25), cond.get("site_alt_m", 0))
    return v

def descent(apogee_m, x_apo, cond, t_apo, eject_t):
    """Chute opens at motor ejection; drift with the power-law wind until touchdown."""
    if apogee_m is None: return None, None, None
    w = cond.get("wind_ms", 0.0); b = cond.get("wind_dir_deg", 0.0) * D2R
    h_open = apogee_m - 0.5 * G0 * max(eject_t - t_apo, 0.0) ** 2 if eject_t > t_apo else apogee_m
    h_open = max(h_open, 0.0)
    # mean of u(z) = w (z/10)^(1/7) over 0..h_open
    um = w * (7 / 8) * (max(h_open, 1.0) / 10.0) ** (1 / 7) if h_open > 0 else 0.0
    t_d = h_open / DESCENT_MS
    lx = x_apo + um * math.cos(b) * t_d; ly = um * math.sin(b) * t_d
    return lx, ly, math.hypot(lx, ly)

def run_flight(cond, control=True, record=False, dt=0.001, maneuver=True, gains=None, base=None):
    """One flight from a condition dict -> (outcome row, trace dict or None)."""
    veh = make_vehicle(cond, base)
    g = dict(gains or _GAINS or F.GAINS_FLIGHT)
    w_in = cond.get("wind_ms", 0.0) * math.cos(cond.get("wind_dir_deg", 0.0) * D2R)
    tb = veh.motor["tb"]
    man = F.maneuver_events(tb, "A") if (maneuver and control) else None
    r, H = F.simulate(veh, wind=w_in, gust=cond.get("gust_ms", 0.0), turb=cond.get("turb_ms", 0.0),
                      control=control, gains=g, dt=dt, seed=int(cond.get("seed", 1)),
                      launch_tilt_deg=cond.get("launch_tilt_deg", 0.0), maneuver=man, ctrl_until="firmware")
    eject_t = tb + min(veh.motor["delays"], key=lambda d: abs(d - ((r["t_apogee"] or tb) - tb)) if d > 0 else 99)
    xa = float(H["x"][-1]) if len(H["t"]) else 0.0
    lx, ly, lr = descent(r["apogee_m"], xa, cond, r["t_apogee"] or 0.0, eject_t)
    M = r.get("maneuver", {}) or {}
    dA = M.get("doublet", {}) or {}; sA = M.get("step", {}) or {}
    stab = C.stability(veh.cg0)
    row = dict(flight=int(cond.get("flight", 0)), wind_ms=cond.get("wind_ms", 0), wind_dir_deg=cond.get("wind_dir_deg", 0),
               wind_inplane_ms=w_in, turb_ms=cond.get("turb_ms", 0), gust_ms=cond.get("gust_ms", 0),
               temp_C=cond.get("temp_C", 15), pressure_mbar=cond.get("pressure_mbar", 1013.25), site_alt_m=cond.get("site_alt_m", 0),
               rho_ratio=veh.rho_scale, launch_tilt_deg=cond.get("launch_tilt_deg", 0), mass_g=veh.M0 * 1000, cg_mm=veh.cg0,
               margin_cal=stab["margin_cal"] if isinstance(stab, dict) and "margin_cal" in stab else float("nan"),
               cd_scale=veh.cd_scale, impulse_scale=veh.imp_scale, fin_bias_deg=veh.fin_bias_deg, servo_scale=veh.servo_scale,
               control=int(control), rail_exit_v=r["rail_exit_v"], apogee_m=r["apogee_m"], t_apogee_s=r["t_apogee"],
               max_q_Pa=r["max_q_Pa"], tilt_rms_deg=r.get("tilt_rms_deg"), tilt_max_deg=r.get("tilt_max_deg"),
               defl_max_deg=r.get("defl_max_deg"), servo_sat_s=r["servo_rate_sat_s"], max_hinge_mNm=r["max_hinge_Nm"] * 1000,
               drift_apogee_m=xa, land_x_m=lx, land_y_m=ly, land_r_m=lr,
               ejection_vs_apogee_s=(eject_t - r["t_apogee"]) if r["t_apogee"] else None,
               man_status=(4 if M.get("aborted") else 3 if M.get("skipped") else 2) if M else 0,
               man_b_ratio_A=dA.get("b_ratio"), man_b_t_A=dA.get("t_stat"), man_b_ratio_B=None,
               man_achieved_A=sA.get("achieved_deg"), man_t63_A=sA.get("t63_s"), man_fin_per_deg_A=sA.get("fin_per_deg"),
               man_achieved_B=None, man_t63_B=None)
    tr = None
    if record:
        n = len(H["t"])
        tr = {"flight": np.full(n, row["flight"])}
        for k in TRACE_COLS[1:]: tr[k] = H[k]
    return row, tr

def _task(args):
    cond, control, record, dt, maneuver = args
    return run_flight(cond, control, record, dt, maneuver)

def batch(conds, control=True, record=False, dt=0.001, maneuver=True, workers=None, gains=None,
          progress=None, cancel=None):
    """Run flights in a process pool. progress(done, total, rate) is called as they finish.
    Yields (row, trace) in completion order."""
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    total = len(conds); t0 = time.time(); done = 0
    if workers == 1:
        _init(gains)
        for c in conds:
            if cancel is not None and cancel.is_set(): return
            yield run_flight(c, control, record, dt, maneuver)
            done += 1
            if progress: progress(done, total, done / max(time.time() - t0, 1e-6))
        return
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(gains,)) as ex:
        futs = [ex.submit(_task, (c, control, record, dt, maneuver)) for c in conds]
        try:
            for fu in as_completed(futs):
                if cancel is not None and cancel.is_set():
                    for f2 in futs: f2.cancel()
                    return
                yield fu.result()
                done += 1
                if progress: progress(done, total, done / max(time.time() - t0, 1e-6))
        finally:
            for f2 in futs: f2.cancel()

def conditions(n, seed=0, envelope=None, disperse=True):
    rng = np.random.default_rng(seed)
    cs = sample_conditions(rng, n, envelope, disperse)
    for i, c in enumerate(cs): c["flight"] = i; c["seed"] = seed * 100003 + i
    return cs

if __name__ == "__main__":
    cs = conditions(4, seed=1)
    for row, _ in batch(cs, workers=2, dt=0.002):
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items() if k in ("flight", "wind_ms", "apogee_m", "tilt_rms_deg", "land_r_m", "man_b_ratio_A")})
