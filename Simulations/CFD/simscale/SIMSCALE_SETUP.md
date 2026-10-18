# SimScale CFD package: fin profiles and control authority

_Generated geometry: `geometry/` (run `python3 gen_simscale.py` after any change in `wf_core.py`). Model predictions to check against: `predictions.csv`. Case list and reference values: `manifest.json`._

## What the free plan allows, and how the matrix fits it

SimScale's Community plan gives one user up to 2000 core hours, 10 unrestricted simulations (after that the results are qualitative only), a 16-core largest machine and no private projects, so anything you run there is publicly visible ([SimScale pricing](https://www.simscale.com/pricing/)). The matrix below is exactly ten runs, so the first pass uses the whole allowance. If you want headroom for a re-run, drop A7 (the flat plate sits between NACA0006 and the double wedge in every model).

| Case | Geometry | Question it answers | Model prediction |
|---|---|---|---|
| A1 | NACA0006 H40, δ 0°, 12 m/s, tunnel duct | zero offset / tare | 0 mN |
| A2 | NACA0006 H40, δ 5° | lift slope | 24.5 mN, hinge moment 0.19 mN m |
| A3 | NACA0006 H40, δ 10° | slope, CP | 49.7 mN, 0.38 mN m |
| A4 | NACA0006 H40, δ 15° | curvature (vortex lift or early stall) | 74.2 mN, 0.57 mN m |
| A5 | double wedge H40, δ 10° | RQ1: sharp-edge vortex lift | 55.2 mN |
| A6 | NACA0012 H40, δ 10° | RQ1: thick section | 47.6 mN |
| A7 | flat plate H40, δ 10° | RQ1 | 51.1 mN |
| R1 | full rocket (rev 3d: H45 fins, 81 x 20 mm stabilizers), α 0, pitch pair +10°, 60 m/s | installed authority | 3.20 N side force, 0.515 N m about the CG |
| R2 | R1 without stabilizers | SQ1: stabilizer vortex load (R1 minus R2) | 3.55 N, 0.609 N m |
| R3 | full rocket, α 4° about the CG, fins neutral, 60 m/s | normal-force slope, CP, margin | 2.90 N, 0.170 N m restoring; CNα 7.25 /rad, CP at station 418 mm |

The R1/R2 pair matters most. With the rev 3d 20 mm stabilizers, the project's vortex-interference model says they cancel 10 % of the pair's side force and 15 % of its pitching moment (it was 26 % and about half with the old 40 mm stabilizers, which is why they were cut down). That model is a single rolled-up vortex and was written down as pessimistic. If R1 comes back much closer to R2 than predicted, the rocket has more authority than the flight sim assumes; if it comes back further, the rev 3d authority gain is smaller than claimed.

## Files per case

- `<case>_fluid.step`: the flow region itself (a duct or box with the body cut out). Upload it and use it as is. This is the quickest path.
- `<case>_solids.step`: just the solid bodies (named parts), if you would rather build the flow region in SimScale's CAD Edit (Flow volume → External) ([SimScale docs](https://www.simscale.com/docs/cad-preparation/fluid-volume-extraction/)). Delete the solid bodies afterwards; incompressible runs are single-region.
- `<case>_part_*.stl`: each part on its own, to make it obvious which faces belong to which force group.

Units are millimetres. Tell SimScale "mm" on upload.

Coordinates:
- Tunnel cases (A): flow +X. The reflection plate is the wall y = 0. The duct is y 0 to 100, z −50 to +50 and x −250 to +600. The hinge line is the Y axis through the origin. +δ turns the leading edge toward +Z, so the fin's normal force is +Z.
- Rocket cases (R): CAD frame. +Z runs along the axis (nose up, z = 692 − station) and the flow is −Z. The box is x, y ±500 mm and z −1800 to +1392 mm. The CG is at (0, 0, 332.3) mm, which is station 359.7 at liftoff (rev 3d, 214 g ballast).

## Set-up (identical for every case unless noted)

1. Create project → Upload CAD → `A3_fluid.step` (mm). One case per upload, so the ten runs stay separate.
2. New simulation → Incompressible, steady state, turbulence model k-ω SST.
3. Material: Air, ν = 1.516e-5 m²/s, ρ = 1.204 kg/m³ (20 °C). Assign it to the single volume.
4. Boundary conditions.

