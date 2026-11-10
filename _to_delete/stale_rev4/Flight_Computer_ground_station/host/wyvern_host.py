#!/usr/bin/env python3
"""GTR70E WYVERN -- ground-station host: record + live-plot the LoRa telemetry, send pad commands,
decode the SD log.

The ground station (a second Feather RP2040 RFM95) prints one tagged CSV line per frame:
    T,...   flight state, 20 Hz            M,...   authority-manoeuvre result

    pip install pyserial matplotlib
    python3 wyvern_host.py --port /dev/tty.usbmodem1101          # live plot + recording
    python3 wyvern_host.py --port ... --cmd ARM                    # queue a pad command
    python3 wyvern_host.py --replay recordings/2026-11-07_101500   # re-plot a recording
    python3 wyvern_host.py --decode WYF003.BIN                     # SD binary log -> CSV

Recordings land in ./recordings/<timestamp>_{T,M}.csv.
"""
import argparse, csv, datetime, glob, os, struct, sys, time
from collections import deque

COLS = {
    "T": "t_ms,state,seq,alt_m,vz,tilt_a,tilt_b,wx,wy,wz,ax_g,ay_g,az_g,d0,d1,d2,d3,qbar,vbat,temp,flags,auth_t,rssi,snr".split(","),
    "M": ["status", "valid"] + [f"{a}_{k}" for a in "AB" for k in
          ("qbar_d", "b_fit", "b_t", "b_ratio", "qbar_s", "sign", "achieved_deg", "t63_s", "return63_s",
           "overshoot_pct", "fin_per_deg", "peak_rate_dps")],
}
STATES = ["BOOT", "SELFTEST", "PAD", "ARMED", "BOOST", "CONTROL", "COAST", "DESCENT", "LANDED", "FAULT"]
FLAGS = {0x01: "ctrl", 0x02: "auth_abort", 0x04: "tilt_abort", 0x08: "doublet", 0x10: "step", 0x20: "man_skip/abort", 0x40: "high-g"}
# 96-byte LogRec in firmware/wyvern_fin/logger.h
LOGREC = struct.Struct("<I4f2f3f3f3f4b2f2fffBBH")
LOG_NAMES = ["t_ms", "qw", "qx", "qy", "qz", "tilt_a", "tilt_b", "wx", "wy", "wz", "ax", "ay", "az", "alt", "vz",
             "qbar", "d0", "d1", "d2", "d3", "u_a", "u_b", "ref_a", "ref_b", "a_axial", "baro_hpa", "state", "flags", "vbat_mv"]
assert LOGREC.size == 96

def decode_bin(path):
    out = os.path.splitext(path)[0] + ".csv"
    with open(path, "rb") as f, open(out, "w", newline="") as g:
        w = csv.writer(g); w.writerow(LOG_NAMES)
        while True:
            b = f.read(LOGREC.size)
            if len(b) < LOGREC.size: break
            r = list(LOGREC.unpack(b))
            for i in range(16, 20): r[i] = r[i] / 2.0
            w.writerow(r)
    print("wrote", out)

def parse(line):
    """-> (tag, dict) or None. Untagged lines with the T column count are accepted (old firmware)."""
    parts = line.strip().split(",")
    if not parts or not parts[0]: return None
    tag = parts[0] if parts[0] in COLS else None
    vals = parts[1:] if tag else parts
    tag = tag or "T"
    if len(vals) != len(COLS[tag]): return None
    try:
        return tag, {k: float(v) for k, v in zip(COLS[tag], vals)}
    except ValueError:
        return None

def man_report(d):
    st = {2: "done", 3: "skipped (gates)", 4: "aborted", 1: "running"}.get(int(d["status"]), "?")
    lines = [f"manoeuvre: {st}"]
    for a in "AB":
        lines.append(f"  axis {a}: doublet @ {d[a+'_qbar_d']:.0f} Pa  M_delta/I = {d[a+'_b_fit']:.1f} 1/s^2 (t = {d[a+'_b_t']:.1f}),"
                     f" measured/model = {d[a+'_b_ratio']:.2f}")
        if d[a + "_sign"] != 0:
            lines.append(f"          step @ {d[a+'_qbar_s']:.0f} Pa  achieved {d[a+'_achieved_deg']:.2f} deg of 1, t63 {d[a+'_t63_s']:.2f} s,"
                         f" overshoot {d[a+'_overshoot_pct']:.0f} %, {d[a+'_fin_per_deg']:.1f} deg fin per deg")
        else:
            lines.append("          step skipped (fins already past the headroom limit)")
    return "\n".join(lines)

