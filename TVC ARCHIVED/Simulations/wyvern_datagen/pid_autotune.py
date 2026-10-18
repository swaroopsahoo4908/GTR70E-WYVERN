#!/usr/bin/env python3
"""
GTR70E WYVERN, PID auto-tune (robust, multi-wind, time-domain).

Complements the frequency-domain margin analysis in PID_TUNING_REPORT.md: searches Kp/Ki/Kd over a
coarse→fine grid and scores each gain set by a robustness cost averaged over several wind speeds,
using the same closed-loop pitch plant as the flight TVC model (core.simulate_tvc_trace).

Cost (lower = better), averaged over winds:
    peak pitch° + 2·steady-error° + 0.3·settle_s + 0.5·RMS gimbal° + 0.05·gimbal-saturation%
i.e. reward tight, low-steady-error tracking without over-driving / saturating the ±8° gimbal.
"""
import numpy as np
try:
    import core
except ImportError:
    from . import core

WINDS = (3.0, 6.0, 9.0, 12.0)
TURB = 15.0


def cost_for(kp, ki, kd, winds=WINDS, turb=TURB, dt=0.004):
    tot = 0.0
    for w in winds:
        m = core.simulate_tvc_trace(kp, ki, kd, wind=w, turb=turb, disturbance="Wind gust", dt=dt)["metrics"]
        tot += (m["peak_pitch_deg"] + 2.0 * m["steady_err_deg"] + 0.3 * m["settle_time_s"]
                + 0.5 * m["rms_gimbal_deg"] + 0.05 * m["gimbal_saturation_pct"])
    return tot / len(winds)


def _search(kps, kis, kds, dt, progress=None):
    rows = []
    n = len(kps) * len(kis) * len(kds); i = 0
    for kp in kps:
        for ki in kis:
            for kd in kds:
                rows.append((cost_for(kp, ki, kd, dt=dt), kp, ki, kd))
                i += 1
                if progress and i % 10 == 0:
                    progress(i, n)
    rows.sort(key=lambda r: r[0])
    return rows


def autotune(dt=0.004, progress=None):
    """Coarse grid then a fine refine around the best point. Returns (best, ranked_rows, firmware)."""
    kps = [0.05, 0.10, 0.20, 0.35, 0.50]
    kis = [0.0, 0.20, 0.40, 0.70, 1.00]
    kds = [0.0, 0.10, 0.20, 0.35, 0.50]
    coarse = _search(kps, kis, kds, dt, progress)
    _, bkp, bki, bkd = coarse[0]
    fine_kp = sorted({max(0.02, bkp + d) for d in (-0.05, 0, 0.05)})
    fine_ki = sorted({max(0.0, bki + d) for d in (-0.15, 0, 0.15)})
    fine_kd = sorted({max(0.0, bkd + d) for d in (-0.08, 0, 0.08)})
    fine = _search(fine_kp, fine_ki, fine_kd, dt, progress)
    ranked = sorted(coarse + fine, key=lambda r: r[0])
    best = ranked[0]
    fw = (cost_for(core.KP, core.KI, core.KD, dt=dt), core.KP, core.KI, core.KD)
    return best, ranked, fw


if __name__ == "__main__":
    import time
    t0 = time.time()
    best, ranked, fw = autotune()
    print(f"searched {len(ranked)} gain sets in {time.time()-t0:.1f}s\n")
    print("rank cost Kp Ki Kd")
    seen = set()
    for c, kp, ki, kd in ranked:
        key = (round(kp, 3), round(ki, 3), round(kd, 3))
        if key in seen:
            continue
        seen.add(key)
        print(f" {c:6.2f} {kp:.3f} {ki:.3f} {kd:.3f}")
        if len(seen) >= 8:
            break
    print(f"\nBEST cost {best[0]:.2f} -> Kp={best[1]:.3f} Ki={best[2]:.3f} Kd={best[3]:.3f}")
    print(f"FIRMWARE cost {fw[0]:.2f} -> Kp={fw[1]:.3f} Ki={fw[2]:.3f} Kd={fw[3]:.3f}")
    print(f"improvement over firmware: {100*(fw[0]-best[0])/fw[0]:.1f}%")
