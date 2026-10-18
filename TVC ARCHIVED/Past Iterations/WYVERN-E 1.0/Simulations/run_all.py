#!/usr/bin/env python3
"""
XRIM-117 WYVERN-E -- master simulation driver (staged)
Run all:        python3 run_all.py all
Or per stage:   python3 run_all.py aero|fea|traj|pk|env1|env2|thermal|disp1|disp2|sens
Each stage persists results into results/results_summary.json (merged) and
intermediate arrays into results/*.npz so stages can run independently.
"""

import json, os, sys, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim import common as cm
from sim import aero, structures, trajectory as tj, guidance_pk as gp, auxiliary as aux

PLOTS, RES = "plots", "results"
os.makedirs(PLOTS, exist_ok=True); os.makedirs(RES, exist_ok=True)
JS = f"{RES}/results_summary.json"
t0 = time.time()
plt.rcParams.update({"figure.dpi": 130, "font.size": 9})


def merge_results(key, d):
    data = json.load(open(JS)) if os.path.exists(JS) else {}
    data[key] = d
    json.dump(data, open(JS, "w"), indent=2)


def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{PLOTS}/{name}.png", bbox_inches="tight")
    plt.close(fig); print(f"  [plot] {name}.png ({time.time()-t0:5.1f}s)")


# ============================================================ AERO
def stage_aero():
    M = np.linspace(0.05, 1.2, 200)
    comp = dict(friction=aero.cd_friction(M), base=aero.cd_base(M),
                fins=aero.cd_fin_profile(M), wave=aero.cd_wave(M))
    cd_tot = sum(comp.values())
    bw = aero.barrowman()
    merge_results("aero", {
        "CNa_total_per_rad": round(float(bw["cna_total"]), 3),
        "CNa_nose": round(float(bw["cna_nose"]), 3),
        "CNa_ring1": round(float(bw["cna_r1"]), 3),
        "CNa_ring2": round(float(bw["cna_r2"]), 3),
        "XN_mm": round(float(bw["xn"]) * 1000, 1),
        "SM_allup_cal": round(float(aero.stability_margin(cm.XCG_ALLUP)), 3),
        "SM_burnout_cal": round(float(aero.stability_margin(cm.XCG_BURNOUT)), 3),
        "CD0_M0.3": round(float(aero.cd0(0.3)), 4),
        "CD0_M0.5": round(float(aero.cd0(0.5)), 4),
        "CD0_M0.8": round(float(aero.cd0(0.8)), 4),
    })
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for k, v in comp.items():
        ax[0].plot(M, v, lw=1.2, label=k)
    ax[0].plot(M, cd_tot, "k", lw=2, label="CD_total")
    ax[0].set(xlabel="Mach", ylabel="CD (ref: body cross-section)",
              title="Zero-lift drag buildup -- 70mm PTD")
    ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)
    al = np.deg2rad(np.linspace(0, 15, 100))
    for m_ in (0.2, 0.4, 0.55):
        ax[1].plot(np.rad2deg(al), aero.cd_total(m_, al), lw=1.4, label=f"M={m_}")
    ax[1].set(xlabel="angle of attack [deg]", ylabel="CD", title="Drag polar (with induced)")
    ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
    save(fig, "01_aero_drag_buildup")

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    labels = ["Nose\n(slender body)", "Ring 2\n(mid canards)", "Ring 1\n(aft fins)"]
    vals = [bw["cna_nose"], bw["cna_r2"], bw["cna_r1"]]
    ax[0].bar(labels, vals, color=["#4878a8", "#a8784a", "#6a994e"])
    ax[0].set(ylabel="CN_alpha [/rad]",
              title=f"CN_alpha breakdown -- total {bw['cna_total']:.2f}/rad")
    for i, v in enumerate(vals):
        ax[0].text(i, v + .1, f"{v:.2f}", ha="center", fontsize=8)
    xcg = np.linspace(0.54, 0.64, 50)
    ax[1].plot(xcg * 1000, (bw["xn"] - xcg) / cm.D_REF, "k", lw=1.5)
    for x_, lbl in [(cm.XCG_ALLUP, "all-up"), (cm.XCG_BURNOUT, "burnout")]:
        sm = (bw["xn"] - x_) / cm.D_REF
        ax[1].plot(x_ * 1000, sm, "ro")
        ax[1].annotate(f"{lbl} {sm:.2f} cal", (x_ * 1000, sm),
                       textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax[1].axhspan(1.0, 2.0, alpha=.12, color="g")
    ax[1].set(xlabel="XCG [mm from nose]", ylabel="static margin [cal]",
              title=f"Stability margin (XN = {bw['xn']*1000:.0f} mm)")
    ax[1].grid(alpha=.3)
    save(fig, "02_aero_stability")


# ============================================================ FEA
def stage_fea():
    st = structures.run_all_cases()
    merge_results("structures", {
        "SF_euler_column": round(st["axial"]["SF_euler"], 1),
        "SF_shell_buckling": round(st["axial"]["SF_shell"], 1),
        "body_bend_sigma_MPa": round(st["bending"]["sigma_max"] / 1e6, 2),
        "body_bend_SF": round(st["bending"]["SF"], 1),
        "fin_R1_sigma_MPa": round(st["fin_r1"]["sigma"] / 1e6, 1),
        "fin_R1_SF": round(st["fin_r1"]["SF"], 2),
        "first_bending_Hz_freefree": round(st["f1_hz"], 1),
        "flutter_V_R1_ms": round(st["Vf_r1"], 1),
        "flutter_V_R2_ms": round(st["Vf_r2"], 1),
        "servo_margin_x": round(st["servo"]["margin"], 1),
    })
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6))
    b = st["bending"]
    ax[0].plot(b["x"] * 1000, b["shear"], lw=1.4)
    ax[0].set(xlabel="station [mm]", ylabel="shear [N]",
              title="Beam shear -- max-q maneuver (8 deg AoA)")
    ax[0].grid(alpha=.3)
    ax[1].plot(b["x"] * 1000, b["moment"], lw=1.4, color="#a23b3b")
    ax[1].set(xlabel="station [mm]", ylabel="bending moment [N m]",
              title=f"Moment (sigma_max = {b['sigma_max']/1e6:.2f} MPa)")
    ax[1].grid(alpha=.3)
    names = ["Euler\ncolumn", "Shell\nbuckle", "Body\nbend", "Fin R1\nroot", "Servo\nhinge"]
    sfs = [st["axial"]["SF_euler"], st["axial"]["SF_shell"], b["SF"],
           st["fin_r1"]["SF"], st["servo"]["margin"]]
    bars = ax[2].bar(names, sfs, color="#46788e")
    ax[2].axhline(1.5, color="r", ls="--", lw=1, label="SF = 1.5 req")
    ax[2].set_yscale("log"); ax[2].set(ylabel="safety factor", title="Safety factor summary")
    for r, v in zip(bars, sfs):
        ax[2].text(r.get_x() + r.get_width() / 2, v * 1.1, f"{v:.1f}x", ha="center", fontsize=7)
    ax[2].legend(fontsize=8)
    save(fig, "03_fea_loads")


