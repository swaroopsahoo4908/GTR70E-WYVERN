#!/usr/bin/env python3
"""GTR70E WYVERN fin-control -- 3-DOF pitch-plane flight simulator with closed-loop fin control.

State  : x, z (m), vx, vz (m/s), theta (rad, body tilt from vertical, +ve toward +x), q (rad/s),
         delta (rad, actual pitch-pair deflection)
Forces : thrust on the body axis; drag on the air-relative velocity; component-wise normal force
         (nose, fixed rectangular fins, control fins) each at its own station, each seeing its own
         local angle of attack alpha_i = alpha + q (x_i - x_cg) / V, which is what gives the model
         its pitch damping without a separate C_mq term.
Control: PID on tilt with rate feedback, gains scheduled on dynamic pressure (K ~ q_ref / q),
         servo = rate-limited first-order lag whose slew rate drops linearly with hinge-moment
         load (KST X08 Plus torque-speed line). Control engages at rail exit.
Wind   : power-law mean wind + 1-cosine discrete gust + Dryden-like first-order turbulence.

Run:  python3 wf_flightsim.py            -> plots_flight/*.png + flight_summary.json
"""
from __future__ import annotations
import json, math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C

OUT = os.path.join(C.HERE, "plots_flight"); os.makedirs(OUT, exist_ok=True)
D2R, R2D = math.pi / 180, 180 / math.pi

# Controller defaults (firmware mirrors these in fc_config.h)
GAINS = dict(kp=0.9, ki=0.25, kd=0.12, q_ref=1500.0, k_min=0.15, k_max=4.0)
GAINS_FLIGHT = dict(GAINS)
_TG = os.path.join(OUT, "tuned_gains.json")
if os.path.exists(_TG):
    GAINS_FLIGHT = json.load(open(_TG))   # written by tune() in __main__ -> mirrored in fc_config.h
CTRL_END_QBAR = 15.0       # Pa: rev 3d firmware keeps the fins active in coast until q falls below this
SERVO_TAU = 0.020           # s, digital-servo position loop lag
HINGE_ARM_FRAC = 0.14       # (x_cp - x_hinge)/c_root from CFD/vlm.py at H = 30 mm (0.155 @20 .. 0.128 @40)

def servo_rate_max(v_batt=7.6):
    sp = C.SERVO["speed_s60"]; vs = sorted(sp)
    s60 = float(np.interp(v_batt, vs, [sp[k] for k in vs]))
    return (60 * D2R) / s60

def servo_stall_Nm(v_batt=7.6):
    tq = C.SERVO["torque_kgcm"]; vs = sorted(tq)
    return float(np.interp(v_batt, vs, [tq[k] for k in vs])) * 0.0980665

class Vehicle:
    # Per-flight dispersion hooks (Monte-Carlo suite, wyvern_finsim/engine.py). Defaults = nominal.
    cd_scale = 1.0        # drag coefficient multiplier
    imp_scale = 1.0       # thrust / total-impulse multiplier
    rho_scale = 1.0       # air density relative to ISA sea level (temperature, pressure, site altitude)
    fin_bias_deg = 0.0    # pitch-pair rigging / trim error, added to the actual deflection
    servo_scale = 1.0     # servo slew-rate multiplier
    def __init__(self, motor=C.FLIGHT_MOTOR, H=C.CFIN_H_NOMINAL, rect_span=C.RECT_FIN["span"],
                 ballast_g=None, profile_eta=1.0, k_defl=None):
        self.motor = C.MOTORS[motor]; self.mname = motor; self.H = H
        self.rect_span = rect_span; self.ballast = ballast_g; self.eta = profile_eta
        M0, cg0, I0, _ = C.mass_properties(motor, 0.0, H, ballast_g, rect_span)
        Mb, cgb, Ib, _ = C.mass_properties(motor, 99, H, ballast_g, rect_span)
        self.M0, self.Mb, self.cg0, self.cgb, self.I0, self.Ib = M0, Mb, cg0, cgb, I0, Ib
        d = C.OD
        cn_n, self.x_n = C.nose_cp()
        self.cna_n = cn_n
        rf = C.RECT_FIN
        self.cna_r = C.barrowman_fin_cna(4, rf["root"], rf["tip"], rect_span, 0) * C.K_WB(C.R / (C.R + rect_span))
        self.x_r = C.barrowman_fin_xcp(rf["root"], rf["tip"], rect_span, 0, C.X_RECT_LE)
        g = C.cfin_geom(H)
        import sys as _s; _s.path.insert(0, os.path.join(C.HERE, "CFD"))
        from vlm import fin_vlm
        # ONE control fin, normal-force slope referenced to A_REF (VLM, ref S_f -> ref A)
        self.cna_1 = fin_vlm(H)["CNa"] * (g["area"] / (math.pi * C.OD ** 2 / 4)) * profile_eta
        self.interf = C.vortex_interference(H, rect_span)   # fixed-fin vortex interference ratio
        self.Kc = C.K_WB(C.R / (C.R + H))
        self.k_defl = self.Kc if k_defl is None else k_defl   # deflection: slender-body k_W(B)+k_B(W) = K_W(B)
        xle_A = C.X_HINGE_A - C.CFIN["hinge_frac"] * g["root"]
        xle_B = C.X_HINGE_B - C.CFIN["hinge_frac"] * g["root"]
        self.x_cA = C.barrowman_fin_xcp(g["root"], 0, H, g["sweep"], xle_A)
        self.x_cB = C.barrowman_fin_xcp(g["root"], 0, H, g["sweep"], xle_B)
        self.area_fin = g["area"] / 1e6
        self.chord = g["root"] / 1000

    def mass(self, t):
        f = 0.0 if t <= 0 else min(1.0, float(C._trapz(self.motor["f"][self.motor["t"] <= t], self.motor["t"][self.motor["t"] <= t])) / self.motor["I"])
        M = self.M0 - (self.M0 - self.Mb) * f
        cg = self.cg0 + (self.cgb - self.cg0) * f
        I = self.I0 + (self.Ib - self.I0) * f
        return M, cg, I

    def thrust(self, t):
        return self.imp_scale * float(np.interp(t, self.motor["t"], self.motor["f"], left=0, right=0))

