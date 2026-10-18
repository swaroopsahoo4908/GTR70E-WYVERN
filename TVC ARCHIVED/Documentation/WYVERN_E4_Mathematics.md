# GTR70E WYVERN, Mathematics & Mass Budget

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


*All values from `../Simulations/we4_sim.py`. Single-stage finned F15-4 TVC sustainer (motor-ejection
recovery via two-body-tube separation at the bulkhead joint), 70 mm OD.*

This is a bottom-up mass build against the two-body-tube CAD (`3D parts/_generator/mass_report.json`)
and the custom-the flight computer avionics stack. The onboard TPS564201 buck regulates the 2S pack directly, so
there's no separate UBEC line in the power budget.

## 1. Mass budget

Material zoning: ASA-Aero (foamed, 0.65 g/cm³) for the Upper BT (avionics housing) and the Lower BT
tube (chute/TVC bay); PETG-CF (1.30 g/cm³) for the fins and the bulkhead joint (the direct
ejection-gas-exposure part, at the higher-strength material); PC-FR (1.20 g/cm³) for the TVC
assembly proper (motor mount, gimbal — the thermal zone nearest the nozzle). The Lower BT is
hoop-stress-checked against the 140 kPa ejection pulse: σ = p·r/t = 2.93 MPa, SF ≈ 6–10× on
ASA-Aero depending on foamed-vs-solid strength assumption — comfortable margin, consistent with the
"structurally over-margined" conclusion `WYVERN_E4_FEA_Structural.md` §6 reaches for the flight
loads. Structural rows below are real CAD output, not scaled estimates.

| Section | Items | Mass |
|---|---|---|
| Nose (ASA-Aero) | ellipsoid nose cone | 20.9 g |
| Upper BT tube (ASA-Aero) | avionics housing, incl. 4x M3 the flight computer standoff bosses (Ø62 mm board) | 44.9 g |
| Lower BT tube (ASA-Aero) | chute/TVC bay, one continuous tube | 94.2 g |
| Bulkhead joint (PETG-CF) | direct gas-exposure release joint | 17.2 g |
| Motor mount (PC-FR) | 29 mm motor mount + centering rings | 57.7 g |
| TVC gimbal assy (PC-FR) | 2-axis gimbal | 105.6 g |
| Fins ×4 (PETG-CF, 87 mm) | bonded root joint | 70.8 g |
| Rail buttons ×2 (PETG-CF) | | 1.2 g |
| **Structure subtotal** | | **412.5 g** |
| Recovery | chute (24 in) + cord + swivel 58 g, Nomex protector 6 g, wadding 6 g | 70 g |
| Avionics | Pico 2 W perfboard assembly (Ø62 mm, self-estimated) 14 g, external BNO085 breakout+cable 4 g, µSD 0.5 g, i3 4K cam 36 g, 2S 450 mAh LiPo 27 g, wiring/connectors 8 g | 89.5 g |
| Actuation | 2× EMAX ES08MA II servo, 12 g ea (datasheet) | 24 g |
| **Dry total** | | **618.3 g airframe + 42 g spent motor casing = 660 g** |
| Motor | Estes F15-4 loaded (60 g propellant + 42 g casing) | 102 g |
| **Liftoff** | | **720 g** |

The Pico 2 W perfboard assembly mass (14 g) is a component-level self-estimate — bare Ø62 mm 2-layer FR4
board (~8.9 g, volume × 1.85 g/cm³) plus populated parts (~5.2 g: USB-C connector, slide switch,
fuse, RP2350 QFN-80, 6–7 small sensor/PMIC packages, 4× JST, STEMMA-QT, H1 header, buck inductor,
~40 passives) — not a bench scale reading. The 2S 450 mAh LiPo (27 g) is a comparable-product
estimate (no published weight found for the specific pack); replace both with real weights if a
scale reading ever contradicts them.

Liftoff comes in at **720 g**, comfortably under the 705 g planning target, while still carrying the
87 mm fins and the full custom-the flight computer avionics stack.

## 2. CG, inertia, control arm

$$x_{cg}=\frac{\sum m_i x_i}{\sum m_i}=50.1\ \mathrm{cm\ (liftoff)},\ 48.4\ \mathrm{cm\ (burnout)};\quad
I_{yy}=\sum m_i (x_i-x_{cg})^2 + \tfrac14 m r^2 = 0.0262\ \mathrm{kg\,m^2}$$

Gimbal pivot at 62 cm from the nose → **control arm $L=x_{pivot}-x_{cg}=11.9$ cm (liftoff), 13.6 cm
(burnout)**. The vehicle is *finned*, so it also carries a real static margin: CP at 53.3 cm (87 mm
fins) gives **+1.14 cal** at liftoff, rising toward 1.5 cal at burnout as the CG moves forward.
Stability is therefore hybrid: passive fins through the ignition transient, active TVC from t = 0.5 s.

