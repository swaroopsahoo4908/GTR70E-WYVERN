# Adapting Jerrod H's tunnel: Phase A single fin, Phase B full finset

_Rev 3: both phases stay, because every printed tunnel part fits a 256 x 256 x 256 mm printer (largest: the 228 mm junction adapter; table in §6). The Phase B test section itself is acrylic and 2020 extrusion, not printed. Drawing: `diagrams/D4_wind_tunnel_adaptation.png`. Printed parts: `3D parts/wind_tunnel/` (`WTA_*` Phase A, `WTB_*` and `WT_*` Phase B). Shopping list: `WYVERN_BOM.xlsx`, section "Wind Tunnel". Why two phases: `Research_Plan.md` §5._

_Scope as of 2026-10-16: only Phase A is being built. Phase B (§3 and the `WTB_*` / `WT_*` parts) stays documented for later, but nothing for it is on the BOM (acrylic, 2020 extrusion, 500 g cell, 12 mm sting rod and the 500 g cell were removed). Rev 3f (2026-11-01): one Metro M4 Express replaces the Pico, the drive is a 6 in EC fan on a shorter 6 in transition, and a printed calibration pulley joins the set. Rev 3e (2026-10-22) cut the Phase A instrumentation to what the RQ needs: two HX711s you already own instead of NAU7802s, a pitot tube and a printed inclined water manometer instead of the SDP810, one Pico 2 W as the only controller, and Amazon / SparkFun sourcing._

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
| `WTA_servo_balance_cradle_PETG` | Holds one EMAX ES9251 II outside the tunnel with the same ear pad and window as the flight wall. Rev 4b: the spline sits 16.6 mm behind the airflow face so the AS5600 gear train fits; the tunnel hub makes up the length, so the fin root is still 1.0 mm off the panel. Carries the sensor-gear post and the AS5600 ledges, and sits on two 1 kg bar cells, 60 mm apart along the chord |
| `WTA_hub_gear40_m1_PETGCF` / `WTA_sensor_gear20_m1_PETGCF` | Tunnel hub with a 40 T module 1 gear and the 20 T magnet gear (section 4.4) |
| `WTA_fin_zero_jig_PETG` | V-groove jig that holds the fin at 0° for zeroing the AS5600 (no angle gauge) |
| `WTA_diffuser_100sq_to_6in_round_PETG` | Rev 3f: 160 mm loft from the stock section exit to 6 in round (area ratio 1.82, about 7° equivalent half-angle, so the flow stays attached), then a 30 mm socket that slides over the fan collar and takes a 6 in clamp. Drives a 6 in EC inline fan (405 CFM, speed controller) or, later, a BLDC prop shroud. 190 x 158 x 158 mm |
| `WTA_calibration_pulley_wheel` + `_bracket` | Rev 3f: 30 mm grooved wheel around the owned MR105 bearing, on an M5 bolt in a slotted L-bracket, so the calibration thread leaves the fin level and the weights hang straight down |
| `WTA_inclined_manometer_ramp_PETG` + `_lid` | 242 x 44 x 32 mm ramp at 1:10 (5.71°) with a 4.6 mm groove for the 1/4 in OD tube, ticks every 5 mm, and a 40 mm reservoir cup. The pitot's total and static lines go to the cup lid and the far end of the tube; the water column moves 10 mm along the tube per 1 mm of head |

Numbers at H = 40 (the largest tunnel fin):

- Blockage: about 2-3 % of the 100 x 100 section at 10° deflection.
- Semi-span / section width 0.40 (0.45 at H = 45), inside the usual half-model limit.
- Speed: a fan's free-air rating overstates what it delivers through screens and a contraction. Intersecting a straight-line fan curve with a tunnel loss of about 0.85 × the test-section dynamic pressure gives roughly 12 m/s for the 6 in EC fan (16 m/s for the 8 in 750 CFM fan it replaced), ±30 %. The predictions below keep 11 m/s; the pitot and manometer measure the real value every session, and the fan's speed knob can trim it.
- Expected normal force on one fin at 10°, 11 m/s: 12-15 mN at H = 20 rising to 40-46 mN at H = 40 and 49-56 mN at H = 45, double wedge highest and NACA 0012 lowest (`plots_authority/A_isolated_vs_H.png`). Between profiles at one height the spread is about 15 %, which sets the precision the balance needs.

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
2. `WT_adapter_228sq_to_200sq_x2_PETG` at each end; `WT_diffuser_200sq_to_8in_round_PETG` to an 8 in fan (Phase B was drawn for the 8 in; re-size it to 6 in if the Phase A fan is reused).
3. Test article, nose to tail: `WT_nose_fairing_ogive100_ASA` → the real 58 mm control tube (servo ring, hubs, fins, spine) → `WTB_stabilizer_tail_section_ASA` → `WT_tail_fairing_sting_socket_ASA`. The tail section reproduces the airframe from the control-tube aft end to the stabilizer trailing edge (122 mm) with four through-the-wall slots at 45°. Blades `WTB_stabilizer_blade_span20`, `span30` and `span40` (four each; 20 mm is the rev 3d flight span, 40 mm the rev 3b one) push into the slots and are pinned with M3; `WTB_slot_plug` closes the slots for the stabilizers-off runs, so the body is identical in every configuration.
4. Model length 471 mm, which leaves about 140 mm of clear section at each end.

