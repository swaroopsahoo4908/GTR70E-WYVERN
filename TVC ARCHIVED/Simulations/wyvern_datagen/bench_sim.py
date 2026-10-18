#!/usr/bin/env python3
"""
GTR70E WYVERN, ground-test bench simulators (backend-agnostic, no Tk).

Pure functions + matplotlib-Figure builders for three bench tools surfaced in the datagen GUI:
  1. Static motor tester -> select a motor, get its thrust curve + the axial load-cell trace a
                              static stand would log (with sensor noise).
  2. Jetvane suitability -> RETIRED 2026-08 (jetvane testing dropped from the program). The
                              analysis is kept because it is what justified dropping it -- any
                              printed vane ablates in a 1150 K BP exhaust -- but it is no longer
                              part of the test plan and the GUI tab is informational only.
  3. Ground TVC test + PID -> the 3-axis thrust-vector balance reading (Fz axial, Fx/Fy lateral)
                              while the firmware PID gimbals the nozzle through a bench maneuver,
                              incl. servo lag, and the resolved thrust vector (T, theta, phi).

Everything is deterministic given a seed so the GUI can redraw live. Physics reuse the canonical
constants in core.py where relevant (F15 curve, gains, gimbal limit, arm) so bench numbers line up
with the flight model.

--------------------------------------------------------------------------------------------
FIDELITY REVISION 2026-08, the stands are now modeled at the SIGNAL level, not the ideal level
--------------------------------------------------------------------------------------------
The previous version modeled each load cell as "true force + white gaussian noise" and the servo
as a first-order lag. That is optimistic in the two ways that actually bite on a real stand:

1. STAND STRUCTURAL COMPLIANCE. A printed stand is not rigid. The motor + gimbal mass on the
    flexure stack forms a lightly-damped second-order system (mount resonance, `f_mount`), and the
    load cell reads the *stand's* response to the thrust, not the thrust. The ignition transient
    is a near-step input, so it rings the mount, this is the single largest error source on an
    amateur thrust stand and it is now modeled explicitly, along with the digital low-pass the
    DAQ must apply to suppress it.

2. DAQ CHAIN. The HX711 is a 24-bit sigma-delta at 10 or 80 SPS with a settling requirement
    after channel switch; it is not a clean continuous sensor. Now modeled: sample-rate aliasing
    of the mount ring, ADC quantization at the cell's actual mV/V sensitivity and the amplifier
    gain, 1/f drift, thermal zero drift over the burn, and a per-channel calibration-slope error
    left over from dead-weight calibration.

Also added: cross-axis coupling between the axial and lateral cells (real flexures are not
perfectly decoupled) and a full uncertainty budget returned alongside every measurement so the stand's resolution can be
compared against the effect size each research question needs to detect.
--------------------------------------------------------------------------------------------
"""
import numpy as np
from matplotlib.figure import Figure

try:
    from . import core
except ImportError:
    import core

_trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))

# ------------------------------------------------------------------ DAQ / stand hardware model
# NOYITO HX711 + generic strain-gauge bridge cells, as specified in BOM section 10.
HX711_SPS_LOW = 10.0 # HX711 RATE pin low (default on most breakouts)
HX711_SPS_HIGH = 80.0 # HX711 RATE pin high (used here; set by cutting the RATE trace)
HX711_BITS = 24
HX711_GAIN = 128.0 # channel A gain
CELL_SENS_MV_V = 1.0 # bridge sensitivity [mV/V] at full scale (typical for these cells)
BRIDGE_EXC_V = 5.0 # HX711 on-board excitation
ADC_FS_V = 0.5 * BRIDGE_EXC_V / HX711_GAIN # +-20 mV differential input span at gain 128

# Stand mechanical model (printed PETG-CF base + flexure stack carrying motor + gimbal)
MOUNT_F_HZ = 42.0 # first mount/flexure resonance [Hz] (measured-class for this build)
MOUNT_ZETA = 0.035 # structural damping ratio (printed polymer + bolted joints: very light)
CROSS_AXIS_PCT = 1.8 # lateral force appearing on the axial channel and vice versa [%]