def simulate(veh: Vehicle, wind=4.0, gust=4.0, gust_t=1.2, gust_len=0.5, turb=1.0,
             control=True, gains=GAINS, dt=0.0005, t_end=None, seed=1, launch_tilt_deg=0.0,
             v_batt=7.6, defl_max_deg=C.CFIN["defl_max_deg"], record=True, ctrl_until="apogee",
             maneuver=None, brake=None):
    """maneuver: list of events dict(kind="doublet"|"step", t0, dur, amp_deg, [hold, rest]) on the
    pitch axis (see MANEUVER_A / MANEUVER_B). ctrl_until: "apogee" | "burnout" | "firmware"
    (firmware rule, rev 3d: after burnout, control until q < WYV_CTRL_END_QBAR = 15 Pa)."""
    rng = np.random.default_rng(seed)
    x = z = vx = vz = 0.0
    th = launch_tilt_deg * D2R; q = 0.0; dl = 0.0; integ = 0.0
    on_rail = True; rail_exit = None; t = 0.0
    wmax = servo_rate_max(v_batt) * veh.servo_scale; Tst = servo_stall_Nm(v_batt)
    fb = veh.fin_bias_deg * D2R
    turb_u = 0.0; Lt = 30.0
    hist = {k: [] for k in ("t", "x", "z", "v", "th", "q", "dl", "dc", "alpha", "qbar", "hm", "u",
                            "ref", "inj", "bq", "mdel", "db", "hpred")}
    db = 0.0; hpred = float("nan")       # split-fin brake deflection (rad, actual) and predicted apogee
    ctrl_time = 0.0
    man_gate_ok = True; man_state = dict(aborted=False, skipped=False); dema = 0.0   # 50 ms EMA of delta (firmware)
    apo = None; maxq = 0.0; max_hm = 0.0; sat_time = 0.0
    tb = veh.motor["tb"]; t_end = t_end or 60.0
    while t < t_end:
        M, cg, I = veh.mass(t); T = veh.thrust(t)
        # wind at altitude (power law, alpha=1/7), gust and turbulence
        uw = wind * (max(z, 0.5) / 10.0) ** (1 / 7)
        if gust and gust_t <= t <= gust_t + gust_len:
            uw += 0.5 * gust * (1 - math.cos(2 * math.pi * (t - gust_t) / gust_len))
        V_g = math.hypot(vx, vz)
        if turb > 0:
            a_t = max(V_g, 1.0) / Lt
            turb_u += (-a_t * turb_u) * dt + turb * math.sqrt(2 * a_t * dt) * rng.standard_normal()
            uw += turb_u
        vax, vaz = vx - uw, vz      # air-relative velocity (wind blows toward +x)
        Va = math.hypot(vax, vaz)
        rho = float(C.rho_at(max(z, 0))) * veh.rho_scale
        qbar = 0.5 * rho * Va * Va
        # body axis unit vector (tilt th from vertical toward +x)
        bx, bz = math.sin(th), math.cos(th)
        nx, nz = math.cos(th), -math.sin(th)      # normal (+ toward +x when th=0)
        if Va > 0.5:
            # angle of attack: angle from body axis to the relative wind (+ve -> pushes nose to +x... )
            va_b = vax * bx + vaz * bz; va_n = vax * nx + vaz * nz
            alpha = math.atan2(va_n, va_b)
        else:
            alpha = 0.0; va_b = Va
        A = C.A_REF
        Fn = 0.0; Mz = 0.0; hm = 0.0; m_del = 0.0
        if Va > 0.5:
            def comp(cna, xs, extra=0.0):
                a_loc = alpha - q * (xs - cg) / 1000 / max(Va, 1.0)
                return -qbar * A * cna * (a_loc + extra)
            # sign: positive alpha (air from +n side) produces force toward -n
            for cna, xs in ((veh.cna_n, veh.x_n), (veh.cna_r, veh.x_r)):
                f = comp(cna, xs); Fn += f; Mz += f * (xs - cg) / 1000 * (-1)
            # control fins: pitch pair (A) deflects; yaw pair (B) only sees alpha in this plane
            # but in the pitch plane the pair whose span is normal to the plane is the one that
            # lifts -> pair A (all four fins share one station).
            bl, _ = C.bl_effectiveness(veh.H, veh.x_cA / 1000, Va, z)
            cna_pair = 2 * veh.cna_1 * veh.Kc * bl
            a_loc = alpha - q * (veh.x_cA - cg) / 1000 / max(Va, 1.0)
            f_c = -qbar * A * (cna_pair * a_loc + 2 * veh.cna_1 * veh.k_defl * bl * (dl + fb))
            Fn += f_c; Mz += -f_c * (veh.x_cA - cg) / 1000
            # trailing-vortex load the lifting pair induces on the fixed fins (alpha AND delta)
            f_i = veh.interf * f_c
            Fn += f_i; Mz += -f_i * (veh.x_r - cg) / 1000
            # control moment derivative M_delta (N m per rad) incl. the vortex load on the fixed fins
            m_del = qbar * A * 2 * veh.cna_1 * veh.k_defl * bl * ((veh.x_cA - cg) + veh.interf * (veh.x_r - cg)) / 1000
            # hinge moment per fin
            fin_force = abs(qbar * A * veh.cna_1 * bl * (a_loc + dl))
            hm = fin_force * HINGE_ARM_FRAC * veh.chord
        # ---- control law
        dc = 0.0; ref = 0.0; inj = 0.0
        active = control and not on_rail and (ctrl_until != "burnout" or t < tb + 0.5)
        if ctrl_until == "firmware" and t > tb and qbar < CTRL_END_QBAR: active = False   # fc_config WYV_CTRL_END_QBAR
        if isinstance(ctrl_until, (tuple, list)) and ctrl_until[0] == "q" and t > tb and qbar < ctrl_until[1]: active = False
        if active and not on_rail and apo is None: ctrl_time += dt
        dema += (dl - dema) * min(dt / 0.05, 1.0)
        if active and maneuver and not man_state["aborted"]:
            for ev in maneuver:
                t0 = ev["t0"]
                if ev is maneuver[0] and abs(t - t0) < dt / 2 + 1e-9:
                    # programme gates, checked once at t_man0 (firmware does the same)
                    man_gate_ok = qbar >= MAN_GATE["qbar_min"] and abs(th) * R2D <= MAN_GATE["tilt_max_deg"] and z >= MAN_GATE["alt_min_m"]
                    man_state["th_man0"] = th
                    if not man_gate_ok: man_state["skipped"] = True
                if not man_gate_ok: break
                if ev["kind"] == "doublet" and t0 <= t < t0 + 2 * ev["dur"]:
                    inj = (ev["amp_deg"] if t < t0 + ev["dur"] else -ev["amp_deg"]) * D2R
                elif ev["kind"] == "step" and t0 <= t < t0 + ev["dur"]:
                    if "th_step0" not in ev:
                        # step is relative to the attitude at its start; needs fin headroom
                        # direction: the one that LOWERS the fin demand (lets the airframe weathercock a
                        # little), so a pair already holding off a crosswind still has room to move
                        ev["sign"] = -1.0 if dema * R2D > 0.5 else 1.0
                        ev["th_step0"] = th; ev["d0"] = dema * R2D
                        ev["headroom_ok"] = abs(dema) * R2D <= MAN_GATE["headroom_deg"]
                        if not ev["headroom_ok"]: man_state["step_skipped"] = True
                    if ev["headroom_ok"]: ref = ev["th_step0"] + ev["sign"] * ev["amp_deg"] * D2R
            if "th_man0" in man_state and abs(th - man_state["th_man0"]) * R2D > MAN_GATE["dev_abort_deg"]:
                man_state["aborted"] = True; ref = inj = 0.0
        if active and apo is None:
            sched = min(max(gains["q_ref"] / max(qbar, 1.0), gains["k_min"]), gains["k_max"])
            err = ref - th
            integ = min(max(integ + err * dt, -0.2), 0.2)
            dc = sched * (gains["kp"] * err + gains["ki"] * integ - gains["kd"] * q)
            # sign: +delta -> fin force toward -n aft of CG -> +theta torque, so the PID output
            # (negative for +theta) maps directly onto delta.
            dc += inj
            dmax = defl_max_deg * D2R
            dc = min(max(dc, -dmax), dmax)
        rate_lim = wmax * max(0.05, 1 - hm / Tst)
        ddl = (dc - dl) / SERVO_TAU
        if abs(ddl) > rate_lim:
            ddl = math.copysign(rate_lim, ddl); sat_time += dt
        dl += ddl * dt
        # ---- forces
        Cd = C.cd_total(Va, z, veh.H, veh.rect_span, motor_burning=t < tb)
        Dr = qbar * A * Cd * veh.cd_scale
        # ---- split-fin airbrake (rev 3d): fins 0/1 at +db/-db, fins 2/3 at -db/+db. Side forces and
        # rolling couples cancel; each fin's normal force tilted by db adds drag N sin(db). It only
        # gets the deflection the attitude loop leaves free, so control authority is never reduced.
        if brake and t > tb + brake.get("after_burn", 0.0) and apo is None and Va > 1.0:
            bl_b, _ = C.bl_effectiveness(veh.H, veh.x_cA / 1000, Va, z)
            kfin = 4 * A * veh.cna_1 * veh.Kc * bl_b          # per unit q, per rad of brake (normal force)
            k0 = 0.5 * rho * A * Cd * veh.cd_scale            # body drag constant (N per (m/s)^2)
            vz_ = max(vz, 0.0)
            def h_apo(kk):                                    # vertical coast with quadratic drag
                return z + (M / (2 * kk)) * math.log(1 + kk * vz_ * vz_ / (M * C.G0)) if kk > 1e-9 else z + vz_ * vz_ / (2 * C.G0)
            hpred = h_apo(k0)
            dfree = max(defl_max_deg * D2R - abs(dc), 0.0)
            want = 0.0
            if hpred > brake["target_m"] and dfree > 0:
                lo_, hi_ = 0.0, dfree                         # smallest brake that brings the prediction to target
                for _ in range(24):
                    mid = 0.5 * (lo_ + hi_)
                    kk = k0 + 0.5 * rho * kfin * mid * math.sin(mid)
                    if h_apo(kk) > brake["target_m"]: lo_ = mid
                    else: hi_ = mid
                want = hi_
            db += max(min((want - db) / SERVO_TAU * dt, wmax * dt), -wmax * dt)
            db = min(db, dfree)
            Dr += qbar * kfin * db * math.sin(db)
        else:
            db = 0.0
        Fx = T * bx - Dr * (vax / Va if Va > 0 else 0) + Fn * nx
        Fz = T * bz - Dr * (vaz / Va if Va > 0 else 0) + Fn * nz - M * C.G0
        if on_rail:
            # constrained along the rail axis
            Fa = Fx * bx + Fz * bz
            if Fa < 0 and z <= 0.0: Fa = 0.0
            a = Fa / M
            v = (vx * bx + vz * bz) + a * dt
            vx, vz = v * bx, v * bz
            q = 0.0
            if math.hypot(x, z) >= C.RAIL_LEN_M - 0.15:
                on_rail = False; rail_exit = (t, v)
        else:
            vx += Fx / M * dt; vz += Fz / M * dt
            q += Mz / I * dt
            th += q * dt
        x += vx * dt; z += vz * dt; t += dt
        maxq = max(maxq, qbar); max_hm = max(max_hm, hm)
        if apo is None and t > tb and vz < 0:
            apo = (t, z)
            if not record: break
        if record and int(t / dt) % 10 == 0:
            for k, v_ in zip(hist, (t, x, z, Va, th * R2D, q * R2D, dl * R2D, dc * R2D,
                                    alpha * R2D, qbar, hm, uw, ref * R2D, inj * R2D,
                                    m_del / I / max(qbar, 1.0), m_del, db * R2D, hpred)):
                hist[k].append(v_)
        if apo is not None and t > apo[0] + 0.5: break
    H = {k: np.array(v) for k, v in hist.items()}
    res = dict(rail_exit_t=rail_exit[0] if rail_exit else None,
               rail_exit_v=rail_exit[1] if rail_exit else None,
               apogee_m=apo[1] if apo else None, t_apogee=apo[0] if apo else None,
               max_q_Pa=maxq, max_hinge_Nm=max_hm, servo_rate_sat_s=sat_time, ctrl_time_s=ctrl_time,
               v_burnout=float(np.interp(tb, H["t"], H["v"])) if record and len(H["t"]) else None)
    if record and len(H["t"]):
        m = (H["t"] >= (res["rail_exit_t"] or 0)) & (H["t"] <= tb + 2.0)
        res["tilt_rms_deg"] = float(np.sqrt(np.mean(H["th"][m] ** 2)))
        res["tilt_max_deg"] = float(np.max(np.abs(H["th"][m])))
        res["tilt_at_apogee_deg"] = float(H["th"][-1])
        res["drift_m"] = float(H["x"][-1])
        res["defl_max_deg"] = float(np.max(np.abs(H["dl"])))
    if maneuver:
        res["maneuver"] = maneuver_metrics(H, maneuver, man_state)
    return res, H

