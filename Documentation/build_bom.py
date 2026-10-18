#!/usr/bin/env python3
"""Build Documentation/WYVERN_FIN_BOM.xlsx (fin-control revision).

Sheets: To Buy - Flight | To Buy - Wind Tunnel | On Hand (reuse) | Retired TVC stock | Summary
Every Line total is a formula; Summary pulls the sheet totals by formula. Prices marked "est."
are estimates to confirm at checkout; the rest were read off the vendor page on 2026-10-15.
Recalculate after building:  python3 <xlsx skill>/scripts/recalc.py WYVERN_FIN_BOM.xlsx
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "WYVERN_FIN_BOM.xlsx")
F = Font(name="Arial", size=10); FB = Font(name="Arial", size=10, bold=True)
FH = Font(name="Arial", size=12, bold=True); BLUE = Font(name="Arial", size=10, color="0000FF")
HDR = PatternFill("solid", fgColor="1F2937"); HDRF = Font(name="Arial", size=10, bold=True, color="FFFFFF")
SEC = PatternFill("solid", fgColor="E5E7EB"); thin = Side(style="thin", color="D1D5DB")
COLS = ["Item", "Vendor", "Part # / Spec", "Link", "Why / where used", "Qty", "Unit ($)", "Line ($)", "Price source"]
WIDTH = [46, 13, 26, 46, 58, 6, 10, 11, 18]

FLIGHT = [
 ("Avionics", [
  ("Adafruit Feather RP2040 RFM95 LoRa 915 MHz", "Adafruit", "PID 5714", "https://www.adafruit.com/product/5714", "Flight computer + ground station (same board at both ends) + 1 spare", 3, 29.95, "vendor 2026-10-16, in stock"),
  ("Adafruit ADXL375 high-g accelerometer +/-200 g, STEMMA QT", "DigiKey", "Adafruit 5374, DK 15998640", "https://www.digikey.com/en/products/detail/adafruit-industries-llc/5374/15998640", "Axial channel during boost (the BNO085 clips at 8 g); -Y spine face. Out of stock at adafruit.com/product/5374 on 2026-10-16; DigiKey lists it as shipping", 1, 24.95, "Adafruit list; confirm at DigiKey"),
  ("STEMMA QT to male header cable 150 mm", "Adafruit", "PID 4209", "https://www.adafruit.com/product/4209", "BME688 onto the Feather's TX / RX pads (I2C0, core 1)", 1, 0.95, "vendor 2026-10-16, in stock"),
  ("STEMMA QT cable 100 mm", "Adafruit", "PID 4210", "https://www.adafruit.com/product/4210", "BNO085 -> ADXL375", 1, 0.95, "vendor 2026-10-16, in stock"),
  ("SMA to uFL RF adapter cable", "Adafruit", "PID 851", "https://www.adafruit.com/product/851", "Ground-station antenna feed (Feather uFL -> SMA jack)", 1, 3.95, "vendor 2026-10-16, in stock"),
  ("Linx 916 MHz whip antenna, straight SMA male", "DigiKey", "TE Linx ANT-916-CW-HW-SMA", "https://www.digikey.com/en/products/detail/te-connectivity-linx/ANT-916-CW-HW-SMA/2694126", "Ground station; replaces the generic Yagi (no verifiable SMA listing). Link margin 51.7 dB at the 236 m worst slant range (wf_link_budget, 1.2 dBi)", 1, 16.00, "est.; price shows at DigiKey"),
  ("Adafruit Micro SD SPI/SDIO breakout, 3V only", "Adafruit", "PID 4682", "https://www.adafruit.com/product/4682", "Flight log of record on the spine's -Y face (25.4 x 22.8 mm) + spare", 2, 3.50, "vendor 2026-10-16, in stock"),
  ("Piezo buzzer PS1240", "Adafruit", "PID 160", "https://www.adafruit.com/product/160", "Pad / landing beacon (D12)", 1, 1.50, "vendor 2026-10-16, in stock"),
  ("NPN transistor PN2222, 10 pack", "Adafruit", "PID 756", "https://www.adafruit.com/product/756", "Buzzer driver on GP12", 1, 1.95, "vendor 2026-10-16, in stock"),
  ("Resistor 1 k 5 % 1/4 W carbon film", "DigiKey", "Stackpole CF14JT1K00", "https://www.digikey.com/en/products/detail/stackpole-electronics-inc/CF14JT1K00/1741314", "Buzzer base resistor (Adafruit 4294 pack is out of stock); buy 10", 10, 0.10, "est."),
  ("SparkFun Solder-able Breadboard (full)", "SparkFun", "PRT-12070", "https://www.sparkfun.com/sparkfun-solder-able-breadboard.html", "Power board cut to 16 x 60 mm on the spine's +Y face (2810, buck, screw switch, divider, buzzer drive, 470 uF). Adafruit Perma-Proto boards were out of stock", 1, 6.95, "vendor 2026-10-16, in stock"),
 ]),
 ("Actuation", [
  ("KST X08 Plus HV coreless micro servo", "Aloft Hobbies", "X08+ 23.5 x 8 x 16.8 mm, 9 g", "https://alofthobbies.com/products/kst-x08-servo-5-30kg-73-60-oz-in-0-09-sec-wide-voltage", "4 control-fin servos in one ring + 1 spare; 3.8-8.4 V direct on 2S", 5, 45.00, "vendor 2026-10-16, in stock"),
  ("Wixey WR300 Type 2 digital angle gauge", "Woodcraft", "WR300, 0.1 deg", "https://www.woodcraft.com/products/wixey-digital-angle-gauge-with-backlight-type-2-wr300", "Servo trim + us/deg calibration (t2_servo_cal)", 1, 34.99, "vendor 2026-10-16, in stock"),
 ]),
 ("Power", [
  ("Pololu 5 V 1 A step-down regulator D24V10F5", "Pololu", "#2831", "https://www.pololu.com/product/2831", "2S -> 5 V for the Feather USB pin. 1 + spare", 2, 12.95, "vendor 2026-10-16"),
  ("Pololu Mini MOSFET slide switch LV", "Pololu", "#2810", "https://www.pololu.com/product/2810", "Main power switch; screw switch on CTRL. 1 + spare (Pololu lists it as rationed)", 2, 4.49, "vendor 2026-10-16"),
  ("MK2 rocketry screw switch (2 pack)", "Tindie (concreted0g)", "M2 PEM-nut screw switch", "https://www.tindie.com/products/concreted0g/mk2-rocketry-screw-switches", "Internal CTRL switch reached through the 3 mm wall hole. Price not shown on the page; the listing gates shipping by country", 1, 8.00, "est."),
  ("XT30 LiPo pigtail with 35 V 470 uF capacitor, 16 AWG (3 pcs)", "GetFPV", "XT30 + 470 uF", "https://www.getfpv.com/xt30-lipo-pigtail-w-35v-470uf-capacitor-16awg-3pcs.html", "Battery lead to the power board; the cap doubles as the servo bulk cap", 1, 12.99, "vendor 2026-10-16, in stock"),
 ]),
 ("Recovery + ejection path", [
  ("Aluminium tube 3/8 in OD x 0.035 in wall, 6061-T6, 24 in", "Speedy Metals", "p-4553", "https://speedymetals.com/p-4553-38-od-x-0035-wall-tube-6061-t6-aluminum.aspx", "Ejection bypass tube on the centreline (cut to 195 mm); 24 in gives two tubes + scrap", 1, 5.55, "vendor 2026-10-16 (24 in option)"),
  ("Buna-N O-ring AS568-012 (9.25 x 1.78 mm), 70A", "Marco Rubber", "B1003-012", "https://www.marcorubber.com/product/B1003-012", "Bypass tube seals at the plenum and the RB floor; price appears after entering a quantity (buy 10)", 1, 8.00, "est."),
  ("M2 nylon shear pins, starter pack (10 + M2 tap)", "LOC Precision", "M2 shear pins", "https://locprecision.com/products/m2-shear-pins", "Nose retention, 2 pins. Replaces #2-56 nylon (2.0 vs 2.18 mm)", 1, 5.89, "vendor 2026-10-16, available"),
  ("Stainless eye bolt #10-24 x 2 in with nut (10 pack)", "Home Depot (Hillman 4283)", "Hillman 4283", "https://www.homedepot.com/p/Hillman-10-24-tpi-x-2-in-Stainless-Steel-Eye-Bolt-with-Nut-10-Pack-4283/204775387", "Shock-cord anchor on the RB floor, 20 mm off-axis; replaces M5 x 20 (#10 = 4.83 mm, same 5 mm hole). Trim the shank", 1, 9.89, "vendor 2026-10-16"),
  ("Stainless quick link 3/16 in", "Home Depot (Everbilt 41564)", "Everbilt 41564", "https://www.homedepot.com/p/Everbilt-3-16-in-Stainless-Steel-Quick-Link-41564/205882822", "Cord -> chute and cord -> nose", 2, 7.66, "vendor 2026-10-16"),
  ("Nickel-plated swivel 4/0 (pair), 400 lb", "LOC Precision", "Swivel4Pair", "https://locprecision.com/products/nickel-plated-swivels", "Between quick link and chute to stop line twist", 1, 3.65, "vendor 2026-10-16, in stock"),
  ("Daisy PrecisionMax steel BBs, 4000 ct", "Academy Sports", "4.5 mm steel", "https://www.academy.com/p/daisy-precision-max-premium-bbs-4-000-count", "Nose ballast (214 g = about 630 BBs, epoxied; rev 3d)", 1, 6.99, "vendor 2026-10-16"),
 ]),
 ("Propulsion", [
  ("AeroTech Econojet F42-4T single-use 29 x 83 mm Blue Thunder, 2-pack", "eRockets", "AER 64204, 4 s delay", "https://www.erockets.biz/aerotech-29mm-composite-model-rocket-motor-single-use-f42-4t-2pk-aer-64204-required-to-pay-for-ups-ground-shipping/", "3 research flights + 1 spare (4 motors). eRockets showed 4 packs in stock on 2026-10-16; New Century ($43.99) was sold out. UPS ground, continental US only", 2, 49.49, "vendor 2026-10-16, stock 4"),
  ("Estes 1010 rail buttons (pair, with screws)", "Estes", "1010", "https://estesrockets.com/products/1010-rail-buttons", "Estes Pro Series II rail (6 ft, 1010)", 1, 3.25, "vendor 2026-10-16, in stock"),
 ]),
 ("Hardware + material", [
  ("Metric socket-cap screw kit, A2 stainless, M2-M8, 441 pcs", "Albany County Fasteners", "1060-090", "https://www.albanycountyfasteners.com/metric-socket-cap-screw-assortment-kit-p/1060-090.htm", "Board screws into the spine's M2 heat-set inserts (owned), servo ears, joints, retainer, hubs, pads", 1, 67.55, "vendor 2026-10-16"),
  ("Bambu Lab ASA-Aero 1.75 mm 1 kg", "MatterHackers", "M264H2ZL", "https://www.matterhackers.com/store/l/bambu-lab-asa-aero-filament-175mm-1kg/sk/M264H2ZL", "Tubes + nose (~200 g). Buy only if the old roll is low; Bambu's own store page would not load for verification", 1, 64.99, "vendor 2026-10-16"),
 ]),
]
TUNNEL = [
 ("Airflow", [
  ("AC Infinity Cloudline PRO T8 inline duct fan, 8 in", "Mini Split Systems Direct", "AI-CLT8", "https://minisplitsystemsdirect.com/products/ac-infinity-cloudline-pro-t8-quiet-inline-duct-fan-system-with-temperature-humidity-vpd-controller-8-inch", "Replaces the 140 mm Noctua: ~12 m/s in the stock section. In stock here; AC Infinity, Hydrobuilder and Happy Hydro ($199) were all out of stock on 2026-10-16", 1, 219.00, "vendor 2026-10-16, in stock"),
  ("AC Infinity stainless duct clamps 8 in (2 pack)", "AC Infinity", "AC-DCA8-2", "https://acinfinity.com/hydroponics-growers/stainless-steel-duct-clamps-8-inch-two-pack", "Fan to the printed 100 sq -> 8 in transitions", 1, 7.99, "vendor 2026-10-16"),
 ]),
 ("Phase A (single fin, stock section)", [
  ("KST X08 Plus HV micro servo", "Aloft Hobbies", "X08+", "https://alofthobbies.com/products/kst-x08-servo-5-30kg-73-60-oz-in-0-09-sec-wide-voltage", "Drives the half-model fin on the balance cradle (keeps the flight servos on the airframe)", 1, 45.00, "vendor 2026-10-16, in stock"),
 ]),
 ("Balance + instrumentation", [
  ("SparkFun Qwiic Scale NAU7802", "SparkFun", "SEN-15242", "https://www.sparkfun.com/sparkfun-qwiic-scale-nau7802.html", "24-bit load-cell ADC, one per cell, behind the owned PCA9548 mux (fixed 0x2A)", 2, 5.95, "vendor 2026-10-16"),
  ("Mini load cell 100 g, straight bar (TAL221)", "SparkFun", "SEN-14727", "https://www.sparkfun.com/mini-load-cell-100g-straight-bar-tal221.html", "Under the servo cradle: normal force and hinge-line moment", 2, 14.50, "vendor 2026-10-16, in stock"),
  ("Sensirion SDP810-125Pa differential pressure sensor", "DigiKey", "SDP810-125PA", "https://www.digikey.com/en/products/detail/sensirion-ag/SDP810-125PA/6605488", "Pitot dynamic pressure (q ~ 85 Pa at 12 m/s; 125 Pa full scale)", 1, 40.00, "est.; price shows at DigiKey"),
  ("Prandtl pitot tube + 40 cm silicone tubing (2 mm ID)", "ReadyMadeRC", "RMRC replacement pitot", "https://www.readymaderc.com/products/details/rmrc-replacement-pitot-tube-for-matek", "Upstream of the model on the centreline, into the SDP810", 1, 8.99, "vendor 2026-10-16, in stock"),
  ("USB Type-C extension cable 2 m", "Adafruit", "PID 5216", "https://www.adafruit.com/product/5216", "Tether to the model's Feather in tunnel mode", 1, 9.95, "vendor 2026-10-16, in stock"),
 ]),
 ("Print material", [
  ("MatterHackers PRO Series PETG black 1.75 mm 1 kg", "MatterHackers", "MGTE765N", "https://www.matterhackers.com/store/l/black-pro-series-petg-high-strength-filament-1.75mm/sk/MGTE765N", "Adapter, transition, cradle and fairings (~0.8 kg for Phase A). The page did not show a price to the fetcher", 1, 30.00, "est."),
 ]),
]
ON_HAND = [
 ("Raspberry Pi Pico 2 W", 2, "Tunnel balance DAQ (1) + spare (the ground station is now a second Feather RP2040 RFM95)"),
 ("Adafruit BNO085 (4754)", 4, "1 flight IMU on the spine's +X face; spares"),
 ("Adafruit BME688 (5046)", 2, "Flight baro + spare"),
 ("Adafruit microSD breakout (254) + 32 GB cards", 1, "Cards go in the 4682; the 254 board itself is too wide for the spine (bench / ground-station logging)"),
 ("OVONIC 2S 450 mAh LiPo (XT30)", 2, "Flight battery (4.2x margin on the 26-min mission)"),
 ("2S/3S balance charger", 1, "Charging"),
 ("470 uF low-ESR + 100 nF; 100k/47k 1 % resistors", 1, "Servo bulk cap, Vbat divider (same values as the TVC board)"),
 ("Adafruit PCA9548 I2C mux (5626)", 1, "Tunnel balance: the two NAU7802s share address 0x2A"),
 ("STEMMA QT 300 mm cables (5384)", 6, "Feather -> BNO085 (Wire1); tunnel balance"),
 ("Estes Pro Series II launch rail (6 ft) + controller", 1, "Launch system (stated on hand)"),
 ("Estes F15-4 motors", 2, "Static-stand thrust runs only; 114 mm long, does not fit the 83 mm motor bay"),
 ("Static thrust stand + deflector (Motor Test Stand/)", 1, "F42-4T thrust-curve check (use the spare motor) before flight"),
 ("Adafruit load cells 1 kg x2, 5 kg x2; HX711 x4; calibration weights", 1, "Static stand; balance calibration"),
 ("Filament: PC-FR, PETG-CF, ASA (black), ASA-Aero, PLA", 1, "Plenum/MMT/retainer (PC-FR), fins/hubs/deck (PETG-CF), tubes (ASA-Aero)"),
 ("Heat-set insert kit M2-M6, J-B Weld, Kapton, 24 AWG silicone wire, heat-shrink, headers", 1, "Assembly"),
 ("Nomex chute protector 12x12 in", 1, "Recovery bay"),
 ("Estes 24 in rip-stop chute, aramid shock cord 19 ft", 1, "VERIFY these arrived (they were on the TVC cart)"),
 ("Jerrod H tunnel kit: STLs, 40 + 80 mesh, magnets, Loc-Line, CF3 fog machine, OXLasers line laser, P96L light", 1, "Upstream modules, screens, smoke + laser sheet reused unchanged"),
 ("Mechatronics MS1238 120 mm fan", 1, "Spare; not used (Cloudline T8 replaces the fan)"),
]
RETIRED = [
 ("EMAX ES08MA II servos", "TVC gimbal; too tall for the single servo ring (needs <= 17 mm body height around the central bypass)"),
 ("MR105-2RS bearings, M2 rod-end ball links", "TVC gimbal linkage"),
 ("Electromagnets (TOMSHIELE, AIRTAK), N52 magnets, IRF520, 1N4007, 12 V PSU", "Magnetic TVC stand"),
 ("TMAG5273 Hall sensor, Arduino Nano", "Magnetic-gimbal sensing / solenoid DAQ"),
 ("VL53L4CD ToF x6", "Unused in both revisions"),
 ("301 SS foil", "TVC balance flexures"),
]

def header(ws, title, sub):
    ws["A1"] = title; ws["A1"].font = FH
    ws["A2"] = sub; ws["A2"].font = Font(name="Arial", size=9, italic=True, color="4B5563")
    for i, (c, w) in enumerate(zip(COLS, WIDTH), 1):
        cell = ws.cell(row=4, column=i, value=c); cell.font = HDRF; cell.fill = HDR
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A5"

def section_sheet(ws, title, sub, sections):
    header(ws, title, sub)
    r = 5; subtot = []
    for name, items in sections:
        ws.cell(row=r, column=1, value=name).font = FB
        for c in range(1, 10): ws.cell(row=r, column=c).fill = SEC
        r += 1; first = r
        for (item, vend, part, link, why, qty, unit, src) in items:
            vals = [item, vend, part, link, why, qty, unit, f"=F{r}*G{r}", src]
            for c, v in enumerate(vals, 1):
                cell = ws.cell(row=r, column=c, value=v); cell.font = F
                cell.alignment = Alignment(wrap_text=c in (1, 5), vertical="top")
            ws.cell(row=r, column=6).font = BLUE; ws.cell(row=r, column=7).font = BLUE
            ws.cell(row=r, column=7).number_format = "$#,##0.00"; ws.cell(row=r, column=8).number_format = "$#,##0.00"
            if link: ws.cell(row=r, column=4).hyperlink = link
            r += 1
        ws.cell(row=r, column=7, value="Subtotal").font = FB
        ws.cell(row=r, column=8, value=f"=SUM(H{first}:H{r-1})").font = FB
        ws.cell(row=r, column=8).number_format = "$#,##0.00"
        subtot.append(f"H{r}"); r += 2
    ws.cell(row=r, column=7, value="TOTAL").font = FB
    ws.cell(row=r, column=8, value="=" + "+".join(subtot)).font = FB
    ws.cell(row=r, column=8).number_format = "$#,##0.00"
    ws.cell(row=r + 2, column=1, value="Blue = inputs (qty, unit price). Line and totals are formulas. 'est.' prices: confirm at checkout.").font = Font(name="Arial", size=9, italic=True)
    return f"H{r}"

wb = Workbook()
ws1 = wb.active; ws1.title = "To Buy - Flight"
t1 = section_sheet(ws1, "GTR70E WYVERN fin-control — flight vehicle, to buy", "Built by Documentation/build_bom.py · numbers trace to Simulations/canonical_numbers.json", FLIGHT)
ws2 = wb.create_sheet("To Buy - Wind Tunnel")
t2 = section_sheet(ws2, "Jerrod H tunnel adaptation — Phase A only: single fin in the stock section", "See Documentation/Wind_Tunnel_Adaptation.md", TUNNEL)
ws3 = wb.create_sheet("On Hand (reuse)")
ws3["A1"] = "Already owned and reused (verify counts on the shelf)"; ws3["A1"].font = FH
for i, (c, w) in enumerate(zip(["Item", "Qty", "Role in the fin-control build"], [62, 6, 90]), 1):
    cell = ws3.cell(row=3, column=i, value=c); cell.font = HDRF; cell.fill = HDR
    ws3.column_dimensions[get_column_letter(i)].width = w
for r, (a, q, b) in enumerate(ON_HAND, 4):
    for c, v in enumerate((a, q, b), 1): ws3.cell(row=r, column=c, value=v).font = F
ws4 = wb.create_sheet("Retired TVC stock")
ws4["A1"] = "Owned but not used by the fin-control vehicle (resell / keep for other projects)"; ws4["A1"].font = FH
for i, (c, w) in enumerate(zip(["Item", "Was used for"], [62, 80]), 1):
    cell = ws4.cell(row=3, column=i, value=c); cell.font = HDRF; cell.fill = HDR
    ws4.column_dimensions[get_column_letter(i)].width = w
for r, (a, b) in enumerate(RETIRED, 4):
    for c, v in enumerate((a, b), 1): ws4.cell(row=r, column=c, value=v).font = F
ws5 = wb.create_sheet("Summary")
ws5["A1"] = "Spend summary"; ws5["A1"].font = FH
rows = [("Flight vehicle (to buy)", f"='To Buy - Flight'!{t1}"), ("Wind tunnel adaptation (to buy)", f"='To Buy - Wind Tunnel'!{t2}"),
        ("TOTAL new spend", "=B3+B4")]
for r, (a, b) in enumerate(rows, 3):
    ws5.cell(row=r, column=1, value=a).font = FB if "TOTAL" in a else F
    c = ws5.cell(row=r, column=2, value=b); c.font = FB if "TOTAL" in a else Font(name="Arial", size=10, color="008000"); c.number_format = "$#,##0.00"
ws5.column_dimensions["A"].width = 40; ws5.column_dimensions["B"].width = 16
ws5["A7"] = "Motors are 2 x Econojet F42-4T 2-packs = 4 motors for $98.98 at eRockets (3 flights + 1 spare / static test). Links checked 2026-10-16; Phase B tunnel items removed."
ws5["A7"].font = Font(name="Arial", size=9, italic=True)
wb.move_sheet("Summary", offset=-4)
wb.save(OUT); print("wrote", OUT)