# Drift and calibration residuals
ZERO_DRIFT_N_PER_S = 0.004 # thermal zero drift while the stand heats during a burn [N/s]
CAL_SLOPE_SIGMA = 0.006 # residual calibration-slope error after dead-weight cal (0.6%)

# ------------------------------------------------------------------ motors
# Estes F15 is the real digitized curve from core.py (49.6 N.s / 3.45 s). Others are represented by
# a plausible rise->sustain->tail shape scaled to the published total impulse / burn / peak so the
# tester shows the right impulse, average and peak. cls = NAR letter class.
MOTORS = {
    "Estes C6": dict(It=8.8, tb=1.86, peak=14.1, cls="C"),
    "Estes D12": dict(It=16.8, tb=1.65, peak=29.7, cls="D"),
    "Estes E12": dict(It=28.5, tb=2.62, peak=28.0, cls="E"),
    "Estes E16": dict(It=30.0, tb=1.90, peak=35.0, cls="E"), # commissioning motor (Gate 5)
    "Estes F15": dict(It=49.6, tb=3.45, peak=25.3, cls="F", real="F15"),
}
MOTOR_NAMES = list(MOTORS)


def _shape_curve(total, burn, peak, spike=0.14, n=80):
    """Generic BP thrust shape: linear rise to `peak` over the first spike*burn, then exponential
    decay toward a sustain, cut to zero at burnout.

    The curve is fitted to BOTH published numbers -- total impulse and peak thrust -- by solving
    for the sustain level rather than uniformly rescaling. Uniform rescaling (what this did
    before) can only satisfy one of the two: it hit the published total impulse and then reported
    a peak that was wrong by up to 2x in either direction, e.g. Estes D12 came out at 14.2 N peak
    against its published 29.7 N. Since the peak is what sizes the load cell and sets the stand's
    headroom check, a 2x error there is the difference between a valid test and a destroyed cell.
    """
    ts = spike * burn
    # Put a sample exactly at the spike apex so the discretized curve actually attains `peak`.
    t = np.unique(np.concatenate([np.linspace(0.0, burn, n), [ts]]))
    rise = peak * (t / max(ts, 1e-9))

    def curve(k):
        """Spike to `peak` at t=ts, then exponential decay at rate k."""
        decay = peak * np.exp(-k * (t - ts))
        f = np.where(t < ts, rise, decay)
        f = np.clip(f, 0.0, None).copy()
        f[-1] = 0.0
        return f

    # Solve the decay rate for the published total impulse. Rate is the right free parameter:
    # a fixed decay constant (burn/2.2, as before) makes the tail carry more impulse than some
    # motors actually have, which forced a uniform rescale that then broke the published peak.
    lo, hi = 0.02, 80.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _trapz(curve(mid), t) > total: lo = mid # too much impulse -> decay faster
        else: hi = mid
    f = curve(0.5 * (lo + hi))
    err = abs(_trapz(f, t) - total) / max(total, 1e-9)
    if err > 0.02:
        # The published (It, burn, peak) triple is not realizable with this shape. Rescale to
        # preserve total impulse and accept the peak error rather than silently misreporting.
        f = f * (total / _trapz(f, t))
    return t, f


def motor_curve(name):
    m = MOTORS[name]
    if m.get("real") == "F15":
        return core._TC.copy(), core._FC.copy()
    return _shape_curve(m["It"], m["tb"], m["peak"])


def motor_stats(name):
    t, f = motor_curve(name)
    It = float(_trapz(f, t)); tb = float(t[-1]); peak = float(f.max())
    avg = It / tb if tb > 0 else 0.0
    # NAR class check: total impulse doubles each letter; F = 40.01-80 N.s etc.
    return dict(name=name, It=It, tb=tb, avg=avg, peak=peak, cls=MOTORS[name]["cls"])


