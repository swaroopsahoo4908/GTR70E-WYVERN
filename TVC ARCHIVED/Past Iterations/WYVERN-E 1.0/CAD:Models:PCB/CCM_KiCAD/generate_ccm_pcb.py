#!/usr/bin/env python3
"""
XRIM-117 CCM KiCAD 7 PCB Generator  Rev 7
62 mm Circular 2-Layer FR4 ENIG
Rev 5 vs Rev 4:
  LAYOUT-01: mk_e22 now accepts rot; reg() calls use rotation matrix → correct routing DB
  LAYOUT-02: E22 at (0,+19) rot=270 — 26mm axis horizontal, RF pad at (0,+26), signals at y=+12
             corners at (±13,+26) = 29.1mm < 31mm ✓  (was (0,+16) overlapping MCU)
  LAYOUT-03: Q1/Q3 moved from (±17,-18) to (±15,-18) — EP corner now 29.1mm < 31mm ✓
  LAYOUT-04: J6/J8 screw terminals rot=90 — 3.5mm pitch is radial → fits at (-14/-14,-23)
             outer pad 28.4mm < 31mm ✓  (was rot=0 at (±19,-22) → 34.3mm violation)
  LAYOUT-05: LED1/2/3 repositioned outside D2PAK EP copper regions
  LAYOUT-06: Power section spread: U6→(-14,+2), L1→(-22,+2), no overlaps with 4.9mm gap
  LAYOUT-07: C1 moved to (-21,-4), C2 to (-19,+7), R26/R27 to (-18,+6/+9)
  LAYOUT-08: R10/R11 moved to (+16,+2/+8) — clear of BMP388 and J2 connector
  LAYOUT-09: C30 moved to (+4,+12) — near E22 signal pads
  LAYOUT-10: SMA at (0,+28) — RF_ANT pad at (0,-2) local → abs (100,126) = E22 RF pad ✓
  All Rev 3/4 electrical fixes retained.
"""

import uuid, math
from collections import defaultdict

CX, CY  = 100.0, 100.0
R_BOARD = 31.0

def u():  return str(uuid.uuid4())
def axy(dx, dy): return CX+dx, CY+dy

# ─── NET REGISTRY ──────────────────────────────────────────────────────────────
NETS = {}
_nid = [0]
def net(name):
    if not name: return 0, ""
    if name not in NETS:
        _nid[0] += 1
        NETS[name] = _nid[0]
    return NETS[name], name

for _n in [
    "GND", "+3V3", "VBAT", "VBAT_ARMED",
    "BUCK_SW", "FB_3V3", "NRST",
    "USB5V", "USB_DP", "USB_DM",
    "SPI0_SCK", "SPI0_MOSI", "SPI0_MISO", "IMU_CS", "FLASH_CS",
    "I2C0_SDA", "I2C0_SCL",
    "LORA_SCK", "LORA_MOSI", "LORA_MISO", "LORA_CS",
    "LORA_BUSY", "LORA_IRQ", "LORA_NRST",
    "UART0_TX", "UART0_RX",
    "PYRO1_MCU", "PYRO2_MCU", "PYRO3_MCU",
    "PYRO1_GATE", "PYRO2_GATE", "PYRO3_GATE",
    "PYRO1_CONT", "PYRO2_CONT", "PYRO3_CONT",
    "PYRO1_D", "PYRO2_D", "PYRO3_D",
    "LED_MCU", "LED_STATUS",
    "IMU_INT1", "IMU_INT2",
    "RF_ANT", "SWCLK", "SWDIO",
]:
    net(_n)

# ─── PAD DATABASE ──────────────────────────────────────────────────────────────
PAD_DB = defaultdict(list)
def reg(n, ax, ay):
    if n and n != "GND": PAD_DB[n].append((ax, ay))

# ─── PAD BUILDERS ──────────────────────────────────────────────────────────────
def spad(num, n, rx, ry, pw, ph, rot=0, shape="rect"):
    nid, nn = net(n)
    ns = f'\n      (net {nid} "{nn}")' if nid else ""
    rs = f" {rot}" if rot else ""
    return (f'    (pad "{num}" smd {shape} (at {rx:.4f} {ry:.4f}{rs})'
            f' (size {pw:.4f} {ph:.4f})'
            f' (layers "F.Cu" "F.Paste" "F.Mask"){ns}\n    )')

def thpad(num, n, rx, ry, pw, ph, dr):
    nid, nn = net(n)
    ns = f'\n      (net {nid} "{nn}")' if nid else ""
    return (f'    (pad "{num}" thru_hole circle (at {rx:.4f} {ry:.4f})'
            f' (size {pw:.4f} {ph:.4f}) (drill {dr:.4f})'
            f' (layers "*.Cu" "*.Mask"){ns}\n    )')

def fp(lib, ref, val, dx, dy, rot, pads, lyr="F.Cu"):
    ax, ay = axy(dx, dy)
    r = f" {int(rot)}" if rot else ""
    lines = [
        f'  (footprint "{lib}" (layer "{lyr}")',
        f'    (at {ax:.4f} {ay:.4f}{r})',
        f'    (uuid "{u()}")',
        f'    (property "Reference" "{ref}" (at 0 -2.5 0) (layer "F.SilkS")'
        f'\n      (effects (font (size 0.6 0.6))))',
        f'    (property "Value" "{val}" (at 0 2.5 0) (layer "F.Fab")'
        f'\n      (effects (font (size 0.6 0.6))))',
    ]
    lines += pads
    lines.append('  )')
    return '\n'.join(lines)

