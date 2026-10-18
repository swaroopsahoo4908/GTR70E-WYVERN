
---

# XRIM-117 WYVERN PTD — Wind Tunnel Evaluation & Programme Adaptation

_CONFIDENTIAL — PROPRIETARY — NOT FOR DISTRIBUTION_ _Skylight Industries LLC | PDR-002 Rev A | Aerodynamic Ground Test Planning Document_

---

## 1. Source Tunnel Evaluation

The tunnel in question is the _Modular Wind Tunnel for STEM Education_ by Jerrod Hofferth, presented at AIAA SciTech 2025. It is an open-return (in-draft) low-speed tunnel designed for FDM fabrication, smoke visualization, and Gridfinity-compatible test article exchange. Published CC BY-NC-SA 4.0. Despite its educational positioning, the underlying design follows established low-speed tunnel best practices and is a legitimate aerodynamic test platform for qualitative visualization and limited quantitative work at the relevant scale.

### 1.1 Tunnel Architecture Summary

The tunnel consists of nine primary printed modules in series:

|Station|Module|Function|
|---|---|---|
|1|Bell-mouth inlet|Smooth ambient ingestion, minimize inlet losses|
|2|Honeycomb flow straightener|Breaks large-scale turbulence, aligns flow|
|3|Empty duct section(s)|Turbulence decay via viscosity|
|4|Smoke-strut section|Smoke/fog injection upstream of contraction|
|5|Contraction cone|4:1 area ratio, accelerates to test velocity|
|6|Test section frame|Open 80mm × 130mm rectangular section, acrylic windows|
|7|Diffuser (standard)|Re-expands flow, recovers static pressure before fan|
|8|Extended diffuser (optional)|Additional pressure recovery|
|9|Fan (Noctua NF-A14 IPPC-3000, 140mm)|Baseline propulsor|

The modular junction ring system (large 4-pc and small 2-pc rings with heat-set inserts) provides tool-free swap of any module, which is exactly what a multi-test-article programme needs.

### 1.2 Key Performance Figures

The acrylic window SVG dimensions confirm the test section cross-section: _80mm (H) × 130mm (W)_. This gives:

$$A_{TS} = 0.080 \times 0.130 = 0.0104 \text{ m}^2 = 104 \text{ cm}^2$$

Flow rate with the baseline Noctua NF-A14 IPPC-3000 at ~120 CFM loaded:

$$V_{TS} = \frac{Q}{A_{TS}} = \frac{0.0566 \text{ m}^3/\text{s}}{0.0104 \text{ m}^2} \approx 5.4 \text{ m/s} \quad (M \approx 0.016)$$

With the optional upgrade to an _AC Infinity Cloudline A8/S8/T8_ (200mm duct fan, ~250 CFM loaded):

$$V_{TS,upgrade} \approx 11.3 \text{ m/s} \quad (M \approx 0.033)$$

Dynamic pressure spans:

|Fan|$V_{TS}$|$q = \frac{1}{2}\rho V^2$|
|---|---|---|
|Noctua NF-A14 baseline|5.4 m/s|17.9 Pa (0.006 psi)|
|AC Infinity A8 upgrade|11.3 m/s|78.8 Pa (0.011 psi)|

These are very low dynamic pressures — appropriate for smoke visualization, qualitative comparison, and light load-cell measurements, but they cannot replicate flight Reynolds numbers. The delta to flight is quantified below and must be understood before any coefficient data is interpreted.

### 1.3 Limitations Relevant to the WYVERN Programme

Three limitations govern everything downstream:

_First — Reynolds number mismatch._ The flight maximum-$q$ condition at $V = 167.5$ m/s, $D = 70$ mm produces:

$$Re_{flight} = \frac{\rho V D}{\mu} = \frac{1.225 \times 167.5 \times 0.070}{1.789 \times 10^{-5}} = 8.03 \times 10^5$$

At tunnel conditions with a 1:3 scale model ($D_{model} = 23.3$ mm):

