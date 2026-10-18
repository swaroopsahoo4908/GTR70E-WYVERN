#!/usr/bin/env python3
"""Standalone launch-detect check: latch t0 when |a| > 3 g sustained for 50 ms (LSM6DSO32)."""
import time, math, board, busio, adafruit_tca9548a
from adafruit_lsm6ds.lsm6dso32 import LSM6DSO32
G=9.80665; THRESH=3.0*G; WIN=0.05
i2c=busio.I2C(board.SCL,board.SDA); mux=adafruit_tca9548a.TCA9548A(i2c,address=0x70)
imu=LSM6DSO32(mux[3])
print(f"priming launch detect: |a|>{THRESH:.0f} m/s^2 for {WIN*1e3:.0f} ms ... (Ctrl-C to abort)")
above=None
while True:
    ax,ay,az=imu.acceleration; a=math.sqrt(ax*ax+ay*ay+az*az)
    if a>THRESH:
        above=above or time.monotonic()
        if time.monotonic()-above>=WIN:
            print(f"LIFTOFF latched, |a|={a:.1f} m/s^2 ({a/G:.1f} g)"); break
    else: above=None
    time.sleep(0.005)
