# Superseded 3D parts, archive only, do not print

These files are retained as a record of design changes, not as buildable parts. Nothing here is
referenced by `_generator/gen_rocket4.py`, the BOM, or the mass stack in `Simulations/we4_sim.py`.

| Part | Why it was superseded |
|---|---|
| `01_nose_cone_PCFR.*`, `01_nose_cone_ellipsoid_PCFR.*` | Nose moved PETG-CF → **PLA**. The nose sees no motor heat, and the mass saving is what moved the CG aft and drove the fin growth to 72 mm. Current part: `../01_nose_cone_ellipsoid_ASA.*` |
| `05b_bulkhead_B_ASA.*` | Bulkhead B moved PLA → **PETG-CF**: it takes the ~140 kPa ejection pressure pulse, so it needs the structural and flame-rated material. Current part: `../05b_bulkhead_B_PCFR.*` |
| `08b_fin_single_PCFR.*` | Fin moved PETG-CF → **PLA** with the airframe material zoning. Current part: `../08b_fin_single_ASA.*` |

**Warning on the archived fin.** `08b_fin_single_PCFR.stl` was exported before the 2026-08 unit fix
in `gen_rocket4.py` (the fin was called with metre-valued arguments in a millimetre file, so it was
built at 1/1000 scale and has effectively zero volume). It is geometrically useless and kept only so
the material change has a matching pair. The current `08b_fin_single_ASA.*` is correct: 11.3 cm³,
7.4 g, 72 mm semispan.
