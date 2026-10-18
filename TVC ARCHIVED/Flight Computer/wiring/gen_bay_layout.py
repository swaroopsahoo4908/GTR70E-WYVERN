# -*- coding: utf-8 -*-
"""GTR70E WYVERN, physical bay layout + cable routing across the separation joint."""
import os
SC=2.05; PADX=120; PADY=210
NOSE,UP,BH,LOW=120.0,198.4,4.0,350.0
TOT=NOSE+UP+BH+LOW
OD=70.0; ID=66.8
W=int(TOT*SC)+PADX*2; H=int(OD*SC)+PADY+470
def x(mm): return PADX+mm*SC
def y(mm): return PADY+ (OD/2 + mm)*SC          # mm measured from tube centreline
s=[];a=s.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#12161c"/>')
a(f'<text x="{W/2}" y="46" fill="#eaf3ee" font-size="27" text-anchor="middle" font-weight="bold">GTR70E WYVERN, bay layout and separation-joint cabling</text>')
a(f'<text x="{W/2}" y="76" fill="#9fb4c4" font-size="18" text-anchor="middle">70 mm OD, 672 mm overall. Section view, nose left. Dupont male-female leads part at the bulkhead; only the aramid cord stays attached.</text>')
GND="#9aa4ad";V5="#e2483d";V33="#e8a13a";SIG="#57c98a";BLU="#4d9be6";PUR="#c07be0";YEL="#f2e14c"
# ---- airframe shell
a(f'<path d="M {x(0)} {y(0)} Q {x(NOSE*0.42)} {y(-OD/2)} {x(NOSE)} {y(-OD/2)} L {x(TOT)} {y(-OD/2)} L {x(TOT)} {y(OD/2)} L {x(NOSE)} {y(OD/2)} Q {x(NOSE*0.42)} {y(OD/2)} {x(0)} {y(0)} Z" fill="#1b3f2a" stroke="#3f8f5f" stroke-width="3"/>')
a(f'<line x1="{x(0)}" y1="{y(0)}" x2="{x(TOT)}" y2="{y(0)}" stroke="#4a5560" stroke-width="1.6" stroke-dasharray="12,8"/>')
def zone(z0,z1,fill,stroke,label,sub="",ty=0):
    a(f'<rect x="{x(z0)}" y="{y(-ID/2)}" width="{(z1-z0)*SC}" height="{ID*SC}" fill="{fill}" fill-opacity="0.55" stroke="{stroke}" stroke-width="2"/>')
    a(f'<text x="{x((z0+z1)/2)}" y="{y(0)-8+ty}" fill="#eaf3ee" font-size="16" text-anchor="middle" font-weight="bold">{label}</text>')
    if sub: a(f'<text x="{x((z0+z1)/2)}" y="{y(0)+14+ty}" fill="#c3ced8" font-size="13.5" text-anchor="middle">{sub}</text>')
# ---- upper section contents
zone(NOSE, NOSE+20, "#2a3340","#7f8b98","wadding","")
zone(NOSE+20, NOSE+72, "#3a2b18","#caa96a","i3 4K cam","36 g")
zone(NOSE+76, NOSE+150, "#14304a","#4d9be6","PERFBOARD CARD","Pico 2 W + 3 breakouts, on-edge")
a(f'<text x="{x(NOSE+113)}" y="{y(-ID/2)-34}" fill="#8fb8d8" font-size="13" text-anchor="middle">70 mm long, 50 mm wide, mounted as an axial card</text>')
# LiPo + UBEC stacked on the back face of the card
a(f'<rect x="{x(NOSE+80)}" y="{y(8)}" width="{58*SC}" height="{22*SC}" fill="#3d1f1c" fill-opacity="0.9" stroke="{V5}" stroke-width="2"/>')
a(f'<text x="{x(NOSE+109)}" y="{y(21)}" fill="#f3cdc8" font-size="13" text-anchor="middle">2S LiPo 450 mAh</text>')
a(f'<rect x="{x(NOSE+80)}" y="{y(-30)}" width="{34*SC}" height="{18*SC}" fill="#1f3a2a" fill-opacity="0.9" stroke="{SIG}" stroke-width="2"/>')
a(f'<text x="{x(NOSE+97)}" y="{y(-19)}" fill="#cfeedd" font-size="12" text-anchor="middle">UBEC</text>')
a(f'<rect x="{x(NOSE+120)}" y="{y(-30)}" width="{26*SC}" height="{18*SC}" fill="#14304a" fill-opacity="0.9" stroke="{BLU}" stroke-width="2"/>')
a(f'<text x="{x(NOSE+133)}" y="{y(-19)}" fill="#cfe2f5" font-size="12" text-anchor="middle">ARM SW</text>')
a(f'<text x="{x(NOSE+150)}" y="{y(-46)}" fill="#8fb8d8" font-size="11.5" text-anchor="middle">reached via nose cone</text>')
# ---- bulkhead / separation plane
BZ=NOSE+UP
a(f'<rect x="{x(BZ)}" y="{y(-OD/2)}" width="{BH*SC}" height="{OD*SC}" fill="#5a3b6b" stroke="#c07be0" stroke-width="3"/>')
a(f'<line x1="{x(BZ+BH/2)}" y1="{y(-OD/2)-70}" x2="{x(BZ+BH/2)}" y2="{y(OD/2)+52}" stroke="#e05a5a" stroke-width="2.6" stroke-dasharray="10,7"/>')
a(f'<text x="{x(BZ+BH/2)}" y="{y(-OD/2)-78}" fill="#e05a5a" font-size="17" text-anchor="middle" font-weight="bold">SEPARATION PLANE  t = 7.45 s</text>')
# ---- lower section contents
zone(BZ+BH, BZ+BH+108, "#2a3340","#7f8b98","chute 24 in + Nomex","aramid shock cord")
zone(BZ+BH+112, BZ+BH+205, "#3d2a1c","#caa96a","TVC BAY","gimbal + 2x ES08MA II + BNO085 0x4A")
zone(BZ+BH+209, LOW+BZ+BH-BH, "#2a2f38","#9aa4ad","F15-4","29 x 114 mm")
# ---- crossing cables (drawn as a bundle through the bulkhead)
cy=y(-24)
a(f'<path d="M {x(NOSE+150)} {cy} L {x(BZ-16)} {cy} L {x(BZ-8)} {cy}" fill="none" stroke="{SIG}" stroke-width="5"/>')
a(f'<path d="M {x(BZ+BH+10)} {cy} L {x(BZ+BH+150)} {cy} L {x(BZ+BH+150)} {y(-8)}" fill="none" stroke="{SIG}" stroke-width="5"/>')
# connector halves
a(f'<rect x="{x(BZ-16)}" y="{cy-13}" width="{9*SC}" height="26" rx="3" fill="#3a3f4a" stroke="#e8eef4" stroke-width="2"/>')
a(f'<rect x="{x(BZ+BH+2)}" y="{cy-13}" width="{9*SC}" height="26" rx="3" fill="#3a3f4a" stroke="#e8eef4" stroke-width="2"/>')
a(f'<text x="{x(BZ+BH/2)}" y="{cy-24}" fill="#e8eef4" font-size="14" text-anchor="middle">dupont M-F, 7 leads</text>')
# shock cord
a(f'<path d="M {x(NOSE+160)} {y(26)} C {x(BZ)} {y(30)}, {x(BZ+60)} {y(22)}, {x(BZ+BH+96)} {y(26)}" fill="none" stroke="{V33}" stroke-width="4.5" stroke-dasharray="3,7"/>')
a(f'<text x="{x(BZ+20)}" y="{y(38)}" fill="{V33}" font-size="14" text-anchor="middle">aramid shock cord, the ONLY retained link</text>')
# ---- dimension line
dy=y(OD/2)+34
a(f'<line x1="{x(0)}" y1="{dy}" x2="{x(TOT)}" y2="{dy}" stroke="#8fa0ad" stroke-width="1.6"/>')
for z,l in [(0,"0"),(NOSE,"120"),(BZ,"318.4"),(TOT,"672.4")]:
    a(f'<line x1="{x(z)}" y1="{dy-7}" x2="{x(z)}" y2="{dy+7}" stroke="#8fa0ad" stroke-width="1.6"/>')
    a(f'<text x="{x(z)}" y="{dy+24}" fill="#8fa0ad" font-size="13" text-anchor="middle">{l}</text>')
