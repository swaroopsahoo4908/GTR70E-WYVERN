#!/usr/bin/env python3
"""D7: mesh renders of the printed wind-tunnel parts, straight from the exported STLs."""
import os, glob, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from stl import mesh
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..", "..", "3D parts", "wind_tunnel")

def load(name):
    return mesh.Mesh.from_file(glob.glob(os.path.join(P, name + "*.stl"))[0]).vectors.copy()

def view_matrix(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Rz

def draw(ax, plist, elev=25, azim=-55, title=None):
    M = view_matrix(elev, azim); L = np.array([0.35, -0.5, 0.8]); L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    for v, col, off in plist:
        v = v.copy() + np.array(off)
        p = v @ M.T
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        k = 0.42 + 0.58 * np.abs(n @ L)
        base = np.array(matplotlib.colors.to_rgb(col))
        polys.append(p[:, :, [0, 2]]); cols.append(np.clip(base[None] * k[:, None], 0, 1)); depth.append(p[:, :, 1].mean(1))
    Pp = np.concatenate(polys); Cc = np.concatenate(cols); D = np.concatenate(depth); o = np.argsort(-D)
    ax.add_collection(PolyCollection(Pp[o], facecolors=Cc[o], edgecolors=Cc[o], linewidths=0.15))
    pts = Pp.reshape(-1, 2); mn, mx = pts.min(0), pts.max(0); pad = 0.05 * (mx - mn).max()
    ax.set_xlim(mn[0] - pad, mx[0] + pad); ax.set_ylim(mn[1] - pad, mx[1] + pad)
    ax.set_aspect("equal"); ax.axis("off")
    if title: ax.set_title(title, fontsize=9)

fig = plt.figure(figsize=(14, 9.5))
gs = fig.add_gridspec(2, 3)
draw(fig.add_subplot(gs[0, 0]), [(load("WTA_reflection_plane_wall_panel"), "#94a3b8", (0, 0, 0))], 30, -50,
     "WTA reflection-plane wall panel (175 x 100 x 4 mm)")
draw(fig.add_subplot(gs[0, 1]), [(load("WTA_servo_balance_cradle"), "#2563eb", (0, 0, 0))], 25, -55,
     "WTA servo balance cradle (EMAX ES9251 II on 2 x 1 kg cells)")
mr = load("WTA_inclined_manometer_ramp"); ml = load("WTA_inclined_manometer_lid")
lid_off = (mr[..., 0].min() - ml[..., 0].min() - 10, 0, mr[..., 2].max() - ml[..., 2].min() + 15)
draw(fig.add_subplot(gs[0, 2]), [(mr, "#16a34a", (0, 0, 0)), (ml, "#facc15", lid_off)], 40, -125,
     "WTA inclined water manometer, 1:10 ramp + reservoir lid")
draw(fig.add_subplot(gs[1, 0]), [(load("WTA_diffuser_100sq_to_6in_round"), "#f59e0b", (0, 0, 0))], 20, -40,
     "WTA diffuser, 100 mm square -> 6 in round (fan collar)")
CF = os.path.join(P, "..", "control_fins")
fins = []; cols = {"flat_plate": "#64748b", "double_wedge": "#c2410c", "NACA0006": "#2563eb", "NACA0012": "#16a34a"}
for i, prof in enumerate(["flat_plate", "double_wedge", "NACA0006", "NACA0012"]):
    for j, H in enumerate([20, 30, 40]):
        v = mesh.Mesh.from_file(glob.glob(os.path.join(CF, prof, f"cfin_{prof}_H{H}_*.stl"))[0]).vectors.copy()
        v = v[..., [2, 1, 0]]; v -= v.reshape(-1, 3).min(0)        # chord -> x, span -> z
        fins.append((v, cols[prof], (j * 80, 0, -i * 55)))
ax = fig.add_subplot(gs[1, 1:])
draw(ax, fins, 18, -15, "Phase A test fins: flat plate / double wedge / NACA 0006 / NACA 0012 (rows) at H = 20 / 30 / 40 mm (columns; 25 and 35 not shown)")
fig.suptitle("D7  Printed wind-tunnel parts, rendered from the exported STLs (mesh plots, not photoreal)", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "D7_wind_tunnel_parts.png"), dpi=140, bbox_inches="tight", facecolor="white")
print("wrote D7_wind_tunnel_parts")