$$Re_{tunnel,baseline} = \frac{1.225 \times 5.4 \times 0.0233}{1.789 \times 10^{-5}} = 8.8 \times 10^3 \qquad (\text{ratio} = 0.011)$$

$$Re_{tunnel,upgrade} = \frac{1.225 \times 11.3 \times 0.0233}{1.789 \times 10^{-5}} = 1.8 \times 10^4 \qquad (\text{ratio} = 0.022)$$

This is a two-orders-of-magnitude gap. Flow topology — specifically laminar separation bubbles, transition location, and base wake structure — will differ from flight. The tunnel is _not_ a quantitative aerodynamic prediction tool for the WYVERN. It is a _qualitative flow visualization and relative comparison_ platform.

_Second — blockage._ At 7.5% blockage the industry standard correction is required; above 10% the wall-interference corrections become non-trivial and uncorrected $C_D$ values can be inflated by 20–40%. The 70mm full-scale WYVERN body alone occupies 37% of the test section area — physically impossible to test at 1:1.

_Third — test section length._ The standard frame appears to accommodate roughly one test section length of ~130–150mm. The full 1:3 rocket at 390mm OAL requires either a custom extended test section module or a fuselage-only stub with isolated fin assemblies — which is in fact the better test strategy anyway.

---

## 2. WYVERN Model Scale Selection

### 2.1 Blockage Constraint Analysis

The accepted blockage threshold for uncorrected low-speed tunnel measurements is $\leq 7.5%$; up to 10% is tolerable with the Maskell solid-body correction. Above that, the tunnel is only useful for visualization with no quantitative interpretation.

$$\text{Blockage} = \frac{A_{frontal,model}}{A_{TS}} \leq 0.075$$

Solving for maximum allowable body diameter:

$$D_{max} = 2\sqrt{\frac{0.075 \times A_{TS}}{\pi}} = 2\sqrt{\frac{0.075 \times 0.0104}{\pi}} = 31.5 \text{ mm}$$

This places the blockage-limited body diameter at 31.5mm, which maps to a scale of approximately 1:2.22 — but that only budgets blockage for the body alone, leaving nothing for fins. Accounting for fins in the full-rocket configuration, the _recommended programme scale is 1:3_, yielding:

|Dimension|Full Scale (PTD)|1:3 Model|
|---|---|---|
|Body OD|70.0mm|23.3mm|
|OAL|1,170mm|390mm|
|Nose cone length|234mm|78mm|
|Ring 1 fin root chord|93mm|31.0mm|
|Ring 1 fin tip chord|47mm|15.7mm|
|Ring 1 fin span|70mm|23.3mm|
|Ring 2 fin root chord|47mm|15.7mm|
|Ring 2 fin tip chord|23mm|7.7mm|
|Ring 2 fin span|35mm|11.7mm|

### 2.2 Per-Article Blockage at 1:3 Scale

The test article programme proceeds in four configurations of increasing complexity. Blockage values drive whether quantitative coefficient extraction is valid:

|Test Article|Frontal Area (cm²)|Blockage|Correction Required|
|---|---|---|---|
|Nose cone on sting (body only)|4.28|4.1%|None — valid|
|Single isolated fin panel (half-span wall mount)|5.44|5.2%|None — valid|
|Ring 2 fin assembly + body stub|6.97|6.7%|None — valid|
|Ring 1 fin assembly + body stub|15.17|14.6%|Maskell correction required|
|Full rocket (both rings, 0° AoA)|18.17|17.5%|Visualization only — no raw $C_D$|

The full-rocket configuration exceeds 10% at 1:3 scale. Two options: drop to 1:4 scale (reduces body to 17.5mm, $Re$ drops further) or accept visualization-only status for the full configuration. Given the $Re$ gap already present, _the visualization-only posture for the full-rocket article is the right call_. The nose cone and isolated fin articles are the quantitatively useful configurations.