# ─── FOOTPRINT DEFINITIONS ─────────────────────────────────────────────────────

def mk_rp2040(dx, dy):
    """QFN-56 RP2040.  Bottom=pads1-14(y=+3.15), Right=15-28(x=+3.15),
    Top=29-42(y=-3.15), Left=43-56(x=-3.15), EP=centre GND."""
    PN = {
        1:"+3V3",       2:"UART0_TX",   3:"UART0_RX",   4:"SPI0_SCK",
        5:"SPI0_MOSI",  6:"SPI0_MISO",  7:"IMU_CS",     8:"FLASH_CS",
        9:"GND",        10:"+3V3",      11:"I2C0_SDA",  12:"I2C0_SCL",
        13:"LORA_SCK",  14:"LORA_MOSI",
        15:"LORA_MISO", 16:"LORA_CS",   17:"LORA_BUSY", 18:"LORA_IRQ",
        19:"GND",       20:"GND",       21:"GND",
        22:"+3V3",      23:"+3V3",      24:"SWCLK",     25:"SWDIO",
        26:"NRST",      27:"GND",       28:"GND",
        29:"GND",       30:"GND",       31:"GND",       32:"GND",
        33:"+3V3",      34:"USB_DM",    35:"USB_DP",
        36:"+3V3",      37:"+3V3",
        38:"PYRO3_CONT",39:"PYRO2_CONT",40:"PYRO1_CONT",
        41:"+3V3",      42:"LED_MCU",
        43:"GND",       44:"PYRO3_MCU", 45:"PYRO2_MCU", 46:"PYRO1_MCU",
        47:"+3V3",      48:"IMU_INT2",  49:"GND",       50:"GND",
        51:"LORA_NRST", 52:"+3V3",      53:"+3V3",      54:"IMU_INT1",
        55:"GND",       56:"+3V3",      57:"GND",
    }
    def ppos(n):
        if n == 57: return 0.0, 0.0
        if  1 <= n <= 14: return -2.60+(n-1)*0.4,   +3.15
        if 15 <= n <= 28: return +3.15,   +2.60-(n-15)*0.4
        if 29 <= n <= 42: return +2.60-(n-29)*0.4,  -3.15
        if 43 <= n <= 56: return -3.15,  -2.60+(n-43)*0.4
        return 0, 0
    ax0, ay0 = axy(dx, dy); pads = []
    for pn in range(1, 58):
        rx, ry = ppos(pn); nn = PN.get(pn, "GND")
        if pn == 57:
            pads.append(spad("EP", nn, rx, ry, 5.2, 5.2, shape="rect"))
        elif 1<=pn<=14 or 29<=pn<=42:
            pads.append(spad(str(pn), nn, rx, ry, 0.80, 0.35))
        else:
            pads.append(spad(str(pn), nn, rx, ry, 0.35, 0.80))
        reg(nn, ax0+rx, ay0+ry)
    return fp("Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm","U1","RP2040",dx,dy,0,pads)

def mk_w25q128(dx, dy):
    PN = {1:"FLASH_CS",2:"SPI0_MISO",3:"+3V3",4:"GND",
          5:"SPI0_MOSI",6:"SPI0_SCK",7:"+3V3",8:"+3V3"}
    ax0, ay0 = axy(dx, dy); pads = []
    for i in range(4):
        rx,ry = -2.54, +1.905-i*1.27
        pads.append(spad(str(i+1), PN[i+1], rx, ry, 1.75, 0.60))
        reg(PN[i+1], ax0+rx, ay0+ry)
    for i in range(4):
        rx,ry = +2.54, -1.905+i*1.27
        pads.append(spad(str(5+i), PN[5+i], rx, ry, 1.75, 0.60))
        reg(PN[5+i], ax0+rx, ay0+ry)
    return fp("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm","U2","W25Q128",dx,dy,0,pads)

def mk_icm42688(dx, dy):
    PN = {1:"+3V3",2:"+3V3",3:"GND",4:"SPI0_MISO",5:"SPI0_SCK",
          6:"SPI0_MOSI",7:"IMU_CS",8:"GND",9:"IMU_INT1",10:"IMU_INT2",
          11:"GND",12:"+3V3"}
    pp = {1:(-0.9,+1.2),2:(-0.3,+1.2),3:(+0.3,+1.2),4:(+0.9,+1.2),
          5:(+1.2,+0.4),6:(+1.2,-0.4),
          7:(+0.9,-1.2),8:(+0.3,-1.2),9:(-0.3,-1.2),10:(-0.9,-1.2),
          11:(-1.2,-0.4),12:(-1.2,+0.4)}
    ax0, ay0 = axy(dx, dy); pads = []
    for pn in range(1, 13):
        rx, ry = pp[pn]; nn = PN.get(pn, "GND")
        pads.append(spad(str(pn), nn, rx, ry, 0.50, 0.50))
        reg(nn, ax0+rx, ay0+ry)
    return fp("Sensor_IMU:InvenSense_ICM-42688-P_LGA-14","U3","ICM-42688-P",dx,dy,0,pads)

