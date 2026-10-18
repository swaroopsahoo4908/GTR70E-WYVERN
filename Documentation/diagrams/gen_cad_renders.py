#!/usr/bin/env python3
"""Mesh renders straight from the exported STLs (3D parts/) -- assembled and exploded views.
These are triangulated-mesh plots for checking geometry, not photoreal renders."""
import os, sys, glob, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Simulations")); import wf_core as C
P = os.path.join(ROOT, "3D parts")

def rot_z(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]); return v @ R.T

def load(name, sub="flight"):
    return mesh.Mesh.from_file(glob.glob(os.path.join(P, sub, name + "*.stl"))[0]).vectors.copy()

def parts(cfin="NACA0006"):
    hub = load("06_servo_hub"); rf = load("12_rect_fin")
    cf = load(f"cfin_{cfin}_H{int(C.CFIN_H_NOMINAL)}", f"control_fins/{cfin}")
    out = [("nose", load("01_nose"), "#e5e7eb", 3), ("rb", load("02_recovery"), "#f1f5f9", 2),
           ("rbc", load("03_rb_floor"), "#b45309", 2), ("ct", load("04_control"), "#94a3b8", 1),
           ("imu", load("05_spine_deck"), "#db2777", 1), ("spine", load("05b_avionics_spine"), "#16a34a", 1), ("mb", load("07_motor_bay"), "#64748b", 0),
           ("plenum", load("08_plenum"), "#d97706", 0), ("mmt", load("09_motor_mount"), "#a78bfa", 0),
           ("ret", load("10_motor_retainer"), "#d97706", -1)]
    for a in (0, 90, 180, 270): out.append(("hub", rot_z(hub, a), "#111827", 1))
    for i in range(4): out.append(("rfin", rot_z(rf, 90 * i), "#1e293b", 0))
    for a in (0, 90, 180, 270): out.append(("cfin", rot_z(cf, a), "#c2410c", 1))
    return out

from matplotlib.collections import PolyCollection

def view_matrix(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Rz

def draw(ax, plist, explode=0.0, elev=12, azim=-60, title=None):
    """Orthographic painter's-algorithm render (2D), so framing is exact."""
    M = view_matrix(elev, azim)
    polys, cols, depth = [], [], []
    L = np.array([0.35, -0.5, 0.8]); L /= np.linalg.norm(L)
    for name, v, col, grp in plist:
        v = v.copy(); v[..., 0] += grp * explode
        p = v @ M.T                                  # x right, y depth, z up  (after rotation)
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        k = 0.42 + 0.58 * np.abs(n @ L)
        base = np.array(matplotlib.colors.to_rgb(col))
        polys.append(p[:, :, [0, 2]]); cols.append(np.clip(base[None] * k[:, None], 0, 1)); depth.append(p[:, :, 1].mean(1))
    P = np.concatenate(polys); Cc = np.concatenate(cols); D = np.concatenate(depth)
    o = np.argsort(-D)
    ax.add_collection(PolyCollection(P[o], facecolors=Cc[o], edgecolors=Cc[o], linewidths=0.15))
    pts = P.reshape(-1, 2); mn, mx = pts.min(0), pts.max(0); pad = 0.03 * (mx - mn).max()
    ax.set_xlim(mn[0] - pad, mx[0] + pad); ax.set_ylim(mn[1] - pad, mx[1] + pad)
    ax.set_aspect("equal"); ax.axis("off")
    if title: ax.set_title(title, fontsize=9)

def horiz(pl):
    out = []
    for name, v, col, grp in pl:
        w = v[..., [2, 0, 1]].copy()          # z (long axis) -> x
        out.append((name, w, col, grp))
    return out

def box_mesh(x0, x1, y0, y1, z0, z1):
    c = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return c[np.array(f)]

def cyl_mesh(r, z0, z1, n=32):
    a = np.linspace(0, 2 * np.pi, n + 1); tris = []
    for i in range(n):
        p0 = [r * np.cos(a[i]), r * np.sin(a[i])]; p1 = [r * np.cos(a[i + 1]), r * np.sin(a[i + 1])]
        tris += [[p0 + [z0], p1 + [z0], p1 + [z1]], [p0 + [z0], p1 + [z1], p0 + [z1]]]
    return np.array(tris)

def internals():
    """Servo envelopes + central bypass tube (not printed parts, so built here from wf_core)."""
    sv = C.SERVO; zc = C.L_TOTAL - C.X_CT_BOT + C.SERVO_RING_Z
    out = [("bypass", cyl_mesh(C.BYPASS["od"] / 2, C.L_TOTAL - C.X_BYPASS_TOP - C.BYPASS["L"], C.L_TOTAL - C.X_BYPASS_TOP), "#a1a1aa", 1)]
    for a in (0, 90, 180, 270):
        b = box_mesh(C.SERVO_BASE_R, C.SERVO_TOP_R, -sv["W"] / 2, sv["W"] / 2, zc - sv["L"] / 2, zc + sv["L"] / 2)
        out.append(("servo", rot_z(b, a), "#2563eb", 1))
    return out

def cutaway(pl, keep=("ct", "imu", "spine", "hub", "cfin", "servo", "bypass")):
    out = []
    for name, v, col, grp in pl:
        if name not in keep: continue
        if name == "ct":
            m = v[..., 1].min(axis=1) >= -0.5    # drop the half of the shell facing the viewer
            v = v[m]
        out.append((name, v, col, grp))
    return out

if __name__ == "__main__":
    pl = parts(); hp = horiz(pl)
    fig = plt.figure(figsize=(18, 13))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.5])
    draw(fig.add_subplot(gs[0, :]), hp, 0, 18, 10, "assembled flight vehicle (H = 40 mm NACA 0006 control fins at one station; 45° stabilizers)")
    exp = [(n, v.copy(), c, g) for n, v, c, g in hp]
    for n, v, c, g in exp: v[..., 0] += {3: 330, 2: 220, 1: 110}.get(g, 0) if n != "rbc" else 220
    draw(fig.add_subplot(gs[1, :]), exp, 0, 18, 10, "exploded: retainer | motor bay | control tube | RB-floor coupler + recovery bay | nose")
    draw(fig.add_subplot(gs[2, 0]), cutaway(pl + internals()), 0, 20, 35, "control tube cut-away: servo ring (4 x X08 Plus, one station), spine deck, avionics spine, central bypass tube")
    mb = [p for p in pl if p[0] in ("mb", "plenum", "mmt", "ret", "rfin")]
    mb = [(n, v[v[..., 1].min(axis=1) >= -0.5] if n in ("mb", "plenum") else v, c, g) for n, v, c, g in mb]
    draw(fig.add_subplot(gs[2, 1]), mb, 0, 20, 35, "motor bay cut-away: plenum + gas gallery (central bypass socket), MMT, through-wall stabilizers, retainer")
    fig.suptitle("GTR70E WYVERN fin-control — renders straight from the exported STL meshes", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "D0_cad_renders.png"), dpi=140, bbox_inches="tight", facecolor="white")
    print("wrote D0_cad_renders")
