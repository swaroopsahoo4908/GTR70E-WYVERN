#!/usr/bin/env python3
"""Flight-computer software-in-the-loop for the suite (no Tk).

* Flies wf_flightsim with the firmware's control rule and the authority manoeuvre.
* Replays each axis through the real firmware manoeuvre code (controller.h, compiled for the
  desktop by Flight Computer/firmware/sil_host/replay.cpp) and puts the firmware's own metrics
  next to the simulator's.
* Rebuilds the flight-state timeline the firmware state machine would log (PAD, BOOST, CONTROL,
  COAST, DESCENT, LANDED) and emulates the ground station's USB lines (T / M), which can be
  saved as a recording that `wyvern_host.py --replay` opens.
"""
from __future__ import annotations
import json, math, os, shutil, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
ROOT = os.path.dirname(SIM)
FW = os.path.join(ROOT, "Flight Computer", "firmware")
if SIM not in sys.path: sys.path.insert(0, SIM)
import wf_core as C          # noqa: E402
import wf_flightsim as F     # noqa: E402

STATES = ["BOOT", "SELFTEST", "PAD", "ARMED", "BOOST", "CONTROL", "COAST", "DESCENT", "LANDED", "FAULT"]

def build_replay():
    """Compile the firmware replay harness once; returns the executable path or None."""
    cxx = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not cxx: return None
    src = os.path.join(FW, "sil_host", "replay.cpp")
    exe = os.path.join(tempfile.gettempdir(), "wyvern_replay")
    newest = max(os.path.getmtime(p) for p in [src] + [os.path.join(FW, "wyvern_fin", h) for h in ("controller.h", "shared_state.h", "fc_config.h")])
    if not os.path.exists(exe) or os.path.getmtime(exe) < newest:
        r = subprocess.run([cxx, "-O2", "-std=c++17", "-I", os.path.join(FW, "sil_host", "shim"), "-I", os.path.join(FW, "wyvern_fin"), src, "-o", exe],
                           capture_output=True, text=True)
        if r.returncode != 0: raise RuntimeError("replay build failed:\n" + r.stderr[-2000:])
    return exe

def firmware_replay(H, axis_idx):
    exe = build_replay()
    if exe is None: return None
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
        fh.write("t,th,q,dl,qbar,tilt_total,alt\n")
        for i in range(len(H["t"])):
            fh.write(f"{H['t'][i]:.6f},{H['th'][i] * F.D2R:.7f},{H['q'][i] * F.D2R:.7f},{H['dl'][i]:.5f},{H['qbar'][i]:.3f},{abs(H['th'][i]) * F.D2R:.7f},{H['z'][i]:.3f}\n")
        path = fh.name
    try:
        out = subprocess.run([exe, path, str(axis_idx)], capture_output=True, text=True, check=True).stdout
    finally:
        os.remove(path)
    return json.loads(out)

def timeline(H, tb, apogee_t):
    """Firmware state per sample: BOOST to rail clear, CONTROL to burnout and vz < 15 m/s, COAST to
    apogee, DESCENT after (the 3-DOF run ends shortly after apogee)."""
    t = H["t"]; vz = np.gradient(H["z"], t)
    st = np.full(len(t), STATES.index("CONTROL"))
    st[t < 0.20] = STATES.index("BOOST")
    st[(t > tb) & (vz < 15.0)] = STATES.index("COAST")
    if apogee_t: st[t >= apogee_t] = STATES.index("DESCENT")
    return st

def run(wind=4.0, gust=0.0, turb=0.5, seed=3, launch_tilt=0.0, gains=None, pad=(40.0, -105.0)):
    veh = F.Vehicle(C.FLIGHT_MOTOR); tb = veh.motor["tb"]; g = gains or F.GAINS_FLIGHT
    res = {}; traces = {}
    for ax, idx in (("A", 0), ("B", 1)):
        r, H = F.simulate(veh, wind=wind, gust=gust, turb=turb, seed=seed, gains=g, ctrl_until="firmware",
                          launch_tilt_deg=launch_tilt, maneuver=F.maneuver_events(tb, ax))
        fw = firmware_replay(H, idx)
        res[ax] = dict(sim=r.get("maneuver", {}), fw=fw, apogee=r["apogee_m"], t_apogee=r["t_apogee"])
        traces[ax] = H
    H = traces["A"]; st = timeline(H, tb, res["A"]["t_apogee"])
    lines = emulate_lines(H, st, res, pad)
    return res, traces, st, lines

def emulate_lines(H, st, res, pad):
    """Ground-station USB lines at the real downlink cadence (20 Hz, the manoeuvre frame after
    the programme ends)."""
    out = []; t = H["t"]; lat0, lon0 = pad; k = 0; man_sent = 0
    t_man_end = F.MAN_T0_AFTER_BURN + C.MOTORS[C.FLIGHT_MOTOR]["tb"] + (F.MAN["offsets"]["sB"] + F.MAN["hold"] + F.MAN["rest"])
    for i in range(0, len(t), 10):      # 200 Hz trace -> 20 Hz
        k += 1; s = int(st[i]); ti = t[i]
        if ti > t_man_end and man_sent < 5 and k % 4 == 0 and res["A"]["fw"]:
            a, b = res["A"]["fw"], res["B"]["fw"] or {}
            def ax(d): return [d.get("qbar_d", 0), d.get("b_fit", 0), d.get("b_t", 0), d.get("b_ratio", 0), d.get("qbar_s", 0),
                               d.get("step_sign", 0), d.get("achieved_deg", 0), d.get("t63_s", -1), d.get("return63_s", -1),
                               d.get("overshoot_pct", 0), d.get("fin_per_deg", 0), d.get("peak_rate_dps", 0)]
            out.append("M,2,15," + ",".join(f"{v:.4g}" for v in ax(a) + ax(b))); man_sent += 1; continue
        vz = (H["z"][min(i + 1, len(t) - 1)] - H["z"][max(i - 1, 0)]) / max(t[min(i + 1, len(t) - 1)] - t[max(i - 1, 0)], 1e-6)
        out.append(f"T,{int(ti * 1000)},{s},{k},{H['z'][i]:.1f},{vz:.2f},{H['th'][i]:.2f},0.00,{-H['q'][i]:.1f},0.0,0.0,0.00,0.00,0.00,"
                   f"{-H['dl'][i]:.1f},{-H['dl'][i]:.1f},0.0,0.0,{int(H['qbar'][i])},7.80,24,1,0.00,-70,9.0")
    return out

def save_recording(lines, stem):
    import csv
    sys.path.insert(0, os.path.join(ROOT, "Flight Computer", "ground_station", "host"))
    import wyvern_host as Hh
    files = {t: open(f"{stem}_{t}.csv", "w", newline="") for t in Hh.COLS}
    ws = {t: csv.writer(f) for t, f in files.items()}
    for t, w in ws.items(): w.writerow(Hh.COLS[t])
    for ln in lines:
        p = Hh.parse(ln)
        if p: ws[p[0]].writerow([p[1][k] for k in Hh.COLS[p[0]]])
    for f in files.values(): f.close()
    return stem

if __name__ == "__main__":
    res, traces, st, lines = run()
    for ax in "AB":
        s, f = res[ax]["sim"], res[ax]["fw"]
        print(ax, "sim b", round(s.get("doublet", {}).get("b_fit", float("nan")), 2), "fw b", f and round(f["b_fit"], 2),
              "sim t63", s.get("step", {}).get("t63_s"), "fw t63", f and f["t63_s"])
    print(len(lines), "lines;", sum(l.startswith("M") for l in lines), "M frames;", lines[-1][:60])
