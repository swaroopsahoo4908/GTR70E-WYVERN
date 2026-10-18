# Build and test procedure

## 1. Print settings

| Part | Material | Orientation | Settings |
|---|---|---|---|
| Nose, RB tube, control tube, MB tube | ASA-Aero | nose-up, vertical | per Bambu ASA-Aero profile (foaming), 1.6 mm wall = 4 perimeters. The control-tube servo pads and corbels are vertical plates: no supports |
| RB-floor coupler, plenum, MMT + aft ring, retainer | PC-FR | flat face down | 100 % infill, enclosure closed, 0.2 mm layers |
| Control fins (one per Phase A configuration, full sets of P* for Phase B and flight), stabilizers, hubs, IMU deck, avionics spine | PETG-CF | fins flat on the bed, hub shaft horizontal | 100 % infill on fins and hubs (the cross-pin hole is loaded) |
| Tunnel adapters, transition, fairings | ASA or PETG | | 3 walls, 15 % gyroid |

Print the control tube first and check the servo fit before printing anything else. The X08 Plus ear span, ear thickness, spline height and hole pitch are tagged VERIFY-WITH-CALIPERS in `wf_core.SERVO`. If a servo is tight in its window, change `SERVO` and regenerate. Do not file the pads.

## 2. Assembly (drawing D3)

1. Motor bay: heat-set M3 inserts in the MMT aft ring (4) and the plenum rim (3). Dry-fit the stabilizers through the wall slots onto the MMT. Bond stabilizers and MMT with J-B Weld using a printed 45° jig. Bond the plenum skirt into the MB bore, gallery side down; its bypass socket is on the axis. Slide the retainer collar on through its four stabilizer slots.
2. Servo ring: from inside the control tube, push each X08 Plus outward until its top passes through the pad window and the ears seat on the pad. Two M2 thread-formers per servo. Centre each servo electrically (t2 sketch, 1520 µs), press the horn into the hub pocket (2 x M2), fit the hub on the spline with the D-flat facing the fin chord line, and drive the servo screw through the hub bore. Route each lead up the diagonal gap beside its servo; nothing runs between the servo bases, where the bypass tube passes with 0.24 mm clearance.
3. Spine deck onto its corbels (3 x M2), servo leads up through the four diagonal slots.
4. Spine, on the bench before it goes in (drawing W4): BNO085 (low) and Feather (high) on the +X standoffs, BME688 (low) and the 4682 microSD (high) on the -Y pillars, the power perfboard on the +Y pillars, battery taped and strapped on -X. Wire per W1 and check the screw switch turns the system on. Then lower the spine onto the deck socket so the spider centres it.
5. Antenna whip from the Feather's top end down the wall over the +X face, about 20 mm from the aluminium tube.
6. Control tube onto the motor-bay shoulder, 3 x M3.
7. RB-floor coupler bonded into the recovery-bay aft end, M5 eyebolt fitted with its eye turned tangentially (radially it would hit the wall). RB onto the control tube, 3 x M3.
8. Bypass tube: O-rings in both sockets, a smear of Super Lube, then push it down the axis through the RB floor, spine and deck until it seats in the plenum. RTV the top land.
9. Fins onto the hubs, M2 cross-pins.

## 3. Bench checks

| Check | Pass |
|---|---|
| t1 I2C scan | Wire1 (STEMMA): 0x4A and 0x53. Wire (TX/RX pads): 0x77. Nothing else |
| Servo calibration (t2) | trim each fin to 0.0 ± 0.2 deg with the angle gauge; record µs per 10 deg into `fc_config.h` |
| SIGN CHECK (critical) | flight firmware, ARMed, `WYV_RAIL_CLEAR_MS` temporarily 0 and the launch threshold lowered on a bench build. Tilt the rocket nose toward +Y by hand: both A fins must move so their force points toward +Y (the trailing edges swing toward -Y). Repeat for +X with the B fins. All four fins sit at the same station, so both pairs should respond with the same amplitude. Any fin that goes the wrong way: flip its `WYV_SERVO_SIGN`. A wrong sign here is the single most likely way to lose the vehicle |
| Telemetry | ground station shows 2 Hz pad frames. ARM / DISARM / ZERO all work from the laptop |
| High-g channel | t1 sketch: the axis chosen in `WYV_ADXL_AXIS` reads +1 g ± 0.4 g with the rocket nose-up; after 30 s on the pad the logged `a_axial` matches the BNO's 1 g to within 0.05 g |
| Manoeuvre dry run | the SIGN CHECK bench build with `WYV_MAN_QBAR_MIN` and `WYV_MAN_ALT_MIN_M` also set to 0: 1.72 s after the fake launch the fins show the A doublet, the B doublet, then the two 1° steps, in that order and sense. Restore all three values before flight |
| Battery | 25 min pad soak at room temperature, then check the pack voltage. Expect about 57 mAh drawn |
| Range walk (t3) | 20 Hz frames at 300 m+ with the airframe on its side |

## 4. CG and margin check

Weigh the finished vehicle with a spent F42 casing plus 27 g of dummy mass in the bay. Balance it on a knife edge and compare with CG 360 mm. Adjust the nose ballast until the measured CG is within ±5 mm, then update `BALLAST_G` and the COTS masses in `wf_core.py` and re-run the cascade. The flight must show margin ≥ 0.9 cal (with interference) at liftoff.

## 5. Static burn

The spare F42-4T on the existing thrust stand (`Motor Test Stand/Static Stand`), fitted with the real plenum, MMT and retainer in a scrap MB tube. This confirms the thrust curve and checks that the retainer holds through the ejection charge (model kick-out about 0.9 kN at 0.3 g, 1.55 kN at 0.5 g).

## 6. Ground ejection test

Full stack, packed as for flight. Charge: 0.30 g FFFFg BP in an e-match cup taped into the plenum gallery, fired remotely.
- Pass: the nose separates cleanly and the chute is pulled out.
- If it fails, drop to one shear pin and retest. Then repeat at 0.70 g to check that nothing else moves (bypass, RB floor, joints).

## 7. Pad and range procedure

1. Install the motor and retainer (4 x M3). Igniter is not installed yet.
2. Screw switch in → buzzer chirps (PAD). Confirm telemetry and battery ≥ 7.8 V.
3. Rocket on the rail, buttons at az 22.5. ZERO from the laptop (captures the pad attitude).
4. ARM from the laptop → double chirp, state ARMED on the dashboard.
5. Igniter in, RSO check, launch. You have 2 h 50 min of battery for holds.
6. Recovery: landed beacon (1 Hz long chirp). Telemetry gives the last altitude and vertical speed.
7. Screw switch out. Pull the SD card and run `wyvern_host.py --decode WYFxxx.BIN`.