---

## 3. Test Article Design Specifications

### 3.1 Mounting System

The base tunnel uses Gridfinity-compatible magnetic hot-swap floor mounts. All WYVERN articles should interface through:

_Floor-mounted sting:_ 4mm carbon fiber rod (matches the existing `model-base-for-aero-strut-with-dovetail-yaw-sector.stl` adapter) with a PETG-CF printed sting-to-body adapter for each article. The aero strut base already provides 0°, 5°, and 10° angle-of-attack setpoints via the hex sting profile — directly usable for the nose cone and full-body articles.

_Half-span wall mount:_ The existing `test-section-wall-for-half-span-model-support-with-print-in-place-aoa.stl` is ideal for isolated fin panel testing. The half-span approach eliminates the body-fin junction as a variable, allowing clean measurement of the fin panel aerodynamics alone.

Sting diameter constraint: $\leq 25%$ of model base diameter = $0.25 \times 23.3 = 5.8$ mm. A 4mm CF rod is compliant and provides adequate bending stiffness.

### 3.2 Test Article 1 — Von Karman Nose Cone

The nose cone model is the cleanest quantitative article in the programme. Blockage is 4.1%, well within the uncorrected limit. Smoke visualization will reveal the stagnation point, the laminar boundary layer developing over the ogive, and (with the laser sheet) the thin attached boundary layer that makes the Von Karman profile preferable to a simple conical nose.

_Print specification:_ PETG-CF, 0.2mm layer height, 2 perimeter walls (thin shell, 0.8mm wall), 0% infill (hollow), 4mm through-bore collinear with body axis for sting insertion. Total print mass approximately 8g.

The article directly validates the nose profile selection over a conical or power-series alternative — a comparison set of nose cone geometries at identical base diameter and length is low-cost and highly informative.

_AoA sweep:_ Use the existing 0°/5°/10° aero strut positions. At 10° the stagnation point shift on the ogive is clearly visible and the leeward separation (if any) will appear in smoke.

### 3.3 Test Article 2 — Isolated Fin Panel (Half-Span Wall Mount)

A single Ring 1 fin panel mounted to the sidewall with its root at the wall, operating as a half-span model. This eliminates body-fin junction interference and allows clean measurement of fin lift curve slope and stall characteristics.

The half-span approach means the wall acts as a symmetry plane — the aerodynamic behavior approximates a full fin panel with zero tip effects on the wall side. Effective aspect ratio is doubled relative to the isolated panel:

$$AR_{eff} = 2 \times \frac{2b}{c_r + c_t} = 2 \times \frac{2 \times 23.3}{31.0 + 15.7} = 2.0$$

This is close to the Barrowman value of $AR = 1.0$ per exposed semi-span used in the stability analysis — confirming the half-span wall test is the right analogue.

The print-in-place AoA wall ($\pm$several degrees, snap-adjustable) allows angle-of-attack sweeps. Smoke injection upstream will reveal:

- Attached flow at small AoA (confirms the double-wedge 4% t/c profile works)
- Separation bubble at the hinge line at large deflection (validates the ±25° limit and the 45% chord pivot placement)
- Leading edge separation onset (informs minimum fin actuation speed — below what airspeed fins lose authority?)

_Print specification:_ PETG-CF, 0.2mm layer height, 4 perimeter walls, 40% gyroid infill (matches PTD structural spec for comparable surface finish). Total mass approximately 12g including wall-mount bracket.

### 3.4 Test Article 3 — Ring 1 and Ring 2 Fin Assemblies (Body Stub)

Two separate articles: one for each fin ring, each consisting of a 100mm body stub section at 1:3 scale (23.3mm OD) with the full four-fin array installed at correct angular positions. The stub provides enough body length for the boundary layer to develop over the body before reaching the fin roots — approximately 4 body diameters of run length, which is minimal but adequate for visualization.

