# GTR70E WYVERN, Structural & Thermal Analysis (first-order FEA)

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


*First-order analytical margins from `../Simulations/we4_analysis.py` → `plots4/08_fea_loads.png`,
`09_thermal.png`. A 25 N motor on a 70 mm tube is handling/print-limited, not load-limited.*

## 1. Load cases
| Case | Source | Magnitude |
|---|---|---|
| Axial compression | F15 peak thrust | 25.3 N |
| Bending (TVC) | side force at ±8° gimbal | $25.3\sin8°=3.5$ N at the nozzle |
| Bulkhead A | reaction of the gimbal mount | 3.5 N + thrust transfer |
| Gimbal pivot | side load through 2 mm pins | 3.5 N |

## 2. Stresses & margins (yield: ASA ~30 MPa, PETG-CF ~60 MPa)
- **Tube axial:** $\sigma=F/(\pi D\,t)=25.3/(\pi\cdot0.070\cdot0.0016)=72$ kPa → SF vs ASA ≈ **400×**.
- **Tube bending:** $M=3.5\times0.16=0.56$ N·m, $\sigma=Mc/I$ with $I=\pi/64(D^4-d^4)$ → ~0.2 MPa → SF **>100×**.
- **Gimbal pivot / Bulkhead A (PETG-CF):** SF **>50×**.
- **Minimum SF across the structure: ~340×.** The airframe wall (1.6 mm) is set by printability and
  handling robustness, not flight loads, there is no structural reason to go thicker.

## 3. Thermal (engine-bay PETG-CF wall, F15 3.45 s burn)
Lumped-wall transient with a **0.5 mm phenolic motor liner** as the thermal barrier (liner-reduced
inner driving temp ~180 °C, $h\approx120$ W/m²K): engine-bay wall peaks **~47 °C**, well under
PETG-CF's ~110 °C HDT, the flight F15 case has wide margin. On the *static stand* (not in the vehicle),
the steel deflector + phenolic liner protect the mounts against the plume.

## 4. Recovery ejection loads at the bulkhead separation joint (F15-4 motor ejection)

Recovery is by the F15-4's built-in ejection charge, separating the two body tubes at a single
bulkhead joint (see `WYVERN_E4_Recovery.md`). The gas path is directly across that joint, with no
intermediate routing between it and the pressurized volume. The joint is meant to *release* at a
controlled 50–150 N (`WYVERN_E4_Recovery.md` §4), so it needs friction-fit/shear-pin sizing
calibrated to let go at that target, not bolted hardware sized to survive indefinitely — a genuine
open engineering decision (pin/friction-fit sizing under the ~140 kPa ejection pulse), not something
to invent a number for here.

**4.1 Bulkhead joint (PETG-CF), ejection pressure.** The recovery-side volume pressurizes to
$p\approx140$ kPa (feasibility sim; re-verify against the current two-BT volume before treating as
final), acting across a bulkhead of bore radius $r=33.4$ mm, thickness $t=4$ mm:
- **Net force on bulkhead:** $F=p\,\pi r^2 = 140{,}000\times\pi(0.0334)^2 = \mathbf{491\ N}$.
- **Plate bending (clamped-edge circular plate), as an upper-bound check if the joint didn't
  release:** $\sigma_{max}=\tfrac{3pr^2}{4t^2}=\tfrac{3(0.14)(0.0334)^2}{4(0.004)^2}=\mathbf{7.3\ MPa}$
  → SF vs PETG-CF (60 MPa) ≈ **8.2×**, comfortable margin if the joint ever fails to release cleanly.
- This 491 N/140 kPa figure is the driving load for the friction-fit or shear-pin sizing pass
  against the 50–150 N release-force target — that sizing pass itself is still open.

**4.2 Bulkhead joint, thermal.** The bulkhead joint is the direct-gas-exposure surface for the
ejection pulse, so it needs a thermal check for the PETG-CF bulkhead's brief (~0.1 s) exposure to
the 200–300 °C ejection gas. Not yet run for the bulkhead's actual geometry. Wadding on both
bulkhead faces (`WYVERN_E4_Recovery.md` §7) is the near-term thermal mitigation regardless of what
that check finds.

## 5. Modal / dynamics note
The body is short (0.672 m) and stiff relative to the loads; first lateral bending mode is well above
the ~10 Hz TVC control bandwidth, so no structural–control coupling. (A full modal FEM is listed as
future work; first-order separation is comfortable.)

## 6. Conclusion
Structurally over-margined on the flight loads (min SF ~340×). Recovery loads still need a release-
force sizing pass at the bulkhead joint (§4.1) and a direct-gas-exposure thermal check (§4.2); both
are open items. The design drivers remain **mass** (ASA-Aero/PETG-CF zoning, PC-FR only at the
motor mount and gimbal where heat or ejection pressure demands it, to keep T/W up) and **CG/
control-arm** (TVC authority) for the flight-load side; the recovery side is driven by
**release-force calibration**, not survival strength.
