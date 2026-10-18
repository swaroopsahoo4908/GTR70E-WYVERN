#!/usr/bin/env python3
"""GTR70E WYVERN -- ejection bypass tube: diameter trade, lumped-volume gas dynamics.

The motor's ejection charge fires into a small PC-FR plenum over the motor cap, runs up an
central aluminium bypass tube up the vehicle axis, through the servo ring and the avionics spine, and pressurises the recovery bay,
which pushes the nose off. Nothing else separates.

Three control volumes, ideal gas with BP-product properties, isentropic orifice flow
(choked/unchoked) between them, convective wall heat loss in each, and a 1.5 mm vent from the bay:

   plenum (V_p, PC-FR walls)  --tube inlet-->  tube (V_t = pi/4 d^2 L, Al wall)  --exit-->  bay (V_b)

Charge: m_bp grams of black powder burned over ~5 ms (triangular rate), lumped with the rocketry
convention R*T = 22.16 ft-lbf/lbm-R x 3307 R = 219 J per gram of powder, gamma 1.25; wall heat loss
is what makes the delivered pressure fall below that ideal.
The motor's charge is fixed (single-use AeroTech / Estes), so the sweep is over 0.40-0.80 g and
the design must work at the low end. A ground ejection test on the real stack is required before
flight; this model sizes the tube, it does not replace that test.

Outputs -> plots_bypass/: A_bay_pressure_vs_d.png, B_traces.png, bypass_trade.json
"""
import json, math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C

OUT = os.path.join(C.HERE, "plots_bypass"); os.makedirs(OUT, exist_ok=True)
GAM = 1.25
RT_BP = 219.0e3        # J/kg of products (ideal-gas R*T at flame temperature)
T_FLAME = 2000.0       # K, effective products temperature entering the plenum
R_G = RT_BP / T_FLAME  # J/kg/K
GAS_YIELD = 1.0    # lumped: the 219 J/g R*T convention is applied per gram of POWDER
CV = R_G / (GAM - 1)
P_AMB, T_AMB = 101325.0, 288.0
H_BAY = 150.0   # W/m2K, bay mixing; tuned so a closed bay reaches ~60 % of the adiabatic ideal

# Volumes
V_PLENUM = (math.pi * (C.RI - 2.0) ** 2 * C.GALLERY_H) * 1e-9  # full-bore gas gallery
BAY_L = (C.X_RB_BOT - 1.5) - (C.X_RB_TOP + C.NOSE["shoulder"])            # free bay length, mm
V_BAY_GROSS = math.pi * C.RI ** 2 * BAY_L * 1e-9
V_PACKED = 230e-6      # chute + Nomex + cord + quick links, m^3 (measure; ~1/3 of the bay)
V_BAY = V_BAY_GROSS - V_PACKED
A_BAY = math.pi * C.RI ** 2 * 1e-6                                         # nose piston area
SHEAR_PINS = dict(n=2, size="#2-56 nylon", F_each_N=110.0)                 # ~25 lbf each (measure)
F_FRICTION = 15.0                                                          # N, nose shoulder fit
A_MOTOR = math.pi * (C.MOTOR_D / 2) ** 2 * 1e-6

def mdot_orifice(p_up, T_up, p_dn, A, cd=0.8):
    if p_up <= p_dn or A <= 0: return 0.0
    pr = p_dn / p_up
    crit = (2 / (GAM + 1)) ** (GAM / (GAM - 1))
    if pr <= crit:
        return cd * A * p_up * math.sqrt(GAM / (R_G * T_up)) * (2 / (GAM + 1)) ** ((GAM + 1) / (2 * (GAM - 1)))
    return cd * A * p_up * math.sqrt(2 * GAM / ((GAM - 1) * R_G * T_up) * (pr ** (2 / GAM) - pr ** ((GAM + 1) / GAM)))

def run(d_mm=C.BYPASS["id"], L_mm=C.BYPASS["L"], m_bp_g=0.6, t_end=0.25, dt=2e-6, h_wall=600.0):
    A_t = math.pi / 4 * (d_mm * 1e-3) ** 2
    V_t = A_t * L_mm * 1e-3
    vols = [V_PLENUM, V_t, V_BAY]
    A_wall = [7e-3, math.pi * d_mm * 1e-3 * L_mm * 1e-3, 0.05]   # plenum, tube, bay wall m^2
    # initial air in each volume
    m = [P_AMB * v / (287.0 * T_AMB) for v in vols]
    U = [m[i] * (287.0 / (GAM - 1)) * T_AMB for i in range(3)]   # treat as one mixed gas (cv approx)
    m_gas_total = m_bp_g * 1e-3 * GAS_YIELD
    t_burn = 0.005
    A_vent = math.pi / 4 * (1.5e-3) ** 2
    hist = []; t = 0.0; released = None; peak = [0, 0, 0]
    while t < t_end:
        # source: triangular burn
        rate = 0.0
        if t < t_burn:
            rate = m_gas_total * (2 / t_burn) * (1 - abs(2 * t / t_burn - 1))
        T = [U[i] / (m[i] * CV) for i in range(3)]
        p = [m[i] * R_G * T[i] / vols[i] for i in range(3)]
        # flows: plenum->tube (tube inlet area), tube->bay, bay->ambient vent
        f1 = mdot_orifice(p[0], T[0], p[1], A_t) - mdot_orifice(p[1], T[1], p[0], A_t)
        f2 = mdot_orifice(p[1], T[1], p[2], A_t) - mdot_orifice(p[2], T[2], p[1], A_t)
        f3 = mdot_orifice(p[2], T[2], P_AMB, A_vent)
        h = [lambda i, f: 0][0]
        def h_up(i, j, f):  # enthalpy carried: upstream stagnation
            src = i if f > 0 else j
            return f * (GAM * CV) * T[src]
        dm = [rate - f1, f1 - f2, f2 - f3]
        dU = [rate * GAM * CV * T_FLAME - h_up(0, 1, f1), h_up(0, 1, f1) - h_up(1, 2, f2), h_up(1, 2, f2) - f3 * GAM * CV * T[2]]
        for i, hh in zip(range(3), (h_wall, h_wall, H_BAY)):
            dU[i] -= hh * A_wall[i] * max(T[i] - T_AMB, 0)
        for i in range(3):
            m[i] += dm[i] * dt; U[i] += dU[i] * dt
            U[i] = max(U[i], m[i] * CV * T_AMB * 0.999)
        for i in range(3): peak[i] = max(peak[i], p[i])
        F_nose = (p[2] - P_AMB) * A_BAY
        if released is None and F_nose > SHEAR_PINS["n"] * SHEAR_PINS["F_each_N"] + F_FRICTION:
            released = t
        if int(t / dt) % 25 == 0:
            hist.append((t, p[0], p[1], p[2], T[2]))
        t += dt
        if released is not None and t > released + 0.02: break
    H = np.array(hist)
    return dict(d_mm=d_mm, V_tube_cm3=V_t * 1e6, V_bay_cm3=V_BAY * 1e6, m_bp_g=m_bp_g,
                peak_plenum_kPa=(peak[0] - P_AMB) / 1e3, peak_bay_kPa=(peak[2] - P_AMB) / 1e3,
                release_ms=None if released is None else released * 1e3,
                motor_kickout_N=(peak[0] - P_AMB) * A_MOTOR,
                nose_force_peak_N=(peak[2] - P_AMB) * A_BAY), H

