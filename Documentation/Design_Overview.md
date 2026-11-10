# GTR70E WYVERN — fin-control revision, design overview (rev 4b)

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
| Overall length | 693 mm (nose 150, recovery bay 250, control tube 174, motor bay 119) |
| Liftoff / burnout mass | 784.6 g / 757.6 g (AeroTech Econojet F42-4T) |
| CG / CP (liftoff) | 338 / 422 mm from the nose tip |
| Static margin | 1.44 cal at liftoff, 1.63 at burnout, with the control-fin vortex on the stabilizers counted |
| Control arm (CG to hinge) | 196 mm (rev 4: 191 mm; rev 3f: 188 mm; rev 3e: 175 mm; rev 3d: 169 mm; rev 3c: 112 mm) |
| Pitch inertia | 0.0501 kg·m² |
| Motor | AeroTech Econojet F42-4T single-use, 29 x 83 mm, 52.9 N·s, 27 g propellant, 1.47 s burn |
| T/W | 4.7 avg, 8.5 peak |
| Rail exit | 15.0 m/s (Estes Pro Series II, 6 ft, printed 1010 buttons) |
| Max dynamic pressure | 1.8 kPa |
| Apogee | 176 m (577 ft) at 6.3 s, under the 600 ft cap with 23 ft to spare; ideal delay 4.9 s, the 4 s delay deploys about 0.9 s before apogee |
| Gust case | 0.6° RMS tilt with the fins working, 10.8° with them locked |
| Classification | F42 is an F-class model rocket motor (27 g propellant, 42 N average): no certification needed. Vehicle under 1,500 g |

## 1g. What changed in rev 4b: back to a Pico, Adafruit microSD

| | rev 4 | rev 4b | why |
|---|---|---|---|
| Flight computer | Teensy 4.1, 600 MHz | Raspberry Pi Pico 2 W (RP2350, 150 MHz), radio never started, single loop on core 0 | Sky's call: the arduino-pico core the project grew up on; 30 mA instead of 100 mA |
| Log | Teensy's built-in SDIO socket | Adafruit 4682 microSD on SPI0, top of the -Y face | the Pico has no card socket; same pre-allocated file + ring buffer |
| I2C | three buses, one sensor each | BNO085 alone on I2C0; BMP388 (0x76, jumper closed) + BME688 (0x77) on I2C1 | the RP2350 has two I2C blocks |
| Mounting | printed saddle and ties (the Teensy has no holes) | 2 mm standoffs on the Pico's four holes | simpler |
| Battery | 14-71 mm up -X | 3-60 mm | the 4682 at 62-87 mm on -Y touched it in the fit check |
| Power | 127 mA pad, 59 mAh mission, 4.2x | 73 mA pad, 35 mAh mission, 6.9x | lower draw |
| Vehicle | 784.5 g, 1.36 / 1.55 cal, 239 g ballast | 784.6 g, 1.44 / 1.63 cal, apogee 176 m, 253 g ballast | the Nomex blanket (14 g, mid-bay) is gone; its mass moved into the nose so liftoff mass and apogee hold, and the CG moves 5 mm forward |
| Tunnel fin angle | commanded only | measured by an AS5600 on a printed 2:1 gear train off the tunnel hub | the servo's gear backlash and wind-up under hinge load no longer end up in the $C_N$ slope |

Fit check: 0 faults. Every sketch compiles for "Raspberry Pi Pico 2W".

## 1f. What changed in rev 4: Teensy 4.1 avionics, no radio, button arming