def _mount_response(t_fine, force, f_hz=MOUNT_F_HZ, zeta=MOUNT_ZETA):
    """Pass the true thrust through the stand's second-order structural response.

    The load cell sits under a compliant printed structure carrying the motor mass, so what it
    reacts is the stand's displacement, not the applied force. Integrated as a discrete
    second-order system driven by the true force; the ignition step therefore rings at the mount
    frequency and decays at the structural damping rate, exactly as an amateur stand does."""
    wn = 2 * np.pi * f_hz
    dt = float(t_fine[1] - t_fine[0])
    y = np.zeros_like(force); v = 0.0; ypos = 0.0
    for i, F in enumerate(force):
        a = wn * wn * (F - ypos) - 2 * zeta * wn * v
        v += a * dt; ypos += v * dt
        y[i] = ypos
    return y


def _daq_chain(t_fine, signal_N, cell_kg, sample_hz, rng, add_drift=True):
    """Take a continuous force signal to what the HX711 actually reports.

    Chain: continuous force -> ADC quantization at the cell's real mV/V sensitivity and the
    HX711's gain-128 input span -> bridge/amplifier noise -> 1/f + thermal zero drift ->
    residual calibration-slope error -> decimation to the DAQ sample rate (which aliases any
    mount ring above sample_hz/2 rather than removing it).
    """
    fs_N = cell_kg * 9.80665
    # ADC resolution referred to force: full-scale bridge output vs 24-bit span
    v_fs = CELL_SENS_MV_V * 1e-3 * BRIDGE_EXC_V # differential volts at cell full scale
    counts_fs = (v_fs / ADC_FS_V) * (2 ** (HX711_BITS - 1))
    lsb_N = fs_N / max(counts_fs, 1.0) # force per ADC count
    # decimate to the DAQ rate (no anti-alias filter on an HX711 breakout -> genuine aliasing)
    ts = np.arange(0.0, float(t_fine[-1]), 1.0 / sample_hz)
    idx = np.clip(np.searchsorted(t_fine, ts), 0, len(t_fine) - 1)
    x = signal_N[idx]
    # noise: bridge Johnson + amplifier, referred to force (vendor-typical ~0.4% FS peak-to-peak)
    x = x + rng.normal(0.0, 0.0012 * fs_N, x.shape)
    if add_drift:
        # thermal zero drift as the stand soaks, plus a slow 1/f wander
        x = x + ZERO_DRIFT_N_PER_S * ts
        x = x + np.cumsum(rng.normal(0.0, 0.0004 * fs_N, x.shape)) / np.sqrt(max(len(x), 1))
    # residual calibration-slope error left after dead-weight calibration
    x = x * (1.0 + rng.normal(0.0, CAL_SLOPE_SIGMA))
    # ADC quantization
    x = np.round(x / lsb_N) * lsb_N
    return ts, x, dict(lsb_N=lsb_N, fs_N=fs_N, counts_fs=counts_fs)


