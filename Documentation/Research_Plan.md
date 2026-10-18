# GTR70E WYVERN — research plan

_Flow chart: `diagrams/D5_research_plan.png`. Simulation outputs: `Simulations/plots_authority/` (main question) and `Simulations/plots_stabilizer/` (SQ1). Tunnel procedure: `Wind_Tunnel_Adaptation.md`._

## 1. Structure

One main question, answered with wind-tunnel measurements and simulation. Two sub-questions of lesser weight. Flight data is a small extra: three launches that check the chosen design and add one installed data point each.

| | Question | Primary data | Secondary data |
|---|---|---|---|
| Main RQ | How do aerofoil section and fin height set the control authority of a servo-actuated triangular control fin, and which combination gives the most? | Tunnel Phase A (single fin, 4 sections x 5 heights) + simulation sweep | Phase B full finset |
| SQ1 | How much do the rectangular stabilizers reduce the installed authority, and how does that depend on their span and azimuth? | `wf_stabilizer.py` sweep + tunnel Phase B (stabilizers off / 20 / 30 / 40 mm) + SimScale R1 vs R2 | flight authority manoeuvre |
| SQ2 | How well do the simulations predict the tunnel, and how far does the tunnel-plus-simulation prediction carry to flight? | sim vs Phase A and Phase B, point by point | three flights |

## 2. Main research question

_How do aerofoil section (flat plate, 6 % double wedge, NACA 0006, NACA 0012) and fin height (20-40 mm) determine the control authority of a servo-actuated triangular control fin on a 58 mm rocket, and which combination gives the most usable authority?_

"Control authority" here means the normal-force slope with deflection, $C_{N\delta}$, measured over ±10° and referenced to the measured dynamic pressure, together with how linear $C_N(\delta)$ stays out to 15°. On the vehicle that becomes the pitching-moment slope $C_{m\delta}$ about the CG.

### Hypotheses

H1 (section). Thin-aerofoil and panel results rank the 2D lift slopes NACA 0012 > flat plate > NACA 0006 > double wedge (6.88 / 6.72 / 6.57 / 6.44 per rad, `CFD/run_airfoil_cfd.py`). At aspect ratios of 1.3-2.7 the Helmbold correction squeezes those differences to about 2.5 % in 3D (VLM $C_{N\alpha}$ at H = 40: 2.77 / 2.75 / 2.72 / 2.70 per rad). So the linear slopes alone should barely separate the sections.

H2 (section, nonlinear). At larger deflections the sharp leading edges shed a leading-edge vortex and gain vortex lift (Polhamus suction analogy). With the assumed suction-retention factors, the model gives the double wedge 17 % more normal force than linear at 10°, flat plate 7 %, NACA 0006 5 % and NACA 0012 -1.5 %. These factors are guesses; the curvature of the measured $C_N(\delta)$ is what tests them, and smoke plus the laser sheet can show whether the vortex is there. This is where the sections are most likely to separate.

H3 (height). Authority grows faster than linearly with H. Aspect ratio rises from 1.33 to 2.67, and more of the fin clears the body boundary layer (effectiveness 0.78 at H = 20, 0.88 at H = 40). The Phase A prediction for one NACA 0006 fin at 10° and 12 m/s is 15 / 23 / 31 / 40 / 50 mN at H = 20 / 25 / 30 / 35 / 40.

H4 (what it buys). In the closed-loop gust case (4 m/s wind, 4 m/s 1-cos gust, light turbulence), RMS tilt falls from 5.7° at H = 20 to 2.2° at H = 40 and 1.9° at H = 45, for about 1 m of apogee per 5 mm. Peak hinge moment in the H = 40 flight sim is about 12 mN·m, roughly 40x below the X08 Plus stall torque at 7.4 V.

### Factors and levels

| Factor | Levels |
|---|---|
| Section | flat plate (2.4 mm), double wedge 6 %, NACA 0006, NACA 0012 |
| Height | 20, 25, 30, 35, 40 mm (tunnel); 15-50 mm (simulation) |
| Deflection | -15 to +15° in 0.5° steps, 3 s dwell, last 2 s averaged |
| Repeats | 2 sweeps per configuration, randomised order |

20 tunnel configurations x 61 points x 2 = 2,440 balance points in Phase A. One printed fin per configuration is enough for Phase A, so the fin matrix costs about a fifth of what full sets would.

### Selection rule and the three launches

- P* = the section with the most observed authority in the tunnel (largest corrected $C_{N\delta}$ over ±10°, tie-break on linearity to 15°).
- H* = the height with the most simulated installed authority (`wf_fin_authority.py`).
- Fly P* at H* - 5, H*, H* + 5 mm on the AeroTech F67-6W.

