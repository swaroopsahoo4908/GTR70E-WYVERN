#!/usr/bin/env python3
"""WYVERN-E 3.0 full preflight self-test orchestrator.
Runs the subsystem checks and prints a PASS/FAIL table. Exit 0 only if all pass.
Usage: python3 preflight_selftest.py [--tvc solenoid|servo]"""
import subprocess, sys, argparse
ap=argparse.ArgumentParser(); ap.add_argument("--tvc",choices=["solenoid","servo"],default="servo")
a=ap.parse_args()
CHECKS=[("Bus enumeration","i2c_scan.py"),
        ("Sensor sample","sensors_selftest.py"),
        ("microSD integrity","microsd_test.py"),
        ("Camera","camera_test.py"),
        (f"TVC {a.tvc}", f"tvc_{a.tvc}_test.py")]
results=[]
for name,script in CHECKS:
    try:
        r=subprocess.run([sys.executable,script],timeout=60)
        results.append((name,"PASS" if r.returncode==0 else "FAIL"))
    except Exception as e:
        results.append((name,f"FAIL ({e})"))
print("\n=== WYVERN-E 3.0 PREFLIGHT SELF-TEST ===")
w=max(len(n) for n,_ in results)
for n,s in results: print(f"  {n:<{w}}  {s}")
ok=all(s=="PASS" for _,s in results)
print("RESULT:", "ALL-PASS — cleared for flight build" if ok else "FAIL — do not fly")
# Reminder: also confirm RRC3+ channel continuity and that RBF (GPIO17) masks pyro before arming.
sys.exit(0 if ok else 1)
