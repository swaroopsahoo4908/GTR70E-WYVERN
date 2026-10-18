#!/usr/bin/env python3
"""GTR70E WYVERN (fin control), ground-test bench simulators for the suite (no Tk).

1. Static motor tester: any RASP .eng in Simulations/motors (F67W, F42T, F67C, G74W, F50T, G40W) on the
   motor test stand, through the stand's structural response and an HX711 load-cell chain. The
   DAQ model is the one built for the TVC-era stand (mount ring, aliasing, quantization, drift,
   calibration-slope residual), now driven by the real AeroTech curves.
2. Wind-tunnel Phase A bench: one control fin on the reflection plate, servo cradle on two 100 g
   TAL221 cells (60 mm apart along the chord) read by NAU7802s. The t2 sweep (-15..+15 deg in
   0.5 deg steps, 3 s dwell, last 2 s averaged) is simulated with cell noise, flow unsteadiness
   and the spanwise-moment crosstalk the thread-and-pulley calibration has to remove. It shows
   whether the bench resolves the differences RQ1/RQ2 ask about.
"""
from __future__ import annotations
import glob, math, os, sys
import numpy as np
from matplotlib.figure import Figure

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
for p in (SIM, os.path.join(SIM, "CFD")):
    if p not in sys.path: sys.path.insert(0, p)
import wf_core as C                                  # noqa: E402
from vlm import fin_vlm, helmbold, polhamus_Kv      # noqa: E402
from run_airfoil_cfd import cl_alpha_2d             # noqa: E402

_trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))

# ------------------------------------------------------------------------------ motors (.eng)
def load_eng(path):
    t, f, hdr = [0.0], [0.0], None
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith(";"): continue
        if hdr is None: hdr = ln.split(); continue
        a, b = ln.split()[:2]; t.append(float(a)); f.append(float(b))
    t, f = np.array(t), np.array(f)
    return dict(name=hdr[0], dia=float(hdr[1]), L=float(hdr[2]), delays=hdr[3], m_prop=float(hdr[4]) * 1000,
                m_tot=float(hdr[5]) * 1000, maker=hdr[6] if len(hdr) > 6 else "", t=t, f=f)

MOTOR_FILES = {os.path.splitext(os.path.basename(p))[0].replace("AeroTech_", "AeroTech "): p
               for p in sorted(glob.glob(os.path.join(SIM, "motors", "*.eng")))}
MOTOR_NAMES = list(MOTOR_FILES)

def motor_stats(name):
    m = load_eng(MOTOR_FILES[name]); It = float(_trapz(m["f"], m["t"])); tb = float(m["t"][-1])
    cls = "ABCDEFGHIJ"[int(max(0, math.floor(math.log2(It / 2.5) + 1)))] if It > 2.5 else "A"
    return dict(name=name, It=It, tb=tb, avg=It / tb, peak=float(m["f"].max()), cls=cls, m=m)

# stand + HX711 chain (from the TVC-era bench model)
HX711_SPS, HX711_BITS, HX711_GAIN = 80.0, 24, 128.0
CELL_SENS_MV_V, BRIDGE_EXC_V = 1.0, 5.0
ADC_FS_V = 0.5 * BRIDGE_EXC_V / HX711_GAIN
MOUNT_F_HZ, MOUNT_ZETA = 42.0, 0.035
ZERO_DRIFT_N_PER_S, CAL_SLOPE_SIGMA = 0.004, 0.006

def _mount_response(t, F, f_hz=MOUNT_F_HZ, zeta=MOUNT_ZETA):
    wn = 2 * np.pi * f_hz; dt = float(t[1] - t[0]); y = np.zeros_like(F); v = x = 0.0
    for i, Fi in enumerate(F):
        a = wn * wn * (Fi - x) - 2 * zeta * wn * v; v += a * dt; x += v * dt; y[i] = x
    return y

def _hx711(t_fine, sig, cell_kg, sps, rng):
    fs_N = cell_kg * 9.80665
    counts_fs = (CELL_SENS_MV_V * 1e-3 * BRIDGE_EXC_V / ADC_FS_V) * 2 ** (HX711_BITS - 1)
    lsb = fs_N / counts_fs
    ts = np.arange(0.0, float(t_fine[-1]), 1.0 / sps)
    x = sig[np.clip(np.searchsorted(t_fine, ts), 0, len(t_fine) - 1)]
    x = x + rng.normal(0, 0.0012 * fs_N, x.shape) + ZERO_DRIFT_N_PER_S * ts
    x = x + np.cumsum(rng.normal(0, 0.0004 * fs_N, x.shape)) / np.sqrt(max(len(x), 1))
    x = np.round(x * (1 + rng.normal(0, CAL_SLOPE_SIGMA)) / lsb) * lsb
    return ts, x, lsb, fs_N