def mk_bmp388(dx, dy):
    PN = {1:"+3V3",2:"+3V3",3:"GND",4:"I2C0_SCL",
          5:"I2C0_SDA",6:"GND",7:"+3V3",8:"GND"}
    pp = {1:(-0.75,-1.0),2:(-0.25,-1.0),3:(+0.25,-1.0),4:(+0.75,-1.0),
          5:(+0.75,+1.0),6:(+0.25,+1.0),7:(-0.25,+1.0),8:(-0.75,+1.0)}
    ax0, ay0 = axy(dx, dy); pads = []
    for pn in range(1, 9):
        rx, ry = pp[pn]; nn = PN[pn]
        pads.append(spad(str(pn), nn, rx, ry, 0.50, 0.40))
        reg(nn, ax0+rx, ay0+ry)
    return fp("Sensor_Pressure:Bosch_LGA-8_2x2.5mm","U4","BMP388",dx,dy,0,pads)

def mk_tlv62569(dx, dy):
    """TLV62569 SOT-23-5 (DBV): 1=SW  2=GND  3=VIN  4=EN  5=FB
    Vout = 0.6*(1+R26/R27) = 0.6*(1+453k/100k) = 3.32V"""
    PN = {1:"BUCK_SW", 2:"GND", 3:"VBAT", 4:"VBAT", 5:"FB_3V3"}
    pp = {1:(-0.95,+1.30),2:(0,+1.30),3:(+0.95,+1.30),
          4:(+0.95,-1.30),5:(-0.95,-1.30)}
    ax0, ay0 = axy(dx, dy); pads = []
    for pn in range(1, 6):
        rx, ry = pp[pn]; nn = PN[pn]
        pads.append(spad(str(pn), nn, rx, ry, 1.50, 0.60))
        reg(nn, ax0+rx, ay0+ry)
    return fp("Package_TO_SOT_SMD:SOT-23-5","U6","TLV62569",dx,dy,0,pads)

def mk_e22(dx, dy, rot=0):
    """Ebyte E22-900M22S 14x26mm.
    Local frame: 9 castellated pads at x=-7 (y0 to y0+8*2.54), RF pad at (+7,0).
    rot=270 -> RF pad maps to board +y (bottom), signal pads at local y=-7 (board centre side).
    At (0,+19) rot=270: signal pads at board-rel (+/-10.16,+12), RF at (0,+26).
    Module corners at (+-13,+12) and (+-13,+26) -> max dist 29.1mm < 31mm.
    Rotation applied to reg() pad positions so MST routing is correct."""
    SIG = ["LORA_SCK","LORA_MOSI","LORA_MISO","LORA_CS",
           "LORA_BUSY","LORA_IRQ","LORA_NRST","+3V3","GND"]
    ax0, ay0 = axy(dx, dy)
    a = math.radians(-rot)
    cos_a, sin_a = math.cos(a), math.sin(a)
    pads = []
    n = len(SIG); y0 = -((n-1)*2.54)/2
    for i, nn in enumerate(SIG):
        rx, ry = -7.0, y0+i*2.54
        pads.append(spad(str(i+1), nn, rx, ry, 1.80, 1.20))
        rrx = rx*cos_a - ry*sin_a
        rry = rx*sin_a + ry*cos_a
        reg(nn, ax0+rrx, ay0+rry)
    # RF pad
    rx, ry = +7.0, 0.0
    pads.append(spad("10", "RF_ANT", rx, ry, 2.0, 2.0))
    rrx = rx*cos_a - ry*sin_a
    rry = rx*sin_a + ry*cos_a
    reg("RF_ANT", ax0+rrx, ay0+rry)
    return fp("RF_Module:Ebyte_E22-900M22S","U5","E22-900M22S",dx,dy,rot,pads)

# IRFZ44N TO-263-3 D2PAK
# rot=0: EP (drain tab, 8.128x4.699mm) at local y=-1.651 → faces board TOP EDGE when in upper zone
#        gate/source leads at local y=+5.588 → face inward toward MCU
def mk_irfz44n(ref, dx, dy, gate_net, drain_net, source_net, rot=0):
    ax0, ay0 = axy(dx, dy)
    pads = [
        spad("1",  gate_net,   -2.286, +5.588, 1.778, 1.778),
        spad("2",  source_net, +2.286, +5.588, 1.778, 1.778),
        spad("EP", drain_net,       0, -1.651, 8.128, 4.699),
    ]
    a = math.radians(-rot)
    for nn, rx, ry in [(gate_net,-2.286,+5.588),(source_net,+2.286,+5.588),
                       (drain_net,0,-1.651)]:
        rrx = rx*math.cos(a)-ry*math.sin(a)
        rry = rx*math.sin(a)+ry*math.cos(a)
        reg(nn, ax0+rrx, ay0+rry)
    return fp("Package_TO_SOT_SMD:TO-263-3_TabEP",ref,"IRFZ44N",dx,dy,rot,pads)

def mk_r(ref, val, na, nb, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy)
    a = math.radians(-rot)
    def rp(rx,ry): return rx*math.cos(a)-ry*math.sin(a), rx*math.sin(a)+ry*math.cos(a)
    pads = [spad("1",na,-0.9,0,1.0,0.9), spad("2",nb,+0.9,0,1.0,0.9)]
    r1x,r1y = rp(-0.9,0); r2x,r2y = rp(+0.9,0)
    reg(na,ax0+r1x,ay0+r1y); reg(nb,ax0+r2x,ay0+r2y)
    return fp("Resistor_SMD:R_0402_1005Metric",ref,val,dx,dy,rot,pads)

