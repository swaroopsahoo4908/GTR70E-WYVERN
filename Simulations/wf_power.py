#!/usr/bin/env python3
"""GTR70E WYVERN -- battery budget: 25 min pad idle + ~1 min powered/coast flight, 2S LiPo.

Current draws are datasheet/typical values (sources in Documentation/Electronics_Power.md) at the
loads' own rails, referred to the pack through the D24V10F5 buck (eta 0.88) or directly (servos are
HV and run straight off the switched 2S rail). Bench-measure the servo idle current: digital
coreless servos vary 5-40 mA idle at 7.4 V depending on hold behaviour.
"""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C

OUT = os.path.join(C.HERE, "plots_power"); os.makedirs(OUT, exist_ok=True)
V_PACK = 7.6; ETA_BUCK = 0.88; V_LOGIC = 5.0
# (name, rail, idle_mA, flight_mA)
LOADS = [
    ("RP2040 @125 MHz + Feather 3V3 LDO quiescent", "5V", 26.0, 30.0),
    ("RFM95W 915 MHz: pad 2 Hz / flight 20 Hz @ +20 dBm, 21.8 ms packets", "5V", 0.044 * 120 + 1.6, 0.44 * 120 + 1.6),
    ("BNO085 (game rotation vector 400 Hz + accel/gyro)", "5V", 12.0, 12.0),
    ("BME688 (T/P/H 50 Hz, gas heater off)", "5V", 0.9, 0.9),
    ("ADXL375 high-g accel, 800 Hz ODR", "5V", 0.14, 0.14),
    ("microSD write (avg; 100 Hz frames, 512 B blocks)", "5V", 8.0, 30.0),
    ("status LED / buzzer (pad beacon, 10 % duty)", "5V", 2.0, 0.0),
    ("Pololu 2810 switch (on-state ~210 uA/V)", "PACK", 1.6, 1.6),
    ("4 x KST X08 Plus idle hold (digital, PWM active)", "PACK", 4 * 15.0, 0.0),
    ("4 x KST X08 Plus active (avg over 1 min, bench-calibrate)", "PACK", 0.0, 4 * 180.0),
]
T_IDLE_MIN, T_FLIGHT_MIN = 25.0, 1.0

def at_pack(mA, rail):
    return mA if rail == "PACK" else mA * V_LOGIC / (V_PACK * ETA_BUCK)

if __name__ == "__main__":
    idle = sum(at_pack(l[2], l[1]) for l in LOADS)
    flight = sum(at_pack(l[3], l[1]) for l in LOADS)
    mAh = idle * T_IDLE_MIN / 60 + flight * T_FLIGHT_MIN / 60
    # derating: 80 % usable depth, x0.85 cold (5 C Nov field), x1.25 ageing/measurement margin
    need = mAh / 0.80 / 0.85 * 1.25
    pack = C.BATTERY["mAh"]
    res = dict(idle_mA=idle, flight_mA=flight, mission_mAh=mAh, required_with_derating_mAh=need,
               pack_mAh=pack, margin_x=pack / need,
               max_pad_hold_min_on_pack=(pack * 0.8 * 0.85 - flight * T_FLIGHT_MIN / 60) / idle * 60,
               loads=[dict(name=n, rail=r, idle_mA=round(i, 2), flight_mA=round(f, 2),
                           idle_at_pack_mA=round(at_pack(i, r), 2), flight_at_pack_mA=round(at_pack(f, r), 2))
                      for n, r, i, f in LOADS])
    json.dump(res, open(os.path.join(OUT, "battery_budget.json"), "w"), indent=2)
    t = np.linspace(0, 40, 400)
    used = np.where(t <= T_IDLE_MIN, idle * t / 60, idle * T_IDLE_MIN / 60 + flight * np.minimum(t - T_IDLE_MIN, T_FLIGHT_MIN) / 60
                    + idle * np.clip(t - T_IDLE_MIN - T_FLIGHT_MIN, 0, None) / 60)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t, used, lw=2, label="consumed (nominal)")
    ax.axhline(pack * 0.8 * 0.85, c="#bc4749", ls="--", label=f"usable {pack} mAh pack (80 % DoD, cold)")
    ax.axhline(need, c="#386641", ls=":", label=f"mission requirement incl. margins ({need:.0f} mAh)")
    ax.axvspan(T_IDLE_MIN, T_IDLE_MIN + T_FLIGHT_MIN, color="#e09f3e", alpha=.25, label="flight minute")
    ax.set(xlabel="time since power-on (min)", ylabel="charge used (mAh)",
           title=f"2S budget: idle {idle:.0f} mA, flight {flight:.0f} mA at the pack"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "battery_budget.png"), dpi=130); plt.close(fig)
    print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in res.items() if k != "loads"}, indent=1))
