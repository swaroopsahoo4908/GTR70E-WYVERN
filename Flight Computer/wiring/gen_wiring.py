#!/usr/bin/env python3
"""GTR70E WYVERN fin-control -- generated wiring + power diagrams (do not hand-edit the outputs).

W1_wiring.png/svg       every conductor: Pico 2 W pins -> servos, sensors, microSD, arm button, power (rev 4b)
W2_power_tree.png/svg   2S pack -> MOSFET switch -> 5 V servo buck + 5 V logic buck -> Pico 2 W VSYS
W3_system.png/svg       flight computer data flow (no radio)
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
    left = [("VSYS  5 V in", W["pwr"]), ("GND", W["gnd"]), ("3V3 OUT", W["pwr"]), (f"GP{define('WYV_PIN_VBAT')} / ADC0", W["ana"]),
            (f"GP{define('WYV_PIN_BUTTON')}  button", W["sig"]), (f"GP{define('WYV_PIN_LED_EXT')}  LED", W["sig"]),
            (f"GP{define('WYV_PIN_SDA1')} SDA1", W["i2c"]), (f"GP{define('WYV_PIN_SCL1')} SCL1", W["i2c"]),
            (f"GP{define('WYV_PIN_SD_SCK')} SCK", W["spi"]), (f"GP{define('WYV_PIN_SD_MOSI')} MOSI", W["spi"]),
            (f"GP{define('WYV_PIN_SD_MISO')} MISO", W["spi"]), (f"GP{define('WYV_PIN_SD_CS')} CS", W["spi"])]
    right = [(f"GP{SERVO_PINS[0]}  PWM", W["sig"]), (f"GP{SERVO_PINS[1]}  PWM", W["sig"]), (f"GP{SERVO_PINS[2]}  PWM", W["sig"]),
             (f"GP{SERVO_PINS[3]}  PWM", W["sig"]), (f"GP{define('WYV_PIN_SDA')} SDA0", W["i2c"]), (f"GP{define('WYV_PIN_SCL')} SCL0", W["i2c"]),
             (f"GP{define('WYV_PIN_BNO_INT')}  INT", W["sig"]), (f"GP{define('WYV_PIN_BNO_RST')}  RST", W["sig"])]
    yl = [top - i * dy for i in range(len(left))]; yr = [top - i * dy for i in range(len(right))]
    fy0 = yl[-1] - 1.6; fh = top + 1.6 - fy0
    box(ax, fx, fy0, fw, fh + 0.4, "Raspberry Pi Pico 2 W", "RP2350 · radio unused", fc="#ecfdf5")
    for (lab, c), y in zip(left, yl): pin(ax, fx, y, lab, "r", c)
    for (lab, c), y in zip(right, yr): pin(ax, fx + fw, y, lab, "l", c)
    ax.text(fx + fw / 2, fy0 + 0.3, "USB to the laptop only on the bench / pad\n1N5817 Schottky from the 5 V buck into VSYS", ha="center", fontsize=6.4, color="#4b5563")
    bx0, bx1 = 8.4, 12.6
    def lbox(y0, y1, t, sub, fc):
        box(ax, bx0, y1 - 0.45, bx1 - bx0, (y0 - y1) + 0.9, t, sub, fc=fc)
    lbox(yl[0], yl[0], "MPM3610 + 1N5817", "5 V logic buck (4739) -> VSYS", "#fee2e2")
    wire(ax, [(bx1, yl[0]), (fx, yl[0])], W["pwr"], 2)
    ax.text(bx1 - 0.2, yl[1] + 0.2, "all GND common (star on the perfboard)", fontsize=6.3, ha="right")
    wire(ax, [(bx1 + 0.05, yl[1]), (fx, yl[1])], W["gnd"], 1.4, "--")
    ax.text(bx1 - 0.2, yl[2] + 0.2, "3V3 OUT -> red leads of both QT cables + 4682 3V", fontsize=6.3, ha="right", color=W["pwr"])
    lbox(yl[3], yl[3], "Vbat divider", "100k/47k + 100 nF", "#ffedd5")
    wire(ax, [(bx1, yl[3]), (fx, yl[3])], W["ana"], 1.4)
    lbox(yl[4], yl[5], "Arm button + LED", "-Y wall cradle\n6 mm tact to GND · 3 mm red\nLED via 220 R to GND", "#fef9c3")
    for y in yl[4:6]: wire(ax, [(bx1, y), (fx, y)], W["sig"], 1.4)
    box(ax, bx0, yl[7] - 0.55, bx1 - bx0, yl[6] - yl[7] + 1.1, "BMP388 + BME688", "spine -Y, both on I2C1\n0x76 (ADDR jumper closed) + 0x77", fc="#ecfeff")
    for y in yl[6:8]: wire(ax, [(bx1, y), (fx, y)], W["i2c"], 1.8)
    box(ax, bx0, yl[11] - 0.55, bx1 - bx0, yl[8] - yl[11] + 1.1, "microSD  Adafruit 4682", "spine -Y, 3 V only\nCLK / DI / DO / CS\nflight log", fc="#f5f3ff")
    for y in yl[8:12]: wire(ax, [(bx1, y), (fx, y)], W["spi"], 1.4)
    ax.text(fx - 0.2, yl[11] - 0.85, "BMP388 -> BME688 on a QT 100 mm (4210); QT-to-male-header (4209) into the Pico", fontsize=6.3, color=W["i2c"], ha="right")
    # ---- power chain (top-left) + VSW buses
    box(ax, 0.4, 20.6, 3.6, 2.4, "2S LiPo 450 mAh", "XT30 · 8.4 V full", fc="#fef3c7")
    box(ax, 4.7, 20.6, 3.6, 2.4, "Pololu 2810", "MOSFET switch (LV)", fc="#fee2e2")
    ax.text(6.5, 20.15, "slide reached through a\n4 x 12 mm wall slot (no screw switch)", fontsize=6.3, ha="center")
    wire(ax, [(4.0, 21.8), (4.7, 21.8)], W["pwr"], 2.4)
    vx = 7.95
    wire(ax, [(8.3, 21.8), (vx + 0.6, 21.8), (vx + 0.6, 23.3), (33.6, 23.3), (33.6, yr[3] - 0.25)], W["vsw"], 2.6)
    ax.text(12, 23.5, "VSW — switched 2S rail: to the two MPM3610 bucks (logic 5 V, servo 5 V) and the divider; servos never see 2S", fontsize=7.2, color=W["vsw"])
    wire(ax, [(vx + 0.6, 21.8), (vx + 0.6, 21.0), (vx, 21.0), (vx, yl[3]), (bx0, yl[3])], W["vsw"], 1.6)
    wire(ax, [(vx, yl[0]), (bx0, yl[0])], W["vsw"], 1.6)
    ax.add_patch(Rectangle((32.9, 22.55), 0.5, 0.45, fc="white", ec=INK)); ax.text(31.3, 22.2, "MPM3610 #2 (servo 5 V)\n470 µF low-ESR + 100 nF", fontsize=6.3, ha="center")
    rx0, rx1 = 24.0, 30.2
    names = ["A+  az 0", "A-  az 180", "B+  az 90", "B-  az 270"]
    for i in range(4):
        y = yr[i]
        box(ax, rx0, y - 0.5, rx1 - rx0, 1.0, f"Servo {i}  {names[i]}  · EMAX ES9251 II", "", fc="#eff6ff")
        wire(ax, [(fx + fw, y), (rx0, y)], W["sig"], 1.4)
        wire(ax, [(33.6, y), (rx1, y)], W["vsw"], 1.2)
    ax.text(30.4, yr[3] - 0.95, "JR lead: orange sig · red SRV 5 V · brown GND", fontsize=6.3)
    ax.text(fx + fw + 0.3, yr[0] + 0.75, f"PWM {define('WYV_SERVO_HZ')} Hz, 1 µs steps", fontsize=6.3, color=W["sig"])
    box(ax, rx0, yr[7] - 0.5, rx1 - rx0, yr[4] - yr[7] + 1.0, "BNO085  0x4A", "Adafruit 4754 · spine +X, lowest board\nI2C0 (alone on its bus) + INT / RST", fc="#fdf2f8")
    for y in yr[4:6]: wire(ax, [(fx + fw, y), (rx0, y)], W["i2c"], 1.8)
    for y in yr[6:8]: wire(ax, [(fx + fw, y), (rx0, y)], W["sig"], 1.2)
    ax.text(22.3, yr[4] + 0.2, "QT 150 mm", fontsize=6.3, color=W["i2c"])
    ax.set_title("W1  Flight computer wiring (rev 4b, Pico 2 W) — generated from firmware/wyvern_fin/fc_config.h", fontsize=11, loc="left")
    save(fig, "W1_wiring")

def power_tree():
    fig, ax = plt.subplots(figsize=(13.5, 5.6)); ax.set_xlim(0, 26.6); ax.set_ylim(0, 10.6); ax.axis("off")
    def b(x, y, t, s, c): box(ax, x, y, 4.6, 2.2, t, s, fc=c)
    b(0.3, 4, "2S LiPo", "450 mAh · 8.7 V max\n6.4 V cutoff (fw)", "#fef3c7")
    b(5.6, 4, "Pololu 2810 switch", "slide via wall slot\n16 mΩ · 3 A cont.", "#fee2e2")
    b(11.0, 7.2, "Servo rail SRV 5 V", "MPM3610 #2 -> 4 x EMAX ES9251 II\nidle ~40 mA · flight ~0.3 A avg\n470 µF bulk", "#eff6ff")
    b(11.0, 4, "MPM3610 buck", "5 V · eta ~0.85 · VIN 6-21 V", "#fee2e2")
    b(11.0, 0.8, "Vbat divider", "100k/47k -> A0", "#ffedd5")
    b(16.4, 4, "Pico 2 W VSYS", "5 V via 1N5817 -> RT6150\nbuck-boost -> 3V3", "#ecfdf5")
    b(21.4, 7.2, "3V3 loads", "RP2350 150 MHz (~30 mA), 4682 uSD,\nBNO085, BMP388, BME688", "#ecfdf5")
    b(21.4, 4, "arm button + LED", "-Y wall cradle\nGP14 / GP15", "#f1f5f9")
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
    ax.add_patch(Rectangle((0.2, 0.3), 21.2, 13.2, fc="#f8fafc", ec="#94a3b8", lw=1, ls="--")); ax.text(0.5, 13.0, "FLIGHT SEGMENT (in the control tube)", fontsize=9, weight="bold", color="#475569")
    ax.add_patch(Rectangle((22.4, 0.3), 9.4, 13.2, fc="#f0f9ff", ec="#94a3b8", lw=1, ls="--")); ax.text(22.7, 13.0, "BENCH / PAD (USB lead, removed before flight)", fontsize=8, weight="bold", color="#475569")
    box(ax, 7.2, 4.6, 6.0, 5.2, "Pico 2 W", "single loop on core 0, 150 MHz:\nBNO085 poll 400 Hz, baro 50 Hz,\nstate machine + control 200 Hz,\nauthority manoeuvre, 4 PWM,\nSD ring buffer, arm button", fc="#ecfdf5")
    box(ax, 0.6, 9.6, 5.0, 2.4, "BNO085", "gyro / accel / GRV\nI2C0 (GP4/5) + INT/RST", fc="#fdf2f8")
    box(ax, 0.6, 6.6, 5.0, 2.4, "BMP388", "pressure 50 Hz, x8 / IIR 3\nI2C1 (GP2/3), 0x76", fc="#ecfeff")
    box(ax, 0.6, 3.6, 5.0, 2.4, "BME688", "T / RH / P 10 Hz\nI2C1 (GP2/3), 0x77", fc="#ecfeff")
    box(ax, 0.6, 0.8, 5.0, 2.2, "Vbat ADC", "2S divider -> A0", fc="#ffedd5")
    box(ax, 14.8, 10.0, 6.0, 2.2, "4 x servos", "fins A+, A-, B+, B-", fc="#eff6ff")
    box(ax, 14.8, 6.2, 6.0, 2.4, "microSD (only record)", "Adafruit 4682 on SPI0\n100 Hz armed, 96 B + MANxxx.TXT", fc="#f5f3ff")
    box(ax, 14.8, 3.6, 6.0, 2.4, "arm button + LED", "-Y wall: hold 2 s, let go,\n1 s still -> zero + ARMED", fc="#fef9c3")
    box(ax, 24.0, 6.2, 7.0, 3.6, "Laptop", "wyvern_host.py --port: live plot\n--decode WYFnnn.BIN after recovery", fc="#f8fafc")
    for (x0, y0, x1, y1, c, t) in ((5.6, 10.8, 7.2, 8.8, "#16a34a", "I2C"), (5.6, 7.8, 7.2, 7.4, "#16a34a", "I2C"), (5.6, 4.8, 7.2, 6.0, "#16a34a", "I2C"),
                                   (5.6, 1.9, 7.2, 5.0, "#ea580c", "ADC"), (13.2, 9.6, 14.8, 11.0, "#2563eb", "PWM 200 Hz"),
                                   (13.2, 7.4, 14.8, 7.8, "#9333ea", "SPI0"), (14.8, 4.8, 13.2, 5.6, "#ca8a04", "GPIO"),
                                   (20.8, 7.2, 24.0, 7.2, "#111827", "card, after flight"), (13.2, 9.35, 24.0, 9.35, "#111827", "USB CSV 10 Hz (pad)")):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.4, color=c))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.25, t, fontsize=6.8, color=c, ha="center")
    ax.text(0.6, 0.35, "No radio in rev 4: nothing can command the rocket once the USB lead is off; the card is read after recovery.", fontsize=7, color="#475569")
    ax.set_title("W3  System architecture and data paths (rev 4)", fontsize=11, loc="left")
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
    a0.text(0, 0, "PC-FR\nbypass", ha="center", va="center", fontsize=5.5)
    cols = dict(battery="#fde68a", bno085="#f9a8d4", pico2w="#065f46", perfboard="#7c2d12", bme688="#155e75", bmp388="#0e7490", microsd="#6d28d9")
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
    a0.text(R + 2, 6, "+X: BNO085 (low)\n+ Pico 2 W (high)\n2 mm standoffs", fontsize=7, va="center")
    a0.text(-R - 2, 6, "-X: 2S LiPo\non foam tape", fontsize=7, va="center", ha="right")
    a0.text(0, R + 3, "+Y: power perfboard, 9 mm pillars", fontsize=7, ha="center")
    a0.text(0, -R - 6, "-Y: BME688, BMP388 (9 mm pillars), 4682 microSD (7 mm, top), one screw line each;\narm button + LED in the -Y wall cradle beside the 4682", fontsize=7, ha="center")
    a0.annotate("4 x 12 mm wall slot over the 2810 slide", xy=(0, R), xytext=(12, R + 8), fontsize=6.5, arrowprops=dict(arrowstyle="->"))
    a0.set_title(f"Spine section looking down ({2*RI:.1f} mm bore, every board shown at once)", fontsize=10, loc="left")
    # ---- perfboard: 6 columns x 23 rows, 2.54 mm pitch, 16 x 60 mm
    a1.set_xlim(-2, 34); a1.set_ylim(-6, 64); a1.set_aspect("equal"); a1.axis("off")
    a1.add_patch(Rectangle((0, 0), 16, 62, fc="#fef3c7", ec=INK))
    for i in range(6):
        for j in range(24):
            a1.plot(1.65 + i * 2.54, 1.9 + j * 2.54, "o", ms=1.2, color="#a16207")
    def part(x, y, w, h, t, c, ls="-"):
        a1.add_patch(Rectangle((x, y), w, h, fc=c, ec=INK, alpha=0.9, ls=ls)); a1.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=6.0)
    part(2.9, 4.0, 10.16, 17.14, "Adafruit\nMPM3610\n5 V logic\n10.2 x 17.1", "#fee2e2")
    part(2.9, 40.0, 10.16, 17.14, "Adafruit\nMPM3610\n5 V servo\n10.2 x 17.1", "#fee2e2")
    a1.text(8, 40, "(free: the 2810 moved\nto the wall cradle)", ha="center", va="center", fontsize=6.0, color="#6b7280")
    a1.annotate("Pololu 2810: in a printed cradle on the CT wall at +Y,\n" f"{C.SWITCH['z0']:.0f} mm up the spine, component side out; its slide\n"
                "sits under a 4 x 12 mm wall slot and moves around the\nairframe (toothpick). 3 x 22 AWG leads: VIN from the\nXT30, VOUT to the VSW bus, GND to the star.",
                xy=(16, 62), xytext=(17, 50), fontsize=6.2, arrowprops=dict(arrowstyle="-", lw=0.5))
    part(5.0, 20.0, 6.3, 11.0, "", "#dbeafe", ls="--"); a1.annotate("UNDERSIDE (9 mm gap to the spine):\n470 µF 10 V 6.3 x 11 laid flat,\n100k/47k divider + 100 nF", xy=(11, 22), xytext=(17, 6), fontsize=6.2, arrowprops=dict(arrowstyle="-", lw=0.5))
    for (u, v) in [h for h in [b for b in C.SPINE_BOARDS if b["key"] == "perfboard"][0]["holes"]]:
        a1.add_patch(Circle((u, v), 1.1, fc="white", ec=INK))
    for (y, t, c) in ((58, "XT30 pigtail in (pack) -> 2810 VIN", W["pwr"]), (40, "2810 VOUT -> VSW bus", W["vsw"]), (17, "5 V -> 1N5817 -> Pico VSYS", W["pwr"]), (0, "SRV 5 V -> 4 servo leads (JR)", W["vsw"])):
        a1.annotate(t, xy=(16, y), xytext=(17, y), fontsize=6.6, va="center", color=c)
    a1.text(0, -4.5, "16 x 62 mm, 0.1 in perf, 1.6 mm FR4 · 4 x M2 on pillars (holes at 3.5 / 12.5 mm across) · top parts <= 6.5 mm tall", fontsize=6.6)
    a1.set_title("Power perfboard (+Y face of the spine)", fontsize=10, loc="left")
    fig.suptitle("W4  Avionics spine around the central bypass tube", x=0.02, ha="left", fontsize=11)
    save(fig, "W4_spine_perfboard")

def harness():
    """Build list. Lengths are cut lengths with ~15 mm service loop, measured on the fit-check
    assembly (BNO085 and Pico 2 W on +X, BME688 / BMP388 / 4682 on -Y, perfboard on +Y, arm button in the -Y wall, servos in the
    ring 30-40 mm below the spine foot, leads up the diagonal slots)."""
    import csv
    P = lambda n: f"GP{define(n)}"
    rows = [
        # (group, from, to, signal, wire, length_mm, termination / note)
        ("power", "2S LiPo XT30", "perfboard XT30 pigtail", "BAT+ / BAT-", "16 AWG silicone pair", 60, "XT30 mated pair; the only removable power joint"),
        ("power", "XT30 pigtail (perfboard top)", "2810 VIN (wall cradle)", "BAT+", "22 AWG silicone, red", 50, "2810 sits in the CT-wall cradle at +Y, above the perfboard"),
        ("power", "2810 VOUT (wall cradle)", "perfboard VSW bus", "VSW", "22 AWG silicone, red", 50, "the VSW bus runs the length of the perfboard edge"),
        ("power", "2810 GND (wall cradle)", "perfboard GND star", "GND", "22 AWG silicone, black", 50, ""),
        ("power", "perfboard VSW bus", "MPM3610 VIN", "VSW", "on-board", 0, "EN unconnected (enabled by default; tie low to shut off)"),
        ("power", "MPM3610 5V", "1N5817 anode (on the perfboard)", "5V", "on-board", 0, "Schottky so USB on the bench can never back-feed the buck (Pico datasheet's external-supply circuit)"),
        ("power", "1N5817 cathode", "Pico VSYS (pin 39)", "5V", "24 AWG silicone, red", 90, "+Y to +X face around the spine"),
        ("power", "perfboard GND star", "Pico GND (pin 38)", "GND", "24 AWG silicone, black", 90, "star point on the perfboard"),
        ("power", "perfboard VSW bus", "MPM3610 #2 VIN (servo buck)", "VSW", "on-board", 0, "rev 3f: the ES9251 II is a 4.5-6 V servo"),
        ("power", "MPM3610 #2 5V", "perfboard SRV bus", "SRV", "on-board", 0, "servo rail only; EN unconnected"),
        ("power", "perfboard SRV bus", "470 µF + 100 nF (underside)", "SRV", "on-board", 0, "servo rail bulk cap"),
        ("power", "perfboard divider 100k/47k + 100 nF", f"Pico GP{define('WYV_PIN_VBAT')} (ADC0)", "VBAT_SENSE", "28 AWG silicone, orange", 90, "VBAT x 47/147; 3.3 V max at the pin"),
        ("servo", "servo 0 A+ (az 0) red / brown", "perfboard SRV / GND", "SRV / GND", "servo lead, shortened", 110, "solder; up the +X/+Y diagonal slot"),
        ("servo", "servo 1 A- (az 180) red / brown", "perfboard SRV / GND", "SRV / GND", "servo lead, shortened", 130, "up the -X/-Y slot, round the spine foot"),
        ("servo", "servo 2 B+ (az 90) red / brown", "perfboard SRV / GND", "SRV / GND", "servo lead, shortened", 100, "up the +Y slot"),
        ("servo", "servo 3 B- (az 270) red / brown", "perfboard SRV / GND", "SRV / GND", "servo lead, shortened", 130, ""),
        ("servo", "servo 0 orange", f"Pico GP{SERVO_PINS[0]}", "PWM A+", "servo lead signal", 110, "200 Hz, 1 µs"),
        ("servo", "servo 1 orange", f"Pico GP{SERVO_PINS[1]}", "PWM A-", "servo lead signal", 130, ""),
        ("servo", "servo 2 orange", f"Pico GP{SERVO_PINS[2]}", "PWM B+", "servo lead signal", 110, ""),
        ("servo", "servo 3 orange", f"Pico GP{SERVO_PINS[3]}", "PWM B-", "servo lead signal", 130, ""),
        ("I2C0", "BNO085 STEMMA QT", f"Pico GP{define('WYV_PIN_SDA')} SDA / GP{define('WYV_PIN_SCL')} SCL / 3V3 / GND", "SDA SCL 3V3 GND", "STEMMA QT to male header 150 mm (4209)", 150, "header pins soldered into the Pico's holes; blue = SDA, yellow = SCL"),
        ("I2C0", "BNO085 INT", f"Pico GP{define('WYV_PIN_BNO_INT')}", "INT", "28 AWG silicone", 60, "data-ready, active low"),
        ("I2C0", "BNO085 RST", f"Pico GP{define('WYV_PIN_BNO_RST')}", "RST", "28 AWG silicone", 60, ""),
        ("I2C1", "BMP388 STEMMA QT", f"Pico GP{define('WYV_PIN_SDA1')} SDA / GP{define('WYV_PIN_SCL1')} SCL / 3V3 / GND", "SDA1 SCL1 3V3 GND", "STEMMA QT to male header 150 mm (4209)", 150, "close the BMP388's ADDR jumper first (0x76)"),
        ("I2C1", "BMP388 STEMMA QT (2nd port)", "BME688 STEMMA QT", "SDA1 SCL1 3V3 GND", "STEMMA QT 100 mm (4210)", 100, "both on -Y; BME688 stays at 0x77"),
        ("SPI0", "4682 CLK / DI / DO / CS", f"Pico GP{define('WYV_PIN_SD_SCK')} / GP{define('WYV_PIN_SD_MOSI')} / GP{define('WYV_PIN_SD_MISO')} / GP{define('WYV_PIN_SD_CS')}", "SCK MOSI MISO CS", "4 x 28 AWG silicone, twisted with GND", 110, "-Y top to +X; 3 V only, no level shifter needed"),
        ("SPI0", "4682 3V / GND", "Pico 3V3 OUT / GND", "3V3 GND", "2 x 28 AWG", 110, ""),
        ("arm", "6 mm tactile switch (wall cradle, -Y)", f"Pico GP{define('WYV_PIN_BUTTON')} / GND", "BUTTON", "2 x 28 AWG silicone", 110, "internal pull-up; switch to GND"),
        ("arm", "3 mm LED anode via 220 R (wall cradle)", f"Pico GP{define('WYV_PIN_LED_EXT')}", "LED", "28 AWG silicone", 110, "resistor on the LED leg, heat-shrunk; cathode to the button's GND"),
    ]
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
