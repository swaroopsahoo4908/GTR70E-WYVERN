# GTR70E WYVERN — fin-control revision, design overview (rev 3d)

_Every number here comes from `Simulations/canonical_numbers.json`, `Documentation/CANONICAL_NUMBERS.md` and the sim outputs they point to. If geometry or mass changes, re-run the cascade in the root README instead of editing numbers in this file. The fit check with vendor models is `3D parts/assembly/FIT_REPORT.md` and drawing `diagrams/D6_fit_check.png`._

## 1. What changed in rev 3

| | rev 2 | rev 3 | why |
|---|---|---|---|
| Servo bases from the axis | 11.2 mm | 5.0 mm | your call: pull the servos in and let the tube shrink around them |
| Airframe OD | 70 mm | 58 mm | derived from the servo ring (below) |
| Bypass tube | 1/2 in x 0.035 Al | 3/8 in x 0.035 Al (7.75 mm ID) | the largest tube that passes between servo bases 10 mm apart |
| Motor | AeroTech G40-7W, $176 for 4 | AeroTech F67-6W, $98.98 for 4 | no certification, under $100 |
| Liftoff mass | 973 g | 723 g | 26 % lighter |
| Length | 792 mm | 688 mm | shorter motor and recovery bay |
| Recovery bay | 330 mm | 250 mm | a 290 mm tube does not fit a 256 mm printer (caught by the fit check) |
| Ballast | 180 g | 110 g | |
| Stabilizers | 120 x 50 mm | 81 x 40 mm | run the length of the 83 mm motor; span equal to the 40 mm control fins (rev 3b, §5) |
| IMU | deck above the servos | lowest board on the spine (+X) | a 25.4 x 22.9 mm BNO085 (vendor model) does not fit beside the tube in a 54.8 mm bore |

| | value |
|---|---|
| Configuration | single stage, 58 mm OD, four printed sections, nose-only separation |
| Overall length | 692 mm (nose 150, recovery bay 250, control tube 173, motor bay 119) |
| Liftoff / burnout mass | 806.7 g / 779.7 g (AeroTech Econojet F42-4T) |
| CG / CP (liftoff) | 360 / 418 mm from the nose tip |
| Static margin | 1.01 cal at liftoff, 1.18 at burnout, with the control-fin vortex on the stabilizers counted |
| Control arm (CG to fin CP) | 169 mm (rev 3c: 112 mm) |
| Pitch inertia | 0.047 kg·m² |
| Motor | AeroTech Econojet F42-4T single-use, 29 x 83 mm, 52.9 N·s, 27 g propellant, 1.47 s burn |
| T/W | 4.6 avg, 8.2 peak |
| Rail exit | 14.8 m/s (Estes Pro Series II, 6 ft) |
| Max dynamic pressure | 1.7 kPa |
| Apogee | 167 m (549 ft) at 6.2 s, under the 600 ft cap with 51 ft to spare; ideal delay 4.7 s, the 4 s delay deploys about 0.7 s before apogee |
| Gust case | 0.44° RMS tilt with the fins working, 10.4° with them locked |
| Classification | F42 is an F-class model rocket motor (27 g propellant, 42 N average): no certification needed. Vehicle under 1,500 g |

## 1c. What changed in rev 3d: 600 ft cap, cheaper motor, no GPS

| | rev 3c | rev 3d | why |
|---|---|---|---|
| Motor | F67-6W, $98.98 for 4 | Econojet F42-4T, $87.98 for 4 | cheapest motor that fits the 83 mm bay; lower impulse helps the cap |
| Apogee | 833 ft | 549 ft | your 600 ft cap |
| Nose ballast | 110 g | 214 g | lowers apogee and moves the CG 57 mm forward, which lengthens the control arm from 112 to 169 mm |
| Stabilizers | 81 x 40 mm | 81 x 20 mm | in the model, the control-fin vortices push back on the stabilizers; halving their span cuts that, and the ballast restores the margin they gave |
| Flight control fins | H40 | H45 (top of the H sweep) | more fin area for the lower dynamic pressure |
| End of active control | climb rate < 15 m/s (~1.5 s before apogee) | q̄ < 15 Pa (~0.7 s before apogee) | more of the ascent under control |
| GPS | PA1010D on the spine | removed | your call; the ADXL375 takes its -Y slot and the LiPo goes back to the middle of -X |

What happened to control authority, flight time and cost (`Simulations/wf_apogee_cap_trade.py`, plot `plots_flight/C_apogee_cap_trade.png`):

