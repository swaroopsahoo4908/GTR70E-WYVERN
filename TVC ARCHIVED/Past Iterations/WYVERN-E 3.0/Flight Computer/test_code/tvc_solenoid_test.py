#!/usr/bin/env python3
"""TVC System A bench test: PWM-pulse the 3 IRF520 gates driving the 50N solenoids."""
import time, lgpio
GATES = {0:12, 1:13, 2:18}   # GPIO -> IRF520 gate
h = lgpio.gpiochip_open(0)
for g in GATES.values(): lgpio.gpio_claim_output(h, g, 0)
try:
    for idx,g in GATES.items():
        print(f"  solenoid {idx} (GPIO{g}): 1 s @ 50% PWM 200 Hz")
        lgpio.tx_pwm(h, g, 200, 50); time.sleep(1.0); lgpio.tx_pwm(h, g, 200, 0); time.sleep(0.3)
    print("solenoid TVC pulse test complete; confirm each pulls + returns (N52 detent)")
finally:
    for g in GATES.values(): lgpio.gpio_write(h, g, 0)
    lgpio.gpiochip_close(h)
