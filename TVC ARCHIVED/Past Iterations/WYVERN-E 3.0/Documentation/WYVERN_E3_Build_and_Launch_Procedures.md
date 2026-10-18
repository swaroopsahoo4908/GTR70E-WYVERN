# WYVERN-E 3.0 — Build & Launch Procedures

### Skylight Rocketry · off-the-shelf Pi-5 two-stage TVC vehicle
## 1. Print plan (all PC-FR except nose)

| Part | Material | Notes |
|---|---|---|
| Nose cone | ASA | mass-sensitive, cool |
| Recovery bay, FC bay, TVC bay, **bulkhead**, booster body, interstage | PC-FR | 100 % flame/heat zones; ~35 % infill, 1.6 mm walls |
| Fins (oversized) | PC-FR | solid (4 mm), 100 % infill |
| Fin test articles (RQ1/RQ2) | PLA Basic | one geometry at a time for the tunnel |

Freeze a single Bambu X1C profile (0.4 mm nozzle) and reference it for all flight parts.

## 2. Flight-computer assembly (off-the-shelf)

1. Mount the **Raspberry Pi 5 + active cooler** to the FC-bay sled; seat the **Camera Module 3**
   ribbon to the side window.
2. Wire the I²C bus through a **TCA9548A mux** (the three BNO085 share an address): channel 0 =
   gimbal BNO085, ch 1 = central BNO085, ch 2 = nose BNO085; LSM6DSO32, LIS2MDL, BMP280, BME688
   on the remaining channels / direct bus.
3. Mount the two **microSD breakouts** (SPI): one for H.264 video, one for the sensor log.
4. Wire the **power system**: 3S pack → USB-C PD/BMS board; 5 V/5 A buck → Pi 5 GPIO 5 V rail;
   6 V buck → servo rail (System B); 11.1 V direct → solenoid bus (System A). Inline fuse + switch.
5. Install the **RRC3+** (recovery + 2nd-stage ignition) with hardware continuity on each channel.
6. Wire the **remove-before-flight jumper** in the arm path (see §5). Verify on bench: all sensors
   enumerate, both microSD read/write, camera captures.

## 3. TVC assembly (build the test article)

- **System A (solenoid):** mount 3× 12 V pull-solenoids at 120° on the gimbal ring; wire to the
  3-channel MOSFET driver; fit return springs; route coil leads through the bulkhead slots.
- **System B (servo):** mount 3× ~35 kg·cm servos; install ball-link linkages to the gimbal;
  wire to the PCA9685; route servo leads through the bulkhead slots.
- The **bulkhead** seals the FC bay from the TVC/motor bay; only the actuator leads + the gimbal
  BNO085 lead pass through its slots. Verify the gimbal swings ±5° freely and returns to neutral.

## 4. Recovery

24″ main + 1/8″ tubular Kevlar shock cord (8 ft) on the nose↔FC-bay bulkhead. Black-powder
ejection in the E-Match Mate canister, MJG initiators on the RRC3+ drogue/main channels.

## 5. Pad / arming sequence

1. Install motors: **F booster** (RMS-29/40) in the booster mount, **G25W-10A** (RMS-29/120) in
   the gimbaled sustainer mount. Igniter on the sustainer per RRC3+ 2nd-stage channel.
2. With the **RBF jumper INSERTED**, the FC is in standby and all pyro/ignition outputs are held
   safe. Power on; confirm sensors logging, microSD armed, camera recording.
3. On the rod, **pull the RBF jumper** → FC armed. Confirm the launch-detect threshold is primed
   (LSM6DSO32 / BNO085).
4. Clear the pad; fire the booster from the launch controller.

## 6. Flight sequence

1. Liftoff on the F booster; accelerometer threshold (> 3 g sustained) starts the flight state
   machine. Fins stabilize the booster phase.
2. Booster burnout + drag separation; RRC3+ arm-gate confirms staging state.
3. RRC3+ fires the **G25W**; **TVC active from ignition** — stabilize, then command the maneuver
   across the 4.7 s burn.
4. Apogee → RRC3+ drogue, then main. Recover.

## 7. Post-flight

Pull both microSD cards; copy the video + sensor log. Cross-check the gimbal BNO085 (actual
thrust-vector attitude) against the FC/nose BNO085 and the commanded gimbal angles. Inspect the
gimbal, motor mounts, and bulkhead pass-throughs. Swap the TVC system for the next A/B block.

## 8. Pre-launch checklist

- [ ] All parts printed in the frozen PC-FR profile; gimbal swings ±5° and returns to neutral
- [ ] Pi 5 boots; 3× BNO085 + LSM6DSO32 + LIS2MDL + BMP280 + BME688 enumerate; both µSD R/W OK
- [ ] Camera records to its µSD; flight log writes to the other
- [ ] Battery charged (USB-C); 5 V / 6 V / 11.1 V rails verified under load
- [ ] RRC3+ continuity good on drogue, main, and 2nd-stage channels
- [ ] Motors installed (F booster RMS-29/40, G25W-10A RMS-29/120); sustainer igniter in
- [ ] RBF jumper inserted (FC safe); pulled only on the rod
- [ ] Recovery packed; shock cord + chute checked; RSO brief complete
