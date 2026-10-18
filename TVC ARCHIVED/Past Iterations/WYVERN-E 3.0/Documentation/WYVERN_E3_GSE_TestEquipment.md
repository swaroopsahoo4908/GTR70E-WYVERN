# WYVERN-E 3.0 — Ground Support Equipment, Test Rigs & 3D-Print Manifest

### Static thrust stand · TVC thrust-vector balance · Hofferth wind tunnel · full print list

*All purchasable items are in `WYVERN_E3_BOM.xlsx` → §9 (launch/stand) and the `GSE & Test Equip`
sheet (wind tunnel + TVC balance). This doc is the engineering rationale + 3D-print manifest.*

## 1. Load cells — updated for the new motors

3.0 motors set the ranges: *F40W* peak **68.1 N** (avg 37.9 N, 78.1 N·s, 2.1 s); *G25W* peak ≈
**50 N** (avg 25 N, ~117 N·s, 4.7 s). Side force from a ±5° gimbal at peak thrust is
$F_\perp = T\sin5° \approx 5.9\ \mathrm{N}$.

| Cell | Where | Range / rationale |
|---|---|---|
| 20 kg (196 N) bar + HX711 | Static axial thrust stand | 2.9× margin on 68 N peak + ignition spikes |
| 10 kg (98 N) bar + HX711 | TVC balance — axial (Z) | resolution over 25–68 N |
| 1 kg (9.8 N) bar + HX711 ×2 | TVC balance — lateral (X, Y) | fine resolution on the ~6 N side force |

The old 10 kg single-cell stand (sized for a ~100 N G64W that was dropped) is superseded.

## 2. TVC Thrust-Vector Balance (works for *both* solenoid and servo)

The gimbal under test (System A solenoid *or* System B servo) is the article; the balance is
actuator-agnostic, so one rig validates both A/B builds on the ground.

### 2.1 3-component balance
Live motor + TVC gimbal bolt to a rigid *thrust block* restrained from the fixed base by three
orthogonal single-axis load cells through stiff flexures (0.4 mm spring-steel shim or printed living
hinges), each reading one axis: *Z* (10 kg) = thrust; *X, Y* (1 kg each) = the side-force from
gimbal deflection in the pitch and yaw planes.

### 2.2 Reduction — thrust magnitude *and* direction
$$T=\sqrt{F_x^2+F_y^2+F_z^2}, \qquad \theta=\arctan\frac{\sqrt{F_x^2+F_y^2}}{F_z}, \qquad
\phi=\operatorname{atan2}(F_y,F_x)$$
$T$ = thrust, $\theta$ = deflection angle (target ±5°), $\phi$ = deflection direction. Logging
$\theta(t),\phi(t)$ vs the commanded angle yields bandwidth, slew rate, overshoot, and
steady-state error — the A/B metrics for solenoid bang-bang vs servo proportional.

### 2.3 DAQ & safety
3× HX711 (separate data pins, shared clock) → the **Arduino Nano** (already in the master BOM) →
microSD at 80 SPS; calibrate each axis with known masses. Steel blast-deflector shields the
cells; frame clamps to the static-stand base. Live-motor test: remote ignition, ≥3 m standoff,
fixed restraint, gimbal-neutral fail-safe.

## 3. Wind tunnel — Hofferth *Modular Wind Tunnel for STEM Education*

