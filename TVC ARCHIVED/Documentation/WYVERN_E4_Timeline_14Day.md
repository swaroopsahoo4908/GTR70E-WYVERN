---
updated_at: 2026-08-01
---

# GTR70E WYVERN, 14-Day Build-to-Flight Timeline

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


This is a procedure-level reference for what each build session actually involves — what a
static-fire day looks like, what the bench-bring-up sequence covers, and so on. The governing
calendar for the full five-research-question program is `WYVERN_E4_Timeline_3Month.md`, targeting
the Nov 7–8 / Nov 14–15 launch weekends; use that for pacing and this document for procedure
detail within any given session.

---

## 1. The one thing that decides this schedule

**$1,241 of the BOM is not ordered yet.** Nothing else on this page matters until that changes.
Every buildable task is downstream of parts arriving, and consumer shipping is 3–7 days. That is
half the window.

So the plan is built around one hard gate and one principle:

> **Gate 0, the order goes out on Day 0. Not Day 1.**
> **Principle, every task that does not need hardware happens while the parts are in transit.**

There is real work that needs no parts: the firmware is written and now fixed, the simulation suite
is complete, the data-reduction pipeline is built and self-tested, and the paper's methods and
apparatus sections describe things that are already designed. That work fills Days 0–4 completely.
If it is done in that window, the hardware days are pure build-and-test with no thinking left to do.

**Honest risk statement.** A 14-day order-to-flight schedule has no slack for a second shipping
cycle. If a critical part arrives dead or wrong, the flight slips past Day 14. The mitigations
below are real but they are mitigations, not guarantees: order priority shipping on the critical
path, order one spare of each cheap single-point-of-failure part, and accept that the ground
campaign (which is weather-independent and needs less hardware) is the fallback that keeps three of
the four research questions alive if the flight slips.

---

## 2. What each research question actually needs

Splitting the RQs by what gates them is what makes "don't lose anything" achievable, they do not
all depend on the same things, so they do not all carry the same risk.

| RQ | Needs | Gated by | Weather? | Risk if the schedule slips |
|---|---|---|---|---|
| **RQ1** actuator A/B | TVC balance + load cells + DAQ + F15-0 × 6 | parts, stand print | No | **Low**, ground only, can run any day |
| **RQ2** zoned materials | bend-to-fracture coupons (dead weight, no load cell) + engine-bay temp from the static fires | filament | No | **Lowest**, coupons print first, no motor needed for the bend tests |
| **RQ3** predicted vs in-situ stability | **One good flight** + measured wind | full vehicle, range, weather | **Yes** | **Highest**, needs the flight |
| **RQ4** gain sensitivity | **≥2 flights**, different gain sets | full vehicle, range, weather | **Yes** | **High**, needs repeat flights |

**Consequence:** RQ1 and RQ2 are scheduled *early and in parallel*, because they can be. RQ3 and RQ4
get the protected flight window plus a backup day, because they cannot be rescheduled cheaply.

---

## 3. Firing budget

The original BOM plan (13 × F15-0 ground, 4 × F15-4 flight, 6 × E16-4 commissioning) is 23 motor
firings. That is not achievable in two weeks alongside everything else, and it is not necessary.
This is the reduced plan that still answers every RQ:

| Motor | Count | Purpose | RQ |
|---|---|---|---|
| E16-4 | 4 | Stand commissioning, 2 per stand (curve vs published) | — |
| F15-0 | 6 | TVC balance A/B, 3 per actuator class | RQ1 |
| F15-0 | 2 | Static stand: motor thrust-curve verification (+ engine-bay wall temperature for RQ2) | RQ2 |
| **F15-4** | **3** | **Flight**, 2 gain sets + 1 spare/repeat | RQ3, RQ4 |
| — | 2 | F15-0 reserve for a failed or aborted run | — |

**15 firings total.** Order 4 × F15-4 (one spare beyond the three planned) and 10 × F15-0.

---

## 4. Day-by-day

Two tracks run in parallel from Day 5. Track A is the vehicle, Track B is the stands. They converge
on Day 10.

### Days 0–4 · Procurement + everything that needs no hardware

