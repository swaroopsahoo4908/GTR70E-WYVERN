#!/usr/bin/env python3
"""GTR70E WYVERN fin-control -- generated wiring + power diagrams (do not hand-edit the outputs).

W1_wiring.png/svg       every conductor: Feather RP2040 RFM95 pins -> servos, sensors, SD, power
W2_power_tree.png/svg   2S pack -> MOSFET switch -> servo rail + 5 V buck -> Feather 3V3 LDO
W3_system.png/svg       flight + ground segment data flow
W4_spine_perfboard.png  avionics spine face map + the 16 x 62 mm power perfboard layout
W5_harness.csv / .md    every conductor as a build list: from, to, signal, wire, length, termination
Pin numbers are read from firmware/wyvern_fin/fc_config.h so the drawing cannot drift from code.
"""
import os, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = open(os.path.join(HERE, "..", "firmware", "wyvern_fin", "fc_config.h")).read()

def define(name):
    m = re.search(rf"#define\s+{name}\s+([^\s/]+)", CFG); return m.group(1) if m else "?"
SERVO_PINS = [int(x) for x in re.search(r"WYV_PIN_SERVO\[4\]\s*=\s*\{([^}]*)\}", CFG).group(1).split(",")]

INK = "#111827"; W = dict(pwr="#dc2626", gnd="#111827", sig="#2563eb", i2c="#16a34a", spi="#9333ea", ana="#ea580c", rf="#0284c7", vsw="#b91c1c")

def box(ax, x, y, w, h, title, sub="", fc="#f8fafc", ec=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h - 0.25, title, ha="center", va="top", fontsize=9, weight="bold")
    if sub: ax.text(x + w / 2, y + h - 0.62, sub, ha="center", va="top", fontsize=6.8, color="#4b5563")

def pin(ax, x, y, label, side="r", color=INK):
    ax.plot(x, y, "o", ms=3.5, color=color)
    ax.text(x + (0.12 if side == "r" else -0.12), y, label, fontsize=6.6, va="center", ha="left" if side == "r" else "right", family="DejaVu Sans Mono")

def wire(ax, pts, color, lw=1.4, ls="-"):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round")

def save(fig, name):
    for e in ("png", "svg"): fig.savefig(os.path.join(HERE, f"{name}.{e}"), dpi=170 if e == "png" else None, bbox_inches="tight", facecolor="white")
    plt.close(fig); print("wrote", name)