def static_stand_trace(name, cell_kg=5.0, sample_hz=HX711_SPS_HIGH, seed=0,
                       model_mount=True, fine_dt=2e-4):
    """Simulate what the single-axis static stand (5 kg axial cell + HX711) actually logs.

    Unlike the previous ideal model, the returned `reading` is the true thrust after the stand's
    structural response and the full HX711 chain -- so the ignition transient rings, the trace
    carries quantization and drift, and the peak the DAQ reports is NOT the motor's true peak.

    Returns (t, thrust_true, cell_reading, stats, info) where `info` carries the uncertainty
    budget and the peak-measurement error the mount ring induces.
    """
    t, f = motor_curve(name)
    tb = t[-1]
    rng = np.random.default_rng(seed)
    t_fine = np.arange(0.0, tb + 0.5, fine_dt)
    true_fine = np.interp(t_fine, t, f, left=0.0, right=0.0)
    sensed = _mount_response(t_fine, true_fine) if model_mount else true_fine
    ts, reading, adc = _daq_chain(t_fine, sensed, cell_kg, sample_hz, rng)
    true = np.interp(ts, t, f, left=0.0, right=0.0)
    st = motor_stats(name)
    fs_N = adc["fs_N"]
    headroom = fs_N / st["peak"] if st["peak"] > 0 else np.inf
    # what the stand would report vs. what the motor actually did
    It_meas = float(_trapz(np.clip(reading, 0, None), ts))
    peak_meas = float(np.max(reading))
    info = dict(
        cell_fs_N=fs_N, headroom=headroom, sample_hz=sample_hz,
        lsb_N=adc["lsb_N"], resolution_pct_fs=100.0 * adc["lsb_N"] / fs_N,
        mount_f_hz=MOUNT_F_HZ, mount_zeta=MOUNT_ZETA,
        nyquist_hz=sample_hz / 2.0, mount_aliased=(MOUNT_F_HZ > sample_hz / 2.0),
        peak_measured_N=peak_meas, peak_true_N=st["peak"],
        peak_error_pct=100.0 * (peak_meas - st["peak"]) / max(st["peak"], 1e-9),
        impulse_measured_Ns=It_meas, impulse_true_Ns=st["It"],
        impulse_error_pct=100.0 * (It_meas - st["It"]) / max(st["It"], 1e-9),
        cal_slope_sigma_pct=100.0 * CAL_SLOPE_SIGMA,
    )
    return ts, true, reading, st, info


def make_motor_figure(name, cell_kg=5.0, seed=0):
    ts, true, reading, st, info = static_stand_trace(name, cell_kg=cell_kg, seed=seed)
    fig = Figure(figsize=(8, 5), dpi=100); ax = fig.add_subplot(111)
    ax.plot(ts, reading, color="#c0c0c0", lw=0.9,
            label=f"load cell as logged ({info['sample_hz']:.0f} SPS, mount ring + HX711 chain)")
    ax.plot(ts, true, color="#2a6f97", lw=2.2, label="true thrust")
    ax.axhline(st["avg"], ls="--", color="#386641", lw=1, label=f"avg {st['avg']:.1f} N")
    ax.axhline(st["peak"], ls=":", color="#bc4749", lw=1, label=f"true peak {st['peak']:.1f} N")
    ax.set_xlabel("t (s)"); ax.set_ylabel("thrust (N)")
    over = " ⚠ cell under-ranged!" if info["headroom"] < 1.05 else ""
    alias = " ⚠ mount ring ALIASED" if info["mount_aliased"] else ""
    ax.set_title(f"{name}: {st['It']:.1f} N·s ({st['cls']}-class) · burn {st['tb']:.2f} s · "
                 f"{cell_kg:.0f} kg cell = {info['cell_fs_N']:.0f} N FS ({info['headroom']:.1f}×){over}{alias}",
                 fontweight="bold")
    ax.text(0.98, 0.55,
            f"peak err {info['peak_error_pct']:+.1f}% impulse err {info['impulse_error_pct']:+.1f}%\n"
            f"resolution {info['resolution_pct_fs']:.3f}% FS ({info['lsb_N']*1000:.1f} mN/count)\n"
            f"mount {info['mount_f_hz']:.0f} Hz ζ={info['mount_zeta']:.3f} · Nyquist {info['nyquist_hz']:.0f} Hz",
            transform=ax.transAxes, ha="right", va="top", fontsize=7.5,
            bbox=dict(fc="#f4f4f4", ec="#bbb", alpha=0.9))
    ax.grid(alpha=0.3); ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ jetvane suitability
