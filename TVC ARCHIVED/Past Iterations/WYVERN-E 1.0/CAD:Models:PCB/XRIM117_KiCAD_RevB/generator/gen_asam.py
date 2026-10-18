#!/usr/bin/env python3
"""XRIM-117 ASAM-1 / ASAM-2 Rev B — STM32F411 actuator controllers.
Run: python3 gen_asam.py 1   or   python3 gen_asam.py 2"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from kicadgen import *
import parts
from autoroute import Router, stitch_gnd
from verify import verify

VAR = int(sys.argv[1]) if len(sys.argv)>1 else 1
NAME = f"ASAM{VAR}"
TITLE = "ASAM-1 Mid Ring Controller" if VAR==1 else "ASAM-2 TVC + Sustainer Controller"
OUT = os.path.join(os.path.dirname(__file__), '..', 'out', f'{NAME}_KiCAD_RevB')
os.makedirs(OUT, exist_ok=True)

# STM32F411CEU6 UFQFPN-48 (ST DS10314; LQFP48-standard pin order)
F4 = {
 1:"+3V3", 2:"LED_STATUS", 3:"", 4:"", 5:"XIN", 6:"XOUT", 7:"NRST", 8:"GND",
 9:"+3V3", 10:("" if VAR==1 else "TVC_PITCH"), 11:("" if VAR==1 else "TVC_YAW"),
 12:"UART_TX", 13:"UART_RX", 14:"IMU_CS", 15:"SPI1_SCK", 16:"SPI1_MISO",
 17:"SPI1_MOSI", 18:("" if VAR==1 else "SUS_CONT"), 19:"VBAT_SENSE",
 20:"PB2_STRAP", 21:("SPARE_IO" if VAR==1 else "REED"), 22:"VCAP",
 23:"GND", 24:"+3V3", 25:"ARM_IN", 26:"", 27:"",
 28:("" if VAR==1 else "SUS_FIRE"),
 29:("SERVO1" if VAR==1 else ""), 30:("SERVO2" if VAR==1 else ""),
 31:("SERVO3" if VAR==1 else ""), 32:("SERVO4" if VAR==1 else ""),
 33:"", 34:"SWDIO", 35:"GND", 36:"+3V3", 37:"SWCLK", 38:"IMU_INT1",
 39:"", 40:"", 41:"BMP_INT", 42:"I2C1_SCL", 43:"I2C1_SDA", 44:"BOOT0",
 45:"", 46:"", 47:"GND", 48:"+3V3", 49:"GND"}
F4N = {1:"VBAT",2:"PC13",3:"PC14",4:"PC15",5:"PH0",6:"PH1",7:"NRST",8:"VSSA",
 9:"VDDA",10:"PA0",11:"PA1",12:"PA2_TX",13:"PA3_RX",14:"PA4",15:"PA5",16:"PA6",
 17:"PA7",18:"PB0",19:"PB1",20:"PB2",21:"PB10",22:"VCAP1",23:"VSS",24:"VDD",
 25:"PB12",26:"PB13",27:"PB14",28:"PB15",29:"PA8",30:"PA9",31:"PA10",32:"PA11",
 33:"PA12",34:"PA13",35:"VSS",36:"VDD",37:"PA14",38:"PA15",39:"PB3",40:"PB4",
 41:"PB5",42:"PB6",43:"PB7",44:"BOOT0",45:"PB8",46:"PB9",47:"VSS",48:"VDD",49:"EP"}

IMU = {1:"SPI1_MISO",2:"",3:"",4:"IMU_INT1",5:"+3V3",6:"GND",7:"GND",8:"+3V3",
       9:"GND",10:"",11:"",12:"IMU_CS",13:"SPI1_SCK",14:"SPI1_MOSI"}
IMU_NAMES={1:"AP_SDO",2:"RESV",3:"RESV",4:"INT1",5:"VDDIO",6:"GND",7:"RESV_GND",
           8:"VDD",9:"INT2/FSYNC",10:"RESV",11:"RESV",12:"AP_CS",13:"AP_SCLK",14:"AP_SDI"}
BMP = {1:"+3V3",2:"I2C1_SCL",3:"GND",4:"I2C1_SDA",5:"GND",6:"+3V3",7:"BMP_INT",
       8:"GND",9:"GND",10:"+3V3"}
BMP_NAMES={1:"VDDIO",2:"SCK",3:"VSS",4:"SDI",5:"SDO",6:"CSB",7:"INT",8:"VSS",9:"VSS",10:"VDD"}
# INA219 SOT-23-8 (TI: IN+=1 IN-=2 GND=3 VS=4 SCL=5 SDA=6 A0=7 A1=8)
INA = {1:"VBAT2S",2:"V_SERVO",3:"GND",4:"+3V3",5:"I2C1_SCL",6:"I2C1_SDA",7:"GND",8:"GND"}
INA_NAMES={1:"IN+",2:"IN-",3:"GND",4:"VS",5:"SCL",6:"SDA",7:"A0",8:"A1"}
# TPS54202 SOT-23-6 (TI: GND=1 SW=2 VIN=3 FB=4 EN=5 BOOT=6) — EN floats (auto-enable)
BUCK = {1:"GND",2:"BUCK_SW",3:"VBAT2S",4:"BUCK_FB",5:"",6:"BUCK_BOOT"}
BUCK_NAMES={1:"GND",2:"SW",3:"VIN",4:"FB",5:"EN",6:"BOOT"}
PC817 = {1:"ARM_IN",2:"SUS_FIRE",3:"GND",4:"SUS_GATE"}  # A,K,E,C ; emitter->GND? see note
# Topology: ARM_IN(3V3 from CCM) -> R330 -> LED A(1); K(2) -> PB15 (MCU sinks to fire)
# OUT: C(4) <- 10k from VBAT2S ... drives gate ... E(3) -> GND  => inverted? use common-emitter:
# C(4) pulled up to VBAT2S via R10k, C also -> FET gate via 1k; E(3) -> GND.
# LED ON => transistor ON => gate LOW => FET OFF.  INVERTED — wrong.
# Correct: LED ON should FIRE. So wire FET gate to emitter-follower:
# C(4) -> VBAT2S ; E(3) -> gate node, gate 100k pulldown. LED ON -> gate HIGH -> fire.
PC817 = {1:"ARM_IN_R",2:"SUS_FIRE",3:"SUS_GATE",4:"VBAT2S"}
PC817_NAMES={1:"A",2:"K",3:"E",4:"C"}

def main():
    sch = Schematic(f"XRIM-117 {TITLE}",
        "Skylight Industries LLC / Legacy Systems Research Group",
        [f"PDR-002 Rev B | STM32F411CEU6 + ICM-42688-P + BMP388 + INA219 + TPS54202",
         "2S LiPo direct servo rail (MT3608 deleted - undersized 3x) | datasheet-verified pinouts",
         ("4x servo TIM1 PA8-PA11" if VAR==1 else
          "TVC TIM2 PA0/PA1 | sustainer: ARM_IN&PB15 -> PC817 -> AO3400A (two-board interlock)")])
    brd = Board(f"XRIM-117 {NAME} Rev B")

    def boxsym(name, ref, val, fpname, pinmap, names, w=18.0):
        items = sorted(pinmap.keys())
        half=(len(items)+1)//2
        L=[(names[p],str(p),"pas") for p in items[:half]]
        R=[(names[p],str(p),"pas") for p in items[half:]]
        sch.add_lib_symbol(make_box_symbol("XRIM",name,ref,val,"XRIM:"+fpname,L,R,w=w),
                           name, Schematic.box_pins(L,R,w=w))
    boxsym("F411","U","STM32F411CEU6","UFQFPN-48_7x7mm_P0.5mm",F4,F4N,w=22)
    boxsym("ICM42688","U","ICM-42688-P","ICM-42688-P_LGA-14_2.5x3mm",IMU,IMU_NAMES)
    boxsym("BMP388","U","BMP388","BMP388_LGA-10_2x2mm",BMP,BMP_NAMES)
    boxsym("INA219","U","INA219BIDCN","SOT-23-8",INA,INA_NAMES)
    boxsym("TPS54202","U","TPS54202","SOT-23-6",BUCK,BUCK_NAMES)
    boxsym("PC817","U","PC817","PC817_DIP-4",PC817,PC817_NAMES,w=12)
    for nm,glyph,fpn in [("R","R","R_0603"),("C","C","C_0603"),
                         ("CP","CP","CP_Radial_D6.3mm_P2.50mm"),("L","L","L_4x4mm"),
                         ("LED","LED","LED_0603"),("RS","R","R_2512_Shunt")]:
        sch.add_lib_symbol(make_2pin_symbol("XRIM",nm,"R" if nm in("R","RS") else {"C":"C","CP":"C","L":"L","LED":"D"}[nm],
                           nm,"XRIM:"+fpn,glyph), nm, Schematic.TWO_PIN)
    sch.add_lib_symbol(make_mosfet_symbol("XRIM","NFET","AO3400A","XRIM:SOT-23"),"NFET",Schematic.FET_PIN)
    for n in ["GND","+3V3","VBAT2S","V_SERVO"]:
        sch.add_lib_symbol(make_power_symbol(n), "power:"+n, [])
    sch.lib_symbols.append(PWR_FLAG)
    def consym(name,npins,names=None):
        L=[(names[i] if names else f"P{i+1}",str(i+1),"pas") for i in range(npins)]
        sch.add_lib_symbol(make_box_symbol("XRIM",name,"J",name,"",L,[],w=12),name,
                           Schematic.box_pins(L,[],w=12))
    consym("XT30",2,["VBAT+","GND"]); consym("SCREW2",2,["A","B"])
    consym("JST_GH8",8); consym("HDR5",5,["3V3","SWDIO","SWCLK","RST","GND"])
    consym("HDR3",3,["SIG","V+","GND"]); consym("HDR2",2,["A","B"])
    XL=[("IN","1","pas"),("GND","2","pwr")]; XR=[("OUT","3","pas"),("GND","4","pwr")]
    sch.add_lib_symbol(make_box_symbol("XRIM","XTAL4","Y","8MHz","XRIM:Crystal_3225_4Pin",XL,XR,w=10),
                       "XTAL4",Schematic.box_pins(XL,XR,w=10))

    S=sch
    S.text(f"{NAME}: POWER — 2S LiPo -> INA219 shunt -> V_SERVO ; TPS54202 -> 3.3V (L=10uH, fsw=500kHz)",20,30)
    S.place("XRIM:XT30","XT30","J9","XT30 2S LiPo",35,45,{"1":"VBAT2S","2":"GND"})
    S.place("XRIM:RS","RS","R20","10m 1% 2512",60,40,{"1":"VBAT2S","2":"V_SERVO"})
    S.place("XRIM:INA219","INA219","U4","INA219",85,50,{str(k):v for k,v in INA.items()})
    S.place("XRIM:TPS54202","TPS54202","U5","TPS54202",120,46,{str(k):v for k,v in BUCK.items()},nc_pins=("5",))
    S.place("XRIM:L","L","L2","10uH",140,40,{"1":"BUCK_SW","2":"+3V3"},rot=90)
    S.place("XRIM:C","C","C40","100nF",140,52,{"1":"BUCK_BOOT","2":"BUCK_SW"})
    S.place("XRIM:R","R","R30","45.3k",152,46,{"1":"+3V3","2":"BUCK_FB"})
    S.place("XRIM:R","R","R31","10k",152,58,{"1":"BUCK_FB","2":"GND"})
    S.place("XRIM:C","C","C41","10uF 25V",112,58,{"1":"VBAT2S","2":"GND"})
    S.place("XRIM:C","C","C42","10uF 25V",118,58,{"1":"VBAT2S","2":"GND"})
    S.place("XRIM:C","C","C43","22uF",146,58,{"1":"+3V3","2":"GND"})
    S.place("XRIM:C","C","C44","22uF",152,64,{"1":"+3V3","2":"GND"})
    S.place("XRIM:R","R","R32","100k",60,60,{"1":"VBAT2S","2":"VBAT_SENSE"})
    S.place("XRIM:R","R","R33","27k",60,72,{"1":"VBAT_SENSE","2":"GND"})
    for i in range(3):
        S.place("XRIM:CP","CP",f"C{45+i}","470uF 16V",70+14*i,85,{"1":"V_SERVO","2":"GND"})
    for net,x in [("VBAT2S",35),("V_SERVO",60),("+3V3",130),("GND",90)]:
        S.power_flag(net,x,98)

    S.text("MCU: STM32F411CEU6 + 8MHz HSE + SWD + BOOT0",20,115)
    S.place("XRIM:F411","F411","U1","STM32F411CEU6",70,180,{str(k):v for k,v in F4.items()},
            nc_pins=tuple(str(k) for k,v in F4.items() if v==""))
    S.place("XRIM:XTAL4","XTAL4","X1","8MHz CL=12p",130,140,{"1":"XIN","2":"GND","3":"XOUT","4":"GND"})
    S.place("XRIM:C","C","C50","18pF",145,140,{"1":"XIN","2":"GND"})
    S.place("XRIM:C","C","C51","18pF",155,140,{"1":"XOUT","2":"GND"})
    S.place("XRIM:C","C","C52","100nF",130,155,{"1":"NRST","2":"GND"})
    S.place("XRIM:C","C","C53","4.7uF",140,155,{"1":"VCAP","2":"GND"})
    S.place("XRIM:R","R","R34","10k",150,155,{"1":"BOOT0","2":"GND"})
    S.place("XRIM:HDR2","HDR2","J8","BOOT0 jumper",165,155,{"1":"BOOT0","2":"+3V3"})
    S.place("XRIM:R","R","R35","10k",150,168,{"1":"PB2_STRAP","2":"GND"})
    S.place("XRIM:HDR5","HDR5","J10","SWD",165,180,{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"NRST","5":"GND"})
    S.place("XRIM:LED","LED","LED1","STATUS",130,168,{"2":"LED_R","1":"GND"})
    S.place("XRIM:R","R","R36","1k",120,168,{"1":"LED_STATUS","2":"LED_R"})
    S.place("XRIM:R","R","R37","100k",130,196,{"1":"ARM_IN","2":"GND"})
    dec=[("C54","100nF","+3V3"),("C55","100nF","+3V3"),("C56","100nF","+3V3"),
         ("C57","10uF","+3V3"),("C58","100nF","+3V3"),("C59","1uF","+3V3")]
    for i,(r,v,net) in enumerate(dec):
        S.place("XRIM:C","C",r,v,30+14*i,240,{"1":net,"2":"GND"})
    S.text("C54-56 VDD pins, C57 bulk, C58+C59 VDDA",20,255,1.2,False)

    S.text("SENSORS: ICM-42688-P (SPI1) + BMP388 (I2C1 0x76) + 4.7k pullups",220,30)
    S.place("XRIM:ICM42688","ICM42688","U2","ICM-42688-P",250,60,{str(k):v for k,v in IMU.items()},nc_pins=("2","3","10","11"))
    S.place("XRIM:BMP388","BMP388","U3","BMP388",310,60,{str(k):v for k,v in BMP.items()})
    S.place("XRIM:R","R","R38","4.7k",340,50,{"1":"+3V3","2":"I2C1_SDA"})
    S.place("XRIM:R","R","R39","4.7k",352,50,{"1":"+3V3","2":"I2C1_SCL"})
    for i,(r,v) in enumerate([("C60","100nF"),("C61","2.2uF"),("C62","10nF"),("C63","100nF"),("C64","100nF")]):
        S.place("XRIM:C","C",r,v,250+14*i,85,{"1":"+3V3","2":"GND"})

    S.text("INTER-BOARD: J1 JST-GH8 to CCM (UART + ARM)",220,110)
    jnets={"1":"GND","2":"UART_RX","3":"UART_TX","4":"ARM_IN","7":"GND","8":"GND"}
    ncj=("5","6") if VAR==2 else ("6",)
    if VAR==1: jnets["5"]="SPARE_IO"
    S.place("XRIM:JST_GH8","JST_GH8","J1","to CCM",250,135,jnets,nc_pins=ncj)

    if VAR==1:
        S.text("ACTUATORS: 4x fin servos — TIM1_CH1..4 on PA8..PA11 (PDR-002)",220,170)
        for i in range(4):
            S.place("XRIM:HDR3","HDR3",f"J{2+i}",f"SERVO {'NESW'[i]}",240+34*i,195,
                    {"1":f"SERVO{i+1}","2":"V_SERVO","3":"GND"})
    else:
        S.text("TVC: pitch PA0 / yaw PA1 (TIM2). SUSTAINER: ARM_IN gates PC817; PB15 sinks LED; AO3400A fires.",220,170)
        S.place("XRIM:HDR3","HDR3","J2","TVC PITCH",240,195,{"1":"TVC_PITCH","2":"V_SERVO","3":"GND"})
        S.place("XRIM:HDR3","HDR3","J3","TVC YAW",274,195,{"1":"TVC_YAW","2":"V_SERVO","3":"GND"})
        S.place("XRIM:R","R","R40","330R",240,220,{"1":"ARM_IN","2":"ARM_IN_R"})
        S.place("XRIM:PC817","PC817","U6","PC817",265,225,{str(k):v for k,v in PC817.items()})
        S.place("XRIM:R","R","R41","100k",290,220,{"1":"SUS_GATE","2":"GND"})
        S.place("XRIM:NFET","NFET","Q1","AO3400A",305,225,{"1":"SUS_GATE","3":"SUS_D","2":"GND"})
        S.place("XRIM:SCREW2","SCREW2","J6","SUSTAINER E-MATCH",330,225,{"1":"VBAT2S","2":"SUS_D"})
        S.place("XRIM:R","R","R42","100k",320,245,{"1":"SUS_D","2":"SUS_CONT"})
        S.place("XRIM:R","R","R43","27k",332,245,{"1":"SUS_CONT","2":"GND"})
        S.place("XRIM:C","C","C65","10nF",344,245,{"1":"SUS_CONT","2":"GND"})
        S.place("XRIM:HDR2","HDR2","J7","REED SW",240,245,{"1":"REED","2":"GND"})
        S.place("XRIM:R","R","R44","10k",252,255,{"1":"+3V3","2":"REED"})

    # ── PCB ──
    F=parts
    f411=F.ufqfpn48(); icm=F.lga14_icm(); bmp=F.lga10_bmp388(); ina=F.sot23_8()
    s236=F.sot23_6(); s23=F.sot23(); c06=F.c0603(); r06=F.r0603(); led=F.led0603()
    l44=F.l_4x4(); shunt=F.r2512(); cp=F.cp_radial_d63(); xt=F.xt30(); sc2=F.screw2_508()
    gh8=F.jst_gh8(); h5=F.header(5); h3=F.header(3); h2=F.header(2); xtl=F.xtal3225()
    m3=F.mount_m3(); pc8=F.pc817_dip4()
    A=brd.add_fp
    sn=lambda d:{str(k):v for k,v in d.items()}
    A(f411,"U1","STM32F411CEU6",100,97,0,sn(F4))
    A(icm,"U2","ICM-42688-P",110.0,93.2,0,sn(IMU))
    A(bmp,"U3","BMP388",112.5,101.5,0,sn(BMP))
    A(ina,"U4","INA219",109.0,116.0,0,sn(INA))
    A(s236,"U5","TPS54202",86.0,106.5,0,sn(BUCK))
    A(l44,"L2","10uH",80.6,101.8,90,{"1":"BUCK_SW","2":"+3V3"})
    A(shunt,"R20","10m 2512",101.0,121.0,0,{"1":"VBAT2S","2":"V_SERVO"})
    A(xt,"J9","XT30 2S",96.5,127.2,180,{"1":"VBAT2S","2":"GND"})
    A(gh8,"J1","to CCM",100,73.5,0,{"1":"GND","2":"UART_RX","3":"UART_TX","4":"ARM_IN",
       **({"5":"SPARE_IO"} if VAR==1 else {}),"7":"GND","8":"GND","MP1":"GND","MP2":"GND"})
    A(h5,"J10","SWD",85.5,87.5,0,{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"NRST","5":"GND"})
    A(h2,"J8","BOOT0",81.0,92.6,0,{"1":"BOOT0","2":"+3V3"})
    A(xtl,"X1","8MHz",91.5,97.0,90,{"1":"XIN","2":"GND","3":"XOUT","4":"GND"})
    A(led,"LED1","STAT",95.0,88.6,0,{"1":"GND","2":"LED_R"})
    # bulk caps
    A(cp,"C45","470uF",*((90.0,115.2,0) if VAR==1 else (92.8,115.4,0)),{"1":"V_SERVO","2":"GND"})
    A(cp,"C46","470uF",*((124.0,99.0,0) if VAR==1 else (118.0,107.5,0)),{"1":"V_SERVO","2":"GND"})
    A(cp,"C47","470uF",107.6,109.6,0,{"1":"V_SERVO","2":"GND"})
    RR=[("R30","45.3k",90.2,109.7,90,{"1":"+3V3","2":"BUCK_FB"}),
        ("R31","10k",94.2,109.7,90,{"1":"BUCK_FB","2":"GND"}),
        ("R32","100k",*((95.6,117.6,0) if VAR==1 else (106.0,120.0,90)),{"1":"VBAT2S","2":"VBAT_SENSE"}),
        ("R33","27k",*((98.6,116.6,90) if VAR==1 else (103.3,115.4,90)),{"1":"VBAT_SENSE","2":"GND"}),
        ("R34","10k",84.6,95.4,0,{"1":"BOOT0","2":"GND"}),
        ("R35","10k",100.4,86.4,90,{"1":"PB2_STRAP","2":"GND"}),
        ("R36","1k",92.0,90.6,0,{"1":"LED_STATUS","2":"LED_R"}),
        ("R37","100k",106.2,77.8,0,{"1":"ARM_IN","2":"GND"}),
        ("R38","4.7k",99.2,106.8,90,{"1":"+3V3","2":"I2C1_SDA"}),
        ("R39","4.7k",101.2,106.8,90,{"1":"+3V3","2":"I2C1_SCL"})]
    CC=[("C40","100nF",83.0,109.8,0,{"1":"BUCK_BOOT","2":"BUCK_SW"}),
        ("C41","10uF 25V",89.8,103.9,0,{"1":"VBAT2S","2":"GND"}),
        ("C42","10uF 25V",92.6,108.4,90,{"1":"VBAT2S","2":"GND"}),
        ("C43","22uF",77.6,97.4,0,{"1":"+3V3","2":"GND"}),
        ("C44","22uF",*((81.2,97.0,90) if VAR==1 else (82.0,112.0,0)),{"1":"+3V3","2":"GND"}),
        ("C50","18pF",89.4,92.4,0,{"1":"XIN","2":"GND"}),
        ("C51","18pF",91.5,101.4,0,{"1":"XOUT","2":"GND"}),
        ("C52","100nF",92.9,93.4,0,{"1":"NRST","2":"GND"}),
        ("C53","4.7uF",99.6,104.2,0,{"1":"VCAP","2":"GND"}),
        ("C54","100nF",109.0,87.0,0,{"1":"+3V3","2":"GND"}),
        ("C55","100nF",96.0,86.6,0,{"1":"+3V3","2":"GND"}),
        ("C56","100nF",100.5,90.4,0,{"1":"+3V3","2":"GND"}),
        ("C57","10uF",96.5,90.4,0,{"1":"+3V3","2":"GND"}),
        ("C58","100nF",93.8,104.6,0,{"1":"+3V3","2":"GND"}),
        ("C59","1uF",95.8,107.0,0,{"1":"+3V3","2":"GND"}),
        ("C60","100nF",113.6,87.4,0,{"1":"+3V3","2":"GND"}),
        ("C61","2.2uF",117.2,90.6,0,{"1":"+3V3","2":"GND"}),
        ("C62","10nF",115.2,98.6,90,{"1":"+3V3","2":"GND"}),
        ("C63","100nF",112.8,107.4,0,{"1":"+3V3","2":"GND"}),
        ("C64","100nF",112.8,105.6,0,{"1":"+3V3","2":"GND"})]
    if VAR==2:
        RR += [("R40","330R",103.0,79.6,0,{"1":"ARM_IN","2":"ARM_IN_R"}),
               ("R41","100k",121.2,101.8,90,{"1":"SUS_GATE","2":"GND"}),
               ("R42","100k",122.6,97.0,0,{"1":"SUS_D","2":"SUS_CONT"}),
               ("R43","27k",124.8,101.0,90,{"1":"SUS_CONT","2":"GND"}),
               ("R44","10k",84.8,97.6,0,{"1":"+3V3","2":"REED"})]
        CC += [("C65","10nF",122.8,104.4,90,{"1":"SUS_CONT","2":"GND"})]
        A(pc8,"U6","PC817",78.5,104.0,90,{"1":"ARM_IN_R","2":"SUS_FIRE","3":"SUS_GATE","4":"VBAT2S"})
        A(s23,"Q1","AO3400A",118.6,98.4,90,{"1":"SUS_GATE","3":"SUS_D","2":"GND"})
        A(sc2,"J6","SUSTAIN",123.6,91.9,289,{"1":"VBAT2S","2":"SUS_D"})
        A(h2,"J7","REED",75.5,93.5,90,{"1":"REED","2":"GND"})
    for ref,val,x,y,rot,nets in RR: A(r06,ref,val,x,y,rot,nets)
    for ref,val,x,y,rot,nets in CC: A(c06,ref,val,x,y,rot,nets)
    # servo headers on south arc
    def arc(theta,r=24.0):
        t=math.radians(theta)
        return (100+r*math.cos(t),100+r*math.sin(t)), (-(90+theta))%360
    if VAR==1:
        for i,th in enumerate([158,116,64,22]):
            (x,y),rot=arc(th)
            A(h3,f"J{2+i}",f"SRV{'NESW'[i]}",x,y,rot,{"1":f"SERVO{i+1}","2":"V_SERVO","3":"GND"})
    else:
        for i,(th,net,nm) in enumerate([(116,"TVC_PITCH","PITCH"),(64,"TVC_YAW","YAW")]):
            (x,y),rot=arc(th)
            A(h3,f"J{2+i}",nm,x,y,rot,{"1":net,"2":"V_SERVO","3":"GND"})
    for i,(mx,my) in enumerate([(81.7,81.7),(118.3,81.7),(81.7,118.3),(118.3,118.3)]):
        d=math.hypot(mx-100,my-100); s=26.0/d
        A(m3,f"H{i+1}","M3",100+(mx-100)*s,100+(my-100)*s,0,{})

    escape_stubs(brd,f411,100,97,0,sn(F4))
    escape_stubs(brd,bmp,112.5,101.5,0,sn(BMP))
    escape_stubs(brd,ina,109.0,116.0,0,sn(INA))
    escape_stubs(brd,icm,110.0,93.2,0,sn(IMU))
    widths={"+3V3":0.5,"VBAT2S":1.0,"V_SERVO":1.2,"GND":0.5,"BUCK_SW":0.6,
            "SUS_D":0.8,"SERVO1":0.25,"SERVO2":0.25,"SERVO3":0.25,"SERVO4":0.25,
            "TVC_PITCH":0.25,"TVC_YAW":0.25}
    rt=Router(brd,widths)
    order=["SERVO1","SERVO2","SERVO3","SERVO4","TVC_PITCH","TVC_YAW",
           "UART_TX","UART_RX","ARM_IN","SWDIO","SWCLK","SPARE_IO","REED",
           "SUS_GATE","SUS_FIRE","SUS_CONT","ARM_IN_R","VBAT_SENSE","LED_STATUS","LED_R",
           "SPI1_SCK","SPI1_MOSI","SPI1_MISO","IMU_CS","IMU_INT1",
           "I2C1_SCL","I2C1_SDA","BMP_INT","XIN","XOUT","NRST","VCAP",
           "BOOT0","PB2_STRAP",
           "V_SERVO","VBAT2S","SUS_D","+3V3","BUCK_SW","BUCK_BOOT","BUCK_FB"]
    allnets=set(n for n in brd.nets if n and n!="GND")
    fails=[]
    import json as _js
    PRO=os.path.join(OUT,"promote.json")
    if os.path.exists(PRO):
        try:
            pass
        except Exception: pass
    import time as _t, pickle as _pk
    _t0=_t.time()
    seq=[n for n in order if n in allnets]+sorted(allnets-set(order))
    CK=os.path.join(OUT,"route_state.pkl")
    done=[]
    if "--resume" in sys.argv and os.path.exists(CK):
        brd2,rt2,fails2,done=_pk.load(open(CK,"rb"))
        brd.__dict__.update(brd2.__dict__); rt.__dict__.update(rt2.__dict__)
        rt.b=brd; fails[:]=fails2
        print("resumed after",done[-1] if done else "?", flush=True)
    for net in seq:
        if net in done: continue
        if not rt.route_net(net,widths.get(net,0.2)): fails.append(net)
        done.append(net)
        print(f"  [{_t.time()-_t0:5.1f}s] {net}", flush=True)
        if _t.time()-_t0 > 30 and net != seq[-1]:
            _pk.dump((brd,rt,fails,done),open(CK,"wb"))
            print("CHECKPOINT — rerun with --resume", flush=True)
            sys.exit(42)
    retry=list(dict.fromkeys(fails)); fails=[]
    for net in retry:
        if not rt.route_net(net,max(0.2,widths.get(net,0.2)*0.6)): fails.append(net)
    print(f"ROUTING {NAME}: {len(fails)} failed: {fails}")
    _js.dump(fails,open(PRO,"w"))
    MR=os.path.join(os.path.dirname(__file__), f"manual_{NAME}.json")
    if os.path.exists(MR):
        for net,routes in _js.load(open(MR)).items():
            for r in routes:
                layer=r.get("layer","F.Cu"); w=r.get("w",0.25)
                pts=[tuple(p) for p in r["pts"]]
                brd.track(net,pts,layer,w)
                for v in r.get("vias",[]):
                    brd.via(net,v[0],v[1],size=0.45,drill=0.25)
            print("manual:",net,flush=True)
    nv=stitch_gnd(brd,spacing=5.5)
    print(f"stitch vias: {nv}")
    brd.gnd_zone("F.Cu"); brd.gnd_zone("B.Cu")
    import pickle
    pickle.dump((brd,sch.netlist,fails),open(os.path.join(OUT,"chk.pkl"),"wb"))
    ok = True
    if "--verify" in sys.argv:
        ok=verify(brd,sch.netlist,NAME)
    base=f"{NAME}_{'Mid_Ring' if VAR==1 else 'TVC_Sustainer'}_Controller"
    open(os.path.join(OUT,base+".kicad_sch"),"w").write(sch.emit())
    open(os.path.join(OUT,base+".kicad_pcb"),"w").write(brd.emit())
    open(os.path.join(OUT,base+".kicad_pro"),"w").write(project_file(base))
    print("WROTE",OUT,"verify_ok=",ok,"fails=",len(fails))
    return 0 if (ok and not fails) else 1

if __name__=="__main__":
    sys.exit(main())
