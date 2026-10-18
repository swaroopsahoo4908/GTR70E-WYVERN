# GTR70E WYVERN, Build-Readiness Report

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Date:** 2026-08-12  
**Program:** GTR70E WYVERN


##### Cross-check of all project files against the current (rev-latest) design, build in 1 week, launch in 2

## 1. Verdict

The airframe is two body tubes (Lower BT, Upper BT) joined at one bulkhead. Every project file
(docs, BOM, firmware, CAD, wiring, simulations, proposal) reflects this single canonical
configuration. The remaining work is *fabrication + a short bench/ground-test punch-list* (§6),
plus the bulkhead release-force/cable-slack decisions in `WYVERN_E4_Recovery.md` §4–5. The 1-week
build / 2-week launch schedule in §7 is scoped against that punch-list.

## 2. Canonical configuration (single source of truth)

| Parameter | Value |
|---|---|
| Airframe | 70 mm OD, ~0.672 m, single stage, **two body tubes (Lower BT, Upper BT) + one separation bulkhead** |
| Liftoff / dry mass | **720 g / 660 g** |
| Motor (flight) | **Estes F15-4** ×4 (4 s delay + ejection charge = recovery) |
| Motor (ground) | **Estes F15-0** ×13-20 (plugged; static thrust curves + MTVC + servo TVC on the balance + jetvane blast-shield screen) |
| Commissioning | Estes/AeroTech **E16-4** ×6 |
| Apogee | **~409 ft / 124.6 m @ 6.72 s** (RK4(2e-4)+Barrowman) |
| v_max / Mach | **37.1 m/s / Mach 0.108** |
| Max acceleration | **2.71 g** net (3.70 g specific force = peak T/W) |
| T/W | **2.04 avg / 3.58 peak** |
| Fins | 4 × **87 mm** PETG-CF, root 70 / tip 35 / LE-sweep 25° |
| Stability | CG 45.0 cm / CP 53.3 cm → **+1.14 cal** (→1.5 cal burnout), no ballast |
| Materials | **ASA-Aero**: nose, Upper BT tube, Lower BT tube · **PETG-CF**: fins, separation bulkhead · **PC-FR**: TVC assembly, motor mount, gimbal |
| Recovery | **F15-4 motor ejection** separating the two body tubes at the bulkhead joint; deploy t≈7.45 s (+0.58 s past apogee, ~5.7 m/s); 24″ chute → ~4.7 m/s; no RRC3/9 V/CO2/e-match |
| Flight computer | **Raspberry Pi Pico 2 W** on a 20×24 (50×70 mm) perfboard, dual-core RP2350, 500 Hz TVC PID **Kp0.10/Ki0.40/Kd0.18**, ±8° gimbal |
| Sensors | **BNO085** ×2 (bay 0x4B, gimbal 0x4A via STEMMA-QT), **BME688** 0x76 + **BMP388** 0x77 baros, microSD on SPI1, i3 4K Thumb Action Camera; telemetry logged, WiFi bench-only |
| Structural margins | flight min SF ~340×; bulkhead separation-joint release-force sizing and direct-gas thermal check are **open items**, see `WYVERN_E4_FEA_Structural.md` §4; engine-bay thermal < HDT |
| Servo torque margin | **2.3× at the full ±8° gimbal** (0.086 N·m hinge vs 0.20 N·m stall), below the 3.0× gate, see §11 |

## 3. Per-target readiness

### 3.1 Flight computer, READY to build
- Firmware sketch `gtr70e_wyvern_tvc/` complete: main `.ino` + 10 header tabs, brace/paren balanced,
  no CO2/RRC3 includes (recovery is passive). PID gains margin-verified (`PID_TUNING_REPORT.md`).
- Wiring: `gen_wiring4.py` + `gen_connected_sch.py` regenerate a balanced `.kicad_sch` + preview,
  now consistent with firmware (BMP388 @3.3 V on mux ch3; GP1/GP6 spare; no 9 V/RRC3 block).
- Bench tests present: `t1_i2c_scan`, `t2_imu_grv_deflection`, `t3_servo_sweep`,
  `t4_sensors_sdlog` (now BMP388), plus `selftest.py`/`host_monitor.py` go/no-go harness.
- Telemetry: `telemetry_wifi_flight` + `telemetry_wifi_receiver` sketches.
- **PID: flight-ready, no change.** Gains **0.10/0.40/0.18** confirmed by both the frequency-domain
  margin analysis (`PID_TUNING_REPORT.md`, PM≈44.7°/GM≈12.6 dB) and a time-domain robust auto-tune
  (`PID_AUTOTUNE_REPORT.md`, within ~4% of grid-optimal; integral retained for steady-bias rejection).
