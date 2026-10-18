#!/usr/bin/env python3
"""GTR70E WYVERN host monitor, reads the Pico 2 W perfboard's (RP2350) USB-serial stream during BOOT
self-test and flight, and tabulates results against the real line protocol emitted by
build/firmware/wyvern4_tvc.ino.

Protocol (see wyvern4_tvc.ino setup()/setup1()/loop1() for the authoritative source):
    SELFTEST:BEGIN
    SELFTEST:<NAME>:PASS|FAIL|SKIP|WAIT[...] one line per check, NAME in CHECK_ORDER below
    SELFTEST:DONE:PASS|FAIL aggregate result core 0's BOOT state gates on
    STATE:<BOOT|ARMED|BOOST|COAST|RECOVER|DESCENT|LANDED> emitted once on every state transition
    HB:t=<ms> state=<name> batt=<V>V rbf=<0|1> drop=<n> ~1 Hz heartbeat, always

Usage:
    python3 host_monitor.py [PORT] [--timeout SECONDS]
    PORT defaults to /dev/ttyACM0 (Linux) -- on macOS pass the /dev/tty.usbmodem* device explicitly.

Exit code: 0 if SELFTEST:DONE:PASS was observed before timeout, 1 otherwise. Designed to be both a
human-readable bench tool and a scriptable preflight gate (see selftest.py, which wraps this).
"""
import sys
import time
import argparse
import re

try:
    import serial
except ImportError:
    print("pyserial not installed -- pip install pyserial", file=sys.stderr)
    sys.exit(2)

# Every SELFTEST:<NAME> the firmware can emit, in the order setup()/setup1() print them. Keeping
# this list explicit (rather than accepting any NAME) means an unexpected/missing check shows up
# as a clear "NOT SEEN" row instead of silently being absent from the table.
CHECK_ORDER = [
    "MUX", "IMU_GIMBAL", "IMU_BODY", "IMU_RECOVERY", "IMU_MINIMUM",
    "BARO_BMP", "BARO_BME", "SERVO", "CORE0_READY",
    "BATTERY", "SD", "WIFI", "RBF", "LOG_RING",
]
SELFTEST_RE = re.compile(r"^SELFTEST:([A-Z0-9_]+):(.*)$")
STATE_RE = re.compile(r"^STATE:([A-Z]+)$")
# Heartbeat gained pend=/peak= in 2026-08 when the inter-core log transport was rewritten as a
# shared-RAM SPSC ring (sd_logger.h). Both new fields are optional so this monitor still parses
# heartbeats from an older build rather than silently showing "NOT SEEN" for everything.
HB_RE = re.compile(
    r"^HB:t=(\d+)\s+state=(\S+)\s+batt=([\d.]+)V\s+rbf=([01])\s+drop=(\d+)"
    r"(?:\s+pend=(\d+))?(?:\s+peak=(\d+))?$"
)


def classify(value: str) -> str:
    """Map a SELFTEST line's value field to PASS/FAIL/SKIP/WAIT for the summary table."""
    v = value.upper()
    if v.startswith("PASS"):
        return "PASS"
    if v.startswith("FAIL"):
        return "FAIL"
    if v.startswith("SKIP"):
        return "SKIP"
    if v.startswith("WAIT"):
        return "WAIT"
    return "?"


def run(port: str, timeout_s: float, baud: int = 115200):
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f"open {port} failed: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"listening on {port} @ {baud} (Ctrl-C to stop, auto-stop after {timeout_s:.0f}s)")
    results = {} # NAME -> (status, raw_value)
    overall = None # SELFTEST:DONE value, classified
    last_state = None
    last_hb = None
    states_seen = []
    t0 = time.time()
    try:
        while time.time() - t0 < timeout_s:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode(errors="ignore").strip()
            if not line:
                continue
            print(" ", line)

            m = SELFTEST_RE.match(line)
            if m:
                name, value = m.group(1), m.group(2)
                if name == "DONE":
                    overall = classify(value)
                elif name == "BEGIN":
                    pass
                else:
                    results[name] = (classify(value), value)
                continue

            m = STATE_RE.match(line)
            if m:
                last_state = m.group(1)
                states_seen.append(last_state)
                continue

            m = HB_RE.match(line)
            if m:
                last_hb = {
                    "t_ms": int(m.group(1)), "state": m.group(2), "batt_v": float(m.group(3)),
                    "rbf": m.group(4) == "1",
                    "drop": int(m.group(5)),
                    "pend": int(m.group(6)) if m.group(6) is not None else None,
                    "peak": int(m.group(7)) if m.group(7) is not None else None,
                }
                # Once we've seen at least one heartbeat AND a DONE verdict, no need to keep
                # listening for the full timeout window during a bench self-test run.
                if overall is not None:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

    print("\n=== preflight self-test summary ===")
    for name in CHECK_ORDER:
        status, raw = results.get(name, ("NOT SEEN", ""))
        tag = {"PASS": "PASS", "FAIL": "FAIL", "SKIP": "SKIP", "WAIT": "WAIT", "NOT SEEN": "????"}[status]
        suffix = f" ({raw})" if raw and status not in ("PASS", "FAIL") else ""
        print(f" [{tag:>4}] {name}{suffix}")
    print(f" ---- aggregate SELFTEST:DONE = {overall or 'NOT SEEN'} ----")
    if last_hb:
        print(f"\nlast heartbeat: state={last_hb['state']} batt={last_hb['batt_v']:.2f}V "
              f"rbf_pulled={last_hb['rbf']} "
              f"dropped_frames={last_hb['drop']}")
        if last_hb.get("pend") is not None:
            print(f"log ring: pending={last_hb['pend']} peak={last_hb.get('peak')} of 256 frames")
        if last_hb["drop"] > 0:
            print(" NOTE: dropped_frames > 0 -- core 1 fell more than a full 256-frame ring "
                  "behind core 0. Suspect a slow SD card; raise FLUSH_EVERY or use a faster card.")
        if last_hb.get("peak") is not None and last_hb["peak"] > 200:
            print(" NOTE: peak ring occupancy >200/256 -- close to dropping. Same remedy as above.")
    if states_seen:
        print(f"state transitions observed: {' -> '.join(states_seen)}")

    missing = [n for n in CHECK_ORDER if n not in results]
    if missing:
        print(f"\nWARNING: never saw a line for: {', '.join(missing)} (port too slow? wrong baud? "
              f"firmware version mismatch?)")
        all_pass = False

    return 0 if (overall == "PASS" and not missing) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("port", nargs="?", default="/dev/ttyACM0",
                     help="serial port (e.g. /dev/ttyACM0, or /dev/tty.usbmodemXXXX on macOS)")
    ap.add_argument("--timeout", type=float, default=20.0, help="seconds to listen (default 20)")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()
    sys.exit(run(args.port, args.timeout, args.baud))