These articles test the body-fin junction aerodynamics: the horseshoe vortex at the fin root, the fin tip vortex, and the wake interaction between opposing fin pairs. At 45° roll (body rotated so the fin pair are at 45° to the flow), the interference between adjacent fins from the two rings is visible in smoke — this is the Ring 1/Ring 2 clocking interaction the Barrowman analysis assumes away.

The Ring 1 assembly at 14.6% blockage requires the Maskell correction if $C_D$ values are to be extracted:

$$C_{D,corr} = C_{D,meas} \left(1 - \frac{A_{frontal}}{A_{TS}}\right)^2$$

At 14.6% blockage, the correction factor is $(1-0.146)^2 = 0.729$ — a 27% reduction in the measured drag coefficient. This correction is applied to reduce the drag to what would be measured in an unconfined flow. Without it, any drag coefficient extracted is meaningless. For visualization purposes only, no correction is needed.

### 3.5 Test Article 4 — Full 1:3 Scale WYVERN (Visualization Only)

The complete vehicle at 1:3 scale: 23.3mm body, both fin rings, Von Karman nose cone, total OAL 390mm. This exceeds the ~150mm test section length available in the standard frame, which means _only the aft 150mm of the vehicle fits in the test section at one time_ — a serious architectural constraint.

Two practical approaches:

_Approach A — Split test._ Print two sub-articles: forward body + Ring 2 (approximately 200mm), and aft body + Ring 1 (approximately 190mm). Test each half in the test section separately. Allows smoke visualization of each fin ring independently in context.

_Approach B — Extended test section module._ The tunnel's modular junction ring system allows insertion of a custom 400mm extended test section module (essentially a longer version of part 3 — the basic duct section, but with the test section's acrylic window slots). This is a straightforward remix of the existing STL files — just extend the prismatic section. Requires a printer with a 400mm Z axis (Bambu X1 can do 256mm; a Bambu P1S or Prusa XL can reach the required height in two sections joined by the existing junction rings).

Approach B is strongly preferred — it gives a single continuous visualization of the full vehicle wake and the two-ring fin interaction at all angles of attack.

At this scale and blockage (17.5%), the aerodynamics are visualization-only: confirmation of attached flow over the ogive, smoke tracing through the fin ring gaps, visualization of the booster/sustainer junction geometry, and qualitative confirmation that the aft fin ring produces attached spanwise flow at low AoA.

---

## 4. Test Programme Sequence

The four articles above map to a natural test progression, each building on the previous:

|Test|Article|Primary Objective|Method|Quantitative?|
|---|---|---|---|---|
|T-1|Nose cone|Boundary layer development, stagnation point|Smoke + laser sheet|Yes ($C_D$ extraction)|
|T-2|Single fin panel (half-span)|Fin lift curve slope, stall AoA, hinge separation|Smoke + AoA sweep|Yes (relative $C_L$)|
|T-3a|Ring 2 assembly + body stub|Body-fin junction, tip vortex|Smoke + laser|Visualization|
|T-3b|Ring 1 assembly + body stub|Body-fin junction, ring spacing interaction|Smoke + laser|Visualization|
|T-4|Full vehicle (approach A or B)|Complete wake topology, two-ring interaction|Smoke sweep|Visualization only|

### 4.1 Instrumentation Recommendations

For quantitative force data on T-1 and T-2, the force levels are small but manageable:

$$F_{drag,T-1} = q \cdot A_{nose} \cdot C_{D,nose} \approx 78.8 \times 4.28 \times 10^{-4} \times 0.04 \approx 1.3 \text{ mN}$$

$$F_{lift,T-2} = q \cdot S_{fin} \cdot C_L \approx 78.8 \times 5.44 \times 10^{-4} \times 0.5 \approx 21 \text{ mN}$$

A _TAL221 50g load cell_ driven by an _HX711 24-bit ADC_ and logged to any microcontroller (including an RP2040) is a perfectly appropriate and programmatically consistent choice. Resolution at 80 dB gain is approximately 0.4 mN — sufficient to resolve the drag on the nose cone and the lift on the fin panel. Mount the load cell in series with the sting, zero before each run, log at 10Hz, average over 10 seconds per point to suppress tunnel turbulence noise.