| | rev 3f | rev 4 | why |
|---|---|---|---|
| Flight computer | Feather RP2040 RFM95, dual core | Teensy 4.1, single loop at 600 MHz | simpler code (no cross-core hand-off), SDIO microSD on the board, $31.50 |
| Telemetry | LoRa downlink 20 Hz + pad uplink, second Feather as ground station | none; USB CSV at 10 Hz on the bench / pad only | the card already holds every number the research question needs; drops one board, one antenna and the Part 15 question |
| Arming | ARM over the uplink | pushbutton through the -Y wall: hold 2 s, let go, 1 s hands-off, IMU zeroes, ARMED; LED next to it | no radio left to arm with |
| Log | Adafruit 254 breakout on SPI, -Y face | the Teensy's built-in socket, pre-allocated file, RAM ring buffer | faster bus, no stall on slow-card housekeeping, frees the -Y slot |
| Altimeter | BME688 only | BMP388 (primary, 50 Hz) + BME688 (temperature / humidity for measured air density) | lower-noise pressure; q̄ uses measured density instead of ISA |
| Boost axial channel | ADXL375 ±200 g above 7 g | BNO085, with the F42T thrust-curve model while it sits at its 8 g clip (~0.2 s) | the clip only lasts ~0.2 s on the F42-4T; uncorrected it costs ~1 m/s, the model removes that bias |
| Ballast | 233 g | 239 g | the avionics came out 6 g lighter; liftoff mass and apogee stay where they were. Margin rises to 1.36 cal |
| Power | 75 mA pad, 37 mAh mission, 6.6x | 127 mA pad, 59 mAh mission, 4.2x | the Teensy draws ~100 mA at 600 MHz; the 450 mAh pack still holds 2.3 h on the pad |
| Flight electronics to buy | $356.63 | $320.18 (rev 4 BOM later merged into one full materials sheet with nothing owned: Rocket $1,067.04 incl. filament, consumables, tools and $222.56 of launch gear) | three Feathers and the ADXL375 out, two Teensys, a BMP388, a button and LEDs in |

The fit check passes with the Teensy, its card, the saddle and the button cradle modelled (0 faults). The trade is that nothing is seen live: if the rocket lands out of sight, it is found by the drift prediction and by eye. Full details in `Electronics_Telemetry.md`.

## 1e. What changed in rev 3f: cheaper servos, 5 V servo rail, tunnel drive

| | rev 3e | rev 3f | why |
|---|---|---|---|
| Servos | 5 x KST X08 Plus, $45 each (Aloft) | 2 x 4-packs EMAX ES9251 II, $28.60 each (Amazon): 4 flight, 1 tunnel, 3 spares | $225 -> $57. Same 7.9-8 mm thickness and 16.8 mm height, so the ring, bore and 58 mm OD do not move; 18 mm long instead of 23.5, so the control tube is 5 mm shorter (174 mm) |
| Servo torque | 5.3 kg·cm | 0.27 kg·cm at 4.8 V | worst-case hinge moment (H45, 15° at max q) is 0.14 kg·cm, about half the stall torque; the simulated flight peak is about 0.02 kg·cm |
| Servo power | straight off 2S | second Adafruit MPM3610, 5.0 V, on the same perfboard | the ES9251 II is a 4.5-6.0 V servo; the logic keeps its own buck |
| Ballast | 214 g | 233 g | the servos took out 20 g; without it apogee rose to 184 m (604 ft), over the cap. Margin rises to 1.30 cal |
| Hub | round-horn pocket, 2 x M2 | single-arm horn pocket, centre screw + one self-tapper | the ES9251 II ships with small arm horns (VERIFY sizes with calipers) |
| Tunnel | 8 in AC fan, Pico 2 W, KST on a 2S pack | 6 in EC fan, Metro M4, ES9251 II on a 5 V wall supply | see `Wind_Tunnel_Adaptation.md` |

Plastic gears are the main cost: a hard landing can strip one, which is why the order carries three spares. The ES9251 II's mounting-tab span, tab thickness, shaft position and horn are not on any spec page found; the CAD uses estimates from the published 21.9 mm hole spacing and 10.15 mm tab height, tagged VERIFY in `wf_core.SERVO`. Caliper one before printing the control tube.

## 1d. What changed in rev 3e: printed recovery path, fewer bought parts, servo trade