| | Tunnel (A1 to A7) | Rocket (R1 to R3) |
|---|---|---|
| Velocity inlet | face x = −250: (12, 0, 0) m/s, turbulence intensity 1 %, mixing length 5 mm (honeycomb cell scale) | face z = +1392: (0, 0, −60) m/s, intensity 0.5 %, eddy-viscosity ratio 10 |
| Pressure outlet | face x = +600: 0 Pa gauge | face z = −1800: 0 Pa gauge |
| Walls | the four duct walls: no-slip (the plate is y = 0) | four box sides: slip |
| Body | fin and hub faces: no-slip | every rocket face: no-slip |

5. Mesh: Standard mesher.
   - Tunnel: a region refinement box x −60 to +120, y 0 to 60, z −25 to +25 at 0.6 mm cells; a surface refinement of 0.25 mm on the fin and hub; inflation 8 layers, first layer 0.02 mm, growth 1.25. That puts y+ near 1, which the 4.7 × 10⁴ chord Reynolds number needs.
   - Rocket: a region refinement around the tail (cylinder radius 120 mm, z −150 to +260) at 2 mm cells; surface refinement 0.5 mm on the fins and stabilizers and 1.5 mm on the body; inflation 4 layers, first layer 0.15 mm (y+ around 30 to 60 at 60 m/s, which suits SST's wall treatment).
   - Aim for 1.5 to 3 M cells per case. At that size a 16-core run takes roughly 10 to 30 core hours, so the full matrix uses a small part of the 2000.
6. Simulation control: 2000 iterations. Write results every 500.
7. Result control → Forces and moments ([SimScale docs](https://www.simscale.com/docs/simulation-setup/result-control/forces-and-moments/)).
   - Tunnel: one group with the fin and hub faces. Centre of rotation (0, 0, 0), which is the hinge. Read Fz (normal force) and My (hinge moment). Fx is drag.
   - Rocket: four groups, each with centre of rotation (0, 0, 332.3):
     - all rocket faces: the R1/R2 side force and pitching moment;
     - the pitch pair (cfin_az0 and cfin_az180);
     - the four stabilizers;
     - the body.
   - The coefficients option needs: reference area 0.0026421 m² (the 58 mm body cross-section), reference length 0.058 m, velocity 12 or 60 m/s.
   - Also add an area-average result control on the inlet and outlet. The pressure drop is a convergence check.
8. Run. A case is converged when the force plot is flat to within 1 % over the last 300 iterations and the residuals have dropped by at least three orders of magnitude.

## Reading the results against the model

- Normal-force coefficient on a fin: CN = F / (q S) with q = ½ρV². That is 86.7 Pa in the tunnel and 2167 Pa for the rocket. S is the fin planform area: 1200 mm² for the H40 tunnel fin, 1350 mm² for the H45 flight fin on the rocket.
- Hinge-moment arm: My / Fz. The model puts the CP 7.7 mm aft of the hinge. If the CFD arm is larger, the servo load grows in proportion.
- Stabilizer interference ratio: (F_R1 − F_R2) / F_R2 on the rocket side force. The model says −0.10 for the rev 3d stabilizers.
- Static margin from R3: CP station = 359.7 + 1000 · |My / Fz| in mm (the moment is about the CG). Divide (CP − 359.7) by 58 to get calibres. The model says 1.01 cal.

Put the numbers back into `Simulations/CFD/simscale/results.csv` (same columns as `predictions.csv` plus `cfd_force_N`, `cfd_moment_Nm`) so the docs and the GUI can show both.

## Limits worth knowing before trusting a number

- The tunnel fin runs at a chord Reynolds number of about 4.7 × 10⁴. That is transitional, and SST assumes a fully turbulent boundary layer. The lift slope should land close; drag and any separation at 15° will not, and the tunnel is the arbiter for those.
- Steady RANS cannot resolve the leading-edge vortex shedding the double wedge may produce at 10 to 15°. If A5 does not converge to a steady force, switch that one case to transient (Δt = 1e-5 s) and average the last 0.05 s.
- The stabilizers are 2.4 mm flat plates with 0.6 mm edge fillets. The control fins carry their real sections. The 1.0 mm root gap is closed by the 8 mm hub, as on the flight hardware.
- The rocket cases carry no rail buttons, launch lug or motor nozzle step. These change drag, not the control moment.