def wiring():
    fig, ax = plt.subplots(figsize=(18, 10.5)); ax.set_xlim(0, 36); ax.set_ylim(3.6, 24); ax.axis("off")
    fx, fw = 14.5, 6.0
    top, dy = 19.0, 1.25
    left = [("USB  5V in", W["pwr"]), ("GND", W["gnd"]), ("3V  out", W["pwr"]), ("A0  GP26", W["ana"]),
            ("SCK GP14", W["spi"]), ("MO  GP15", W["spi"]), ("MI  GP8", W["spi"]), (f"D10 GP{define('WYV_PIN_SD_CS')}", W["spi"]),
            (f"D12 GP{define('WYV_PIN_BUZZER')}", W["sig"]),
            (f"TX GP{define('WYV_PIN_SDA_AUX')} SDA0", W["i2c"]), (f"RX GP{define('WYV_PIN_SCL_AUX')} SCL0", W["i2c"])]
    right = [(f"D5  GP{SERVO_PINS[0]}", W["sig"]), (f"D6  GP{SERVO_PINS[1]}", W["sig"]), (f"D9  GP{SERVO_PINS[2]}", W["sig"]),
             (f"D11 GP{SERVO_PINS[3]}", W["sig"]), ("SDA GP2 (QT)", W["i2c"]), ("SCL GP3 (QT)", W["i2c"]),
             (f"D24 GP{define('WYV_PIN_BNO_INT')}", W["sig"]), (f"D25 GP{define('WYV_PIN_BNO_RST')}", W["sig"]), ("ANT / uFL", W["rf"])]
    yl = [top - i * dy for i in range(len(left))]; yr = [top - i * dy for i in range(len(right))]
    fy0 = yl[-1] - 1.6; fh = top + 1.6 - fy0
    box(ax, fx, fy0, fw, fh + 0.4, "Feather RP2040 RFM95", "Adafruit PID 5714", fc="#ecfdf5")
    for (lab, c), y in zip(left, yl): pin(ax, fx, y, lab, "r", c)
    for (lab, c), y in zip(right, yr): pin(ax, fx + fw, y, lab, "l", c)
    ax.text(fx + fw / 2, fy0 + 0.3, "onboard RFM95 on SPI1: CS GP16, RST GP17,\nDIO0 GP21, DIO1 GP22 · NeoPixel GP4 · LED GP13", ha="center", fontsize=6.4, color="#4b5563")
    # ---- left peripherals
    bx0, bx1 = 8.4, 12.6
    def lbox(y0, y1, t, sub, fc):
        box(ax, bx0, y1 - 0.45, bx1 - bx0, (y0 - y1) + 0.9, t, sub, fc=fc)
    lbox(yl[0], yl[0], "Pololu D24V10F5", "5 V 1 A buck", "#fee2e2")
    wire(ax, [(bx1, yl[0]), (fx, yl[0])], W["pwr"], 2)
    ax.text(bx1 - 0.2, yl[1] + 0.2, "all GND common (star at the 2810 board)", fontsize=6.3, ha="right")
    wire(ax, [(bx1 + 0.05, yl[1]), (fx, yl[1])], W["gnd"], 1.4, "--")
    lbox(yl[3], yl[3], "Vbat divider", "100k/47k + 100 nF", "#ffedd5")
    wire(ax, [(bx1, yl[3]), (fx, yl[3])], W["ana"], 1.4)
    lbox(yl[4], yl[7], "microSD breakout", "Adafruit 4682\nCLK / DI / DO / CS\n(3V + GND from Feather 3V)", "#f5f3ff")
    for y in yl[4:8]: wire(ax, [(bx1, y), (fx, y)], W["spi"], 1.4)
    wire(ax, [(fx, yl[2]), (13.4, yl[2]), (13.4, yl[4] + 0.3), (bx1, yl[4] + 0.3)], W["pwr"], 1.0)
    lbox(yl[8], yl[8], "Piezo via 2N3904", "1 kΩ base", "#f1f5f9")
    wire(ax, [(bx1, yl[8]), (fx, yl[8])], W["sig"], 1.4)
    # core-1 I2C bus (Wire, I2C0) on the TX / RX pads: the BME688 alone
    box(ax, bx0, yl[10] - 0.55, bx1 - bx0, yl[9] - yl[10] + 1.1, "BME688  0x77", "Adafruit 5046 · spine -Y", fc="#ecfeff")
    for y in yl[9:11]: wire(ax, [(bx1, y), (fx, y)], W["i2c"], 1.8)
    ax.text(fx - 0.2, yl[10] - 0.85, "I2C0 (core 1): QT-to-header cable onto TX / RX + 3V + GND", fontsize=6.3, color=W["i2c"], ha="right")
    # ---- power chain (top-left) + VSW buses
    box(ax, 0.4, 20.6, 3.6, 2.4, "2S LiPo 450 mAh", "XT30 · 8.7 V full", fc="#fef3c7")
    box(ax, 4.7, 20.6, 3.6, 2.4, "Pololu 2810", "MOSFET switch (LV)", fc="#fee2e2")
    box(ax, 4.3, 16.9, 3.2, 2.4, "Screw switch", "M2 bolt: CTRL->GND = ON\nØ3 access hole", fc="#fee2e2")
    wire(ax, [(4.0, 21.8), (4.7, 21.8)], W["pwr"], 2.4)
    wire(ax, [(5.9, 20.6), (5.9, 19.3)], W["gnd"], 1.2); ax.text(6.05, 19.95, "CTRL", fontsize=6.3)
    vx = 7.95
    wire(ax, [(8.3, 21.8), (vx + 0.6, 21.8), (vx + 0.6, 23.3), (33.6, 23.3), (33.6, yr[3] - 0.25)], W["vsw"], 2.6)
    ax.text(12, 23.5, "VSW — switched 2S rail: straight to the HV servos (X08 Plus 3.8-8.4 V), the buck, and the divider", fontsize=7.2, color=W["vsw"])
    wire(ax, [(vx + 0.6, 21.8), (vx + 0.6, 21.0), (vx, 21.0), (vx, yl[3]), (bx0, yl[3])], W["vsw"], 1.6)
    wire(ax, [(vx, yl[0]), (bx0, yl[0])], W["vsw"], 1.6)
    ax.add_patch(Rectangle((32.9, 22.55), 0.5, 0.45, fc="white", ec=INK)); ax.text(31.3, 22.2, "470 µF low-ESR\n+ 100 nF", fontsize=6.3, ha="center")
    # ---- right peripherals
    rx0, rx1 = 24.0, 30.2
    names = ["A+  az 0", "A-  az 180", "B+  az 90", "B-  az 270"]
    for i in range(4):
        y = yr[i]
        box(ax, rx0, y - 0.5, rx1 - rx0, 1.0, f"Servo {i}  {names[i]}  · KST X08 Plus", "", fc="#eff6ff")
        wire(ax, [(fx + fw, y), (rx0, y)], W["sig"], 1.4)
        wire(ax, [(33.6, y), (rx1, y)], W["vsw"], 1.2)
    ax.text(30.4, yr[3] - 0.95, "JR lead: orange sig · red VSW · brown GND", fontsize=6.3)
    box(ax, rx0, yr[7] - 0.5, rx1 - rx0, yr[4] - yr[7] + 1.0, "BNO085  0x4A", "Adafruit 4754 · spine +X, lowest board\nI2C1 (core 0) + INT / RST", fc="#fdf2f8")
    for y in yr[4:6]: wire(ax, [(fx + fw, y), (rx0, y)], W["i2c"], 1.8)
    for y in yr[6:8]: wire(ax, [(fx + fw, y), (rx0, y)], W["sig"], 1.2)
    ax.text(22.0, yr[6] + 0.15, "INT", fontsize=6.3); ax.text(22.0, yr[7] + 0.15, "RST", fontsize=6.3)
    box(ax, 31.2, yr[7] - 0.5, 4.4, yr[5] - yr[7] + 1.0, "ADXL375  0x53", "Adafruit 5374\n±200 g · spine -Y", fc="#fae8ff")
    wire(ax, [(rx1, yr[5]), (31.2, yr[5])], W["i2c"], 1.8); wire(ax, [(rx1, yr[5] - 0.35), (31.2, yr[5] - 0.35)], W["i2c"], 1.8)
    ax.text(30.3, yr[5] + 0.25, "QT 100 mm", fontsize=6.0, color=W["i2c"])
    ax.text(22.3, yr[4] + 0.2, "QT 300 mm", fontsize=6.3, color=W["i2c"])
    wire(ax, [(fx + fw, yr[8]), (26.0, yr[8])], W["rf"], 1.6); ax.plot([26.0, 30.5], [yr[8], yr[8]], color=W["rf"], lw=3)
    ax.text(26.0, yr[8] - 0.55, "915 MHz 1/4-wave whip (78 mm) on ANT pad or uFL pigtail; up the wall over the Feather (+X face), >= 20 mm from the central Al bypass", fontsize=6.3, color=W["rf"])
    ax.set_title("W1  Flight computer wiring — generated from firmware/wyvern_fin/fc_config.h", fontsize=11, loc="left")
    save(fig, "W1_wiring")

