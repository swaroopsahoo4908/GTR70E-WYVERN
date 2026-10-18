# -*- coding: utf-8 -*-
"""GTR70E WYVERN, perfboard wiring diagram generator (20x24, 2.54 mm pitch)."""
P=42; MX=110; MY=96; COLS=20; ROWS=24
W=MX*2+(COLS-1)*P+330; H=MY*2+(ROWS-1)*P+560
def X(c): return MX+(c-1)*P
def Y(r): return MY+(r-1)*P
s=[]
a=s.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#12161c"/>')
# board
a(f'<rect x="{MX-58}" y="{MY-58}" width="{(COLS-1)*P+116}" height="{(ROWS-1)*P+116}" rx="14" fill="#1d6b3a" stroke="#2fa05a" stroke-width="3"/>')
a(f'<text x="{W/2}" y="{MY-70}" fill="#cfe8d8" font-size="26" text-anchor="middle">GTR70E WYVERN, Pico 2 W perfboard, 20 x 24, 2.54 mm pitch (50 x 70 mm)</text>')
# holes + labels
L="ABCDEFGHIJKLMNOPQRST"
for c in range(1,COLS+1):
    a(f'<text x="{X(c)}" y="{MY-24}" fill="#8fb8a0" font-size="19" text-anchor="middle">{L[c-1]}</text>')
for r in range(1,ROWS+1):
    a(f'<text x="{MX-78}" y="{Y(r)+7}" fill="#8fb8a0" font-size="19" text-anchor="middle">{r}</text>')
for c in range(1,COLS+1):
    for r in range(1,ROWS+1):
        a(f'<circle cx="{X(c)}" cy="{Y(r)}" r="6.5" fill="#0d1116" stroke="#caa96a" stroke-width="2.2"/>')
def bus(col,r0,r1,color,label,dx=0):
    a(f'<line x1="{X(col)}" y1="{Y(r0)}" x2="{X(col)}" y2="{Y(r1)}" stroke="{color}" stroke-width="9" stroke-linecap="round" opacity="0.95"/>')
    a(f'<text x="{X(col)+dx}" y="{Y(r1)+34}" fill="{color}" font-size="17" text-anchor="middle" font-weight="bold">{label}</text>')
