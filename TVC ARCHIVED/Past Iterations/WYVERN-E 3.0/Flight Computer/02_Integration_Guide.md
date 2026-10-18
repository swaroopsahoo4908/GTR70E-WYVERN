# WYVERN-E 3.0 — Flight Computer Integration Guide

### Wiring, assembly, and first power-on bring-up

## 1. Before you start

Flash Raspberry Pi OS (64-bit, Bookworm) to a boot microSD (separate from the two SPI flight
cards). Enable I²C, SPI, UART, and the camera in `raspi-config`. Install deps:

    python3 -m venv ~/wyvern && source ~/wyvern/bin/activate
    pip install -r test_code/requirements.txt

## 2. I²C sensor harness (STEMMA QT)

1. Wire I²C1 (GPIO2 SDA, GPIO3 SCL, 3V3, GND) to the *TCA9548A* with a male JST-SH cable.
2. Daisy each sensor to its mux channel with the female JST-SH cables (qty 3 of each in the cart):
   ch0/1/2 = the three *BNO085* (gimbal, FC, nose); ch3 *LSM6DSO32*; ch4 *LIS2MDL*; ch5 *BMP280*;
   ch6 *BME688*. The gimbal BNO085 lead routes through the bulkhead slot into the TVC bay.
3. Run `python3 test_code/i2c_scan.py` — every channel must report its expected address.

## 3. Storage and camera

1. Mount the two SPI microSD breakouts: #1 CS→CE0/GPIO8 (`/mnt/sd_video`), #2 CS→CE1/GPIO7
   (`/mnt/sd_log`); share MOSI/MISO/SCLK. Add both to `/etc/fstab`.
2. Seat the Camera Module 3 ribbon to the CSI-2 port; route to the FC-bay side window.
3. Verify: `python3 test_code/microsd_test.py` and `python3 test_code/camera_test.py`.

## 4. Power

1. 3S Li-ion pack → IP2368 USB-C PD/BMS board. Master switch + inline fuse on the pack +.
2. 5 V/5 A buck → Pi 5 5 V rail (GPIO pins 2/4 + GND). 6 V UBEC → servo rail (System B only).
   11.1 V bus direct → solenoid bus (System A) and RRC3+.
3. Confirm 5.0 V, 6.0 V, and 11.1 V under load *before* connecting the Pi 5.

## 5. Recovery / ignition controller

1. Install the *RRC3+*: VBAT + GND from the 11.1 V bus; UART to GPIO14/15.
2. Wire DROGUE (apogee), MAIN (150 m), AUX (G25W 2nd-stage igniter). Hardware continuity check
   on each channel with the igniters disconnected.
3. Mount the *Jolly Logic Altimeter 2* on its own battery as an independent backup log.

## 6. TVC backend (build the A/B article under test)

System A — solenoid: mount 3× 50 N solenoids at 120° on the gimbal ring; IRF520 gates to
GPIO12/13/18; 1N4007 flyback across each coil; N52 magnets set the return/detent; coil leads
through the bulkhead slots. Grease pivots with Super Lube; bond brackets with J-B Weld.

System B — servo: mount 3× DS3235 servos; ball-link to the gimbal; signal to PCA9685 CH0/1/2;
V+ from the 6 V UBEC. Set `set_pulse_width_range(500,2500)` and neutral = 90°.

Verify the chosen backend: `tvc_solenoid_test.py` or `tvc_servo_test.py`. Gimbal must swing ±5°
and return to neutral.

## 7. Arm path

Wire the remove-before-flight jumper into GPIO17 so *inserted = safe*. With it inserted, confirm
in software that RRC3+ AUX/DROGUE/MAIN are masked. The jumper is pulled only on the rail.

## 8. First full bring-up

Run `python3 test_code/preflight_selftest.py`. It exercises every subsystem and prints a PASS/FAIL
table; do not proceed to a flight build until it is all-PASS. Then dry-run the control law with
`python3 test_code/tvc_control_loop.py` (no hardware) to confirm the loop tracks the maneuver and
clamps at ±5°.