Simulated authority rises monotonically with H for every section, so H* = 40 mm and the flights are 35 / 40 / 45 mm (rev 3d flies H45 as the demonstration fin, so it carries the authority manoeuvre's headline numbers). 45 mm is one step outside the tunnel set, which makes that flight an out-of-sample check on the height trend.

## 3. SQ1: impact of the rectangular stabilizers

_How much do the fixed rectangular stabilizers reduce the installed control authority, and how does that depend on stabilizer span and on their azimuth relative to the control fins?_

A deflected control fin sheds a tip vortex that streams aft past the stabilizers. Its downwash pushes on them in the direction opposite to the control force. The stabilizers buy static margin and take back control power at the same time.

### Simulation (`Simulations/wf_stabilizer.py`)

Span 0-60 mm and azimuth offset 0 / 22.5 / 45° between stabilizers and control fins, H = 40, F67-6W, 58 mm airframe, pessimistic single-vortex model (Nielsen-type, rolled-up vortex plus body image):

| Stab span (45° offset) | Liftoff margin (cal) | I = induced / control force | Installed / isolated $C_{m\delta}$ | RMS tilt, fins active | RMS tilt, fins locked |
|---|---|---|---|---|---|
| 0 | -0.65 | 0 | 1.00 | 0.4° | tumbles |
| 20 | -0.04 | -0.11 | 0.81 | 0.0° | 8.2° |
| 30 | 0.51 | -0.19 | 0.66 | 0.7° | 6.8° |
| 40 (flight, = control-fin height) | 1.02 | -0.26 | 0.53 | 2.2° | 8.4° |
| 45 | 1.24 | -0.29 | 0.47 | 4.3° | 8.9° |
| 50 | 1.44 | -0.32 | 0.42 | 6.8° | 9.1° |
| 60 | 1.75 | -0.35 | 0.35 | 10.2° | 9.6° |

(110 g ballast. The 20 mm row flies with the fins locked only because the margin is about zero, so the gust barely turns it; it would not survive a fin failure in a bigger gust.)

At 40 mm span the azimuth matters a lot:

| Offset | Margin | I | Installed / isolated | RMS tilt active / locked |
|---|---|---|---|---|
| 0° (stabilizers in line with the control fins) | 0.55 | -0.67 | -0.20 (reversed) | 20.2° / 7.2° |
| 22.5° | 0.90 | -0.38 | 0.33 | 3.7° / 8.0° |
| 45° (as built) | 1.02 | -0.26 | 0.53 | 2.2° / 8.4° |

Rev 3d took this one step further: with the apogee capped at 600 ft, the stabilizers went to 20 mm span and 214 g of ballast restored the margin; per-q authority doubled (`wf_apogee_cap_trade.py`, Design_Overview §1c). That makes SQ1 a flight-critical question, not just a research one, and the 20 mm blade joins the Phase B set.

Planform trade (`wf_stabilizer_planform_trade.py`, also in Design_Overview §5): cutting the stabilizers from 45 to 40 mm, the same height as the control fins, raises the installed $C_{m\delta}$ by 32 % once 20 g of ballast restores the margin. Stretching the chord AIM-54 style along the motor bay adds more authority but drops the margin to 0.58 cal unless 60 g of ballast goes in. Putting the stabilizers in line with the control fins, as on the AIM-54, reverses the control in the model (S2).

Predictions to test:

- S1. The interference ratio grows with stabilizer span and shrinks as the offset goes from 0 to 45°.
- S2. With stabilizers in line (0°), the model predicts the control derivative reverses sign. That is the most striking prediction in the project and the cheapest to check: Phase B with the tail section rotated 45°.
- S3. Bigger stabilizers make the airframe more stable, which is what lets it fly with the fins locked (no stabilizers: it tumbles). They also cost authority twice: the vortex interference above, and a larger restoring moment the fins must overcome. And a more stable airframe weathercocks harder into a gust, so with the fins active the RMS tilt rises with span (2.2° at 40 mm, 6.8° at 50 mm). The flight uses 40 mm (matched to the control fins) with 110 g of ballast, because the fail-safe (fins centred) needs about 1 cal of margin on its own.

### Tunnel (Phase B)

Full four-fin control tube with the removable stabilizer tail section, stabilizers off (slots plugged), 20 mm (rev 3d flight), 30 mm and 40 mm, at H = 35 / 40 / 45 with P*. One pair deflected; the strut balance reads the total side force. The difference between stabilizers-on and stabilizers-off is the induced stabilizer force, so $\Delta N / N_{off}$ measures I directly. Expected at 7 m/s and 10°, H = 40: 45.1 mN off, 36.4 mN with 30 mm, 33.2 mN with 40 mm.

A second sweep rotates the strut through ±6° of yaw with the fins at zero, which gives the model's restoring-force slope with and without stabilizers (expected 7.5 / 10.7 / 13.0 mN per degree for off / 30 / 40). That ties the tunnel to the static-margin column above.

If time allows, rotate the tail section by 45° (stabilizers in line with the control fins) to test S2.

## 4. SQ2: simulation to tunnel to flight

_How well does the simulation chain (panel CFD → VLM → slender-body → boundary layer → vortex interference) predict what the tunnel measures, and how much of the tunnel-plus-simulation prediction survives in flight?_

- Sim vs Phase A: prediction error of $C_{N\delta}$ for each of the 20 configurations, and whether the ranking holds (Spearman rank correlation). This tests the section and height modelling with no body and no stabilizers.
- Sim vs Phase B: body carry-over $K_{W(B)}$ (pair on body vs twice the single fin) and the measured I vs the single-vortex model. Fit the interference scale factor `WYV_INTERF` to Phase B.
- CFD (rev 3c): ten SimScale RANS cases (`Simulations/CFD/simscale/`): the Phase A fin at four deflections and four profiles, and the full rocket with and without stabilizers and at 4° incidence. They sit between the potential-flow models and the tunnel, and R1 minus R2 is a third estimate of the stabilizer interference.
- Flight: the authority manoeuvre (Electronics_Telemetry §6). Early in coast the firmware injects a ±5° doublet on each axis and fits $\dot\omega = c + a\theta + m_q\omega + b\delta$; $b = M_\delta / I$, so $C_{m\delta} = b I / (\bar q A_{ref} d)$. It then commands 1° attitude steps and records t63, overshoot and fin per degree. The sim predicts the fit lands within ±31 % (1 sd) of the model in winds up to 7 m/s, and the firmware code reproduces the simulator's numbers to three decimals in replay, so a flight value outside that band is a model error, not an estimator artefact. Three flights give six axis-points against the tunnel-calibrated prediction.

## 5. Single fin or all four fins in the tunnel?

A single fin is the right test article for the main question, and it is what Phase A uses. All four fins earn their place only for SQ1, so they appear in Phase B at three heights.

Why one fin is enough for section x height:

- The main question compares fins with each other. Every configuration would share the same body, hubs and servos, so the body adds the same factor to all of them and does not change the ranking.
- A half-model on a reflection-plane wall fits the stock 100 x 100 mm section: about 2-3 % blockage at 10° deflection, against about 9 % for the full 58 mm model in a 200 x 200 section. Smaller corrections mean cleaner differences between sections.
- The stock contraction with the Cloudline T8 should reach about 12 m/s (measure it), and force scales with V², so a single fin at 12 m/s gives more signal (50 mN at H = 40) than a pair at 7 m/s in the large section (46 mN).
- It needs one fin per configuration instead of four.

What one fin cannot show:

- Body carry-over (the body's share of the lift a fin induces): about 1.5x in slender-body theory.
- Pair interaction and the vortex from one fin reaching the other fins.
- The stabilizer interference, which is SQ1 itself.

Phase B covers those three with the real control tube, at the three heights that will fly.

## 6. Analysis

- Tunnel corrections: solid and wake blockage, and for Phase A the reflection-plane correction (Barlow, Rae and Pope, _Low-Speed Wind Tunnel Testing_, 3rd ed., ch. 9-10).
- Slopes by least squares over ±10° with 95 % confidence intervals; curvature from a cubic fit to ±15°.
- Two-way ANOVA (section x height) on the Phase A slopes.
- SQ1: I with its confidence interval at each height and span; regression of I on span.
- SQ2: per-configuration percent error and rank correlation; `WYV_INTERF` fitted to Phase B, then the three flights compared against the model before and after that fit.

## 7. Order of work

1. Print the control tube and servo ring, check the X08 Plus fit and the bench sign check (t2 sketch).
2. Phase A: wall panel, cradle on two 100 g cells, pitot. Calibrate, run the 20 configurations, pick P*.
3. Re-run `wf_fin_authority.py` with the measured section factors and confirm H*.
4. Phase B: 200 x 200 section, stabilizer tail, P* at 35 / 40 / 45, stabilizers off / 30 / 50, yaw sweep.
5. Ground ejection test, static burn of the spare F67-6W, pad rehearsal with telemetry.
6. Three flights, swapping only the control fins.