# ============================================================ TRAJECTORIES
def stage_traj():
    bal = tj.point_mass_3dof(elev_deg=90.0, dt=0.005)                       # full stack
    boo = tj.point_mass_3dof(elev_deg=90.0, dt=0.005, motors="booster_only")  # test card
    tilt = tj.point_mass_3dof(elev_deg=80.0, azim_deg=90.0,
                              wind=np.array([3.0, 0, 0]), dt=0.005)
    pp = tj.pitch_plane_6dof(elev_deg=85.0, wind_x=4.0, t_max=8.0)
    np.savez(f"{RES}/traj.npz",
             **{f"bal_{k}": v for k, v in bal.items() if isinstance(v, np.ndarray)},
             **{f"boo_{k}": v for k, v in boo.items() if isinstance(v, np.ndarray)})
    merge_results("trajectory", {
        "fullstack_apogee_m": round(float(bal["apogee"]), 1),
        "fullstack_v_max_ms": round(float(bal["v_max"]), 1),
        "fullstack_M_max": round(float(bal["M_max"]), 3),
        "fullstack_q_max_kPa": round(float(bal["q_max"]) / 1000, 2),
        "fullstack_t_apogee_s": round(float(bal["t_apogee"] or 0), 1),
        "booster_only_apogee_m": round(float(boo["apogee"]), 1),
        "booster_only_v_max_ms": round(float(boo["v_max"]), 1),
        "booster_only_M_max": round(float(boo["M_max"]), 3),
        "tilt80_apogee_m": round(float(tilt["apogee"]), 1),
        "tilt80_downrange_m": round(float(np.hypot(*tilt["landing_xy"])), 1),
        "pp6dof_alpha_max_deg": round(float(np.max(np.abs(pp["alpha_deg"][pp["t"] > 0.6]))), 2),
    })
    fig, ax = plt.subplots(2, 2, figsize=(10, 7))
    ax[0, 0].plot(bal["t"], bal["z"], lw=1.4, label=f"full stack (apo {bal['apogee']:.0f} m)")
    ax[0, 0].plot(boo["t"], boo["z"], lw=1.4, label=f"booster only (apo {boo['apogee']:.0f} m)")
    ax[0, 0].plot(tilt["t"], tilt["z"], lw=1.2, ls="--",
                  label=f"80 deg rail + 3 m/s wind")
    ax[0, 0].set(xlabel="t [s]", ylabel="altitude [m]", title="Altitude profiles", xlim=(0, 120))
    ax[0, 0].legend(fontsize=7); ax[0, 0].grid(alpha=.3)
    ax[0, 1].plot(bal["t"], bal["V"], lw=1.2, label="full stack")
    ax[0, 1].plot(boo["t"], boo["V"], lw=1.2, label="booster only")
    ax[0, 1].set(xlabel="t [s]", ylabel="V [m/s]", xlim=(0, 40),
                 title=f"Velocity (full {bal['v_max']:.0f} m/s M{bal['M_max']:.2f} | "
                       f"boost {boo['v_max']:.0f} m/s M{boo['M_max']:.2f})")
    ax[0, 1].legend(fontsize=8); ax[0, 1].grid(alpha=.3)
    ax[1, 0].plot(bal["t"], bal["q"] / 1000, lw=1.2, label="full stack")
    ax[1, 0].plot(boo["t"], boo["q"] / 1000, lw=1.2, label="booster only")
    ax[1, 0].set(xlabel="t [s]", ylabel="q [kPa]", xlim=(0, 40),
                 title=f"Dynamic pressure (max {bal['q_max']/1000:.1f} kPa)")
    ax[1, 0].legend(fontsize=8); ax[1, 0].grid(alpha=.3)
    m_ = pp["t"] > 0.55
    ax[1, 1].plot(pp["t"][m_], pp["alpha_deg"][m_], lw=1.1, label="alpha")
    ax[1, 1].plot(pp["t"][m_], pp["theta_deg"][m_] - pp["theta_deg"][0], lw=1.1,
                  label="delta theta")
    ax[1, 1].set(xlabel="t [s]", ylabel="[deg]",
                 title="Pitch-plane rigid body: 4 m/s crosswind response")
    ax[1, 1].legend(fontsize=8); ax[1, 1].grid(alpha=.3)
    save(fig, "04_flight_paths")