def power_tree():
    fig, ax = plt.subplots(figsize=(13.5, 5.6)); ax.set_xlim(0, 26.6); ax.set_ylim(0, 10.6); ax.axis("off")
    def b(x, y, t, s, c): box(ax, x, y, 4.6, 2.2, t, s, fc=c)
    b(0.3, 4, "2S LiPo", "450 mAh · 8.7 V max\n6.4 V cutoff (fw)", "#fef3c7")
    b(5.6, 4, "Pololu 2810 switch", "screw switch on CTRL\n16 mΩ · 3 A cont.", "#fee2e2")
    b(11.0, 7.2, "Servo rail VSW", "4 x KST X08 Plus direct\nidle ~60 mA · flight ~0.7 A avg\n470 µF bulk", "#eff6ff")
    b(11.0, 4, "D24V10F5 buck", "5 V · eta ~0.88", "#fee2e2")
    b(11.0, 0.8, "Vbat divider", "100k/47k -> A0", "#ffedd5")
    b(16.4, 4, "Feather USB pin", "5 V -> AP2112 3V3 LDO\n500 mA peak", "#ecfdf5")
    b(21.4, 7.2, "3V3 loads", "RP2040, RFM95 (120 mA TX), BNO085,\nADXL375, BME688, uSD", "#ecfdf5")
    b(21.4, 4, "5V loads", "piezo buzzer", "#f1f5f9")
    for (x0, y0, x1, y1) in ((4.9, 5.1, 5.6, 5.1), (10.2, 5.1, 11.0, 5.1), (10.2, 5.1, 10.6, 8.3), (10.6, 8.3, 11.0, 8.3), (10.6, 5.1, 10.6, 1.9), (10.6, 1.9, 11.0, 1.9),
                           (15.6, 5.1, 16.4, 5.1), (21.0, 5.1, 21.4, 5.1), (21.0, 5.1, 21.0, 8.3), (21.0, 8.3, 21.4, 8.3)):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>" if (x1 - x0) > 0.3 else "-", lw=1.4, color="#b91c1c"))
    import json as _j
    bb = _j.load(open(os.path.join(HERE, "..", "..", "Simulations", "plots_power", "battery_budget.json")))
    ax.text(0.3, 10.1, f"Battery budget (Simulations/wf_power.py): 25 min pad idle ~{bb['idle_mA']:.0f} mA + 1 min flight ~{bb['flight_mA'] / 1000:.2f} A = "
            f"{bb['mission_mAh']:.0f} mAh -> 450 mAh pack carries {bb['margin_x']:.1f}x margin after derating", fontsize=8)
    ax.set_title("W2  Power tree", fontsize=11, loc="left")
    save(fig, "W2_power_tree")

