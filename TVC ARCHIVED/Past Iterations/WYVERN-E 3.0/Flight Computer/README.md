# WYVERN-E 3.0 — Flight Computer

Everything for the off-the-shelf *Raspberry Pi 5* flight computer: schematics, a dedicated BOM,
flowcharts, processes, test code, and the integration guide. No custom PCBs. Both TVC backends
(tri-solenoid System A, servo-gimbal System B) share the same core and are documented together.

## Contents

| Path | What |
|---|---|
| `01_FlightComputer_Spec.md` | Architecture, bus map, GPIO, power tree, A/B backends |
| `02_Integration_Guide.md` | Wiring + assembly + first power-on bring-up, step by step |
| `03_Test_Procedures.md` | Bench test procedures T1–T8 (map to `test_code/`) |
| `BOM/WYVERN_E3_FlightComputer_BOM.xlsx` | Avionics/electrical-only BOM, your real cart links + prices |
| `wiring/WYVERN_E3_solenoid_harness.kicad_sch` | System A interconnect (IRF520 + 50 N solenoids + N52) |
| `wiring/WYVERN_E3_servo_harness.kicad_sch` | System B interconnect (PCA9685 + DS3235) |
| `wiring/gen_wiring.py` | Regenerates both `.kicad_sch` |
| `flowcharts/01_flight_state_machine.mermaid` | BOOT → … → LANDED state machine |
| `flowcharts/02_tvc_control_loop.mermaid` | 200 Hz PID gimbal loop |
| `flowcharts/03_arming_launch_detect.mermaid` | RBF arming + 3 g launch latch + pyro safety |
| `flowcharts/04_power_tree.mermaid` | Power distribution |
| `test_code/` | Pi 5 Python test + control suite (see its README) |

## Sourcing note

Parts are sourced from the procurement list you provided (real vendor links + prices), *dropping
the custom PCBs and the old single-use F25/G78 motors*. Items the Pi 5 design needs that were not
yet in your cart (Pi 5, camera, the extra sensors, dual µSD breakouts, servos + PCA9685, RRC3+,
USB-C power) are added with verified vendor links. The launch system is the *Estes Pro Series II
Launch Controller* on a launch-rail pad — not the Porta-Pad II.
