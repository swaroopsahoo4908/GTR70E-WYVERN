#!/usr/bin/env python3
"""Closes the loop between the simulator and the firmware's manoeuvre code: runs the predicted
manoeuvre in wf_flightsim, replays each axis's trace through the C++ ManeuverSeq/AuthorityMonitor
(replay.cpp, built from the flight headers), and compares the two sets of metrics.
    python3 sil_check.py        -> sil_check.json + a table on stdout"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, "..", "..", "..", "Simulations"))
sys.path.insert(0, SIM)
import wf_flightsim as F

def build():
    exe = os.path.join(HERE, "replay")
    subprocess.run(["g++", "-O2", "-std=c++17", "-I", os.path.join(HERE, "shim"), "-I", os.path.join(HERE, "..", "wyvern_fin"),
                    os.path.join(HERE, "replay.cpp"), "-o", exe], check=True, capture_output=True)
    return exe

def main(cases=((4.0, 0.5, 3), (0.0, 0.0, 1), (6.0, 1.2, 7))):
    exe = build(); veh = F.Vehicle(); tb = veh.motor["tb"]; out = []
    for wind, turb, seed in cases:
        for ax, axi in (("A", 0), ("B", 1)):
            r, H = F.simulate(veh, wind=wind, gust=0.0, turb=turb, seed=seed, gains=F.GAINS_FLIGHT,
                              ctrl_until="firmware", maneuver=F.maneuver_events(tb, ax))
            py = r["maneuver"]
            csv = os.path.join(HERE, f"_trace_{ax}.csv")
            tt = np.abs(H["th"]) * F.D2R
            np.savetxt(csv, np.column_stack([H["t"], H["th"] * F.D2R, H["q"] * F.D2R, H["dl"], H["qbar"], tt, H["z"]]),
                       delimiter=",", header="t,th,q,dl,qbar,tilt_total,alt", comments="", fmt="%.6f")
            fw = json.loads(subprocess.run([exe, csv, str(axi)], capture_output=True, text=True, check=True).stdout)
            d, s = py.get("doublet", {}), py.get("step", {})
            row = dict(wind=wind, turb=turb, axis=ax,
                       b_fit_py=d.get("b_fit"), b_fit_fw=fw["b_fit"], t_py=d.get("t_stat"), t_fw=fw["b_t"],
                       ach_py=s.get("achieved_deg"), ach_fw=fw["achieved_deg"], t63_py=s.get("t63_s"), t63_fw=fw["t63_s"],
                       finpd_py=s.get("fin_per_deg"), finpd_fw=fw["fin_per_deg"], sign_py=s.get("sign"), sign_fw=fw["step_sign"],
                       status_fw=fw["status"])
            out.append(row); os.remove(csv)
    json.dump(out, open(os.path.join(HERE, "sil_check.json"), "w"), indent=1, default=float)
    f = lambda v: "   -  " if v is None else f"{v:7.3f}"
    print(" wind ax |  b_fit py    fw |  t py    fw | achieved py   fw |  t63 py   fw | fin/deg py  fw")
    for r in out:
        print(f" {r['wind']:4.1f} {r['axis']}  |{f(r['b_fit_py'])}{f(r['b_fit_fw'])} |{f(r['t_py'])}{f(r['t_fw'])} |"
              f"{f(r['ach_py'])}{f(r['ach_fw'])} |{f(r['t63_py'])}{f(r['t63_fw'])} |{f(r['finpd_py'])}{f(r['finpd_fw'])}")
    return out

if __name__ == "__main__":
    main()
