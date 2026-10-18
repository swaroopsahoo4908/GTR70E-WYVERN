#!/usr/bin/env python3
"""GTR70E WYVERN -- vortex-lattice model of one all-moving triangular control fin.

Horseshoe-vortex VLM (Bertin & Cummings, *Aerodynamics for Engineers*, ch. 7; Katz & Plotkin,
*Low-Speed Aerodynamics*, ch. 12). The fin is mirrored across its root chord, which models the
body wall as a reflection plane; the resulting planar wing of span 2H is the "wing alone" whose
loads the slender-body interference factors (wf_core.K_WB) then scale onto the body.

Planform (matches the CAD): root chord c at the body, leading edge swept from the root LE to the
tip, trailing edge normal to the body. All-moving: the whole panel sees the same incidence
(alpha + delta), so the boundary condition is uniform.

Returns per-fin coefficients referenced to the fin's own exposed area S_f = c H / 2:
  CNa      normal-force slope (per rad)
  xcp_c    chordwise centre of pressure from the root LE, fraction of c
  ycp_H    spanwise centre of pressure from the root, fraction of H
  Chd      hinge-moment slope about the hinge line at hinge_frac*c (per rad, ref S_f*c)
"""
import numpy as np

def _seg_vel(P, A, B):
    """Velocity at points P (N,3) induced by unit-strength segments A->B (M,3). -> (N,M,3)"""
    r1 = P[:, None, :] - A[None, :, :]
    r2 = P[:, None, :] - B[None, :, :]
    r0 = (B - A)[None, :, :]
    c = np.cross(r1, r2)
    c2 = np.sum(c * c, axis=-1)
    n1 = np.linalg.norm(r1, axis=-1); n2 = np.linalg.norm(r2, axis=-1)
    dot = np.sum(r0 * (r1 / n1[..., None] - r2 / n2[..., None]), axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        k = np.where(c2 > 1e-12, dot / (4 * np.pi * c2), 0.0)
    return c * k[..., None]

def fin_vlm(H, c=60.0, hinge_frac=0.45, nc=8, ns=24):
    # spanwise stations over the full mirrored span [-H, H], cosine-clustered at tips and root
    th = np.linspace(0, np.pi, ns + 1)
    yh = 0.5 * H * (1 - np.cos(th))                  # 0..H on one side
    y = np.concatenate([-yh[::-1], yh[1:]])          # -H..H
    panels = []
    for j in range(len(y) - 1):
        ya, yb = y[j], y[j + 1]
        ym = 0.5 * (ya + yb)
        def le(yy): return c * abs(yy) / H
        for i in range(nc):
            fa0 = i / nc; fa1 = (i + 1) / nc
            # quarter-chord bound vortex and 3/4 control point of this panel at each edge
            xa = le(ya) + (c - le(ya)) * (fa0 + 0.25 * (fa1 - fa0))
            xb = le(yb) + (c - le(yb)) * (fa0 + 0.25 * (fa1 - fa0))
            xm_cp = le(ym) + (c - le(ym)) * (fa0 + 0.75 * (fa1 - fa0))
            xm_b = le(ym) + (c - le(ym)) * (fa0 + 0.25 * (fa1 - fa0))
            panels.append((xa, ya, xb, yb, xm_cp, ym, xm_b, yb - ya))
    P = np.array(panels)
    far = 1000.0 * c
    A = np.c_[P[:, 0], P[:, 1], np.zeros(len(P))]
    B = np.c_[P[:, 2], P[:, 3], np.zeros(len(P))]
    Ainf = A.copy(); Ainf[:, 0] = far
    Binf = B.copy(); Binf[:, 0] = far
    CP = np.c_[P[:, 4], P[:, 5], np.zeros(len(P))]
    w = (_seg_vel(CP, Ainf, A) + _seg_vel(CP, A, B) + _seg_vel(CP, B, Binf))[..., 2]
    # unit incidence (1 rad small-angle): w_induced = -V * alpha
    G = np.linalg.solve(w, -np.ones(len(P)))       # Gamma / V per rad
    dy = P[:, 7]; xb = P[:, 6]; ym = P[:, 5]
    Lp = G * dy                                     # lift per unit (rho V^2) per rad
    S_wing = c * H                                  # both halves
    CLa = 2 * Lp.sum() / S_wing                     # per rad, ref wing area (= fin CNa, ref S_f)
    xcp = float((Lp * xb).sum() / Lp.sum())
    half = ym > 0
    ycp = float((Lp[half] * ym[half]).sum() / Lp[half].sum())
    xh = hinge_frac * c
    Chd = float((Lp[half] * (xh - xb[half])).sum() * 2 / (S_wing / 2) / c) / 2 * 2
    # Chd: hinge moment slope per fin, nose-up-about-hinge positive, ref S_f * c
    Chd = float((Lp[half] * (xh - xb[half])).sum() / Lp[half].sum()) / c * CLa
    return dict(H=H, AR_wing=(2 * H) ** 2 / S_wing, CNa=float(CLa), xcp_c=xcp / c, ycp_H=ycp / H,
                Chd=Chd, hinge_arm_c=(xcp - xh) / c)

def helmbold(AR, eta=1.0):
    return 2 * np.pi * AR / (2 + np.sqrt(AR * AR / (eta * eta) + 4))

def polhamus_Kv(CNa, AR, sweep_le_rad):
    """Polhamus leading-edge-suction-analogy vortex-lift constant (per fin, ref S_f)."""
    Ki = 1.0 / (np.pi * AR)
    return (CNa - CNa ** 2 * Ki) / np.cos(sweep_le_rad)

if __name__ == "__main__":
    # validation: unswept rectangular AR via a crude rectangle limit is not this planform;
    # compare the delta-planform slope against Helmbold and slender-wing (pi*AR/2) estimates.
    for H in (20, 25, 30, 35, 40):
        r = fin_vlm(H)
        print(f"H={H:2d}  AR={r['AR_wing']:.2f}  CNa_VLM={r['CNa']:.3f}  Helmbold={helmbold(r['AR_wing']):.3f}  "
              f"slender={np.pi*r['AR_wing']/2:.3f}  xcp/c={r['xcp_c']:.3f}  ycp/H={r['ycp_H']:.3f}  "
              f"hinge arm/c={r['hinge_arm_c']:.3f}")