def system():
    fig, ax = plt.subplots(figsize=(16, 7)); ax.set_xlim(0, 32); ax.set_ylim(0, 14); ax.axis("off")
    ax.add_patch(Rectangle((0.2, 0.3), 17.2, 13.2, fc="#f8fafc", ec="#94a3b8", lw=1, ls="--")); ax.text(0.5, 13.0, "FLIGHT SEGMENT (in the control tube)", fontsize=9, weight="bold", color="#475569")
    ax.add_patch(Rectangle((18.4, 0.3), 13.4, 13.2, fc="#f0f9ff", ec="#94a3b8", lw=1, ls="--")); ax.text(18.7, 13.0, "GROUND SEGMENT (RSO table)", fontsize=9, weight="bold", color="#475569")
    box(ax, 6.2, 5.0, 5.4, 4.6, "RP2040 (Feather)", "core 0: attitude 400 Hz, high-g,\nstate machine, control 200 Hz,\nauthority manoeuvre, 4 PWM\ncore 1: baro, radio, log", fc="#ecfdf5")
    box(ax, 0.6, 9.2, 4.6, 2.4, "BNO085 + ADXL375", "gyro / accel / GRV, ±200 g\nI2C1, core 0", fc="#fdf2f8")
    box(ax, 0.6, 6.0, 4.6, 2.4, "BME688", "P / T / RH\nI2C0, core 1", fc="#ecfeff")
    box(ax, 0.6, 2.8, 4.6, 2.4, "Vbat ADC", "2S divider", fc="#ffedd5")
    box(ax, 12.6, 9.2, 4.4, 2.4, "4 x servos", "fins A+, A-, B+, B-", fc="#eff6ff")
    box(ax, 12.6, 6.0, 4.4, 2.4, "microSD (only log)", "100 Hz, 96 B records\n+ MANxxx.TXT summary", fc="#f5f3ff")
    box(ax, 12.6, 2.8, 4.4, 2.4, "QSPI flash", "program only (no log)", fc="#f1f5f9")
    box(ax, 6.2, 0.8, 5.4, 2.6, "RFM95W 915 MHz", "SF7 / 500 kHz / +20 dBm\nW 20 Hz · M x5", fc="#e0f2fe")
    box(ax, 19.0, 0.8, 5.6, 3.0, "Feather RP2040 RFM95", "ground station: LoRa RX,\nuplink TX, tagged CSV on USB", fc="#e0f2fe")
    box(ax, 26.0, 5.0, 5.4, 3.0, "Laptop", "wyvern_host.py: record,\nlive plots, ARM / ZERO", fc="#f8fafc")
    for (x0, y0, x1, y1, c, t) in ((5.2, 10.4, 6.2, 8.6, "#16a34a", "I2C"), (5.2, 7.2, 6.2, 7.2, "#16a34a", "I2C"), (5.2, 4.0, 6.2, 5.6, "#ea580c", "ADC"),
                                   (11.6, 8.6, 12.6, 10.4, "#2563eb", "PWM 200 Hz"), (11.6, 7.2, 12.6, 7.2, "#9333ea", "SPI1"),
                                   (8.9, 5.0, 8.9, 3.4, "#9333ea", "SPI1"), (11.6, 2.1, 19.0, 2.4, "#0284c7", "LoRa downlink"), (19.0, 1.5, 11.6, 1.5, "#dc2626", "pad uplink: ARM / ZERO"),
                                   (24.6, 2.6, 26.0, 6.0, "#111827", "USB CSV")):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.4, color=c))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.25, t, fontsize=6.8, color=c, ha="center")
    ax.set_title("W3  System architecture and data paths", fontsize=11, loc="left")
    save(fig, "W3_system")

