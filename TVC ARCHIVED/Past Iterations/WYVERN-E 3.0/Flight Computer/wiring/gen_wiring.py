#!/usr/bin/env python3
"""WYVERN-E 3.0 Flight Computer wiring-diagram generator.
Emits two KiCad-7 (.kicad_sch) interconnect diagrams: tri-solenoid (A) and servo (B).
Flat netlist via global labels; no symbol library required. Documentation schematic."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
def esc(s): return s.replace('"','\\"')
def box(x,y,title,pins,w=46):
    h=6+len(pins)*4
    it=[f'(rectangle (start {x} {y}) (end {x+w} {y+h}) (stroke (width 0.25)(type solid)) (fill (type none)))']
    it.append(f'(text "{esc(title)}" (at {x+2} {y+3} 0)(effects (font (size 1.6 1.6))(justify left)))')
    yy=y+8
    for p in pins:
        it.append(f'(text "{esc(p)}" (at {x+2} {yy} 0)(effects (font (size 1.2 1.2))(justify left)))')
        it.append(f'(global_label "{esc(p.split(":")[0].strip())}" (shape input)(at {x+w} {yy} 0)(effects (font (size 1.0 1.0))(justify left)))')
        it.append(f'(wire (pts (xy {x+w-1} {yy}) (xy {x+w} {yy})) (stroke (width 0.15)(type solid)))')
        yy+=4
    return it,h
def sch(title,modules):
    items=[]; x=20; y=20; colmax=0; col=0
    for m in modules:
        t,h=box(x,y,m[0],m[1],m[2] if len(m)>2 else 46)
        items+=t; y+=h+8; colmax=max(colmax,h)
        if y>240: y=20; x+=70
    body="\n  ".join(items)
    return f'''(kicad_sch (version 20230121) (generator "wyvern_fc_wiring")
  (paper "A2")
  (title_block (title "{esc(title)}") (company "Skylight Rocketry") (rev "3.0")
    (comment 1 "Off-the-shelf Raspberry Pi 5 flight computer") (comment 2 "Documentation interconnect — flat netlist via global labels"))
  (lib_symbols)
  {body}
  (sheet_instances (path "/" (page "1")))
)'''

CORE = [
 ("POWER — 3S Li-ion 11.1V / USB-C PD",[
   "VBAT_11V1: 3S pack +  (also 12V 2A bench supply)","GND: common ground",
   "USB_C_IN: IP2368 PD charge","BUCK5V_EN: 5V/5A buck -> Pi5","BUCK6V_EN: 6V UBEC -> servo rail (B)"],52),
 ("RASPBERRY PI 5 (4GB)",[
   "5V: from 5V/5A buck","GND","SDA: GPIO2 I2C1","SCL: GPIO3 I2C1",
   "SPI_MOSI: GPIO10","SPI_MISO: GPIO9","SPI_SCLK: GPIO11","CE0: GPIO8 uSD#1","CE1: GPIO7 uSD#2",
   "UART_TX: GPIO14 -> RRC3+","UART_RX: GPIO15","RBF_SENSE: GPIO17","LAUNCH_IRQ: GPIO27",
   "PWM_A: GPIO12/13/18 (TVC)","CSI: Camera Module 3"],58),
 ("TCA9548A I2C MUX",[
   "SDA","SCL","VIN: 3V3","GND",
   "CH0: BNO085 gimbal","CH1: BNO085 FC","CH2: BNO085 nose",
   "CH3: LSM6DSO32","CH4: LIS2MDL","CH5: BMP280","CH6: BME688"],50),
 ("SENSORS (STEMMA QT chain)",[
   "BNO085_x3: 0x4A/0x4B via mux ch0-2","LSM6DSO32: 0x6A ch3","LIS2MDL: 0x1E ch4",
   "BMP280: 0x77 ch5","BME688: 0x76 ch6"],54),
 ("STORAGE — 2x microSD (SPI)",[
   "uSD1_CS: CE0 (video)","uSD2_CS: CE1 (flight log)","SPI_MOSI","SPI_MISO","SPI_SCLK","GND"],48),
 ("RRC3+ DUAL-DEPLOY + 2nd-STAGE IGNITION",[
   "VBAT_11V1","GND","UART_TX","UART_RX",
   "DROGUE: apogee charge","MAIN: main charge","AUX: G25W 2nd-stage igniter"],56),
 ("JOLLY LOGIC ALTIMETER 2 (backup record)",["VBAT_11V1","GND: independent log"],52),
 ("RBF ARM JUMPER (remove-before-flight)",[
   "RBF_SENSE: GPIO17 (inserted=safe)","GND","PYRO_INHIBIT: masks AUX/DROGUE/MAIN until pulled"],56),
]

SOL = CORE + [
 ("TVC SYSTEM A — 3-ch IRF520 MOSFET DRIVER",[
   "GATE0: GPIO12 (PWM)","GATE1: GPIO13","GATE2: GPIO18","VBAT_11V1: solenoid bus","GND"],54),
 ("3x 50N 12V SOLENOID (gimbal actuators @120deg)",[
   "SOL0: drain Q0 + 1N4007 flyback","SOL1: drain Q1","SOL2: drain Q2","N52: magnet return/detent"],58),
]
SERVO = CORE + [
 ("TVC SYSTEM B — PCA9685 16-ch PWM (I2C)",[
   "SDA","SCL","V+: 6V UBEC servo rail","GND","OE: output enable","CH0/1/2: servo signal"],52),
 ("3x DS3235 35kg DIGITAL SERVO (gimbal)",[
   "SIG0: PCA9685 CH0","SIG1: CH1","SIG2: CH2","VCC: 6V rail","GND"],50),
]

open("WYVERN_E3_solenoid_harness.kicad_sch","w").write(sch("WYVERN-E 3.0 FC — TVC System A (tri-solenoid) harness",SOL))
open("WYVERN_E3_servo_harness.kicad_sch","w").write(sch("WYVERN-E 3.0 FC — TVC System B (servo-gimbal) harness",SERVO))
for f in ("WYVERN_E3_solenoid_harness.kicad_sch","WYVERN_E3_servo_harness.kicad_sch"):
    s=open(f).read(); print(f, "parens", s.count("("), "==", s.count(")"), "OK" if s.count("(")==s.count(")") else "MISMATCH")
