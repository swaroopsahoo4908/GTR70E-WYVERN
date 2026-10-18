#!/usr/bin/env python3
"""TVC System B bench test: sweep 3x DS3235 servos via PCA9685 across +/-5 deg gimbal."""
import time
from adafruit_servokit import ServoKit
kit = ServoKit(channels=16, address=0x40)       # PCA9685
CH=[0,1,2]; NEUTRAL=90; LIMIT=5                  # +/-5 deg mapped about neutral
for c in CH: kit.servo[c].set_pulse_width_range(500,2500); kit.servo[c].angle=NEUTRAL
time.sleep(0.5)
print("sweeping +/-5 deg on channels", CH)
for a in list(range(NEUTRAL-LIMIT,NEUTRAL+LIMIT+1))+list(range(NEUTRAL+LIMIT,NEUTRAL-LIMIT-1,-1)):
    for c in CH: kit.servo[c].angle=a
    time.sleep(0.05)
for c in CH: kit.servo[c].angle=NEUTRAL
print("servo TVC sweep complete; verify gimbal returns to neutral")