def spine_perfboard():
    """Left: cross-section of the avionics spine around the central bypass tube (from
    wf_core.SPINE_BOARDS; the vendor-model fit check is D6). Right: the power perfboard."""
    import math, sys
    sys.path.insert(0, os.path.join(HERE, "..", "..", "Simulations")); import wf_core as C
    from matplotlib.patches import Circle, Polygon
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(15, 7.2), gridspec_kw=dict(width_ratios=[1, 1.15]))
    R, RI = C.R, C.RI
    a0.set_aspect("equal"); a0.set_xlim(-R - 14, R + 14); a0.set_ylim(-R - 10, R + 10); a0.axis("off")
    a0.add_patch(Circle((0, 0), R, fc="#e5e7eb", ec=INK)); a0.add_patch(Circle((0, 0), RI, fc="white", ec=INK))
    f = C.SPINE_FLAT
    a0.add_patch(Rectangle((-f, -f), 2 * f, 2 * f, fc="#bbf7d0", ec=INK))
    a0.add_patch(Circle((0, 0), C.BYPASS["od"] / 2, fc="#9ca3af", ec=INK)); a0.add_patch(Circle((0, 0), C.BYPASS["id"] / 2, fc="white", ec=INK))
    a0.text(0, 0, "3/8 in\nbypass", ha="center", va="center", fontsize=5.5)
    cols = dict(battery="#fde68a", bno085="#f9a8d4", feather="#065f46", perfboard="#7c2d12", bme688="#155e75", microsd="#0e7490",
                gps="#4d7c0f", adxl375="#a21caf")
    for bd in C.SPINE_BOARDS:
        P = C.board_plane(bd); th = 14.0 if bd["key"] == "battery" else 1.6; off = bd.get("offset", 0.0)
        az = math.radians(dict(px=0, py=90, nx=180, ny=270)[bd["face"]]); ca, sa = math.cos(az), math.sin(az)
        pts = [(P, off - bd["W"] / 2), (P + th, off - bd["W"] / 2), (P + th, off + bd["W"] / 2), (P, off + bd["W"] / 2)]
        a0.add_patch(Polygon([(x * ca - y * sa, x * sa + y * ca) for x, y in pts], fc=cols[bd["key"]], ec=INK, alpha=0.75))
        for (u, v) in bd["holes"][:1] + ([bd["holes"][1]] if len(bd["holes"]) == 2 else bd["holes"][1:2]):
            t = u - bd["W"] / 2 + off
            q = [(f, t - 2), (P, t - 2), (P, t + 2), (f, t + 2)]
            if bd["key"] != "battery":
                a0.add_patch(Polygon([(x * ca - y * sa, x * sa + y * ca) for x, y in q], fc="#9ca3af", ec=INK, lw=0.4))
    a0.text(R + 2, 6, "+X: BNO085 (low)\n+ Feather (high)\n2 mm standoffs", fontsize=7, va="center")
    a0.text(-R - 2, 6, "-X: 2S LiPo\non foam tape", fontsize=7, va="center", ha="right")
    a0.text(0, R + 3, "+Y: power perfboard, 9 mm pillars", fontsize=7, ha="center")
    a0.text(0, -R - 6, "-Y: BME688 (low), microSD, ADXL375 (high),\none line of screws each, 9 mm pillars", fontsize=7, ha="center")
    a0.annotate("Ø3 hex-key hole to the screw switch", xy=(0, R), xytext=(12, R + 8), fontsize=6.5, arrowprops=dict(arrowstyle="->"))
    a0.set_title(f"Spine section looking down ({2*RI:.1f} mm bore, every board shown at once)", fontsize=10, loc="left")
    # ---- perfboard: 6 columns x 23 rows, 2.54 mm pitch, 16 x 60 mm
    a1.set_xlim(-2, 34); a1.set_ylim(-6, 64); a1.set_aspect("equal"); a1.axis("off")
    a1.add_patch(Rectangle((0, 0), 16, 62, fc="#fef3c7", ec=INK))
    for i in range(6):
        for j in range(24):
            a1.plot(1.65 + i * 2.54, 1.9 + j * 2.54, "o", ms=1.2, color="#a16207")
    def part(x, y, w, h, t, c, ls="-"):
        a1.add_patch(Rectangle((x, y), w, h, fc=c, ec=INK, alpha=0.9, ls=ls)); a1.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=6.0)
    part(1.65, 4.0, 12.7, 17.78, "Pololu D24V10F5\n5 V buck\n12.7 x 17.8", "#fee2e2")
    part(6.0, 25.0, 4.0, 4.0, "", "#fca5a5"); a1.annotate("screw switch: M2 into a brass\nstandoff, CTRL to GND\n(under the Ø3 wall hole)", xy=(10, 27), xytext=(17, 25), fontsize=6.2, arrowprops=dict(arrowstyle="-", lw=0.5))
    part(0.4, 30.0, 15.24, 15.24, "Pololu 2810\nMOSFET switch\n15.2 x 15.2", "#fecaca")
    a1.add_patch(Circle((8, 53.0), 6.0, fc="#374151", ec=INK)); a1.text(8, 53.0, "piezo\n12 mm", color="white", ha="center", va="center", fontsize=6)
    part(5.0, 20.0, 6.3, 11.0, "", "#dbeafe", ls="--"); a1.annotate("UNDERSIDE (9 mm gap to the spine):\n470 µF 10 V 6.3 x 11 laid flat,\n100k/47k divider + 100 nF, 2N3904 + 1k", xy=(11, 22), xytext=(17, 6), fontsize=6.2, arrowprops=dict(arrowstyle="-", lw=0.5))
    for (u, v) in [h for h in [b for b in C.SPINE_BOARDS if b["key"] == "perfboard"][0]["holes"]]:
        a1.add_patch(Circle((u, v), 1.1, fc="white", ec=INK))
    for (y, t, c) in ((58, "XT30 pigtail in (pack)", W["pwr"]), (40, "VOUT -> VSW bus", W["vsw"]), (17, "5 V -> Feather USB pin", W["pwr"]), (0, "VSW -> 4 servo leads (JR)", W["vsw"])):
        a1.annotate(t, xy=(16, y), xytext=(17, y), fontsize=6.6, va="center", color=c)
    a1.text(0, -4.5, "16 x 62 mm, 0.1 in perf, 1.6 mm FR4 · 4 x M2 on pillars (holes at 3.5 / 12.5 mm across) · top parts <= 6.5 mm tall", fontsize=6.6)
    a1.set_title("Power perfboard (+Y face of the spine)", fontsize=10, loc="left")
    fig.suptitle("W4  Avionics spine around the central bypass tube", x=0.02, ha="left", fontsize=11)
    save(fig, "W4_spine_perfboard")

