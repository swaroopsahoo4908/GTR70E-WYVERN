#!/usr/bin/env python3
"""GTR70E WYVERN -- control-fin authority model: 4 aerofoil blocks x 5 fin heights.

This is the "simulated authority" half of the RQ1/RQ2 plan. Chain, per (profile, H):

  1. 2D section lift slope           CFD/run_airfoil_cfd.py  (vortex-panel, root chord)
  2. 3D isolated-fin loads           CFD/vlm.py              (horseshoe VLM, reflection plane)
     section shape enters through the Helmbold ratio  helm(AR, eta) / helm(AR, 1)
  3. fin on body                     slender-body K_W(B) (wf_core.K_WB), k_W(B)+k_B(W) = K_W(B)
  4. body boundary layer             wf_core.bl_effectiveness (1/7-power turbulent profile)
  5. interference on the fixed fins  single trailing-vortex + body image (Nielsen-type), induced
                                     normal force on the 45-deg rectangular fins, strip theory
  6. moments about the flight CG     pitch pair (level A) and yaw pair (level B) separately
  7. closed loop                     wf_flightsim with the net control derivative, gust case

Outputs -> plots_authority/ :
  authority_matrix.csv / .json      every number per (profile, H)
  A_isolated_vs_H.png               isolated-fin normal-force slope (what the tunnel measures)
  B_net_authority_vs_H.png          flight-installed Cm_delta incl. interference (what flies)
  C_closed_loop_vs_H.png            gust-rejection RMS tilt, apogee, hinge load vs H
  D_tunnel_predictions.png          expected balance loads at the tunnel speed
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C
sys.path.insert(0, os.path.join(C.HERE, "CFD"))
from vlm import fin_vlm, helmbold, polhamus_Kv
from run_airfoil_cfd import cl_alpha_2d

OUT = os.path.join(C.HERE, "plots_authority"); os.makedirs(OUT, exist_ok=True)
MOTOR = C.FLIGHT_MOTOR
V_REF = 55.0          # m/s, mid-burn reference airspeed (F67), sets BL thickness
V_TUNNEL = 7.0        # m/s, Phase B: 200 x 200 mm section, Cloudline T8 (measure; 6-8 expected)
V_TUNNEL_A = 12.0     # m/s, Phase A: stock 100 x 100 section, Cloudline T8 via 100 sq -> 8 in (measure)
X_PLATE_A = 0.090     # m, reflection-plate leading edge to the fin hinge
LE_SUCTION = dict(flat_plate=0.5, double_wedge=0.0, NACA0006=0.6, NACA0012=0.9)
# ^ fraction of leading-edge suction retained (1 = fully attached, no vortex lift). Hypotheses,
#   not data: sharp double-wedge LE sheds a LE vortex (Polhamus vortex lift), the 12 % NACA LE
#   mostly holds suction. The tunnel measurement of CN(delta) curvature is what pins these.

def authority_table(cg_mm, rect_span, profiles=C.CFIN_PROFILES, heights=C.CFIN_HEIGHTS):
    rows = []
    d = C.OD; Aref = math.pi * d * d / 4
    cla = {p: cl_alpha_2d(p) for p in profiles}
    for H in heights:
        v = fin_vlm(H, c=C.CFIN["root"], hinge_frac=C.CFIN["hinge_frac"])
        AR = v["AR_wing"]; Sf = C.CFIN["root"] * H / 2
        tau = C.R / (C.R + C.CFIN["gap"] + H)
        K = C.K_WB(tau)
        bl_f, dbl = C.bl_effectiveness(H, C.X_HINGE_A / 1000, V_REF)
        bl_t, dbl_t = C.bl_effectiveness(H, 0.21, V_TUNNEL)   # Phase B model: 100 mm nose + 112 mm CT top to hinge
        bpr = 0.70
        I = C.vortex_interference(H, rect_span, bprime=bpr)
        yv = C.R + C.CFIN["gap"] + bpr * H
        for p in profiles:
            eta = cla[p] / (2 * math.pi)
            cna = v["CNa"] * helmbold(AR, eta) / helmbold(AR, 1.0)      # per fin, ref S_f
            Kv = polhamus_Kv(cna, AR, math.atan(C.CFIN["root"] / H)) * (1 - LE_SUCTION[p])
            d10 = math.radians(10)
            cn10_lin = cna * d10
            cn10 = cna * math.sin(d10) * math.cos(d10) ** 2 + Kv * math.cos(d10) * math.sin(d10) ** 2
            # pitch-pair control derivative about the CG (per rad, ref A_ref and d)
            cnd_pair = 2 * cna * Sf / Aref * K * bl_f
            armA = (C.X_HINGE_A - C.CFIN["hinge_frac"] * C.CFIN["root"] + v["xcp_c"] * C.CFIN["root"] - cg_mm) / d
            armB = (C.X_HINGE_B - C.CFIN["hinge_frac"] * C.CFIN["root"] + v["xcp_c"] * C.CFIN["root"] - cg_mm) / d
            x_rect = C.barrowman_fin_xcp(C.RECT_FIN["root"], C.RECT_FIN["tip"], rect_span, 0, C.X_RECT_LE)
            arm_r = (x_rect - cg_mm) / d
            cmd_iso_A = cnd_pair * armA
            cmd_net_A = cnd_pair * (armA + I * arm_r)
            cmd_net_B = cnd_pair * (armB + I * arm_r)
            hm_per_deg = cna * Sf * 1e-6 * v["hinge_arm_c"] * C.CFIN["root"] * 1e-3 * math.radians(1)  # N m per (Pa deg)
            # tunnel: isolated, body present (test article), no fixed fins
            q_t = 0.5 * 1.204 * V_TUNNEL ** 2
            N_t_10 = q_t * Sf * 1e-6 * (cn10 if True else cn10_lin) * K * bl_t * 2   # pair, at 10 deg
            # Phase A: one fin on the reflection plate (image = the other half), no body: K = 1
            q_a = 0.5 * 1.204 * V_TUNNEL_A ** 2
            bl_a, _ = C.bl_effectiveness(H, X_PLATE_A, V_TUNNEL_A)
            N_a_10 = q_a * Sf * 1e-6 * cn10 * bl_a
            rows.append(dict(profile=p, H_mm=H, AR=round(AR, 3), Cla_2d=round(cla[p], 3),
                             CNa_fin_isolated=round(cna, 4), K_WB=round(K, 3),
                             BL_eff_flight=round(bl_f, 3), BL_delta_mm=round(dbl, 1),
                             BL_eff_tunnel=round(bl_t, 3), xcp_c=round(v["xcp_c"], 3),
                             hinge_arm_c=round(v["hinge_arm_c"], 3), Kv_vortex=round(Kv, 3),
                             CN10_nonlin_over_lin=round(cn10 / cn10_lin, 3),
                             interference_ratio=round(I, 4), vortex_y_mm=round(yv, 1),
                             CNd_pair=round(cnd_pair, 4), arm_A_cal=round(armA, 3), arm_B_cal=round(armB, 3),
                             arm_rect_cal=round(arm_r, 3),
                             Cmd_isolated_A=round(cmd_iso_A, 4), Cmd_net_A=round(cmd_net_A, 4),
                             Cmd_net_B=round(cmd_net_B, 4),
                             hinge_Nm_per_kPa_deg=round(hm_per_deg * 1000, 6),
                             tunnel_pair_N_at10deg=round(N_t_10, 4),
                             tunnelA_fin_N_at10deg=round(N_a_10, 4),
                             tunnelA_CP_from_hinge_mm=round((v["xcp_c"] - C.CFIN["hinge_frac"]) * C.CFIN["root"], 2)))
    return rows

def closed_loop(rows, profile, rect_span):
    import wf_flightsim as F
    out = []
    for r in [r for r in rows if r["profile"] == profile]:
        H = r["H_mm"]
        veh = F.Vehicle(MOTOR, H=H, rect_span=rect_span,
                        profile_eta=r["CNa_fin_isolated"] / fin_vlm(H)["CNa"])
        res, _ = F.simulate(veh, wind=4.0, gust=4.0, dt=0.001, gains=F.GAINS_FLIGHT)
        veh.interf *= 0.5
        res_h, _ = F.simulate(veh, wind=4.0, gust=4.0, dt=0.001, gains=F.GAINS_FLIGHT)
        out.append(dict(H_mm=H, tilt_rms=res["tilt_rms_deg"], tilt_max=res["tilt_max_deg"],
                        apogee=res["apogee_m"], hinge_max=res["max_hinge_Nm"],
                        defl_max=res["defl_max_deg"], sat=res["servo_rate_sat_s"],
                        tilt_rms_half_interf=res_h["tilt_rms_deg"]))
    return out

if __name__ == "__main__":
    import wf_flightsim as F
    M0, cg0, I0, _ = C.mass_properties(MOTOR, 0.0)
    rs = C.RECT_FIN["span"]
    rows = authority_table(cg0, rs, heights=C.CFIN_HEIGHTS_SIM)
    with open(os.path.join(OUT, "authority_matrix.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    cols = dict(flat_plate="#6d597a", double_wedge="#bc4749", NACA0006="#2a6f97", NACA0012="#386641")
    Hs = C.CFIN_HEIGHTS_SIM
    # A: isolated fin
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for p in C.CFIN_PROFILES:
        rr = [r for r in rows if r["profile"] == p]
        ax[0].plot(Hs, [r["CNa_fin_isolated"] * r["K_WB"] for r in rr], "o-", c=cols[p], label=p)
        ax[1].plot(Hs, [r["tunnelA_fin_N_at10deg"] * 1000 for r in rr], "o-", c=cols[p], label=f"{p}, Phase A single fin")
        ax[1].plot(Hs, [r["tunnel_pair_N_at10deg"] * 1000 for r in rr], ":", c=cols[p])
    ax[0].set(xlabel="fin height H (mm)", ylabel="CNα fin-on-body (per rad, ref fin area)", title="Isolated fin on body (VLM x K_W(B))")
    ax[1].set(xlabel="fin height H (mm)", ylabel="normal force at δ=10° (mN)", title=f"Tunnel: Phase A fin at {V_TUNNEL_A:.0f} m/s (solid), Phase B pair at {V_TUNNEL:.0f} m/s (dotted)")
    for a in ax: a.grid(alpha=.3); a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "A_isolated_vs_H.png"), dpi=130); plt.close(fig)
    # B: net authority
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for p in C.CFIN_PROFILES:
        rr = [r for r in rows if r["profile"] == p]
        ax[0].plot(Hs, [r["Cmd_net_A"] for r in rr], "o-", c=cols[p], label=f"{p} net")
        ax[0].plot(Hs, [r["Cmd_isolated_A"] for r in rr], ":", c=cols[p])
    rr = [r for r in rows if r["profile"] == "NACA0006"]
    ax[1].plot(Hs, [r["interference_ratio"] for r in rr], "o-k", label="pessimistic (single rolled-up vortex)")
    ax[1].plot(Hs, [0.5 * r["interference_ratio"] for r in rr], "o--", c="gray", label="half strength (partly rolled-up sheet)")
    ax[1].legend(fontsize=8)
    for a_ in ax: a_.axvspan(min(C.CFIN_HEIGHTS), max(C.CFIN_HEIGHTS), color="#e09f3e", alpha=0.08)
    ax[0].set(xlabel="fin height H (mm)", ylabel="|Cmδ| pitch pair about CG (per rad)", title="Installed authority (solid = with fixed-fin vortex interference, dotted = without)")
    ax[1].set(xlabel="fin height H (mm)", ylabel="induced fixed-fin force / control force", title="Control-fin vortex on the 45° fixed fins")
    for a in ax: a.grid(alpha=.3)
    ax[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "B_net_authority_vs_H.png"), dpi=130); plt.close(fig)
    # C: closed loop for every profile
    cl = {p: closed_loop(rows, p, rs) for p in C.CFIN_PROFILES}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    for p in C.CFIN_PROFILES:
        ax[0].plot(Hs, [c["tilt_rms"] for c in cl[p]], "o-", c=cols[p], label=p)
        ax[0].plot(Hs, [c["tilt_rms_half_interf"] for c in cl[p]], ":", c=cols[p])
        ax[1].plot(Hs, [c["apogee"] for c in cl[p]], "o-", c=cols[p], label=p)
        ax[2].plot(Hs, [c["hinge_max"] * 1000 for c in cl[p]], "o-", c=cols[p], label=p)
    ax[0].set(xlabel="H (mm)", ylabel="RMS tilt, rail exit -> burnout+2 s (deg)", title="Closed-loop gust rejection (lower = more authority)")
    ax[1].set(xlabel="H (mm)", ylabel="apogee (m)", title="Apogee cost of fin height")
    ax[2].set(xlabel="H (mm)", ylabel="peak hinge moment (mN·m)", title=f"Servo load vs {C.SERVO['name']} stall ≈ {C.SERVO['torque_kgcm'][7.4]*98.07:.0f} mN·m at 7.4 V")
    for a in ax: a.grid(alpha=.3); a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "C_closed_loop_vs_H.png"), dpi=130); plt.close(fig)
    # selection per profile: H* = argmax |Cmd_net_A| (open-loop simulated authority)
    sel = {}
    for p in C.CFIN_PROFILES:
        rr = [r for r in rows if r["profile"] == p and r["H_mm"] in C.CFIN_HEIGHTS]
        hstar = max(rr, key=lambda r: r["Cmd_net_A"])["H_mm"]
        clt = [c for c in cl[p] if c["H_mm"] in C.CFIN_HEIGHTS]
        hcl = min(clt, key=lambda c: c["tilt_rms"])["H_mm"]
        inc = C.CFIN_HEIGHTS[1] - C.CFIN_HEIGHTS[0]
        sel[p] = dict(H_star_open_loop=hstar, H_star_closed_loop=hcl,
                      flight_heights=[hstar - inc, hstar, hstar + inc],
                      monotonic=bool(all(b["Cmd_net_A"] > a_["Cmd_net_A"] for a_, b in zip(
                          [r for r in rows if r["profile"] == p][:-1], [r for r in rows if r["profile"] == p][1:]))))
    json.dump(dict(cg_mm=cg0, rect_span=rs, motor=MOTOR, rows=rows, closed_loop=cl, selection=sel),
              open(os.path.join(OUT, "authority_matrix.json"), "w"), indent=2, default=float)
    for r in rows:
        if r["profile"] == "NACA0006":
            print({k: r[k] for k in ("H_mm", "CNa_fin_isolated", "K_WB", "BL_eff_flight", "interference_ratio", "Cmd_isolated_A", "Cmd_net_A", "Cmd_net_B")})
    print(json.dumps(sel, indent=1))
    for p in cl: print(p, [(c["H_mm"], round(c["tilt_rms"], 2), round(c["apogee"])) for c in cl[p]])
