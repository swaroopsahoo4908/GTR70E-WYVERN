#!/usr/bin/env python3
"""Footprints (datasheet-verified land patterns) for XRIM-117 avionics boards.
All local coords mm, y-down, pin-1 marked. Generated as embedded 'XRIM:*' footprints."""
from kicadgen import Pad, FP

def _silk_dot(x, y):
    return f'(fp_circle (center {x:.2f} {y:.2f}) (end {x+0.15:.2f} {y:.2f}) (stroke (width 0.3) (type default)) (fill solid) (layer "F.SilkS") (uuid "TSTAMP"))'

def _silk_box(x1,y1,x2,y2,w=0.15):
    return f'(fp_rect (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width {w}) (type default)) (fill none) (layer "F.SilkS") (uuid "TSTAMP"))'

# ── QFN-56 1EP 7x7 P0.4 (RP2040) — pads CCW from top of left side; EP=57 ──
def qfn56():
    pads=[]
    # 14 per side, pitch 0.4. Left side: pins 1-14 top→bottom at x=-3.65
    for i in range(14):
        y=-2.6+0.4*i
        pads.append(Pad(i+1, -3.65, y, 1.0, 0.22))
    # Bottom: 15-28 left→right
    for i in range(14):
        x=-2.6+0.4*i
        pads.append(Pad(15+i, x, 3.65, 0.22, 1.0))
    # Right: 29-42 bottom→top
    for i in range(14):
        y=2.6-0.4*i
        pads.append(Pad(29+i, 3.65, y, 1.0, 0.22))
    # Top: 43-56 right→left
    for i in range(14):
        x=2.6-0.4*i
        pads.append(Pad(43+i, x, -3.65, 0.22, 1.0))
    pads.append(Pad(57, 0, 0, 3.2, 3.2, shape="rect"))
    silk=[_silk_dot(-4.6,-4.6), _silk_box(-3.6,-3.6,3.6,3.6,0.12)]
    return FP("QFN-56-1EP_7x7mm_P0.4mm", pads, (-4.5,-4.5,4.5,4.5), silk)

# ── UFQFPN-48 7x7 P0.5 (STM32F411CEU6) EP=49 ──
def ufqfpn48():
    pads=[]
    for i in range(12):
        pads.append(Pad(i+1, -3.65, -2.75+0.5*i, 1.0, 0.28))
    for i in range(12):
        pads.append(Pad(13+i, -2.75+0.5*i, 3.65, 0.28, 1.0))
    for i in range(12):
        pads.append(Pad(25+i, 3.65, 2.75-0.5*i, 1.0, 0.28))
    for i in range(12):
        pads.append(Pad(37+i, 2.75-0.5*i, -3.65, 0.28, 1.0))
    pads.append(Pad(49, 0, 0, 5.6, 5.6, shape="rect"))
    silk=[_silk_dot(-4.6,-4.6), _silk_box(-3.6,-3.6,3.6,3.6,0.12)]
    return FP("UFQFPN-48_7x7mm_P0.5mm", pads, (-4.5,-4.5,4.5,4.5), silk)

# ── LGA-14 ICM-42688-P (2.5W x 3.0L, P0.5). Pin1 top-left, CCW.
#    Left col (1-4 top→bottom), bottom row (5-7 L→R), right col (8-11 bottom→top), top row (12-14 R→L)
def lga14_icm():
    pads=[]
    for i in range(4):  pads.append(Pad(i+1, -1.10, -0.75+0.5*i, 0.50, 0.30))
    for i in range(3):  pads.append(Pad(5+i, -0.5+0.5*i, 1.35, 0.30, 0.50))
    for i in range(4):  pads.append(Pad(8+i, 1.10, 0.75-0.5*i, 0.50, 0.30))
    for i in range(3):  pads.append(Pad(12+i, 0.5-0.5*i, -1.35, 0.30, 0.50))
    silk=[_silk_dot(-1.8,-1.9), _silk_box(-1.25,-1.5,1.25,1.5,0.12)]
    return FP("ICM-42688-P_LGA-14_2.5x3mm", pads, (-1.8,-2.0,1.8,2.0), silk)