For smoke: the _Vosentech MicroFogger 5 Pro_ (cited in the source design) is adequate. Injection at the smoke-strut section upstream of the contraction produces clean streaklines by the time the flow reaches the test section.

For visualization enhancement: the _OxLasers 520nm laser line generator_ on the existing ceiling gantry produces a thin horizontal sheet that can be swept vertically to isolate specific spanwise stations. This is particularly useful for resolving the Ring 1/Ring 2 tip vortex interaction at the clocking plane.

---

## 5. Fabrication Specifications for WYVERN Test Articles

All articles are printed in _PETG-CF 20% CF_ to match the PTD structural material and to obtain a consistent surface finish across all models. ABS or standard PLA would introduce different surface roughness characteristics at the model scale, which at these Reynolds numbers noticeably affects boundary layer transition location.

|Article|Material|Layer Height|Walls|Infill|Est. Mass|Est. Print Time|
|---|---|---|---|---|---|---|
|Nose cone (1:3)|PETG-CF|0.15mm|2|0% hollow|~8g|~2.5h|
|Single fin panel + wall bracket|PETG-CF|0.15mm|4|40% gyroid|~12g|~3.5h|
|Ring 1 fin assembly + body stub|PETG-CF|0.15mm|3|20% gyroid|~25g|~7h|
|Ring 2 fin assembly + body stub|PETG-CF|0.15mm|3|20% gyroid|~18g|~5h|
|Full rocket body (two halves)|PETG-CF|0.20mm|2|10% gyroid|~45g|~12h|
|Sting adapter (Gridfinity base)|PETG|0.20mm|4|40%|~5g|~1h|
|AoA wall bracket (nose cone)|PETG|0.20mm|4|40%|~6g|~1.5h|

Total material: approximately 119g PETG-CF at approximately $3.81 in filament cost — negligible against the $632 vehicle build cost.

Use _0.15mm layer height_ on all aerodynamically-critical surfaces (nose cone, fin panels) to minimize surface roughness. At 1:3 scale, a 0.20mm layer is 0.60mm full-scale — a realistic surface flaw. Dropping to 0.15mm brings this to 0.45mm equivalent, which is still rough by full-scale aircraft standards but acceptable for educational visualization at this $Re$ regime.

Sand all external aerodynamic surfaces through 400 grit and apply two coats of _Rust-Oleum 2X primer_ spray. This reduces equivalent sand-grain roughness from approximately 50μm to approximately 5μm, keeping the surface in the hydraulically smooth regime for $Re < 10^5$.

---

## 6. Upgrade Recommendations Specific to the WYVERN Programme

The stock tunnel is adequate for nose cone and isolated fin work. Two targeted upgrades push it significantly further.

_Fan upgrade — AC Infinity Cloudline A8._ The upgrade doubles test section velocity from 5.4 to ~11.3 m/s and nearly doubles dynamic pressure. The upgrade diffuser STL (already in the archive) is designed for this fan and requires printing only two additional parts. Cost is approximately $80. For WYVERN testing this is essentially mandatory — at baseline velocity, the fin hinge forces are less than 2 mN and the load cell signal-to-noise ratio at 10Hz logging is borderline. At upgrade velocity the forces are 4× higher and the HX711 can reliably resolve them.

_Extended test section module._ A custom 400mm extended test section that replaces the stock 130mm frame. This is a parametric extension of `6-test-section-frame.stl` — add 270mm of prismatic cross-section with window slots on all four faces at 80mm × 400mm. Print in three junction-ring-coupled segments if build volume is limited. This enables T-4 as a proper single-article test rather than a split-article approximation. Design cost is approximately 4 hours of CAD time in any slicer-compatible modelling tool.

