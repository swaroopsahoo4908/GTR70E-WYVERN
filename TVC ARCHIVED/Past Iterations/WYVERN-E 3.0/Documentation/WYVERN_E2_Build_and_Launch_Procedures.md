# WYVERN-E 2.0 — Build & Launch Procedures

### A Skylight Rocketry Venture
##### 84 mm 2-Stage Magnetic-TVC 3D-Printed Research Vehicle

> *Safety first.* This vehicle carries energetics (motors, black-powder ejection charges,
> igniters). Handle per NAR/Tripoli safety codes. Two-stage + onboard energetics operations
> require RSO approval. Never connect igniters/charges until the vehicle is on the pad and the
> range is clear. Eye protection during ground tests and ejection charge work.

## Part A — 3D Printing

### A.1 Print settings (by material)

| Part group | Material | Walls | Infill | Notes |
|---|---|---|---|---|
| Body tubes, booster, couplers | PETG-CF | 4 perim (2.0 mm) | 35% gyroid | 0.2 mm layer; dry filament; 250–260 °C |
| Nose cone, camera pod | ASA | 4 perim | 20% | Enclosure printer; 240–250 °C; brim |
| Fins | PC-FR | solid (4 mm) | 100% | 270–290 °C; anneal optional |
| TVC gimbal/cradle, test stand | PC-FR | 4 perim | 40% | 270–290 °C; flame-rated zone |
| Wind tunnel mount + fan collar | PLA | 3 perim | 20% | 200–210 °C |

### A.2 Print order & files (`3DP/Rocket/`, `3DP/WindTunnel/`, `3DP/TestStand/`)

1. `01_nose_cone` (ASA) — print tip-up, supports off; light support in shoulder.
2. `02_recovery_bay`, `03_avionics_bay`, `05_stage2_tvc_bay`, `09_stage1_booster_body`
   (PETG-CF) — print vertically; the booster has the fin can + motor mount integrated.
3. `07_interstage_coupler` (PC-FR).
4. `08_fin_single` (PC-FR) — print 4× for flight; print extra candidate geometries for the tunnel.
5. `06_tvc_gimbal_mech` (PC-FR) — supports under trunnions.
6. `04_pcb_internal_mount` (PETG-CF), `10_camera_pod_fairing` (ASA).
7. GSE: `WindTunnel/WT_fin_test_mount`, `WindTunnel/WT_120mm_fan_collar` (PLA);
   `TestStand/TS_base_plate`, `TS_motor_tower`, `TS_loadcell_bracket` (PC-FR).
8. `00_full_assembly` / `11_outer_shell_full` are reference/visual STLs (not printed for flight).

Each part is provided as `.stl` (print) and `.step` (CAD edit). Regenerate or re-parametrize
with `3DP/_generator/gen_rocket.py`.

### A.3 Post-processing

- Ream coupler bores to a snug slip fit (test fit before any bonding).
- Tap/clean threaded coupler interfaces.
- Bond fins into the booster fin-can slots with 2-part epoxy; fillet the root.
- Install the motor retainer ring; verify 29 mm motor slides into the mount tube.

## Part B — Avionics (FCM)

### B.1 PCB fabrication

1. Open `PCB/FCM_KiCAD/WYVERN_E2_FCM.kicad_pcb` in KiCad 7/8/9.
2. **Promote to 4-layer** (Board Setup → Physical Stackup) per PCB doc §6; move 12 V / V_SOL /
   5 V / 3.3 V polygons to the inner power layer.
3. Finish the 4 open nets interactively (press `X`, follow ratsnest): RF_ANT as a 50 Ω jog to
   the edge SMA, and the +5V_USB / boot-cap stubs. The JLCPCB fab package is in
   `PCB/FCM_KiCAD/gerbers/` (upload `WYVERN_E2_FCM_gerbers.zip`; add BOM + CPL for assembly).
4. Run DRC; re-export Gerbers (or use the provided `gerbers/` package); fabricate ENIG, 2 oz inner copper.

### B.2 Assembly & bring-up

1. Reflow/hand-solder per the BOM; inspect the RP2350B QFN-80 and fine-pitch sensors.
2. Power over USB-C first (no battery); confirm 3.3 V and 5 V rails.
3. Flash firmware; verify each sensor on its bus (ICM SPI, BME/LIS/INA/BNO I2C), NAND +
   microSD read/write, camera capture.
