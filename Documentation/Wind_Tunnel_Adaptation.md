# Adapting Jerrod H's tunnel: Phase A single fin, Phase B full finset

_Rev 3: both phases stay, because every printed tunnel part fits a 256 x 256 x 256 mm printer (largest: the 228 mm junction adapter; table in §6). The Phase B test section itself is acrylic and 2020 extrusion, not printed. Drawing: `diagrams/D4_wind_tunnel_adaptation.png`. Printed parts: `3D parts/wind_tunnel/` (`WTA_*` Phase A, `WTB_*` and `WT_*` Phase B). Shopping list: `WYVERN_FIN_BOM.xlsx`, sheet "To Buy - Wind Tunnel". Why two phases: `Research_Plan.md` §5._

_Scope as of 2026-10-16: only Phase A is being built. Phase B (§3 and the `WTB_*` / `WT_*` parts) stays documented for later, but nothing for it is on the BOM (acrylic, 2020 extrusion, 500 g cell, 12 mm sting rod and the third NAU7802 were removed)._

## 1. The stock tunnel, measured

The designer's page gives only the window size (80 x 130 mm), so the internal dimensions below were measured by slicing the STLs in `Wind Tunnel/STEM+Tunnel+Promo+-+0.4n_stls/`:

| Module | Internal cross-section | Length |
|---|---|---|
| Basic duct / honeycomb / screen sections (228 mm outer) | 202 x 202 mm | 75 mm each |
| Contraction (Body4) | 202 → 100 mm square (4:1 area) | 250 mm |
| Test section frame (part 6) | 100 x 100 mm | 175 mm |
| Diffuser + extension (parts 7, 8) | 100 → 140 mm round (NF-A14) | 175 + 180 mm |
| Fan | Noctua NF-A14 iPPC 3000, 140 mm | |

## 2. Phase A: one fin on a reflection plane, stock section

This phase answers the main research question (section x height). The tunnel stays stock up to the end of the test section.

| Part | What it does |
|---|---|
| `WTA_reflection_plane_wall_panel_PETG` | 175 x 100 x 4 mm panel that replaces one side wall of the stock section. Bevelled leading edge so the panel's boundary layer starts thin, 10 mm bore for the hub. Corner holes are marked VERIFY against Jerrod's part 4 ("Test Section Wall for Half-Span Model Support") |
| `WTA_servo_balance_cradle_PETG` | Holds one KST X08 Plus outside the tunnel with the same ear pad and window as the flight wall, so the flight hub and fin fit unchanged: spline face 4.0 mm behind the airflow face, fin root 1.0 mm off it. The cradle sits on two 100 g TAL221 cells, 60 mm apart along the chord |
| `WTA_diffuser_100sq_to_8in_round_PETG` | 250 mm transition from the stock section exit to 8 in round, so the Cloudline T8 replaces the Noctua |

Numbers at H = 40 (the largest tunnel fin):

- Blockage: about 2-3 % of the 100 x 100 section at 10° deflection.
- Semi-span / section width 0.40 (0.45 at H = 45), inside the usual half-model limit.
- Speed: the T8 is rated 807 CFM free air, which would be 38 m/s through 0.01 m². With the honeycomb, screens and a steep transition the simulation assumes 12 m/s. Measure it with the pitot.
- Expected normal force on one fin at 10°, 12 m/s: 15 mN at H = 20 rising to 50 mN at H = 40 (`plots_authority/A_isolated_vs_H.png`).

The two cells give normal force (sum) and chordwise centre of pressure (difference x 30 mm / sum). The fin's force also acts about 20 mm out from the panel, so the cells see a spanwise moment as well. The in-situ calibration removes that crosstalk: hang weights from a thread tied at three chord stations on the fin, run over a pulley, and fit a 2 x 2 calibration matrix.

## 3. Phase B: full four-fin model with the stabilizer tail, 200 x 200 section

This phase answers SQ1 (stabilizer impact) and gives the body and pair data for SQ2. It keeps everything upstream of the contraction and replaces everything downstream:

| Keep (unchanged) | Replace |
|---|---|
| Inlet, honeycomb, 40-mesh screen module, junction rings, stands, smoke rake, laser sheet, LED module | 4:1 contraction (Body4) |
| 80-mesh screen module (optional; it costs the most pressure) | 100 x 100 x 175 test section |
| | Diffuser, diffuser extension, fan guard, Noctua |

New parts:

1. Test section: 200 x 200 mm internal, 750 mm long (lengthened from 600 so the stabilizer tail fits). Four 2020 extrusions as corner longerons, 3 mm cast acrylic on both sides and the top, a 6 mm floor plate with a slot for the strut.
2. `WT_adapter_228sq_to_200sq_x2_PETG` at each end; `WT_diffuser_200sq_to_8in_round_PETG` to the Cloudline T8.
3. Test article, nose to tail: `WT_nose_fairing_ogive100_ASA` → the real 58 mm control tube (servo ring, hubs, fins, spine) → `WTB_stabilizer_tail_section_ASA` → `WT_tail_fairing_sting_socket_ASA`. The tail section reproduces the airframe from the control-tube aft end to the stabilizer trailing edge (122 mm) with four through-the-wall slots at 45°. Blades `WTB_stabilizer_blade_span20`, `span30` and `span40` (four each; 20 mm is the rev 3d flight span, 40 mm the rev 3b one) push into the slots and are pinned with M3; `WTB_slot_plug` closes the slots for the stabilizers-off runs, so the body is identical in every configuration.
4. Model length 471 mm, which leaves about 140 mm of clear section at each end.

Numbers:

- Control-fin tip to tip at H = 45: 150 mm, 0.75 of the width. Stabilizers at 45° reach 69 mm from the axis, towards the corners.
- Blockage about 9 % with one pair at 10° and the 40 mm stabilizers fitted (less with the 20 mm flight set) (the 58 mm body alone is 6.6 %). Above the 7.5 % guideline, so apply solid- and wake-blockage corrections (Barlow, Rae and Pope ch. 9). The on/off comparison shares the same body, so the stabilizer increment depends very little on the correction.
- Speed 6-8 m/s expected (7 m/s assumed in the predictions).

Test matrix: P* at H = 35 / 40 / 45, stabilizers off / 20 / 30 / 40, one pair swept ±15°, plus a ±6° strut-yaw sweep at zero deflection for the restoring-force slope. Predicted readings are in `plots_stabilizer/S3_tunnel_phaseB.png` and `stabilizer_sweep.json`.

## 4. Balance electronics (both phases)

| Cell | Phase A | Phase B |
|---|---|---|
| 2 x 100 g TAL221 (SEN-14727) | under the servo cradle, fore and aft along the chord | fore and aft under the strut base: side force and yawing moment |
| 1 x 500 g TAL221 (SEN-14728) | unused | axial (drag increment) |

Three SparkFun Qwiic Scale NAU7802 boards, all at 0x2A, behind the owned Adafruit PCA9548 mux. A spare Pico 2 W (owned) reads them and the SDP810 pitot sensor (0x25). Firmware: `Wind Tunnel/wt_balance_daq/`. The t2 sketch's `w0` / `w1` command drives the deflection sweep (-15 to +15° in 0.5° steps, 3 s dwell) and prints `WT,<ms>,<deg>` markers for syncing.

## 5. Running a session

1. Calibrate the cells (five loads up and down; Phase A uses the thread-and-pulley matrix above).
2. Fit the fin(s). Run t2 to confirm 0° and ±10° with the angle gauge.
3. Fan to speed, wait 60 s, log q.
4. Sweep; average the last 2 s of each dwell at 80 Hz.
5. Tare: hub only, no fin (Phase A); fins off, hubs on (Phase B).
6. Two repeats per configuration, randomised order.

Smoke and laser-sheet runs at 10-15° on the double wedge and NACA 0012 show whether the sharp edge sheds a leading-edge vortex (hypothesis H2). In Phase B the same setup can show where the control-fin tip vortex passes the stabilizers.

## 6. What to buy

From the BOM sheet: Cloudline PRO T8 and two 8 in clamps, three 12 x 36 in sheets of 3 mm acrylic (the 750 mm section needs the longer cuts), 2020 extrusion with brackets, three NAU7802 boards, two 100 g cells and one 500 g cell, an SDP810-125Pa with a pitot probe and tubing, 12 mm rod, a fifth KST X08 Plus for the Phase A cradle, a USB-C extension, and about 2.5 kg of ASA or PETG for the adapters, transitions, wall panel, cradle, tail section and fairings.

## 7. Does the full stack fit your printers?

Yes. Every printed tunnel part, flight part and control fin was checked against a 256 x 256 x 256 mm bed by `gen_fit_assembly.py` (full list in `3D parts/assembly/FIT_REPORT.md`). The big ones:

| part | bounding box (mm) |
|---|---|
| WT_adapter_228sq_to_200sq (x2) | 228 x 228 x 12 |
| WTA_diffuser_100sq_to_8in_round | 250 x 213 x 213 |
| WT_diffuser_200sq_to_8in_round | 213 x 213 x 150 |
| WTA_reflection_plane_wall_panel | 175 x 100 x 4 |
| control tube (the test article) | 169 x 58 x 58 |
| WTB_stabilizer_tail_section | 142 x 58 x 58 |

Phase A remains the main experiment and needs only the wall panel, the cradle and the 100 sq to 8 in transition. Phase B adds the 200 mm section for the stabilizer study. If time or money runs short, Phase B is the part to drop, and SQ1 then rests on simulation plus the flight doublets.

Reused, already owned: every upstream STL, the 40/80 mesh, magnets, Loc-Line, CF3 fog machine, line laser, P96L light, PCA9548, a spare Pico 2 W, calibration weights.