| | rev 3d | rev 3e | why |
|---|---|---|---|
| Bypass tube | 3/8 in x 0.035 in 6061 Al (7.75 mm ID), AS568-012 O-rings | printed PC-FR, 9.5 mm OD x 7.5 mm ID (1.0 mm wall), high-temp RTV bead at each socket | your call: the ejection path is printed. 7.5 mm keeps the 0.3 g kick-out within 5 % of the Al tube (`wf_bypass.py`); a 6.5 mm bore would raise it 20 % |
| Shock-cord anchor | M5 eyebolt, quick links, swivel | printed arch on the RB-floor coupler; the cord is tied to it and to the chute / nose bar | your call: no metal recovery hardware |
| Nose retention | two #2-56 nylon shear pins | friction fit on the 35 mm shoulder | the shear pins went with the recovery hardware; the ground ejection test sets the fit (tape on the shoulder) |
| Rail buttons | Estes 1010 Delrin + printed spacers | one printed PETG-CF part each (saddle, 6.0 mm neck, 11.1 mm head), M4 screw | your call |
| Power switch access | screw switch on the 2810's CTRL line, 3 mm wall hole | the 2810 sits in a printed wall cradle, its slide under a 4 x 12 mm slot; the slide moves around the airframe | one less bought part; the slide travel is at right angles to boost and ejection loads |
| Pad beacon | piezo + 2N3904 on GP12 | onboard red LED (GP13) blinks the state | your call |
| microSD | Adafruit 4682 (to buy) | the owned Adafruit 254 on a 14 mm board plane; outline and holes from Adafruit's Eagle file | already owned. The -Y face grew 6 mm (spine 94 mm, control tube 179 mm) |
| Ground antenna | SMA pigtail + Linx whip | 78 mm wire on the ground Feather's ANT pad, same as the flight board | about 52 dB of margin either way |
| Motor test stand | F42 thrust check on the static stand | dropped | your call; the F42-4T curve is the thrustcurve.org .eng file |
| Liftoff mass | 806.7 g | 784.0 g | |
| Apogee | 549 ft | 578 ft | lighter, still under the 600 ft cap |

Servo trade (not adopted). A 20 kg low-profile servo (SPT4420LV, 40 x 19 x 27 mm, 4.8-6.0 V) was sized properly before the decision: it sets a 97 mm body, 1.43 kg at liftoff, 81 x 90 mm stabilizers, 250 g of ballast and a G74 motor to reach 1.0 cal, and it still leaves the 6 ft rail at 12.7 m/s with about half of rev 3d's control authority (peak b 26 against 54.6, integrated 46 against 117.5). It also needs a 6 V regulator and a bigger chute, which erases most of the servo savings. The owned EMAX ES08MA II (11.5 x 24 mm) would fit a 78.5 mm body at about 1.0 kg; on a G74 it beats rev 3d's authority but flies to about 730 ft, and on an F67-6W it stays under 600 ft with peak b about 45. The KST X08 Plus at 58 mm stays.

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
| 0 – 4.75 | printed PC-FR bypass tube, 7.5 mm bore (0.25 mm clear of the servo bases) |
| 5.0 | inner end of each EMAX ES9251 II |
| 16.35 | mounting tabs bear on the wall pad (tab underside 10.15 mm above the case bottom) |
| 21.8 | servo output face |
| 24.8 | spline tip; the horn sits in a pocket in the hub flange |
| 24.8 – 26.4 | hub flange, 13 mm diameter, 1.6 mm thick |
| 27.4 | bore (flange corners clear it by 0.2 mm) |
| 29.0 | outer wall, 1.6 mm |

The fit check caught one thing the old layout also had wrong: a 14 mm flange 2 mm thick pokes its corners into the bore wall, because the bore is curved and the flange is flat. The 13 mm x 1.6 mm flange with 1.0 mm between spline tip and bore clears it.

The servo leads cannot run up the middle anymore, because the tube fills it. They run up the four diagonal gaps between servos and through the spine deck's diagonal slots.

## 3. Sections

1. Nose cone, 150 mm tangent ogive, ASA-Aero, 35 mm shoulder. 253 g of steel BBs in epoxy fills the tip cavity (rev 3f added 19 g for the lighter servos, rev 4 another 6 g for the lighter avionics and rev 4b 14 g for the dropped Nomex, all to keep apogee under 600 ft). Steel shot or BBs need about 45 cc and fill to about 82 mm from the tip; steel nuts and washers about 56 cc, to 89 mm; lead fishing weights about 32 cc, to 72 mm. The model places the ballast at 30 mm, so weigh and balance the finished nose (Build_and_Test §3) and re-run the cascade with the real centroid. Friction fit on the shoulder (rev 3e: no shear pins); set it on the ground ejection test.
2. Recovery bay, 250 mm. The packed 24 in chute (assumed 46 x 95 mm, measure it) sits under the nose shoulder (rev 4b: no Nomex wrap); the shock cord bundle sits on the RB floor. The RB-floor coupler (PC-FR) carries the 3 mm gas-tight floor, the central bypass socket (slip fit + high-temp RTV) and a printed cord-anchor arch 15 mm off-axis; the aramid cord is tied through it.
3. Control tube, 174 mm. Servo ring at the bottom, spine deck, avionics spine, and the Pololu 2810 cradle on the wall at +Y under its slide slot.
4. Motor bay, 119 mm: plenum bulkhead with a 10 mm full-bore gas gallery, motor mount, four stabilizers bonded to the MMT through the wall, retainer collar (now slotted so it slides over the stabilizer roots; the fit check found the collar and stabilizers overlapping).
5. Bypass tube, printed PC-FR, 9.5 x 7.5 mm, 205 mm, dropped down the axis last.

