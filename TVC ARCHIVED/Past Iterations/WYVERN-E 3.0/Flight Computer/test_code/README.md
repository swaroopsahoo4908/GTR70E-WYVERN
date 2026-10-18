# WYVERN-E 3.0 — Flight Computer Test Code

Runs on the Raspberry Pi 5 (Raspberry Pi OS Bookworm 64-bit). Install: `pip install -r requirements.txt`.

| Script | Purpose | Bench test |
|---|---|---|
| `i2c_scan.py` | Enumerate I²C1 + all TCA9548A channels | T1 |
| `sensors_selftest.py` | One sample from all 7 sensors | T2 |
| `microsd_test.py` | 16 MB write/read/verify both SPI cards | T3 |
| `camera_test.py` | Still + 3 s H.264 to µSD#1 | T4 |
| `tvc_solenoid_test.py` | System A: IRF520 → 50 N solenoid pulse | T5 |
| `tvc_servo_test.py` | System B: PCA9685 → DS3235 ±5° sweep | T5 |
| `launch_detect.py` | 3 g / 50 ms liftoff latch (LSM6DSO32) | T6 |
| `tvc_control_loop.py` | Core PID gimbal loop (HW-free dry sim runnable) | T7 |
| `preflight_selftest.py` | Orchestrates T1–T5 → PASS/FAIL table | T8 |

`tvc_control_loop.py` is import-safe and runs its own dry simulation with no hardware attached,
so the control math can be unit-tested on any machine.