# ------------------------------------------------------------------------------------------------
# Authority-demonstration manoeuvre (mirrors ManeuverSeq in firmware controller.h / fc_config.h)
#   t_man0 = burnout + 0.25 s, then (ms after t_man0):
#     0    doublet axis A  +/-5 deg injected on top of the PID, 120 ms each half
#     400  doublet axis B                                  -> M_delta / I by least squares
#     800  attitude step axis A +1 deg, held 500 ms, then back to 0 for 400 ms
#     1700 attitude step axis B, same                      -> tilt per degree of fin, t63, overshoot
#   gates (checked once at t_man0): qbar >= 800 Pa, tilt <= 10 deg, altitude >= 30 m
#   each step: relative to the attitude at its start, in the direction that lowers the pair's current
#   deflection (a crosswind already has the fins working), skipped if the pair is at > 14 deg
#   abort (any time): tilt more than 8 deg away from the t_man0 attitude -> programme dropped
# The step is 1 deg because this airframe is stability-dominated: at ~1.9 kPa a 1 deg attitude
# change takes ~11 deg of fin (trim gradient ~0.09 deg/deg), so 4 deg would just saturate the fins.
MAN_T0_AFTER_BURN = 0.25
MAN = dict(doublet_deg=5.0, doublet_half=0.12, step_deg=1.0, hold=0.5, rest=0.4,
           offsets=dict(dA=0.0, dB=0.4, sA=0.8, sB=1.7))