if __name__ == "__main__":
    ds = sorted({4.0, 5.0, 6.0, 7.0, C.BYPASS["id"], 8.81, 10.0, 10.92, 12.0})
    charges = [0.3, 0.5, 0.7]
    res = {q: [run(d, m_bp_g=q, dt=4e-6)[0] for d in ds] for q in charges}
    need = SHEAR_PINS["n"] * SHEAR_PINS["F_each_N"] + F_FRICTION
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for q, col in zip(charges, ("#bc4749", "#2a6f97", "#386641")):
        rr = res[q]
        ax[0].plot(ds, [r["nose_force_peak_N"] for r in rr], "o-", c=col, label=f"{q:.1f} g BP")
        ax[1].plot(ds, [r["peak_plenum_kPa"] for r in rr], "o-", c=col, label=f"{q:.1f} g")
        ax[2].plot(ds, [r["release_ms"] if r["release_ms"] else np.nan for r in rr], "o-", c=col, label=f"{q:.1f} g")
    ax[0].axhline(need, ls="--", c="k"); ax[0].text(4, need * 1.03, f"release {need:.0f} N (2x #2-56 nylon + fit)", fontsize=8)
    for a in ax: a.axvline(C.BYPASS["id"], ls=":", c="gray"); a.grid(alpha=.3); a.legend(fontsize=8); a.set_xlabel("bypass tube ID (mm)")
    ax[0].set(ylabel="peak nose push-off force (N)", title="Bay pressure delivered to the nose")
    ax[1].set(ylabel="peak plenum gauge pressure (kPa)", title="Plenum spike (motor kick-out load)")
    ax[2].set(ylabel="time to nose release (ms)", title="Delivery time")
    fig.suptitle(f"Bypass tube trade, L = {C.BYPASS['L']:.0f} mm, bay free volume {V_BAY*1e6:.0f} cm³ — chosen {C.BYPASS['mat']} (ID {C.BYPASS['id']} mm); limited to 9.5 mm OD by the servo bases at r = {C.SERVO_BASE_R} mm")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "A_bay_pressure_vs_d.png"), dpi=130); plt.close(fig)
    r, H = run(C.BYPASS["id"], m_bp_g=0.5)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(H[:, 0] * 1e3, (H[:, 1] - P_AMB) / 1e3, label="plenum"); ax.plot(H[:, 0] * 1e3, (H[:, 2] - P_AMB) / 1e3, label="tube")
    ax.plot(H[:, 0] * 1e3, (H[:, 3] - P_AMB) / 1e3, label="recovery bay")
    ax.axhline(need / A_BAY / 1e3, ls="--", c="k", lw=1); ax.set_yscale("symlog", linthresh=10)
    ax.set(xlabel="t after charge (ms)", ylabel="gauge pressure (kPa)", title=f"0.5 g charge, {C.BYPASS['id']} mm ID bypass"); ax.grid(alpha=.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "B_traces.png"), dpi=130); plt.close(fig)
    out = dict(V_bay_cm3=V_BAY * 1e6, V_plenum_cm3=V_PLENUM * 1e6, release_force_N=need, results=res,
               chosen=dict(od_mm=C.BYPASS["od"], id_mm=C.BYPASS["id"], L_mm=C.BYPASS["L"], mass_g=C.bypass_mass()))
    json.dump(out, open(os.path.join(OUT, "bypass_trade.json"), "w"), indent=2, default=float)
    for q in charges:
        for r in res[q]:
            print(f"{q:.1f} g  d={r['d_mm']:5.2f}  Vt={r['V_tube_cm3']:5.1f} cm3  plenum={r['peak_plenum_kPa']:7.0f} kPa  "
                  f"bay={r['peak_bay_kPa']:6.1f} kPa  F={r['nose_force_peak_N']:6.0f} N  kick={r['motor_kickout_N']:6.0f} N  rel={r['release_ms']}")