def static_stand(name, cell_kg=10.0, sps=HX711_SPS, seed=0):
    st = motor_stats(name); m = st["m"]; rng = np.random.default_rng(seed)
    tf = np.arange(0.0, st["tb"] + 0.5, 2e-4)
    true_f = np.interp(tf, m["t"], m["f"], left=0, right=0)
    ts, rd, lsb, fs = _hx711(tf, _mount_response(tf, true_f), cell_kg, sps, rng)
    tru = np.interp(ts, m["t"], m["f"], left=0, right=0)
    info = dict(fs_N=fs, headroom=fs / st["peak"], lsb_N=lsb, aliased=MOUNT_F_HZ > sps / 2,
                It_meas=float(_trapz(np.clip(rd, 0, None), ts)), peak_meas=float(rd.max()))
    info["It_err_pct"] = 100 * (info["It_meas"] - st["It"]) / st["It"]
    info["peak_err_pct"] = 100 * (info["peak_meas"] - st["peak"]) / st["peak"]
    return ts, tru, rd, st, info

def motor_figure(name, cell_kg=10.0, sps=HX711_SPS, seed=0):
    ts, tru, rd, st, info = static_stand(name, cell_kg, sps, seed)
    fig = Figure(figsize=(9, 5.2), dpi=100); ax = fig.add_subplot(111)
    ax.plot(ts, rd, color="#9a9a9a", lw=0.9, label=f"load cell as logged ({sps:.0f} SPS, mount ring + HX711)")
    ax.plot(ts, tru, color="#2a6f97", lw=2.2, label="thrust (.eng)")
    ax.axhline(st["avg"], ls="--", color="#386641", lw=1, label=f"average {st['avg']:.1f} N")
    ax.axhline(st["peak"], ls=":", color="#bc4749", lw=1, label=f"peak {st['peak']:.1f} N")
    w = " (cell under-ranged)" if info["headroom"] < 1.1 else ""
    ax.set_title(f"{name}: {st['It']:.1f} N s ({st['cls']}), burn {st['tb']:.2f} s, case {st['m']['dia']:.0f} x {st['m']['L']:.0f} mm, "
                 f"{cell_kg:.0f} kg cell = {info['fs_N']:.0f} N FS ({info['headroom']:.1f}x){w}", fontsize=9.5)
    ax.text(0.98, 0.55, f"impulse error {info['It_err_pct']:+.1f} %   peak error {info['peak_err_pct']:+.1f} %\n"
            f"{info['lsb_N'] * 1000:.1f} mN per count   mount {MOUNT_F_HZ:.0f} Hz"
            + ("  (aliased at this rate)" if info["aliased"] else ""),
            transform=ax.transAxes, ha="right", va="top", fontsize=8, bbox=dict(fc="#f4f4f4", ec="#bbb"))
    ax.set_xlabel("t (s)"); ax.set_ylabel("thrust (N)"); ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout(); return fig

# ------------------------------------------------------------------------------ tunnel Phase A
LE_SUCTION = dict(flat_plate=0.5, double_wedge=0.0, NACA0006=0.6, NACA0012=0.9)   # as wf_fin_authority
X_PLATE_A = 0.090
CELL_FS_N = 0.1 * 9.80665        # TAL221 100 g
CELL_PITCH_MM = 60.0
NAU_SPS = 80.0
NAU_NOISE_FS = 2e-4              # rms, fraction of FS after the NAU7802 (assumed; measure on the bench)
FLOW_UNSTEADY = 0.015            # rms fraction of the fin load (fan + section turbulence)
CROSSTALK = 0.03                 # spanwise moment leaking into the normal-force sum before calibration

def fin_model(profile, H):
    v = fin_vlm(H, c=C.CFIN["root"], hinge_frac=C.CFIN["hinge_frac"])
    eta = cl_alpha_2d(profile) / (2 * math.pi)
    cna = v["CNa"] * helmbold(v["AR_wing"], eta) / helmbold(v["AR_wing"], 1.0)
    Kv = polhamus_Kv(cna, v["AR_wing"], math.atan(C.CFIN["root"] / H)) * (1 - LE_SUCTION[profile])
    Sf = C.CFIN["root"] * H / 2 * 1e-6
    x_cp = (v["xcp_c"] - C.CFIN["hinge_frac"]) * C.CFIN["root"]          # mm aft of the hinge
    return dict(cna=cna, Kv=Kv, Sf=Sf, x_cp_mm=x_cp, y_cp_mm=C.CFIN["gap"] + 0.33 * H, AR=v["AR_wing"])

def fin_force(m, delta_deg, V):
    d = math.radians(delta_deg); s = math.copysign(1, d) if d else 0.0; a = abs(d)
    q = 0.5 * 1.204 * V * V
    cn = m["cna"] * math.sin(a) * math.cos(a) ** 2 + m["Kv"] * math.cos(a) * math.sin(a) ** 2
    return s * q * m["Sf"] * cn          # plate boundary-layer loss applied by the caller