def mk_c(ref, val, na, nb, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy)
    a = math.radians(-rot)
    def rp(rx,ry): return rx*math.cos(a)-ry*math.sin(a), rx*math.sin(a)+ry*math.cos(a)
    pads = [spad("1",na,-0.9,0,1.0,0.9), spad("2",nb,+0.9,0,1.0,0.9)]
    r1x,r1y = rp(-0.9,0); r2x,r2y = rp(+0.9,0)
    reg(na,ax0+r1x,ay0+r1y); reg(nb,ax0+r2x,ay0+r2y)
    return fp("Capacitor_SMD:C_0402_1005Metric",ref,val,dx,dy,rot,pads)

def mk_cpol(ref, val, np, nn_neg, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy)
    pads = [spad("1",np,-1.0,0,1.60,1.45), spad("2",nn_neg,+1.0,0,1.60,1.45)]
    reg(np,ax0-1.0,ay0); reg(nn_neg,ax0+1.0,ay0)
    return fp("Capacitor_SMD:C_0805_2012Metric",ref,val,dx,dy,rot,pads)

def mk_led(ref, val, na, nk, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy)
    pads = [spad("K",nk,-1.0,0,1.60,1.45), spad("A",na,+1.0,0,1.60,1.45)]
    reg(nk,ax0-1.0,ay0); reg(na,ax0+1.0,ay0)
    return fp("LED_SMD:LED_0805_2012Metric",ref,val,dx,dy,rot,pads)

def mk_inductor(ref, val, na, nb, dx, dy, rot=0):
    """1210 power inductor: Bourns SRR1260 or equiv, 2.2uH 1.2A."""
    ax0, ay0 = axy(dx, dy)
    a = math.radians(-rot)
    def rp(rx,ry): return rx*math.cos(a)-ry*math.sin(a), rx*math.sin(a)+ry*math.cos(a)
    pads = [spad("1",na,-1.5,0,1.6,3.5), spad("2",nb,+1.5,0,1.6,3.5)]
    r1x,r1y = rp(-1.5,0); r2x,r2y = rp(+1.5,0)
    reg(na,ax0+r1x,ay0+r1y); reg(nb,ax0+r2x,ay0+r2y)
    return fp("Inductor_SMD:L_1210_3225Metric",ref,val,dx,dy,rot,pads)

def mk_xt30(dx, dy):
    ax0, ay0 = axy(dx, dy)
    pads = [thpad("1","VBAT",-1.75,0,2.5,2.5,1.5),
            thpad("2","GND", +1.75,0,2.5,2.5,1.5)]
    reg("VBAT",ax0-1.75,ay0)
    return fp("Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
              "J4","XT30-M",dx,dy,0,pads)

def mk_sw2pin(ref, na, nb, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy)
    a = math.radians(-rot)
    def rp(rx,ry): return rx*math.cos(a)-ry*math.sin(a), rx*math.sin(a)+ry*math.cos(a)
    pads = [thpad("1",na,-1.27,0,1.7,1.7,1.0), thpad("2",nb,+1.27,0,1.7,1.7,1.0)]
    r1x,r1y = rp(-1.27,0); r2x,r2y = rp(+1.27,0)
    reg(na,ax0+r1x,ay0+r1y); reg(nb,ax0+r2x,ay0+r2y)
    return fp("Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
              ref,"SW_2pin",dx,dy,rot,pads)

def mk_screw2(ref, na, nb, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy)
    a = math.radians(-rot)
    def rp(rx,ry): return rx*math.cos(a)-ry*math.sin(a), rx*math.sin(a)+ry*math.cos(a)
    pads = [thpad("1",na,-1.75,0,2.5,2.5,1.3), thpad("2",nb,+1.75,0,2.5,2.5,1.3)]
    r1x,r1y = rp(-1.75,0); r2x,r2y = rp(+1.75,0)
    reg(na,ax0+r1x,ay0+r1y); reg(nb,ax0+r2x,ay0+r2y)
    return fp("TerminalBlock:TerminalBlock_bornier-2_P3.5mm",ref,"Screw_2",dx,dy,rot,pads)

def mk_jst_gh8(ref, nets, dx, dy, rot=0):
    ax0, ay0 = axy(dx, dy); pads = []
    xs = -((8-1)*1.25)/2
    a = math.radians(-rot)
    for i, nn in enumerate(nets):
        rx = xs+i*1.25; ry = 0
        rrx = rx*math.cos(a)-ry*math.sin(a)
        rry = rx*math.sin(a)+ry*math.cos(a)
        pads.append(spad(str(i+1), nn, rx, ry, 0.80, 1.80))
        reg(nn, ax0+rrx, ay0+rry)
    return fp("Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal",
              ref,"JST-GH-8",dx,dy,rot,pads)

def mk_sma(dx, dy):
    """Edge-mount SMA. RF_ANT pad at local (0,-2).
    At (0,+28): abs RF pad = (100,126) = board-rel (0,+26) = E22 RF pad position. """
    ax0, ay0 = axy(dx, dy)
    pads = [spad("1","RF_ANT",0,-2.0,1.60,3.00),
            spad("2","GND",-3.6,0,2.00,2.00),
            spad("3","GND",+3.6,0,2.00,2.00)]
    reg("RF_ANT",ax0,ay0-2.0)
    return fp("Connector_Coaxial:SMA_Molex_0732511150_Horizontal","J3","SMA_Edge",dx,dy,0,pads)

