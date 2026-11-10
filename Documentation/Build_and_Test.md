# Build and test procedure

## 1. Print settings

| Part | Material | Orientation | Settings |
|---|---|---|---|
| Nose, RB tube, control tube, MB tube | ASA-Aero | nose-up, vertical | per Bambu ASA-Aero profile (foaming), 1.6 mm wall = 4 perimeters. The control-tube servo pads and corbels are vertical plates: no supports |
| RB-floor coupler, plenum, MMT + aft ring, retainer | PC-FR | flat face down | 100 % infill, enclosure closed, 0.2 mm layers |
| Control fins (one per Phase A configuration, full sets of P* for Phase B and flight), stabilizers, hubs, IMU deck, avionics spine | PETG-CF | fins flat on the bed, hub shaft horizontal | 100 % infill on fins and hubs (the cross-pin hole is loaded) |
| Tunnel adapters, transition, fairings | ASA or PETG | | 3 walls, 15 % gyroid |

Print the control tube first and check the servo fit before printing anything else. The ES9251 II tab span, ear thickness, spline height and hole pitch are tagged VERIFY-WITH-CALIPERS in `wf_core.SERVO`. If a servo is tight in its window, change `SERVO` and regenerate. Do not file the pads.

## 2. Assembly (drawing D3)

1. Motor bay: heat-set M3 inserts in the MMT aft ring (4) and the plenum rim (3). Dry-fit the stabilizers through the wall slots onto the MMT. Bond stabilizers and MMT with J-B Weld using a printed 45° jig. Bond the plenum skirt into the MB bore, gallery side down; its bypass socket is on the axis. Slide the retainer collar on through its four stabilizer slots.
2. Servo ring: from inside the control tube, push each ES9251 II outward until its top passes through the pad window and the ears seat on the pad. Two M2 thread-formers per servo. Centre each servo electrically (t2 sketch, 1520 µs), press the horn into the hub pocket (2 x M2), fit the hub on the spline with the D-flat facing the fin chord line, and drive the servo screw through the hub bore. Route each lead up the diagonal gap beside its servo; nothing runs between the servo bases, where the bypass tube passes with 0.25 mm clearance.
3. Spine deck onto its corbels (3 x M2), servo leads up through the four diagonal slots.
4. Spine, on the bench before it goes in (drawing W4): BNO085 (low) on the +X standoffs; the Pico 2 W (leads soldered in, USB down) on the +X standoffs above it; BME688 (low) and BMP388 (middle, ADDR jumper closed) on the -Y 9 mm pillars and the 4682 microSD (top, card in, a strip of Kapton over the card) on the -Y 7 mm pillars, the power perfboard on the +Y pillars, battery taped and strapped low on -X (3-60 mm up the spine). Leave the 2810's three leads (VIN, VOUT, GND) long enough to reach the wall cradle. Then lower the spine onto the deck socket so the spider centres it.
4b. Pololu 2810 into its cradle on the control-tube wall at +Y, component side out, so the slide knob shows through the 4 x 12 mm slot. A dab of hot glue on two edges. Check with a toothpick through the slot that the slide moves the full stroke and turns the system on and off (W1).
5. Arm button and LED into the -Y wall cradle from the bore side: switch plunger out through the 4 mm hole, LED dome into the 3.2 mm hole, a dab of hot glue on each. Press the plunger with a pen tip through the hole to check it clicks; leave the four leads long enough to reach Pico GP14, GP15 and GND. The microSD card must be reachable once the spine is out: check it slides out of the 4682 before closing up.
6. Control tube onto the motor-bay shoulder, 3 x M3.
7. RB-floor coupler bonded into the recovery-bay aft end. Tie the aramid shock cord through the printed anchor arch (bowline, then a dab of CA on the tail). RB onto the control tube, 3 x M3.
8. Bypass tube (printed PC-FR, 9.5 x 7.5 mm): a bead of high-temp RTV in the plenum socket, then push it down the axis through the RB floor, spine and deck until it seats. RTV the RB-floor socket too. Let it cure before the ejection test.
9. Fins onto the hubs, M2 cross-pins.

## 3. Bench checks

