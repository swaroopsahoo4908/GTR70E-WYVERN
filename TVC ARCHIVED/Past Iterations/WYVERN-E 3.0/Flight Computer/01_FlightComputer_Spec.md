# WYVERN-E 3.0 — Flight Computer Specification

### Off-the-shelf Raspberry Pi 5 avionics, COTS sensor harness, dual interchangeable TVC backends

## 1. Architecture

A *Raspberry Pi 5 (4 GB)* runs the high-level flight software under Raspberry Pi OS (Bookworm,
64-bit): state machine, sensor logging (dual µSD), camera, RRC3+ interface, and trajectory. All
sensing is COTS breakouts on a shared I²C bus through a TCA9548A multiplexer; the camera is on
CSI-2. No custom PCB — every connection is JST-SH (STEMMA QT), Dupont, or screw terminal. Recovery
and 2nd-stage ignition are delegated to an RRC3+; a Jolly Logic Altimeter 2 logs an independent
backup altitude trace.

### 1.1 Why a Teensy 4.0 coprocessor (PWM is *not* done in Linux)

Linux is not real-time, so GPIO/“software” PWM from the Pi 5 jitters — unacceptable for a
fast TVC loop. So **all PWM is hardware-generated, off the Pi’s scheduler**:

- *System B servos* → **PCA9685** (a dedicated 16-channel I²C PWM chip; the Pi only sends
  setpoints over I²C, the chip generates rock-steady PWM).
- *System A solenoids* → a **Teensy 4.0** (600 MHz, FlexPWM hardware timers). The Pi 5 streams
  `{arm, phase, setpoint}` to the Teensy over **USB-serial**; the Teensy reads the gimbal BNO085
  and closes the *deterministic* PID gimbal loop at 500 Hz, driving the IRF520 gates with true
  hardware PWM and returning telemetry. The Teensy can also drive the System-B servos directly
  (or via the PCA9685), so the same real-time core runs both A/B builds.

Net split: **Pi 5 = high-level + logging + vision; Teensy 4.0 = real-time control + hardware PWM.**

## 2. Bus map

| Bus | Members |
|---|---|
| I²C1 (GPIO2/3) → TCA9548A @0x70 | ch0 BNO085 gimbal, ch1 BNO085 FC, ch2 BNO085 nose, ch3 LSM6DSO32, ch4 LIS2MDL, ch5 BMP280, ch6 BME688; (System B adds PCA9685 @0x40) |
| SPI0 (GPIO9/10/11) | microSD #1 video (CE0/GPIO8), microSD #2 log (CE1/GPIO7) |
| CSI-2 | Camera Module 3 |
| UART (GPIO14/15) | RRC3+ telemetry / arm interface |
| USB (host) | **Teensy 4.0** TVC coprocessor — setpoint/telemetry link |

The three BNO085 share I²C address 0x4A/0x4B, so each sits on its own mux channel. The gimbal
BNO085 is read by the **Teensy** (its own I²C) for the real-time loop; the Pi reads the FC/nose
BNO085s for logging.

## 3. GPIO allocation (40-pin header)

| GPIO | Function |
|---|---|
| 2 / 3 | I²C1 SDA / SCL → TCA9548A (+ PCA9685 in System B) |
| 7 / 8 | SPI CE1 / CE0 (µSD log / video) |
| 9 / 10 / 11 | SPI MISO / MOSI / SCLK |
| 14 / 15 | UART TX / RX → RRC3+ |
| 17 | RBF arm-pin sense (inserted = safe) |
| 27 | launch-detect IRQ (LSM6DSO32 / BNO085 INT) |
| (USB) | TVC PWM is offloaded to the Teensy 4.0 — *no* jittery Pi GPIO PWM in the control path |

## 4. Power tree

$$P_{idle} \approx 4.2\ \mathrm{W}, \quad P_{active} \approx 8.3\ \mathrm{W}, \quad E_{pack} = 11.1\ \mathrm{V}\times 3.0\ \mathrm{Ah} = 33\ \mathrm{Wh}$$

giving $33 / (4.2 \cdot 2 + 0.14\cdot 6\ \mathrm{flights}) \approx 1.9\times$ margin over the
5-flight + 2 h-idle requirement. The 11.1 V pack feeds three rails: a 5 V/5 A buck (Pi 5 + 3V3
sensors), a 6 V UBEC (servo rail, System B), and the 11.1 V bus direct (50 N solenoids System A +
RRC3+). USB-C PD (IP2368) charges; a 12 V 2 A supply is the bench alternate. See `flowcharts/04_power_tree.mermaid`.

## 5. Storage & camera

Dual SPI microSD, 32 GB each: #1 = H.264 1080p flight video, #2 = full-rate sensor log. No radio;
both pulled and copied post-flight. Camera Module 3 on CSI-2.

## 6. Arming & launch detection

RBF jumper on GPIO17: *inserted → safe* (RRC3+ AUX/DROGUE/MAIN masked in firmware); *pulled on the
rod → armed*. Launch is latched when $|a| > 3g$ is sustained for 50 ms on the LSM6DSO32 / BNO085
INT (GPIO27). No pyro output can assert on the pad. See `flowcharts/03_arming_launch_detect.mermaid`.

## 7. TVC actuator backends (A/B)

| | System A — tri-solenoid | System B — servo-gimbal |
|---|---|---|
| Hardware PWM source | **Teensy 4.0 FlexPWM** → 3-ch IRF520 MOSFET | **PCA9685** 16-ch I²C PWM @0x40 |
| Actuator | 3× 50 N 12 V solenoid + N52 return/detent | 3× DS3235 ~35 kg·cm digital servo (6 V) |
| Flyback | 1N4007 across each coil | n/a |
| Wiring | `wiring/WYVERN_E3_solenoid_harness.kicad_sch` | `wiring/WYVERN_E3_servo_harness.kicad_sch` |

Neither backend uses Pi GPIO software PWM: System A's PWM comes from the Teensy's FlexPWM timers,
System B's from the PCA9685's onboard oscillator. Both share the Pi 5 + sensor + power + RRC3+ +
Teensy core; only the driver/actuator is swapped between the A/B flight blocks (3 flights each). The
control law (`test_code/tvc_control_loop.py`) is identical and runs on the Teensy; only the output
mapping differs.