| | rev 3c (F67-6W) | rev 3d (F42-4T) | change |
|---|---|---|---|
| Control derivative per unit q, M_δ/(I q̄) | 0.0151 | 0.0315 | ×2.1 |
| Peak control acceleration, M_δ/I at the highest q̄ under control | 54.4 1/s² per rad | 54.6 | +0.4 % |
| Authority integrated over the controlled flight | 117.5 1/s per rad | 117.5 | 0 % |
| Trim angle per degree of fin (C_mδ / C_mα) | 0.36 | about 1.2 | ×3.4 |
| Gust case RMS tilt, fins active | 2.18° | 0.44° | 5× steadier |
| Time with the fins flying the rocket | 5.55 s (old rule) | 5.47 s | −1 % |
| ...of which under thrust | 0.73 s | 1.24 s | +70 % |
| Share of the ascent under control | 77 % | 88 % | |
| Apogee | 842 ft | 549 ft | |
| 4 motors | $98.98 | $87.98 | −$11 |

Both authority totals were held at the rev 3c values on purpose: the ballast (214 g) was set as the lightest that keeps the integrated authority and the peak acceleration at or above rev 3c with the margin at 1.0 cal. Per unit dynamic pressure the airframe now has twice the authority, which is what lets it hold the same absolute authority at 40 % less q̄.

The one thing the cap does not allow is a longer flight. A 600 ft ascent lasts about 6.2 s, against 7.2 s for the old 833 ft flight, so the total controlled time stays at about 5.5 s even though control now runs closer to apogee and the powered, highest-authority part grew by 70 %. Stretching the flight at the same apogee would need a slower, longer-burning motor (F27R or F20W, 2.0 to 2.5 s burns), and those leave a 6 ft rail at only 11 to 12 m/s. With an 8 to 10 ft rail they become an option.

Two other things to watch. Rail exit drops to 14.8 m/s, just under the usual 15 m/s rule of thumb; the stabilizers and the fins (armed at rail exit) handle it in the sim, but a longer rail would help. And the margin with the fins locked is still 1.01 cal, so a passive flight (fins disarmed or the authority monitor tripping) stays stable, at 10° RMS tilt in the gust case instead of 7.7°.

## 1b. What changed in rev 3c

| | rev 3b | rev 3c | why |
|---|---|---|---|
| Logging | microSD 100 Hz + LittleFS on the QSPI flash 50 Hz | microSD only (96 B records) | your call; the 20 Hz downlink is the second record |
| Ground station | Pico 2 W + RFM95W breakout, WiFi dashboard | second Feather RP2040 RFM95, laptop over USB | one radio build at both ends |
| Boost acceleration | BNO085 only (clips at 8 g) | + ADXL375 ±200 g for the axial channel | the F67-6W holds 11-12 g for 0.65 s; q̄ would read ~20 m/s low at burnout |
| I2C | one bus shared by both cores | one bus per core | the old layout was a cross-core race |
| Spine | 84 mm | 88 mm | room for the ADXL375 on -Y |
| Control code | coast doublets ±3° | authority manoeuvre: ±5° doublets then 1° attitude steps, results downlinked and on the card | a measurable authority demonstration |
| Length | 688 mm | 692 mm | |

The fit check with the vendor ADXL375 model in place shows no interference.

## 2. The servo ring sets the diameter

Everything radial is derived from one number in `wf_core.py`, `SERVO_BASE_R = 5.0`:

| radius (mm) | what sits there |
|---|---|
| 0 – 4.76 | 3/8 in aluminium bypass tube (0.24 mm clear of the servo bases) |
| 5.0 | inner end of each KST X08 Plus |
| 17.8 | ears bear on the wall pad |
| 21.8 | servo output face |
| 24.8 | spline tip; the horn sits in a pocket in the hub flange |
| 24.8 – 26.4 | hub flange, 13 mm diameter, 1.6 mm thick |
| 27.4 | bore (flange corners clear it by 0.2 mm) |
| 29.0 | outer wall, 1.6 mm |

The fit check caught one thing the old layout also had wrong: a 14 mm flange 2 mm thick pokes its corners into the bore wall, because the bore is curved and the flange is flat. The 13 mm x 1.6 mm flange with 1.0 mm between spline tip and bore clears it.

The servo leads cannot run up the middle anymore, because the tube fills it. They run up the four diagonal gaps between servos and through the spine deck's diagonal slots.

## 3. Sections