Numbers:

- Control-fin tip to tip at H = 45: 150 mm, 0.75 of the width. Stabilizers at 45° reach 69 mm from the axis, towards the corners.
- Blockage about 9 % with one pair at 10° and the 40 mm stabilizers fitted (less with the 20 mm flight set) (the 58 mm body alone is 6.6 %). Above the 7.5 % guideline, so apply solid- and wake-blockage corrections (Barlow, Rae and Pope ch. 9). The on/off comparison shares the same body, so the stabilizer increment depends very little on the correction.
- Speed 6-8 m/s expected (7 m/s assumed in the predictions).

Test matrix: P* at H = 35 / 40 / 45, stabilizers off / 20 / 30 / 40, one pair swept ±15°, plus a ±6° strut-yaw sweep at zero deflection for the restoring-force slope. Predicted readings are in `plots_stabilizer/S3_tunnel_phaseB.png` and `stabilizer_sweep.json`.

## 4. What gets measured, and with what (Phase A)

The research question asks which profile and height give the most normal force per degree of deflection. That needs three numbers per data point: the fin's normal force, the dynamic pressure, and the deflection angle. Everything else is bookkeeping.

### 4.1 Fin force: a two-cell balance

The servo cradle sits on two 1 kg straight-bar load cells (the ShangHJ kit, two cells and two HX711 modules for $9.99), 60 mm apart along the chord, outside the tunnel wall. The cradle base takes each cell's two end bolts at 15 mm pitch in 5.3 mm holes, which fit M4 or M5; check the pitch on the cells you get. The fin's normal force pushes the cradle sideways into both cells, so

$$N = (F_{fore} + F_{aft})\,g, \qquad x_{cp} = \frac{d}{2}\,\frac{F_{aft} - F_{fore}}{F_{fore} + F_{aft}}, \quad d = 60\ \text{mm}$$

The sum is the normal force, and the split between the cells gives the chordwise centre of pressure (useful for hinge moment and for spotting separation). The fin's force also acts about 20 mm out from the panel, so the cells see a spanwise moment too; the thread-and-pulley calibration (weights hung from three chord stations on the fin) fits a 2 x 2 matrix that removes that crosstalk.

Each cell goes to its own HX711 module, gain 128, with VCC from the Metro's 3.3V pin so DOUT stays at 3.3 V logic (red E+, black E-, green A+, white A-). A 1 kg bar cell puts out about 1 mV/V, so at 3.3 V excitation that is about 3.3 µV per gram, six times less than a 100 g cell would give. The HX711's 50 nV rms input noise at 10 samples/s is then about 15 mg per sample, or about 3 mg (0.03 mN) after the 2 s average at each sweep step. The smallest predicted reading, 12 mN at H = 20, is about 1.2 g, so noise stays near 0.3 % even there.

The 1 kg cells' weak spot is not noise but creep and hysteresis: cheap cells are typically a few hundredths of a percent of full scale, which is a few tenths of a gram here, a sizeable fraction of the H = 20 loads. Three habits keep it out of the slopes: tare (`t`) right before and right after every sweep and remove the linear drift between the two; sweep both ways (`s` then `r`) and average, so hysteresis cancels; and fly the check-standard fin first and last each session. The 1 kg cells are also about ten times stiffer, so the cradle barely moves under load, which helps the angle measurement.

The NAU7802 is a better ADC on paper (lower noise, I2C, programmable rate), but at 1-6 g loads it buys nothing the HX711 can't already resolve. The PCA9548 mux is no longer needed (the HX711 uses two GPIOs, not an I2C address).

### 4.2 Airspeed: pitot tube and inclined water manometer

You control the fan, but a knob setting is not a speed: screens load up with dust, mains voltage moves, and the room temperature changes air density. Force coefficients need $q$, so something has to measure it. A pitot tube reads it directly, with no calibration of its own:

$$q = \rho_w\,g\,L\,\sin\theta\,\left(1 + \frac{A_{tube}}{A_{cup}}\right), \qquad V = \sqrt{2q/\rho_{air}}$$