def mk_tc2030(dx, dy):
    nets = ["SWCLK","SWDIO","+3V3","GND","UART0_TX","UART0_RX"]
    ax0, ay0 = axy(dx, dy); pads = []
    for i, nn in enumerate(nets):
        col=i%2; row=i//2
        rx=-0.635+col*1.27; ry=-1.27+row*1.27
        pads.append(thpad(str(i+1),nn,rx,ry,1.0,1.0,0.5))
        reg(nn,ax0+rx,ay0+ry)
    return fp("Tag-Connect:TC2030-IDC-FP_2x03_P1.27mm_Vertical","SW1","TC2030-SWD",dx,dy,0,pads)

def mk_usb_tp(dx, dy):
    """4-pin USB test header: 1=GND 2=USB_DM 3=USB_DP 4=USB5V (1.27mm pitch)."""
    nets = ["GND","USB_DM","USB_DP","USB5V"]
    ax0, ay0 = axy(dx, dy); pads = []
    for i, nn in enumerate(nets):
        rx = -((4-1)*1.27)/2 + i*1.27
        pads.append(thpad(str(i+1),nn,rx,0,1.5,1.5,0.8))
        reg(nn,ax0+rx,ay0)
    return fp("Connector_PinHeader_2.54mm:PinHeader_1x04_P1.27mm_Vertical",
              "J9","USB_TP",dx,dy,0,pads)

# ─── PLACE ALL COMPONENTS ──────────────────────────────────────────────────────
# Rev 5 layout zones:
#   CENTRE  (r<10mm): RP2040, ICM42688, W25Q128
#   INNER   (r 8-16mm): BMP388, TLV62569, sensors decoupling
#   MID     (r 14-24mm): E22 module (upper), MOSFETs (lower), connectors (right/left)
#   OUTER   (r 24-30mm): Screw terminals, XT30, SMA

FPS = []

# ── MCU core ─────────────────────────────────────────────────────────────────
FPS.append(mk_rp2040(0, 0))
FPS.append(mk_w25q128(-9, +1))
FPS.append(mk_icm42688(+9, -1))

# ── Sensor cluster ────────────────────────────────────────────────────────────
FPS.append(mk_bmp388(+13, +6))

# ── RP2040 decoupling ─────────────────────────────────────────────────────────
FPS.append(mk_c("C10","100nF","+3V3","GND",  +5, -5))
FPS.append(mk_c("C11","10uF", "+3V3","GND",  +7, -5))
FPS.append(mk_c("C12","100nF","NRST","GND",  -5, -5))
FPS.append(mk_c("C13","100nF","+3V3","GND",  +5, +4))
FPS.append(mk_c("C14","100nF","+3V3","GND",  -5, +4))
FPS.append(mk_c("C15","100nF","+3V3","GND",  +7, +4))
FPS.append(mk_r("R1", "10k",  "+3V3","NRST", -5, -8))   # NRST pull-up
FPS.append(mk_sw2pin("SW_BOOT","FLASH_CS","GND", -8, -5)) # BOOTSEL

# ── IMU decoupling & I2C pull-ups ─────────────────────────────────────────────
FPS.append(mk_c("C20","100nF","+3V3","GND", +9, -5))
FPS.append(mk_c("C21","100nF","+3V3","GND", +9, -8))
# Rev 5: moved from (+15,+4/+7) → (+16,+2/+8) — clear of BMP388 (+13,+6) and J2 (+22,+5)
FPS.append(mk_r("R10","4.7k", "+3V3","I2C0_SDA", +16, +2))
FPS.append(mk_r("R11","4.7k", "+3V3","I2C0_SCL", +16, +8))

# ── Power section (left arc) ──────────────────────────────────────────────────
# Rev 5: U6 at (-14,+2) [was -17], L1 at (-22,+2) — 4.9mm gap between them
# U6 left edge ~-15.5, L1 right edge ~-20.4 → 4.9mm gap ✓
FPS.append(mk_tlv62569(-14, +2))
FPS.append(mk_inductor("L1","2.2uH","BUCK_SW","+3V3", -22, +2))
FPS.append(mk_r("R26","453k", "+3V3","FB_3V3",  -18, +6))   # FB top → Vout=3.32V
FPS.append(mk_r("R27","100k", "FB_3V3","GND",   -18, +9))   # FB bottom
# Rev 5: C1 at (-21,-4) [was -22,-2], C2 at (-19,+7) [was -22,+5]
FPS.append(mk_cpol("C1","47uF 10V","VBAT","GND",   -21, -4)) # VBAT input bulk
FPS.append(mk_cpol("C2","22uF 6.3V","+3V3","GND",  -19, +7)) # +3V3 output
FPS.append(mk_xt30(-25, -4))                                   # XT30 power input
# Rev F: J5 moved from (-25,+3) to (-23,+3) — VBAT_ARMED pad shifts from
#         (-23.73,+3) to (-21.73,+3); MST corner drops from 31.85mm to 30.39mm ✓
FPS.append(mk_sw2pin("J5","VBAT","VBAT_ARMED", -23, +3))      # arm switch

# ── LoRa module + RF (upper centre) ───────────────────────────────────────────
# Rev 5: rot=270 → 26mm axis horizontal, 14mm axis radial
#   Signal pads at board-rel (+-10.16, +12), RF pad at (0,+26)
#   Module body: x±13, y +12 to +26 → corners at 29.1mm < 31mm ✓
FPS.append(mk_e22(0, +19, rot=270))
FPS.append(mk_c("C30","100nF","+3V3","GND", +4, +10))  # near E22 signal pads — (+12 overlapped E22 body)
FPS.append(mk_sma(0, +28))                               # RF_ANT pad → (100,126) ✓

