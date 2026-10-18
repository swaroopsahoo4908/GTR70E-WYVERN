# Electronics — WYVERN-E 3.0 (off-the-shelf)

**No custom PCBs.** The flight computer is a **Raspberry Pi 5** carrier with COTS breakout
sensors on an I²C/SPI harness. See `Documentation/WYVERN_E3_*` for architecture, the
power/mass/motor analysis, and the BOM.

## Contents

- `wiring/WYVERN_E3_solenoid_harness.kicad_sch` — tri-solenoid TVC driver wiring
- `wiring/WYVERN_E3_servo_harness.kicad_sch` — servo-gimbal TVC wiring

Both share the Pi 5 + sensor + power + RRC3+ core; only the TVC actuator branch differs.

## ⚠ Delete the old `PCB/` folder

The `PCB/` folder is the **superseded 2.0 custom two-board design** (carried over by the copy).
3.0 uses no custom PCBs, so `PCB/` should be deleted. The sandbox can't delete on the
iCloud-synced volume, so remove it manually:

```
rm -rf "WYVERN-E 3.0/PCB"
```