# ── LGA-10 BMP388 (2x2, P0.4). Pin1 top-left; left col 1-5 top→bottom, right col 6-10 bottom→top.
def lga10_bmp388():
    pads=[]
    for i in range(5):  pads.append(Pad(i+1, -0.80, -0.8+0.4*i, 0.55, 0.25))
    for i in range(5):  pads.append(Pad(6+i, 0.80, 0.8-0.4*i, 0.55, 0.25))
    silk=[_silk_dot(-1.5,-1.4), _silk_box(-1.0,-1.0,1.0,1.0,0.12)]
    return FP("BMP388_LGA-10_2x2mm", pads, (-1.6,-1.4,1.6,1.4), silk)

# ── SOIC-8 3.9x4.9 P1.27 (W25Q128JVSIQ). Pin1 top-left, CCW. ──
def soic8():
    pads=[]
    for i in range(4):  pads.append(Pad(i+1, -2.70, -1.905+1.27*i, 1.6, 0.65))
    for i in range(4):  pads.append(Pad(5+i, 2.70, 1.905-1.27*i, 1.6, 0.65))
    silk=[_silk_dot(-3.9,-2.4), _silk_box(-1.95,-2.45,1.95,2.45,0.12)]
    return FP("SOIC-8_3.9x4.9mm_P1.27mm", pads, (-3.8,-2.7,3.8,2.7), silk)

# ── SOT-23-5 (TLV62569: EN=1 GND=2 SW=3 FB=4 VIN=5). 1,2,3 bottom L→R; 4 top-R, 5 top-L. ──
def sot23_5():
    pads=[Pad(1,-0.95,1.30,0.60,1.10), Pad(2,0,1.30,0.60,1.10), Pad(3,0.95,1.30,0.60,1.10),
          Pad(4,0.95,-1.30,0.60,1.10), Pad(5,-0.95,-1.30,0.60,1.10)]
    silk=[_silk_dot(-1.8,1.4), _silk_box(-1.5,-0.85,1.5,0.85,0.12)]
    return FP("SOT-23-5", pads, (-1.6,-2.0,1.6,2.0), silk)

# ── SOT-23-6 (TPS54202: GND=1 SW=2 VIN=3 FB=4 EN=5 BOOT=6). 1,2,3 bottom L→R; 4 top-R,5 top-M,6 top-L ──
def sot23_6():
    pads=[Pad(1,-0.95,1.30,0.60,1.10), Pad(2,0,1.30,0.60,1.10), Pad(3,0.95,1.30,0.60,1.10),
          Pad(4,0.95,-1.30,0.60,1.10), Pad(5,0,-1.30,0.60,1.10), Pad(6,-0.95,-1.30,0.60,1.10)]
    silk=[_silk_dot(-1.8,1.4), _silk_box(-1.5,-0.85,1.5,0.85,0.12)]
    return FP("SOT-23-6", pads, (-1.6,-2.0,1.6,2.0), silk)

# ── SOT-23-8 (INA219B: 1..4 bottom L→R, 5..8 top R→L) P0.65 ──
def sot23_8():
    pads=[]
    for i in range(4): pads.append(Pad(i+1, -0.975+0.65*i, 1.30, 0.40, 1.10))
    for i in range(4): pads.append(Pad(5+i, 0.975-0.65*i, -1.30, 0.40, 1.10))
    silk=[_silk_dot(-1.8,1.4), _silk_box(-1.5,-0.85,1.5,0.85,0.12)]
    return FP("SOT-23-8", pads, (-1.6,-2.0,1.6,2.0), silk)

# ── SOT-23 N-FET (AO3400A: 1=G bottom-L, 2=S bottom-R, 3=D top-center) ──
def sot23():
    pads=[Pad(1,-0.95,1.10,0.60,1.05), Pad(2,0.95,1.10,0.60,1.05), Pad(3,0,-1.10,0.60,1.05)]
    silk=[_silk_box(-1.5,-0.7,1.5,0.7,0.12)]
    return FP("SOT-23", pads, (-1.6,-1.8,1.6,1.8), silk)