def live(port, cmd=None):
    import serial
    import matplotlib.pyplot as plt
    ser = serial.Serial(port, 115200, timeout=0.05)
    if cmd: ser.write((cmd + "\n").encode()); print("sent", cmd)
    os.makedirs("recordings", exist_ok=True)
    stem = os.path.join("recordings", datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    files = {t: open(f"{stem}_{t}.csv", "w", newline="") for t in COLS}
    writers = {t: csv.writer(f) for t, f in files.items()}
    for t, w in writers.items(): w.writerow(COLS[t])
    N = 600
    buf = {k: deque(maxlen=N) for k in COLS["T"]}
    plt.ion(); fig = plt.figure(figsize=(12, 9)); gsp = fig.add_gridspec(4, 2, width_ratios=[2.2, 1])
    ax = [fig.add_subplot(gsp[i, 0]) for i in range(4)]
    for a in ax[1:]: a.sharex(ax[0])
    axt = fig.add_subplot(gsp[:, 1]); axt.axis("off")
    lines = {}
    for a, keys in zip(ax, (("alt_m",), ("tilt_a", "tilt_b"), ("d0", "d1", "d2", "d3"), ("vbat",))):
        for k in keys: lines[k], = a.plot([], [], label=k)
        a.legend(loc="upper left", fontsize=8); a.grid(alpha=.3)
    ax[-1].set_xlabel("t (s)")
    info = axt.text(0, 1, "", va="top", family="monospace", fontsize=8)
    last_draw = 0; status = {"man": ""}
    print("recording ->", stem + "_*.csv", "  (Ctrl-C to stop)")
    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line.startswith("#"):
                print(line); continue
            p = parse(line)
            if not p: continue
            tag, d = p
            writers[tag].writerow([d[k] for k in COLS[tag]])
            if tag == "T":
                for k, v in d.items(): buf[k].append(v)
            elif tag == "M":
                status["man"] = man_report(d); print(status["man"])
            if time.time() - last_draw > 0.2 and buf["t_ms"]:
                t = [x / 1000 for x in buf["t_ms"]]
                for k, ln in lines.items(): ln.set_data(t, list(buf[k]))
                for a in ax: a.relim(); a.autoscale_view()
                st = int(buf["state"][-1]); fl = int(buf["flags"][-1])
                fig.suptitle(f"{STATES[st] if st < len(STATES) else st}   RSSI {buf['rssi'][-1]:.0f} dBm   "
                             + " ".join(n for b_, n in FLAGS.items() if fl & b_))
                info.set_text(status["man"])
                plt.pause(0.001); last_draw = time.time()
    except KeyboardInterrupt:
        pass
    for f in files.values(): f.close()
    print("saved", stem + "_*.csv")

def replay(stem):
    import matplotlib.pyplot as plt
    T = list(csv.DictReader(open(stem + "_T.csv")))
    t = [float(r["t_ms"]) / 1000 for r in T]
    fig, ax = plt.subplots(4, 1, figsize=(9, 9), sharex=True)
    for a, keys in zip(ax, (("alt_m",), ("tilt_a", "tilt_b"), ("d0", "d1", "d2", "d3"), ("vbat",))):
        for k in keys: a.plot(t, [float(r[k]) for r in T], label=k)
        a.legend(fontsize=8); a.grid(alpha=.3)
    if os.path.exists(stem + "_M.csv"):
        M = list(csv.DictReader(open(stem + "_M.csv")))
        if M: print(man_report({k: float(v) for k, v in M[-1].items()}))
    plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--cmd"); ap.add_argument("--decode"); ap.add_argument("--replay")
    a = ap.parse_args()
    if a.decode: decode_bin(a.decode)
    elif a.replay: replay(a.replay)
    elif a.port: live(a.port, a.cmd)
    else: ap.print_help()
