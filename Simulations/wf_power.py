#!/usr/bin/env python3
"""GTR70E WYVERN -- battery budget: 25 min pad idle + ~1 min powered/coast flight, 2S LiPo.
Rev 4b: Pico 2 W flight computer + Adafruit 4682 microSD, no radio, no high-g accelerometer.

Current draws are datasheet/typical values (sources in Documentation/Electronics_Power.md) at the
loads' own rails, referred to the pack through the Adafruit MPM3610 bucks (eta ~0.85): one for the logic,
a second for the four EMAX ES9251 II servos at 5.0 V (rev 3f). Bench-measure the servo currents: the vendor
gives about 100 mA moving and 300 mA stalled at 3.6 V for the coreless motor.
"""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C

OUT = os.path.join(C.HERE, "plots_power"); os.makedirs(OUT, exist_ok=True)
V_PACK = 7.6; ETA_BUCK = 0.85; V_LOGIC = 5.0; V_SERVO = 5.0; ETA_SERVO = 0.85
# (name, rail, idle_mA, flight_mA)
LOADS = [
    ("Pico 2 W, RP2350 @ 150 MHz, CYW43 radio off, incl. its RT6150 buck-boost (~30 mA)", "5V", 30.0, 30.0),
    ("BNO085 (game rotation vector 200 Hz + gyro/accel 400 Hz)", "5V", 12.0, 12.0),
    ("BMP388 normal mode 50 Hz, pressure x8 (Bosch DS: ~0.7 mA at this rate)", "5V", 0.7, 0.7),
    ("BME688 (T/P/H 10 Hz forced, gas heater off)", "5V", 0.9, 0.9),
    ("microSD on SPI, Adafruit 4682 (avg; 10 Hz on the pad unarmed / 100 Hz armed + flight, 512 B sectors)", "5V", 8.0, 30.0),
    ("arm LED 3 mm via 220 ohm (pad blink, ~5 % duty; off in flight)", "5V", 0.3, 0.0),
    ("Pololu 2810 switch (on-state ~210 uA/V)", "PACK", 1.6, 1.6),
    ("4 x EMAX ES9251 II idle hold (digital, PWM active), 5 V servo rail", "SRV", 4 * 10.0, 0.0),
    ("4 x EMAX ES9251 II active (avg over 1 min, bench-calibrate), 5 V servo rail", "SRV", 0.0, 4 * 80.0),
]
T_IDLE_MIN, T_FLIGHT_MIN = 25.0, 1.0

def at_pack(mA, rail):
    if rail == "PACK": return mA
    if rail in ("6V", "SRV"): return mA * V_SERVO / (V_PACK * ETA_SERVO)
    return mA * V_LOGIC / (V_PACK * ETA_BUCK)

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