# ── E22-900M22S — exact stamp-hole pattern (verified): cols x=0/13.97 → recentered ±6.985 ──
def e22_900m22s():
    pads=[]; xL=-6.985; xR=6.985; y0=-8.509  # recenter: original y 0..17.018 → -8.509..+8.509
    leftY = [0,1.27,2.54, 8.128,9.398,10.668,11.938,13.208,14.478,15.748,17.018]
    for i,y in enumerate(leftY):
        pads.append(Pad(i+1, xL, y0+y, 1.6764, 0.8128))
    for i,y in enumerate(reversed(leftY)):
        pads.append(Pad(12+i, xR, y0+y, 1.6764, 0.8128))
    silk=[_silk_dot(-8.3,-8.5), _silk_box(-7.0,-10.0,7.0,10.0,0.15)]
    return FP("Ebyte_E22-900M22S", pads, (-8.2,-10.3,8.2,10.3), silk)

# ── chips ──
def c0603(name="C_0603"):
    pads=[Pad(1,-0.7875,0,0.875,0.95), Pad(2,0.7875,0,0.875,0.95)]
    return FP(name, pads, (-1.48,-0.73,1.48,0.73), [])
def r0603(): return c0603("R_0603")
def led0603():
    pads=[Pad(1,-0.7875,0,0.875,0.95), Pad(2,0.7875,0,0.875,0.95)]
    silk=[f'(fp_line (start -1.6 -0.6) (end -1.6 0.6) (stroke (width 0.18) (type default)) (layer "F.SilkS") (uuid "TSTAMP"))']
    return FP("LED_0603", pads, (-1.48,-0.73,1.48,0.73), silk)  # pin1 = cathode
def l_4x4(): # power inductor 4x4mm (NR4018/4030)
    pads=[Pad(1,-1.7,0,1.4,3.6), Pad(2,1.7,0,1.4,3.6)]
    return FP("L_4x4mm", pads, (-2.3,-2.2,2.3,2.2), [_silk_box(-2.1,-2.05,2.1,2.05,0.12)])
def r2512():
    pads=[Pad(1,-2.9,0,1.6,3.6), Pad(2,2.9,0,1.6,3.6)]
    return FP("R_2512_Shunt", pads, (-3.9,-2.0,3.9,2.0), [])
def cp_radial_d63(): # radial electrolytic D6.3 P2.5
    pads=[Pad(1,-1.25,0,1.8,1.8,shape="rect",kind="thru_hole",drill=0.9),
          Pad(2, 1.25,0,1.8,1.8,shape="circle",kind="thru_hole",drill=0.9)]
    silk=[f'(fp_circle (center 0 0) (end 3.25 0) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS") (uuid "TSTAMP"))',
          f'(fp_text user "+" (at -2.4 -2.4) (layer "F.SilkS") (uuid "TSTAMP") (effects (font (size 0.8 0.8) (thickness 0.15))))']
    return FP("CP_Radial_D6.3mm_P2.50mm", pads, (-3.4,-3.4,3.4,3.4), silk, attr="through_hole")
def xtal3225():
    # 1 BL(XIN side), 2 BR(GND), 3 TR(XOUT side), 4 TL(GND)
    pads=[Pad(1,-1.1,0.8,1.3,1.0), Pad(2,1.1,0.8,1.3,1.0), Pad(3,1.1,-0.8,1.3,1.0), Pad(4,-1.1,-0.8,1.3,1.0)]
    return FP("Crystal_3225_4Pin", pads, (-2.1,-1.65,2.1,1.65), [_silk_dot(-2.2,1.5)])

# ── connectors ──
def xt30():
    pads=[Pad(1,-2.5,0,3.0,3.0,shape="rect",kind="thru_hole",drill=1.8),
          Pad(2, 2.5,0,3.0,3.0,shape="circle",kind="thru_hole",drill=1.8)]
    silk=[_silk_box(-5.0,-2.6,5.0,2.6),
          f'(fp_text user "+" (at -4.2 -3.4) (layer "F.SilkS") (uuid "TSTAMP") (effects (font (size 1.0 1.0) (thickness 0.2))))']
    return FP("XT30_Male_Vertical", pads, (-5.2,-2.8,5.2,2.8), silk, attr="through_hole")
def screw2_508():
    pads=[Pad(1,-2.54,0,2.6,2.6,shape="rect",kind="thru_hole",drill=1.3),
          Pad(2, 2.54,0,2.6,2.6,shape="circle",kind="thru_hole",drill=1.3)]
    return FP("TerminalBlock_2P_5.08mm", pads, (-5.1,-4.1,5.1,4.1),
              [_silk_box(-5.0,-4.0,5.0,4.0)], attr="through_hole")
