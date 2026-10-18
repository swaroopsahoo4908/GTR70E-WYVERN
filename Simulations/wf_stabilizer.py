#!/usr/bin/env python3
"""GTR70E WYVERN -- SQ1: what do the rectangular stabilizers do to the control fins?

The stabilizers (fixed rectangular fins along the motor) buy static margin, but they sit in the
trailing vortices of the lifting control fins. The downwash those vortices put on the
stabilizers produces a force that opposes the control moment, so the installed control
derivative is smaller than the isolated one. This script sweeps stabilizer span and azimuth
offset and reports, per configuration:

  static margin (liftoff / burnout), with and without the interference term
  interference ratio I = induced stabilizer force / control-pair force
  installed / isolated control derivative            Cm_delta,net / Cm_delta,iso
  control power   alpha_trim / delta = Cm_delta,net / Cm_alpha   (how hard the fins can turn it)
  closed-loop gust case (4 m/s wind + 4 m/s 1-cos gust) with the flight gains: RMS / max tilt,
  drift, apogee, and the same with the fins locked (passive only)
  tunnel Phase B predictions at the measured heights: pair side force with stabilizers off/on,
  and the yaw-sweep restoring-moment slope the strut rotation measures

Outputs -> plots_stabilizer/ : stabilizer_sweep.csv/.json, S1_margin_interference.png,
S2_closed_loop.png, S3_tunnel_phaseB.png
"""
from __future__ import annotations
import csv, json, math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C
import wf_flightsim as F

OUT = os.path.join(C.HERE, "plots_stabilizer"); os.makedirs(OUT, exist_ok=True)
MOTOR = C.FLIGHT_MOTOR
H = C.CFIN_H_NOMINAL
V_TUNNEL_B = 7.0             # m/s, 200 x 200 section with the Cloudline T8 (measure; 6-8 expected)
PHASE_B_HEIGHTS = [35.0, 40.0, 45.0]

def interference(H_, span, off):
    if span <= 0.5:
        return 0.0
    return C.vortex_interference(H_, span, offset_deg=off)

def static(span, off, t):
    """Margin with the interference evaluated at this azimuth offset (stability() reads the
    module-level az0, so it is set for the call and restored)."""
    M, cg, I_, _ = C.mass_properties(MOTOR, t, H, None, span)
    keep = C.RECT_FIN["az0_deg"]; C.RECT_FIN["az0_deg"] = off
    try:
        if span <= 0.5:
            st = C.stability(cg, H, 1e-3, interference=False)
            st_nointerf = st
        else:
            st = C.stability(cg, H, span, interference=True)
            st_nointerf = C.stability(cg, H, span, interference=False)
    finally:
        C.RECT_FIN["az0_deg"] = keep
    return M, cg, st, st_nointerf

def control_derivs(span, off, cg, st):
    d = C.OD; Aref = math.pi * d * d / 4
    g = C.cfin_geom(H)
    import sys; sys.path.insert(0, os.path.join(C.HERE, "CFD"))
    from vlm import fin_vlm
    v = fin_vlm(H, c=C.CFIN["root"], hinge_frac=C.CFIN["hinge_frac"])
    K = C.K_WB(C.R / (C.R + C.CFIN["gap"] + H))
    cnd_pair = 2 * v["CNa"] * g["area"] / Aref * K
    x_c = C.X_HINGE - C.CFIN["hinge_frac"] * g["root"] + v["xcp_c"] * g["root"]
    arm_c = (x_c - cg) / d
    I = interference(H, span, off)
    x_r = C.barrowman_fin_xcp(C.RECT_FIN["root"], C.RECT_FIN["tip"], max(span, 1e-3), 0, C.X_RECT_LE)
    arm_r = (x_r - cg) / d
    cmd_iso = cnd_pair * arm_c
    cmd_net = cnd_pair * (arm_c + I * arm_r)
    cma = st["cna"] * st["margin_cal"]               # restoring, per rad (ref A, d)
    return dict(I=I, cmd_iso=cmd_iso, cmd_net=cmd_net, cma=cma,
                trim_ratio=cmd_net / cma if cma > 1e-6 else float("nan"),
                cnd_pair=cnd_pair, x_c=x_c, x_r=x_r)