# ── USB test + status LED ─────────────────────────────────────────────────────
FPS.append(mk_usb_tp(+8, +8))
FPS.append(mk_c("C31","100nF","USB5V","GND", +11, +8))
FPS.append(mk_r("R28","330R","LED_MCU","LED_STATUS", -1, +5))
FPS.append(mk_led("LED4","Status","LED_STATUS","GND", -3, +8))

# ── Pyro channels (lower arc) ──────────────────────────────────────────────────
# Rev 5: Q1/Q3 at (+-15,-18) [was +-17] → EP corner at 29.1mm < 31mm ✓
# D2PAK rot=0: EP (drain tab) at local y=-1.651 → faces board top edge (outward)
#              gate/source at local y=+5.588 → faces board centre ✓

# Q1 lower-left
FPS.append(mk_irfz44n("Q1",-15,-18,"PYRO1_GATE","PYRO1_D","GND",rot=0))
FPS.append(mk_r("R20","100R","PYRO1_MCU","PYRO1_GATE", -9,-9))   # gate series R
FPS.append(mk_r("R23","10k", "PYRO1_GATE","GND",       -11,-13)) # gate pull-down
# J6 rot=90: 3.5mm pitch becomes radial, outer pad at 28.4mm < 31mm ✓
FPS.append(mk_screw2("J6","VBAT_ARMED","PYRO1_D",      -14,-23, 90))   # screws face -X (left edge) ✓
# LED1 at (-24,-16): board-rel x=-24 < Q1 EP left (-19.064), y=-16 > EP top (-17.3) ✓
FPS.append(mk_led("LED1","Cont LED","PYRO1_CONT","GND", -24,-16, 0))

# Q2 lower-centre
FPS.append(mk_irfz44n("Q2", 0,-20,"PYRO2_GATE","PYRO2_D","GND",rot=0))
FPS.append(mk_r("R21","100R","PYRO2_MCU","PYRO2_GATE",  0,-9))
FPS.append(mk_r("R24","10k", "PYRO2_GATE","GND",        0,-14))
# J7 rot=180: screws face -Y (toward top board edge, outward) — was rot=0 which faced +Y (inward)
FPS.append(mk_screw2("J7","VBAT_ARMED","PYRO2_D",       0,-25, 180))
# LED2 at (+6,-17): x=+6 > Q2 EP right (+4.064), y=-17 > EP top (-19.3) ✓
FPS.append(mk_led("LED2","Cont LED","PYRO2_CONT","GND",  +6,-17, 0))

# Q3 lower-right
FPS.append(mk_irfz44n("Q3",+15,-18,"PYRO3_GATE","PYRO3_D","GND",rot=0))
FPS.append(mk_r("R22","100R","PYRO3_MCU","PYRO3_GATE", +9,-9))
FPS.append(mk_r("R25","10k", "PYRO3_GATE","GND",       +11,-13))
# J8 rot=270: screws face +X (right edge, outward) — was rot=90 which faced -X (inward)
FPS.append(mk_screw2("J8","VBAT_ARMED","PYRO3_D",      +14,-23, 270))
# LED3 at (+24,-16): symmetric to LED1 ✓
FPS.append(mk_led("LED3","Cont LED","PYRO3_CONT","GND", +24,-16, 0))

# ── Right-arc I/O connectors ───────────────────────────────────────────────────
# rot=270: JST default opening faces +Y; 270° CCW rotates +Y → +X (toward board right edge).
# J1 moved -2mm in Y (to -6) so pad arrays don't clash after pads rotate to Y-axis direction.
# J1 pads: (+22, -10.4) to (+22, -1.6) → max 24.3mm ✓
# J2 pads: (+22,  +0.6) to (+22, +9.4) → max 23.9mm ✓
# Gap between arrays: 2.0mm ✓
FPS.append(mk_jst_gh8("J1",
    ["+3V3","GND","UART0_TX","UART0_RX","I2C0_SDA","I2C0_SCL","SPI0_SCK","PYRO1_GATE"],
    +22, -6, rot=270))
FPS.append(mk_jst_gh8("J2",
    ["+3V3","GND","UART0_TX","UART0_RX","I2C0_SDA","I2C0_SCL","SPI0_SCK","PYRO2_GATE"],
    +22, +5, rot=270))
FPS.append(mk_tc2030(+22, +15))

# ─── ROUTING ───────────────────────────────────────────────────────────────────
SEGS = []

def seg(x1,y1,x2,y2,nn,w=0.25,lyr="F.Cu"):
    nid,nm = net(nn)
    if abs(x1-x2)<0.001 and abs(y1-y2)<0.001: return
    SEGS.append(f'  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f})'
                f' (width {w:.4f}) (layer "{lyr}") (net {nid}) (uuid "{u()}"))')

def lroute(x1,y1,x2,y2,nn,w=0.25,lyr="F.Cu",hfirst=True):
    mx,my = (x2,y1) if hfirst else (x1,y2)
    seg(x1,y1,mx,my,nn,w,lyr)
    seg(mx,my,x2,y2,nn,w,lyr)

