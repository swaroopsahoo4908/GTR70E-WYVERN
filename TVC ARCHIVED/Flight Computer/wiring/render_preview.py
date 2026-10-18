#!/usr/bin/env python3
"""Render WYVERN_E4_flight_wiring_connected.kicad_sch -> _preview.png (matplotlib).
Parses the graphical primitives (rectangle/wire/junction/text) the generator emits, so the
preview always tracks the .kicad_sch. KiCad Y is screen-down; we invert Y for display."""
import re,os,matplotlib;matplotlib.use("Agg");import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,"WYVERN_E4_flight_wiring_connected.kicad_sch")).read()
fig,ax=plt.subplots(figsize=(16,11),dpi=150)
for a,b,c,d in re.findall(r'\(rectangle \(start ([\d.\-]+) ([\d.\-]+)\) \(end ([\d.\-]+) ([\d.\-]+)\)',src):
    a,b,c,d=map(float,(a,b,c,d))
    ax.add_patch(Rectangle((a,-max(b,d)),abs(c-a),abs(d-b),fill=True,fc="#eef4fb",ec="#20507a",lw=1.1))
for pts in re.findall(r'\(wire \(pts ((?:\(xy [\d.\-]+ [\d.\-]+\) ?)+)\)',src):
    xy=re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)',pts)
    xs=[float(x) for x,y in xy]; ys=[-float(y) for x,y in xy]
    ax.plot(xs,ys,"-",color="#c0392b",lw=0.7)
for x,y in re.findall(r'\(junction \(at ([\d.\-]+) ([\d.\-]+)\)',src):
    ax.plot(float(x),-float(y),".",color="#c0392b",ms=3)
for txt,x,y,sz in re.findall(r'\(text "((?:[^"\\]|\\.)*)" \(at ([\d.\-]+) ([\d.\-]+)[^)]*\).*?\(size ([\d.]+)',src):
    ax.text(float(x),-float(y),txt.replace('\\"','"'),fontsize=float(sz)*2.6,va="center",ha="left",color="#123",zorder=5)
ax.set_aspect("equal");ax.axis("off");plt.tight_layout()
out=os.path.join(HERE,"WYVERN_E4_flight_wiring_connected_preview.png")
plt.savefig(out,bbox_inches="tight",facecolor="white");print("wrote",out)