def wire(c1,r1,c2,r2,color,w=4.2,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ''
    a(f'<path d="M {X(c1)} {Y(r1)} L {X(c1)} {Y(r2)} L {X(c2)} {Y(r2)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"{d}/>')
def direct(c1,r1,c2,r2,color,w=4.2):
    a(f'<line x1="{X(c1)}" y1="{Y(r1)}" x2="{X(c2)}" y2="{Y(r2)}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')
def part(c1,r1,c2,r2,fill,stroke,label,fs=17,ty=0):
    x1,y1,x2,y2=X(c1)-20,Y(r1)-20,X(c2)+20,Y(r2)+20
    a(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" rx="9" fill="{fill}" fill-opacity="0.82" stroke="{stroke}" stroke-width="2.6"/>')
    a(f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2+ty}" fill="#eaf3ee" font-size="{fs}" text-anchor="middle" font-weight="bold">{label}</text>')
GND="#9aa4ad"; V5="#e2483d"; V33="#e8a13a"; SDA="#4d9be6"; SCL="#f2e14c"; SIG="#57c98a"; ADC="#c07be0"
# ---- buses
bus(1,1,24,GND,"GND"); bus(2,1,24,V5,"+5V")
bus(17,2,20,GND,"GND"); bus(18,2,20,SDA,"SDA"); bus(19,2,20,SCL,"SCL"); bus(20,2,20,V33,"3V3")
# ---- Pico 2 W (pins col E rows2-21 = pins1-20 ; col L rows2-21 = pins40-21)
part(5,2,12,21,"#1c3a5e","#4d9be6","",17)
a(f'<text x="{(X(5)+X(12))/2}" y="{Y(9)}" fill="#cfe2f5" font-size="30" text-anchor="middle" font-weight="bold">Pico 2 W</text>')
a(f'<text x="{(X(5)+X(12))/2}" y="{Y(10)+2}" fill="#8fb8d8" font-size="17" text-anchor="middle">USB toward row 1</text>')
for r in range(2,22):
    a(f'<circle cx="{X(5)}" cy="{Y(r)}" r="8" fill="#0d1116" stroke="#d8dee4" stroke-width="2.4"/>')
    a(f'<circle cx="{X(12)}" cy="{Y(r)}" r="8" fill="#0d1116" stroke="#d8dee4" stroke-width="2.4"/>')
pl={2:"1 GP0",3:"2 GP1",4:"3 GND",5:"4 GP2",6:"5 GP3",12:"11 GP8",13:"12 GP9",15:"14 GP10",16:"15 GP11"}
pr={2:"40 VBUS",3:"39 VSYS",4:"38 GND",6:"36 3V3",11:"31 GP26"}
for r,t in pl.items(): a(f'<text x="{X(5)+22}" y="{Y(r)+6}" fill="#dbe6f0" font-size="15">{t}</text>')
for r,t in pr.items(): a(f'<text x="{X(12)-22}" y="{Y(r)+6}" fill="#dbe6f0" font-size="15" text-anchor="end">{t}</text>')
# ---- sensor landing rows (4 male pins across cols Q R S T)
sens=[(3,"BNO085 bay      0x4B   DI->3V3"),(7,"BNO085 gimbal  0x4A   STEMMA QT 300 mm"),
      (11,"BME688           0x76   SDO->GND"),(15,"BMP388           0x77   default")]
for r,lab in sens:
    a(f'<rect x="{X(17)-22}" y="{Y(r)-20}" width="{X(20)-X(17)+44}" height="40" rx="8" fill="#2b2f39" fill-opacity="0.9" stroke="#7f8b98" stroke-width="2.4"/>')
    a(f'<text x="{X(20)+40}" y="{Y(r)+6}" fill="#e8eef4" font-size="16">{lab}</text>')
# ---- servo headers  col A/B/C
for r,lab,pin in [(5,"SERVO 1  pitch",5),(8,"SERVO 2  yaw",6)]:
    a(f'<rect x="{X(1)-22}" y="{Y(r)-20}" width="{X(3)-X(1)+44}" height="40" rx="8" fill="#3a2b18" fill-opacity="0.92" stroke="#caa96a" stroke-width="2.4"/>')
    a(f'<text x="{X(2)}" y="{Y(r)-30}" fill="#e8d9b8" font-size="15" text-anchor="middle">{lab}</text>')
    direct(3,r,5,pin,SIG)
# ---- microSD breakout col C rows 12-19
part(3,12,3,19,"#241d33","#c07be0","",15)
a(f'<text x="{X(3)-30}" y="{Y(15)}" fill="#dcc9f0" font-size="17" text-anchor="middle" transform="rotate(-90 {X(3)-30} {Y(15)})">microSD breakout</text>')
sd={12:"5V",13:"3V",14:"CS",15:"DI",16:"DO",17:"CLK",18:"GND",19:"CD"}
for r,t in sd.items(): a(f'<text x="{X(3)+22}" y="{Y(r)+5}" fill="#e6dcf5" font-size="14">{t}</text>')
# SD wiring
wire(3,12,2,12,V5)          # 5V
wire(3,18,1,18,GND)         # GND
direct(3,14,5,13,SIG)       # CS  -> GP9
direct(3,15,5,16,SIG)       # DI  -> GP11 MOSI
direct(3,16,5,12,SIG)       # DO  -> GP8 MISO
direct(3,17,5,15,SIG)       # CLK -> GP10
# ---- Pico power + I2C + ADC
a(f'<path d="M {X(12)} {Y(3)} L {X(13)} {Y(3)} L {X(13)} {Y(23)} L {X(2)} {Y(23)}" fill="none" stroke="{V5}" stroke-width="5" stroke-linejoin="round"/>')
a(f'<path d="M {X(12)} {Y(4)} L {X(14)} {Y(4)} L {X(14)} {Y(24)} L {X(1)} {Y(24)}" fill="none" stroke="{GND}" stroke-width="5" stroke-linejoin="round"/>')
a(f'<path d="M {X(12)} {Y(6)} L {X(15)} {Y(6)} L {X(15)} {Y(2)} L {X(20)} {Y(2)}" fill="none" stroke="{V33}" stroke-width="5" stroke-linejoin="round"/>')
a(f'<path d="M {X(5)} {Y(2)} L {X(4)} {Y(2)} L {X(4)} {Y(1)} L {X(18)} {Y(1)} L {X(18)} {Y(2)}" fill="none" stroke="{SDA}" stroke-width="5" stroke-linejoin="round"/>')
a(f'<path d="M {X(5)} {Y(3)} L {X(4)} {Y(3)} L {X(4)} {Y(22)} L {X(19)} {Y(22)} L {X(19)} {Y(20)}" fill="none" stroke="{SCL}" stroke-width="5" stroke-linejoin="round"/>')
a(f'<path d="M {X(12)} {Y(11)} L {X(15)} {Y(11)} L {X(15)} {Y(21)} L {X(16)} {Y(21)}" fill="none" stroke="{ADC}" stroke-width="5" stroke-linejoin="round"/>')
# right-side GND tie
a(f'<path d="M {X(17)} {Y(20)} L {X(17)} {Y(24)} L {X(1)} {Y(24)}" fill="none" stroke="{GND}" stroke-width="5" stroke-linejoin="round"/>')
# ---- divider + bulk cap + power entry
a(f'<rect x="{X(16)-22}" y="{Y(21)-20}" width="{X(18)-X(16)+44}" height="{Y(23)-Y(21)+40}" rx="8" fill="#2a2035" fill-opacity="0.9" stroke="#c07be0" stroke-width="2.4"/>')
a(f'<text x="{X(17)}" y="{Y(21)-30}" fill="#dcc9f0" font-size="15" text-anchor="middle">100k / 47k divider</text>')
a(f'<text x="{X(19)+30}" y="{Y(22)+5}" fill="#dcc9f0" font-size="14">100k to PACK+, 47k to GND, 100nF to GND</text>')
a(f'<rect x="{X(1)-24}" y="{Y(11)-20}" width="{X(2)-X(1)+48}" height="40" rx="8" fill="#3d1f1c" fill-opacity="0.92" stroke="#e2483d" stroke-width="2.4"/>')
a(f'<text x="{X(4)+18}" y="{Y(12)+30}" fill="#f0c9c5" font-size="15">470 uF bulk (+ to B, - to A)</text>')
a(f'<rect x="{X(1)-24}" y="{Y(22)-20}" width="{X(2)-X(1)+48}" height="40" rx="8" fill="#14304a" fill-opacity="0.92" stroke="#4d9be6" stroke-width="2.4"/>')
a(f'<text x="{X(4)+18}" y="{Y(23)+30}" fill="#cfe2f5" font-size="15">UBEC 5 V out (+ to B22, - to A22)</text>')
# ---- power chain schematic panel
ly=MY+(ROWS-1)*P+110
a(f'<rect x="{MX-58}" y="{ly-34}" width="{(COLS-1)*P+116+300}" height="420" rx="12" fill="#161b22" stroke="#39424d" stroke-width="2"/>')
a(f'<text x="{MX-38}" y="{ly}" fill="#eaf3ee" font-size="23" font-weight="bold">Power chain, off-board (everything before column A / column B)</text>')
def blk(x,y,w,h,fill,stroke,t1,t2="",t3=""):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" fill-opacity="0.9" stroke="{stroke}" stroke-width="2.6"/>')
    a(f'<text x="{x+w/2}" y="{y+26}" fill="#eef4f8" font-size="16" text-anchor="middle" font-weight="bold">{t1}</text>')
    if t2: a(f'<text x="{x+w/2}" y="{y+46}" fill="#c3ced8" font-size="13.5" text-anchor="middle">{t2}</text>')
    if t3: a(f'<text x="{x+w/2}" y="{y+64}" fill="#c3ced8" font-size="13.5" text-anchor="middle">{t3}</text>')
def arrow(x1,y,x2,color,lab=""):
    a(f'<line x1="{x1}" y1="{y}" x2="{x2-10}" y2="{y}" stroke="{color}" stroke-width="4.5"/>')
    a(f'<path d="M {x2-12} {y-6} L {x2} {y} L {x2-12} {y+6} Z" fill="{color}"/>')
    if lab: a(f'<text x="{(x1+x2)/2}" y="{y-10}" fill="{color}" font-size="13" text-anchor="middle">{lab}</text>')
by=ly+24; bh=78
blk(MX-38,      by,138,bh,"#3d1f1c",V5,"2S LiPo","450 mAh 25C","7.4 V nom, 8.4 V max")
arrow(MX+104,by+bh/2,MX+150,V5,"pack+")
blk(MX+152,     by,126,bh,"#2a2f38","#9aa4ad","PPTC 2.6 A","resettable","series, pack+ leg")
arrow(MX+282,by+bh/2,MX+328,V5)
blk(MX+330,     by,132,bh,"#14304a","#4d9be6","ARM SWITCH","SPDT 3 A","breaks pack+")
arrow(MX+466,by+bh/2,MX+512,V5,"armed")
blk(MX+514,     by,168,bh,"#1f3a2a",SIG,"UBEC 5 V 3 A","switching, not linear","IN+ IN-  ->  OUT+ OUT-")
arrow(MX+686,by+bh/2,MX+732,V5,"5 V")
blk(MX+734,     by,150,bh,"#3d1f1c",V5,"COLUMN B","+5 V bus","Pico VSYS, servos, SD")
# ground return
a(f'<path d="M {MX+32} {by+bh+14} L {MX+32} {by+bh+42} L {MX+809} {by+bh+42} L {MX+809} {by+bh+14}" fill="none" stroke="{GND}" stroke-width="4"/>')
a(f'<text x="{MX+420}" y="{by+bh+60}" fill="{GND}" font-size="14" text-anchor="middle">pack- -> UBEC IN-  ->  UBEC OUT-  ->  COLUMN A (GND bus).  One common ground, no split returns.</text>')
# second row: the three passives, drawn
sy=by+bh+92
a(f'<text x="{MX-38}" y="{sy-6}" fill="#eaf3ee" font-size="19" font-weight="bold">The three passives, and what each is for</text>')
py=sy+18; pw=268; ph=126
# 470uF
a(f'<rect x="{MX-38}" y="{py}" width="{pw}" height="{ph}" rx="9" fill="#1b2029" stroke="#e2483d" stroke-width="2.2"/>')
a(f'<text x="{MX-22}" y="{py+24}" fill="#f3cdc8" font-size="16" font-weight="bold">470 uF electrolytic  ->  A11 / B11</text>')
cx=MX+40; cy=py+66
a(f'<line x1="{cx}" y1="{cy-22}" x2="{cx}" y2="{cy-6}" stroke="{V5}" stroke-width="3.4"/>')
a(f'<line x1="{cx-20}" y1="{cy-6}" x2="{cx+20}" y2="{cy-6}" stroke="{V5}" stroke-width="4.4"/>')
a(f'<path d="M {cx-20} {cy+8} A 20 12 0 0 0 {cx+20} {cy+8}" fill="none" stroke="{GND}" stroke-width="4.4"/>')
a(f'<line x1="{cx}" y1="{cy+10}" x2="{cx}" y2="{cy+28}" stroke="{GND}" stroke-width="3.4"/>')
a(f'<text x="{cx+34}" y="{cy-14}" fill="{V5}" font-size="13">+ to B (5 V)</text>')
a(f'<text x="{cx+34}" y="{cy+24}" fill="{GND}" font-size="13">- to A (GND)</text>')
a(f'<text x="{MX-22}" y="{py+112}" fill="#c3ced8" font-size="13">Servo stall transient reservoir. Without it a stall browns out the Pico.</text>')
# divider
a(f'<rect x="{MX+248}" y="{py}" width="{pw+40}" height="{ph}" rx="9" fill="#1b2029" stroke="#c07be0" stroke-width="2.2"/>')
a(f'<text x="{MX+264}" y="{py+24}" fill="#e2cdf3" font-size="16" font-weight="bold">100k + 47k divider  ->  GP26</text>')
dx=MX+300; dy=py+46
a(f'<line x1="{dx}" y1="{dy}" x2="{dx}" y2="{dy+12}" stroke="{V5}" stroke-width="3"/>')
a(f'<rect x="{dx-11}" y="{dy+12}" width="22" height="26" fill="none" stroke="#e8eef4" stroke-width="2.6"/>')
a(f'<line x1="{dx}" y1="{dy+38}" x2="{dx}" y2="{dy+50}" stroke="{ADC}" stroke-width="3"/>')
a(f'<rect x="{dx-11}" y="{dy+50}" width="22" height="26" fill="none" stroke="#e8eef4" stroke-width="2.6"/>')
a(f'<line x1="{dx}" y1="{dy+76}" x2="{dx}" y2="{dy+88}" stroke="{GND}" stroke-width="3"/>')
a(f'<line x1="{dx-14}" y1="{dy+88}" x2="{dx+14}" y2="{dy+88}" stroke="{GND}" stroke-width="4"/>')
a(f'<line x1="{dx}" y1="{dy+44}" x2="{dx+54}" y2="{dy+44}" stroke="{ADC}" stroke-width="3"/>')
a(f'<text x="{dx+20}" y="{dy+30}" fill="#e8eef4" font-size="13">100k</text>')
a(f'<text x="{dx+20}" y="{dy+68}" fill="#e8eef4" font-size="13">47k</text>')
a(f'<text x="{dx-18}" y="{dy-4}" fill="{V5}" font-size="13" text-anchor="end">armed pack+</text>')
a(f'<text x="{dx+58}" y="{dy+40}" fill="{ADC}" font-size="13">GP26</text>')
a(f'<text x="{MX+264}" y="{py+112}" fill="#c3ced8" font-size="13">8.4 V -> 2.686 V   |   6.0 V -> 1.918 V   both inside the 3.3 V ADC range</text>')
# 100nF
a(f'<rect x="{MX+576}" y="{py}" width="{pw+40}" height="{ph}" rx="9" fill="#1b2029" stroke="#e8a13a" stroke-width="2.2"/>')
a(f'<text x="{MX+592}" y="{py+24}" fill="#f3e0c0" font-size="16" font-weight="bold">100 nF  ->  GP26 to GND</text>')
nx=MX+640; ny=py+62
a(f'<line x1="{nx}" y1="{ny-20}" x2="{nx}" y2="{ny-5}" stroke="{ADC}" stroke-width="3"/>')
a(f'<line x1="{nx-20}" y1="{ny-5}" x2="{nx+20}" y2="{ny-5}" stroke="#e8eef4" stroke-width="4"/>')
a(f'<line x1="{nx-20}" y1="{ny+5}" x2="{nx+20}" y2="{ny+5}" stroke="#e8eef4" stroke-width="4"/>')
a(f'<line x1="{nx}" y1="{ny+5}" x2="{nx}" y2="{ny+22}" stroke="{GND}" stroke-width="3"/>')
a(f'<line x1="{nx-14}" y1="{ny+22}" x2="{nx+14}" y2="{ny+22}" stroke="{GND}" stroke-width="4"/>')
a(f'<text x="{MX+592}" y="{py+112}" fill="#c3ced8" font-size="13">Anti-alias / noise filter on the ADC tap. Sits across the 47k leg.</text>')
a('</svg>')
import os; _here=os.path.dirname(os.path.abspath(__file__)); open(os.path.join(_here,"wyvern_perfboard_wiring.svg"),"w").write("\n".join(s))
print("ok", W, H)