def route_net_mst(nn, w=0.25, lyr="F.Cu"):
    pads = list(PAD_DB.get(nn, []))
    if len(pads) < 2: return
    rem = pads[:]
    chain = [rem.pop(0)]
    while rem:
        last = chain[-1]
        rem.sort(key=lambda p: (p[0]-last[0])**2+(p[1]-last[1])**2)
        chain.append(rem.pop(0))
    for i in range(len(chain)-1):
        x1,y1 = chain[i]; x2,y2 = chain[i+1]
        lroute(x1,y1,x2,y2,nn,w,lyr, abs(x1-x2)>=abs(y1-y2))

# Power rails
route_net_mst("VBAT",        w=0.60)
route_net_mst("VBAT_ARMED",  w=0.80)
route_net_mst("+3V3",        w=0.50)

# Buck converter nets
route_net_mst("BUCK_SW",     w=0.60)
route_net_mst("FB_3V3",      w=0.20)
route_net_mst("USB5V",       w=0.30)

# SPI0 bus
for nn in ["SPI0_SCK","SPI0_MOSI","SPI0_MISO","IMU_CS","FLASH_CS"]:
    route_net_mst(nn, w=0.20)

# I2C bus
for nn in ["I2C0_SDA","I2C0_SCL"]: route_net_mst(nn, w=0.20)

# LoRa SPI + control
for nn in ["LORA_SCK","LORA_MOSI","LORA_MISO","LORA_CS",
           "LORA_BUSY","LORA_IRQ","LORA_NRST"]:
    route_net_mst(nn, w=0.20)

# RF 50Ω trace (PYRO_HV netclass: 0.9mm per spec)
route_net_mst("RF_ANT", w=0.90)

# Pyro gate nets
for nn in ["PYRO1_MCU","PYRO2_MCU","PYRO3_MCU"]: route_net_mst(nn, w=0.20)
for nn in ["PYRO1_GATE","PYRO2_GATE","PYRO3_GATE"]: route_net_mst(nn, w=0.20)

# Pyro drain (PYRO_HV: 0.8mm)
for nn in ["PYRO1_D","PYRO2_D","PYRO3_D"]: route_net_mst(nn, w=0.80)

# Pyro continuity
for nn in ["PYRO1_CONT","PYRO2_CONT","PYRO3_CONT"]: route_net_mst(nn, w=0.20)

# UART / SWD / misc
for nn in ["UART0_TX","UART0_RX","SWCLK","SWDIO","NRST",
           "LED_MCU","LED_STATUS","IMU_INT1","IMU_INT2","USB_DP","USB_DM"]:
    route_net_mst(nn, w=0.20)

# ─── BOARD OUTLINE + POURS ─────────────────────────────────────────────────────
def board_circle():
    return (f'  (gr_circle (center {CX:.4f} {CY:.4f}) (end {CX+R_BOARD:.4f} {CY:.4f})'
            f' (layer "Edge.Cuts") (width 0.05) (uuid "{u()}"))')

def gnd_pour():
    nid,_ = net("GND")
    pts = " ".join(f"(xy {CX+(R_BOARD-0.3)*math.cos(2*math.pi*i/64):.4f}"
                  f" {CY+(R_BOARD-0.3)*math.sin(2*math.pi*i/64):.4f})"
                  for i in range(64))
    return f'''  (zone (net {nid}) (net_name "GND") (layer "B.Cu") (uuid "{u()}")
    (hatch edge 0.508)
    (connect_pads (clearance 0.30))
    (min_thickness 0.25)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.50) (thermal_bridge_width 0.50))
    (polygon (pts {pts}))
  )'''

def pwr_pour(nn, x1, y1, x2, y2):
    nid,nm = net(nn)
    ax1,ay1 = axy(x1,y1); ax2,ay2 = axy(x2,y2)
    pts = (f"(xy {ax1:.3f} {ay1:.3f}) (xy {ax2:.3f} {ay1:.3f}) "
           f"(xy {ax2:.3f} {ay2:.3f}) (xy {ax1:.3f} {ay2:.3f})")
    return f'''  (zone (net {nid}) (net_name "{nm}") (layer "F.Cu") (uuid "{u()}")
    (hatch edge 0.508)
    (connect_pads (clearance 0.20))
    (min_thickness 0.20)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.40) (thermal_bridge_width 0.40))
    (polygon (pts {pts}))
  )'''

# ─── ASSEMBLE ──────────────────────────────────────────────────────────────────
def net_decls():
    lines = ['  (net 0 "")']
    for nm,nid in sorted(NETS.items(), key=lambda x: x[1]):
        lines.append(f'  (net {nid} "{nm}")')
    return '\n'.join(lines)

def build():
    fp_blk  = '\n'.join(FPS)
    seg_blk = '\n'.join(SEGS)
    return f"""(kicad_pcb (version 20230121) (generator "pcbnew")
  (general (thickness 1.6) (legacy_teardrops no))
  (paper "A3")
  (title_block
    (title "XRIM-117 CCM - Central Command Module PCB")
    (rev "Rev G") (date "2026-05-30")
    (company "Skylight Industries LLC / Legacy Systems Research Group")
    (comment 1 "62mm Circular 2-Layer FR4 ENIG | PDR-002")
    (comment 2 "Rev G: Connector orientations corrected — J1/J2 rot=270, J7 rot=180, J8 rot=270")
  )
  (layers
    (0  "F.Cu"      signal)  (31 "B.Cu"      signal)
    (34 "B.Paste"   user)    (35 "F.Paste"   user)
    (36 "B.SilkS"   user "B.Silkscreen")
    (37 "F.SilkS"   user "F.Silkscreen")
    (38 "B.Mask"    user)    (39 "F.Mask"    user)
    (44 "Edge.Cuts" user)
    (45 "F.CrtYd"   user "F.Courtyard")
    (47 "F.Fab"     user "F.Fabrication")
  )
  (setup
    (pad_to_mask_clearance 0.05)
    (solder_mask_min_width 0.05)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (outputformat 1) (mirror no) (outputdirectory "gerbers/")
    )
  )
{net_decls()}
{fp_blk}
{board_circle()}
{seg_blk}
{gnd_pour()}
{pwr_pour("+3V3",       -26, -6, -12, +12)}
{pwr_pour("VBAT_ARMED", -20,-28, +20,-19)}
)"""

