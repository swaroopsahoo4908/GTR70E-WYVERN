#!/usr/bin/env python3
"""XRIM-117E SDM Rev C — Solenoid Drive Module (100mm disc, finless TVC).
3x proportional solenoid channels (20kHz PWM current-mode) + sustainer interlock."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from kicadgen import *
import parts
from autoroute import Router, stitch_gnd
from verify import verify

OUT = os.path.join(os.path.dirname(__file__), '..', 'out', 'SDM_KiCAD_RevC')
os.makedirs(OUT, exist_ok=True)
R_BOARD = 50.0

# STM32F411CEU6 UFQFPN-48 — PDR-003 §3.1 allocation
F4 = {
 1:"+3V3", 2:"LED_STATUS", 3:"", 4:"", 5:"XIN", 6:"XOUT", 7:"NRST", 8:"GND",
 9:"+3V3", 10:"SOL1_SNS", 11:"SOL2_SNS", 12:"UART_TX", 13:"UART_RX",
 14:"SUS_CONT", 15:"SPI1_SCK", 16:"SPI1_MISO", 17:"SPI1_MOSI",
 18:"SOL3_SNS", 19:"VBAT_SENSE", 20:"PB2_STRAP", 21:"REED", 22:"VCAP",
 23:"GND", 24:"+3V3", 25:"IMU_CS", 26:"ARM_IN", 27:"",
 28:"SUS_FIRE", 29:"SOL1_PWM", 30:"SOL2_PWM", 31:"SOL3_PWM", 32:"",
 33:"", 34:"SWDIO", 35:"GND", 36:"+3V3", 37:"SWCLK", 38:"IMU_INT1",
 39:"", 40:"", 41:"BMP_INT", 42:"I2C1_SCL", 43:"I2C1_SDA", 44:"BOOT0",
 45:"", 46:"", 47:"GND", 48:"+3V3", 49:"GND"}
F4N = {1:"VBAT",2:"PC13",3:"PC14",4:"PC15",5:"PH0",6:"PH1",7:"NRST",8:"VSSA",
 9:"VDDA",10:"PA0_A0",11:"PA1_A1",12:"PA2_TX",13:"PA3_RX",14:"PA4_A4",15:"PA5",
 16:"PA6",17:"PA7",18:"PB0_A8",19:"PB1_A9",20:"PB2",21:"PB10",22:"VCAP1",
 23:"VSS",24:"VDD",25:"PB12",26:"PB13",27:"PB14",28:"PB15",29:"PA8_T1C1",
 30:"PA9_T1C2",31:"PA10_T1C3",32:"PA11",33:"PA12",34:"PA13",35:"VSS",36:"VDD",
 37:"PA14",38:"PA15",39:"PB3",40:"PB4",41:"PB5",42:"PB6",43:"PB7",44:"BOOT0",
 45:"PB8",46:"PB9",47:"VSS",48:"VDD",49:"EP"}
IMU = {1:"SPI1_MISO",2:"",3:"",4:"IMU_INT1",5:"+3V3",6:"GND",7:"GND",8:"+3V3",
       9:"GND",10:"",11:"",12:"IMU_CS",13:"SPI1_SCK",14:"SPI1_MOSI"}
IMU_NAMES={1:"AP_SDO",2:"RESV",3:"RESV",4:"INT1",5:"VDDIO",6:"GND",7:"RESV_GND",
           8:"VDD",9:"INT2/FSYNC",10:"RESV",11:"RESV",12:"AP_CS",13:"AP_SCLK",14:"AP_SDI"}
BMP = {1:"+3V3",2:"I2C1_SCL",3:"GND",4:"I2C1_SDA",5:"GND",6:"+3V3",7:"BMP_INT",
       8:"GND",9:"GND",10:"+3V3"}
BMP_NAMES={1:"VDDIO",2:"SCK",3:"VSS",4:"SDI",5:"SDO",6:"CSB",7:"INT",8:"VSS",9:"VSS",10:"VDD"}
INA = {1:"VBAT2S",2:"V_SOL",3:"GND",4:"+3V3",5:"I2C1_SCL",6:"I2C1_SDA",7:"GND",8:"GND"}
INA_NAMES={1:"IN+",2:"IN-",3:"GND",4:"VS",5:"SCL",6:"SDA",7:"A0",8:"A1"}
BUCK = {1:"GND",2:"BUCK_SW",3:"VBAT2S",4:"BUCK_FB",5:"",6:"BUCK_BOOT"}
BUCK_NAMES={1:"GND",2:"SW",3:"VIN",4:"FB",5:"EN",6:"BOOT"}
PC817 = {1:"ARM_IN_R",2:"SUS_FIRE",3:"SUS_GATE",4:"VBAT2S"}
PC817_NAMES={1:"A",2:"K",3:"E",4:"C"}

def main():
    sch = Schematic("XRIM-117E SDM - Solenoid Drive Module",
        "Skylight Industries LLC / Legacy Systems Research Group",
        ["PDR-003 Rev C | finless airframe - 3x proportional solenoid TVC (LSRG-S25)",
         "20kHz PWM current-mode: TIM1 CH1-3 -> AO3400A + SS34 freewheel + 20m shunt -> ADC",
         "Replaces ASAM-1 + ASAM-2. Sustainer two-board interlock retained. 100mm disc."])
    brd = Board("XRIM-117E SDM Rev C", radius=R_BOARD)

    def boxsym(name, ref, val, fpname, pinmap, names, w=18.0):
        items=sorted(pinmap.keys()); half=(len(items)+1)//2
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
                         ("LED","LED","LED_0603"),("RS","R","R_2512_Shunt"),("D","D","D_SMA")]:
        sch.add_lib_symbol(make_2pin_symbol("XRIM",nm,"R" if nm in("R","RS") else {"C":"C","CP":"C","L":"L","LED":"D","D":"D"}[nm],
                           nm,"XRIM:"+fpn,glyph), nm, Schematic.TWO_PIN)
    sch.add_lib_symbol(make_mosfet_symbol("XRIM","NFET","AO3400A","XRIM:SOT-23"),"NFET",Schematic.FET_PIN)
    for n in ["GND","+3V3","VBAT2S","V_SOL"]:
        sch.add_lib_symbol(make_power_symbol(n), "power:"+n, [])
    sch.lib_symbols.append(PWR_FLAG)
    def consym(name,npins,names=None):
        L=[(names[i] if names else f"P{i+1}",str(i+1),"pas") for i in range(npins)]
        sch.add_lib_symbol(make_box_symbol("XRIM",name,"J",name,"",L,[],w=12),name,
                           Schematic.box_pins(L,[],w=12))
    consym("XT30",2,["VBAT+","GND"]); consym("SCREW2",2,["V_SOL","COIL"])
    consym("JST_GH8",8); consym("HDR5",5,["3V3","SWDIO","SWCLK","RST","GND"])
    consym("HDR2",2,["A","B"])
    XL=[("IN","1","pas"),("GND","2","pwr")]; XR=[("OUT","3","pas"),("GND","4","pwr")]
    sch.add_lib_symbol(make_box_symbol("XRIM","XTAL4","Y","8MHz","XRIM:Crystal_3225_4Pin",XL,XR,w=10),
                       "XTAL4",Schematic.box_pins(XL,XR,w=10))

    S=sch
    S.text("POWER: 2S LiPo -> INA219 10m shunt -> V_SOL (3x coils, 6A pk) ; TPS54202 -> 3.3V",20,30)
    S.place("XRIM:XT30","XT30","J9","XT30 2S",35,45,{"1":"VBAT2S","2":"GND"})
    S.place("XRIM:RS","RS","R20","10m 1% 2512",60,40,{"1":"VBAT2S","2":"V_SOL"})
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
        S.place("XRIM:CP","CP",f"C{45+i}","470uF 16V",70+14*i,85,{"1":"V_SOL","2":"GND"})
    for net,x in [("VBAT2S",35),("V_SOL",60),("+3V3",130),("GND",90)]:
        S.power_flag(net,x,98)

    S.text("SOLENOID TVC x3: V_SOL -> coil -> AO3400A low-side @20kHz ; SS34 freewheel ; 20m shunt -> ADC",20,115)
    for ch in range(3):
        y=135+ch*30
        S.place("XRIM:SCREW2","SCREW2",f"J{2+ch}",f"SOL{ch+1} (LSRG-S25)",30,y,
                {"1":"V_SOL","2":f"SOL{ch+1}_D"})
        S.place("XRIM:D","D",f"D{1+ch}","SS34 freewheel",55,y-5,{"1":f"SOL{ch+1}_D","2":"V_SOL"})
        S.place("XRIM:NFET","NFET",f"Q{1+ch}","AO3400A",75,y,
                {"1":f"SOL{ch+1}_G","3":f"SOL{ch+1}_D","2":f"SOL{ch+1}_SH"})
        S.place("XRIM:R","R",f"R{1+ch*4}","100R",95,y-8,{"1":f"SOL{ch+1}_PWM","2":f"SOL{ch+1}_G"})
        S.place("XRIM:R","R",f"R{2+ch*4}","100k",107,y-8,{"1":f"SOL{ch+1}_G","2":"GND"})
        S.place("XRIM:RS","RS",f"R{3+ch*4}","20m 1% 2512",95,y+6,{"1":f"SOL{ch+1}_SH","2":"GND"})
        S.place("XRIM:R","R",f"R{4+ch*4}","1k",119,y-8,{"1":f"SOL{ch+1}_SH","2":f"SOL{ch+1}_SNS"})
        S.place("XRIM:C","C",f"C{50+ch}","100nF",131,y-8,{"1":f"SOL{ch+1}_SNS","2":"GND"})

    S.text("MCU: STM32F411 + 8MHz HSE + SWD + BOOT0 ; UART to CCM ; ARM interlock",20,235)
    S.place("XRIM:F411","F411","U1","STM32F411CEU6",70,300,{str(k):v for k,v in F4.items()},
            nc_pins=tuple(str(k) for k,v in F4.items() if v==""))
    S.place("XRIM:XTAL4","XTAL4","X1","8MHz CL=12p",130,260,{"1":"XIN","2":"GND","3":"XOUT","4":"GND"})
    S.place("XRIM:C","C","C52","18pF",145,260,{"1":"XIN","2":"GND"})
    S.place("XRIM:C","C","C53","18pF",155,260,{"1":"XOUT","2":"GND"})
    S.place("XRIM:C","C","C54","100nF",130,275,{"1":"NRST","2":"GND"})
    S.place("XRIM:C","C","C55","4.7uF",140,275,{"1":"VCAP","2":"GND"})
    S.place("XRIM:R","R","R34","10k",150,275,{"1":"BOOT0","2":"GND"})
    S.place("XRIM:HDR2","HDR2","J8","BOOT0",165,275,{"1":"BOOT0","2":"+3V3"})
    S.place("XRIM:R","R","R35","10k",150,288,{"1":"PB2_STRAP","2":"GND"})
    S.place("XRIM:HDR5","HDR5","J10","SWD",165,300,{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"NRST","5":"GND"})
    S.place("XRIM:LED","LED","LED1","STATUS",130,288,{"2":"LED_R","1":"GND"})
    S.place("XRIM:R","R","R36","1k",120,288,{"1":"LED_STATUS","2":"LED_R"})
    S.place("XRIM:R","R","R37","100k",130,316,{"1":"ARM_IN","2":"GND"})
    for i,(r,v,net) in enumerate([("C56","100nF","+3V3"),("C57","100nF","+3V3"),
        ("C58","100nF","+3V3"),("C59","10uF","+3V3"),("C60","100nF","+3V3"),("C61","1uF","+3V3")]):
        S.place("XRIM:C","C",r,v,30+14*i,345,{"1":net,"2":"GND"})

    S.text("SENSORS: ICM-42688-P (SPI1, CS=PB12) + BMP388 (I2C1 0x76) + pullups",220,235)
    S.place("XRIM:ICM42688","ICM42688","U2","ICM-42688-P",250,265,{str(k):v for k,v in IMU.items()},nc_pins=("2","3","10","11"))
    S.place("XRIM:BMP388","BMP388","U3","BMP388",310,265,{str(k):v for k,v in BMP.items()})
    S.place("XRIM:R","R","R38","4.7k",340,255,{"1":"+3V3","2":"I2C1_SDA"})
    S.place("XRIM:R","R","R39","4.7k",352,255,{"1":"+3V3","2":"I2C1_SCL"})
    for i,(r,v) in enumerate([("C62","100nF"),("C63","2.2uF"),("C64","10nF"),("C65","100nF"),("C66","100nF")]):
        S.place("XRIM:C","C",r,v,250+14*i,290,{"1":"+3V3","2":"GND"})

    S.text("SUSTAINER (interlocked) + REED + CCM LINK",220,310)
    S.place("XRIM:JST_GH8","JST_GH8","J1","to CCM",250,330,
            {"1":"GND","2":"UART_RX","3":"UART_TX","4":"ARM_IN","7":"GND","8":"GND"},nc_pins=("5","6"))
    S.place("XRIM:R","R","R40","330R",240,355,{"1":"ARM_IN","2":"ARM_IN_R"})
    S.place("XRIM:PC817","PC817","U6","PC817",265,360,{str(k):v for k,v in PC817.items()})
    S.place("XRIM:R","R","R41","100k",290,355,{"1":"SUS_GATE","2":"GND"})
    S.place("XRIM:NFET","NFET","Q4","AO3400A",305,360,{"1":"SUS_GATE","3":"SUS_D","2":"GND"})
    S.place("XRIM:SCREW2","SCREW2","J6","SUSTAINER",330,360,{"1":"VBAT2S","2":"SUS_D"})
    S.place("XRIM:R","R","R42","100k",320,380,{"1":"SUS_D","2":"SUS_CONT"})
    S.place("XRIM:R","R","R43","27k",332,380,{"1":"SUS_CONT","2":"GND"})
    S.place("XRIM:C","C","C67","10nF",344,380,{"1":"SUS_CONT","2":"GND"})
    S.place("XRIM:HDR2","HDR2","J7","REED",240,380,{"1":"REED","2":"GND"})
    S.place("XRIM:R","R","R44","10k",252,390,{"1":"+3V3","2":"REED"})

    # ── PCB (100mm disc — generous annulus for power) ──
    F=parts
    f411=F.ufqfpn48(); icm=F.lga14_icm(); bmp=F.lga10_bmp388(); ina=F.sot23_8()
    s236=F.sot23_6(); s23=F.sot23(); c06=F.c0603(); r06=F.r0603(); led=F.led0603()
    l44=F.l_4x4(); shunt=F.r2512(); cp=F.cp_radial_d63(); xt=F.xt30(); sc2=F.screw2_508()
    gh8=F.jst_gh8(); h5=F.header(5); h2=F.header(2); xtl=F.xtal3225(); m3=F.mount_m3()
    pc8=F.pc817_dip4()
    do214 = FP("D_SMA", [Pad(1,-2.0,0,1.8,1.7), Pad(2,2.0,0,1.8,1.7)], (-3.2,-1.6,3.2,1.6),
               ['(fp_line (start -3.0 -1.2) (end -3.0 1.2) (stroke (width 0.2) (type default)) (layer "F.SilkS") (uuid "TSTAMP"))'])
    A=brd.add_fp
    sn=lambda d:{str(k):v for k,v in d.items()}
    # center cluster (identical relative layout to proven ASAM core)
    A(f411,"U1","STM32F411CEU6",100,97,0,sn(F4))
    A(icm,"U2","ICM-42688-P",110.0,93.2,0,sn(IMU))
    A(bmp,"U3","BMP388",112.5,101.5,0,sn(BMP))
    A(ina,"U4","INA219",109.0,116.0,0,sn(INA))
    A(s236,"U5","TPS54202",86.0,106.5,0,sn(BUCK))
    A(l44,"L2","10uH",80.6,101.8,90,{"1":"BUCK_SW","2":"+3V3"})
    A(shunt,"R20","10m 2512",101.0,121.0,0,{"1":"VBAT2S","2":"V_SOL"})
    A(xtl,"X1","8MHz",91.5,97.0,90,{"1":"XIN","2":"GND","3":"XOUT","4":"GND"})
    A(led,"LED1","STAT",95.0,88.6,0,{"1":"GND","2":"LED_R"})
    A(h5,"J10","SWD",85.5,87.5,0,{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"NRST","5":"GND"})
    A(h2,"J8","BOOT0",81.0,92.6,0,{"1":"BOOT0","2":"+3V3"})
    A(h2,"J7","REED",75.5,93.5,90,{"1":"REED","2":"GND"})
    A(pc8,"U6","PC817",78.5,104.0,90,{"1":"ARM_IN_R","2":"SUS_FIRE","3":"SUS_GATE","4":"VBAT2S"})
    # big-ring items (annulus r 34..46)
    A(xt,"J9","XT30 2S",100,141.0,180,{"1":"VBAT2S","2":"GND"})
    A(gh8,"J1","to CCM",100,59.5,0,{"1":"GND","2":"UART_RX","3":"UART_TX","4":"ARM_IN","7":"GND","8":"GND","MP1":"GND","MP2":"GND"})
    # 3 solenoid channels at 120 deg (90deg=down, 210, 330)
    for ch,th in enumerate([90,210,330]):
        t=math.radians(th)
        jx,jy=100+42*math.cos(t),100+42*math.sin(t)
        rot=(-(90+th))%360
        A(sc2,f"J{2+ch}",f"SOL{ch+1}",jx,jy,rot,{"1":"V_SOL","2":f"SOL{ch+1}_D"})
        qx,qy=100+33*math.cos(t),100+33*math.sin(t)
        A(s23,f"Q{1+ch}","AO3400A",qx,qy,rot,{"1":f"SOL{ch+1}_G","3":f"SOL{ch+1}_D","2":f"SOL{ch+1}_SH"})
        dx,dy=100+37.5*math.cos(t)+6*math.cos(t+math.pi/2),100+37.5*math.sin(t)+6*math.sin(t+math.pi/2)
        A(do214,f"D{1+ch}","SS34",dx,dy,rot,{"1":f"SOL{ch+1}_D","2":"V_SOL"})
        sx,sy=100+28*math.cos(t),100+28*math.sin(t)
        A(shunt,f"RS{1+ch}","20m 2512",sx,sy,rot,{"1":f"SOL{ch+1}_SH","2":"GND"})
        g1x,g1y=100+33*math.cos(t)+5.5*math.cos(t+math.pi/2),100+33*math.sin(t)+5.5*math.sin(t+math.pi/2)
        A(r06,f"R{1+ch*4}","100R",g1x,g1y,rot,{"1":f"SOL{ch+1}_PWM","2":f"SOL{ch+1}_G"})
        g2x,g2y=100+33*math.cos(t)+9.0*math.cos(t+math.pi/2),100+33*math.sin(t)+9.0*math.sin(t+math.pi/2)
        A(r06,f"R{2+ch*4}","100k",g2x,g2y,rot,{"1":f"SOL{ch+1}_G","2":"GND"})
        f1x,f1y=100+24*math.cos(t)+4*math.cos(t+math.pi/2),100+24*math.sin(t)+4*math.sin(t+math.pi/2)
        A(r06,f"R{3+ch*4}","1k",f1x,f1y,rot,{"1":f"SOL{ch+1}_SH","2":f"SOL{ch+1}_SNS"})
        f2x,f2y=100+24*math.cos(t)+7.5*math.cos(t+math.pi/2),100+24*math.sin(t)+7.5*math.sin(t+math.pi/2)
        A(c06,f"C{50+ch}","100nF",f2x,f2y,rot,{"1":f"SOL{ch+1}_SNS","2":"GND"})
    # sustainer terminal NE
    A(sc2,"J6","SUSTAIN",100+42*math.cos(math.radians(20)),100+42*math.sin(math.radians(20)),
      (-(110))%360,{"1":"VBAT2S","2":"SUS_D"})
    A(s23,"Q4","AO3400A",128.5,105.5,90,{"1":"SUS_GATE","3":"SUS_D","2":"GND"})
    # bulk caps in the annulus
    A(cp,"C45","470uF",78.0,124.0,0,{"1":"V_SOL","2":"GND"})
    A(cp,"C46","470uF",122.0,124.0,0,{"1":"V_SOL","2":"GND"})
    A(cp,"C47","470uF",128.0,89.0,0,{"1":"V_SOL","2":"GND"})
    RR=[("R30","45.3k",90.2,109.7,90,{"1":"+3V3","2":"BUCK_FB"}),
        ("R31","10k",94.2,109.7,90,{"1":"BUCK_FB","2":"GND"}),
        ("R32","100k",106.0,120.0,90,{"1":"VBAT2S","2":"VBAT_SENSE"}),
        ("R33","27k",103.3,115.4,90,{"1":"VBAT_SENSE","2":"GND"}),
        ("R34","10k",84.6,95.4,0,{"1":"BOOT0","2":"GND"}),
        ("R35","10k",100.4,86.4,90,{"1":"PB2_STRAP","2":"GND"}),
        ("R36","1k",92.0,90.6,0,{"1":"LED_STATUS","2":"LED_R"}),
        ("R37","100k",106.2,77.8,0,{"1":"ARM_IN","2":"GND"}),
        ("R38","4.7k",99.2,106.8,90,{"1":"+3V3","2":"I2C1_SDA"}),
        ("R39","4.7k",101.2,106.8,90,{"1":"+3V3","2":"I2C1_SCL"}),
        ("R40","330R",91.0,73.0,0,{"1":"ARM_IN","2":"ARM_IN_R"}),
        ("R41","100k",84.0,113.6,90,{"1":"SUS_GATE","2":"GND"}),
        ("R42","100k",131.0,99.0,90,{"1":"SUS_D","2":"SUS_CONT"}),
        ("R43","27k",133.5,103.0,90,{"1":"SUS_CONT","2":"GND"}),
        ("R44","10k",78.8,96.0,0,{"1":"+3V3","2":"REED"})]
    CC=[("C40","100nF",83.0,109.8,0,{"1":"BUCK_BOOT","2":"BUCK_SW"}),
        ("C41","10uF 25V",89.8,103.9,0,{"1":"VBAT2S","2":"GND"}),
        ("C42","10uF 25V",92.6,108.4,90,{"1":"VBAT2S","2":"GND"}),
        ("C43","22uF",77.6,97.4,0,{"1":"+3V3","2":"GND"}),
        ("C44","22uF",81.2,97.0,90,{"1":"+3V3","2":"GND"}),
        ("C52","18pF",89.4,92.4,0,{"1":"XIN","2":"GND"}),
        ("C53","18pF",91.5,101.4,0,{"1":"XOUT","2":"GND"}),
        ("C54","100nF",94.8,93.6,0,{"1":"NRST","2":"GND"}),
        ("C55","4.7uF",99.6,104.2,0,{"1":"VCAP","2":"GND"}),
        ("C56","100nF",106.2,93.0,0,{"1":"+3V3","2":"GND"}),
        ("C57","100nF",105.6,102.6,0,{"1":"+3V3","2":"GND"}),
        ("C58","100nF",100.5,90.4,0,{"1":"+3V3","2":"GND"}),
        ("C59","10uF",96.5,90.4,0,{"1":"+3V3","2":"GND"}),
        ("C60","100nF",93.8,104.6,0,{"1":"+3V3","2":"GND"}),
        ("C61","1uF",95.8,107.0,0,{"1":"+3V3","2":"GND"}),
        ("C62","100nF",113.6,87.4,0,{"1":"+3V3","2":"GND"}),
        ("C63","2.2uF",117.2,90.6,0,{"1":"+3V3","2":"GND"}),
        ("C64","10nF",115.2,98.6,90,{"1":"+3V3","2":"GND"}),
        ("C65","100nF",112.8,105.6,0,{"1":"+3V3","2":"GND"}),
        ("C66","100nF",112.8,107.4,0,{"1":"+3V3","2":"GND"}),
        ("C67","10nF",136.0,101.0,90,{"1":"SUS_CONT","2":"GND"})]
    for ref,val,x,y,rot,nets in RR: A(r06,ref,val,x,y,rot,nets)
    for ref,val,x,y,rot,nets in CC: A(c06,ref,val,x,y,rot,nets)
    for i,(mx,my) in enumerate([(100-31.1,100-31.1),(100+31.1,100-31.1),(100-31.1,100+31.1),(100+31.1,100+31.1)]):
        A(m3,f"H{i+1}","M3",mx,my,0,{})

    escape_stubs(brd,f411,100,97,0,sn(F4))
    escape_stubs(brd,bmp,112.5,101.5,0,sn(BMP))
    escape_stubs(brd,ina,109.0,116.0,0,sn(INA))
    escape_stubs(brd,icm,110.0,93.2,0,sn(IMU))

    widths={"+3V3":0.5,"VBAT2S":1.5,"V_SOL":1.8,"GND":0.5,"BUCK_SW":0.6,
            "SOL1_D":1.2,"SOL2_D":1.2,"SOL3_D":1.2,"SUS_D":0.8,
            "SOL1_SH":1.0,"SOL2_SH":1.0,"SOL3_SH":1.0}
    rt=Router(brd,widths)
    order=["SOL1_PWM","SOL2_PWM","SOL3_PWM","SOL1_SNS","SOL2_SNS","SOL3_SNS",
           "UART_TX","UART_RX","ARM_IN","SWDIO","SWCLK","REED",
           "SUS_GATE","SUS_FIRE","SUS_CONT","ARM_IN_R","VBAT_SENSE","LED_STATUS","LED_R",
           "SPI1_SCK","SPI1_MOSI","SPI1_MISO","IMU_CS","IMU_INT1",
           "I2C1_SCL","I2C1_SDA","BMP_INT","XIN","XOUT","NRST","VCAP","BOOT0","PB2_STRAP",
           "SOL1_G","SOL2_G","SOL3_G","SOL1_SH","SOL2_SH","SOL3_SH",
           "SOL1_D","SOL2_D","SOL3_D","V_SOL","VBAT2S","SUS_D",
           "+3V3","BUCK_SW","BUCK_BOOT","BUCK_FB"]
    allnets=set(n for n in brd.nets if n and n!="GND")
    fails=[]
    import time as _t, pickle as _pk
    _t0=_t.time()
    seq=[n for n in order if n in allnets]+sorted(allnets-set(order))
    CK=os.path.join(OUT,"route_state.pkl")
    done=[]
    if "--resume" in sys.argv and os.path.exists(CK):
        brd2,rt2,fails2,done=_pk.load(open(CK,"rb"))
        brd.__dict__.update(brd2.__dict__); rt.__dict__.update(rt2.__dict__)
        rt.b=brd; fails=fails2
        print("resumed",flush=True)
    for net in seq:
        if "--finish" in sys.argv:
            fails=sorted(set(fails)|set(n for n in seq if n not in done)); break
        if net in done: continue
        if not rt.route_net(net,widths.get(net,0.2)): fails.append(net)
        done.append(net)
        if _t.time()-_t0 > 26 and net != seq[-1]:
            _pk.dump((brd,rt,fails,done),open(CK,"wb"))
            print("CHECKPOINT",flush=True); sys.exit(42)
    retry=[] if "--finish" in sys.argv else list(dict.fromkeys(fails))
    if retry: fails=[]
    for net in retry:
        if not rt.route_net(net,max(0.2,widths.get(net,0.2)*0.6)): fails.append(net)
    print(f"ROUTING SDM: {len(fails)} failed: {fails}",flush=True)
    nv=stitch_gnd(brd,spacing=7.0)
    print(f"stitch vias: {nv}",flush=True)
    brd.gnd_zone("F.Cu"); brd.gnd_zone("B.Cu")
    _pk.dump((brd,sch.netlist,fails),open(os.path.join(OUT,"chk.pkl"),"wb"))
    ok=True
    if "--verify" in sys.argv: ok=verify(brd,sch.netlist,"SDM")
    base="SDM_Solenoid_Drive_Module"
    open(os.path.join(OUT,base+".kicad_sch"),"w").write(sch.emit())
    open(os.path.join(OUT,base+".kicad_pcb"),"w").write(brd.emit())
    open(os.path.join(OUT,base+".kicad_pro"),"w").write(project_file(base))
    print("WROTE",OUT,"fails=",len(fails))
    return 0 if not fails else 1

if __name__=="__main__":
    sys.exit(main())
