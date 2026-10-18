#!/usr/bin/env python3
"""GTR70E WYVERN -- stabilizer planform trade (rev 3b): what happens to control authority, margin and
gust rejection when the rectangular stabilizers are cut to the same height (span) as the triangular
control fins, and when their chord is stretched AIM-54 style along the motor bay.
Writes plots_stabilizer/planform_trade.json. Uses the same models as wf_stabilizer.py."""
import sys, math, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf_core as C, wf_flightsim as F
import wf_stabilizer as S
H = 40.0
base_root = C.RECT_FIN["root"]; base_le = C.X_RECT_LE; base_span = C.RECT_FIN["span"]
mb_top_free = C.X_MB_TOP + 1.0   # stabilizer LE can start at the MB top (control fin TE is upstream of it)
out = []
def run(label, span, root, ballast, offset=45.0):
    C.RECT_FIN["root"] = root; C.RECT_FIN["tip"] = root
    C.X_RECT_LE = C.X_MOTOR_AFT - root - 1.0
    # extra blade mass for chord change (mass_properties only scales span from the CAD blade)
    extra = 4 * (root - base_root) * span * C.RECT_FIN["t"] * C.DENS["PETGCF"] / 1000
    xr = C.X_RECT_LE + root / 2
    keep = list(C.COTS)
    C.COTS = keep + [("stabilizer chord delta", extra, xr, root)]
    M0, cg, I, _ = C.mass_properties(None, 0.0, H, ballast, span)
    keepaz = C.RECT_FIN["az0_deg"]; C.RECT_FIN["az0_deg"] = offset
    st = C.stability(cg, H, span); st0 = C.stability(cg, H, span, interference=False)
    cd = S.control_derivs(span, offset, cg, st)
    v = F.Vehicle(rect_span=span, ballast_g=ballast)
    v.interf = S.interference(H, span, offset)
    on, _ = F.simulate(v, gains=F.GAINS_FLIGHT); off, _ = F.simulate(v, control=False)
    C.RECT_FIN["az0_deg"] = keepaz; C.COTS = keep
    r = dict(label=label, span=span, root=root, ballast=ballast, mass=round(M0 * 1000), SM=round(st["margin_cal"], 2),
             I=round(cd["I"], 3), inst_iso=round(cd["cmd_net"] / cd["cmd_iso"], 3), Cmd_net=round(cd["cmd_net"], 2),
             Cma=round(cd["cma"], 2), trim=round(cd["trim_ratio"], 3), arm=round(C.X_HINGE - cg, 1),
             rms_on=round(on["tilt_rms_deg"], 2), rms_off=round(off["tilt_rms_deg"], 2), max_on=round(on["tilt_max_deg"], 1),
             apogee=round(on["apogee_m"]), rail=round(on["rail_exit_v"], 1), sat=round(on["servo_rate_sat_s"], 3))
    r = {k: (float(v) if hasattr(v, 'dtype') else v) for k, v in r.items()}
    out.append(r); print(r)
run("rev 3: 45 x 81, 90 g", 45, 81, 90)
run("span = H: 40 x 81, 90 g", 40, 81, 90)
run("span = H: 40 x 81, 110 g (chosen)", 40, 81, 110)
run("40 x 81, 110 g, 22.5° offset", 40, 81, 110, offset=22.5)
run("AIM-54 in line: 40 x 81, 110 g, 0° offset", 40, 81, 110, offset=0.0)
run("AIM-54 long chord: 40 x 116, 90 g", 40, 116, 90)
run("AIM-54 long chord: 40 x 116, 150 g", 40, 116, 150)
C.RECT_FIN["root"] = base_root; C.RECT_FIN["tip"] = base_root; C.X_RECT_LE = base_le
json.dump(out, open(os.path.join(C.HERE, "plots_stabilizer", "planform_trade.json"), "w"), indent=1, default=float)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(16, 5))
labs = [r["label"] for r in out]; y = list(range(len(out)))
cols = ["#94a3b8", "#60a5fa", "#2563eb", "#f59e0b", "#dc2626", "#64748b", "#475569"]
ax[0].barh(y, [r["inst_iso"] for r in out], color=cols); ax[0].axvline(0, c="k", lw=0.8)
ax[0].set(title="installed / isolated control derivative", yticks=y); ax[0].set_yticklabels(labs, fontsize=8)
ax[1].barh(y, [r["SM"] for r in out], color=cols); ax[1].axvline(1.0, c="k", ls="--", lw=0.8)
ax[1].set(title="static margin at liftoff (cal)", yticks=y); ax[1].set_yticklabels([])
ax[2].barh(y, [r["rms_on"] for r in out], color=cols)
ax[2].scatter([r["rms_off"] for r in out], y, c="k", marker="|", s=250, zorder=5, label="fins locked")
ax[2].set(title="RMS tilt, gust case (deg); bar = fins active", yticks=y); ax[2].set_yticklabels([]); ax[2].legend(fontsize=8)
for a_ in ax: a_.invert_yaxis(); a_.grid(alpha=.3, axis="x")
fig.suptitle("Stabilizer planform trade: H = 40 mm control fins, F67-6W, pessimistic vortex model")
fig.tight_layout(); fig.savefig(os.path.join(C.HERE, "plots_stabilizer", "S4_planform_trade.png"), dpi=130)
print("wrote S4_planform_trade.png")