def header(n, name=None, pitch=2.54):
    pads=[]
    x0=-(n-1)*pitch/2
    for i in range(n):
        shape = "rect" if i==0 else "circle"
        pads.append(Pad(i+1, x0+pitch*i, 0, 1.7, 1.7, shape=shape, kind="thru_hole", drill=1.0))
    return FP(name or f"PinHeader_1x{n:02d}_P2.54mm", pads,
              (x0-1.3,-1.3,-x0+1.3,1.3), [_silk_box(x0-1.27,-1.27,-x0+1.27,1.27)], attr="through_hole")
def jst_gh8():
    pads=[]
    for i in range(8):
        pads.append(Pad(i+1, -4.375+1.25*i, -2.0, 0.6, 1.8))
    pads.append(Pad("MP1", -5.85, 1.5, 1.2, 2.0))
    pads.append(Pad("MP2",  5.85, 1.5, 1.2, 2.0))
    silk=[_silk_dot(-5.2,-3.3), _silk_box(-6.0,-1.6,6.0,2.8,0.12)]
    return FP("JST_GH_SM08B-GHS-TB", pads, (-6.8,-3.2,6.8,3.0), silk)
def jst_sh4():
    pads=[]
    for i in range(4):
        pads.append(Pad(i+1, -1.5+1.0*i, -2.2, 0.6, 1.55))
    pads.append(Pad("MP1", -2.8, 1.2, 1.2, 1.8))
    pads.append(Pad("MP2",  2.8, 1.2, 1.2, 1.8))
    silk=[_silk_dot(-2.3,-3.2)]
    return FP("JST_SH_SM04B-SRSS-TB", pads, (-3.6,-3.0,3.6,2.4), silk)
def sma_edge():
    pads=[Pad(1,0,0,1.5,3.6,layers='(layers "F.Cu" "F.Mask")'),
          Pad(2,-2.55,0,2.0,3.6,layers='(layers "F.Cu" "F.Mask")'),
          Pad(3, 2.55,0,2.0,3.6,layers='(layers "F.Cu" "F.Mask")'),
          Pad(4,-2.55,0,2.0,3.6,layers='(layers "B.Cu" "B.Mask")'),
          Pad(5, 2.55,0,2.0,3.6,layers='(layers "B.Cu" "B.Mask")')]
    return FP("SMA_EdgeMount", pads, (-3.8,-2.0,3.8,2.0), [])
def tact2():
    pads=[Pad(1,-2.95,0,1.6,1.4), Pad(2,2.95,0,1.6,1.4)]
    return FP("SW_SPST_Tact_6x3.5", pads, (-3.9,-1.9,3.9,1.9), [_silk_box(-3.0,-1.75,3.0,1.75)])
def pc817_dip4():
    # DIP-4: pin1 BL? Standard DIP: 1 top-left... we use: 1=(-3.81,+1.27) A, 2=(-1.27,+1.27)?? No:
    # DIP-4 rows 7.62 apart, pins 1,2 on left side (1 top), 4,3 on right (4 top).
    pads=[Pad(1,-3.81,-1.27,1.6,1.6,shape="rect",kind="thru_hole",drill=0.8),
          Pad(2,-3.81, 1.27,1.6,1.6,shape="circle",kind="thru_hole",drill=0.8),
          Pad(3, 3.81, 1.27,1.6,1.6,shape="circle",kind="thru_hole",drill=0.8),
          Pad(4, 3.81,-1.27,1.6,1.6,shape="circle",kind="thru_hole",drill=0.8)]
    silk=[_silk_dot(-4.9,-1.3), _silk_box(-2.4,-2.4,2.4,2.4,0.12)]
    return FP("PC817_DIP-4", pads, (-4.9,-2.6,4.9,2.6), silk, attr="through_hole")
def mount_m3():
    pads=[Pad(1,0,0,6.0,6.0,shape="circle",kind="np_thru_hole",drill=3.2,
              layers='(layers "*.Cu" "*.Mask")')]
    return FP("MountingHole_M3", pads, (-3.3,-3.3,3.3,3.3), [], attr="through_hole")