a(f'<text x="{x(TOT/2)}" y="{dy+46}" fill="#8fa0ad" font-size="13" text-anchor="middle">station from nose tip, mm</text>')
# ---- crossing-lead table
ty0=dy+92
a(f'<rect x="{PADX-20}" y="{ty0-30}" width="{W-2*PADX+40}" height="330" rx="12" fill="#161b22" stroke="#39424d" stroke-width="2"/>')
a(f'<text x="{PADX}" y="{ty0}" fill="#eaf3ee" font-size="21" font-weight="bold">The seven leads that cross the joint, and what happens at separation</text>')
hdr=["lead","from (perfboard)","to (TVC bay)","colour","at separation"]
colx=[PADX, PADX+190, PADX+430, PADX+700, PADX+860]
for i,hh in enumerate(hdr):
    a(f'<text x="{colx[i]}" y="{ty0+34}" fill="#9fb4c4" font-size="15" font-weight="bold">{hh}</text>')
rows=[("SERVO1 sig","C5","servo 1 orange",SIG,"open, TVC already done at 3.45 s"),
      ("SERVO2 sig","C8","servo 2 orange",SIG,"open, TVC already done"),
      ("+5 V","B bus","servo 1+2 red",V5,"servos unpowered, harmless"),
      ("GND","A bus","servo 1+2 brown",GND,"return opens with the rest"),
      ("SDA","R bus","gimbal BNO085 blue",BLU,"0x4A drops off the bus"),
      ("SCL","S bus","gimbal BNO085 yellow",YEL,"0x4A drops off the bus"),
      ("3V3","T bus","gimbal BNO085 red",V33,"gimbal IMU unpowered")]
for i,(a1,a2,a3,c,a5) in enumerate(rows):
    yy=ty0+64+i*32
    a(f'<circle cx="{PADX-8}" cy="{yy-5}" r="5.5" fill="{c}"/>')
    a(f'<text x="{colx[0]}" y="{yy}" fill="#dbe6f0" font-size="14.5">{a1}</text>')
    a(f'<text x="{colx[1]}" y="{yy}" fill="#dbe6f0" font-size="14.5">{a2}</text>')
    a(f'<text x="{colx[2]}" y="{yy}" fill="#dbe6f0" font-size="14.5">{a3}</text>')
    a(f'<rect x="{colx[3]}" y="{yy-12}" width="26" height="14" rx="3" fill="{c}"/>')
    a(f'<text x="{colx[4]}" y="{yy}" fill="#c3ced8" font-size="14">{a5}</text>')
a(f'<text x="{PADX}" y="{ty0+300}" fill="#9fb4c4" font-size="14.5">Leave a 25-30 mm service loop each side so the tubes are already moving before the pins take load. Firmware treats 0x4A going quiet after DEPLOY_T as expected, not a fault.</text>')
a('</svg>')
_here=os.path.dirname(os.path.abspath(__file__))
open(os.path.join(_here,"wyvern_bay_layout.svg"),"w").write("\n".join(s))
print("ok",W,H)
