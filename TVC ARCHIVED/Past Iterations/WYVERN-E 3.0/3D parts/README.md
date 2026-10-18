# 3D Parts — Rocket Airframe & Mechanism

Printable STL and CAD STEP for every rocket part of the two-stage 84 mm vehicle: nose, recovery bay, avionics bay, PCB mount, sustainer TVC bay (with the fin can), gimbal mechanism, interstage coupler, single fin test article, booster body, camera pod, outer shell, and the full assembly.

Per PDR-005 the fixed fins are on the sustainer (TVC bay), and the booster is finless.

## Regenerate

Parts are parametric. Edit `_generator/gen_rocket.py` (geometry in the `P` dict) and rebuild:

```
cd _generator
python3 gen_rocket.py     # requires OCP (cadquery-ocp); writes STL + STEP to the part folders
```

`_generator/wcad.py` is the thin OpenCascade helper layer. Material assignments and a mass report are printed at build time.
