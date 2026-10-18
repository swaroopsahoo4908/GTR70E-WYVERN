# GTR70E WYVERN Flight Computer, Flight-Readiness Document

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


Flight hardware is a **Raspberry Pi Pico 2 W** on a 20 x 24 (50 x 70 mm) perfboard, with **one
shared I²C bus, no mux**, carrying two **BNO085** units (bay 0x4B, gimbal 0x4A via STEMMA-QT,
bulkhead-boundary mount), and no onboard radio chip. §1 below matches `01_FlightComputer_Spec.md`
and the real firmware in `firmware/wyvern4_tvc/`.

This is the top-level readiness summary for the Pico 2 W flight-computer firmware. Read
`CONFLICTS.md` first, it's the frozen parameter table and the record of the resolved design
conflicts (including the PID gain retune, §1) that this firmware's behavior depends on. Also read
`COMPATIBILITY.md` for the full I2C/SPI/PWM/ADC/power audit across every component, it surfaces
three unresolved hardware conflicts (§4 below) that are not fixable from firmware alone. This
document covers: what was built, what must be bench-verified before the firmware can be trusted in
the air, and the go/no-go sequence.

## 1. What this firmware does

- **Core 0 (500 Hz, real-time, never blocks):** reads bay BNO085 (0x4B) + gimbal BNO085 (0x4A)
  fused attitude off the **one shared I²C bus** (GP0/GP1, no mux, no second controller), 2-of-2
  voting between them, runs the dual-axis PID (`wyvern_pid.h`), commands the pitch/yaw TVC servos
  (GP2/GP3), runs launch-detect and the BOOT→ARMED→BOOST→COAST→RECOVER→DESCENT→LANDED state
  machine, and pushes one log frame per tick into a lock-free inter-core FIFO.
- **Core 1 (housekeeping, may block):** drains that FIFO to a microSD flight log (`sd_logger.h`),
  services the camera gate / status LED / RBF sense (`launch_status.h`), and hosts the (currently
  inert in flight) UDP telemetry code path (`wifi_telemetry.h`, `WYV_WIFI_ENABLED` — enabled only
  radio chip populated, so this never runs in flight). The INA226 battery monitor (`battery.h`)
  shares core 0's I²C bus and is polled there, not on core 1.
- **The flight computer never drives recovery.** Recovery is the **F15-4 motor's own ejection charge**, fired
  4 s after burnout (t ≈ 7.45 s, 0.58 s past apogee), pressurizing the Lower BT and **separating the
  two body tubes at the bulkhead joint** (the airframe is two body tubes, Lower BT/Upper BT, 
  joined at one bulkhead, not a single continuous tube). There is no pyro, e-match, CO2, or recovery
  computer of any kind in the vehicle, the FC only logs baro/IMU; telemetry is not streamed. See
  `WYVERN_E4_Recovery.md` and the feasibility study (`Simulations/we4_ejection_feasibility.py`).

## 2. Design conflicts resolved (full detail in `CONFLICTS.md`)

1. **PID gains**: Kp=0.10/Ki=0.40/Kd=0.18, margin-verified across a 24-point phase/gain-margin sweep
   (4 atmospheres × 6 burn-time slices), worst case PM=44.7°, GM=12.6 dB against a 30° target — see
   `PID_TUNING_REPORT.md` for the full sweep and `CONFLICTS.md` §1 for the parameter table.
2. **Recovery architecture**, recovery is now the F15-4 motor ejection charge separating the two
   body tubes at the bulkhead joint (no RRC3+, no pyro, no CO2). **Moot for the FC** since it never
   drives recovery, the flight computer only observes. Prior CO2/RRC3 deploy logic has been removed
   from the firmware.
3. **Battery monitoring wiring defect (INA226, U4)**, traced pin-by-pin against the real netlist:
   U4 reads the TPS564201 buck's ~5 V output rail, not the raw 2S pack input, so the 6.4 V/6.0 V
   (3.2/3.0 V-per-cell) pack cutoffs don't apply to this reading as wired — `battery.h` uses
   rail-sag thresholds as a software workaround. U4's address strap is also not cleanly wired to any
   of the INA226's four documented address options; `0x40` is a bench-scan candidate, not confirmed.
   See `01_FlightComputer_Spec.md` §4 and `CONFLICTS.md` §3 for the full defect record.

## 3. Hardware items flagged by `COMPATIBILITY.md`, do not fly past these silently

1. **Gimbal deflection is measured by the 3-axis load balance, not an onboard IMU.** There is no
   gimbal-mounted IMU on this vehicle and no ranging hardware anywhere on the flight airframe.
