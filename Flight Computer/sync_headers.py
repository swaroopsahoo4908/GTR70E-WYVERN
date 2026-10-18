#!/usr/bin/env python3
"""Copy the shared headers from firmware/wyvern_fin into every other sketch folder.

Arduino builds a sketch from a copy of its own folder, so relative includes into a sibling
sketch break. The flight sketch owns the single source of truth for the frame format, pins and
mixer; this script stamps read-only copies into the ground-station and test sketches.
Run after editing any of these headers:  python3 sync_headers.py
"""
import os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "firmware", "wyvern_fin")
SHARED = ["fc_config.h", "shared_state.h", "telemetry.h", "fin_mixer.h"]
TARGETS = {"ground_station/wyvern_ground": ["fc_config.h", "shared_state.h", "telemetry.h"],
           "test_code/t2_servo_cal": ["fc_config.h", "fin_mixer.h"],
           "test_code/t3_lora_range": ["fc_config.h", "shared_state.h", "telemetry.h"]}
BANNER = "// GENERATED COPY -- edit firmware/wyvern_fin/{0} and run sync_headers.py\n"
for tgt, files in TARGETS.items():
    for f in files:
        txt = open(os.path.join(SRC, f)).read()
        with open(os.path.join(HERE, tgt, f), "w") as o:
            o.write(BANNER.format(f) + txt)
    print("synced", tgt, files)
