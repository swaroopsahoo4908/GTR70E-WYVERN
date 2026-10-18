#!/usr/bin/env python3
"""WYVERN-E 2.0 fin cross-section geometry for the panel-method CFD.

Generates closed coordinate loops (ordered clockwise from the trailing edge,
over the top to the LE, under the bottom back to the TE) for the four RQ1 fin
profiles, all at unit chord:

  - NACA 0006   (thin symmetric 4-digit)
  - NACA 0012   (moderate symmetric 4-digit)
  - double-wedge (6% symmetric diamond, max thickness at mid-chord)
  - flat-plate   (1.5% thin symmetric, rounded for panel stability)

Cosine spacing clusters nodes at the LE/TE for accuracy.
"""
import numpy as np

def _cosine_x(n):
    """n+1 x-stations, unit chord, cosine-clustered at LE/TE."""
    beta = np.linspace(0.0, np.pi, n+1)
    return 0.5*(1.0-np.cos(beta))

def naca4_symmetric(tt, n=160):
    """NACA 00xx, tt = thickness fraction (e.g. 0.12). Returns closed loop x,y."""
    x = _cosine_x(n//2)
    yt = 5*tt*(0.2969*np.sqrt(x) - 0.1260*x - 0.3516*x**2
               + 0.2843*x**3 - 0.1015*x**4)        # open TE form
    # clockwise from TE: lower TE->LE, then upper LE->TE
    X = np.concatenate([x[::-1], x[1:]])
    Y = np.concatenate([(-yt)[::-1], yt[1:]])
    return X, Y

def double_wedge(tt=0.06, n=160):
    """Symmetric double-wedge (diamond), max thickness tt at mid-chord."""
    x = _cosine_x(n//2)
    yt = np.where(x <= 0.5, tt*x/0.5, tt*(1.0-x)/0.5)
    X = np.concatenate([x[::-1], x[1:]])
    Y = np.concatenate([(-yt)[::-1], yt[1:]])
    return X, Y

def flat_plate(tt=0.015, n=160):
    """Thin symmetric plate (small thickness + rounded ends for panel stability)."""
    x = _cosine_x(n//2)
    # elliptical-ish thin section so panels stay well-conditioned
    yt = tt*np.sqrt(np.clip(x*(1.0-x)/0.25, 0, None))
    X = np.concatenate([x[::-1], x[1:]])
    Y = np.concatenate([(-yt)[::-1], yt[1:]])
    return X, Y

PROFILES = {
    "NACA0006":     lambda n=160: naca4_symmetric(0.06, n),
    "NACA0012":     lambda n=160: naca4_symmetric(0.12, n),
    "double_wedge": lambda n=160: double_wedge(0.06, n),
    "flat_plate":   lambda n=160: flat_plate(0.015, n),
}

if __name__ == "__main__":
    for name, fn in PROFILES.items():
        X, Y = fn()
        print(f"{name:13s}  {len(X)-1} panels  t/c≈{2*Y.max():.3f}  "
              f"closed={np.allclose([X[0],Y[0]],[X[-1],Y[-1]])}")