## 3. Thrust-to-weight

$$\mathrm{(T/W)_{avg}}=\frac{14.4}{0.7203\cdot 9.81}=2.10,\qquad \mathrm{(T/W)_{peak}}=\frac{25.3}{0.7203\cdot 9.81}=3.70$$

The F15 black-powder curve is front-loaded (25.3 N spike → ~14 N sustain), so the rocket gets a
**3.70** T/W kick off the rail, then holds ~2.10 — comfortable margin for a TVC launch.

## 4. Trajectory (RK4 + Barrowman engine)
*Solved by `we4_flightsim.py`, 4th-order Runge-Kutta (dt = 2x10⁻⁴ s) with Barrowman drag buildup;
finned ⇒ static margin +1.14 cal, with active TVC taking over at t = 0.5 s.*
 (RK4 point mass, Cd = 0.539, A = π(0.0435)² m², 87 mm fins)

Burnout 3.45 s at **74.0 m, 36.3 m/s**; coast to apogee **124.6 m / ~409 ft at t = 6.72 s** (unified
RK4 + Barrowman engine, `we4_flightsim.py`, Cd 0.539). Monte-Carlo dispersion in `we4_validation.py`:
100% of dispersed flights stay stable (≥0.5 cal) and land under 35 m/s. Still low and no-waiver
(< 125 g propellant, < G, < 1.5 kg).

## 5. TVC control (rigid-body pitch, servo lag τ=0.04 s, PID)

$$I_{yy}\dot q = T\sin\delta\,L - T\sin(1°)L_{\text{(misalign)}},\quad \dot\theta=q,\quad
\delta=\mathrm{clip}(K_p e+K_i\!\int\! e+K_d\dot e,\ \pm5°)$$

The loop stabilizes to vertical then tracks a 4° commanded maneuver with the **gimbal staying inside
±8°** and peak pitch deviation <4°. Control authority (restoring moment $T\sin8°\,L$ vs a 2°-AoA-
equivalent disturbance) is **positive throughout the burn and falls to zero only as thrust → 0 at
burnout**, which is exactly why recovery is forced right after burnout (no thrust ⇒ no control on a
finned body plus the gimbal). See `plots4/03_tvc_control.png`, `04_control_authority.png`.

## 6. Recovery

Deploy is by the **F15-4 motor ejection charge**, fired 4 s after burnout at **t ≈ 7.45 s** (0.58 s
past apogee), pressurizing the Lower BT and **separating the two body tubes at the bulkhead joint**
(see `WYVERN_E4_Recovery.md`); the finned uncontrolled body can tumble far before that. At burnout
the vehicle is still climbing at **~36 m/s**; size the chute/cord for a hard opening, or push the
timer if a softer opening is preferred. A **24″ chute** gives terminal **~4.7 m/s**:

$$v_t=\sqrt{\frac{2 m g}{\rho\,C_d A_{chute}}}=\sqrt{\frac{2(0.6603)(9.81)}{1.225(1.5)\pi(0.3048)^2}}\approx 4.7\ \mathrm{m/s}$$

Recovery is a single passive event (the motor's own charge), there is no electronic deploy path or
backup channel; robustness comes from the bay-pressurization margin against the bulkhead joint's
release-force target (see `WYVERN_E4_Recovery.md` §4, §6).

## 7. No-waiver / class

Single F15-4: 49.6 N·s, 60 g propellant, < 125 g cap, ≤ F class, liftoff 720 g < 1500 g → FAA
Class-1, no waiver, no L1 cert.

## References

CEVA, Inc. (2023). *BNO08X datasheet* (Rev. 1.17). https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf

EMAX. (n.d.). *ES08MA II 12 g mini metal gear analog servo* [Product specification]. Retrieved August 12, 2026, from https://www.getfpv.com/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model.html

Estes Industries. (n.d.). *F15-4 engines* [Product specification]. Retrieved August 12, 2026, from https://estesrockets.com/products/f15-4-engines

Federal Aviation Administration. (n.d.). *14 CFR Part 101 — Moored balloons, kites, amateur rockets, and unmanned free balloons*. Electronic Code of Federal Regulations. https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101

National Fire Protection Association. (2018). *NFPA 1122: Code for model rocketry*. https://www.nfpa.org/product/nfpa-1122-code/p1122code

Raspberry Pi Ltd. (2024). *RP2350 datasheet*. https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

Texas Instruments. (n.d.). *TPS564201: 4.5-V to 17-V input, 4-A synchronous step-down voltage regulator* (SLVSFB5) [Datasheet]. https://www.ti.com/lit/ds/symlink/tps564201.pdf