2. **INA226 wiring defect (§2 item 3 above)** needs a board revision to fix properly; the firmware
   workaround (rail-sag thresholds) is not a substitute for a real pack-voltage reading.
3. **RBF sense (GP12) is not wired to any physical switch on this board rev** — see
   `01_FlightComputer_Spec.md` §3. Arming safety currently comes entirely from U13, the physical
   power switch, not from any software-visible RBF gate.
4. **Ground-rig DAQ is a separate off-the-shelf Raspberry Pi Pico/Pico 2 W** on both
   `wyvern4_gse_servo_rig.ino` and `wyvern4_gse_solenoid_rig.ino`, matching `GSE_TestStands.md` and
   `gen_wiring4.py` — this is bench hardware, not the flight computer.

## 4. Action items before this flies, do not skip these

| # | Item | Why it matters | How to clear it |
|---|---|---|---|
| 1 | **Ground-test the bulkhead separation joint** | Recovery now depends entirely on the F15-4 charge pressurizing the Lower BT to separate the two body tubes at the bulkhead joint, this is the single point of the recovery system | Do the bench ground-separation test in `WYVERN_E4_Recovery.md` §8: fire a representative charge (or the motor's own charge in a restrained static test) and confirm the bulkhead joint releases cleanly in the 50-150 N band, the chute deploys, and the servo/STEMMA-QT cable pass-through survives the separation event. |
| 3 | **Decide the LAUNCH_IRQ branch** | The hardware inertial-switch backup to the software 3g/50 ms launch latch is an *assumption* (active-low, closes to GND) — this was an artefact of the retired the flight computer's H1 header and does not apply to the Pico 2 W pin map | Either wire a redundant mechanical switch to a spare Pico GPIO and update `wyvern_config.h`, or remove the IRQ branch from `LaunchDetect::update()` since no such switch exists in this build. Flying with an undocumented floating input is worse than removing the dead code path. |
| 4 | **Add a real RBF switch on GP12, or accept there is none** | GP12 is wired to an `INPUT_PULLUP` software gate but, as fabricated, nothing is soldered there — the pin floats HIGH and `g_rbf_pulled` always reads true, so this stage of the BOOT gate currently provides no protection. Arming safety is entirely U13 (the physical power switch) today | Either bodge a switch from H1 pin13 (GP12) to GND, or explicitly document that RBF is power-switch-only on this board rev and stop treating the software gate as a second layer. |
| 5 | **Bench-confirm INA226's real address and rail** | U4's address strap isn't cleanly wired to a documented option (`0x40` is a scan guess) and it reads the buck's ~5 V output, not the 2S pack — both are netlist findings, not yet bench-confirmed | Run `test_code/t1_i2c_scan.ino`, update `INA226_ADDR` in `battery.h` to whatever address is found, and multimeter-verify the VBUCK rail voltage against the calculated ~4.98 V before trusting `battery.h`'s rail-sag thresholds. |
| 6 | **Confirm accelerometer support on the bay BNO085 firmware path** | Launch-detect and landing-detect depend on `imu_grv.h` reading a live accelerometer alongside the BNO085's IMUPLUS fusion mode | During self-test, watch for the accel magnitude settling near 1 g at rest (visible in the FIFO/log), if it stays at a frozen default, the accel report isn't updating and launch/landing detect are running on stale data. Add a bench print if you want this surfaced explicitly before flight. |
| 7 | **Servo throw and gimbal mechanical limit** | Firmware clamps to ±8° in software; confirm the printed gimbal + servo linkage physically allow ±8° travel (raised from ±5° for wind authority) with no binding | During the SERVO self-test sweep, visually confirm no binding/buzzing at the endpoints. |

## 5. Preflight bench sequence (ground test, every time before flight)

1. Power the Pico 2 W from USB (or flight battery through the UBEC) with
   the vehicle **horizontal and restrained**, the servo sweep and IMU motion during self-test are
   expected, not a fault.
2. Run `python3 test_code/selftest.py /dev/tty.usbmodemXXXX` (macOS) or `.../ttyACM0` (Linux).
3. Confirm **every** row in the printed table reads `PASS` (or `SKIP` for WIFI if disabled, or
   WAIT on RBF is correct if the switch is still inserted).
4. Pull the RBF switch; confirm the table/heartbeat shows `rbf_pulled=True` and the status LED/
   buzzer switches to the ARMED pattern (`launch_status.h`).
5. Confirm `SELFTEST:DONE:PASS` and `>>> PREFLIGHT GO <<<` from `selftest.py`'s own exit message.
6. Re-insert the RBF, disconnect the bench monitor, and proceed to the pad per the normal rocketry
   range-safety procedure, RBF removal and arming should be one of the last actions at the pad,
   matching its name.
7. **If any row reads `FAIL` or `NOT SEEN`, do not fly.** `selftest.py` exits non-zero in both
   cases (suitable for scripting into a larger ground-station go/no-go gate); re-run after fixing
   the indicated subsystem.

## 6. Firmware file map

The flight firmware is an Arduino IDE sketch folder, `firmware/wyvern4_tvc/` (folder name matches
the `.ino` filename, as the IDE requires), containing the main sketch plus every header as a tab in
the same folder. Open `wyvern4_tvc/wyvern4_tvc.ino` in the IDE and every file below loads as a tab.

| File | Role |
|---|---|
| `wyvern4_tvc/wyvern4_tvc.ino` | Main sketch: pin map, dual-core ownership, state machine, setup/loop |
| `wyvern4_tvc/wyvern_pid.h` | Dual-axis PID: anti-windup, filtered derivative, slew limit, bumpless reset. Frozen gains: Kp=0.10/Ki=0.40/Kd=0.18 (margin-verified retune, §2 item 1) |
| `wyvern4_tvc/wyvern_config.h` | Pin map, I²C addresses, and the flight / ground-stand role switch. Single source of truth for hardware constants |
| `wyvern4_tvc/imu_grv.h` | Dual-IMU driver (bay BNO085 + external BNO085, different chip families), quaternion/Euler math, 2-of-2 voting, body accelerometer |
| `wyvern4_tvc/baro.h` | BME688 driver (no BMP388 populated on this board rev; that code path degrades gracefully rather than being deleted) |
| `wyvern4_tvc/battery.h` | INA226 rail monitor on the shared I²C bus — reads the buck's VBUCK output, not raw pack voltage, see §2 item 3; voltage snapshotted cross-core into every log row |
| `wyvern4_tvc/launch_status.h` | Launch-detect (GP37 IRQ), camera gate (GP36), RBF sense (GP12, unwired on this board rev), status LED/buzzer patterns |
| `wyvern4_tvc/sd_logger.h` | **Schema v2**: 37-field `LogFrame` (up from 19) + inter-core FIFO + microSD flight logger. Adds flight time, loop-timing jitter, IMU vote disagreement, commanded setpoint, per-axis P/I/D term breakdown, battery flags/voltage, and cumulative dropped-frame count, see the header's schema-v2 comment for the full rationale |
| `wyvern4_tvc/wifi_telemetry.h` | UDP telemetry over the Pico 2 W's CYW43439. Enabled on the ground stand, off in flight (`WYV_WIFI_ENABLED`) |
| `test_code/host_monitor.py` | Parses the live serial protocol, tabulates self-test + heartbeat |
| `test_code/selftest.py` | Go/no-go wrapper around `host_monitor.py` for the bench sequence above |
| `../Documentation/CONFLICTS.md` | Design-conflict memo + frozen parameter table (read this first) |
| `../Documentation/COMPATIBILITY.md` | Full I2C/SPI/PWM/ADC/power compatibility audit across every component and both ground rigs |

## 7. Known limitations / honest caveats

- Recovery is a **single passive event**, the F15-4 motor's own ejection charge, now separating the
  two body tubes at the bulkhead joint rather than popping a nose off one continuous tube. There is
  no electronic deploy path and no backup channel; the ground-separation test (action item #1) is
  the primary way to build confidence before flight. The bulkhead joint's release-force spec and the
  bay-pressurization margin against it both need re-verification for the new two-BT geometry, see
  `WYVERN_E4_Recovery.md` §4, §6.
- Launch detect's hardware-IRQ branch (GP37) and the camera/CAM_EN polarity (GP36) are implemented
  per the design docs' stated intent but are unconfirmed against an actual wired harness (action
  item #3).
- The WiFi telemetry path is bench-only by design. The Pico 2 W does have a radio, but flight
  has no radio chip populated at all, so it cannot be, and should not be treated as, part of any
  go/no-go criterion.
- IMU voting is 2-of-2 (bay BNO085 vs. external BNO085) for vehicle attitude. There is no
  gimbal-mounted IMU on this vehicle, so nozzle deflection is not computable in flight — that
  measurement lives on the ground rigs' 3-axis load balance instead, see `imu_grv.h`'s header
  comment for the full reasoning.