1. Nose cone, 150 mm tangent ogive, ASA-Aero, 35 mm shoulder. 214 g of steel shot in epoxy fills the first 60 mm of the tip cavity. Two #2-56 nylon shear pins.
2. Recovery bay, 250 mm. The packed 24 in chute (assumed 46 x 95 mm, measure it) and the Nomex wrap sit under the nose shoulder; the shock cord bundle sits on the RB floor. The RB-floor coupler (PC-FR) carries the 3 mm gas-tight floor, the central bypass socket with an AS568-012 O-ring, and an M5 eyebolt 20 mm off-axis with its eye turned tangentially so it clears the bore.
3. Control tube, 173 mm. Servo ring at the bottom, spine deck, avionics spine.
4. Motor bay, 119 mm: plenum bulkhead with a 10 mm full-bore gas gallery, motor mount, four stabilizers bonded to the MMT through the wall, retainer collar (now slotted so it slides over the stabilizer roots; the fit check found the collar and stabilizers overlapping).
5. Bypass tube, 3/8 in x 0.035 in 6061, 195 mm, dropped down the axis last.

Every printed part fits a 256 x 256 x 256 mm bed; the longest is the 250 mm recovery-bay tube, printed upright.

## 4. Avionics spine

A square PETG-CF sleeve, 14 mm across flats and 88 mm tall, slides over the bypass tube. Boards sit on all four faces (drawing `Flight Computer/wiring/W4_spine_perfboard.png`; positions in `wf_core.SPINE_BOARDS`):

| face | boards (bottom to top) | mounting |
|---|---|---|
| +X | BNO085 (Adafruit 4754, 25.4 x 22.9), Feather RP2040 RFM95 (50.8 x 22.9) | 2 mm standoffs, board plane 9 mm off-axis |
| -X | 2S 450 mAh LiPo (57 x 30 x 14) | foam tape on the face, two straps |
| +Y | 16 x 62 mm power perfboard: Pololu D24V10F5, screw switch, Pololu 2810, piezo; 470 µF, divider and 2N3904 underneath | 9 mm pillars, board plane 16 mm off-axis |
| -Y | BME688 (Adafruit 5046), microSD (Adafruit 4682), ADXL375 (Adafruit 5374, 25.4 x 17.8) | 9 mm pillars, one line of screws each |

The ±Y boards stand on pillars so they clear the 30 mm wide battery and the 22.9 mm wide Feather. The pillars themselves have to fit between those two, which is why the -Y boards use one line of holes each, offset sideways. Board sizes and hole grids were read from the vendor STEP files, not assumed.

The BNO085 is about 10 mm off the axis, at station 533 mm. Rates do not care where it sits; the accelerometer sees about 1.6 m/s² of lateral acceleration at 2 rev/s of roll, which the firmware never uses for attitude in flight.

## 5. Stability, ballast and the stabilizers

_Rev 3d update: the flight stabilizers are now 81 x 20 mm with 214 g of ballast and H45 control fins (§1c). The rev 3b study below is kept because it is how the equal-span and offset questions were answered; its numbers are for the F67-6W, 40 mm stabilizers and H40 fins. The 45° offset conclusion still holds._

Rev 3b cuts the stabilizers to the same span as the triangular control fins (40 mm, the design height H*), as on missiles like the AIM-54 where the fixed surfaces and the control fins have about the same span. `Simulations/wf_stabilizer_planform_trade.py` weighs it (H = 40, F67-6W, gust case, pessimistic vortex model; plot `plots_stabilizer/S4_planform_trade.png`):

| stabilizers / ballast | liftoff | margin (cal) | installed Cmδ (per rad) | installed / isolated | α_trim per δ | RMS tilt active / locked | apogee |
|---|---|---|---|---|---|---|---|
| 81 x 45 mm / 90 g (rev 3) | 708 g | 1.05 | 2.71 | 0.45 | 0.25 | 3.7° / 7.8° | 263 m |
| 81 x 40 mm / 90 g | 703 g | 0.83 | 3.11 | 0.51 | 0.39 | 2.1° / 7.3° | 268 m |
| 81 x 40 mm / 110 g (chosen) | 723 g | 1.02 | 3.57 | 0.53 | 0.37 | 2.2° / 7.6° | 258 m |
| 81 x 40 mm, 22.5° offset / 110 g | 723 g | 0.90 | 2.21 | 0.33 | 0.27 | 3.4° / 7.4° | 258 m |
| 81 x 40 mm in line with the control fins (AIM-54 layout) / 110 g | 723 g | 0.55 | -1.32 | -0.20 | -0.30 | 19.8° / 6.8° | 225 m |
| 116 x 40 mm long chord, AIM-54 style / 90 g | 721 g | 0.58 | 3.22 | 0.55 | 0.58 | 1.4° / 6.9° | 257 m |
| 116 x 40 mm long chord / 150 g | 781 g | 1.11 | 4.50 | 0.59 | 0.42 | 1.8° / 8.1° | 229 m |