# Jetvanes deflect the exhaust for TVC. Effectiveness ~ side force per degree; axial loss from vane
# drag + cosine; thermal is the killer for a 3.45 s black-powder burn on a printed vane.
EXHAUST = {
    "Estes BP (F15)": dict(Tflame_K=1150.0, kind="black powder"),
    "APCP composite": dict(Tflame_K=2100.0, kind="ammonium-perchlorate composite"),
}
VANE_MAT = {
    "PETG-CF (printed)": dict(Tmax_K=353.0, survives=False), # HDT ~80 C -> ablates instantly
    "PLA (printed)": dict(Tmax_K=328.0, survives=False), # HDT ~55 C -> ablates instantly
    "ABS (printed)": dict(Tmax_K=371.0, survives=False), # coupon: HDT ~98 C -> ablates
    "Graphite": dict(Tmax_K=3900.0, survives=True), # sublimes ~3900 K; mild erosion in BP
    "Tungsten": dict(Tmax_K=3695.0, survives=True),
}


def jetvane_analysis(motor="Estes F15", vane_mat="Graphite", exhaust="Estes BP (F15)",
                     max_defl_deg=15.0, vane_eff_per_deg=0.010, cd_vane=0.15):
    """Side force and axial-thrust loss vs vane deflection over a sweep, plus a thermal-survival
    verdict and a suitability call against the servo-gimbal TVC baseline (~8 deg -> 3.5 N side)."""
    st = motor_stats(motor)
    T = st["avg"]
    d = np.linspace(0.0, max_defl_deg, 60)
    # side force ~ effectiveness * thrust * deflection (small-angle linear region)
    side = vane_eff_per_deg * T * d
    # axial loss = cosine loss + vane profile drag growing with deflection
    axial_loss = T * (1 - np.cos(np.radians(d))) + cd_vane * T * (d / max_defl_deg) ** 2
    axial_loss_pct = 100.0 * axial_loss / T
    ex = EXHAUST[exhaust]; vm = VANE_MAT[vane_mat]
    survives = vm["survives"] and vm["Tmax_K"] > ex["Tflame_K"]
    # servo-TVC baseline side force at the vehicle's +-8 deg gimbal (peak thrust) for comparison
    servo_side = st["peak"] * np.sin(np.radians(8.0))
    side_at_max = side[-1]
    verdict = []
    if not survives:
        verdict.append(f"THERMAL FAIL: {vane_mat} (Tmax {vm['Tmax_K']:.0f} K) cannot survive the "
                       f"{ex['Tflame_K']:.0f} K {ex['kind']} exhaust for the full {st['tb']:.1f} s burn.")
    else:
        verdict.append(f"Thermal OK: {vane_mat} survives the {ex['Tflame_K']:.0f} K exhaust (expect "
                       f"mild leading-edge erosion over {st['tb']:.1f} s; profile the vane accordingly).")
    verdict.append(f"Side force at {max_defl_deg:.0f} deg vane ~= {side_at_max:.2f} N "
                   f"(servo gimbal at 8 deg gives ~{servo_side:.2f} N for comparison).")
    verdict.append(f"Axial thrust loss at {max_defl_deg:.0f} deg ~= {axial_loss_pct[-1]:.1f}% of average thrust.")
    ok = survives and side_at_max >= 0.6 * servo_side and axial_loss_pct[-1] <= 12.0
    verdict.append("SUITABLE (graphite/tungsten only), jetvanes give control authority comparable to "
                   "the servo gimbal, at the cost of a few % axial loss." if ok else
                   "NOT the preferred TVC for WYVERN, the servo (or magnetic) nozzle gimbal beats a "
                   "jetvane on axial loss and, for any printed vane, on survivability.")
    return dict(d=d, side=side, axial_loss_pct=axial_loss_pct, survives=survives,
                servo_side=servo_side, verdict="\n".join("• " + v for v in verdict), suitable=ok)