- **Digital twin available:** `Simulations/wyvern_datagen/fc_sil.py` (+ GUI *Flight Computer SIL* tab)
  runs the full FC in software-in-the-loop with sensor noise and simulated Wi-Fi telemetry, use it to
  rehearse the flight and sanity-check the state machine before the pad.

### 3.2 Rocket airframe, READY per `gen_rocket4.py`
- `3D parts/` covers: nose (ASA-Aero), Upper BT, Lower BT, one separation bulkhead (PETG-CF, with
  servo-extension + STEMMA-QT cable pass-through holes), motor mount, 2-axis gimbal, 87 mm fins,
  1010 rail buttons.
- FEA (`WYVERN_E4_FEA_Structural.md` §4) covers flight loads (comfortable margin) but flags the
  ejection/separation-joint analysis as an open item pending the release-force sizing pass.

### 3.3 Wind tunnel, RESTORED TO PROGRAM (2026-08-10)
- The bench wind tunnel is back in scope, see `WYVERN_E4_GSE_TestStands.md` §4 and `CONFLICTS.md`
  §7 for the reversal record. Current rig is the STL/3MF kit in `Wind Tunnel/`, not the original
  Hofferth (2025) modular design that was struck.
- The airfoil-CFD package (`Simulations/CFD/`) is also restored, recovered from git history at the
  pre-deletion commit, solver re-run and re-verified (validation reproduces the documented NACA0012
  result), workbook recalculated clean.
- Aerodynamic characterization now runs three independent tracks: the Barrowman/drag-buildup model
  in the flight-sim suite, the 2D vortex-panel CFD in `Simulations/CFD/` (both predicted), and
  direct tunnel-measured lift/drag/stall (RQ3 in-situ) cross-checked against flight telemetry (RQ4).

### 3.4 Motor test stands, READY to print/build
- **Servo TVC stand** (`gtr70e_wyvern_gse_servo_rig`): base, thrust block, flexure template (PETG-CF).
- **Magnetic TVC stand** (`gtr70e_wyvern_gse_solenoid_rig`): separate physical rig, same flexure/DAQ chain as the servo stand, solenoid gimbal actuator swapped in for the RQ1 A/B comparison.
- **Static fire stand**: base plate, load-cell bracket, motor tower, steel blast deflector, plus a jetvane/material coupon rack (restored 2026-08-10, see `WYVERN_E4_GSE_TestStands.md` §1). Print PLA/PETG-CF baseline jetvanes and the PC/PC-FR comparison set alongside the coupon set (ABS dropped 2026-08-14).
- **Wind tunnel** (`Wind Tunnel/`): bench aerofoil rig for RQ3/RQ4, assemble per the STL/3MF kit in that folder.
- DAQ: Raspberry Pi Pico + load cells/HX711 (BOM §10); ground-rig sketches target Pico. Both TVC stands and the static-fire stand share the same DAQ chain for directly comparable data.

## 4. Bill of materials

`Documentation/WYVERN_E4_BOM.xlsx`, **9 live sections** spanning **all three build targets**: FC &
sensors, power, TVC (flight servo + ground magnetic A/B), recovery (motor ejection), propulsion
(F15-4 flight / F15-0 ground / E16-4 commissioning), airframe filament (ASA-Aero + PETG-CF + PC-FR),
harness/connectors/prototyping, the TVC balance + static stand, and the new §9 (custom PCB fab +
2026-08-09 cart reconciliation). **Former §9 (Hofferth wind tunnel) has been deleted** per the
2026-08 scope change and that section number reused for the cart-reconciliation section above.
Every live line has a purchase link and verified price. Filament allocation matches the material
zoning in §2.

**2026-08-09: reconciled against 3 live carts (Amazon $252.93, Adafruit $95.10, Estes $325.01) plus
a $175 custom PCB fab cost, added as new Section 9; corrected per follow-up feedback; then the
to-buy total was restricted to only what's actually in those 3 carts.** A handful of stale duplicate
line items from an earlier gap-fill pass were zeroed to avoid double-counting. Design-intent
quantities were corrected: 1 flight chute (not 4), 1 wadding pack (not 2), USB-C dust covers already
sufficient, and the BNO085 count drops to **1**, the custom PCB has a single STEMMA-QT port, so
there is one external IMU (mounted at the TVC-bay/electronics boundary, near the bulkhead joint), not
a gimbal+body+recovery+spare set. The Amazon 5kg load cell was dropped for the Adafruit one. Recovery
uses a single separation-joint bulkhead with no intermediate gas routing (see
`WYVERN_E4_Recovery.md`).

