# GTR70E WYVERN, Ground Test Stands & Motor Plan

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


Four instrumented ground-test rigs, one per research question that needs physical validation before
flight: static fire (RQ2 materials + calibration), servo TVC stand (RQ1/RQ5), magnetic TVC stand
(RQ1/RQ5), wind tunnel (RQ3/RQ4). Jetvane testing runs on the static-fire stand as a materials
screen. A fifth fixture, the RQ2 bend-to-fracture bench rig in section 5, is uninstrumented dead
weight and needs neither a motor nor a load cell.

## 1. Static fire test stand, calibration, thrust curves, jetvane materials screen
Axial-only load path (1x 5 kg cell + HX711) with a **steel blast deflector**, sized for the F15-0's
3.45 s burn thermal case. Three jobs run on this one stand:

- **RQ1 baseline**: total impulse, average and peak thrust, burn time and curve shape for the
  F15-0, the reference curve both TVC stands are compared against.
- **Stand/DAQ calibration**: known hanging masses calibrate the load cell before every firing
  campaign; E16-4 commissioning firings validate the calibrated chain against a published curve.
- **RQ2 jetvane blast-shield screen**: this is a materials screen, not a
  vane-deflection test. A flat coupon plate of each candidate material, 5 mm thick and printed at
  100% infill, is mounted directly in the exhaust path like a blast shield and fired on. The motor
  runs straight into the plate; the response is melt-through, surface ablation depth, and slag
  buildup, not thrust or deflection. Five materials go through the screen: PLA, PETG-CF,
  ASA-Aero, PC, and PC-FR. ABS was dropped from the program 2026-08-14. Any material that survives
  5 mm without melting through gets retested at 4 mm, then 3 mm, then 2 mm, until it fails, giving
  a failure-thickness ranking across the five candidates rather than a single pass/fail. The BME688 already on the stand logs plume-adjacent
  temperature alongside each firing so the melt/slag result has a temperature record to go with it.

## 2. Servo TVC test stand
The servo-gimbal actuator bolts to a thrust block restrained from a fixed base by **three
strain-gauge load cells through flexures**: one **axial (Z)** and two **lateral (X, Y)**. Resolves
the full thrust vector, magnitude *and* direction:

$$T=\sqrt{F_x^2+F_y^2+F_z^2},\quad \theta=\arctan\frac{\sqrt{F_x^2+F_y^2}}{F_z},\quad
\phi=\operatorname{atan2}(F_y,F_x)$$

Sized for the small motors here: **F15 peak 25.3 N**, side force at ±8° ≈ **3.5 N** → a **5 kg
axial + two 1 kg lateral** cells + 3× HX711 → a Raspberry Pi Pico / Pico 2 W DAQ at 80 SPS. Logging
commanded vs measured (θ, φ) gives bandwidth, slew, overshoot, and steady-state error for the servo
system, this is the rig the flight vehicle's actual TVC gets qualified on (`wyvern4_gse_servo_rig`).

One HX711 per axis is not optional. The part multiplexes its two channels through a single ADC and
needs settling time after a channel switch, so sharing one chip across two axes forfeits
simultaneous sampling and smears the vector reconstruction. Program total is four: three here, one
on the static stand. Strap RATE high for 80 SPS rather than the 10 SPS default; at 80 SPS the 3.45 s
F15 burn yields roughly 275 samples, of which only about 16 land on the ignition transient, so treat
the reported peak as a lower bound and the total impulse as the trustworthy figure.

No bend-rig cell is carried. The program's cell count is four: two 1 kg lateral, two 5 kg axial.
RQ2's structural half runs as a dead-weight bend-to-fracture test with no load cell at all, spec'd
in section 5.

