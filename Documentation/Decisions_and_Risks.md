# Decisions and risks (fin-control revision)

## Decision log

| # | Decision | Why | Where it lives |
|---|---|---|---|
| D1 | TVC retired; all TVC-only material moved to `TVC ARCHIVED/` | project re-scope to fin control | `TVC ARCHIVED/README.md` |
| D2 | Servos above the motor, all four in ONE ring at the same station, ears bolted to pads in the tube wall, shafts radial (direct drive) | all fins at the same height (rev 2); equal arms for both pairs; no linkage slop | `wf_core.SERVO`, `gen_wyvern_fin.ct_tube()` |
| D3 | KST X08 Plus (16.8 mm tall, 9 g, HV, 4.85 kg·cm at 7.4 V) with bases 5.0 mm from the axis; the airframe OD (58 mm) is derived from that | rev 3 request: smaller tube, less mass | Design_Overview §2 |
| D4 | Ejection bypass: 3/8 in x 0.035 in Al tube on the centreline (195 mm) + 10 mm full-bore gallery | the largest tube that passes between servo bases 10 mm apart; the deeper gallery keeps 0.3 g kick-out under 0.9 kN | `wf_bypass.py` |
| D5 | Motor: AeroTech Econojet F42-4T (29 x 83 mm single-use), 4 for $87.98 (rev 3d) | cheapest motor that fits the bay; no certification; with the rev 3d airframe it reaches 549 ft, under the 600 ft cap. The F67-6W still fits but overshoots (729 ft); the F67-9C does not fit (112 mm case); Estes F15 / E16 are too long and too weak | `wf_apogee_cap_trade.py`, Design_Overview §6 |
| D6 | 250 mm recovery bay + 214 g nose ballast (rev 3d; was 110 g) | the ballast sets the apogee under the cap and moves the CG forward: 169 mm control arm, 1.01 cal; 250 mm is the longest tube a 256 mm printer takes upright | Design_Overview §1c |
| D7 | Stabilizers 81 x 20 mm (rev 3d; rev 3b was 81 x 40), 45° interleaved | halving the span halves the vortex load that fights the control fins; with the extra ballast the margin stays at 1.01 cal and per-q authority doubles. 45° stays: in line reverses control | `wf_apogee_cap_trade.py`, Design_Overview §1c, §5 |
| D8 | Feather RP2040 RFM95 in flight and a second one as the ground station (rev 3c; the Pico 2 W ground station is retired) | LoRa range, single board; one radio build, one pin map, one frame header at both ends | Electronics_Telemetry §1 |
| D9 | Internal screw switch on a Pololu 2810 control line | microamp contact, no battery current through the screw | W1/W2 |
| D10 | Hinge at 45 % root chord | fin CP at 58-60 % (VLM) → self-centring if a servo fails | `vlm.py` |
| D11 | Tunnel Phase A: single-fin half-model on a reflection-plane panel in the stock 100 x 100 section | the main RQ ranks fins against each other; ~3 % blockage, higher speed, one fin per configuration | Wind_Tunnel_Adaptation §2 |
| D11b | Tunnel Phase B: full finset + removable stabilizer tail in a 200 x 200 x 750 section + Cloudline T8 | body carry-over, pair interaction and the stabilizer interference (SQ1) need the whole model | Wind_Tunnel_Adaptation §3 |
| D12 | PCA9548 (owned) goes to the tunnel balance | three NAU7802s share 0x2A | BOM "On Hand" |
| D14 | Avionics on a square spine around the bypass: Feather +X and sensors -Y on 4 mm standoffs, battery -X on rails, 16 mm power perfboard +Y | central tube owns the axis; standoffs clear the board corners | W4, `avionics_spine()` |
| D15 | One main RQ (section x height), SQ1 stabilizer impact, SQ2 sim → tunnel → flight | revision 2 request | Research_Plan |
| D16 | Full fit-check assembly with vendor STEP models (Adafruit, Pololu) and datasheet-built bought parts; interference, bore clearance, fin sweep and 256 mm print-bed checks | rev 3 request; it found five real clashes (hub flange vs bore, MMT ring vs plenum posts, retainer vs stabilizers, spine pillars vs Feather and LiPo, a 290 mm tube too long to print) | `gen_fit_assembly.py`, FIT_REPORT.md |
| D17 | BNO085 moved from the deck to the spine's +X face | the real board is 25.4 x 22.9 mm and cannot sit beside the tube in a 54.8 mm bore | Design_Overview §4 |
| D18 | Both tunnel phases kept | every printed tunnel part fits a 256 mm printer | Wind_Tunnel_Adaptation §7 |
| D19 | microSD is the only log; the LittleFS copy on the QSPI flash is gone | the 20 Hz downlink is already the second record, and it frees a core-1 write path | Electronics_Telemetry §5 |
| D20 | GPS removed (rev 3d, your call). Recovery relies on the buzzer beacon and the simulator's drift prediction | saves 6 g, about 30 mA and $66 (two PA1010D + cells) | Electronics_Telemetry §1 |
| D21 | ADXL375 ±200 g axial channel for the vertical estimate | the F67-6W holds 11 to 12 g for 0.65 s, past the BNO085's 8 g range: q̄ and the gain schedule would read about 20 m/s low at burnout | `highg.h`, Electronics_Telemetry §5 |
| D22 | One I2C bus per core (Wire1: BNO085 + ADXL375 on core 0; Wire on TX/RX: BME688 on core 1) | rev 3 had the BNO and BME on one bus from two cores, which arduino-pico's Wire does not support | `fc_config.h` |
| D23 | Authority-demonstration manoeuvre in early coast: ±5° doublets per axis, then 1° attitude steps; results downlinked and written to the card | measures M_δ/I and closed-loop response in flight instead of inferring it; sized to the stability-dominated airframe (1° costs 2 to 4° of fin) | Electronics_Telemetry §6, `wf_flightsim.MAN` |
| D24 | Stabilizers stay 45° from the control fins | 45° gives the best margin and the most installed authority of 0 / 22.5 / 45°; in line reverses the control | Research_Plan SQ1, Design_Overview §5 |
| D25 | Apogee capped at 600 ft without losing authority: F42-4T + 214 g ballast + 20 mm stabilizers + H45 flight fins; active control now ends at q̄ < 15 Pa instead of climb rate < 15 m/s | your rev 3d request; peak and integrated authority held at the rev 3c values, per-q authority ×2.1, gust tilt 0.44° | Design_Overview §1c |
| D13 | ToF sensors stay unused; the TVC-era ToF ring math stays in the archived `MATH_DERIVATIONS.md` | not part of either design | — |