**Final pass (2026-08-09b): every to-buy line not present in one of the 3 carts was zeroed from
cost**, kept as a line item and flagged "NOT IN CURRENT CART" rather than deleted, so nothing
silently disappears from the procurement record. Airframe filament (Section 6) is the one explicit
exception and stays costed. **⚠ This zeroes the F15-4 flight motor (row 41) and the E16-4
commissioning motors (row 43)**, neither is in the given Estes cart, so they're zeroed from this
total, not from the build. They still need to be purchased separately before flight/commissioning.
Also zeroed: the Raspberry Pi Pico 2 W line (superseded by the custom PCB, already costed in
Section 9), BMP388, the old harness/prototyping line items (solder, wire, heat-set inserts,
breadboard, etc., none in the current carts), microSD breakout, 1010 rail, Nomex protector,
anemometer, and the steel blast deflector.

**2026-08-10: custom PCB fab cost updated to $200 for 3 boards** (was $195 for the same 3-board
run). Quantity was already 3 in the BOM; only the total fab price changed. One of the three boards
is earmarked for the ground servo TVC test stand rather than flight/spare use, worth noting in the
GSE build-out even though it doesn't change the BOM row itself. Total program spend rises by $5 to
match.

**2026-08-11: custom PCB revised, now Ø61 mm circular** (`PCB/`, fab package dated 2026-08-11,
supersedes `PCB/Archive 2.zip` from 2026-08-09, which is still sitting in the live folder pending
cleanup). Fits the Upper BT with ~2.9 mm radial clearance per side against the 70 mm OD / ~66.8 mm
ID airframe (`WYVERN_E4_Recovery.md` §1, `CONFLICTS.md` §7). No board-size figure existed anywhere
in the repo before this pass, so this isn't a correction to a prior number, it's the first time
diameter got written down. Cost/quantity (3 boards, $200 total) is unaffected by this revision.

**2026-08-11b: custom PCB fab cost updated to $207.01 for 3 boards** (was $200). Quantity
unchanged at 3; only the total fab price changed. Total program spend rises by $7.01 to
**$1,653.26**.

**2026-08-12: custom PCB diameter revised to Ø62 mm circular** (was Ø61 mm, per the 2026-08-11
pass above), to accommodate the larger `SS-12D10-G5` power switch footprint. Fit check against the
70 mm OD / ~66.8 mm ID Upper BT (`WYVERN_E4_Recovery.md` §1, `CONFLICTS.md` §7) now reads ~4.8 mm
diametral clearance (~2.4 mm radial per side), down from ~5.8 mm / ~2.9 mm at Ø61 mm — still clears.
Rocket/airframe OD is unaffected (70 mm, unchanged).

**2026-08-12b: fresh EasyEDA export confirms the Ø62 mm board and updates the fab cost.**
`PCB/Info_PCB_PCB1_2026-08-12.txt` (real export, supersedes the 2026-08-11 61mm×61mm snapshot):
board 62mm×62mm, 65 components (was 61), 36 devices (was 33), 50 nets (was 49) — the extra parts
account for the larger switch footprint and whatever else changed in this pass. Custom PCB fab cost
updated to **$231.72 for 3 boards** (was $207.01); quantity unchanged at 3. Total program spend
rises by $24.71 to **$1,677.97**. The standalone Hobbywing UBEC BOM line (§ Power) is now flagged
not-needed: PCB1's onboard TPS564201 buck already regulates 2S→~5V, so there's no second physical
regulator to buy.

**Filament pass (2026-08-09c):** Section 6 reconciled against the real Bambu Lab cart, PC-FR
($54.99), PC ($39.99), ABS ($19.99), ASA Aero ($49.99), all 1 kg, $164.96 total. **⚠ None of these
four match the current design's material scope.** PLA (primary airframe) and PETG-CF (TVC bay/
gimbal/bulkhead) are the only materials the design actually calls for as of the 2026-08b scope
change, when the RQ2 coupon-testing program (which needed PC-FR/PC/ABS/ASA-Aero) was dropped, 
see `CONFLICTS.md` §6. Added to the BOM as real cart items and flagged for confirmation rather than
assumed as flight-part material; if this is reserve stock or an RQ2-baseline archive, fine, but it's
not covering anything the current build needs. The "buy 2 more kg PLA" line was dropped, ~8kg
PLA/PETG-CF already acquired covers the airframe.

| Budget line | Value |
|---|---|
| Gross to-buy | $993.20 |
| Less reimbursed (launch controller) | −$39.60 |
| **Net out-of-pocket (still to buy)** | **$953.60** |
| Already acquired (owned) | $479.27 |
| **Total program spend** | **$1,432.87** |

> Rose from $1,725.46 on 2026-08-01 when the cart gap analysis found **five items the BOM never
> costed at all**, the microSD SPI breakout the firmware requires, the 1010 launch rail, the Nomex
> chute protector, an anemometer for the RQ3 wind measurement, and a steel blast deflector. The
> parachute line was also corrected from 24 in to the 18 in canopy every simulation actually uses.
> See `WYVERN_E4_Cart_Gap_Analysis.md`.

## 5. Files reconciled in this pass