MAN_GATE = dict(qbar_min=800.0, tilt_max_deg=10.0, alt_min_m=30.0, dev_abort_deg=8.0, headroom_deg=14.0)
FIT_TAIL = 0.16           # s of free response kept after the doublet in the fit window

def maneuver_events(tb, axis="A"):
    """Pitch-plane event list. The 3-DOF model has one plane, so axis B is predicted by running the
    same airframe with the B events (same station, same arm, later and lower q)."""
    t0 = tb + MAN_T0_AFTER_BURN; o = MAN["offsets"]
    d = o["dA"] if axis == "A" else o["dB"]; s_ = o["sA"] if axis == "A" else o["sB"]
    return [dict(kind="doublet", t0=t0 + d, dur=MAN["doublet_half"], amp_deg=MAN["doublet_deg"]),
            dict(kind="step", t0=t0 + s_, dur=MAN["hold"], amp_deg=MAN["step_deg"], rest=MAN["rest"])]

def _fit_b(qd, th, w, dl):
    """omega_dot = c + a*theta + m_q*omega + b*delta (least squares) -> b and its t-statistic.
    Firmware AuthorityMonitor solves the same 4x4 normal equations."""
    X = np.column_stack([np.ones_like(dl), th, w, dl])
    beta, *_ = np.linalg.lstsq(X, qd, rcond=None)
    r = qd - X @ beta; n = len(qd)
    s2 = float(r @ r) / max(n - 4, 1)
    cov = s2 * np.linalg.pinv(X.T @ X)
    return float(beta[3]), float(beta[3] / math.sqrt(max(cov[3, 3], 1e-30)))

