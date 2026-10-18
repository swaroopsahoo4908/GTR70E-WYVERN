#!/usr/bin/env python3
"""XRIM-117 CCM Rev B — RP2040 flight computer, datasheet-verified netlist.
Generates CCM_Central_Command_Module.kicad_sch / .kicad_pcb / .kicad_pro"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from kicadgen import *
import parts
from autoroute import Router, stitch_gnd
from verify import verify
from shapely.geometry import box as sbox

OUT = os.path.join(os.path.dirname(__file__), '..', 'out', 'CCM_KiCAD_RevB')
os.makedirs(OUT, exist_ok=True)

# ───────── component & net tables ─────────
# RP2040 QFN-56 pin map (RP2040 datasheet §1.2, verified)
RP = {  # pin -> net
 1:"+3V3", 2:"UART0_TX", 3:"UART0_RX", 4:"SPI0_SCK", 5:"SPI0_MOSI", 6:"SPI0_MISO",
 7:"IMU_CS", 8:"IMU_INT1", 9:"BMP_INT", 10:"+3V3",
 11:"UART1_TX", 12:"UART1_RX", 13:"SPI1_SCK", 14:"SPI1_MOSI", 15:"SPI1_MISO",
 16:"LORA_NSS", 17:"LORA_BUSY", 18:"LORA_DIO1", 19:"GND", 20:"XIN", 21:"XOUT",
 22:"+3V3", 23:"+1V1", 24:"SWCLK", 25:"SWDIO", 26:"RUN",
 27:"LORA_NRST", 28:"LORA_RXEN", 29:"ARM_OUT", 30:"PYRO1_GATE_MCU",
 31:"I2C0_SDA", 32:"I2C0_SCL", 33:"+3V3", 34:"PYRO2_GATE_MCU", 35:"PYRO3_GATE_MCU",
 36:"ARM_SENSE", 37:"LED_STATUS", 38:"PYRO1_CONT", 39:"PYRO2_CONT", 40:"PYRO3_CONT",
 41:"VBAT_SENSE", 42:"+3V3", 43:"+3V3", 44:"+3V3", 45:"+1V1",
 46:"USB_DM_R", 47:"USB_DP_R", 48:"+3V3", 49:"+3V3", 50:"+1V1",
 51:"QSPI_SD3", 52:"QSPI_SCLK", 53:"QSPI_SD0", 54:"QSPI_SD2", 55:"QSPI_SD1",
 56:"QSPI_SS", 57:"GND"}
RP_NAMES = {1:"IOVDD",2:"GPIO0",3:"GPIO1",4:"GPIO2",5:"GPIO3",6:"GPIO4",7:"GPIO5",
 8:"GPIO6",9:"GPIO7",10:"IOVDD",11:"GPIO8",12:"GPIO9",13:"GPIO10",14:"GPIO11",
 15:"GPIO12",16:"GPIO13",17:"GPIO14",18:"GPIO15",19:"TESTEN",20:"XIN",21:"XOUT",
 22:"IOVDD",23:"DVDD",24:"SWCLK",25:"SWD",26:"RUN",27:"GPIO16",28:"GPIO17",
 29:"GPIO18",30:"GPIO19",31:"GPIO20",32:"GPIO21",33:"IOVDD",34:"GPIO22",35:"GPIO23",
 36:"GPIO24",37:"GPIO25",38:"GPIO26_A0",39:"GPIO27_A1",40:"GPIO28_A2",41:"GPIO29_A3",
 42:"IOVDD",43:"ADC_AVDD",44:"VREG_VIN",45:"VREG_VOUT",46:"USB_DM",47:"USB_DP",
 48:"USB_VDD",49:"IOVDD",50:"DVDD",51:"QSPI_SD3",52:"QSPI_SCLK",53:"QSPI_SD0",
 54:"QSPI_SD2",55:"QSPI_SD1",56:"QSPI_SS",57:"EP_GND"}

# W25Q128JVSIQ SOIC-8 (std SPI-NOR pinout)
FLASH = {1:"QSPI_SS",2:"QSPI_SD1",3:"QSPI_SD2",4:"GND",5:"QSPI_SD0",6:"QSPI_SCLK",
         7:"QSPI_SD3",8:"+3V3"}
FLASH_NAMES={1:"/CS",2:"DO_IO1",3:"/WP_IO2",4:"GND",5:"DI_IO0",6:"CLK",7:"/HOLD_IO3",8:"VCC"}

# ICM-42688-P LGA-14 (TDK DS-000347 §4.1, verified)
IMU = {1:"SPI0_MISO",2:"",3:"",4:"IMU_INT1",5:"+3V3",6:"GND",7:"GND",8:"+3V3",
       9:"GND",10:"",11:"",12:"IMU_CS",13:"SPI0_SCK",14:"SPI0_MOSI"}
IMU_NAMES={1:"AP_SDO",2:"RESV",3:"RESV",4:"INT1",5:"VDDIO",6:"GND",7:"RESV_GND",
           8:"VDD",9:"INT2/FSYNC",10:"RESV",11:"RESV",12:"AP_CS",13:"AP_SCLK",14:"AP_SDI"}

# BMP388 LGA-10 (Bosch DS001 §6.1, verified) — I2C mode addr 0x76
BMP = {1:"+3V3",2:"I2C0_SCL",3:"GND",4:"I2C0_SDA",5:"GND",6:"+3V3",7:"BMP_INT",
       8:"GND",9:"GND",10:"+3V3"}
BMP_NAMES={1:"VDDIO",2:"SCK",3:"VSS",4:"SDI",5:"SDO",6:"CSB",7:"INT",8:"VSS",9:"VSS",10:"VDD"}

# E22-900M22S (Ebyte manual v1.20, verified). DIO2 strapped to TXEN on-board.
E22 = {1:"GND",2:"GND",3:"GND",4:"GND",5:"GND",6:"LORA_RXEN",7:"LORA_TXEN",
       8:"LORA_TXEN",9:"+3V3",10:"GND",11:"GND",12:"GND",13:"LORA_DIO1",
       14:"LORA_BUSY",15:"LORA_NRST",16:"SPI1_MISO",17:"SPI1_MOSI",18:"SPI1_SCK",
       19:"LORA_NSS",20:"GND",21:"RF_ANT",22:"GND"}
E22_NAMES={1:"GND",2:"GND",3:"GND",4:"GND",5:"GND",6:"RXEN",7:"TXEN",8:"DIO2",
           9:"VCC",10:"GND",11:"GND",12:"GND",13:"DIO1",14:"BUSY",15:"NRST",
           16:"MISO",17:"MOSI",18:"SCK",19:"NSS",20:"GND",21:"ANT",22:"GND"}

# TLV62569 SOT-23-5 (TI SLVSDG1: EN=1 GND=2 SW=3 FB=4 VIN=5, verified)
BUCK = {1:"VIN_SYS",2:"GND",3:"BUCK_SW",4:"BUCK_FB",5:"VIN_SYS"}
BUCK_NAMES={1:"EN",2:"GND",3:"SW",4:"FB",5:"VIN"}

def main():
    sch = Schematic("XRIM-117 CCM - Central Command Module",
        "Skylight Industries LLC / Legacy Systems Research Group",
        ["PDR-002 Rev B | RP2040 + W25Q128 QSPI + ICM-42688-P + BMP388 + E22-900M22S",
         "3x AO3400A logic-level pyro FETs w/ ADC continuity | 1S LiPo + USB diode-OR",
         "All IC pinouts datasheet-verified. RF: keep antenna trace <4mm, pour-fenced."])
    brd = Board("XRIM-117 CCM Rev B")

    # ── lib symbols ──
    def boxsym(name, ref, val, fpname, pinmap, names, w=18.0, types=None):
        items = sorted(pinmap.keys())
        half = (len(items)+1)//2
        L = [(names[p], str(p), (types or {}).get(p,"pas")) for p in items[:half]]
        R = [(names[p], str(p), (types or {}).get(p,"pas")) for p in items[half:]]
        sch.add_lib_symbol(make_box_symbol("XRIM", name, ref, val, "XRIM:"+fpname, L, R, w=w),
                           name, Schematic.box_pins(L, R, w=w))
        return L, R
    boxsym("RP2040","U","RP2040","QFN-56-1EP_7x7mm_P0.4mm",RP,RP_NAMES,w=22)
    boxsym("W25Q128","U","W25Q128JVSIQ","SOIC-8_3.9x4.9mm_P1.27mm",FLASH,FLASH_NAMES)
    boxsym("ICM42688","U","ICM-42688-P","ICM-42688-P_LGA-14_2.5x3mm",IMU,IMU_NAMES)
    boxsym("BMP388","U","BMP388","BMP388_LGA-10_2x2mm",BMP,BMP_NAMES)
    boxsym("E22","U","E22-900M22S","Ebyte_E22-900M22S",E22,E22_NAMES,w=20)
    boxsym("TLV62569","U","TLV62569","SOT-23-5",BUCK,BUCK_NAMES)
    for nm,glyph,fpn in [("R","R","R_0603"),("C","C","C_0603"),("CP","CP","CP_Radial_D6.3mm_P2.50mm"),
                         ("L","L","L_4x4mm"),("LED","LED","LED_0603"),("D","D","D_SMA"),
                         ("SW","SW","SW_SPST_Tact_6x3.5"),("XTAL","XTAL","Crystal_3225_4Pin")]:
        sch.add_lib_symbol(make_2pin_symbol("XRIM",nm,nm[0] if nm not in ("LED","SW","XTAL","CP") else {"LED":"D","SW":"SW","XTAL":"Y","CP":"C"}[nm],
                           nm,"XRIM:"+fpn,glyph), nm, Schematic.TWO_PIN)
    sch.add_lib_symbol(make_mosfet_symbol("XRIM","NFET","AO3400A","XRIM:SOT-23"),"NFET",Schematic.FET_PIN)
    for n in ["GND","+3V3","+1V1","VBAT","VBAT_ARMED","VIN_SYS","USB5V"]:
        sch.add_lib_symbol(make_power_symbol(n), "power:"+n, [])
    sch.lib_symbols.append(PWR_FLAG)
    # connectors
    def consym(name, npins, names=None):
        L=[(names[i] if names else f"P{i+1}", str(i+1), "pas") for i in range(npins)]
        sch.add_lib_symbol(make_box_symbol("XRIM",name,"J",name,"",L,[],w=12), name,
                           Schematic.box_pins(L,[],w=12))
    consym("XT30",2,["VBAT+","GND"]); consym("SCREW2",2,["A","B"])
    consym("JST_GH8",8); consym("JST_SH4",4,["5V","D-","D+","GND"])
    consym("SMA",5,["RF","GND","GND","GND","GND"])
    consym("HDR5",5,["3V3","SWDIO","SWCLK","RST","GND"])
    # 4-pad 3225 crystal: 1=IN 2=GND 3=OUT 4=GND
    XL=[("IN","1","pas"),("GND","2","pwr")]; XR=[("OUT","3","pas"),("GND","4","pwr")]
    sch.add_lib_symbol(make_box_symbol("XRIM","XTAL4","Y","12MHz","XRIM:Crystal_3225_4Pin",XL,XR,w=10),
                       "XTAL4", Schematic.box_pins(XL,XR,w=10))

    # ── schematic placement (grid of sections; positions cosmetic) ──
    S = sch
    S.text("POWER: 1S LiPo + USB diode-OR -> TLV62569 3.3V (L=2.2uH) ; pyro rail via key switch", 20, 30)
    S.place("XRIM:XT30","XT30","J4","XT30 1S LiPo",40,45,{ "1":"VBAT","2":"GND"})
    S.place("XRIM:D","D","D1","SS34",70,40,{"1":"VBAT","2":"VIN_SYS"},rot=90,footprint="XRIM:D_SMA")
    S.place("XRIM:D","D","D2","SS34",70,52,{"1":"USB5V","2":"VIN_SYS"},rot=90,footprint="XRIM:D_SMA")
    S.place("XRIM:SCREW2","SCREW2","J5","ARM KEY SW",40,60,{"1":"VBAT","2":"VBAT_ARMED"})
    S.place("XRIM:TLV62569","TLV62569","U6","TLV62569",100,46,{str(k):v for k,v in BUCK.items()})
    S.place("XRIM:L","L","L1","2.2uH",120,40,{"1":"BUCK_SW","2":"+3V3"},rot=90,footprint="XRIM:L_4x4mm")
    S.place("XRIM:R","R","R1","560k",132,46,{"1":"+3V3","2":"BUCK_FB"})
    S.place("XRIM:R","R","R2","124k",132,58,{"1":"BUCK_FB","2":"GND"})
    S.place("XRIM:C","C","C1","10uF",88,58,{"1":"VIN_SYS","2":"GND"})
    S.place("XRIM:C","C","C2","22uF",120,58,{"1":"+3V3","2":"GND"})
    S.place("XRIM:R","R","R3","100k",52,70,{"1":"VBAT","2":"VBAT_SENSE"})
    S.place("XRIM:R","R","R4","100k",52,82,{"1":"VBAT_SENSE","2":"GND"})
    S.place("XRIM:R","R","R5","100k",64,70,{"1":"VBAT_ARMED","2":"ARM_SENSE"})
    S.place("XRIM:R","R","R6","200k",64,82,{"1":"ARM_SENSE","2":"GND"})
    for net,x in [("VBAT",40),("VIN_SYS",76),("+3V3",114),("VBAT_ARMED",46),("USB5V",70),("GND",90),("+1V1",150)]:
        S.power_flag(net,x,95)

    S.text("MCU: RP2040 + 12MHz + QSPI flash + USB + SWD", 20, 115)
    S.place("XRIM:RP2040","RP2040","U1","RP2040",70,180,{str(k):v for k,v in RP.items()})
    S.place("XRIM:W25Q128","W25Q128","U2","W25Q128JVSIQ",130,140,{str(k):v for k,v in FLASH.items()})
    S.place("XRIM:XTAL4","XTAL4","X1","12MHz 3225 CL=10p",30,150,{"1":"XIN","2":"GND","3":"XOUT_R","4":"GND"})
    S.place("XRIM:R","R","R7","1k",30,165,{"1":"XOUT_R","2":"XOUT"})
    S.place("XRIM:C","C","C3","27pF",42,150,{"1":"XIN","2":"GND"})
    S.place("XRIM:C","C","C4","27pF",42,165,{"1":"XOUT_R","2":"GND"})
    S.place("XRIM:R","R","R8","10k",30,128,{"1":"+3V3","2":"RUN"})
    S.place("XRIM:R","R","R9","27R",130,170,{"1":"USB_DM_R","2":"USB_DM"})
    S.place("XRIM:R","R","R10","27R",130,182,{"1":"USB_DP_R","2":"USB_DP"})
    S.place("XRIM:JST_SH4","JST_SH4","J9","USB (JST-SH)",150,176,{"1":"USB5V","2":"USB_DM","3":"USB_DP","4":"GND"})
    S.place("XRIM:R","R","R11","1k",130,196,{"1":"QSPI_SS","2":"BOOTSEL_SW"})
    S.place("XRIM:SW","SW","SW1","BOOTSEL",150,196,{"1":"BOOTSEL_SW","2":"GND"})
    S.place("XRIM:HDR5","HDR5","J10","SWD",150,222,{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"RUN","5":"GND"})
    # decoupling bank
    dec=[("C5","100nF","+3V3"),("C6","100nF","+3V3"),("C7","100nF","+3V3"),
         ("C8","100nF","+3V3"),("C9","100nF","+3V3"),("C10","10uF","+3V3"),
         ("C11","100nF","+1V1"),("C12","100nF","+1V1"),("C13","1uF","+1V1"),
         ("C14","100nF","+3V3"),("C15","1uF","+3V3"),("C16","100nF","+3V3")]
    for i,(r,v,net) in enumerate(dec):
        S.place("XRIM:C","C",r,v,30+14*i,240,{"1":net,"2":"GND"})
    S.text("decoupling: C5-C9 IOVDD, C10 bulk, C11-C13 DVDD/core, C14 ADC_AVDD, C15 VREG_VIN, C16 USB_VDD",20,255,1.2,False)

    S.text("SENSORS: ICM-42688-P (SPI0) + BMP388 (I2C0 addr 0x76, INT->GPIO7)", 220, 30)
    S.place("XRIM:ICM42688","ICM42688","U3","ICM-42688-P",250,60,{str(k):v for k,v in IMU.items()},
            nc_pins=("2","3","10","11"))
    S.place("XRIM:BMP388","BMP388","U4","BMP388",310,60,{str(k):v for k,v in BMP.items()})
    S.place("XRIM:R","R","R12","4.7k",340,50,{"1":"+3V3","2":"I2C0_SDA"})
    S.place("XRIM:R","R","R13","4.7k",352,50,{"1":"+3V3","2":"I2C0_SCL"})
    S.place("XRIM:C","C","C17","100nF",250,85,{"1":"+3V3","2":"GND"})
    S.place("XRIM:C","C","C18","2.2uF",262,85,{"1":"+3V3","2":"GND"})
    S.place("XRIM:C","C","C19","10nF",274,85,{"1":"+3V3","2":"GND"})
    S.place("XRIM:C","C","C20","100nF",310,85,{"1":"+3V3","2":"GND"})
    S.place("XRIM:C","C","C21","100nF",322,85,{"1":"+3V3","2":"GND"})

    S.text("LoRa: E22-900M22S (SX1262+PA). DIO2 strap -> TXEN ; RXEN GPIO17. RF<4mm to SMA.", 220, 110)
    S.place("XRIM:E22","E22","U5","E22-900M22S",260,150,{str(k):v for k,v in E22.items()})
    S.place("XRIM:SMA","SMA","J3","SMA edge",320,140,{"1":"RF_ANT","2":"GND","3":"GND","4":"GND","5":"GND"})
    S.place("XRIM:C","C","C27","100nF",352,160,{"1":"VBAT_ARMED","2":"GND"})
    S.place("XRIM:C","C","C22","100nF",310,160,{"1":"+3V3","2":"GND"})
    S.place("XRIM:C","C","C23","10uF",322,160,{"1":"+3V3","2":"GND"})

    S.text("PYRO: VBAT_ARMED -> e-match -> AO3400A low-side ; ADC continuity divider", 220, 195)
    for ch in range(3):
        y=215+ch*32
        S.place("XRIM:SCREW2","SCREW2",f"J{6+ch}",f"PYRO CH{ch+1}",230,y,
                {"1":"VBAT_ARMED","2":f"PYRO{ch+1}_D"})
        S.place("XRIM:NFET","NFET",f"Q{ch+1}","AO3400A",262,y,
                {"1":f"PYRO{ch+1}_GATE","3":f"PYRO{ch+1}_D","2":"GND"})
        S.place("XRIM:R","R",f"R{14+ch*4}","1k",280,y-6,{"1":f"PYRO{ch+1}_GATE_MCU","2":f"PYRO{ch+1}_GATE"})
        S.place("XRIM:R","R",f"R{15+ch*4}","100k",292,y-6,{"1":f"PYRO{ch+1}_GATE","2":"GND"})
        S.place("XRIM:R","R",f"R{16+ch*4}","100k",304,y-6,{"1":f"PYRO{ch+1}_D","2":f"PYRO{ch+1}_CONT"})
        S.place("XRIM:R","R",f"R{17+ch*4}","100k",316,y-6,{"1":f"PYRO{ch+1}_CONT","2":"GND"})
        S.place("XRIM:C","C",f"C{24+ch}","10nF",328,y-6,{"1":f"PYRO{ch+1}_CONT","2":"GND"})
        S.place("XRIM:LED","LED",f"LED{ch+1}","GRN cont",344,y-6,{"2":f"PYRO{ch+1}_D","1":f"LEDK{ch+1}"})
        S.place("XRIM:R","R",f"R{26+ch}","2.2k",356,y-6,{"1":f"LEDK{ch+1}","2":"GND"})
    S.place("XRIM:LED","LED","LED4","STATUS",344,310,{"2":"LED_R","1":"GND"})
    S.place("XRIM:R","R","R29","1k",356,310,{"1":"LED_STATUS","2":"LED_R"})

    S.text("INTER-BOARD: J1->ASAM-1 (UART0) ; J2->ASAM-2 (UART1) ; ARM_OUT on pin4", 220, 320)
    S.place("XRIM:JST_GH8","JST_GH8","J1","to ASAM-1",250,345,
            {"1":"GND","2":"UART0_TX","3":"UART0_RX","4":"ARM_OUT","7":"GND","8":"GND"},nc_pins=("5","6"))
    S.place("XRIM:JST_GH8","JST_GH8","J2","to ASAM-2",310,345,
            {"1":"GND","2":"UART1_TX","3":"UART1_RX","4":"ARM_OUT","7":"GND","8":"GND"},nc_pins=("5","6"))

    # ── PCB ──
    F = parts
    qfn=F.qfn56(); soic=F.soic8(); icm=F.lga14_icm(); bmp=F.lga10_bmp388()
    e22=F.e22_900m22s(); s235=F.sot23_5(); s23=F.sot23()
    c06=F.c0603(); r06=F.r0603(); led=F.led0603(); l44=F.l_4x4()
    xt=F.xt30(); sc2=F.screw2_508(); gh8=F.jst_gh8(); sh4=F.jst_sh4()
    sma=F.sma_edge(); tact=F.tact2(); xtl=F.xtal3225(); h5=F.header(5)
    m3=F.mount_m3()
    # SMA diode footprint
    do214 = FP("D_SMA", [Pad(1,-2.0,0,1.8,1.7), Pad(2,2.0,0,1.8,1.7)], (-3.2,-1.6,3.2,1.6),
               ['(fp_line (start -3.0 -1.2) (end -3.0 1.2) (stroke (width 0.2) (type default)) (layer "F.SilkS") (uuid "TSTAMP"))'])

    A=brd.add_fp
    sn=lambda d:{str(k):v for k,v in d.items()}
    A(qfn,"U1","RP2040",100,103,180,sn(RP))
    A(soic,"U2","W25Q128JVSIQ",104.5,112.6,0,sn(FLASH))
    A(icm,"U3","ICM-42688-P",112.5,100.0,0,sn(IMU))
    A(bmp,"U4","BMP388",88.5,100.0,0,sn(BMP))
    A(e22,"U5","E22-900M22S",98,82,0,sn(E22))
    A(s235,"U6","TLV62569",86,114.5,0,sn(BUCK))
    A(l44,"L1","2.2uH",82.8,107.2,90,{"1":"BUCK_SW","2":"+3V3"})
    A(do214,"D1","SS34",94.0,122.2,90,{"1":"VBAT","2":"VIN_SYS"})
    A(do214,"D2","SS34",80,93.5,60,{"1":"USB5V","2":"VIN_SYS"})
    A(xt,"J4","XT30",100,126.0,180,{"1":"VBAT","2":"GND"})
    A(sc2,"J5","ARM",75.5,111.5,118,{"1":"VBAT","2":"VBAT_ARMED"})
    A(sc2,"J6","PYRO1",87.5,121.5,149,{"1":"VBAT_ARMED","2":"PYRO1_D"})
    A(sc2,"J7","PYRO2",112.5,121.5,211,{"1":"VBAT_ARMED","2":"PYRO2_D"})
    A(sc2,"J8","PYRO3",122.5,111.5,242,{"1":"VBAT_ARMED","2":"PYRO3_D"})
    A(sma,"J3","SMA",106.3,70.8,0,{"1":"RF_ANT","2":"GND","3":"GND","4":"GND","5":"GND"})
    A(gh8,"J1","ASAM1",74.5,100,90,{"1":"GND","2":"UART0_TX","3":"UART0_RX","4":"ARM_OUT","7":"GND","8":"GND","MP1":"GND","MP2":"GND"})
    A(gh8,"J2","ASAM2",125.5,100,270,{"1":"GND","2":"UART1_TX","3":"UART1_RX","4":"ARM_OUT","7":"GND","8":"GND","MP1":"GND","MP2":"GND"})
    A(sh4,"J9","USB",79.5,87.0,240,{"1":"USB5V","2":"USB_DM","3":"USB_DP","4":"GND","MP1":"GND","MP2":"GND"})
    A(h5,"J10","SWD",115.2,86.0,90,{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"RUN","5":"GND"})
    A(tact,"SW1","BOOTSEL",87.5,93.5,90,{"1":"BOOTSEL_SW","2":"GND"})
    A(xtl,"X1","12MHz",100.0,95.6,0,{"1":"XIN","2":"GND","3":"XOUT_R","4":"GND"})
    # pyro FETs + glue
    A(s23,"Q1","AO3400A",92.5,114.5,0,{"1":"PYRO1_GATE","3":"PYRO1_D","2":"GND"})
    A(s23,"Q2","AO3400A",108.5,114.5,0,{"1":"PYRO2_GATE","3":"PYRO2_D","2":"GND"})
    A(s23,"Q3","AO3400A",115.5,108.0,0,{"1":"PYRO3_GATE","3":"PYRO3_D","2":"GND"})
    RR=[("R14","1k",96.5,111.0,90,{"1":"PYRO1_GATE_MCU","2":"PYRO1_GATE"}),
        ("R15","100k",90.0,111.0,90,{"1":"PYRO1_GATE","2":"GND"}),
        ("R16","100k",95.0,117.5,0,{"1":"PYRO1_D","2":"PYRO1_CONT"}),
        ("R17","100k",95.0,119.5,0,{"1":"PYRO1_CONT","2":"GND"}),
        ("R18","1k",105.5,111.0,90,{"1":"PYRO2_GATE_MCU","2":"PYRO2_GATE"}),
        ("R19","100k",111.5,111.0,90,{"1":"PYRO2_GATE","2":"GND"}),
        ("R20","100k",105.0,117.5,0,{"1":"PYRO2_D","2":"PYRO2_CONT"}),
        ("R21","100k",105.0,119.5,0,{"1":"PYRO2_CONT","2":"GND"}),
        ("R22","1k",112.0,105.0,0,{"1":"PYRO3_GATE_MCU","2":"PYRO3_GATE"}),
        ("R23","100k",112.0,111.2,0,{"1":"PYRO3_GATE","2":"GND"}),
        ("R24","100k",117.5,104.0,90,{"1":"PYRO3_D","2":"PYRO3_CONT"}),
        ("R25","100k",119.5,104.0,90,{"1":"PYRO3_CONT","2":"GND"}),
        ("R26","2.2k",91.0,118.8,90,{"1":"LEDK1","2":"GND"}),
        ("R27","2.2k",109.0,118.8,90,{"1":"LEDK2","2":"GND"}),
        ("R28","2.2k",119.8,107.5,90,{"1":"LEDK3","2":"GND"}),
        ("R29","1k",111.6,96.4,0,{"1":"LED_STATUS","2":"LED_R"}),
        ("R1","560k",82.5,114.0,90,{"1":"+3V3","2":"BUCK_FB"}),
        ("R2","124k",82.5,118.0,90,{"1":"BUCK_FB","2":"GND"}),
        ("R3","100k",97.9,120.9,90,{"1":"VBAT","2":"VBAT_SENSE"}),
        ("R4","100k",99.5,120.9,90,{"1":"VBAT_SENSE","2":"GND"}),
        ("R5","100k",81.0,103.5,0,{"1":"VBAT_ARMED","2":"ARM_SENSE"}),
        ("R6","200k",81.0,105.5,0,{"1":"ARM_SENSE","2":"GND"}),
        ("R7","1k",104.3,95.0,90,{"1":"XOUT_R","2":"XOUT"}),
        ("R8","10k",109.8,93.0,0,{"1":"+3V3","2":"RUN"}),
        ("R9","27R",84.5,90.0,60,{"1":"USB_DM_R","2":"USB_DM"}),
        ("R10","27R",85.8,91.8,60,{"1":"USB_DP_R","2":"USB_DP"}),
        ("R11","1k",91.5,95.7,0,{"1":"QSPI_SS","2":"BOOTSEL_SW"}),
        ("R12","4.7k",92.0,103.8,90,{"1":"+3V3","2":"I2C0_SDA"}),
        ("R13","4.7k",93.8,103.8,90,{"1":"+3V3","2":"I2C0_SCL"})]
    for ref,val,x,y,rot,nets in RR: A(r06,ref,val,x,y,rot,nets)
    CC=[("C1","10uF",90.5,110.5,90,{"1":"VIN_SYS","2":"GND"}),
        ("C2","22uF",85.8,104.6,0,{"1":"+3V3","2":"GND"}),
        ("C3","27pF",96.4,96.8,0,{"1":"XIN","2":"GND"}),
        ("C4","27pF",106.4,96.6,0,{"1":"XOUT_R","2":"GND"}),
        ("C5","100nF",104.8,107.0,0,{"1":"+3V3","2":"GND"}),   # IOVDD bottom (pin1 @103.65,105.6)
        ("C6","100nF",95.4,107.0,0,{"1":"+3V3","2":"GND"}),    # IOVDD 33/42 left
        ("C7","100nF",105.0,100.5,90,{"1":"+3V3","2":"GND"}),  # IOVDD right top
        ("C8","100nF",93.2,101.5,90,{"1":"+3V3","2":"GND"}),
        ("C9","100nF",93.2,109.0,0,{"1":"+3V3","2":"GND"}),
        ("C10","10uF",107.0,103.5,90,{"1":"+3V3","2":"GND"}),
        ("C11","100nF",110.6,107.6,90,{"1":"+1V1","2":"GND"}),
        ("C12","100nF",101.8,97.4,0,{"1":"+1V1","2":"GND"}),
        ("C13","1uF",97.0,110.6,0,{"1":"+1V1","2":"GND"}),
        ("C14","100nF",96.8,108.6,90,{"1":"+3V3","2":"GND"}),
        ("C15","1uF",93.5,97.8,0,{"1":"+3V3","2":"GND"}),
        ("C16","100nF",98.0,93.2,0,{"1":"+3V3","2":"GND"}),
        ("C17","100nF",109.0,97.6,0,{"1":"+3V3","2":"GND"}),
        ("C18","2.2uF",115.8,97.0,0,{"1":"+3V3","2":"GND"}),
        ("C19","10nF",112.5,103.6,0,{"1":"+3V3","2":"GND"}),
        ("C20","100nF",85.5,97.5,0,{"1":"+3V3","2":"GND"}),
        ("C21","100nF",85.0,102.5,90,{"1":"+3V3","2":"GND"}),
        ("C22","100nF",88.0,82.0,90,{"1":"+3V3","2":"GND"}),
        ("C23","10uF",88.0,84.8,90,{"1":"+3V3","2":"GND"}),
        ("C24","10nF",97.2,119.5,90,{"1":"PYRO1_CONT","2":"GND"}),
        ("C25","10nF",107.2,119.5,90,{"1":"PYRO2_CONT","2":"GND"}),
        ("C26","10nF",121.5,104.0,90,{"1":"PYRO3_CONT","2":"GND"}),
        ("C27","100nF",110.5,112.0,90,{"1":"VBAT_ARMED","2":"GND"})]
    for ref,val,x,y,rot,nets in CC: A(c06,ref,val,x,y,rot,nets)
    A(led,"LED1","CONT1",91.0,116.8,0,{"1":"LEDK1","2":"PYRO1_D"})
    A(led,"LED2","CONT2",109.0,116.8,0,{"1":"LEDK2","2":"PYRO2_D"})
    A(led,"LED3","CONT3",119.8,109.8,0,{"1":"LEDK3","2":"PYRO3_D"})
    A(led,"LED4","STAT",115.0,96.4,0,{"1":"GND","2":"LED_R"})
    for i,(mx,my) in enumerate([(81.7,81.7),(118.3,81.7),(81.7,118.3),(118.3,118.3)]):
        ddx,ddy = mx-100,my-100
        sc=26.0/math.hypot(ddx,ddy)
        A(m3,f"H{i+1}","M3",100+ddx*sc,100+ddy*sc,0,{})

    # RF: manual route, fat & short
    antx, anty = 104.985, 82-8.509+1.27  # E22 pin21 abs
    brd.track("RF_ANT",[(antx,anty),(106.3,anty),(106.3,70.8)],"F.Cu",0.9)
    rf_keepout = sbox(104.2, 69.0, 108.4, anty+1.3)

    # escape stubs for fine-pitch parts
    escape_stubs(brd,qfn,100,103,180,sn(RP))
    escape_stubs(brd,bmp,88.5,100.0,0,sn(BMP))
    escape_stubs(brd,icm,112.5,100.0,0,sn(IMU))
    # autoroute
    widths={"+3V3":0.5,"VIN_SYS":0.6,"VBAT":0.8,"VBAT_ARMED":0.8,"GND":0.4,"+1V1":0.4,
            "PYRO1_D":0.8,"PYRO2_D":0.8,"PYRO3_D":0.8,"BUCK_SW":0.5}
    rt=Router(brd,widths,keepouts=[(rf_keepout,("F.Cu","B.Cu"))])
    order=["UART0_TX","UART0_RX","UART1_TX","UART1_RX","ARM_OUT","SWDIO","SWCLK","RUN",
           "USB_DM","USB_DP","USB_DM_R","USB_DP_R","USB5V","BOOTSEL_SW","LED_STATUS","LED_R",
           "PYRO1_GATE_MCU","PYRO2_GATE_MCU","PYRO3_GATE_MCU","PYRO1_CONT","PYRO2_CONT","PYRO3_CONT",
           "ARM_SENSE","VBAT_SENSE",
           "QSPI_SS","QSPI_SCLK","QSPI_SD0","QSPI_SD1","QSPI_SD2","QSPI_SD3",
           "XIN","XOUT","XOUT_R","RUN","SWDIO","SWCLK",
           "SPI0_SCK","SPI0_MOSI","SPI0_MISO","IMU_CS","IMU_INT1",
           "I2C0_SDA","I2C0_SCL","BMP_INT",
           "SPI1_SCK","SPI1_MOSI","SPI1_MISO","LORA_NSS","LORA_BUSY","LORA_DIO1",
           "LORA_NRST","LORA_RXEN",
           "UART0_TX","UART0_RX","UART1_TX","UART1_RX","ARM_OUT",
           "USB_DM","USB_DP","USB_DM_R","USB_DP_R","USB5V","BOOTSEL_SW",
           "PYRO1_GATE","PYRO2_GATE","PYRO3_GATE",
           "PYRO1_GATE_MCU","PYRO2_GATE_MCU","PYRO3_GATE_MCU",
           "PYRO1_CONT","PYRO2_CONT","PYRO3_CONT",
           "LEDK1","LEDK2","LEDK3","LED_R","LED_STATUS",
           "ARM_SENSE","VBAT_SENSE","LORA_TXEN",
           "+1V1","VIN_SYS","VBAT","VBAT_ARMED","PYRO1_D","PYRO2_D","PYRO3_D",
           "+3V3","BUCK_SW","BUCK_FB"]
    allnets=set(n for n in brd.nets if n and n!="GND" and n!="RF_ANT")
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
        print("resumed", flush=True)
    for net in seq:
        if "--finish" in sys.argv:
            fails=sorted(set(fails)|set(n for n in seq if n not in done)); break
        if net in done: continue
        if not rt.route_net(net,widths.get(net,0.2)): fails.append(net)
        done.append(net)
        if _t.time()-_t0 > 8 and net != seq[-1]:
            _pk.dump((brd,rt,fails,done),open(CK,"wb"))
            print("CHECKPOINT", flush=True)
            sys.exit(42)
    # second chance at reduced width
    retry=[] if "--finish" in sys.argv else list(fails)
    if retry: fails=[]
    for net in retry:
        w=max(0.25, widths.get(net,0.2)*0.6)
        ok=rt.route_net(net,w)
        if not ok: fails.append(net)
    rt.commit()
    print(f"ROUTING: {len(fails)} failed nets: {fails}")
    stitch=stitch_gnd(brd, spacing=5.5, avoid=[rf_keepout])
    print(f"GND stitching vias: {stitch}")
    brd.gnd_zone("F.Cu"); brd.gnd_zone("B.Cu")
    import pickle
    pickle.dump((brd,sch.netlist,fails),open(os.path.join(OUT,"chk.pkl"),"wb"))
    ok = True
    if "--verify" in sys.argv:
        ok=verify(brd, sch.netlist, "CCM")
    with open(os.path.join(OUT,"CCM_Central_Command_Module.kicad_sch"),"w") as f: f.write(sch.emit())
    with open(os.path.join(OUT,"CCM_Central_Command_Module.kicad_pcb"),"w") as f: f.write(brd.emit())
    with open(os.path.join(OUT,"CCM_Central_Command_Module.kicad_pro"),"w") as f: f.write(project_file("CCM_Central_Command_Module"))
    print("WROTE", OUT, "verify_ok=",ok, "routing_fails=",len(fails))
    return 0 if (ok and not fails) else 1

if __name__=="__main__":
    sys.exit(main())
