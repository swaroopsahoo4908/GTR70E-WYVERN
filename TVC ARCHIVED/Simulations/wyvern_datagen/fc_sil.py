#!/usr/bin/env python3
"""
GTR70E WYVERN, Flight-Computer Software-in-the-Loop (SIL) digital twin.

Steps the *actual flight-computer processes* at 500 Hz against a simulated vehicle + atmosphere:

  - State machine : BOOT → ARMED → BOOST → COAST → RECOVER → DESCENT → LANDED
                      (same transitions as wyvern4_tvc.ino: 2 g launch latch, burnout, F15-4
                       motor ejection at t≈7.45 s, apogee cross-check, landing detect).
  - Sensors : baro altitude, IMU pitch, and body accel, each with realistic noise/bias.
                      The PID closes on the *measured* attitude (not the true state), like the real FC.
  - Control loop : firmware PID (Kp/Ki/Kd, ±8° gimbal, anti-windup) → thrust-vector moment.
  - Atmosphere : ISA troposphere + power-law wind shear + Dryden-form turbulence, all shared
                      with core.py so the SIL and the Monte-Carlo core cannot drift apart.
  - Actuator : second-order servo with slew-rate limit and an explicit sense->actuate
                      transport delay, driven by a 500 Hz zero-order hold (as on the vehicle).
  - Recovery : motor ejection (no FC pyro) → 18" parachute descent.
  - Outputs : a full state time-series, a flight-log frame stream (sd_logger schema), and a
                      simulated Wi-Fi heartbeat telemetry stream (the `HB:` lines the FC broadcasts).

This is the same physics as core.py (so apogee/mass/recovery match), wrapped in the FC's own logic.
"""
import numpy as np
try:
    import core
except ImportError:
    from . import core

STATES = ["BOOT", "ARMED", "BOOST", "COAST", "RECOVER", "DESCENT", "LANDED"]

# firmware-matched thresholds (wyvern4_tvc.ino / launch_status.h)
LAUNCH_G = 2.0 # launch latch: |a| > 2 g ... (was 3.0; see launch_status.h note --
                          # at 792 g the vehicle clears 3 g for only 61 ms vs a 50 ms sustain)
LAUNCH_HOLD_S = 0.05 # ... sustained 50 ms
LAND_SPEED = 1.0 # |v| < 1 m/s after apogee -> LANDED
BATT_FULL = 7.9 # 2S nominal at arm


# Wind shear is core.wind_at (standard power law referenced to 10 m). The bespoke profile that
# used to live here disagreed with core.py's, which meant the SIL and the Monte-Carlo core were
# quietly flying two different atmospheres.
wind_at = core.wind_at