def closed_loop(span, off):
    veh = F.Vehicle(MOTOR, H=H, rect_span=max(span, 1e-3))
    veh.interf = interference(H, span, off)
    on, _ = F.simulate(veh, wind=4.0, gust=4.0, dt=0.001, gains=F.GAINS_FLIGHT)
    off_, _ = F.simulate(veh, wind=4.0, gust=4.0, dt=0.001, gains=F.GAINS_FLIGHT, control=False)
    return on, off_

def tunnel_phase_b(span, off=45.0):
    """Expected strut-balance readings for the full four-fin model, one pair at +10 deg.
    Stabilizers-off vs on isolates the induced stabilizer force: dN / N_off = I."""
    rows = []
    q = 0.5 * 1.204 * V_TUNNEL_B ** 2
    import sys; sys.path.insert(0, os.path.join(C.HERE, "CFD"))
    from vlm import fin_vlm
    for Hh in PHASE_B_HEIGHTS:
        g = C.cfin_geom(Hh)
        v = fin_vlm(Hh, c=C.CFIN["root"], hinge_frac=C.CFIN["hinge_frac"])
        K = C.K_WB(C.R / (C.R + C.CFIN["gap"] + Hh))
        N_off = 2 * q * g["area"] * 1e-6 * v["CNa"] * K * math.radians(10)
        I = interference(Hh, span, off)
        rows.append(dict(H_mm=Hh, span_mm=span, N_off_mN=N_off * 1e3, N_on_mN=N_off * (1 + I) * 1e3,
                         dN_mN=N_off * I * 1e3, I=I))
    return rows

def tunnel_yaw_slope(span):
    """Side-force slope of the whole model per degree of strut rotation (body + both fin sets),
    which the Phase B yaw sweep measures and which sets the static-margin check."""
    q = 0.5 * 1.204 * V_TUNNEL_B ** 2
    st = C.stability(500.0, H, max(span, 1e-3), interference=span > 0.5)
    return q * C.A_REF * st["cna"] * math.radians(1) * 1e3   # mN/deg