## Risk register

| Risk | Likelihood / impact | Mitigation |
|---|---|---|
| R1 Control-fin vortex on the stabilizers cancels most of the control moment (installed/isolated 0.47 pessimistic at H = 40) | medium / high | sized for the pessimistic bound; Phase B measures it before flight (SQ1); authority monitor aborts to neutral on a reversed sign |
| R2 Servo sign error after a rebuild | medium / catastrophic | bench SIGN CHECK every time the stack is touched; authority monitor as a backstop |
| R3 Ejection under-pressure (motor charge unknown; 0.3 g gives ~1.0x release) | medium / high | ground test at 0.30 g; drop to 1 shear pin if marginal |
| R4 Motor kick-out on ejection (about 1 kN at 0.5 g in the model) | low / high | 4 x M3 into PC-FR inserts; static-burn check |
| R5 Real masses differ from the model → CG shift | high / medium | weigh, update COTS, re-run the cascade, re-ballast |
| R6 BNO085 clips at 8 g (F42 ignition spike 8.2 g; an F67 holds 11-12 g) | certain / medium (closed) | gyro-only attitude propagation from launch; the vertical channel switches to the ADXL375 above 7 g (D21) |
| R7 Tunnel speed below 6 m/s → small signals | medium / medium | loads scale with V²; 100 g cells still resolve about 50:1 at 6 m/s |
| R8 Fin root boss / cross-pin cracking on landing | medium / low | print spares (STLs are generated); fins are the cheapest part |
| R9 2S HV pack at 8.7 V over the servo's 8.4 V | medium / low | charge to 8.40 V (LiPo mode) |
| R11 X08 Plus real dimensions differ from the datasheet (ear span, spline height) | medium / medium | caliper check, edit `wf_core.SERVO`, regenerate before printing the control tube |
| R12 Crowded spine: leads chafe on the Al tube, board corners touch | medium / medium | 4.85 mm lead annulus, spiral wrap on the tube in the ring, fit-check the spine stack before wiring |
| R13 F67 ejection charge unknown; the bay is half the old volume so pressures run higher | medium / medium | ground test at 0.30 g; plenum and retainer sized for 0.5 g |
| R14 3/8 in tube has only 0.24 mm to each servo base | medium / low | servos sit on their pads before the tube goes in; chamfer the tube end; a light touch on a static aluminium case is harmless |
| R16 ADXL375 axis or sign set wrong | medium / medium | t1 sketch prints all three axes nose-up; pad bias learning would show a 2 g offset in the log; the baro fusion pulls h back after burnout |
| R17 In a 4 m/s or stronger wind, holding vertical saturates the pair late in coast (q below about 1.3 kPa) | likely / low | the airframe stays passively stable; the manoeuvre steps in the direction that relieves the fins and skips if they are past 14°; fly in light wind for the research flights |
| R18 SimScale Community runs are public | certain / low | nothing in the geometry is sensitive; keep proprietary work out of those projects |
| R19 Rail exit 14.8 m/s, just under the usual 15 m/s guideline | medium / medium | fins arm at rail exit and the airframe is 1.01 cal stable; an 8 ft rail (or a 1010 rail extension) gets it to about 17 m/s |
| R20 The authority gain from the 20 mm stabilizers rests on the vortex-interference model | medium / medium | it is the pessimistic single-vortex model, so the real gain is more likely smaller than larger; the margin does not depend on it. Tunnel Phase B (20 / 30 / 40 mm blades) and SimScale R1 vs R2 measure it before flight |
| R10 Altitude (167 m) on an F motor | — | NAR site dimension for F; check with the club RSO |