def run_sil(kp=None, ki=None, kd=None, wind_ms=6.0, turb_pct=12.0, temp_C=15.0,
            pressure_mbar=1013.25, launch_tilt_deg=2.0, gimbal_deg=8.0, seed=0,
            dt=0.002, hb_hz=5, log_hz=50, t_max=35.0):
    """Run one SIL flight. Returns arrays, telemetry lines, log frames, and a summary."""
    kp = core.KP if kp is None else kp
    ki = core.KI if ki is None else ki
    kd = core.KD if kd is None else kd
    rng = np.random.default_rng(seed)

    T0 = core.T0_ISA + (temp_C - 15.0); P0 = pressure_mbar * 100.0
    lim = np.deg2rad(gimbal_deg); I_MAX = lim / ki if ki > 1e-9 else 1e6
    ZETA = 0.15; arm_len = core.PIVOT - core.CG
    tilt = np.deg2rad(launch_tilt_deg); turb = turb_pct / 100.0
    shear_alpha = 0.16
    # actuator + control-timing state (matches core.simulate_tvc)
    delta = 0.0; delta_rate = 0.0; d_state = 0.0; prev_err = 0.0; cmd_held = 0.0
    ctrl_every = max(1, int(round(core.CTRL_DT / dt)))
    ndelay = max(1, int(round(core.CTRL_DELAY_S / dt)))
    delay_buf = np.zeros(ndelay); di = 0

    # true state
    x = z = vx = vz = 0.0
    theta = 0.0; omega = 0.0; integ = 0.0
    # FC state
    st = 0 # index into STATES (BOOT)
    st = 1 # ARMED at t=0 (RBF pulled on the pad in this sim)
    launch_t = None; launched = False; deploy_time = None
    baro_bias = rng.normal(0, 0.3); gyro_drift = rng.normal(0, 0.02) # deg/s
    apogee_baro = -1e9; apogee_true = 0.0; apogee_t = 0.0; deployed = False

    steps = int(np.ceil(min(t_max, 35.0) / dt)) + 1
    rec_t = core.DEPLOY_T
    hb_every = max(1, int(round((1.0 / hb_hz) / dt)))
    log_every = max(1, int(round((1.0 / log_hz) / dt)))
    # pre-draw all sensor/gust noise for the flight (one vectorized RNG call each, ~3x faster loop)
    n_baro = rng.normal(0, 0.4, steps); n_imu = rng.normal(0, np.deg2rad(0.2), steps)
    n_accel = rng.normal(0, 0.05, steps); n_batt = rng.normal(0, 0.005, steps)
    n_gyro = rng.normal(0, core.GYRO_NOISE_RAD_S, steps)
    gyro_bias = rng.normal(0, core.GYRO_BIAS_RAD_S)
    t_arr = dt * np.arange(steps) # precompute time-only quantities
    Th_arr = np.asarray(core.thrust(t_arr), dtype=float); m_arr = np.asarray(core.mass(t_arr), dtype=float)
    gust = core._DrydenGust(rng, 1, sigma=np.array([wind_ms * turb]))

    T = []; Z = []; VZ = []; TH = []; DE = []; BALT = []; STt = []
    telem = []; logs = []
    t = 0.0
    for i in range(steps):
        Th = Th_arr[i]; m = m_arr[i]
        # --- translation (vertical dominant; wind drift horizontal) ---
        rho, a_snd, _Tk = core.isa_state(z, P0, T0)
        w = wind_at(z, wind_ms, shear_alpha) + float(gust.step(dt, np.array([max(vz, 1.0)]))[0])
        rvx = vx - w; rvz = vz
        vrel = np.hypot(rvx, rvz) + 1e-9; mach = vrel / a_snd
        if not deployed:
            re = rho * vrel * core.LTOT / core.MU_AIR
            Cd = float(core.cd_buildup(mach, re)); Aref = core.A
        else:
            Cd = core.CHUTE_CD; Aref = core.CHUTE_A # under parachute
        drag = 0.5 * rho * Cd * Aref * vrel * vrel
        thx = Th * np.sin(tilt) * (Th > 0); thz = Th * np.cos(tilt) * (Th > 0)
        ax = (thx - drag * rvx / vrel) / m
        az = (thz - drag * rvz / vrel) / m - core.G
        vx += ax * dt; vz += az * dt; x += vx * dt; z += vz * dt
        if z < 0: z = 0.0
        # BUG FIX (2026-08): an accelerometer measures SPECIFIC FORCE, not kinematic acceleration, 
        # it reads +1 g sitting on the pad and (thrust-drag)/m in flight. The previous line used the
        # kinematic magnitude hypot(ax, az), which subtracts gravity and therefore peaked at only
        # ~2.65 g on this vehicle. Against the (then) firmware 3 g launch latch that meant the SIL
        # state machine NEVER left ARMED: no BOOST, no TVC engage, no deploy, and a ballistic ~70 m/s
        # "touchdown" in every logged flight. Specific force peaks at 3.27 g (= T/W peak 3.26), which
        # is what the real BNO085 reports and why the latch was lowered to the current 2 g (LAUNCH_G).
        a_mag_g = np.hypot(ax, az + core.G) / core.G

        # --- sensors (what the FC actually sees) ---
        baro_alt = z + baro_bias + n_baro[i]
        imu_theta = theta + np.deg2rad(gyro_drift) * t + n_imu[i]
        accel_g_meas = a_mag_g + n_accel[i]

        # --- pitch plant + control (closes on measured attitude) ---
        q = 0.5 * rho * vz * vz
        alpha_w = np.arctan2(w, max(vz, 1.0))
        k_aero = q * core.A * core.CN_ALPHA * (core.XCP - core.CG)
        c_aero = 2.0 * ZETA * np.sqrt(max(k_aero, 0.0) * core.IYY)
        on_rail = z < core.RAIL_LEN
        engaged = (STATES[st] in ("BOOST", "COAST")) and (t >= core.TVC_ENGAGE_T) and (Th > 1.0) and (not on_rail)
        # --- controller runs at the firmware's 500 Hz, held between updates (ZOH) ---
        if i % ctrl_every == 0:
            omega_meas = omega + gyro_bias + n_gyro[i]
            omega_meas = round(omega_meas / core.GYRO_LSB_RAD_S) * core.GYRO_LSB_RAD_S
            err = imu_theta
            integ = float(np.clip(integ + err * core.CTRL_DT, -I_MAX, I_MAX))
            raw_d = (err - prev_err) / core.CTRL_DT
            alpha_f = core.CTRL_DT / (core.TAU_D + core.CTRL_DT)
            d_state += alpha_f * (raw_d - d_state)
            prev_err = err
            delta_cmd = kp * err + ki * integ + kd * (0.5 * d_state + 0.5 * omega_meas)
            cmd_held = float(np.clip(delta_cmd, -lim, lim)) if engaged else 0.0
        # --- transport delay + second-order servo with slew-rate limit ---
        delay_buf[di] = cmd_held; di = (di + 1) % ndelay
        cmd_delayed = delay_buf[di]
        sacc = core.SERVO_WN**2 * (cmd_delayed - delta) - 2 * core.SERVO_ZETA * core.SERVO_WN * delta_rate
        delta_rate = float(np.clip(delta_rate + sacc * dt, -core.SERVO_RATE, core.SERVO_RATE))
        delta = float(np.clip(delta + delta_rate * dt, -lim, lim))
        M_tvc = -Th * np.sin(delta) * arm_len
        ang = (k_aero * (alpha_w - theta) - c_aero * omega + M_tvc) / core.IYY
        if on_rail:
            omega = 0.0
        else:
            omega += ang * dt; theta += omega * dt

        # --- state machine (mirrors the firmware) ---
        if not launched and accel_g_meas > LAUNCH_G:
            launch_t = t if launch_t is None else launch_t
            if t - launch_t >= LAUNCH_HOLD_S:
                launched = True; st = 2 # BOOST
        elif not launched:
            launch_t = None
        if launched and Th <= 0 and STATES[st] == "BOOST":
            st = 3 # COAST at burnout
        if baro_alt > apogee_baro:
            apogee_baro = baro_alt
        if z > apogee_true:
            apogee_true = z; apogee_t = t
        if (not deployed) and t >= rec_t and STATES[st] in ("BOOST", "COAST"):
            deployed = True; deploy_time = t; st = 4 # RECOVER (motor ejection + chute inflation)
        if STATES[st] == "RECOVER" and deploy_time is not None and t >= deploy_time + 0.3:
            st = 5 # DESCENT (chute open)
        if deployed and STATES[st] == "DESCENT" and z <= 0.10 and t > apogee_t + 1.0:
            st = 6 # LANDED (touchdown under chute)

        batt = BATT_FULL - 0.015 * t + n_batt[i]

        # --- logging + telemetry ---
        if i % log_every == 0:
            logs.append((round(t, 4), STATES[st], round(z, 2), round(vz, 2),
                         round(np.rad2deg(theta), 3), round(np.rad2deg(delta), 3),
                         round(baro_alt, 2), round(batt, 2)))
        if i % hb_every == 0:
            telem.append(f"HB:t={int(t*1000)} state={STATES[st]} alt={baro_alt:.1f} v={vz:.1f} "
                         f"pitch={np.rad2deg(theta):.1f} gmbl={np.rad2deg(delta):.1f} "
                         f"batt={batt:.2f}V rbf=1 drop=0")
        T.append(t); Z.append(z); VZ.append(vz); TH.append(np.rad2deg(theta))
        DE.append(np.rad2deg(delta)); BALT.append(baro_alt); STt.append(st)

        t += dt
        if STATES[st] == "LANDED" and t > rec_t + 1:
            break
        if t > t_max:
            break

    arr = {k: np.asarray(v) for k, v in
           dict(t=T, z=Z, vz=VZ, theta_deg=TH, gimbal_deg=DE, baro_alt=BALT, state=STt).items()}
    boost = arr["state"] == 2 # BOOST = controlled phase
    peak_boost = float(np.max(np.abs(arr["theta_deg"][boost]))) if boost.any() else 0.0
    rms_gimbal_boost = float(np.sqrt(np.mean(arr["gimbal_deg"][boost] ** 2))) if boost.any() else 0.0
    sat_boost = (100.0 * float(np.mean(np.abs(arr["gimbal_deg"][boost]) >= gimbal_deg - 0.1))
                 if boost.any() else 0.0)
    summary = dict(
        apogee_true_m=round(apogee_true, 1), apogee_baro_m=round(apogee_baro, 1),
        apogee_t_s=round(apogee_t, 2), apogee_err_m=round(apogee_baro - apogee_true, 2),
        deploy_t_s=rec_t, deployed=deployed, landed=(STATES[STt[-1]] == "LANDED"),
        peak_pitch_boost_deg=round(peak_boost, 2), # control metric (TVC active)
        rms_gimbal_boost_deg=round(rms_gimbal_boost, 2),
        gimbal_sat_boost_pct=round(sat_boost, 1),
        peak_pitch_coast_deg=round(float(np.max(np.abs(arr["theta_deg"]))), 1), # incl. apogee nose-over
        touchdown_v_ms=round(float(arr["vz"][-1]), 2), flight_time_s=round(float(arr["t"][-1]), 2),
        gains=(kp, ki, kd),
    )
    return dict(arr=arr, telemetry=telem, logs=logs, summary=summary,
                log_cols=["t_s", "state", "alt_m", "vz_ms", "pitch_deg", "gimbal_deg", "baro_m", "batt_v"])


if __name__ == "__main__":
    for w in (0, 6, 12):
        r = run_sil(wind_ms=w, turb_pct=12 if w else 0, seed=1)
        s = r["summary"]
        seq = []
        last = None
        for i in r["arr"]["state"]:
            if i != last: seq.append(STATES[i]); last = i
        print(f"wind {w:2d} m/s | states: {'→'.join(seq)} | landed={s['landed']}")
        print(f" apogee true {s['apogee_true_m']} m (baro {s['apogee_baro_m']}, err {s['apogee_err_m']} m) "
              f"@ {s['apogee_t_s']}s | peak pitch BOOST {s['peak_pitch_boost_deg']}° (coast nose-over "
              f"{s['peak_pitch_coast_deg']}°) | touchdown {s['touchdown_v_ms']} m/s | flight {s['flight_time_s']}s | "
              f"{len(r['telemetry'])} HB")
    print("\nsample telemetry:")
    for line in run_sil(wind_ms=6, seed=2)["telemetry"][::40][:6]:
        print(" " + line)