if __name__ == "__main__":
    rows = []
    for off in C.STAB_OFFSETS_DEG:
        for sp in C.STAB_SPANS_SIM:
            M0, cg0, st0, st0n = static(sp, off, 0.0)
            Mb, cgb, stb, _ = static(sp, off, 99.0)
            cd = control_derivs(sp, off, cg0, st0)
            run_cl = (off == 45.0) or (sp == C.RECT_FIN["span"])
            r = dict(offset_deg=off, span_mm=sp, liftoff_g=round(M0 * 1000, 1), cg_mm=round(cg0, 1),
                     xcp_mm=round(st0["xcp"], 1),
                     SM_liftoff_cal=round(st0["margin_cal"], 3), SM_liftoff_no_interf=round(st0n["margin_cal"], 3),
                     SM_burnout_cal=round(stb["margin_cal"], 3),
                     interference_ratio=round(cd["I"], 4),
                     Cmd_iso=round(cd["cmd_iso"], 4), Cmd_net=round(cd["cmd_net"], 4),
                     installed_over_isolated=round(cd["cmd_net"] / cd["cmd_iso"], 3),
                     Cma=round(float(cd["cma"]), 3), trim_alpha_per_delta=round(cd["trim_ratio"], 3))
            if run_cl:
                on, lk = closed_loop(sp, off)
                r.update(tilt_rms_ctrl=round(on["tilt_rms_deg"], 2), tilt_max_ctrl=round(on["tilt_max_deg"], 2),
                         drift_ctrl_m=round(on["drift_m"], 1), apogee_ctrl_m=round(on["apogee_m"], 1),
                         defl_max_deg=round(on["defl_max_deg"], 1),
                         tilt_rms_locked=round(lk["tilt_rms_deg"], 2), tilt_max_locked=round(lk["tilt_max_deg"], 2),
                         apogee_locked_m=round(lk["apogee_m"], 1))
            r = {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in r.items()}
            rows.append(r); print({k: r[k] for k in ("offset_deg", "span_mm", "SM_liftoff_cal", "interference_ratio",
                                                   "installed_over_isolated", "trim_alpha_per_delta")},
                                  r.get("tilt_rms_ctrl"), r.get("tilt_rms_locked"))
    keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[-1].keys()).index(k) if k in rows[-1] else 99)
    with open(os.path.join(OUT, "stabilizer_sweep.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    tb = {f"span{int(s)}": tunnel_phase_b(s) for s in C.STAB_SPANS_WT}
    yaw = {f"span{int(s)}": round(tunnel_yaw_slope(s), 2) for s in [0.0] + C.STAB_SPANS_WT}
    json.dump(dict(H=H, motor=MOTOR, rows=rows, tunnel_phase_b=tb, tunnel_yaw_slope_mN_per_deg=yaw,
                   V_tunnel_B=V_TUNNEL_B), open(os.path.join(OUT, "stabilizer_sweep.json"), "w"), indent=1)

    # ---- S1: margin and interference vs span (one line per offset)
    cols = {0.0: "#bc4749", 22.5: "#e09f3e", 45.0: "#2a6f97"}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    for off in C.STAB_OFFSETS_DEG:
        rr = [r for r in rows if r["offset_deg"] == off]
        sp = [r["span_mm"] for r in rr]
        ax[0].plot(sp, [r["SM_liftoff_cal"] for r in rr], "o-", c=cols[off], label=f"offset {off:g}°")
        ax[1].plot(sp, [r["interference_ratio"] for r in rr], "o-", c=cols[off], label=f"offset {off:g}°")
        ax[2].plot(sp, [r["trim_alpha_per_delta"] for r in rr], "o-", c=cols[off], label=f"offset {off:g}°")
    r45 = [r for r in rows if r["offset_deg"] == 45.0]
    ax[0].plot([r["span_mm"] for r in r45], [r["SM_liftoff_no_interf"] for r in r45], ":", c="k", label="45°, no interference")
    ax[0].axhline(0.9, c="gray", ls="--", lw=0.8); ax[0].axhline(0, c="k", lw=0.6)
    ax[0].set(xlabel="stabilizer span (mm)", ylabel="static margin at liftoff (cal)", title="Margin bought by the stabilizers")
    ax[1].set(xlabel="stabilizer span (mm)", ylabel="I = induced stabilizer force / control force", title="Control-fin vortex on the stabilizers")
    ax[2].set(xlabel="stabilizer span (mm)", ylabel="α_trim / δ", title="Control power (trim α per unit deflection)")
    ax[2].set_ylim(0, 1.5)
    for a in ax: a.grid(alpha=.3); a.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S1_margin_interference.png"), dpi=130); plt.close(fig)

    # ---- S2: closed loop vs span at 45 deg
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    sp = [r["span_mm"] for r in r45]
    ax[0].plot(sp, [r["tilt_rms_ctrl"] for r in r45], "o-", c="#2a6f97", label="fins active")
    ax[0].plot(sp, [r["tilt_rms_locked"] for r in r45], "s--", c="#bc4749", label="fins locked")
    ax[0].set(xlabel="stabilizer span (mm)", ylabel="RMS tilt, gust case (deg)", title="Gust rejection vs stabilizer span (45° offset)")
    ax[0].set_ylim(0, 30)
    ax[1].plot(sp, [r["apogee_ctrl_m"] for r in r45], "o-", c="#386641")
    ax[1].set(xlabel="stabilizer span (mm)", ylabel="apogee (m), fins active", title="Apogee cost of stabilizer drag + mass")
    for a in ax: a.grid(alpha=.3)
    ax[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S2_closed_loop.png"), dpi=130); plt.close(fig)

    # ---- S3: tunnel Phase B predictions
    fig, ax = plt.subplots(figsize=(7, 4.5))
    w = 1.2
    for k, (key, rr) in enumerate(tb.items()):
        Hs = [r["H_mm"] for r in rr]
        if k == 0:
            ax.bar([h - w for h in Hs], [r["N_off_mN"] for r in rr], width=w, color="#999", label="stabilizers off")
        ax.bar([h + k * w for h in Hs], [r["N_on_mN"] for r in rr], width=w, label=f"stabilizers on, {key}")
    ax.set(xlabel="control fin height H (mm)", ylabel="pair side force at δ = 10° (mN)",
           title=f"Phase B balance, {V_TUNNEL_B:g} m/s (pessimistic vortex model)")
    ax.grid(alpha=.3, axis="y"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S3_tunnel_phaseB.png"), dpi=130); plt.close(fig)
    print(json.dumps(dict(tunnel_phase_b=tb, yaw=yaw), indent=1))
