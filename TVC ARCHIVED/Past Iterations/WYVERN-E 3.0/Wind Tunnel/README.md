# Wind Tunnel — Ground Support Equipment (RQ1/RQ2 fin testing)

Base platform: Jerrod Hofferth's **Modular Wind Tunnel for STEM Education** (Printables 849713,
free; AIAA SCITECH 2025, doi:10.2514/6.2025-2560) — an in-draft / open-return low-speed tunnel with
a 4:1 contraction and full flow conditioning (honeycomb + screens). The Hofferth STLs are in
`modular-wind-tunnel-for-stem-education-model_files/`.

## Our printed parts (from `../3D parts/_generator/gen_rocket.py`)
- `WT_fin_test_mount.*` — deflection-indexed single-fin mount (one fin at a time; 0.5° deflection
  sweeps for RQ1/RQ2), mounts to the Gridfinity strut/sting base or the sidewall half-span mount.
- `WT_120mm_fan_collar.*` — 120 mm fan → tunnel collar (only needed for the PFB1212UHE fan path).

## Fan — best spec for *force measurement* (see trade study)
RQ1 measures fin aero forces, so test-section velocity is the limiter. **Recommended: AC Infinity
Cloudline A8 (8″, 724 CFM, 42 dB, self-contained EC + 10-speed controller)** with Hofferth's
*Diffuser & Fan Upgrade Kit* (Printables 864377) — the configuration purpose-built for force
measurement. The **Delta PFB1212UHE (120 mm, 253 CFM, 351 Pa, 66 dB)** + the collar above is the
compact high-static-pressure alternative (needs a 12 V/48 W supply + PWM). Pick one.

## Where everything is purchased / documented
- **Hardware + exact links:** `../Documentation/WYVERN_E3_BOM.xlsx` → `GSE & Test Equip` sheet
  (fan options A / A2, flow-conditioning screens, magnets, inserts, acrylic, smoke/laser viz).
- **Trade study, flow-conditioning rationale, and full 3D-print manifest:**
  `../Documentation/WYVERN_E3_GSE_TestEquipment.md`.
- **Fin CFD (RQ1 airfoil polars):** `../Simulations/CFD/`.