def maneuver_metrics(H, events, man_state):
    t = H["t"]; out = dict(skipped=man_state["skipped"], aborted=man_state["aborted"],
                           step_skipped=man_state.get("step_skipped", False))
    th = H["th"] * D2R; w = H["q"] * D2R; dl = H["dl"] * D2R
    qd = np.concatenate([[0.0], np.diff(w) / np.diff(t)])     # backward difference, as the firmware does
    if man_state["skipped"]:
        return out
    for ev in events:
        t0 = ev["t0"]
        if ev["kind"] == "doublet":
            if np.std(H["inj"][(t >= t0) & (t < t0 + 2 * ev["dur"])]) < 0.5 * ev["amp_deg"]:
                continue          # doublet was cut short by an abort
            m = (t >= t0) & (t < t0 + 2 * ev["dur"] + FIT_TAIL); m[np.argmax(m)] = False   # first sample has no difference
            if m.sum() < 10: continue
            b, tst = _fit_b(qd[m], th[m], w[m], dl[m])
            b_true = float(np.mean(H["bq"][m] * H["qbar"][m]))
            out["doublet"] = dict(t0=t0, qbar_Pa=float(np.mean(H["qbar"][m])), b_fit=b, t_stat=tst,
                                  b_model=b_true, b_ratio=b / b_true if b_true else None,
                                  b_per_q=float(np.mean(H["bq"][m])),
                                  peak_rate_dps=float(np.max(np.abs(H["q"][m]))))
        elif ev.get("headroom_ok", False):
            A = ev["amp_deg"]; t1 = t0 + ev["dur"]; t2 = t1 + ev.get("rest", 0.4)
            i0 = np.searchsorted(t, t0); th0 = H["th"][i0]
            d0 = ev.get("d0", 0.0)
            sg = ev.get("sign", 1.0)
            m = (t >= t0) & (t < t1); y = sg * (H["th"][m] - th0); tt = t[m] - t0
            last = tt >= ev["dur"] - 0.2
            ach = float(np.mean(y[last]))
            k63 = np.nonzero(y >= 0.63 * ach)[0] if ach > 0 else []
            mr = (t >= t1) & (t < t2); yr = sg * (H["th"][mr] - th0); tr = t[mr] - t1
            kr = np.nonzero(yr <= 0.37 * ach)[0] if ach > 0 else []
            dfin = float(np.mean(H["dl"][m][last])) - d0
            out["step"] = dict(t0=t0, amp_deg=A, sign=sg, qbar_Pa=float(np.mean(H["qbar"][m])),
                               achieved_deg=ach, achieved_frac=ach / A,
                               t63_s=float(tt[k63[0]]) if len(k63) else None,
                               overshoot_pct=float(max(0.0, (y.max() - ach) / ach * 100)) if ach > 0 else None,
                               fin_per_deg=abs(dfin) / ach if ach > 0 else None,
                               trim_gradient_deg_per_deg=ach / abs(dfin) if dfin else None,
                               peak_defl_deg=float(np.max(np.abs(H["dl"][m]))),
                               peak_rate_dps=float(np.max(np.abs(H["q"][m]))),
                               return63_s=float(tr[kr[0]]) if len(kr) else None)
    return out

