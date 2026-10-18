#!/usr/bin/env python3
"""GTR70E WYVERN -- control-fin cross-sections (RQ1 aerofoil blocks).

Carried over from the TVC revision's panel-method profile set (same four families), re-defined
so that what the CFD analyses is exactly what the printer makes:

  flat_plate    constant 2.4 mm thickness, semicircular LE and TE (the "no aerofoil" control)
  double_wedge  symmetric diamond, t/c = 6 %, max thickness at mid-chord, sharp LE/TE
  NACA0006      4-digit symmetric, t/c = 6 %
  NACA0012      4-digit symmetric, t/c = 12 %

Every section has a 1.0 mm minimum thickness (two 0.4 mm perimeters + gap) so the tip region of
the triangular fin stays printable. Two interfaces:

  PROFILES[name](n)            unit-chord closed loop (X, Y) for the vortex-panel solver
  section_points(name, c, n)   dimensional (u, y) loop in mm for the CAD loft
"""
import numpy as np

T_MIN_MM = 1.0
FLAT_T_MM = 2.4
TC = dict(flat_plate=None, double_wedge=0.06, NACA0006=0.06, NACA0012=0.12)

def _cosine_x(n):
    beta = np.linspace(0.0, np.pi, n + 1)
    return 0.5 * (1.0 - np.cos(beta))

def half_thickness(name, x, tc):
    """y_t(x) for unit chord, thickness ratio tc."""
    if name.startswith("NACA"):
        return 5 * tc * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2
                         + 0.2843 * x ** 3 - 0.1036 * x ** 4)        # closed-TE form
    if name == "double_wedge":
        return np.where(x <= 0.5, tc * x, tc * (1.0 - x))
    if name == "flat_plate":
        r = tc / 2                                                    # LE/TE radius = t/2
        y = np.full_like(x, tc / 2)
        le = x < r; te = x > 1 - r
        y[le] = np.sqrt(np.clip(r * r - (r - x[le]) ** 2, 0, None))
        y[te] = np.sqrt(np.clip(r * r - (x[te] - (1 - r)) ** 2, 0, None))
        return y
    raise KeyError(name)

def loop(name, tc, n=160):
    x = _cosine_x(n // 2)
    yt = half_thickness(name, x, tc)
    X = np.concatenate([x[::-1], x[1:]])
    Y = np.concatenate([(-yt)[::-1], yt[1:]])
    return X, Y

def tc_at_chord(name, chord_mm):
    if name == "flat_plate":
        return max(FLAT_T_MM, T_MIN_MM) / chord_mm
    return max(TC[name], T_MIN_MM / chord_mm)

def section_points(name, chord_mm, n=36):
    """Closed (u, y) polygon in mm, u from LE (0) to TE (chord), no repeated end point."""
    tc = tc_at_chord(name, chord_mm)
    x = _cosine_x(n // 2)
    yt = half_thickness(name, x, tc) * chord_mm
    yt = np.maximum(yt, 0.0)
    u = x * chord_mm
    upper = list(zip(u, yt))
    lower = list(zip(u[::-1], -yt[::-1]))
    pts = upper + lower[1:-1]
    # drop zero-thickness duplicate points at LE/TE that would make degenerate edges
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append((float(p[0]), float(p[1])))
    return out

# unit-chord loops at the ROOT chord (60 mm) thickness, for the panel method
ROOT_CHORD_MM = 60.0
PROFILES = {name: (lambda n=160, nm=name: loop(nm, tc_at_chord(nm, ROOT_CHORD_MM), n))
            for name in TC}

if __name__ == "__main__":
    for name, fn in PROFILES.items():
        X, Y = fn()
        print(f"{name:13s} {len(X)-1} panels  t/c(root)={2*Y.max():.3f}  "
              f"closed={np.allclose([X[0],Y[0]],[X[-1],Y[-1]])}  "
              f"CAD pts @60mm={len(section_points(name,60))}")