# ============================================================ PK SAMPLES + MC
def stage_pk():
    sample_runs = {}
    fig = plt.figure(figsize=(10, 7))
    axp = fig.add_subplot(111, projection="3d")
    for kind, c in [("crossing", "#2a6f97"), ("inbound", "#bc4749"),
                    ("weave", "#6a994e"), ("hover", "#7b6d8d")]:
        miss, h = gp.fly_engagement(kind=kind, record=True, seeker_noise=False)
        sample_runs[kind] = round(float(miss), 2)
        axp.plot(h["px"], h["py"], h["pz"], color=c, lw=1.5,
                 label=f"{kind} (miss {miss:.2f} m)")
        axp.plot(h["tx"], h["ty"], h["tz"], color=c, lw=1.0, ls="--", alpha=.6)
    axp.set(xlabel="E [m]", ylabel="N [m]", zlabel="alt [m]",
            title="Sample PN engagements -- interceptor (solid) vs target (dashed)")
    axp.legend(fontsize=8)
    save(fig, "05_engagement_paths_3d")
    merge_results("pk_samples", sample_runs)


def stage_pkmc(half):
    misses = gp.monte_carlo(n=50)
    np.save(f"{RES}/misses_{half}.npy", misses)
    if half < 3:
        return
    misses = np.concatenate([np.load(f"{RES}/misses_{i}.npy") for i in (1, 2, 3)])
    np.save(f"{RES}/misses.npy", misses)
    data = json.load(open(JS)) if os.path.exists(JS) else {}
    sample_runs = data.get("pk_samples", {})
    radii = np.linspace(0.25, 10, 60)
    pk = gp.pk_vs_radius(misses, radii)
    merge_results("pk", {
        "n_runs": int(len(misses)),
        "miss_median_m": round(float(np.median(misses)), 2),
        "miss_p90_m": round(float(np.percentile(misses, 90)), 2),
        "Pk_capture_1m": round(float((misses <= 1.0).mean()), 3),
        "Pk_capture_2m": round(float((misses <= 2.0).mean()), 3),
        "Pk_capture_5m": round(float((misses <= 5.0).mean()), 3),
        "sample_miss": sample_runs,
    })
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].hist(np.clip(misses, 0, 15), bins=40, color="#46788e", edgecolor="k", lw=.3)
    ax[0].axvline(np.median(misses), color="r", ls="--",
                  label=f"median {np.median(misses):.2f} m")
    ax[0].set(xlabel="miss distance [m]", ylabel="count",
              title=f"Miss distance -- {len(misses)}-run MC, crossing target")
    ax[0].legend(fontsize=8)
    ax[1].plot(radii, pk, lw=1.6)
    for r_ in (1.0, 2.0, 5.0):
        ax[1].plot(r_, (misses <= r_).mean(), "ro", ms=4)
        ax[1].annotate(f"Pk({r_:.0f}m)={(misses<=r_).mean():.2f}",
                       (r_, (misses <= r_).mean()),
                       textcoords="offset points", xytext=(8, -4), fontsize=8)
    ax[1].set(xlabel="capture radius [m]", ylabel="Pk",
              title="Pk vs capture radius", ylim=(0, 1.05))
    ax[1].grid(alpha=.3)
    save(fig, "06_pk_curves")