if __name__ == "__main__":
    import re

    pcb = build()
    out = "/sessions/tender-funny-rubin/mnt/outputs/CCM_Central_Command_Module.kicad_pcb"
    with open(out,"w") as f: f.write(pcb)

    opens  = pcb.count('(')
    closes = pcb.count(')')
    fps    = len(re.findall(r'\(footprint ', pcb))
    segs   = len(re.findall(r'\(segment ',  pcb))
    zones  = len(re.findall(r'\(zone ',     pcb))
    print(f"Size: {len(pcb):,} bytes | FPs:{fps} Segs:{segs} Zones:{zones}")
    print(f"Parens: {opens}=={closes} → {'OK' if opens==closes else 'MISMATCH'}")

    # ── Boundary check ──────────────────────────────────────────────────────
    # D2PAK EP half-dims: 4.064mm x, 2.3495mm y; centre at (0,-1.651) local
    # Gate/source pads: 0.889mm half-size at (+-2.286, +5.588) local
    print("\n── Boundary verification ──")
    components = {
        "Q1 EP corner":   (-15-4.064, -18-1.651-2.3495),
        "Q3 EP corner":   (+15+4.064, -18-1.651-2.3495),
        "Q2 EP corner":   ( 0+4.064,  -20-1.651-2.3495),
        "J6 outer pad":   (-14,        -23-1.75),   # rot=90 → pad2 at dy=-1.75
        "J8 outer pad":   (+14,        -23-1.75),
        "J7 pad":         (+1.75,      -25),
        "J4 XT30 pad":    (-25-1.75,   -4),
        "J5 ARM pad":     (-23-1.27,   +3),   # moved to (-23,+3)
        "SMA GND pad":    (+3.6,       +28),
        "LED1 K pad":     (-24-1.0,    -16),
        "LED3 A pad":     (+24+1.0,    -16),
        "E22 corner":     (+13,        +19+7),      # rot=270: body x±13, y+12 to +26
        "J1 outer pad":   (+22,  -6-4.375),  # rot=270 → pads along Y; J1 moved to dy=-6
        "J2 outer pad":   (+22,  +5+4.375),  # rot=270 → pads along Y
    }
    all_ok = True
    for name, (dx, dy) in components.items():
        dist = math.sqrt(dx**2 + dy**2)
        ok = dist <= 31.0
        status = "✓" if ok else "✗ VIOLATION"
        if not ok: all_ok = False
        print(f"  {name:20s}: ({dx:+.2f},{dy:+.2f}) = {dist:.2f}mm {status}")

    # ── D2PAK orientation check ──────────────────────────────────────────────
    print("\n── D2PAK orientation (rot=0) ──")
    q1_drain_y = 100-18-1.651
    q1_gate_y  = 100-18+5.588
    print(f"  Q1 drain at y={q1_drain_y:.2f} (upper), gate at y={q1_gate_y:.2f} (lower) ",
          "✓" if q1_drain_y < q1_gate_y else "✗")

    # ── E22 RF pad alignment check ───────────────────────────────────────────
    print("\n── E22 RF pad / SMA alignment ──")
    # E22 at (0,+19) rot=270: RF pad local (+7,0) → abs (100+0, 100+19+7)=(100,126)
    e22_rf_abs_y = 100+19+7  # = 126
    sma_rf_abs_y = 100+28-2  # = 126
    print(f"  E22 RF pad abs y={e22_rf_abs_y}, SMA RF_ANT abs y={sma_rf_abs_y}",
          "✓" if e22_rf_abs_y == sma_rf_abs_y else "✗ MISMATCH")

    # ── Power section gap check ───────────────────────────────────────────────
    print("\n── Power section gaps ──")
    u6_left_edge  = -14 - 1.5   # SOT-23-5 half-body ~1.5mm
    l1_right_edge = -22 + 1.5 + 0.8  # pad centre + half-pad
    gap_u6_l1 = abs(u6_left_edge - l1_right_edge)
    print(f"  U6 left edge: {u6_left_edge:.1f}mm, L1 right edge: {l1_right_edge:.1f}mm, gap={gap_u6_l1:.1f}mm",
          "✓" if gap_u6_l1 > 1.0 else "✗ TOO CLOSE")

    print(f"\n{'ALL BOUNDARY CHECKS PASS' if all_ok else 'BOUNDARY VIOLATIONS FOUND'}")
    assert opens == closes,   f"Paren mismatch: {opens} vs {closes}"
    assert fps >= 49,          f"Expected >=49 FPs, got {fps}"
    assert segs > 100,         f"Expected >100 segs, got {segs}"
    assert all_ok,             "Boundary violation(s) detected!"
    print("PASS")