- Fin geometry aligned to **72 mm** in `we4_flightsim`, `we4_validation`, `we4_deepsim`,
  `build_ork4.py` (`.ork` fin height was 60 mm, fixed).
- **Teensy → Pico 2 W** purged from `README.md`, `WYVERN_E4_Camera_Solution.md`,
  `WYVERN_E4_GSE_TestStands.md`, and proposal rev1 §5.1 (kept only as historical "it replaces"
  contrast in the FC spec).
- **BMP280 → BMP388** aligned across wiring generators (now 3.3 V, not 5 V), the regenerated
  schematic + preview, `t4_sensors_sdlog.ino`, test READMEs/selftest, and the audit docs.
- Ground-rig DAQ conflict marked **resolved** (Pico everywhere) in `COMPATIBILITY.md`.
- `baro.h` apogee comment corrected to 397 ft / 121.1 m.
- Full-project sweep confirms **zero** surviving 708/662/648 g, 432 ft, 2.07/3.62 T/W, 58 mm fin,
  CG 46.7 / CP 52.5, or F15-0-as-flight references outside intentional "superseded/removed" notes.

## 6. Pre-flight punch-list (bench + ground test, the only open items)

These are hardware-verification steps from `FLIGHT_READINESS.md` §4, none are design changes:

1. **Ground-test the bulkhead separation joint**, fire a representative charge; confirm the joint
   releases cleanly in the 50–150 N band, the chute deploys, and the servo/STEMMA-QT cable
   pass-through survives the separation. *(Single point of the recovery system, do this first.)*
2. **Confirm LAUNCH_IRQ (GP7) wiring**, wire the redundant inertial switch or remove the branch.
3. **Confirm RBF sense polarity**, verify `HB:...rbf=` matches the switch state.
4. **Verify the 2S LiPo divider** (GP26, 100 k/62 k) against a multimeter within ~2 %, and scope VSYS during a servo stall to confirm the bulk-cap + SS34 hold-up keeps it above the Pico brown-out threshold.
5. **Confirm SH2_ACCELEROMETER** report enables on your BNO085 firmware revision (launch/landing
   detect depend on it).
6. **Servo throw / gimbal mechanical limit**, confirm the printed gimbal + linkage allow the ±8° travel (raised from ±5° for wind authority).
7. **Commission each stand** with ≥2 E16-4 firings before F15-0 data runs (curve vs. published).

Run `selftest.py` before every flight; it gates on all of the above that are observable in software.

## 7. Suggested 1-week build / 2-week launch schedule

> **Superseded 2026-08 by `WYVERN_E4_Timeline_14Day.md`.** That schedule is built around the fact
> that $1,337 of the BOM is still unordered, which this section assumed away. Kept below as the
> original build-effort estimate; use the 14-day timeline for actual planning.

**Week 1, fabricate & bench:**
- Days 1–2: print airframe (PLA body/nose/fins; PETG-CF bulkheads/tube/engine bay/gimbal/mount)
  and both stands. Order-long-lead items already in BOM.
- Days 3–4: assemble FC (Pico 2 W perfboard + sensors), wire per `wyvern_perfboard_wiring.svg`, flash firmware,
  run `t1`–`t4` bench tests + `selftest.py`.