with $L$ the travel along the 1:10 ramp ($\sin\theta = 0.0995$) and $A_{tube}/A_{cup} = (3.175/40)^2$. At 11 m/s, $q \approx 73$ Pa, which is 7.4 mm of water head and 74 mm of travel along the tube. Reading the meniscus to ±0.5 mm gives ±0.7 % on $q$, close to the SDP810's ±3 % of reading and good enough because the RQ compares fins at one speed. Water costs nothing, needs no electronics, and the manometer is printed.

You type the reading into the Metro (`m74`), and from then on every result line carries $q$, $V$ and $C_N$. Air density comes from the spare BME688 (temperature, pressure and humidity, Magnus formula for the water vapour). The SDP810-125Pa and the RMRC pitot are both out of stock, and the MS4525DO kits on Amazon run $36-49 from sellers with doubtful listings; a handheld vane anemometer would cost less but reads ±5 % and blocks the section.

### 4.3 One controller

An Adafruit Metro M4 Express (ATSAMD51, 3.3 V logic), programmed from the Arduino IDE, does everything: servo signal on D9, fore HX711 on D2 (DT) / D3 (SCK), aft HX711 on D4 / D5, BME688 on the SDA/SCL header through a STEMMA QT to male-header cable, and the AS5600 daisy-chained off the BME688's second QT port (0x36). The EMAX ES9251 II is powered from a 5 V 3 A wall supply through a barrel-jack terminal, with its minus tied to Metro ground, so servo current never flows on the USB rail the cells share. The laptop runs a serial terminal (or the IDE's Serial Monitor at 115200) and saves the CSV. Firmware `Wind Tunnel/wt_balance_daq/wt_balance_daq.ino` (v3.1; it prints every number with `Serial.print` because SAMD's newlib-nano does not format floats in `printf`). The full pin map is in the sketch header.

| Command | Does |
|---|---|
| `t` | tare both cells (fan off, fin on) |
| `k0,<g>` / `k1,<g>` | calibrate a cell with a known mass |
| `a<deg>` | set the deflection (±15° clamp) |
| `s` / `r` | sweep −15° to +15° (`s`) or back down (`r`) in 0.5° steps; 1 s settle, 2 s average, one `R` line per step |
| `m<mm>` | manometer travel for this run |
| `h<mm>` | fin height for $C_N$ |
| `z` | zero the angle sensor with the fin held at 0° by the printed `WTA_fin_zero_jig` |
| `g<deg>` | optional calibration point against an outside reference (3+ points refit the scale); normally not needed |
| `p` | print settings |

Output: `D` lines (every sample: commanded and measured angle, raw counts and grams), `WT` markers at each step, and `R,<deg_cmd>,<deg_meas>,<fore_g>,<aft_g>,<N_mN>,<xcp_mm>,<q_Pa>,<V>,<CN>` per step. The slope $dC_N/d\delta$ is fitted against `deg_meas`. The flight computer is not needed in the tunnel.

### 4.4 Deflection: measured with an AS5600, not taken from the command

The commanded angle is not the fin's angle. The ES9251 II has a plastic gear train with backlash, and under aerodynamic hinge load the servo winds up a little before its feedback pot notices. A $C_N$ slope fitted against the command would fold that error into the aerofoil comparison. So the fin's angle is read downstream of the servo, on the hub itself (drawing `diagrams/D10_wt_angle_sensor.png`):

- The tunnel hub `WTA_hub_gear40_m1_PETGCF` is the flight hub with a 40-tooth, module 1 spur gear printed into its flange. It takes the same servo horn and screw and the same fin (D-flat and cross-pin), so every test fin fits.
- It drives `WTA_sensor_gear20_m1_PETGCF` (20 teeth) at 2:1, so ±15° at the fin is ±30° at the sensor. The sensor gear spins on a 4 mm post printed into the cradle and carries a 6 x 2.5 mm diametric NdFeB magnet in a pocket in its top face.
- An Adafruit AS5600 (12 bit, 0.088° per count) sits chip-down over the magnet with a 1.5 mm gap, on two ledges of the same cradle. With the 2:1 step-up the fin resolves to 0.044°.
- Backlash in the printed mesh would otherwise show up directly as angle error. A small rubber band from the preload pin under the sensor gear to the hook on the cradle arm keeps the teeth on one flank, so the mesh has no free play to cross. Use the lightest band that still pulls: about 0.1 N at the pin's 7 mm radius is 0.7 mN·m at the sensor gear, 1.4 mN·m at the hub after the 2:1, about 5 % of the servo's 26 mN·m stall torque. The servo holds its position against it, and whatever small offset is left shows up in the measured angle anyway.
- All of it rides on the balance cradle. Nothing touches the panel (3.0 mm clearance above the AS5600 board), so it adds no load path to ground; the STEMMA cable to the Metro is dressed slack like the cell leads.
- Calibration: no angle gauge. The printed `WTA_fin_zero_jig` sits on the panel and its two V-grooves catch the fin's root leading and trailing edges; every section is symmetric, so both edges lie on the chord line and the jig holds the fin at exactly 0° whatever its thickness. Send `z` with the jig on, then take it off. The scale comes from the tooth count (40:20, exactly 2.0) and the AS5600's 4096 counts per turn, so there is nothing to fit; `g<deg>` stays in the firmware in case you ever want to check it against an outside reference.

To make room for the gear and the board, the servo sits 12.4 mm deeper behind the panel than it does behind the flight wall, and the tunnel hub's shaft is 12.4 mm longer, so the fin root still sits 1.0 mm off the panel. The cradle legs also moved outboard of the servo's mounting ears (the old cradle had them overlapping). A stack check of panel, cradle, servo, hub, both gears, magnet and board finds no overlaps.

Phase B (deferred) would add a third cell under the strut and is unchanged on paper.

## 5. Running a session

1. Fan off. Level the manometer (bubble in the ramp's top face), zero the meniscus at the 0 tick.
2. Fit the fin. Seat `WTA_fin_zero_jig` on the panel over the fin, send `z`, remove the jig. Redo this whenever the hub comes off the servo.
3. `t` to tare; `k0,<g>` and `k1,<g>` with the thread-and-pulley weights (five loads up and down at the start of each test day).
4. Fan to the full-speed stop and wait 60 s. Read the manometer, type `m<mm>`, and `h<mm>` for the fin.
5. `t`, `s`, `r`, `t`. Each sweep takes about 3 minutes; average the two directions and remove the drift between the two tares.
6. Fan off, `t` again, note the zero shift (drift check).
7. Two repeats per configuration, in a randomised order.
8. Check standard: the same fin (double wedge, H = 40) is swept first and last every session. If its $C_N$ slope moves more than 2 %, that session's data gets flagged.

Tufts: 20-30 mm sewing-thread tufts taped at the fin's leading edge, mid-chord and tip show attached versus separated flow at 10-15° through the top acrylic window. That covers hypothesis H2 (whether the double wedge's sharp edge sheds a leading-edge vortex). Smoke and the laser sheet are on the optional sheet if you want pictures later.

## 6. What to buy (Phase A, updated 2026-11-01)

The tunnel's buy list is the "Wind Tunnel" section of `WYVERN_BOM.xlsx` (one sheet for the whole project, built by `build_bom.py`). It comes to $250.93: Metro M4, BME688, AS5600, QT cables and the 2.1 mm jack terminal from Adafruit; the 1 kg load-cell + HX711 kit, 6 in EC fan, clamps, 40 and 80 mesh, pitot kit, PVC tube, acrylic, 5 V 3 A supply, calibration weights, MR105 bearings and diametric magnets from Amazon. PETG, PETG-CF, thread, screws, servo extensions and jumpers are already yours; the servo and heat-set inserts are bought once under "Rocket".

The drive is the 6 in EC fan. A BLDC motor with a 6 in prop in a printed shroud would also work (ESC, 12 V 10 A supply, lead and props, about $66 in place of the $64.99 fan), but it needs the motor's model and KV first, so it is not on the list.

Optional, not needed for the RQ data (the "Flow-Vis" section of the same sheet, $229.48): fog machine and fluid, green line laser, light, Loc-Line, magnets.

Skip Jerrod's Noctua diffuser, extension and fan guard; `WTA_diffuser_100sq_to_6in_round` replaces all three.

## 7. Does the full stack fit your printers?

Yes. Every printed tunnel part, flight part and control fin was checked against a 256 x 256 x 256 mm bed by `gen_fit_assembly.py` (full list in `3D parts/assembly/FIT_REPORT.md`). The big ones:

| part | bounding box (mm) |
|---|---|
| WT_adapter_228sq_to_200sq (x2) | 228 x 228 x 12 |
| WTA_diffuser_100sq_to_6in_round | 190 x 158 x 158 |
| WT_diffuser_200sq_to_8in_round | 213 x 213 x 150 |
| WTA_reflection_plane_wall_panel | 175 x 100 x 4 |
| control tube (the test article) | 169 x 58 x 58 |
| WTB_stabilizer_tail_section | 142 x 58 x 58 |

Phase A remains the main experiment and needs only the wall panel, the cradle, the 100 sq to 6 in transition, the manometer and the calibration pulley. Phase B adds the 200 mm section for the stabilizer study. If time or money runs short, Phase B is the part to drop, and SQ1 then rests on simulation plus the flight doublets.

Reused: every upstream STL and the filament. Phase B's own parts (acrylic section, 2020 extrusion, third cell) are not on the BOM.
