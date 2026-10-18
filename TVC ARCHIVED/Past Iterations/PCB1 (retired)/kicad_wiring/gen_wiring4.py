#!/usr/bin/env python3
"""GTR70E WYVERN wiring, KiCad-7 .kicad_sch (flat netlist via global labels). Custom PCB1 (bare
RP2350B) flight harness + 3-axis TVC-balance harness (ground rig, separate Pico/Pico 2 W DAQ). No
symbol library required (documentation schematic)."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
def esc(s): return s.replace('"','\\"')
def box(x,y,title,pins,w=48):
    h=6+len(pins)*4; it=[f'(rectangle (start {x} {y}) (end {x+w} {y+h}) (stroke (width 0.25)(type solid)) (fill (type none)))',
        f'(text "{esc(title)}" (at {x+2} {y+3} 0)(effects (font (size 1.6 1.6))(justify left)))']
    yy=y+8
    for p in pins:
        it.append(f'(text "{esc(p)}" (at {x+2} {yy} 0)(effects (font (size 1.2 1.2))(justify left)))')
        it.append(f'(global_label "{esc(p.split(":")[0].strip())}" (shape input)(at {x+w} {yy} 0)(effects (font (size 1.0 1.0))(justify left)))')
        it.append(f'(wire (pts (xy {x+w-1} {yy}) (xy {x+w} {yy})) (stroke (width 0.15)(type solid)))'); yy+=4
    return it,h
def sch(title,mods):
    items=[]; x=20; y=20
    for m in mods:
        t,h=box(x,y,m[0],m[1],m[2] if len(m)>2 else 48); items+=t; y+=h+8
        if y>250: y=20; x+=72
    body="\n ".join(items)
    return f'''(kicad_sch (version 20230121) (generator "gtr70e_wyvern_wiring") (paper "A2")
  (title_block (title "{esc(title)}") (company "Skylight Industries") (rev "4.0"))
  (lib_symbols)
  {body}
  (sheet_instances (path "/" (page "1"))))'''
FLIGHT=[
 ("POWER",["VBAT: 2S LiPo 7.4V +","GND","TPS564201 buck -> intermediate rail","AP2112K-3.3 LDO -> 3V3 logic",
   "servo/expansion connectors (U8-U11) off buck rail"],62),
 # Every pin traced against the actual custom RP2350B PCB1 netlist and cross-checked against the
 # labeled schematic pin text (see CONFLICTS.md section 4 and firmware/wyvern4_tvc/imu_grv.h's file
 # header). This board has NO PCA9548A mux, no second I2C bus, NO GP26 ADC battery divider
 # (RP2350B's ADC pins are GPIO40-47, not 26-29), NO WiFi radio chip, and NO SWDIO/SWCLK on H1. The
 # INA226's own wiring has two real problems, not just an unverified address -- see the block below.
 ("INA226 POWER MONITOR (U4, shared I2C bus) -- WIRING PROBLEM, SEE CONFLICTS.md",[
   "VBUS/VIN-: trace to the ~5V BUCK OUTPUT rail, not pack voltage",
   "VIN+: traces to GND -- no real shunt in this path, current/power not meaningful",
   "A1 addr pin: traces to ~5V (R10/U13 node), not a valid GND/VS+/SDA/SCL strap",
   "getBusVoltage() -> battery.h, rail-sag thresholds only (NOT LiPo pack protection)",
   "address 0x40 is a bench-scan starting guess, not confirmed"],72),
 ("RP2350B (U1, bare QFN-80, custom PCB1)",["3V3: logic + sensor rail","GND",
   "GP0/GP1: shared I2C -> body BNO055, external BNO085 (STEMMA-QT), BME680, INA226, LIS3MDL",
   "GP2: PWM servo1 (pitch, JST U8)","GP3: PWM servo2 (yaw, JST U9)","GP4/GP5: spare JST (U10/U11, function TBD)",
   "GP8/GP9/GP10/GP11: microSD (MISO/CS/SCK/MOSI, all 4 pins confirmed)",
   "GP12: reserved for RBF, NOT wired to any switch on this board rev",
   "GP34: buzzer (H1 pin10, confirmed GPIO)","GP35: status LED (H1 pin9, confirmed GPIO)",
   "GP36: CAM_EN gate (H1 pin8, confirmed GPIO)","GP37: LAUNCH_IRQ (H1 pin7, confirmed GPIO)",
   "no WiFi/BLE chip on this board -- wifi_telemetry.h compiled only if WIFI_ENABLED"],86),
 ("IMUs x2, shared bus (different chip families)",["body: BNO055 0x28 CONFIRMED (COM3/ADR -> GND)",
   "external: BNO085 0x4A (SH2 protocol, STEMMA-QT, bulkhead-boundary mount, not on the gimbal)"],56),
 ("BME680 (0x76 CONFIRMED, shared bus)",["SDO->GND, CSB->3V3 (I2C mode) -- pressure/temp/gas, no BMP388 populated"],48),
 ("LIS3MDL (0x1C CONFIRMED, shared bus)",["SDO/SA1->GND -- magnetometer, present on PCB1, unused by firmware"],48),
 ("STORAGE, microSD (CARD1, TF-01A) -- POSSIBLE DEFECT, SEE CONFLICTS.md",[
   "MISO GP8 / CS GP9 / SCK GP10 / MOSI GP11 -- all confirmed against the netlist",
   "pin4 (expected VDD) traces to GND in the netlist, not 3V3 -- bench-check before trusting SD logging",
   "3V3(?)/GND: full-rate flight log"],62),
 ("Action camera (self-contained)",["V(buck): gated by CAM_EN (GP36)","GND: records to own microSD"],54),
 ("TVC SERVOS (2-axis gimbal)",["S1_SIG: GP2 (JST U8)","S2_SIG: GP3 (JST U9)","+V (buck rail)","GND"],50),
]
# Ground-rig DAQ MCU is a Raspberry Pi Pico / Pico 2 W (Arduino-Pico core) per wyvern4_gse_servo_rig.ino
# and wyvern4_gse_solenoid_rig.ino, NOT the Arduino Nano/Teensy this file's older revisions specified.
# See CONFLICTS.md item 3 for the record of that supersession. Pin numbers below are pulled directly
# from each sketch's header PIN MAP comment -- keep in sync if the sketches' pin maps ever change.
BAL_SERVO=[
 ("RPi PICO / PICO 2 W, servo-rig DAQ",["3V3: HX711 + BNO085 power","GND","USB: CSV log to host",
   "GP4/GP5: I2C0 -> gimbal BNO085 (0x4A)","GP14: PWM servo1 (pitch)","GP15: PWM servo2 (yaw)",
   "LED_BUILTIN: tare-complete blink"],64),
 ("LOAD CELLS + HX711 x3 (bit-banged)",["Z (axial, 5kg): DT GP10 / SCK GP11","X (lateral, 1kg): DT GP6 / SCK GP7","Y (lateral, 1kg): DT GP8 / SCK GP9"],56),
 ("GIMBAL BNO085 (Game Rotation Vector)",["I2C0 0x4A: nozzle-angle cross-check vs. commanded servo pos"],52),
 ("SERVO GIMBAL UNDER TEST",["S1_SIG: GP14 (pitch)","S2_SIG: GP15 (yaw)","VSERVO","GND"],50),
]
BAL_SOLENOID=[
 ("RPi PICO / PICO 2 W, solenoid-rig DAQ",["3V3: HX711 + BNO085 power","GND","USB: CSV log to host",
   "GP4/GP5: I2C0 -> BNO085 (gimbal attitude)","GP16-19: solenoid PWM -> 4x IRF520 gate"],64),
 ("LOAD CELLS + HX711 x3 (bit-banged)",["Z (axial, 5kg): DT GP10 / SCK GP11","X (lateral, 1kg): DT GP12 / SCK GP13","Y (lateral, 1kg): DT GP14 / SCK GP15"],56),
 ("GIMBAL BNO085 (I2C0 0x4A)",["Game Rotation Vector + gyro rate -> deflection from 3-axis load balance"],48),
 ("SOLENOIDS x4 via IRF520 (+ 1N4007 flyback EACH)",["PITCH+: GP16","PITCH-: GP17","YAW+: GP18","YAW-: GP19","V12: coil supply"],62),
]
open("WYVERN_E4_flight_harness.kicad_sch","w").write(sch("GTR70E WYVERN, custom PCB1 (RP2350B) flight harness",FLIGHT))
open("WYVERN_E4_tvc_balance_servo_harness.kicad_sch","w").write(sch("GTR70E WYVERN, TVC balance harness (servo rig, Pico)",BAL_SERVO))
open("WYVERN_E4_tvc_balance_solenoid_harness.kicad_sch","w").write(sch("GTR70E WYVERN, TVC balance harness (solenoid rig, Pico)",BAL_SOLENOID))
for f in ("WYVERN_E4_flight_harness.kicad_sch","WYVERN_E4_tvc_balance_servo_harness.kicad_sch","WYVERN_E4_tvc_balance_solenoid_harness.kicad_sch"):
    s=open(f).read(); print(f,"parens",s.count("("),"==",s.count(")"),"OK" if s.count("(")==s.count(")") else "BAD")