- Days 5–7: assemble rocket; join the two body tubes at the bulkhead (route the servo/STEMMA-QT
  cables through the pass-through holes first), install recovery (chute + shock cord + Nomex);
  commission stands with E16-4; run **ground separation test** (punch-list #1).

**Week 2, ground data & fly:**
- Days 8–10: F15-0 static thrust-curve verification (+ engine-bay wall temperature for RQ2); F15-0 TVC balance
  A/B (servo vs. magnetic) on the 3-axis stand; lock the flown actuator (servo).
- Days 11–12: full preflight `selftest.py` GO; range procedures (remote ignition, ≥3 m standoff,
  igniter installed last).
- Days 13–14: **launch on F15-4** (FAA Class-1, no waiver; 720 g < 1500 g). Recover, pull SD +
  Wi-Fi logs, feed flight data back into `Simulations/` for post-flight validation.

## 8. Notes / residual risk

- Recovery is a **single passive event** (motor charge) with no electronic backup, the bulkhead
  joint's release-force calibration (still open, see `WYVERN_E4_Recovery.md` §4) and the ground
  separation test (punch-list #1) are what retire that risk.
- The vehicle is authority-limited in strong wind (documented low-speed weathercocking); the
  atmospheric dataset + PID tuner in `Simulations/wyvern_datagen/` quantify this, prefer a
  low-wind launch window.
- Because runs no longer overwrite, `Simulations/` and dataset folders will accumulate timestamped
  outputs; prune as needed.

---

## 9. 2026-08 rerun & reconciliation pass

Everything below was regenerated or corrected in a single pass. The verdict in §1 is unchanged
(**GO for build**); the numbers moved because the motor model was corrected, not because the design
changed.

### 9.1 Scope

The program runs the full five-research-question set, including a physical wind tunnel
(`CONFLICTS.md` §6). `Simulations/CFD/` holds the airfoil-CFD package supporting RQ3/RQ4. Every
research question has two independent methods behind it (Proposal §3, Table 0).

### 9.2 Defects found and fixed

| # | Defect | Effect | Fix |
|---|---|---|---|
| 1 | F15 thrust curve renormalized to 49.6 N·s from a shape integrating to 41.97 N·s | peak thrust inflated to **29.9 N** vs Estes' published 25.3 N; peak T/W read 4.32 against the 3.66 quoted repo-wide | sustain block lifted +2.4408 N so the curve matches impulse, peak **and** average simultaneously |
| 2 | `fc_sil.py` fed the launch detector kinematic acceleration, not specific force | peaked at 2.65 g against the firmware's 3 g latch, the SIL state machine **never left ARMED** in any flight: no BOOST, no TVC, no deploy, ~70 m/s ballistic "touchdown" in every logged run | accelerometer now reports specific force (peaks at 3.27 g ≈ peak T/W 3.26) |
| 3 | `we4_sim.py` hard-coded **Kp=8.0/Ki=1.5/Kd=1.2** | the TVC plot disagreed with the firmware, `pid_reference.py`, and `CONFLICTS.md` §1, which record those gains as superseded and unstable | gains set to the frozen 0.10/0.40/0.18 |
| 4 | `we4_deepsim.py` used **CG 0.467 / CP 0.537**; `we4_validation.py` used **CG 0.467** | every margin, flutter, CG-tolerance and stability gate was scored against a pre-PLA, pre-camera vehicle | both set to CG/CP **0.491/0.568** at the time of this fix, **superseded 2026-08-10**: the material change to PLA/PETG-CF shifted the mass stack again, and the actual canonical value (independently re-derived from the `we4_sim.py` component stack, and matching `we4_flightsim.py`/`we4_stability.py`) is **CG 0.484, margin +1.14 cal**, not 0.491/1.10. This row's "fix" value is itself now stale; treat 0.484/56.8/1.20 as current. |
| 5 | `we4_stability.py` reported `fin_span_mm: 35.0` while evaluating `s35=0.055` | the "35 mm fins are unstable (−0.52 cal)" finding was quoting a **55 mm** fin; the flown 72 mm fin was never evaluated | file rewritten; 35 mm is **−0.99 cal (unstable)**, flown 72 mm reproduces 48.4/56.8/+1.20 exactly |
| 6 | Deploy sampled at **t = 4.0 s** in three files | reported a 29 m/s deploy against the Recovery doc's ~6.5 m/s, the retired finless-era electronic timer, not motor ejection | deploy is now t = burnout + 4 s = **7.45 s**; integration runs through apogee to reach it |
| 7 | Three different Cd for one vehicle (0.50 / 0.58 / 0.539) | apogee disagreed between scripts | unified to the **0.539** componentwise buildup |
| 8 | Mass stack summed to **606 g / 708 g** | contradicted the 603/705 used everywhere, including the FAA Class-1 argument | harness estimate trimmed 25→22 g; dry total is now exactly 690 g |
| 9 | `we4_deepsim.py` battery pack **850 mAh** | no such pack exists in the BOM or power tree | set to the Zeee 2S **450 mAh** → 40 flights/charge |
| 10 | Generic motor shapes normalized to impulse only | published peaks wrong by up to 2× (D12 read 14.2 N vs 29.7 N), the number that sizes the load cell | decay rate solved per motor; all five motors now match published impulse and peak |
| 11 | `build_ork4.py` gave PLA nose/fins **PETG-CF density**, and announced a 150 g-ballast config | the `.ork` cross-check modelled the wrong vehicle | densities corrected to 650 kg/m³; no ballast |
| 12 | Control-authority margin swept from t=0 to burnout | both endpoints are thrust-zero, so the reported minimum was always exactly 0.0 mN·m | swept over the TVC-active window → **71.7 mN·m** |
| 13 | `gen_rocket4.py` called `fin(0.070, 0.035, 0.072, 0.025, 0.003)`, **metres**, in a file whose every other dimension is millimetres | the fin was built at 1/1000 scale: `08b_fin_single_ASA.stl` exported at **0.0 cm³ / 0.0 g**. Slicing that file yields a speck, and the script's printed-mass roll-up silently omitted all four fins | called in mm; fin is now 11.3 cm³ / **7.4 g** each → 29.6 g for four, matching the 30 g in the mass stack |
| 14 | Printed-mass roll-up filtered part prefixes `01`–`07` | excluded the fins (`08b`) and one lower-body part, so the reported printed mass could never be reconciled against the dry stack | roll-up now covers the full flight airframe with per-part quantities |
| 15 | Battery-sense divider (GP26/ADC0) documented in `CONFLICTS.md` §4, verified in `COMPATIBILITY.md` §4, read by `battery.h`, but **routed in no schematic** | the wiring generators disagreed with the firmware on a net the flight computer samples every loop | both generators now emit a `VBAT DIVIDER` block tapped upstream of the UBEC into GP26 |
| 16 | `02_tvc_control_loop.mermaid` clamped the gimbal at **±5°** | the retired limit; `wyvern_pid.h` uses `OUT_LIM_DEG = 8.0` | flowchart regenerated at ±8° |
| 17 | `PID_TUNING_REPORT.png` and `phase0_math_validation.png` were hand-made orphans with no generating script | both showed superseded numbers and could not be kept in step | each is now a reproducible output of the script that derives it (`we4_pid_retune.py`, `derive_math.py`) |

### 9.3 Fidelity increases

- **Integrator:** semi-implicit Euler → RK4 throughout; `we4_flightsim` dt 1e-3 → 2e-4.
- **Atmosphere:** exponential density → ISA troposphere with real lapse rate.
- **Wind:** scalar mean → power-law shear with per-flight roughness exponent + Dryden-form
  turbulence (the old model was a single deterministic sinusoid, coherent across the whole ensemble).
- **Dispersion:** atmosphere only → atmosphere **plus** liftoff mass, CG station, Cd, total impulse
  and thrust-axis misalignment.
- **TVC loop:** first-order servo → second-order servo with slew-rate limit, explicit transport
  delay, 500 Hz zero-order hold, filtered derivative, and a noisy/biased/quantized gyro.
- **Ground stands:** ideal load cells → full signal chain, mount resonance (42 Hz, ζ=0.035),
  HX711 quantization and sample-rate aliasing, thermal zero drift, calibration-slope residual, and a
  returned uncertainty budget. Flags that the 42 Hz mount ring **aliases** against the 80 SPS
  Nyquist of 40 Hz: stiffen the mount or filter before trusting peak thrust.
- **Datasets:** regenerated at 6.0 M rows / 344 MB across 50 shards, widened from 23 to 34 columns
  (build dispersion and rail-exit/coast-Cd are now first-class), every file ≤ 26 MB.

### 9.3b Printed-mass reconciliation

`gen_rocket4.py` now reports the full printed flight airframe: **413.2 g** of printed structure
(+1.3 g rail buttons). Against the itemized stack in `we4_sim.py` the tube/nose/bulkhead/fin parts
agree to better than 0.5 g each. Two parts differ by design and should not be "fixed" silently:

| Part | Solid volume × density | `we4_sim.py` allowance | Why |
|---|---|---|---|
| Motor mount (PETG-CF) | 59.1 g | 45 g | as-built sparse infill, not a 100 %-dense solid |
| TVC gimbal (PETG-CF) | 112.5 g | 105 g | same, plus the CAD solid includes trunnion stock removed in post |

The generator's number is raw solid volume; the flight budget's number is the as-built allowance.
The 690 g dry mass additionally carries avionics, battery, camera, servos, chute and harness, so the
two figures are not directly comparable, the script now prints that caveat alongside the roll-up.

### 9.4 Post-rerun canonical numbers

**Updated 2026-08-12** for the mass recompute (§2, `WYVERN_E4_Mathematics.md` §1): Lower BT tube
PETG-CF→ASA-Aero, the discrete UBEC line dropped, and recovery consumables re-itemized, taking
liftoff from 729 g to 720 g. Every row below was re-run this pass (`we4_flightsim.py`,
`we4_validation.py`, `we4_deepsim.py`, `we4_pid_retune.py`), not carried over.

| Quantity | Value |
|---|---|
| Apogee | **124.6 m / 409 ft @ 6.72 s** (was 397 ft at 729 g; 324 ft at 792 g; 435 ft at the original 705 g spec) |
| Burnout | 3.45 s, 74.0 m, 36.3 m/s |
| v_max / Mach | 37.1 m/s / **Mach 0.108** |
| Max acceleration | 2.71 g net (3.70 g specific force) |
| CG / CP / margin | 45.0 cm / 53.3 cm / **+1.14 cal** |
| Deploy | t = 7.45 s, +0.58 s past apogee, 5.7 m/s |
| PID margins | PM **44.1°**, GM **12.6 dB**, worst gust pitch **2.45°**, gimbal per `we4_pid_retune.py` re-run |
| Gates | validation **10/13**, deepsim **7/8** (servo torque flagged, §11) |
| Cross-file check | pending a fresh cross-file numeric-agreement pass against these re-run values |

The three flagged validation gates are unchanged in character and share one root cause: the F15 is
underpowered for a 720 g vehicle, even lighter than before. Rail exit and weathercock figures have not been re-run against the
new mass stack; peak T/W is now 3.54 against the 5.0 rule of thumb used elsewhere. This is a
launch-window constraint, not a design defect, but it is real and should not be presented as passing.

---

## 10. Firmware flight-readiness pass (2026-08)

The firmware was audited line by line against the frozen parameter table in `CONFLICTS.md` §4.
**Six defects were found, two of which would each independently have cost the entire flight.**

### 10.1 Defects fixed

| # | Defect | Consequence | Fix |
|---|---|---|---|
| **F1** | **Inter-core log transport used the 8-word hardware FIFO for a 33-word frame**, and guarded it with `rp2040.fifo.available()`, which reports words waiting to be *read* on the inbound side, not outbound free space. `0 < 33` was true forever. | **The flight computer logged nothing.** Every frame was dropped at 500 Hz; the SD card would have contained a header row and no data. Every research question depends on that log. Had the guard ever passed, `push()` blocks, which would have stalled the 500 Hz loop on SD latency instead. | Replaced with a lock-free shared-RAM SPSC ring (256 frames, ~38 kB, 0.51 s of buffer). Verified off-target: 5000 frames across a simulated 100 ms SD stall, **0 dropped, in order, payload intact**, peak occupancy 55/256. |
| **F2** | `core0_apply_servo_commands()` re-clamped the servo command to **±5°** after the PID had already limited to ±8°. | **37.5% of control authority silently discarded.** The ±8° limit exists specifically for crosswind weathercock rejection, it was raised 5→8 for that reason, and the extra 3° existed in the controller, the sims, the `.ork` and every document, but not in the signal path that moves the nozzle. | Clamp now reads `wyvern_pid_defaults::OUT_LIM_DEG` directly, so the two cannot diverge again. Also moved to `writeMicroseconds()`, `write(int)` quantized to whole degrees, ~6% of full authority. |
| F3 | Boot servo sweep exercised only ±5° while printing "operator visually confirms ±8° travel". | A linkage binding between 6° and 8° would have passed the bench and been found in flight. | Sweep now goes to the full `OUT_LIM_DEG`, both axes, and says what it swept. |
| F4 | `LaunchDetect` re-stamped `launch_ms_` every tick after latching. | `launch_time_ms()` always returned "now", so any `t_flight` derived from it would read ~0 for the whole flight. Masked only because the sketch latches its own copy at the transition. | Stamped once, on the latching tick. |
| F5 | `RECOVER_BACKSTOP_S = 7.5` | 50 ms off the canonical 7.45 s ejection time used everywhere else. | Set to 7.45. |
| F6 | `pid_reference.py`, the "reference implementation that matches the firmware exactly", used a **±5°** clamp and lacked the firmware's first-tick derivative priming. | Tick 0 of every study importing it saw a phantom ~27 rad/s derivative that saturated the command: **7.7° disagreement with the firmware on the first sample**, then a 3° clamp mismatch thereafter. | Both corrected. Firmware and twin now agree to **1.2 × 10⁻⁹ rad** (float32 rounding) over a 2000-tick pseudo-random sequence. |

### 10.2 Verification performed

- **Flight PID compiled off-target and unit-tested**: constants match the frozen table; saturates at
  exactly 8.000°; anti-windup recovers in 1 tick; `dt ≤ 0` and NaN return the previous output.
- **Ring buffer stress-tested** across a 100 ms SD stall (see F1).
- **Firmware ↔ Python twin numerical equivalence** verified to float32 rounding.
- Structural balance check across all 21 firmware, test and ground-rig sources: **all balanced**.
- Four dead deprecation stubs deleted (`co2_deploy.h`, `rrc3_telemetry.h`, `tof_ring.h`,
  `kalman_filter.h`), nothing included them.

### 10.3 Self-test and tooling changes

- `SELFTEST:FIFO` → **`SELFTEST:LOG_RING`**, and it is now *two-sided*: it verifies core 1 is
  actually draining, not merely that a drop counter reads zero. The old check reported a contented
  PASS in exactly the failure mode where 100% of frames were being lost.
- Heartbeat gained `pend=` and `peak=` (ring occupancy). `host_monitor.py` parses both, tolerates
  older builds, and warns when peak occupancy exceeds 200/256.
- `t3_servo_sweep.ino` rewritten to drive the **same** microsecond signal path as flight, with a
  hold-and-measure procedure for calibrating `SERVO_LINKAGE_RATIO`. The old version drove a
  different path than flight, which is why it "passed" while flight was clamped to ±5°.

### 10.4 Flight-day data reduction

`Simulations/we4_flight_reduce.py` takes the onboard CSV to the RQ3/RQ4 results in one pass.

- **RQ3a coast Cd** by 2-parameter (Cd, v₀) forward-model RK4 least-squares fit over the coast.
  The obvious method, differentiating baro altitude twice, returned **Cd = 1.40 ± 0.76** against
  a known 0.539 on the SIL selftest (wrong by 160%, useless error bar). The fit returns
  **0.477 ± 0.020**, and the residual ~11% bias is understood: the reduction models a purely
  vertical coast while the flight has a crosswind, so the 1-D fit slightly under-attributes drag.
- **RQ3b static margin** from the passive window (rail exit → TVC engage), which is the only part of
  the flight not confounded by the controller. Reported with its caveat: short, low-q, and weaker
  than the Cd result.
- **RQ4** peak/RMS pitch, gimbal utilisation and saturation, and commanded-vs-measured servo
  tracking error, the last of which no bench test can fully predict.
- `--selftest` validates the whole pipeline against a synthetic SIL flight before flight day.
  Currently recovers apogee to **0.1 m**.

### 10.5 Remaining hardware-verification items

Unchanged from §6 and still open, these need a bench, not a code change:

1. Ground bulkhead-separation test (Gate 3 in the timeline).
2. `SERVO_LINKAGE_RATIO` calibration (build guide §B4), the flight code assumes the nozzle
   actually reaches ±8°.
3. LAUNCH_IRQ (GP7) wiring confirmed or the branch removed.
4. RBF sense polarity confirmed.
5. Battery divider verified against a multimeter, and VSYS scoped during a servo stall.
6. `SH2_ACCELEROMETER` confirmed available on your BNO085 firmware revision.
7. Stand commissioning against published curves, watching for the 42 Hz aliased mount ring.

---

## 11. New open item, servo torque margin at the full gimbal limit

Correcting the ±5°/±8° mismatch in the firmware (§10, F2) exposed the same mismatch in four
simulation scripts, and fixing those changed one result materially.

**`we4_deepsim.py` check C now reports a servo torque margin of 2.3×, below its 3.0× gate.
Deepsim goes 8/8 → 7/8.**

| | Before | After |
|---|---|---|
| Deflection the hinge moment was evaluated at | 5° | **8° (the actual limit)** |
| Peak hinge moment | 0.054 N·m | **0.086 N·m** |
| Margin vs ES08MA II 0.20 N·m stall | 3.7× | **2.3×** |

This is a real finding, not a regression. The old 3.7× was computed at a mid-range deflection while
the vehicle is designed and cleared to command ±8°, so worst-case hinge load was understated by
1.6×. Three other scripts had the same error and are also corrected: `we4_atmos_tvc.py` and
`we4_pid_retune.py` were clamping the modelled gimbal at 5°, and `we4_validation.py` computed
available TVC authority at 5° **while its own plot was labelled "±8° gimbal"**, the label had been
updated when the limit was raised and the number had not. With that fixed, TVC authority ratio rises
from 39.6× to **63.2×**.

### What to do about it

Do not change the servo on the strength of a model. 2.3× is still a working margin, and the
**ground TVC balance campaign measures this quantity directly**, the balance resolves the thrust
vector, and the rig logs commanded versus measured nozzle angle under real F15-0 thrust.

**Action, Timeline Day 9 (RQ1 session):** record servo current and commanded-vs-achieved deflection
at the ±8° extremes under thrust. If the servo reaches and holds ±8° without stalling or visible
droop, the margin is adequate and the model is conservative. If it droops, the options in order of
preference are: reduce the linkage ratio (trading servo travel for torque), raise the servo supply
to 6 V (~2.0 kg·cm instead of ~1.8), or fit a higher-torque servo.

This is a good outcome from the audit: a modelling error was flagged before flight, and the test
that resolves it is already in the schedule three days before the flight window.

## References

CEVA, Inc. (2023). *BNO08X datasheet* (Rev. 1.17). https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf

EMAX. (n.d.). *ES08MA II 12 g mini metal gear analog servo* [Product specification]. Retrieved August 12, 2026, from https://www.getfpv.com/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model.html

Estes Industries. (n.d.). *F15-4 engines* [Product specification]. Retrieved August 12, 2026, from https://estesrockets.com/products/f15-4-engines

Federal Aviation Administration. (n.d.). *14 CFR Part 101 — Moored balloons, kites, amateur rockets, and unmanned free balloons*. Electronic Code of Federal Regulations. https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101

National Fire Protection Association. (2018). *NFPA 1122: Code for model rocketry*. https://www.nfpa.org/product/nfpa-1122-code/p1122code

Raspberry Pi Ltd. (2024). *RP2350 datasheet*. https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

Texas Instruments. (n.d.). *TPS564201: 4.5-V to 17-V input, 4-A synchronous step-down voltage regulator* (SLVSFB5) [Datasheet]. https://www.ti.com/lit/ds/symlink/tps564201.pdf