def run_maneuver(veh=None, wind=4.0, gust=0.0, turb=0.5, seed=3, gains=None, dt=0.0005):
    """Predicted manoeuvre on the flight vehicle, axis A and axis B, plus a fins-active reference
    run with no manoeuvre (the difference is what the flight should show)."""
    veh = veh or Vehicle(C.FLIGHT_MOTOR); gains = gains or GAINS_FLIGHT; tb = veh.motor["tb"]
    out = {}; Hs = {}
    for ax_ in ("A", "B"):
        r, H = simulate(veh, wind=wind, gust=gust, turb=turb, seed=seed, gains=gains, dt=dt,
                        ctrl_until="firmware", maneuver=maneuver_events(tb, ax_))
        out[ax_] = r["maneuver"]; out[ax_]["apogee_m"] = r["apogee_m"]; Hs[ax_] = H
    r0, H0 = simulate(veh, wind=wind, gust=gust, turb=turb, seed=seed, gains=gains, dt=dt, ctrl_until="firmware")
    out["reference_apogee_m"] = r0["apogee_m"]; Hs["ref"] = H0
    out["t_man0_s"] = tb + MAN_T0_AFTER_BURN
    out["ctrl_end_time_s"] = float(H0["t"][np.nonzero((H0["t"] > tb) & (H0["qbar"] < CTRL_END_QBAR))[0][0]])
    return out, Hs

