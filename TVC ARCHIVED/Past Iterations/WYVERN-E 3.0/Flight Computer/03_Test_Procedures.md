# WYVERN-E 3.0 — Flight Computer Bench Test Procedures

Each procedure maps to a script in `test_code/`. Run in order; record PASS/FAIL in the build log.

## T1 — Bus enumeration
`i2c_scan.py` → all 7 mux channels report expected addresses (System B also shows PCA9685 @0x40 on root). Pass = exit 0.

## T2 — Sensor sample
`sensors_selftest.py` → one valid sample from all 3 BNO085 + LSM6DSO32 + LIS2MDL + BMP280 + BME688. Pass = "ALL SENSORS OK".

## T3 — Storage integrity
`microsd_test.py` → 16 MB write/read/verify on both cards; log throughput. Pass = both "verify OK" and ≥ 2 MB/s.

## T4 — Camera
`camera_test.py` → still + 3 s H.264 clip to `/mnt/sd_video`. Pass = files present and non-zero.

## T5 — TVC actuation (run the backend under test)
`tvc_solenoid_test.py` (A) or `tvc_servo_test.py` (B) → each axis pulses/sweeps ±5° and returns to neutral.

## T6 — Launch detect
`launch_detect.py` → shake/drop test trips the 3 g / 50 ms latch and prints LIFTOFF. Pass = latches only above threshold (no false trip at rest).

## T7 — Control-law dry run
`tvc_control_loop.py` → prints setpoint vs commanded vs modelled pitch; commands clamp at ±5°, pitch tracks the maneuver after 2.5 s.

## T8 — Full preflight
`preflight_selftest.py` → orchestrates T1–T4 + RRC3+ continuity + RBF mask check. Pass = all-PASS table.

## Ground campaign (per BOM test plan)
2 static motor fires per motor type on the 20 kg load-cell stand (HX711 DAQ), and 3 TVC ground
runs per backend on the bench gimbal, before each A/B flight block.