_Force balance integration._ The sting mount on the existing Gridfinity aero-strut base has a 6mm hex hole for roll indexing. A 4mm CF rod insert bonded into a PETG-CF adapter with a TAL221 load cell in-line and a waterproof JST-GH connector (already the programme's standard connector) passing through the test section floor makes the instrumentation fully hot-swappable and consistent with the existing avionics wiring standard.

---

## 7. Summary of Limitations and What the Data Is Worth

The WYVERN tunnel programme will not produce flight-representative aerodynamic coefficients. The two-decade Reynolds number gap means the tunnel drag numbers should not be used to calibrate OpenRocket models or validate the Barrowman $C_N$ calculations. What the tunnel _will_ produce, at low cost and before first flight, is genuinely useful:

Confirmation that the _Von Karman ogive produces attached flow_ without separation over the full AoA range tested — if separation is visible at 10° in the tunnel, it will certainly occur in flight at the same AoA regardless of Reynolds number.

Confirmation that the _fin panels are free of leading-edge separation bubbles at small deflection angles_ — the double-wedge 4% t/c profile at $AR \approx 1.0$ is known to be separation-resistant but the junction region with the body is less predictable.

Visualization of the _Ring 1/Ring 2 clocking interaction wake_ — the 45° offset between rings creates an interdigitated fin tip vortex field in the wake that OpenRocket does not model and that no hand calculation captures. This is exactly the kind of insight a flow visualization tunnel provides that analysis cannot.

Evidence that the _aft fin root/gimbal bay junction is not creating separated flow_ that would degrade control effectiveness — the 15mm annulus with protruding servo linkage hardware is geometrically messy and worth checking in smoke.

Any anomalous result from the tunnel is a prompt to revisit the design or adjust the OpenRocket model, not a direct coefficient replacement.




The tunnel is designed ground-up around the WYVERN test programme constraints rather than adapted from the STEM reference design. The key decisions and their justification:

_Test section 150 × 150 mm square._ The STEM tunnel's 80 × 130 mm section put the full 1:3 rocket at 17.5% blockage — uncorrectable. The new section brings the full rocket at 0° AoA to 7.9%, which is Maskell-correctable, and isolated fin assemblies below 7%. The square cross-section also means roll sweeps are geometrically consistent at all roll angles, which matters for the 45° Ring 1/Ring 2 clocking tests.

_9:1 contraction ratio._ The STEM tunnel uses 4:1, which gives a turbulence intensity of roughly 0.5–1.0% in the test section. Upgrading to 9:1 with two-screen conditioning brings estimated TI to 0.21%, which is the difference between seeing laminar separation bubbles in smoke (requires TI < 0.3%) and watching them smear into turbulent noise. The downside is a 900 mm contraction cone — the dominant length driver on the 2.47 m OAL.

_Bell 5th-order polynomial contraction profile._ The zero-slope, zero-curvature boundary conditions at both ends guarantee no adverse pressure gradient at either junction. A simpler linear or cubic taper would produce inflection-point separation on the contraction walls at high contraction ratios — particularly dangerous at 9:1.

_4° diffuser half-angle._ Barlow, Rae and Pope (1999) place the separation threshold at ~4–5° for a turbulent boundary layer. At 4.0° exactly the diffuser recovers static pressure without separation. The square-to-circle transition is handled by linearly growing the corner radius from 0 to 100 mm over the 220 mm diffuser length, maintaining mass conservation at each station.

_Contraction print strategy._ The 450 × 450 mm settling chamber exterior is 456 × 456 mm — impossible as a single print on any home machine. The solution is six 150 mm-long tunnel sections each with a 156 × 156 mm exterior cross-section, all of which fit on a 180 mm bed. The taper from 450 to 150 mm internal is distributed across these sections per the Bell polynomial table. The Bambu X1 or Prusa XL is only required for the diffuser.

The $433 total is well within the PDR-002 programme budget context and represents roughly one replacement set of motors.