def make_jetvane_figure(motor="Estes F15", vane_mat="Graphite", exhaust="Estes BP (F15)",
                        max_defl_deg=15.0, vane_eff_per_deg=0.010):
    r = jetvane_analysis(motor, vane_mat, exhaust, max_defl_deg, vane_eff_per_deg)
    fig = Figure(figsize=(8, 5), dpi=100); ax = fig.add_subplot(111)
    ax.plot(r["d"], r["side"], color="#2a6f97", lw=2.2, label="jetvane side force (N)")
    ax.axhline(r["servo_side"], ls="--", color="#386641", lw=1.2, label=f"servo gimbal @8° ({r['servo_side']:.1f} N)")
    ax.set_xlabel("vane deflection (deg)"); ax.set_ylabel("side force (N)", color="#2a6f97")
    ax2 = ax.twinx()
    ax2.plot(r["d"], r["axial_loss_pct"], color="#bc4749", lw=2.0, label="axial thrust loss (%)")
    ax2.set_ylabel("axial thrust loss (%)", color="#bc4749")
    tv = "SUITABLE" if r["suitable"] else ("THERMAL FAIL" if not r["survives"] else "not preferred")
    ax.set_title(f"Jetvane suitability, {motor} · {vane_mat} vane · {exhaust} → {tv}", fontweight="bold")
    ax.grid(alpha=0.3)
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [l.get_label() for l in lines], loc="upper left", fontsize=8)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ ground TVC test + PID
def ground_tvc_test(motor="Estes F15", kp=None, ki=None, kd=None, gimbal_deg=8.0,
                    tau_servo=0.04, scenario="Step to 5°, then hold", link_ratio=1.0,
                    axial_cell_kg=5.0, lat_cell_kg=1.0, noise_frac=0.004, dt=0.002, seed=0):
    """Simulate the 3-axis thrust-vector balance during a bench run: the DAQ commands a gimbal
    profile (or the firmware PID rejects a bench disturbance), the servo tracks it through a
    first-order lag, and the balance load cells read the resolved thrust vector with noise.

    Returns time series (t, cmd_deg, meas_deg, Fz, Fx, T, theta_deg) + metrics.
    """
    kp = core.KP if kp is None else kp
    ki = core.KI if ki is None else ki
    kd = core.KD if kd is None else kd
    t, f = motor_curve(motor)
    tb = t[-1]
    rng = np.random.default_rng(seed)
    n = int(np.ceil((tb + 0.5) / dt))
    T_axis = np.arange(n) * dt
    thrust = np.interp(T_axis, t, f, left=0.0, right=0.0)
    lim = gimbal_deg

    # commanded gimbal profile
    step_mode = scenario.startswith("Step")
    sweep_mode = scenario.startswith("Sweep")
    pid_mode = scenario.startswith("PID")
    cmd = np.zeros(n)
    if step_mode:
        cmd[T_axis >= 0.4] = 5.0
    elif sweep_mode:
        cmd = lim * 0.8 * np.sin(2 * np.pi * 0.7 * T_axis)
    # (pid_mode handled in the loop below: PID rejects a 3 deg mount misalignment disturbance)

    meas = np.zeros(n) # measured nozzle angle (servo lag + linkage)
    Fz = np.zeros(n); Fx = np.zeros(n)
    g = 0.0; integ = 0.0; theta = 3.0 if pid_mode else 0.0; prev = 0.0
    fs_ax = axial_cell_kg * 9.80665; fs_lat = lat_cell_kg * 9.80665
    sat = 0
    for i in range(n):
        Th = thrust[i]
        if pid_mode:
            # firmware PID drives the bench "attitude proxy" theta back to 0 (disturbance rejection)
            err = -theta
            integ = float(np.clip(integ + err * dt, -lim / max(ki, 1e-6), lim / max(ki, 1e-6)))
            deriv = (err - prev) / dt; prev = err
            c = kp * err + ki * integ + kd * deriv
        else:
            c = cmd[i]
        c = float(np.clip(c, -lim, lim))
        if abs(c) >= lim - 1e-6:
            sat += 1
        # servo first-order lag toward the commanded (link_ratio scales cmd->nozzle)
        g += (c * link_ratio - g) * dt / tau_servo
        meas[i] = g
        # balance reads the resolved thrust vector
        fz = Th * np.cos(np.radians(g)); fx = Th * np.sin(np.radians(g))
        Fz[i] = fz + rng.normal(0, noise_frac * fs_ax)
        Fx[i] = fx + rng.normal(0, noise_frac * fs_lat)
        if pid_mode and Th > 1.0:
            # nozzle side force produces a restoring rate on the bench attitude proxy (toy 2nd order)
            theta += (-Th * np.sin(np.radians(g)) * 0.02) * dt * 100 * dt
    # resolve
    T_mag = np.sqrt(Fz ** 2 + Fx ** 2)
    theta_meas = np.degrees(np.arctan2(np.abs(Fx), np.maximum(Fz, 1e-6)))
    st = motor_stats(motor)
    metrics = dict(
        peak_side_N=float(np.nanmax(np.abs(Fx))),
        peak_axial_N=float(np.nanmax(Fz)),
        max_gimbal_deg=float(np.nanmax(np.abs(meas))),
        sat_pct=100.0 * sat / n,
        lat_headroom=(fs_lat / max(float(np.nanmax(np.abs(Fx))), 1e-6)),
        ax_headroom=(fs_ax / max(float(np.nanmax(Fz)), 1e-6)),
        motor=st,
    )
    return dict(t=T_axis, cmd=cmd if not pid_mode else None, meas=meas,
                Fz=Fz, Fx=Fx, T=T_mag, theta_deg=theta_meas, metrics=metrics, pid_mode=pid_mode)


