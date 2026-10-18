#!/usr/bin/env python3
"""GTR70E WYVERN, fully-routed flight wiring schematic (KiCad-7 .kicad_sch).
Unlike the flat-netlist harness, every component is DRAWN and PHYSICALLY WIRED pin-to-pin with
orthogonal wire segments, junctions, power rails (2S LiPo -> buck -> LDO / GND) and net labels.
No symbol library required, components are documentation rectangles with real pin stubs + wires.

Traced pin-by-pin against the actual custom RP2350B PCB1 (netlist/BOM/schematic in PCB/ -- see
CONFLICTS.md section 4 and firmware/wyvern4_tvc/imu_grv.h's file header). The board carries ONE
bare RP2350B chip, ONE shared I2C bus carrying every sensor by address (no mux), and a real INA226
power monitor for rail sensing."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
S=[] # s-expr item accumulator
def esc(x): return str(x).replace('"','\\"')
def rect(x,y,w,h):
    S.append(f'(rectangle (start {x} {y}) (end {x+w} {y+h}) (stroke (width 0.25)(type solid)) (fill (type none)))')
def text(x,y,t,sz=1.3,j="left"):
    S.append(f'(text "{esc(t)}" (at {x} {y} 0)(effects (font (size {sz} {sz}))(justify {j})))')
def wire(x1,y1,x2,y2,w=0.15):
    S.append(f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width {w})(type solid)))')
def poly(pts,w=0.15):
    for i in range(len(pts)-1): wire(*pts[i],*pts[i+1],w)
def junc(x,y):
    S.append(f'(junction (at {x} {y}) (diameter 0.9) (color 0 0 0 0))')
def label(x,y,t,sz=1.0,ang=0):
    S.append(f'(label "{esc(t)}" (at {x} {y} {ang})(effects (font (size {sz} {sz}))(justify left)))')

PINLEN=3.0
class Comp:
    def __init__(self,name,x,y,w,h,subtitle=""):
        self.x,self.y,self.w,self.h=x,y,w,h; self.an={}
        rect(x,y,w,h); text(x+1.5,y+3.5,name,1.5)
        if subtitle: text(x+1.5,y+h-1.5,subtitle,1.0)
    def pins(self,side,names,y0=None,y1=None,x0=None,x1=None):
        n=len(names)
        for i,nm in enumerate(names):
            f=(i+1)/(n+1)
            if side=="L":
                py=self.y+self.h*f; px=self.x
                a=(px-PINLEN,py); wire(px,py,a[0],a[1]); text(px+1,py-0.6,nm,1.0)
            elif side=="R":
                py=self.y+self.h*f; px=self.x+self.w
                a=(px+PINLEN,py); wire(px,py,a[0],a[1]); text(px-1,py-0.6,nm,1.0,"right")
            elif side=="T":
                px=self.x+self.w*f; py=self.y
                a=(px,py-PINLEN); wire(px,py,a[0],a[1]); text(px,py-PINLEN-0.6,nm,0.9)
            elif side=="B":
                px=self.x+self.w*f; py=self.y+self.h
                a=(px,py+PINLEN); wire(px,py,a[0],a[1]); text(px,py+PINLEN+2.0,nm,0.9)
            self.an[nm]=a
    def p(self,nm): return self.an[nm]

# ---------------- layout ----------------
# Power rails (horizontal): buck rail (servos/expansion connectors), 3V3 logic rail, GND.
# 2S LiPo -> TPS564201 buck -> intermediate rail -> AP2112K-3.3 LDO -> 3V3 logic rail.
RAIL_VBUCK=18; RAIL_3V3=26; RAIL_GND=286
RX0,RX1=40,395
for ry,nm in [(RAIL_VBUCK,"+VBUCK"),(RAIL_3V3,"+3V3"),(RAIL_GND,"GND")]:
    wire(RX0,ry,RX1,ry,0.3); label(RX0-8,ry-0.6,nm,1.3)

# I2C bus rails (horizontal, like the power rails): SDA/SCL run the full width and every sensor on
# the shared bus taps in with a junction -- there is no mux fanning channels out to each device.
RAIL_SDA=125; RAIL_SCL=131
for ry,nm in [(RAIL_SDA,"SDA0 (GP0)"),(RAIL_SCL,"SCL0 (GP1)")]:
    wire(RX0,ry,RX1,ry,0.3); label(RX0-8,ry-0.6,nm,1.3)

# ----- power source (far left): 2S LiPo -> TPS564201 buck -> AP2112K-3.3 LDO -----
batt=Comp("2S LiPo 7.4V",42,45,46,22,"~450mAh flight pack")
batt.pins("T",["+"] ,); batt.pins("B",["GND"])
buck=Comp("TPS564201 BUCK (U15)",42,88,46,20,"7.4V -> VBUCK")
buck.pins("L",["VIN","G"]); buck.pins("T",["VBUCK"]); buck.pins("B",["GND"])
ldo=Comp("AP2112K-3.3 LDO (U7)",42,128,46,20,"VBUCK -> 3.3V")
ldo.pins("L",["VIN","G"]); ldo.pins("T",["3V3"]); ldo.pins("B",["GND"])

# battery -> buck input
poly([batt.p("+"),(batt.p("+")[0],38),(34,38),(34,buck.p("VIN")[1]),buck.p("VIN")])
poly([batt.p("GND"),(batt.p("GND")[0],RAIL_GND)]); junc(batt.p("GND")[0],RAIL_GND)
poly([buck.p("G"),(buck.p("G")[0],RAIL_GND)]); junc(buck.p("G")[0],RAIL_GND)
# buck VBUCK -> VBUCK rail, also feeds the LDO input
poly([buck.p("VBUCK"),(buck.p("VBUCK")[0],RAIL_VBUCK)]); junc(buck.p("VBUCK")[0],RAIL_VBUCK)
poly([ldo.p("VIN"),(30,ldo.p("VIN")[1]),(30,RAIL_VBUCK)]); junc(30,RAIL_VBUCK)
poly([ldo.p("G"),(ldo.p("G")[0],RAIL_GND)]); junc(ldo.p("G")[0],RAIL_GND)
poly([ldo.p("3V3"),(ldo.p("3V3")[0],RAIL_3V3)]); junc(ldo.p("3V3")[0],RAIL_3V3)

# ----- RP2350B (central hub, custom PCB1 -- bare chip, not a Pico module) -----
mcu=Comp("RP2350B (U1)",150,40,70,220,"QFN-80 · dual-M33 · no radio chip")
mcu.pins("T",["3V3IN"])
mcu.pins("B",["GND"])
mcu.pins("R",["GP0 SDA0","GP1 SCL0","GP2 S1","GP3 S2","GP4 spare","GP5 spare",
              "GP8 MISO","GP9 CS","GP10 SCK","GP11 MOSI",
              "GP12 RBF","GP34 BUZ","GP35 LED","GP36 CAM","GP37 IRQ"])
poly([mcu.p("3V3IN"),(mcu.p("3V3IN")[0],RAIL_3V3)]); junc(mcu.p("3V3IN")[0],RAIL_3V3)
poly([mcu.p("GND"),(mcu.p("GND")[0],RAIL_GND)]); junc(mcu.p("GND")[0],RAIL_GND)

# ----- microSD (CARD1, TF-01A) -----
sd=Comp("microSD (CARD1)",250,40,60,40,"flight log · pin4/VDD traces to GND, possible defect")
sd.pins("L",["MISO","MOSI","SCK","CS"]); sd.pins("T",["3V3"]); sd.pins("B",["GND"])

# ----- servos -----
sv1=Comp("SERVO 1 (pitch, JST U8)",250,90,58,18)
sv1.pins("L",["SIG","+V","GND"])
sv2=Comp("SERVO 2 (yaw, JST U9)",250,112,58,18)
sv2.pins("L",["SIG","+V","GND"])

# ----- shared-bus sensors (all tap the same SDA0/SCL0 rails, differentiated by I2C address only) -----
# No PCA9548A mux exists on the real PCB1 -- every onboard sensor plus the external STEMMA-QT port
# shares ONE bus. Body is a BNO055 (a different chip family/driver than the external unit, see
# imu_grv.h); BMP388 is not populated on this board rev (baro.h keeps that code path as a
# fails-closed no-op, so it's omitted from this wiring diagram, not drawn as present).
body=Comp("BNO055 BODY 0x28",340,60,58,26,"onboard · addr CONFIRMED (COM3->GND)")
body.pins("L",["SDA","SCL"]); body.pins("T",["3V3"]); body.pins("B",["GND"])
ext=Comp("BNO085 EXTERNAL 0x4A",340,96,58,26,"STEMMA-QT · bulkhead-boundary mount, not gimbal")
ext.pins("L",["SDA","SCL"]); ext.pins("T",["3V3"]); ext.pins("B",["GND"])
bme=Comp("BME680 0x76",340,132,58,24,"onboard baro · addr CONFIRMED (SDO->GND)")
bme.pins("L",["SDA","SCL"]); bme.pins("T",["3V3"]); bme.pins("B",["GND"])
ina=Comp("INA226 (U4) -- WIRING PROBLEM",340,166,58,30,"reads VBUCK not pack V; addr strap invalid, see CONFLICTS.md")
ina.pins("L",["SDA","SCL"]); ina.pins("T",["3V3"]); ina.pins("B",["GND"]); ina.pins("R",["VIN+","VIN-","VBUS","A1"])
mag=Comp("LIS3MDL (U5) 0x1C",340,206,58,24,"addr CONFIRMED (SD0/SA1->GND) · unused by firmware")
mag.pins("L",["SDA","SCL"]); mag.pins("T",["3V3"]); mag.pins("B",["GND"])

# ----- R10 (in parallel with power switch U13, NOT a current shunt in series with pack current) -----
# R10 does not feed INA226's VIN+ as a textbook current shunt would. Real wiring, traced pin-by-pin:
# INA226 VIN+ -> GND directly, VIN- -> VBUCK directly, VBUS and the A1 address pin both -> the same
# node R10 bridges to VBUCK (in parallel with switch U13). None of this spans real pack current.
# See battery.h and CONFLICTS.md section 3 for the full finding.
shunt=Comp("R10 (10mOhm, 2512) -- parallel w/ SW U13, not a shunt",42,168,70,18)
shunt.pins("R",["to VBUCK"])
a=ina.p("VIN+"); poly([a,(a[0]+10,a[1]),(a[0]+10,RAIL_GND)]); junc(a[0]+10,RAIL_GND)
label(a[0]+2,a[1]-0.6,"VIN+ -> GND (not pack-referenced)")
b=ina.p("VIN-"); poly([b,(b[0]+10,b[1]),(b[0]+10,RAIL_VBUCK)]); junc(b[0]+10,RAIL_VBUCK)
label(b[0]+2,b[1]-0.6,"VIN- -> VBUCK (buck OUTPUT, not pack)")
c=ina.p("VBUS"); poly([c,(c[0]+14,c[1]),(c[0]+14,RAIL_VBUCK)]); junc(c[0]+14,RAIL_VBUCK)
label(c[0]+2,c[1]-0.6,"VBUS -> VBUCK (reads ~5V rail)")
d=ina.p("A1"); poly([d,(d[0]+18,d[1]),(d[0]+18,RAIL_VBUCK)]); junc(d[0]+18,RAIL_VBUCK)
label(d[0]+2,d[1]-0.6,"A1 -> ~5V, NOT a valid addr strap")

# camera
cam=Comp("i3 4K thumb cam",96,40,46,30,"self-contained")
cam.pins("R",["V_EN","GND"])

# ================= WIRING =================
def chan(a,b,cx,lbl=None):
    poly([a,(cx,a[1]),(cx,b[1]),b])
    if lbl: label(a[0]+ (4 if a[0]<cx else -4), a[1]-0.6, lbl)

# SD interface, RP2350B -> microSD (4 nets) -- confirmed via netlist trace (CARD1's CMD/DI pin,
# i.e. MOSI, traces to GP11, and DAT3/CS to GP9)
for pin,sdpin,cx,nm in [("GP8 MISO","MISO",226,"MISO"),("GP9 CS","CS",229,"CS"),
                        ("GP10 SCK","SCK",232,"SCK"),("GP11 MOSI","MOSI",235,"MOSI")]:
    chan(mcu.p(pin),sd.p(sdpin),cx,nm)

# servo signals
chan(mcu.p("GP2 S1"),sv1.p("SIG"),243,"SERVO1")
chan(mcu.p("GP3 S2"),sv2.p("SIG"),246,"SERVO2")

# RP2350B -> shared I2C bus rails
poly([mcu.p("GP0 SDA0"),(mcu.p("GP0 SDA0")[0]+8,mcu.p("GP0 SDA0")[1]),(mcu.p("GP0 SDA0")[0]+8,RAIL_SDA)])
junc(mcu.p("GP0 SDA0")[0]+8,RAIL_SDA)
poly([mcu.p("GP1 SCL0"),(mcu.p("GP1 SCL0")[0]+8,mcu.p("GP1 SCL0")[1]),(mcu.p("GP1 SCL0")[0]+8,RAIL_SCL)])
junc(mcu.p("GP1 SCL0")[0]+8,RAIL_SCL)

# each shared-bus sensor taps SDA0/SCL0 directly -- no mux fan-out
def tap_i2c(comp):
    a=comp.p("SDA"); poly([a,(a[0]-4,a[1]),(a[0]-4,RAIL_SDA)]); junc(a[0]-4,RAIL_SDA)
    b=comp.p("SCL"); poly([b,(b[0]-4,b[1]),(b[0]-4,RAIL_SCL)]); junc(b[0]-4,RAIL_SCL)
for c in [body,ext,bme,ina,mag]: tap_i2c(c)

# GPIO: all four of GP37/36/35/34 are CONFIRMED-usable H1 GPIOs (H1 pins 7/8/9/10); which flight
# signal rides which pin is a firmware choice, not a schematic label. GP12 (H1 pin13) is reserved
# for a possible future RBF bodge wire -- NOTHING is soldered there on PCB1 as fabricated; U13 (the
# physical power switch) has no GPIO connection at all, see CONFLICTS.md section 4.
poly([mcu.p("GP36 CAM"),(248,mcu.p("GP36 CAM")[1]),(248,33),(cam.p("V_EN")[0]+8,33),
      (cam.p("V_EN")[0]+8,cam.p("V_EN")[1]),cam.p("V_EN")])
label(mcu.p("GP36 CAM")[0]+4,mcu.p("GP36 CAM")[1]-0.6,"CAM_EN")
for pin,nm in [("GP37 IRQ","LAUNCH_IRQ (H1 pin7, confirmed GPIO)"),
               ("GP12 RBF","RBF (H1 pin13, NOT wired to anything on PCB1)"),
               ("GP34 BUZ","BUZZER (H1 pin10, confirmed GPIO)"),
               ("GP35 LED","STATUS_LED (H1 pin9, confirmed GPIO)")]:
    a=mcu.p(pin); poly([a,(a[0]+8,a[1])]); label(a[0]+9,a[1]-0.6,nm)

# ----- power-rail taps: 3V3 (top pins up to 3V3 rail), GND (bottom pins down to GND rail) -----
def to3v3(comp,pin="3V3"):
    a=comp.p(pin); poly([a,(a[0],RAIL_3V3)]); junc(a[0],RAIL_3V3)
def toGND(comp,pin="GND"):
    a=comp.p(pin); poly([a,(a[0],RAIL_GND)]); junc(a[0],RAIL_GND)
for c in [sd,body,ext,bme,ina,mag]: to3v3(c)
for c in [sd,body,ext,bme,ina,mag]: toGND(c)
# servos off the VBUCK rail (not the 3V3 logic rail) -- matches the real power chain in §3
for sv in [sv1,sv2]:
    a=sv.p("+V"); poly([a,(a[0],RAIL_VBUCK)]); junc(a[0],RAIL_VBUCK)
    g=sv.p("GND"); poly([g,(g[0]-2,g[1]),(g[0]-2,RAIL_GND)]); junc(g[0]-2,RAIL_GND)
g=cam.p("GND"); poly([g,(g[0]+12,g[1]),(g[0]+12,RAIL_GND)]); junc(g[0]+12,RAIL_GND)

# title + notes
text(40,8,"GTR70E WYVERN, Flight Wiring (fully routed, all components connected) -- PCB1 custom RP2350B",2.4)
text(40,300,"One shared I2C bus (no mux), every address netlist-CONFIRMED: body BNO055 0x28, "
             "external BNO085 0x4A (STEMMA-QT, bulkhead-boundary mount), BME680 0x76, LIS3MDL 0x1C. "
             "No BMP388 populated, no WiFi/BLE radio chip on this board. INA226 (U4) has a real "
             "wiring problem, not just an unverified address -- reads the ~5V buck rail instead of "
             "pack voltage, no true current shunt, address strap ties to an invalid ~5V node -- see "
             "CONFLICTS.md section 3 and battery.h. RBF (GP12/H1 pin13) is not wired to any switch "
             "on this board rev; the other four H1 GPIOs (37/36/35/34) are confirmed-usable, their "
             "function assignment is a firmware choice. CARD1 pin4 traces to GND where VDD would be "
             "expected -- possible SD-power defect, bench-check before trusting flight logging.",1.1)

body_s="\n ".join(S)
out=f'''(kicad_sch (version 20230121) (generator "gtr70e_wyvern_connected") (paper "A1")
  (title_block (title "GTR70E WYVERN Flight Wiring, fully routed") (company "Skylight Industries") (rev "5.0"))
  (lib_symbols)
  {body_s}
  (sheet_instances (path "/" (page "1"))))'''
p=os.path.join(HERE,"WYVERN_E4_flight_wiring_connected.kicad_sch")
open(p,"w").write(out)
print("wrote",p,"| parens",out.count("("),"==",out.count(")"),"OK" if out.count("(")==out.count(")") else "BAD")
print("wires:",sum(1 for i in S if i.startswith("(wire")),"junctions:",sum(1 for i in S if i.startswith("(junction")),
      "rects:",sum(1 for i in S if i.startswith("(rectangle")))
