#!/usr/bin/env python3
"""Copy the shared headers from firmware/wyvern_fin into every test sketch folder.

Arduino builds a sketch from a copy of its own folder, so relative includes into a sibling
sketch break. The flight sketch owns the single source of truth for pins, the mixer, the
barometer driver, the arming logic and the log format; this script stamps read-only copies
into the test sketches. Run after editing any of these headers:  python3 sync_headers.py
(Rev 4: no ground station any more; the flight Pico 2 W talks to wyvern_host.py over USB.)
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "firmware", "wyvern_fin")
TARGETS = {"test_code/t1_i2c_scan": ["fc_config.h", "baro.h"],
           "test_code/t2_servo_cal": ["fc_config.h", "fin_mixer.h"],
           "test_code/t3_arm_log": ["fc_config.h", "shared_state.h", "arming.h", "logger.h"]}
BANNER = "// GENERATED COPY -- edit firmware/wyvern_fin/{0} and run sync_headers.py\n"
for tgt, files in TARGETS.items():
    for f in files:
        txt = open(os.path.join(SRC, f)).read()
        with open(os.path.join(HERE, tgt, f), "w") as o:
            o.write(BANNER.format(f) + txt)
    print("synced", tgt, files)