Matching the span does give more authority: the installed control derivative rises 32 % (2.71 → 3.57 per rad) and the trim angle the fins can command per degree rises 50 %, for 15 g more ballast and 5 m less apogee. Two things drive it. The control-fin tip vortices trail about 58 mm from the axis; a 40 mm stabilizer ends at 69 mm instead of 74 mm, so less of it sits in the strong part of the downwash and the opposing load drops (interference ratio −0.29 → −0.26). And they add less restoring moment for the fins to fight. Cutting span alone drops the margin to 0.83 cal, which is why 20 g of ballast goes back in; that also lengthens the control arm from 98 to 111 mm.

The AIM-54 also puts its fixed and moving surfaces in line, at the same azimuth. Copied here, that reverses the control: the stabilizers sit straight in the control fins' tip vortices and the induced load (−0.67 of the control force, on a longer arm) outweighs the fins themselves, so the model's gust tilt goes to 19.8°. Keep the 45° interleave. The AIM-54 gets away with it because its moving fins are at the tail: the wing wake reaches the control fins but does not push against them, and with the steering surfaces behind the CG there is no fixed surface further aft to fight them.

The long-chord AIM-54 planform was tested too. Stretching the chord along the whole 116 mm motor bay moves the stabilizer's centre of pressure forward, so margin collapses to 0.59 cal. Getting it back costs 60 g of ballast and 33 m of apogee. It controls best per degree, but the 81 mm chord at matched span is the better trade here. One difference from the AIM-54 matters: on that missile the steering fins are at the tail, behind the long wings, while here the control fins are ahead of the stabilizers, so the stabilizers sit in the control fins' wake.

The stabilizers still do the job you'd expect. With the fins locked, no stabilizers means the rocket tumbles; with these it flies at 7.6° RMS. A more stable rocket is not the same as a more vertical one, though: a stiffer airframe turns harder into a crosswind gust, so with the fins active the RMS tilt rises from 2.2° at 40 mm span to 6.8° at 50 mm. SQ1 measures both effects.

### Is the 45° offset the better choice?

Yes, on both counts you asked about. Holding the span at 40 mm and the ballast at 110 g, the three azimuths compare like this:

| offset from the control fins | margin | installed / isolated authority | RMS tilt, fins active / locked |
|---|---|---|---|
| 45° (as built) | 1.02 cal | 0.53 | 2.2° / 7.6° |
| 22.5° | 0.90 cal | 0.33 | 3.4° / 7.4° |
| 0°, in line (AIM-54) | 0.55 cal | −0.20 (reversed) | 19.8° / 6.8° |

At 45° each stabilizer sits as far as it can from both neighbouring control-fin tip vortices, so it loses the least lift to their downwash (higher margin) and feels the least opposing load when a pair deflects (more authority). With the fins locked, the in-line layout actually tilts slightly less, but only because a passive rocket with less margin weathercocks less. "More stable" in the static-margin sense and "flies straighter" are different things. With the fins working, 45° is clearly the best of the three. Phase B can check it by turning the tail section 45° (test S2).

## 6. Motor

Rev 3d values (H45 fins, 81 x 20 mm stabilizers, 214 g ballast), from `plots_flight/flight_summary.json`:

| | Econojet F42-4T (chosen) | F67-6W | G74-6W |
|---|---|---|---|
| Impulse | 52.9 N·s | 61.1 N·s | 82.8 N·s |
| Average thrust / burn | 42 N / 1.47 s | 69 N / 0.92 s | 74 N / 1.19 s |
| Rail exit | 14.8 m/s | 17.6 m/s | see flight_summary.json |
| Apogee | 167 m (549 ft) | 222 m (729 ft), over the cap | over the cap |
| Gust case RMS tilt, fins active / locked | 0.44° / 10.4° | 0.54° / 7.6° | |
| Delay | 4 s against a 4.7 s ideal: chute 0.7 s before apogee | 6 s | |
| 4 motors | $87.98 ($43.99 per 2-pack) | $98.98 | price not found |