| Day | Task | Output | Gate |
|---|---|---|---|
| **0** | **PLACE THE ENTIRE ORDER, including the items in `WYVERN_E4_Cart_Gap_Analysis.md` that the current cart is missing.** The flight-blocking ones are the BME688, microSD SPI breakout, airframe filament, and the decoupling kit. Separately, **re-source the M2 linkage rod ends and the servos**, both currently deliver after the bench gate. | Priority shipping on: the flight computer fab, BNO085, servos, HX711 × 4 + load cells, ASA-Aero + PETG-CF filament, all motors. Order **spares** of the the flight computer fab, one BNO085, and one servo, they are cheap and each is a single point of failure. | Order confirmations, ETA per line | **Gate 0** |
| 0 | Flash the firmware to the flight computer, or run the SIL. Read §5 of `CONFLICTS.md`, the frozen parameter table is the contract the firmware is written against. | — | |
| 1 | Slice every print. Airframe, gimbal, both stands. Confirm plate layout, material assignment (PLA vs PETG-CF, see the zoning table), and total print hours. **This is the schedule's hidden long pole.** | Print queue with hour estimates | |
| 1 | `python3 we4_flight_reduce.py --selftest`, confirm the reduction pipeline passes on your machine. | `SELFTEST: PASS` | |
| 2 | Run the full sim suite end to end so every number in the paper is regenerable on demand. Read the go/no-go gates in `plots_val/validation_summary.json`. | 10/13 gates, 7/8 deep checks (the flag is servo torque, see §11 of the build-readiness report) | |
| 2 | **Start the paper.** Methods, apparatus, vehicle description, simulation methodology, none of this needs results. Target: §1–§5 drafted. | Draft §1–5 | |
| 3 | Build the ground-station laptop: Arduino IDE + Arduino-Pico core + the five libraries, `pyserial`, and a dry run of `selftest.py` against nothing (confirm it reports NOT SEEN cleanly rather than crashing). | Toolchain verified | |
| 3 | Range logistics: confirm the launch site, the RSO, and the two candidate flight days. Check the 10-day forecast. **Book the range now**, this is the other thing with a lead time. | Range confirmed | |
| 4 | Print any parts whose filament has already landed. Cut the Kevlar shock cord, pack the chute, prepare the Nomex. | Recovery pack ready | |
| **4** | **Gate 1, parts arrival check.** Anything critical still not shipped? Escalate now: local pickup, substitute, or accept the flight slips to the backup day. | Arrival status per line | **Gate 1** |

### Days 5–9 · Two parallel tracks

**Track A, vehicle**

| Day | Task | Gate |
|---|---|---|
| 5 | Print airframe: nose, Upper BT, Lower BT, separation bulkhead, motor mount, gimbal, 4 × fins, rail buttons. ~20 h of printer time, start the longest plate overnight Day 4. | |
| 6 | Populate and bring up the flight computer per the schematic. Confirm the onboard TPS564201 buck rail and INA226 monitor per `01_FlightComputer_Spec.md` §4. Keep the servo feed and logic feed as separate star runs off the buck output. | |
| 7 | Bench bring-up: `t1_i2c_scan` → `t2_imu_grv_deflection` → `t3_servo_sweep` → `t4_sensors_sdlog`, then `selftest.py`. Full procedure in `WYVERN_E4_Build_Guide.md` §B. | **Gate 2: `>>> PREFLIGHT GO <<<`** |
| 7 | **Calibrate `SERVO_LINKAGE_RATIO`** in `t3` and copy it into `wyvern4_tvc.ino`. Do not skip, the flight code assumes the nozzle actually reaches ±8°. | |
| 8 | Assemble the airframe. Route servo/STEMMA-QT cables through the bulkhead pass-through, join the two body tubes at the bulkhead joint, install rail buttons, mount the gimbal and servos. | |
| 9 | **Ground separation test**, the single most important pre-flight check. Fire a representative charge, confirm the bulkhead joint releases cleanly in the 50–150 N band and the chute deploys, confirm the cable pass-through survives. | **Gate 3: clean bulkhead separation** |

**Track B, stands (runs alongside Track A)**

| Day | Task | Gate |
|---|---|---|
| 5–6 | Print both stands: TVC balance base, thrust block, flexure; static stand base plate, load-cell bracket, motor tower. Fit the steel blast deflector. | |
| 6 | Wire both DAQs (Pico + HX711 × 3 on the balance, × 1 on the static stand). Flash the GSE rig sketches. | |
| 7 | **Dead-weight calibrate every load-cell channel** before any motor is anywhere near the stand. Known masses across the full range, record the transfer function per channel. | **Gate 4: cal residual < 1%** |
| 7 | **Print RQ2 coupons**, 2.0 × 15 × 100 mm in all five materials, identical print parameters, 5 each. Run the bend-to-fracture tests on the 80 mm-span dead-weight fixture; no motor and no load cell needed, do this while waiting on parts. | RQ2 fracture-mass data |
| 8 | **Commission both stands: 2 × E16-4 each.** Compare measured curve against published. Check for mount ringing, the bench model predicts a 42 Hz resonance that **aliases** against the 80 SPS HX711 sample rate. If you see it, stiffen the mount or drop to 10 SPS. | **Gate 5: measured curve within 10% of published** |
| 9 | **RQ1 data day: TVC balance A/B.** 3 × F15-0 per actuator class, step and ramp commands, log everything. | **RQ1 DATA COMPLETE** |
| 9 | **Also measure servo torque margin.** `we4_deepsim` check C now reports only **2.3×** against stall at the full ±8° (it was computed at 5° before). Record servo current and commanded-vs-achieved deflection at the ±8° extremes under thrust. See `WYVERN_E4_BUILD_READINESS.md` §11. | **Servo margin resolved** |
| 9 | **Static stand: 2 × F15-0**, motor thrust-curve verification, plus a thermocouple on the engine-bay wall for the RQ2 heat-deflection margin. | **RQ2 DATA COMPLETE** |

### Days 10–14 · Flight and reduction

