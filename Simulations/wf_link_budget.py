#!/usr/bin/env python3
"""GTR70E WYVERN -- 915 MHz LoRa downlink: time-on-air, rate, and link budget.

SX1276 (RFM95W) time-on-air per Semtech AN1200.13; sensitivity from the noise-floor form
S = -174 + 10 log10(BW) + NF + SNR_limit (NF 6 dB, SNR limit per SF from the SX1276 datasheet).
"""
import json, math, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import wf_core as C

OUT = os.path.join(C.HERE, "plots_link"); os.makedirs(OUT, exist_ok=True)
SNR_LIM = {6: -5, 7: -7.5, 8: -10, 9: -12.5, 10: -15, 11: -17.5, 12: -20}
PAYLOAD = 42         # bytes, binary telemetry frame (Flight Computer/firmware/wyvern_fin/telemetry.h)

def toa_ms(pl=PAYLOAD, sf=7, bw=500e3, cr=1, pre=8, crc=1, ih=0):
    ts = (2 ** sf) / bw
    de = 1 if ts > 16e-3 else 0
    n = 8 + max(math.ceil((8 * pl - 4 * sf + 28 + 16 * crc - 20 * ih) / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return ((pre + 4.25) + n) * ts * 1e3

def sens(sf, bw): return -174 + 10 * math.log10(bw) + 6 + SNR_LIM[sf]

def fspl(d_m, f=915e6): return 20 * math.log10(d_m) + 20 * math.log10(f) - 147.55

if __name__ == "__main__":
    # ground antenna: Linx ANT-916-CW-HW-SMA whip, 1.2 dBi (the Yagi was dropped in the BOM link pass)
    cfg = dict(sf=7, bw=500e3, tx_dBm=20, g_tx=2.1, g_rx=1.2, orient_loss=10.0, cable=1.0, fade=10.0)
    t = toa_ms(sf=cfg["sf"], bw=cfg["bw"])
    rate_max = 1000 / t
    s = sens(cfg["sf"], cfg["bw"])
    d = np.logspace(1, 4.3, 200)
    prx = cfg["tx_dBm"] + cfg["g_tx"] + cfg["g_rx"] - cfg["orient_loss"] - cfg["cable"] - np.array([fspl(x) for x in d])
    margin = prx - s
    _fs = os.path.join(C.HERE, "plots_flight", "flight_summary.json") if "C" in globals() else None
    try:
        import json as _j, wf_core as _C
        _ap = _j.load(open(os.path.join(_C.HERE, "plots_flight", "flight_summary.json")))[_C.FLIGHT_MOTOR]["control_on"]["apogee_m"]
    except Exception:
        _ap = 315.0
    slant = math.hypot(_ap + 15.0, 150.0)   # apogee + margin; 150 m stand-off at the RSO table
    m_slant = cfg["tx_dBm"] + cfg["g_tx"] + cfg["g_rx"] - cfg["orient_loss"] - cfg["cable"] - fspl(slant) - s
    rng = d[np.argmin(np.abs(margin - cfg["fade"]))]
    res = dict(config=cfg, payload_B=PAYLOAD, time_on_air_ms=t, max_rate_Hz=rate_max, flight_rate_Hz=20,
               duty_flight=20 * t / 1000, sensitivity_dBm=s, worst_slant_m=slant,
               margin_at_slant_dB=m_slant, range_at_10dB_fade_margin_m=float(rng),
               alt_configs={f"SF{sf}/BW{int(bw/1e3)}": dict(toa_ms=round(toa_ms(sf=sf, bw=bw), 2), sens_dBm=round(sens(sf, bw), 1))
                            for sf in (7, 8, 9) for bw in (125e3, 250e3, 500e3)})
    json.dump(res, open(os.path.join(OUT, "link_budget.json"), "w"), indent=2)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.semilogx(d, margin, lw=2); ax.axhline(cfg["fade"], ls="--", c="#bc4749", label="10 dB fade allowance")
    ax.axvline(slant, ls=":", c="k", label=f"worst flight slant range {slant:.0f} m")
    ax.set(xlabel="range (m)", ylabel="link margin (dB)", title=f"LoRa SF{cfg['sf']}/BW{int(cfg['bw']/1e3)} kHz, +{cfg['tx_dBm']} dBm, {PAYLOAD} B @ 20 Hz ({t:.1f} ms on air)")
    ax.grid(alpha=.3, which="both"); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "link_budget.png"), dpi=130); plt.close(fig)
    print(json.dumps({k: v for k, v in res.items() if k != "alt_configs"}, indent=1, default=float))