Every printed part fits a 256 x 256 x 256 mm bed; the longest is the 250 mm recovery-bay tube, printed upright.

## 4. Avionics spine

A square PETG-CF sleeve, 14 mm across flats and 94 mm tall, slides over the bypass tube. Boards sit on all four faces (drawing `Flight Computer/wiring/W4_spine_perfboard.png`; positions in `wf_core.SPINE_BOARDS`):

| face | boards (bottom to top) | mounting |
|---|---|---|
| +X | BNO085 (Adafruit 4754, 25.4 x 22.9), Raspberry Pi Pico 2 W (51 x 21, rev 4b) | 2 mm standoffs, board plane 9 mm off-axis |
| -X | 2S 450 mAh LiPo (57 x 30 x 14), 3-60 mm up the spine (rev 4b: 11 mm lower, so the 4682 clears it) | foam tape on the face, two straps |
| +Y | 16 x 62 mm power perfboard: two Adafruit MPM3610 5 V bucks (logic rail and, rev 3f, servo rail; EN unconnected = on); 470 µF on the servo rail and the divider underneath. Above it, the Pololu 2810 in its wall cradle (slide under the wall slot) | 9 mm pillars, board plane 16 mm off-axis |
| -Y | BME688 (Adafruit 5046), BMP388 (Adafruit 3966, 25.4 x 17.8), microSD (Adafruit 4682, 25.4 x 22.9, rev 4b). Beside the 4682, the arm button and LED in their wall cradle | 9 mm pillars (7 mm for the 4682 on its 14 mm plane), one line of screws each |

The ±Y boards stand on pillars so they clear the 30 mm wide battery and the +X boards. The pillars themselves have to fit between those two, which is why the -Y boards use one line of holes each, offset sideways. Board sizes and hole grids were read from the vendor STEP files, not assumed.

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

Rev 4b values (H45 fins, 81 x 20 mm stabilizers, 253 g ballast, ES9251 II servos, Pico 2 W avionics, printed recovery path), from `plots_flight/flight_summary.json`:

| | Econojet F42-4T (chosen) | F67-6W | G74-6W |
|---|---|---|---|
| Impulse | 52.9 N·s | 61.1 N·s | 82.8 N·s |
| Average thrust / burn | 42 N / 1.47 s | 69 N / 0.92 s | 74 N / 1.19 s |
| Rail exit | 15.0 m/s | 17.9 m/s | 17.2 m/s |
| Apogee | 176 m (577 ft) | 232 m (761 ft), over the cap | 370 m (1214 ft), over the cap |
| Gust case RMS tilt, fins active / locked | 0.6° / 10.8° | 0.7° / 7.8° | 0.8° / 7.3° |
| Delay | 4 s against a 4.9 s ideal: chute 0.9 s before apogee | 6 s | |
| 4 motors | $98.98 ($49.49 per 2-pack at eRockets; New Century's $43.99 was sold out) | $98.98 | $129.98 (G74-4W, $64.99 per 2-pack at AeroTech; ships only with proof of age 18+) |

All three fit the 29 x 83 mm bay. The F67-9C that used to sit in this table does not: its case is 112 mm long (its own .eng header and thrustcurve.org agree), so it was dropped.

Cheaper motors were checked and ruled out:
- Estes F15 and E16 ($32-34) are 114 mm long, too long for the bay, and their 14-16 N average thrust would leave the rail at under 10 m/s.
- AeroTech F27R and F20W fit the bay and cost the same as the F67. Their 2.0-2.5 s burns would stretch the flight, but on a 6 ft rail they leave at only 11-12 m/s.

### Would the F27R-4, F20W-4 or F20W-7 do better? No.

`Simulations/wf_motor_study.py` flies all four on the rev 3e airframe off 6, 8 and 10 ft rails (plot `plots_flight/D_motor_study.png`):

| 6 ft rail | F42-4T | F27R-4 | F20W-4 | F20W-7 |
|---|---|---|---|---|
| Burn | 1.47 s | 2.03 s | 2.49 s | 2.49 s |
| Rail exit | 15.0 m/s | 10.7 m/s | 11.2 m/s | 11.2 m/s |
| Rail exit on a 10 ft rail | 19.5 m/s | 14.3 m/s | 14.6 m/s | 14.6 m/s |
| Apogee | 578 ft | 467 ft | 506 ft | 506 ft |
| Time with the fins flying it | 5.61 s | 5.27 s | 5.53 s | 5.53 s |
| ...of which under thrust | 1.24 s | 2.08 s | 2.16 s | 2.16 s |
| Peak control acceleration | 60.0 | 37.6 (−37 %) | 38.9 (−35 %) | 38.9 |
| Integrated authority | 131.1 | 86.9 (−34 %) | 98.0 (−25 %) | 98.0 |
| Gust RMS tilt, fins active / locked | 0.46° / 10.3° | 0.34° / 17.2° | 0.34° / 16.9° | 0.34° / 16.9° |
| Authority manoeuvre | runs (doublet at 1.3 kPa) | skipped: q̄ never reaches the gate in coast | marginal (doublet at 0.75 kPa) | marginal |
| Ejection | 0.9 s before apogee, still climbing at 8.6 m/s | 0.3 s after apogee | 0.1 s after apogee | 3.1 s after apogee, falling fast: zipper or strip risk |
| 4 motors | $98.98 | $98.98 | $98.98 | $98.98 |

The slow motors do keep the fins working under thrust for longer, about 2.1 s against 1.2 s. They lose on everything else:
- The total controlled time is shorter, because they climb more slowly and stop lower.
- The peak and integrated authority drop by a quarter to a third.
- The passive (fins-locked) flight is much worse.
- They leave the 6 ft rail at 10.6–11 m/s, and even a 10 ft rail only gets them to about 14 m/s.
- They cost the same, so there is no saving to offset any of that.

The F20W-7's long delay would also pop the chute late. The quieter fins-active tilt (0.32°) just reflects the lower airspeed: there is less weathercocking to fight, and less authority to fight it with.

Buy the 4 s delay version (F42-4T). The F42 is mailable as a model rocket motor; check the vendor's age policy.

## 7. Ejection path

The motor's charge vents into the 10 mm gallery under the plenum, runs 205 mm up the printed PC-FR tube (7.5 mm bore) and pressurises the recovery bay. With the smaller bay (274 cm³ free volume) the same charge gives higher pressure:

| BP charge | plenum peak | bay peak | force on the nose | motor kick-out |
|---|---|---|---|---|
| 0.3 g | 1.41 MPa | 177 kPa | 418 N | 932 N |
| 0.5 g | 2.44 MPa | 336 kPa | 793 N | 1.61 kN |

The model's 235 N release force assumed two nylon shear pins; with the rev 3e friction-fit nose the real figure is whatever the shoulder fit gives, so the ground test sets it (0.3 g pushes with 418 N). The printed tube's 7.5 mm bore keeps the kick-out within 4 % of the old aluminium tube's; a 6.5 mm bore would have pushed it to 1.10 kN at 0.3 g. Hoop stress in the 1.0 mm PC-FR wall is about 5 MPa at the 0.3 g plenum peak. AeroTech does not publish the F42's ejection charge, so ground-test the stack first (Build_and_Test §6).

## 8. Mass

| | mass (g) |
|---|---|
| Printed parts (with the four H45 fins) | 288 |
| Ballast | 233 |
| Avionics, battery, servos, harness, recovery soft goods, printed bypass tube, hardware | ~187 |
| Motor (F42-4T) | 76 |
| Liftoff | 784.0 |

## 9. Before the first print

- Measure a real ES9251 II (tab span and thickness, hole pitch, shaft position, horn) and the owned LiPo; both are datasheet-built in the fit check.
- Fit a printed 1010 rail button on the real rail before printing the pair: the 6.0 mm neck has to slide freely and the 11.1 mm head must not pull through.
- The 254 microSD holes and outline come from Adafruit's Eagle file; the Pololu 2810 cradle from Pololu's STEP. Dry-fit both in the printed spine and control tube.
- Measure the packed chute; the 46 x 95 mm bundle is an assumption.
- Print the control tube first and fit the servos, then the spine with the real boards, before anything else.