def tunnel_sweep(profile="NACA0006", H=40.0, V=12.0, dmax=15.0, step=0.5, dwell=3.0, avg_last=2.0, seed=0,
                 calibrated=True):
    m = fin_model(profile, H); rng = np.random.default_rng(seed)
    try:
        bl, _ = C.bl_effectiveness(H, X_PLATE_A, V)
    except Exception:
        bl = 1.0
    ds = np.arange(-dmax, dmax + 1e-9, step); rows = []
    tare_f, tare_a = rng.normal(0, 0.002 * CELL_FS_N, 2)
    for d in ds:
        N = fin_force(m, d, V) * bl
        n = int(dwell * NAU_SPS); k0 = int((dwell - avg_last) * NAU_SPS)
        Nt = N * (1 + rng.normal(0, FLOW_UNSTEADY, n))
        xc = m["x_cp_mm"]
        Ffore = Nt * (CELL_PITCH_MM / 2 - xc) / CELL_PITCH_MM
        Faft = Nt * (CELL_PITCH_MM / 2 + xc) / CELL_PITCH_MM
        if not calibrated:      # spanwise moment N*y_cp leaks into both cells
            leak = CROSSTALK * Nt * m["y_cp_mm"] / CELL_PITCH_MM
            Ffore = Ffore + leak; Faft = Faft + leak
        Ffore = Ffore + tare_f + rng.normal(0, NAU_NOISE_FS * CELL_FS_N, n)
        Faft = Faft + tare_a + rng.normal(0, NAU_NOISE_FS * CELL_FS_N, n)
        Ffore -= tare_f; Faft -= tare_a                   # tare run (hub only) removed
        s = (Ffore + Faft)[k0:]; diff = (Faft - Ffore)[k0:]
        Nm = float(s.mean()); se = float(s.std(ddof=1) / math.sqrt(len(s)))
        cp = float(diff.mean() / Nm * CELL_PITCH_MM / 2) if abs(Nm) > 4 * se else float("nan")
        rows.append(dict(delta=d, N_true=N, N_meas=Nm, N_se=se, cp_true=xc, cp_meas=cp))
    return rows, m, bl

def tunnel_figure(profile="NACA0006", H=40.0, V=12.0, seed=0, calibrated=True, compare=None):
    fig = Figure(figsize=(10, 5.4), dpi=100); a1 = fig.add_subplot(121); a2 = fig.add_subplot(122)
    profs = [profile] + [p for p in (compare or []) if p != profile]
    cols = dict(flat_plate="#555", double_wedge="#bc4749", NACA0006="#2a6f97", NACA0012="#386641")
    summary = []
    for p in profs:
        rows, m, bl = tunnel_sweep(p, H, V, seed=seed, calibrated=calibrated)
        d = np.array([r["delta"] for r in rows]); Nt = np.array([r["N_true"] for r in rows]) * 1000
        Nm = np.array([r["N_meas"] for r in rows]) * 1000; se = np.array([r["N_se"] for r in rows]) * 1000
        c = cols.get(p, None)
        a1.plot(d, Nt, color=c, lw=1.2, label=f"{p} model")
        a1.errorbar(d, Nm, yerr=2 * se, fmt=".", ms=3, color=c, alpha=0.7, label=f"{p} bench (2 se)")
        cpm = np.array([r["cp_meas"] for r in rows])
        a2.plot(d, cpm, ".", color=c, ms=4, label=f"{p} measured CP"); a2.axhline(m["x_cp_mm"], color=c, lw=0.8)
        slope = np.polyfit(d[np.abs(d) <= 5], Nm[np.abs(d) <= 5], 1)[0]
        summary.append(f"{p}: slope {slope:.2f} mN/deg, N(10) {np.interp(10, d, Nm):.1f} mN, se {np.median(se):.2f} mN")
    a1.set(xlabel="deflection (deg)", ylabel="normal force (mN)", title=f"Phase A: H{H:.0f} at {V:.0f} m/s, one fin on the plate")
    a1.grid(alpha=0.3); a1.legend(fontsize=7)
    a2.set(xlabel="deflection (deg)", ylabel="CP aft of the hinge (mm)", title="chordwise CP from the two cells")
    a2.grid(alpha=0.3); a2.legend(fontsize=7); a2.set_ylim(-15, 20)
    fig.suptitle(("calibrated (2x2 matrix applied)" if calibrated else "raw, before the thread-and-pulley calibration")
                 + "\n" + "\n".join(summary), fontsize=8)
    fig.tight_layout(); return fig, summary

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg")
    print(MOTOR_NAMES)
    for n in MOTOR_NAMES:
        st = motor_stats(n); print(n, round(st["It"], 1), round(st["avg"], 1), round(st["peak"], 1), st["tb"])
    f = motor_figure(MOTOR_NAMES[0]); f.savefig("/tmp/claude-0/bench_motor.png")
    f, s = tunnel_figure(compare=["double_wedge", "NACA0012", "flat_plate"]); f.savefig("/tmp/claude-0/bench_tunnel.png"); print(s)