We use Jerrod Hofferth's open-source tunnel (Printables 849713 — **free** since Jan 2025, FDM,
presented at *AIAA SCITECH 2025*, [doi:10.2514/6.2025-2560](https://doi.org/10.2514/6.2025-2560)).
It is an **in-draft / open-return low-speed** tunnel: room air → bellmouth inlet → honeycomb
straightener → mesh screens → settling duct → **4:1 contraction** → test section → diffuser → fan →
exhaust. Flow conditioning (honeycomb + progressively finer screens + duct decay) gives a clean,
uniform, low-turbulence test section. Test articles mount on a Gridfinity strut/sting base
(configurable AoA / sideslip / roll) or a sidewall half-span mount.

### 3.1 Our use — RQ1/RQ2 fin testing
RQ1 fin profiles mount on the strut/sting base for **AoA / deflection sweeps** with smoke +
520 nm laser-sheet flow visualization; the sidewall half-span mount is used for deflected-fin
runs. RQ2 surface/coating articles run in the same section. (Future: a lift-drag force balance on
the Gridfinity floor — Hofferth's forthcoming kit uses 100 g/500 g cells on a floating frame.)

### 3.2 Fan trade study — *best spec for force measurement*

Because our goal is **measuring fin aero forces** (not just smoke play), the limiting requirement is
*test-section velocity / Reynolds number*. Hofferth's own diffuser-and-fan **upgrade kit** exists
precisely "to enable… measurement of forces and moments… more velocity = more-significant
aerodynamic forces to measure." Options:

| Fan | Flow | Static press. | Noise | Drive | Verdict |
|---|---|---|---|---|---|
| Noctua NF-A14 iPPC 3000 (140 mm) | ~140 CFM | ~250 Pa | ~40 dB | 12 V PWM PC fan | stock default; lowest velocity |
| Delta PFB1212UHE (120 mm) | 253 CFM | **351 Pa** | 66 dB | 12 V/48 W + PWM + 120 mm adapter | compact, highest static pressure, but loud + lower flow |
| **AC Infinity Cloudline A8 (8″)** | **724 CFM** | high (mixed-flow) | **42 dB** | self-contained EC + 10-speed | **recommended** — ~2.9× the flow, quiet, force-measurement upgrade |

**Recommendation: the AC Infinity Cloudline A8** with Hofferth's *Diffuser & Fan Upgrade Kit*
(Printables 864377). It delivers by far the highest test-section velocity (724 CFM through the
~200 mm upgrade diffuser), runs quietly (42 dB) on a self-contained EC motor with a built-in
10-speed controller (no separate 12 V supply or PWM board needed), and is the configuration the
designer purpose-built for force/moment measurement — i.e., our RQ1. Mate the upgrade diffuser to
the A8 with a rubber duct coupler + hose clamps.

The **PFB1212UHE (120 mm)** stays in the BOM as the compact, very-high-static-pressure alternative
(useful if duct space is tight or to push hard through extra screens), but it is louder and moves
less air, and it needs the 120 mm fan adapter + a 12 V/48 W supply + PWM controller. Pick **one**
fan path; the BOM `GSE & Test Equip` sheet lists A (A8, recommended) and A2 (PFB1212UHE, alt).

### 3.3 Flow conditioning & assembly hardware
Honeycomb straightener (printed at 20 % hex infill / 0 walls, *or* the drinking-straw + screen
alternate); **40-mesh + 80-mesh** stainless screens upstream (progressively finer turbulence
breakup), plus a coarse 5–10 mesh debris screen downstream of the test section to protect the fan.
Junction rings use **M5×10 heat-set inserts**; test-section window retainers + tabs use **M2.5×4
inserts** (both covered by the M2–M6 assortment). Test-article bases use **6×2 mm** neodymium discs
(Gridfinity) and the floor uses **10×3 mm** discs. Optional inter-module **O-rings** (ASTM
A568-160 / -275, softest durometer). Smoke rakes feed via **¼″ Loc-Line**; clean exit ports with
**2 mm OD brass tube**. Windows: **3 mm acrylic** laser-cut to 80×130 mm (r13 corners) or the
SendCutSend preset cart.

### 3.4 Materials & printing
PETG recommended (robust for transport) or PLA; **~5 kg** total (Bambu 0.4 mm-nozzle preset = 22
plates / ~7 days, or 0.6–0.8 mm nozzle for the large parts). Printer: 256³ mm class (Bambu
A1/X1/P1, Prusa XL) for the chamber; downstream parts fit a 180³ Mini. Bed 85 °C, textured PEI,
minimal part cooling first ~10 layers; enable the full 256×256 build area for the contraction cone.

## 4. Full 3D-print manifest

### 4.1 Flight vehicle — `3D parts/_generator/gen_rocket.py`
Nose cone (ASA); recovery bay, FC Pi-5 sled, FC/TVC bulkhead, TVC bay, gimbal mech, interstage,
oversized fins ×4, booster body, camera-pod fairing — PC-FR except nose.

### 4.2 Static thrust stand — generator
Base plate, motor tower, load-cell bracket (PC-FR).

### 4.3 TVC thrust-vector balance — *to add to generator*
Thrust block, 3× flexure mounts, 2× lateral-cell brackets, axial-cell mount, base-clamp adapter,
blast-deflector backer.

### 4.4 Wind tunnel — Hofferth STLs (Printables 849713, + upgrade 864377)
*Minimum:* contraction cone, large + small junction rings, test-section frame, window retainer
tabs, diffuser w/ fan interface, fan guard, stands. *Full:* bellmouth inlet, honeycomb straightener,
empty duct ×1–2, smoke-rake strut + 3 wands + 4 port covers, Gridfinity test-article floor + bases
(strut/sting, flat plate, half-span sidewall), LED ceiling module, laser X/Y gantry, blank walls.
*If A8 (recommended):* the **Diffuser & Fan Upgrade Kit** (864377) — 2-part long diffuser,
upgrade junction ring, optional hub diverter/flow straightener, A8 fan stand (M5×10 inserts).
*If PFB1212UHE:* the **120 mm fan adapter/collar** (our `gen_rocket.py` Wind Tunnel part). Our RQ1
fin test mount is also produced by `gen_rocket.py`.

## 5. Additional tools (beyond the FC tool list)
Heat-set insert installation (soldering iron + insert tip); the 12 V 10 A supply + PWM controller
(needed *only* for the PFB1212UHE fan path; also handy for solenoid/servo bench tests); load-cell
calibration mass set; drill bit (2 mm) for smoke-rake ports. The crimper, multimeter, calipers, and
helping-hands already in the master BOM §10 cover the rest. (Excluded as on-hand: 3D printer, AA
batteries, basic hand tools.)

## 6. References
Hofferth, J. — *Modular Wind Tunnel for STEM Education*, Printables 849713 (free); AIAA SCITECH
2025 paper, doi:10.2514/6.2025-2560. Diffuser & Fan Upgrade Kit, Printables 864377. Barlow, Rae &
Pope, *Low-Speed Wind Tunnel Testing*, 3rd ed. NASA *Beginner's Guide to Wind Tunnels*.