RANGES = np.array([200, 350, 500, 650, 800])
ALTS = np.array([60, 120, 200, 300])


def stage_env(half):
    alts = ALTS[:2] if half == 1 else ALTS[2:]
    env = gp.engagement_envelope(RANGES, alts, n=12)
    np.save(f"{RES}/env_{half}.npy", env)
    if half == 2 and os.path.exists(f"{RES}/env_1.npy"):
        env_full = np.vstack([np.load(f"{RES}/env_1.npy"), env])
        merge_results("pk_envelope", {
            "ranges_m": RANGES.tolist(), "alts_m": ALTS.tolist(),
            "Pk_grid_2m_capture": np.round(env_full, 2).tolist(),
        })
        fig, ax = plt.subplots(figsize=(6.6, 4.4))
        im = ax.imshow(env_full, origin="lower", aspect="auto", cmap="RdYlGn",
                       vmin=0, vmax=1,
                       extent=[RANGES[0] - 75, RANGES[-1] + 75, ALTS[0] - 30, ALTS[-1] + 50])
        for i, a_ in enumerate(ALTS):
            for j, r_ in enumerate(RANGES):
                ax.text(r_, a_, f"{env_full[i,j]:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, label="Pk (2 m capture radius)")
        ax.set(xlabel="launch range to target track [m]", ylabel="target altitude [m]",
               title="Engagement envelope -- crossing Group-1 UAS, 12 m/s")
        save(fig, "07_pk_envelope")


# ============================================================ THERMAL
def stage_thermal():
    d = np.load(f"{RES}/traj.npz")
    bal = {k[4:]: d[k] for k in d.files if k.startswith("bal_")}
    Ms = np.linspace(0, 1.0, 100)
    Tw = aux.skin_temp_history(bal)
    merge_results("thermal", {
        "T_stag_M0.55_C": round(float(aux.stagnation_temp(0.55) - 273.15), 1),
        "T_stag_M1.0_C": round(float(aux.stagnation_temp(1.0) - 273.15), 1),
        "T_skin_max_C": round(float(Tw.max() - 273.15), 1),
    })
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ax[0].plot(Ms, aux.stagnation_temp(Ms) - 273.15, lw=1.4, label="stagnation")
    ax[0].plot(Ms, aux.recovery_temp(Ms) - 273.15, lw=1.4, label="recovery (r=0.89)")
    ax[0].axhline(70, color="r", ls="--", lw=1, label="PETG-CF Tg margin 70 C")
    ax[0].set(xlabel="Mach", ylabel="T [deg C]", title="Aerothermal limit check")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    msk = bal["t"] < 60
    ax[1].plot(bal["t"][msk], Tw[msk] - 273.15, lw=1.4)
    ax[1].set(xlabel="t [s]", ylabel="skin T [deg C]",
              title=f"Skin temp, lumped node x=0.5 m -- max {Tw.max()-273.15:.1f} C")
    ax[1].grid(alpha=.3)
    save(fig, "08_thermal")


# ============================================================ DISPERSION
def stage_disp(half):
    pts, apo = aux.dispersion_mc(n=30)
    np.savez(f"{RES}/disp_{half}.npz", pts=pts, apo=apo)
    if half == 2 and os.path.exists(f"{RES}/disp_1.npz"):
        d1 = np.load(f"{RES}/disp_1.npz")
        pts = np.vstack([d1["pts"], pts]); apo = np.concatenate([d1["apo"], apo])
        cep50 = aux.cep(pts)
        merge_results("dispersion", {
            "n_runs": int(len(apo)), "config": "booster_only, 88 deg rail, 4 m/s mean wind",
            "CEP_m": round(float(cep50), 1),
            "max_drift_m": round(float(np.linalg.norm(pts, axis=1).max()), 1),
            "apogee_mean_m": round(float(apo.mean()), 1),
            "apogee_std_m": round(float(apo.std()), 1),
        })
        fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
        ax[0].scatter(pts[:, 0], pts[:, 1], s=8, alpha=.6, color="#46788e")
        c = plt.Circle(pts.mean(axis=0), cep50, fill=False, color="r", ls="--",
                       label=f"CEP {cep50:.0f} m")
        ax[0].add_patch(c); ax[0].plot(0, 0, "k^", ms=8, label="pad")
        ax[0].set(xlabel="E [m]", ylabel="N [m]",
                  title=f"Landing dispersion -- {len(apo)}-run MC, 24 in chute")
        ax[0].axis("equal"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
        ax[1].hist(apo, bins=20, color="#6a994e", edgecolor="k", lw=.3)
        ax[1].set(xlabel="apogee [m]", ylabel="count",
                  title=f"Apogee spread (mean {apo.mean():.0f} +/- {apo.std():.0f} m)")
        save(fig, "09_dispersion")


# ============================================================ SENSITIVITY
def stage_sens():
    base, rows = aux.tornado_apogee()
    merge_results("sensitivity", {
        "apogee_base_m": round(float(base), 1),
        "tornado_delta_m": {n: [round(l, 1), round(h, 1)] for n, l, h in rows},
    })
    fig, ax = plt.subplots(figsize=(7, 3.6))
    names = [r[0] for r in rows]
    lo = [r[1] for r in rows]; hi = [r[2] for r in rows]
    y = np.arange(len(rows))
    ax.barh(y, hi, color="#6a994e", label="favorable")
    ax.barh(y, lo, color="#bc4749", label="adverse")
    ax.set_yticks(y); ax.set_yticklabels(names); ax.axvline(0, color="k", lw=1)
    ax.set(xlabel=f"delta apogee [m] about base {base:.0f} m",
           title="Apogee sensitivity tornado (full stack)")
    ax.legend(fontsize=8); ax.grid(alpha=.3, axis="x")
    save(fig, "10_sensitivity_tornado")


STAGES = dict(aero=stage_aero, fea=stage_fea, traj=stage_traj, pk=stage_pk,
              pkmc1=lambda: stage_pkmc(1), pkmc2=lambda: stage_pkmc(2),
              pkmc3=lambda: stage_pkmc(3),
              env1=lambda: stage_env(1), env2=lambda: stage_env(2),
              thermal=stage_thermal, disp1=lambda: stage_disp(1),
              disp2=lambda: stage_disp(2), sens=stage_sens)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    keys = list(STAGES) if which == "all" else [which]
    for k in keys:
        print(f"== stage {k} ==")
        STAGES[k]()
    print(f"done in {time.time()-t0:.1f}s")