def maneuver_monte_carlo(n=40, seed0=100):
    """Spread of the manoeuvre metrics over wind 0-7 m/s, turbulence 0-1.5 m/s, launch tilt 0-3 deg:
    what range the flight result should land in if the model is right."""
    veh = Vehicle(C.FLIGHT_MOTOR); tb = veh.motor["tb"]; rng = np.random.default_rng(seed0)
    rows = []
    for i in range(n):
        wind = rng.uniform(0, 7); turb = rng.uniform(0, 1.5); lt = rng.uniform(0, 3)
        for ax_ in ("A", "B"):
            r, _ = simulate(veh, wind=wind, gust=0.0, turb=turb, seed=seed0 + i, gains=GAINS_FLIGHT,
                            dt=0.001, ctrl_until="firmware", launch_tilt_deg=lt, maneuver=maneuver_events(tb, ax_))
            M = r["maneuver"]; d = M.get("doublet", {}); s_ = M.get("step", {})
            rows.append(dict(axis=ax_, wind=wind, turb=turb, launch_tilt=lt, skipped=M["skipped"], aborted=M["aborted"],
                             step_skipped=M["step_skipped"],
                             b_ratio=d.get("b_ratio"), t_stat=d.get("t_stat"), qbar_doublet=d.get("qbar_Pa"),
                             achieved_deg=s_.get("achieved_deg"), t63_s=s_.get("t63_s"), fin_per_deg=s_.get("fin_per_deg"),
                             qbar_step=s_.get("qbar_Pa")))
    def stat(key, ax_):
        v = np.array([r[key] for r in rows if r["axis"] == ax_ and r[key] is not None and not r["skipped"]], float)
        return dict(mean=float(v.mean()), sd=float(v.std()), p05=float(np.percentile(v, 5)), p95=float(np.percentile(v, 95))) if len(v) else None
    summ = {ax_: {k: stat(k, ax_) for k in ("b_ratio", "t_stat", "achieved_deg", "t63_s", "fin_per_deg", "qbar_step")} for ax_ in ("A", "B")}
    summ["n"] = n; summ["skipped"] = sum(r["skipped"] for r in rows); summ["aborted"] = sum(r["aborted"] for r in rows)
    summ["step_skipped"] = sum(r["step_skipped"] for r in rows)
    return summ, rows

def plot_maneuver(out, Hs, path):
    fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    t0 = out["t_man0_s"]
    for k, c in (("A", "#2a6f97"), ("B", "#bc4749")):
        H = Hs[k]
        ax[0].plot(H["t"], H["th"], c=c, label=f"tilt, programme {k}")
        ax[0].plot(H["t"], H["ref"], c=c, ls=":", lw=1, label=f"reference {k}")
        ax[1].plot(H["t"], H["dl"], c=c, label=f"pair deflection {k}")
        ax[1].plot(H["t"], H["inj"], c=c, ls=":", lw=1, label=f"doublet injection {k}")
        ax[2].plot(H["t"], H["q"], c=c, label=f"pitch rate {k}")
    ax[0].plot(Hs["ref"]["t"], Hs["ref"]["th"], c="0.5", lw=1, label="no manoeuvre")
    a2 = ax[2].twinx(); a2.plot(Hs["ref"]["t"], Hs["ref"]["qbar"], c="0.6", ls="--", lw=1); a2.set_ylabel("qbar (Pa)", color="0.5")
    for a, yl in zip(ax, ("tilt (deg)", "deflection (deg)", "rate (deg/s)")):
        a.set_ylabel(yl); a.grid(alpha=.3); a.legend(fontsize=8, loc="upper right"); a.axvline(t0, c="k", lw=.6, ls="--")
    ax[2].set_xlabel("t (s)"); ax[0].set_xlim(t0 - 0.3, t0 + 2.9)
    sA, sB = out["A"].get("step", {}), out["B"].get("step", {})
    dA, dB = out["A"].get("doublet", {}), out["B"].get("doublet", {})
    fig.suptitle(f"Authority manoeuvre (predicted): +/-{MAN['doublet_deg']:.0f} deg doublets, then {MAN['step_deg']:.0f} deg attitude steps\n"
                 f"doublet A at {dA.get('qbar_Pa', 0):.0f} Pa: M_delta/I = {dA.get('b_model', 0):.1f} 1/s^2, fit/model {dA.get('b_ratio', 0) or 0:.2f}   "
                 f"doublet B at {dB.get('qbar_Pa', 0):.0f} Pa: fit/model {dB.get('b_ratio', 0) or 0:.2f}\n"
                 f"step A at {sA.get('qbar_Pa', 0):.0f} Pa: {sA.get('achieved_deg', 0):.2f} deg achieved, t63 {sA.get('t63_s') or 0:.2f} s, "
                 f"{sA.get('fin_per_deg') or 0:.1f} deg fin per deg   step B at {sB.get('qbar_Pa', 0):.0f} Pa: {sB.get('achieved_deg', 0):.2f} deg, "
                 f"{sB.get('fin_per_deg') or 0:.1f} deg fin per deg", fontsize=9.5)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)