## 3. Magnetic TVC test stand
A second, physically separate rig (`gtr70e_wyvern_gse_solenoid_rig`) using the same three-load-cell
flexure and DAQ chain as the servo stand, but with the magnetic-solenoid gimbal actuator in place
of the servo gimbal. Running the identical instrumentation chain on both stands is what makes the
**RQ1 magnetic-vs-servo A/B comparison** valid, commanded vs measured (θ, φ) from each stand feed
directly into the same bandwidth/slew/overshoot/steady-state-error metrics for a like-for-like
comparison. Only the servo system flies (RQ1 answers which actuation type wins on the bench; the
flight vehicle carries the winner's specs into the record either way).

## 4. Wind tunnel, aerofoil performance testing (RQ3/RQ4)
Bench aerofoil rig (`Wind Tunnel/`) for direct measurement of fin aerofoil performance, 
lift/drag/stall behavior across the flown fin's angle-of-attack range, to calibrate against the
Barrowman-derived stability numbers in `WYVERN_E4_Stability_FinSizing.md`. This is the RQ4
wind-tunnel-vs-flight comparison: tunnel-measured coefficients here, flight-derived weathercocking
and stability margin from telemetry (`Simulations/plots_val/05_wind_weathercock.png`) after launch.
Feeds RQ3 (fin aerofoil selection) directly, whichever aerofoil the tunnel run favors is the one
committed to the flown fin can.

## 5. RQ2 bench bend-to-fracture fixture

Not a motor stand and not instrumented. A printed coupon is simply supported on two rollers, a
string and hanger yoke hangs from mid-span, and dead weight is added in steps until the coupon
snaps. The force reference is gravity, which is a better standard than a load cell that would
itself have been calibrated with known masses. Reported result is the mass at fracture, converted
to flexural strength.

| Parameter | Value |
|---|---|
| Coupon | 2.0 mm thick × 15 mm wide × 100 mm long, printed flat, identical parameters across materials |
| Support | two 6 mm rollers, 80 mm span, simply supported |
| Load | string + hanger yoke at mid-span, dead weight in steps |
| Design ceiling | 6 kg (59 N) |
| Samples | 5 coupons per material, 5 materials, 25 total |

Flexural strength at fracture follows from the simply-supported mid-span load case:

$$\sigma_f=\frac{3FL}{2bd^2}=\frac{3(0.080)}{2(0.015)(0.002)^2}F$$

which reduces to a clean conversion for this exact geometry: 2.0 MPa per newton, or

$$\sigma_f\;[\text{MPa}]=19.6\,m\;[\text{kg}]$$

Every kilogram hanging on the yoke is 19.6 MPa of flexural stress in the coupon. The 6 kg ceiling
corresponds to 118 MPa, above every candidate's published flexural strength, so the fixture cannot
be the limiting element.

Predicted fracture masses, from published FDM flexural strengths for each class:

| Material | Flexural strength (printed, typ.) | Predicted fracture mass |
|---|---|---|
| PC | 85–100 MPa | 4.3–5.1 kg |
| PC-FR | 80–95 MPa | 4.1–4.8 kg |
| PLA | 70–90 MPa | 3.6–4.6 kg |
| PETG-CF | 60–80 MPa | 3.1–4.1 kg |
| ASA-Aero (foamed) | 20–35 MPa | 1.0–1.8 kg |

Printed flat with the layers perpendicular to the load, interlayer adhesion rather than bulk
strength governs, so expect real fractures 20–40 % below these numbers. Working range is roughly
0.9 to 4 kg. Load in 500 g steps to bracket the failure, then bisect in 100 g steps on the
remaining coupons of that material.

Mid-span deflection at fracture runs 9 to 22 mm depending on modulus, so leave 40 mm of clearance
under the coupon and expect the weight to drop that far the instant it snaps. Land it on foam or
sand from under 100 mm, wear eye protection, and keep hands and feet out from under the yoke —
PC-FR and PETG-CF fail brittle and throw fragments.

## 6. Motor plan & counts (verified specs, jetvane blast-shield screen included)
| Motor | Spec (verified) | Use |
|---|---|---|
| **Estes F15-4** | 49.6 N.s, 14.4 N avg / 25.3 N pk, 3.45 s, 4 s delay + ejection | **flight only** (ejection charge = recovery) |
| **Estes F15-0** | 49.6 N.s, 14.4 N avg / 25.3 N pk, 3.45 s, 0-delay (plugged) | **ground stands** (no ejection into fixtures) |
| **Estes/AeroTech E16-4** | ~16 N avg, E-class | stand commissioning firings |

**Counts:**
- *F15-4* = **4 (flight only)**: the ejection charge is the recovery system.
- *F15-0 (plugged)* = **13-20** for ground, split three ways: 6 TVC-stand firings (3 servo + 3
  magnetic), 2 static thrust-curve firings, and the jetvane blast-shield screen, which is adaptive
  rather than a fixed count. Five materials at up to 4 thickness steps each (5/4/3/2 mm, stopping at
  first melt-through) tops out at 20 firings if every material survives to 2 mm; in practice most
  candidates are expected to fail by 4 mm, so budget for roughly 10-14 firings and treat 20 as the
  worst-case ceiling. Plan for **13 firings as the low estimate plus a spares allowance for repeats**.
  Ground fixtures use the 0-delay F15-0 so no ejection charge fires into the stand; the thrust curve
  is identical to the F15-4 (same F15 propellant), so ground data transfers directly to the flight motor.
- *E16-4 (calibration)* = **6 recommended** (3 per TVC stand for repeatability); **4 is the floor**
  (2/stand). Load cells are *calibrated* with known hanging masses, free and precise; the E16 firings
  *commission and validate* the calibrated stand against a published curve.

## 7. Data paths
Static fire + both TVC stands → `Data/Motor (thrust curves)/` and `Data/TVC (vector + control)/`.
Wind tunnel → `Data/Wind Tunnel/`.