4. **Solenoid loop test** (bench, no motor): command each coil; confirm 20 kHz PWM, shunt
   current readback, and gimbal motion to ±5°; verify spring return on power-off.
5. Mount the FCM to `04_pcb_internal_mount`; slide into the avionics bay rails; route the
   camera to the pod window and the BNO055/coil harnesses.

## Part C — Ground Testing

### C.1 Motor static fire (test stand)

1. Stake `TS_base_plate` into firm dirt; assemble tower + load-cell bracket; install the
   Wishiot bar cell (10 kg) with HX711 → Metro M4 + microSD.
2. **Calibrate** with an Estes E16-4 (known 32.5 N·s); compute N/count; integrate to confirm
   impulse.
3. Static-fire a G78 and an F25; log thrust curves. **Watch for cell clipping at the G78 peak
   (101.9 N > 98 N)** — if clipped, fit a 20 kg cell and re-calibrate.
4. Compare measured $I_t$ / $\bar F$ to published; update the trajectory model.

### C.2 Wind-tunnel fin down-select

1. Print candidate fins (one geometry per print). Assemble the Printables modular tunnel +
   120 mm fan adapter; fit `WT_120mm_fan_collar` and `WT_fin_test_mount`.
2. Mount ONE fin in the turntable; sweep angle of attack via the 15° index holes.
3. Measure normal force / pressure at matched Reynolds number; repeat per candidate.
4. Select the geometry with the best lift-to-drag and CP behavior; this becomes the flight fin.

### C.3 Ground ejection test

1. With the recovery bay packed (chute + 6 ft Kevlar), test-fire the FFFFg charge in the
   E-Match Mate canister; confirm clean separation and full chute extraction.
2. Tune charge mass; repeat for both the booster and main events.

## Part D — Pre-Flight Assembly (at the field)

1. Pack the main chute (18″, or 24″ if selected) with the 6 ft Kevlar shock cord; nose
   shoulder dry-fit.
2. Pack the booster chute; set the interstage coupler with the 2nd-stage igniter channel clear.
3. Install motors: F25 in the sustainer gimbal cradle; G78 in the booster; retainers on.
4. Charge/secure the 12 V NiCd pack; connect to the FCM (XT60). Confirm boot, GPS/baro zero,
   storage armed.
5. **Energetics last, on the pad**: install the First Fire Jr. sustainer igniter; connect the
   MJG initiators + ejection canisters to the onboard FCM pyro channels. Verify continuity reads
   on the FCM (drogue/main/ignition).
6. Set the onboard FCM deploy thresholds (baro apogee → main; drogue per booster recovery plan).

## Part E — Launch (Estes Pro Series II rail + controller)

1. Place the vehicle on the rail; verify free travel. **Use the rail extension** (rail-exit
   velocity is marginal at 10.0 m/s — Math §4).
2. Arm in this order: recovery (FCM pyro) → TVC enable → FCM "armed." Confirm the staging
   interlock is active (drogue inhibited until sustainer ignition + separation).
3. Clear the range; RSO go.
4. Launch. Flight sequence: G78 boost → booster burnout → sustainer ignition (TVC active) →
   booster separation + booster chute → sustainer coast → apogee → main chute.
5. Track the rocket visually through descent; recover and note landing coordinates (all flight data is on the onboard SD-NAND/microSD).

## Part F — Recovery & Post-Flight

1. Recover both stages. Safe any unfired energetics before handling.
2. Power down the FCM; pull the microSD and/or download NAND over USB-C.
3. Extract flight video; review TVC loop logs, attitude, and the full sensor record.
4. Inspect the airframe, gimbal, and fins; log any damage and descent-rate adequacy.
5. Update the trajectory and TVC models with measured data; iterate.

## Appendix — Field Checklist (quick)

- [ ] Chutes packed (main + booster), shock cords attached
- [ ] Motors installed + retained (F25 sustainer, G78 booster)
- [ ] Battery charged + connected; FCM booted, storage armed
- [ ] Igniter + ejection charges connected (on pad); continuity verified
- [ ] Onboard FCM deploy thresholds set
- [ ] Rail extension fitted; vehicle travels freely
- [ ] Staging interlock confirmed; TVC enabled
- [ ] Range clear; RSO go