def tune(veh, wind=4.0, gust=4.0):
    best = None
    for kp in (1.0, 2.0, 3.0, 4.5):
        for kd in (0.15, 0.3, 0.5, 0.8):
            for ki in (0.0, 0.5, 1.0):
                g = dict(GAINS, kp=kp, kd=kd, ki=ki)
                r, _ = simulate(veh, wind, gust, gains=g, dt=0.001, turb=0.8)
                score = r["tilt_rms_deg"] + 0.2 * r["tilt_max_deg"] + 2.0 * r["servo_rate_sat_s"]
                if best is None or score < best[0]: best = (score, g, r)
    return best

if __name__ == "__main__":
    summary = {}
    import sys
    fast = "--fast" in sys.argv
    # --- tune on the flight configuration, then use those gains everywhere
    if "--retune" in sys.argv or not os.path.exists(_TG):
        best = tune(Vehicle(C.FLIGHT_MOTOR))
        GAINS_FLIGHT.update(best[1]); json.dump(best[1], open(_TG, "w"), indent=1)
    summary["gains"] = GAINS_FLIGHT
    # --- motor trade, same airframe
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    for mot, col in zip(C.MOTORS, ("#2a6f97", "#bc4749", "#386641")):
        veh = Vehicle(mot)
        r_off, Hoff = simulate(veh, control=False)
        r_on, Hon = simulate(veh, control=True, gains=GAINS_FLIGHT)
        summary[mot] = dict(liftoff_g=round(veh.M0 * 1000, 1), cg0=round(veh.cg0, 1),
                            control_off=r_off, control_on=r_on,
                            TW_avg=round(veh.motor["avg"] / (veh.M0 * C.G0), 2))
        ax[0, 0].plot(Hon["t"], Hon["z"], c=col, label=f"{mot} (on)")
        ax[0, 0].plot(Hoff["t"], Hoff["z"], c=col, ls="--", label=f"{mot} (fins locked)")
        ax[0, 1].plot(Hon["t"], Hon["v"], c=col, label=mot)
        ax[1, 0].plot(Hon["t"], Hon["th"], c=col, label=f"{mot} on")
        ax[1, 0].plot(Hoff["t"], Hoff["th"], c=col, ls="--", label=f"{mot} locked")
        ax[1, 1].plot(Hon["t"], Hon["dl"], c=col, label=mot)
    for a, yl in zip(ax.flat, ("altitude (m)", "airspeed (m/s)", "tilt from vertical (deg)", "pitch-pair deflection (deg)")):
        a.set_ylabel(yl); a.set_xlabel("t (s)"); a.grid(alpha=.3); a.legend(fontsize=8)
    fig.suptitle("Motor trade on the fin-control airframe (4 m/s wind + 4 m/s 1-cos gust at 1.2 s)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "A_motor_trade.png"), dpi=130); plt.close(fig)
    # --- deploy timing per delay
    for mot in C.MOTORS:
        r = summary[mot]["control_on"]; tb = C.MOTORS[mot]["tb"]
        coast = r["t_apogee"] - tb
        summary[mot]["optimal_delay_s"] = round(coast, 2)
        summary[mot]["delay_pick"] = min(C.MOTORS[mot]["delays"], key=lambda d: abs(d - coast) if d > 0 else 99)
    # --- authority-demonstration manoeuvre (firmware programme), flight motor
    man, Hs = run_maneuver()
    summary["maneuver"] = man
    json.dump(man, open(os.path.join(OUT, "maneuver_prediction.json"), "w"), indent=2, default=float)
    plot_maneuver(man, Hs, os.path.join(OUT, "B_authority_maneuver.png"))
    if not fast:
        mc, rows = maneuver_monte_carlo()
        man["monte_carlo"] = mc
        json.dump(man, open(os.path.join(OUT, "maneuver_prediction.json"), "w"), indent=2, default=float)
    json.dump(summary, open(os.path.join(OUT, "flight_summary.json"), "w"), indent=2, default=float)
    print(json.dumps(summary, indent=2, default=float))