| Check | Pass |
|---|---|
| t1 I2C scan | Wire: 0x4A. Wire1: 0x77 (BMP388). Wire2: 0x77 (BME688). Nothing else; the two pressures agree within a few Pa |
| Servo calibration (t2) | trim each fin with the printed `15_fin_zero_jig` (it slides on and off without moving the fin); µs per degree for each servo from the tunnel cradle's AS5600 (`a±10` vs measured), into `fc_config.h` |
| SIGN CHECK (critical) | flight firmware, ARMed, `WYV_RAIL_CLEAR_MS` temporarily 0 and the launch threshold lowered on a bench build. Tilt the rocket nose toward +Y by hand: both A fins must move so their force points toward +Y (the trailing edges swing toward -Y). Repeat for +X with the B fins. All four fins sit at the same station, so both pairs should respond with the same amplitude. Any fin that goes the wrong way: flip its `WYV_SERVO_SIGN`. A wrong sign here is the single most likely way to lose the vehicle |
| Arming | button held 2 s → LED solid; released and left still 1 s → two blinks (ARMED). Shaking it during that second → fast flicker (refused). Hold 2 s again → disarmed. `wyvern_host.py --port` shows the state change |
| SD soak (t3) | 30 min at 100 Hz with the flight card: 0 dropped records, worst loop time under 2 ms |
| Manoeuvre dry run | the SIGN CHECK bench build with `WYV_MAN_QBAR_MIN` and `WYV_MAN_ALT_MIN_M` also set to 0: 1.72 s after the fake launch the fins show the A doublet, the B doublet, then the two 1° steps, in that order and sense. Restore all three values before flight |
| Battery | 25 min pad soak at room temperature, then check the pack voltage. Expect about 59 mAh drawn |

## 4. CG and margin check

Weigh the finished vehicle with a spent F42 casing plus 27 g of dummy mass in the bay. Balance it on a knife edge and compare with CG 338 mm. Adjust the nose ballast until the measured CG is within ±5 mm, then update `BALLAST_G` and the COTS masses in `wf_core.py` and re-run the cascade. The flight must show margin ≥ 0.9 cal (with interference) at liftoff.

## 5. Static burn

Dropped in rev 3e (no motor test stand). The motor is a certified single-use F42-4T, so its thrust curve is the thrustcurve.org data the sims use. The retainer and plenum get checked against the ejection kick-out in the ground test below, with a spent F42 casing in the bay (model kick-out about 0.93 kN at 0.3 g, 1.61 kN at 0.5 g).

## 6. Ground ejection test

Full stack, packed as for flight. Charge: 0.30 g FFFFg BP in an e-match cup taped into the plenum gallery, fired remotely.
- Pass: the nose separates cleanly and the chute is pulled out.
- The nose now holds by friction on its shoulder (no shear pins). If it fails to separate, sand or slim the shoulder and retest; if it slides off on the pad or under handling, add a turn of tape. Then repeat at 0.70 g to check that nothing else moves (bypass, RB floor, joints).

## 7. Pad and range procedure

1. Install the motor and retainer (4 x M3). Igniter is not installed yet.
2. Flip the 2810 slide on through the wall slot (toothpick) → the wall LED is solid during self-test, then blinks once every 2 s (PAD). On the bench beforehand, `wyvern_host.py --port` over USB confirms battery ≥ 7.8 V and all three sensors; unplug USB before going to the pad.
3. Rocket on the rail (printed 1010 buttons at az 22.5).
4. Hold the arm button 2 s with a pen tip (LED solid), let go and step back from the rail for a second → two blinks every 2 s (ARMED; pad attitude zeroed, pad air captured). A fast flicker means refused: check the battery and that the rail is within 20° of vertical, then try again.
5. Igniter in, RSO check, launch. You have about 2 h 20 min of battery for holds.
6. Recovery: no radio and no audible beacon in rev 4. Watch the chute down and walk the simulator's drift line (about 20 m at apogee in a 4 m/s wind); the LED blinks 1 Hz once it has landed.
7. Slide the 2810 off through the slot. Pull the SD card and run `wyvern_host.py --decode WYFxxx.BIN`.