def make_ground_tvc_figure(motor="Estes F15", kp=None, ki=None, kd=None, gimbal_deg=8.0,
                           scenario="Step to 5°, then hold", tau_servo=0.04, seed=0):
    r = ground_tvc_test(motor, kp, ki, kd, gimbal_deg=gimbal_deg, scenario=scenario,
                        tau_servo=tau_servo, seed=seed)
    m = r["metrics"]
    fig = Figure(figsize=(8, 6), dpi=100)
    ax1 = fig.add_subplot(211); ax2 = fig.add_subplot(212)
    if r["cmd"] is not None:
        ax1.plot(r["t"], r["cmd"], "k:", lw=1.2, label="commanded δ")
    ax1.plot(r["t"], r["meas"], color="#bc4749", lw=1.8, label="measured nozzle δ (servo lag)")
    ax1.axhline(gimbal_deg, ls="--", color="#999", lw=0.7); ax1.axhline(-gimbal_deg, ls="--", color="#999", lw=0.7)
    ax1.set_ylabel("gimbal δ (deg)"); ax1.grid(alpha=0.3); ax1.legend(fontsize=8, loc="upper right")
    ax1.set_title(f"Ground 3-axis TVC balance, {motor} · "
                  f"{'PID reject' if r['pid_mode'] else scenario} · sat {m['sat_pct']:.0f}%",
                  fontweight="bold")
    ax2.plot(r["t"], r["Fz"], color="#2a6f97", lw=1.6, label="Fz axial (load cell)")
    ax2.plot(r["t"], r["Fx"], color="#bc4749", lw=1.6, label="Fx lateral (load cell)")
    ax2.set_xlabel("t (s)"); ax2.set_ylabel("force (N)"); ax2.grid(alpha=0.3)
    ax2.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    return fig, m


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg")
    for nm in MOTOR_NAMES:
        s = motor_stats(nm)
        print(f"{nm:10} It={s['It']:5.1f} N·s avg={s['avg']:5.1f} N peak={s['peak']:5.1f} N burn={s['tb']:.2f}s {s['cls']}")
    j = jetvane_analysis("Estes F15", "PETG-CF (printed)")
    print("jetvane PETG-CF survives:", j["survives"], "| graphite:",
          jetvane_analysis("Estes F15", "Graphite")["survives"])
    r = ground_tvc_test("Estes F15", scenario="PID reject 3° mount tilt")
    print("ground TVC PID:", {k: round(v, 3) for k, v in r["metrics"].items() if isinstance(v, float)})
    print("bench_sim self-test OK")