def harness():
    """Build list. Lengths are cut lengths with ~15 mm service loop, measured on the fit-check
    assembly (Feather and BNO on +X, BME / microSD / ADXL375 on -Y, perfboard on +Y, servos in the
    ring 30-40 mm below the spine foot, leads up the diagonal slots)."""
    import csv
    P = lambda n: f"GP{define(n)}"
    rows = [
        # (group, from, to, signal, wire, length_mm, termination / note)
        ("power", "2S LiPo XT30", "perfboard XT30 pigtail", "BAT+ / BAT-", "16 AWG silicone pair", 60, "XT30 mated pair; the only removable power joint"),
        ("power", "perfboard 2810 VOUT", "perfboard VSW bus", "VSW", "solid 22 AWG bus wire", 40, "runs the length of the perfboard edge"),
        ("power", "perfboard 2810 CTRL", "screw-switch standoff", "CTRL", "on-board", 0, "screw closes CTRL to GND = ON"),
        ("power", "perfboard VSW bus", "D24V10F5 VIN", "VSW", "on-board", 0, ""),
        ("power", "D24V10F5 VOUT", "Feather USB pin", "5V", "24 AWG silicone, red", 90, "solder to the USB pad, +Y to +X face around the spine"),
        ("power", "perfboard GND star", "Feather GND", "GND", "24 AWG silicone, black", 90, "star point is the 2810 GND pad"),
        ("power", "perfboard VSW bus", "470 µF + 100 nF (underside)", "VSW", "on-board", 0, "servo rail bulk cap"),
        ("power", "perfboard divider 100k/47k + 100 nF", f"Feather A0 ({P('WYV_PIN_VBAT')})", "VBAT_SENSE", "28 AWG silicone, orange", 90, "VBAT x 47/147"),
        ("servo", "servo 0 A+ (az 0) red / brown", "perfboard VSW / GND", "VSW / GND", "servo lead, shortened", 110, "solder; up the +X/+Y diagonal slot"),
        ("servo", "servo 1 A- (az 180) red / brown", "perfboard VSW / GND", "VSW / GND", "servo lead, shortened", 130, "up the -X/-Y slot, round the spine foot"),
        ("servo", "servo 2 B+ (az 90) red / brown", "perfboard VSW / GND", "VSW / GND", "servo lead, shortened", 100, "up the +Y slot"),
        ("servo", "servo 3 B- (az 270) red / brown", "perfboard VSW / GND", "VSW / GND", "servo lead, shortened", 130, ""),
        ("servo", "servo 0 orange", f"Feather D5 ({SERVO_PINS and 'GP'+str(SERVO_PINS[0])})", "PWM A+", "servo lead signal", 120, "200 Hz, 1 µs"),
        ("servo", "servo 1 orange", f"Feather D6 (GP{SERVO_PINS[1]})", "PWM A-", "servo lead signal", 140, ""),
        ("servo", "servo 2 orange", f"Feather D9 (GP{SERVO_PINS[2]})", "PWM B+", "servo lead signal", 120, ""),
        ("servo", "servo 3 orange", f"Feather D11 (GP{SERVO_PINS[3]})", "PWM B-", "servo lead signal", 140, ""),
        ("I2C1 core 0", "Feather STEMMA QT", "BNO085 STEMMA QT", "3V3 GND SDA SCL", "STEMMA QT 100 mm (4210)", 100, "Wire1, 400 kHz"),
        ("I2C1 core 0", "BNO085 STEMMA QT (2nd port)", "ADXL375 STEMMA QT", "3V3 GND SDA SCL", "STEMMA QT 300 mm (5384, owned)", 300, "+X low to -Y high; fold the slack under a strap"),
        ("I2C1 core 0", "BNO085 INT", f"Feather D24 ({P('WYV_PIN_BNO_INT')})", "INT", "28 AWG silicone", 70, "data-ready, active low"),
        ("I2C1 core 0", "BNO085 RST", f"Feather D25 ({P('WYV_PIN_BNO_RST')})", "RST", "28 AWG silicone", 70, ""),
        ("I2C0 core 1", "BME688 STEMMA QT", f"Feather TX {P('WYV_PIN_SDA_AUX')} / RX {P('WYV_PIN_SCL_AUX')} / 3V / GND", "SDA0 SCL0 3V3 GND", "STEMMA QT to male header 150 mm (4209)", 150, "header pins soldered into TX, RX, 3V, GND; blue = SDA, yellow = SCL"),
        ("SPI1", "microSD 4682 CLK / SI / SO / CS", f"Feather SCK {P('WYV_PIN_SCK')} / MO {P('WYV_PIN_MOSI')} / MI {P('WYV_PIN_MISO')} / D10 {P('WYV_PIN_SD_CS')}", "SCK MOSI MISO CS", "4 x 28 AWG silicone, twisted with GND", 110, "shares SPI1 with the onboard radio; 3V only"),
        ("SPI1", "microSD 4682 3V / GND", "Feather 3V / GND", "3V3 GND", "2 x 28 AWG", 110, ""),
        ("I/O", "perfboard 2N3904 base (1k)", f"Feather D12 ({P('WYV_PIN_BUZZER')})", "BUZZER", "28 AWG silicone", 90, "piezo on the perfboard, from VSW? no: from 5V via the NPN"),
        ("RF", "Feather ANT pad", "1/4-wave whip", "915 MHz", "78 mm 22 AWG solid", 78, "up the wall over the +X face, >= 20 mm from the Al bypass tube"),
    ]
    rows[-2] = rows[-2][:6] + ("piezo between the 5 V rail and the NPN collector",)
    with open(os.path.join(HERE, "W5_harness.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["group", "from", "to", "signal", "wire", "cut_length_mm", "note"]); w.writerows(rows)
    md = ["# W5 harness build list (generated by gen_wiring.py from fc_config.h)", "",
          "| # | group | from | to | signal | wire | cut length | note |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        md.append(f"| {i} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5] or 'on board'}{' mm' if r[5] else ''} | {r[6]} |")
    tot = {}
    for r in rows:
        if "AWG" in r[4] and "x" not in r[4].split()[0]: tot[r[4]] = tot.get(r[4], 0) + r[5]
    md += ["", "Wire to cut (single conductors, before service loops): " + ", ".join(f"{k}: {v} mm" for k, v in tot.items()) + "."]
    open(os.path.join(HERE, "W5_harness.md"), "w").write("\n".join(md) + "\n")
    print("wrote W5_harness")

if __name__ == "__main__":
    wiring(); power_tree(); system(); spine_perfboard(); harness()