All three fit the 29 x 83 mm bay. The F67-9C that used to sit in this table does not: its case is 112 mm long (its own .eng header and thrustcurve.org agree), so it was dropped.

Cheaper motors were checked and ruled out:
- Estes F15 and E16 ($32-34) are 114 mm long, too long for the bay, and their 14-16 N average thrust would leave the rail at under 10 m/s.
- AeroTech F27R and F20W fit the bay and cost the same as the F67. Their 2.0-2.5 s burns would stretch the flight, but on a 6 ft rail they leave at only 11-12 m/s.

### Would the F27R-4, F20W-4 or F20W-7 do better? No.

`Simulations/wf_motor_study.py` flies all four on the rev 3d airframe off 6, 8 and 10 ft rails (plot `plots_flight/D_motor_study.png`):

| 6 ft rail | F42-4T | F27R-4 | F20W-4 | F20W-7 |
|---|---|---|---|---|
| Burn | 1.47 s | 2.03 s | 2.49 s | 2.49 s |
| Rail exit | 14.8 m/s | 10.6 m/s | 11.0 m/s | 11.0 m/s |
| Rail exit on a 10 ft rail | 19.2 m/s | 14.0 m/s | 14.3 m/s | 14.3 m/s |
| Apogee | 549 ft | 441 ft | 478 ft | 478 ft |
| Time with the fins flying it | 5.47 s | 5.13 s | 5.38 s | 5.38 s |
| ...of which under thrust | 1.24 s | 2.07 s | 2.15 s | 2.15 s |
| Peak control acceleration | 54.6 | 33.9 (−38 %) | 35.1 (−36 %) | 35.1 |
| Integrated authority | 117.5 | 77.0 (−34 %) | 86.9 (−26 %) | 86.9 |
| Gust RMS tilt, fins active / locked | 0.44° / 10.4° | 0.32° / 17.7° | 0.32° / 17.2° | 0.32° / 17.2° |
| Authority manoeuvre | runs (doublet at 1.2 kPa) | skipped: q̄ never reaches the 800 Pa gate in coast | skipped | skipped |
| Ejection | 0.7 s before apogee, still climbing at 7 m/s | 0.4 s after apogee | 0.3 s after apogee | 3.3 s after apogee, falling at roughly 25–30 m/s: zipper or strip risk |
| 4 motors | $87.98 | $98.98 | $98.98 | $98.98 |

The slow motors do keep the fins working under thrust for longer, about 2.1 s against 1.2 s. They lose on everything else:
- The total controlled time is shorter, because they climb more slowly and stop lower.
- The peak and integrated authority drop by a quarter to a third.
- The passive (fins-locked) flight is much worse.
- They leave the 6 ft rail at 10.6–11 m/s, and even a 10 ft rail only gets them to about 14 m/s.
- They cost $11 more.

The F20W-7's long delay would also pop the chute late. The quieter fins-active tilt (0.32°) just reflects the lower airspeed: there is less weathercocking to fight, and less authority to fight it with.

Buy the 4 s delay version (F42-4T). The F42 is mailable as a model rocket motor; check the vendor's age policy.

## 7. Ejection path

The motor's charge vents into the 10 mm gallery under the plenum, runs 195 mm up the central tube and pressurises the recovery bay. With the smaller bay (274 cm³ free volume) the same charge gives higher pressure:

| BP charge | plenum peak | bay peak | force on the nose | motor kick-out |
|---|---|---|---|---|
| 0.3 g | 1.36 MPa | 180 kPa | 425 N | 896 N |
| 0.5 g | 2.35 MPa | 341 kPa | 804 N | 1.55 kN |

Release needs 235 N, so even 0.3 g gives 1.8x margin. The gallery grew from 6 to 10 mm because the narrower tube raises the plenum spike; at 6 mm the 0.3 g kick-out was 1.07 kN. AeroTech does not publish the F67's ejection charge, so ground-test the stack first (Build_and_Test §6).

## 8. Mass

| | mass (g) |
|---|---|
| Printed parts | 288 |
| Ballast | 214 |
| Avionics (with the ADXL375), battery, servos, harness, recovery, hardware | ~229 |
| Motor (F42-4T) | 76 |
| Liftoff | 806.7 |

## 9. Before the first print

- Measure a real X08 Plus (ears, spline, hole pitch) and the owned LiPo; both are datasheet-built in the fit check.
- Measure the packed chute; the 46 x 95 mm bundle is an assumption.
- Print the control tube first and fit the servos, then the spine with the real boards, before anything else.