| Day | Task | Gate |
|---|---|---|
| 10 | Integration: install FC, battery, camera in the airframe. Full mass check against the 792 g budget, **weigh it, don't assume**. Balance check: confirm CG at 48.4 ± 1 cm from the nose. | **Gate 6: 792 ± 15 g, CG 48.4 ± 1 cm** |
| 10 | Full `selftest.py` in flight configuration. Rehearse the pad procedure on the bench, start to finish. | |
| **11** | **FLIGHT DAY 1.** Two flights: gain set A (flight gains, Kp 0.10 / Ki 0.40 / Kd 0.18) and gain set B (the comparison set for RQ4). **Measure and record the surface wind at each launch**, RQ3's margin reconstruction needs it. | **RQ3 + RQ4 DATA** |
| 11 | Same evening: pull the SD cards and run `we4_flight_reduce.py FLIGHT_A.csv FLIGHT_B.csv --wind <measured> --label gainA gainB`. Results in minutes. | Reduction JSON + figures |
| 12 | **Backup flight day**, weather slip, or the third F15-4 for a repeat if either Day 11 flight was compromised. If Day 11 went clean, use this day for analysis and figure production instead. | |
| 13 | Reduce everything. Ground data (RQ1 actuator comparison, RQ2 material ranking) plus flight data (RQ3 predicted-vs-measured, RQ4 gain comparison). Produce every results figure. | All figures |
| 14 | Write the results section against real numbers. Update `CONFLICTS.md` and the build-readiness report with anything the hardware taught you. Archive raw data into `Data/`. | **Gate 7: results in hand** |
| **15** | **Paper writing starts.** §1–5 already drafted on Day 2; §6 onward written against data already reduced. | |

---

## 5. Slip triggers, decide early, not on the day

Pre-committing to these means you make the call with a clear head instead of at 6 a.m. on the range.

| If, by… | …this hasn't happened | Then |
|---|---|---|
| End of Day 4 | Critical parts not shipped | Move flight to Day 12, compress bench to one day. Ground campaign unaffected. |
| End of Day 7 | Bench self-test not GO | **Stop and debug.** Do not build the airframe around a flight computer that hasn't passed. Ground campaign continues on Track B regardless. |
| End of Day 9 | Ejection test not clean | **Do not fly.** A recovery failure loses the vehicle, the camera and all flight data at once, it costs RQ3 *and* RQ4. Re-seal and retest on Day 10. |
| End of Day 12 | No flight data | Accept RQ1 + RQ2 as the paper's primary results; write RQ3/RQ4 as sim-only with an explicit "flight validation pending" statement. **Say so plainly in the paper**, a stated limitation is publishable, an unstated one is not. |
| Any time | Weather outside the launch window | Do not force it. This vehicle weathercocks 63° at 10 m/s. A marginal-wind launch produces a flight you cannot cleanly interpret, which is worse than no flight. |

---

## 6. Standing weather limits

From `we4_validation.py` and the weathercock analysis, these are not conservative, they are what
the vehicle actually does:

| Parameter | Limit | Why |
|---|---|---|
| Surface wind | **< 5 m/s** (hard stop 7 m/s) | Rail exit is only 11.5 m/s; weathercock reaches 35° at 5 m/s and 63° at 10 m/s |
| Gusts | < 2 m/s above mean | Gust response is the RQ4 signal; large gusts swamp the gain comparison |
| Ceiling | > 300 m | Apogee is 98.9 m; you must be able to see it |
| Precipitation | None | Foamed ASA is not sealed, and the electronics bay is not weatherproofed |

---

## 7. What is already done (so you don't redo it)

- **Firmware is fixed and flight-ready.** The ±5° servo clamp, the inter-core log transport that
  dropped 100% of samples, and the launch-timestamp bug are all corrected. Details in
  `WYVERN_E4_BUILD_READINESS.md` §10.
- **Flight PID verified against its Python twin** to 1.2 × 10⁻⁹ rad over 2000 ticks.
- **Data reduction is built and self-tested**, `we4_flight_reduce.py --selftest` passes against a
  synthetic SIL flight, recovering apogee to 0.1 m.
- **Every simulation is regenerable** and 16/16 cross-file numeric checks agree.
- **Wind tunnel is gone**, BOM is 8 sections, program spend is $1,720.35 (see `WYVERN_E4_Cart_Gap_Analysis.md`, the current cart is missing 14 items, 5 of them flight-blocking).

---

## 8. Day-0 checklist, do these today

- [ ] Place the full BOM order, priority shipping on the critical path
- [ ] Add spares: 1 × extra the flight computer fab (custom flight computer, not a Pico), 1 × BNO085, 1 × servo
- [ ] Order 4 × F15-4, 10 × F15-0, 4 × E16-4
- [ ] Confirm launch site and RSO for Day 11, hold Day 12 as backup
- [ ] Slice all prints, total the hours, identify the longest plate
- [ ] Run `we4_flight_reduce.py --selftest` and confirm PASS
- [ ] Read `CONFLICTS.md` §4 (frozen parameters) and §6 (wind tunnel scope)
