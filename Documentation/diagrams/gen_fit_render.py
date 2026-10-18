#!/usr/bin/env python3
"""D6 fit-check renders from 3D parts/assembly/fit_meshes (written by gen_fit_assembly.py):
every printed part plus the vendor / datasheet models of the bought parts, in place.
Painter's-algorithm orthographic mesh plots (for checking fit, not photoreal)."""
import os, sys, json, math, glob
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from stl import mesh
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Simulations")); import wf_core as C
MD = os.path.join(ROOT, "3D parts", "assembly", "fit_meshes")
IDX = json.load(open(os.path.join(MD, "index.json")))
REP = json.load(open(os.path.join(ROOT, "3D parts", "assembly", "fit_report.json")))
SHELLS = ("01_nose", "02_recovery", "03_rb_floor", "04_control_tube", "07_motor_bay", "nomex")

def load(name):
    return mesh.Mesh.from_file(os.path.join(MD, name + ".stl")).vectors.copy()
PARTS = {n: (load(n), tuple(v["color"]), v["group"]) for n, v in IDX.items() if os.path.exists(os.path.join(MD, n + ".stl"))}

def view_matrix(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Rz

def draw(ax, items, elev, azim, title, horizontal=False):
    M = view_matrix(elev, azim)
    Lgt = np.array([0.35, -0.5, 0.8]); Lgt /= np.linalg.norm(Lgt)
    P, Cc, D = [], [], []
    for v, col in items:
        if horizontal: v = v[..., [2, 0, 1]] * np.array([-1, 1, 1])
        p = v @ M.T
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        k = 0.40 + 0.60 * np.abs(n @ Lgt)
        P.append(p[:, :, [0, 2]]); Cc.append(np.clip(np.array(col)[None] * k[:, None], 0, 1)); D.append(p[:, :, 1].mean(1))
    P = np.concatenate(P); Cc = np.concatenate(Cc); D = np.concatenate(D); o = np.argsort(-D)
    ax.add_collection(PolyCollection(P[o], facecolors=Cc[o], edgecolors=Cc[o], linewidths=0.1))
    pts = P.reshape(-1, 2); mn, mx = pts.min(0), pts.max(0); pad = 0.03 * (mx - mn).max()
    ax.set_xlim(mn[0] - pad, mx[0] + pad); ax.set_ylim(mn[1] - pad, mx[1] + pad); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=9)

def cut(v, name, axis=1, keep_ge=-0.3):
    if name.startswith(SHELLS):
        m = v[..., axis].min(axis=1) >= keep_ge
        return v[m]
    return v

def zband(z0, z1):
    out = []
    for n, (v, col, g) in PARTS.items():
        zc = v[..., 2].mean(1)
        m = (zc >= z0) & (zc <= z1)
        if m.any(): out.append((v[m], col))
    return out

L = C.L_TOTAL
fig = plt.figure(figsize=(18, 14))
gs = fig.add_gridspec(3, 3, height_ratios=[1.0, 1.5, 1.2])
# A: full vehicle, near half of every shell removed, seen from -Y
items = [(cut(v, n, axis=0), col) for n, (v, col, g) in PARTS.items()]
draw(fig.add_subplot(gs[0, :]), items, 0, 0, "A  whole vehicle, near half of the shells removed: nose ballast, packed chute + cord, RB floor + eyebolt, spine with boards, servo ring, motor", horizontal=True)
# B: control tube close-up (oblique)
zlo = L - C.X_CT_BOT - 10; zhi = L - C.X_CT_TOP + 25
ct_items = []
for n, (v, col, g) in PARTS.items():
    zc = v[..., 2].mean(1)
    m = (zc > zlo) & (zc < zhi)
    if not m.any(): continue
    vv = v[m]
    if n.startswith(SHELLS) or n.startswith("05_spine_deck"):
        mm = vv[..., 1].min(axis=1) >= -0.3; vv = vv[mm]
    ct_items.append((vv, col))
draw(fig.add_subplot(gs[1, 0:2]), ct_items, 18, -35, "B  control tube cut-away: X08 Plus ring at one station, spine with the vendor BNO085 / Feather / BME688 / microSD / Pololu models, LiPo, bypass")
# C/D/E: slabs looking down the axis
def slab(ax, z0, z1, title):
    draw(ax, zband(z0, z1), 90, 0, title)
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(C.RI * np.cos(th), C.RI * np.sin(th), color="#dc2626", lw=0.6, ls="--")
zr = L - C.X_CT_BOT + C.SERVO_RING_Z
slab(fig.add_subplot(gs[1, 2]), zr - 13, zr + 13, f"C  slab through the servo ring (red dashed = {2*C.RI:.1f} mm bore)")
zs = L - C.X_CT_BOT + C.SPINE_Z0
slab(fig.add_subplot(gs[2, 0]), zs + 14, zs + 30, "D  slab through the spine: BNO085, BME688, LiPo, perfboard")
slab(fig.add_subplot(gs[2, 1]), zs + 44, zs + 66, "E  slab through the spine: Feather, microSD, LiPo, perfboard")
ax = fig.add_subplot(gs[2, 2]); ax.axis("off")
f = REP["interference_faults"]; d = REP["designed_contacts"]
txt = [f"Fit check ({REP['components']} components)", "",
       f"interference faults: {len(f)}" + ("" if f else "  (none)")]
txt += [f"  {x['a']} x {x['b']}: {x['mm3']} mm3" for x in f[:6]]
txt += [f"designed contacts (seats, glands): {len(d)}", "", "tightest radial clearance to the bore:"]
txt += [f"  {b['name']}: {b['clearance_to_bore']:.2f} mm" for b in REP["bore_clearance"][:5]]
txt += ["", "control fins swept ±15°: " + ("clear" if all(s["overlap_mm3"] == 0 for s in REP["fin_sweep"]) else "CONTACT"),
        "print bed 256 mm: " + ("all parts fit" if all(b["fits_256"] for b in REP["print_bed_256"]) else
                                 "TOO BIG: " + ", ".join(b["part"] for b in REP["print_bed_256"] if not b["fits_256"])),
        f"nose ballast fills {REP['ballast_fill_mm']:.0f} mm of the tip"]
ax.text(0, 1, "\n".join(txt), va="top", family="DejaVu Sans Mono", fontsize=8.5)
fig.suptitle("D6  Fit check — printed parts + vendor STEP models (Adafruit, Pololu) + datasheet-built bought parts", fontsize=12, x=0.02, ha="left")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "D6_fit_check.png"), dpi=130, bbox_inches="tight", facecolor="white")
print("wrote D6_fit_check")
