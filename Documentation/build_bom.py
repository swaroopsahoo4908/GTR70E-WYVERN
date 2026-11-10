#!/usr/bin/env python3
"""Build Documentation/WYVERN_BOM.xlsx: the whole project's buy list on ONE sheet (rev 4).

Sections: Rocket | Wind Tunnel | Flow-Vis. Full materials list: nothing is assumed owned except the
3D printers and a laptop. Filament, consumables (solder, wire, glue, tape, ballast) and hand tools are all
on it. Items both builds use (servo 4-packs, angle gauge, screw kit, heat-set inserts, PETG-CF, tools)
are bought once, under Rocket.
Every line total and subtotal is a formula. Recalculate after building:
    python3 <xlsx skill>/scripts/recalc.py WYVERN_BOM.xlsx
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "WYVERN_BOM.xlsx")
F = Font(name="Arial", size=10); FB = Font(name="Arial", size=10, bold=True)
FH = Font(name="Arial", size=12, bold=True); BLUE = Font(name="Arial", size=10, color="0000FF")
HDR = PatternFill("solid", fgColor="1F2937"); HDRF = Font(name="Arial", size=10, bold=True, color="FFFFFF")
SEC = PatternFill("solid", fgColor="E5E7EB"); thin = Side(style="thin", color="D1D5DB")
COLS = ["Item", "Vendor", "Part # / Spec", "Link", "Why / where used", "Qty", "Unit ($)", "Line ($)", "Price source"]
WIDTH = [46, 13, 26, 46, 58, 6, 10, 11, 18]

CHK = "vendor 2026-11-02"
ROCKET = [
 ("Avionics", [
  ("Raspberry Pi Pico 2 W (no headers)", "Adafruit", "PID 6087", "https://www.adafruit.com/product/6087", "Rev 4b flight computer (RP2350, radio left off). Leads soldered straight in. 1 flight + 1 spare. Out of stock at Adafruit and SparkFun (DEV-27345, $7.70) on 2026-11-02: if still out, Amazon B0DPF9N1MN is $13.99 in stock", 2, 7.00, f"{CHK}, OUT OF STOCK"),
  ("Adafruit Micro SD SPI or SDIO card breakout, 3 V only", "Adafruit", "PID 4682", "https://www.adafruit.com/product/4682", "Flight log on SPI0, top of the spine's -Y face (25.4 x 22.9 mm, 2.5 g); 1 + spare", 2, 3.50, f"{CHK}, in stock"),
  ("Adafruit BNO085 9-DOF IMU, STEMMA QT", "Adafruit", "PID 4754", "https://www.adafruit.com/product/4754", "Attitude + rates, lowest board on the spine's +X face (Wire)", 1, 29.50, f"{CHK}, in stock"),
  ("Adafruit BMP388 barometric pressure / altimeter, STEMMA QT", "Adafruit", "PID 3966", "https://www.adafruit.com/product/3966", "Primary altimeter, 50 Hz, I2C1 at 0x76 (close its ADDR jumper), spine -Y", 1, 9.95, f"{CHK}, in stock"),
  ("Adafruit BME688 temperature / humidity / pressure, STEMMA QT", "Adafruit", "PID 5046", "https://www.adafruit.com/product/5046", "Pad temperature + humidity for measured air density, I2C1 at 0x77, spine -Y", 1, 19.95, "vendor 2026-11-01, in stock"),
  ("STEMMA QT to male header cable 150 mm", "Adafruit", "PID 4209", "https://www.adafruit.com/product/4209", "BNO085 to I2C0 and BMP388 to I2C1 on the Pico (header pins soldered in) + 1 spare", 3, 0.95, "vendor 2026-10-16, in stock"),
  ("STEMMA QT cable 100 mm", "Adafruit", "PID 4210", "https://www.adafruit.com/product/4210", "BMP388 -> BME688 (both on I2C1)", 1, 0.95, "vendor 2026-10-16, in stock"),
 ]),
 ("Actuation", [
  ("EMAX ES9251 II digital micro servo, 4-pack", "Amazon", "B0DLKJ3MJJ", "https://www.amazon.com/dp/B0DLKJ3MJJ", "18.0 x 7.9 x 16.8 mm, 4 g, 4.5-6.0 V. 4 control fins + 1 for the tunnel cradle + 3 spares (plastic gears)", 2, 28.60, "vendor 2026-11-02, only 5 left"),
 ]),
 ("Power", [
  ("OVONIC 2S 450 mAh 100C LiPo, XT30, 2-pack", "Amazon", "B0D3F5SQ5T", "https://www.amazon.com/dp/B0D3F5SQ5T", "Flight battery + spare (4.2x margin on the 26 min mission). HV-rated: charge to 8.40 V anyway", 1, 20.37, f"{CHK}, in stock"),
  ("OVONIC D15 dual LiPo charger, 1S-3S, 1.2 A", "Amazon", "B0G6CMG9GW", "https://www.amazon.com/dp/B0G6CMG9GW", "Balance-charges the 2S packs", 1, 22.99, f"{CHK}, in stock"),
  ("Adafruit MPM3610 5 V buck, 6-21 V in, 1.2 A", "Adafruit", "PID 4739", "https://www.adafruit.com/product/4739", "One for the Pico (VSYS through the 1N5817), one for the servo rail, 1 spare", 3, 6.95, "vendor 2026-10-22, in stock"),
  ("Pololu Mini MOSFET slide switch LV", "Pololu", "#2810", "https://www.pololu.com/product/2810", "Main power switch in the +Y wall cradle; 1 + spare. No Adafruit / SparkFun part carries 3 A with reverse protection at this size", 2, 4.49, "vendor 2026-10-16"),
  ("1N5817 Schottky diodes 1 A 20 V, 125 pcs", "Amazon", "B0FC2CTR7F", "https://www.amazon.com/dp/B0FC2CTR7F", "5 V buck -> Pico VSYS, so a USB lead on the bench can never back-feed the buck (Pico datasheet's external-supply circuit)", 1, 5.99, CHK),
  ("BOJACK 1 % metal-film resistor kit, 50 values, 1350 pcs", "Amazon", "B07P3MFG5D", "https://www.amazon.com/dp/B07P3MFG5D", "100k / 47k battery divider, 220 ohm LED resistor", 1, 12.99, f"{CHK}"),
 ]),
 ("Propulsion", [
  ("AeroTech Econojet F42-4T single-use 29 x 83 mm, 2-pack", "eRockets", "AER 64204, 4 s delay", "https://www.erockets.biz/aerotech-29mm-composite-model-rocket-motor-single-use-f42-4t-2pk-aer-64204-required-to-pay-for-ups-ground-shipping/", "3 research flights + 1 spare. Not sold by Adafruit / SparkFun / Amazon; UPS ground, continental US", 2, 49.49, "vendor 2026-10-16, stock 4"),
 ]),
 ("Recovery (no Nomex blanket, per your call; see risk R33)", [
  ("Estes 302271 24 in parachute", "Amazon", "B0006NAQ6E", "https://www.amazon.com/dp/B0006NAQ6E", "Main chute, ~6.3 m/s descent at 758 g", 1, 10.79, f"{CHK}, only 1 left"),
  ("9KM DWLIFE braided Kevlar cord", "Amazon", "B0B1WKH21R", "https://www.amazon.com/dp/B0B1WKH21R", "Shock cord, 19 ft tied to the printed anchor. Pick a 300-500 lb option at least 20 ft long (price shown is the listing's default option)", 1, 5.72, f"{CHK}"),
 ]),
 ("Hardware", [
  ("Heat-set insert kit M2-M6, 400 pcs", "Amazon", "B0CLKDPN65", "https://www.amazon.com/dp/B0CLKDPN65", "M2 / M3 inserts in the airframe; tunnel M5 junction rings and M2.5 window tabs", 1, 15.97, "vendor 2026-11-01, in stock"),
 ]),
 ("Filament", [
  ("Bambu ASA-Aero 1.75 mm, 1 kg", "Amazon", "B0HD6ZT4HZ", "https://www.amazon.com/dp/B0HD6ZT4HZ", "Nose, recovery bay, control tube, motor bay (141 g per airframe; room for a full reprint)", 1, 58.99, f"{CHK}, only 11 left"),
  ("kexcelled flame-retardant PC (PC-FR) 1.75 mm, 1 kg, UL94 V0", "Amazon", "B0FN8366S3", "https://www.amazon.com/dp/B0FN8366S3", "Hot-gas parts: RB-floor coupler, plenum, motor mount, retainer, bypass tube (90 g per set)", 1, 49.99, CHK),
 ]),
 ("Assembly consumables", [
  ("Permatex 81630 Ultra Red high-temp RTV, 3 oz", "Amazon", "B08CRY2BJB", "https://www.amazon.com/dp/B08CRY2BJB", "Bypass-tube sockets", 1, 7.56, CHK),
 ]),
 ("Tools", [
  ("LR44 / AG13 / SR44 button cells, 24 pcs", "Amazon", "B0FLJQCND9", "https://www.amazon.com/dp/B0FLJQCND9", "Battery for your digital calipers (most 6 in calipers take one LR44 / SR44; check the cover)", 1, 6.79, CHK),
  ("Heat-set insert soldering tips M2-M8, 7 pcs", "Amazon", "B0FYGXGSYB", "https://www.amazon.com/dp/B0FYGXGSYB", "Installing M2 / M3 / M5 inserts (check the tip thread matches the iron)", 1, 5.99, CHK),
 ]),
 ("Launch equipment (you own the rail)", [
  ("Estes 2240 Pro Series II launch controller", "Amazon", "B00FU4AX44", "https://www.amazon.com/dp/B00FU4AX44", "Remote ignition from the safe distance", 1, 42.77, f"{CHK}, in stock"),
 ]),
]
TUNNEL = [
 ("Airflow", [
  ("6 in inline duct fan, 405 CFM, EC motor, 0-100 % speed controller", "Amazon", "B08JZM1KHX", "https://www.amazon.com/dp/B08JZM1KHX", "Tunnel drive on the printed 100 sq -> 6 in transition", 1, 64.99, "vendor 2026-11-01, only 3 left"),
  ("AC Infinity stainless duct clamps 6 in, 2-pack", "Amazon", "B07L4S62Q6", "https://www.amazon.com/dp/B07L4S62Q6", "Clamps the transition socket onto the fan collar", 1, 7.99, "vendor 2026-11-01"),
  ("40 mesh 304 stainless woven mesh, 2 x 31 x 115 cm", "Amazon", "B0BBMTDK88", "https://www.amazon.com/dp/B0BBMTDK88", "Coarse turbulence screen, laid into Jerrod's screen frame at the print pause", 1, 15.99, "vendor 2026-11-01, only 1 left"),
  ("80 mesh 304 stainless woven mesh, 5 x 20 x 30 cm", "Amazon", "B09VNKDS9R", "https://www.amazon.com/dp/B09VNKDS9R", "Fine turbulence screen (second frame)", 1, 7.99, "vendor 2026-11-01, in stock"),
 ]),
 ("Balance (fin force)", [
  ("ShangHJ 1 kg bar load cell + HX711 module, 2 sets", "Amazon", "B09K7G51KJ", "https://www.amazon.com/dp/B09K7G51KJ", "Two cells under the servo cradle, 60 mm apart along the chord: normal force (sum) and chordwise CP (difference); one HX711 each, VCC to the Metro's 3.3 V. Red E+, black E-, green A+, white A-", 1, 9.99, f"{CHK}, in stock"),
  ("Bekith precision calibration weights, 10 mg-100 g, 17 pcs", "Amazon", "B07K7F7D8K", "https://www.amazon.com/dp/B07K7F7D8K", "Thread-and-pulley calibration of both cells (stay under 100 g)", 1, 8.99, "vendor 2026-11-01, in stock"),
  ("uxcell MR105ZZ bearings 5 x 10 x 4 mm, 10 pcs", "Amazon", "B0DP7FYPDV", "https://www.amazon.com/dp/B0DP7FYPDV", "Presses into the printed calibration pulley wheel", 1, 8.39, "vendor 2026-11-01, only 15 left"),
 ]),
 ("Fin-angle measurement (AS5600 on a printed 2:1 gear train)", [
  ("Adafruit AS5600 magnetic angle sensor, STEMMA QT", "Adafruit", "PID 6357", "https://www.adafruit.com/product/6357", "Reads the 20 T sensor gear's magnet, 12 bit, 0.044 deg per count at the fin after the 2:1 gearing; daisy-chained off the BME688 (0x36)", 1, 5.95, f"{CHK}, in stock"),
  ("Diametrically magnetized NdFeB disc 6 x 2.5 mm, 50 pcs", "Amazon", "B0H1578MWG", "https://www.amazon.com/dp/B0H1578MWG", "Glued into the sensor gear's pocket, 1.5 mm under the AS5600 chip (diametric: N and S on opposite edges, not faces)", 1, 20.98, CHK),
  ("STEMMA QT cable 100 mm", "Adafruit", "PID 4210", "https://www.adafruit.com/product/4210", "BME688 -> AS5600", 1, 0.95, "vendor 2026-10-16, in stock"),
 ]),
 ("Controller and wiring (the servo comes from the Rocket 4-packs)", [
  ("Adafruit Metro M4 feat. Microchip ATSAMD51", "Adafruit", "PID 3382", "https://www.adafruit.com/product/3382", "Tunnel controller (wt_balance_daq v3.0, Arduino IDE): servo, both HX711s, BME688", 1, 27.50, "vendor 2026-11-01, 17 in stock"),
  ("Adafruit BME688 temperature / humidity / pressure, STEMMA QT", "Adafruit", "PID 5046", "https://www.adafruit.com/product/5046", "Room air density for q (a second unit; the flight one stays in the rocket)", 1, 19.95, "vendor 2026-11-01, in stock"),
  ("STEMMA QT to male header cable 150 mm", "Adafruit", "PID 4209", "https://www.adafruit.com/product/4209", "BME688 to the Metro's SDA / SCL header", 1, 0.95, "vendor 2026-10-16, in stock"),
  ("Female DC power adapter, 2.1 mm jack to screw terminal", "Adafruit", "PID 368", "https://www.adafruit.com/product/368", "Breaks the 5 V supply out to the servo lead and the Metro GND", 1, 2.00, "vendor 2026-11-02, in stock"),
  ("5 V 3 A wall power supply, 5.5 x 2.1 mm plug, UL listed", "Amazon", "B09JW38H3X", "https://www.amazon.com/dp/B09JW38H3X", "Servo power (4.5-6 V servo, no LiPo in the tunnel)", 1, 8.95, "vendor 2026-11-02"),
 ]),
 ("Airspeed and test section", [
  ("Jadeshay differential pitot tube kit with silicone hose", "Amazon", "B07Q6126B6", "https://www.amazon.com/dp/B07Q6126B6", "Total + static ports upstream of the fin, to the printed inclined manometer", 1, 10.39, "vendor 2026-11-01, only 9 left"),
  ("DERNORD clear PVC tubing 1/8 in ID x 1/4 in OD, 25 ft", "Amazon", "B0D2CR3322", "https://www.amazon.com/dp/B0D2CR3322", "Manometer leg in the 1:10 ramp + pitot lines", 1, 9.99, "vendor 2026-11-01, in stock"),
  ("Clear acrylic sheet 3 mm, 12 x 12 in, 5-pack", "Amazon", "B0GY1GB12W", "https://www.amazon.com/dp/B0GY1GB12W", "Test-section windows to watch the tufts", 1, 18.99, "vendor 2026-11-01, in stock"),
 ]),
]
OPTIONAL_VIS = [
 ("Smoke + laser sheet (optional: tufts already cover the RQ data)", [
  ("COLBOR CF3 30 W portable fog machine", "Amazon", "B0FW4VQ72H", "https://www.amazon.com/dp/B0FW4VQ72H", "Smoke source for Jerrod's rake", 1, 89.00, "your link, 2026-10-21"),
  ("COLBOR fog fluid for CF3 / CF5 (2 fl oz x 4)", "Arts Cameras", "COLBOR CF fluid", "https://artscameras.com/products/colbor-fluid-for-cf3-cf5-fog-machine-2-fl-oz-4-pack", "Only if the CF3 box has none", 1, 25.90, "vendor 2026-10-21"),
  ("520 nm focusable green line laser module", "Amazon", "B0CKP4SYL7", "https://www.amazon.com/dp/B0CKP4SYL7", "Laser sheet on the X/Y gantry", 1, 39.00, "your link"),
  ("SmallRig P96L RGB video light", "Amazon", "B09G98NRQZ", "https://www.amazon.com/dp/B09G98NRQZ", "LED ceiling module; any lamp works for tufts", 1, 30.60, "your link"),
  ("Loc-Line 40413 hose sample kit (1/4 in)", "Amazon", "B0GZL8N636", "https://www.amazon.com/dp/B0GZL8N636", "Smoke wand plumbing", 1, 25.00, "your link"),
  ("Magnets 6 x 2 mm (250) and 10 x 3 mm (50)", "Amazon", "B0DBVJF1G2 / B0BVY5VYQY", "https://www.amazon.com/dp/B0DBVJF1G2", "Only Jerrod's smoke-rake ports and Gridfinity floor use them; Phase A uses the wall panel", 2, 9.99, "your links"),
 ]),
]
COLS = ["Item", "Vendor", "Part # / Spec", "Link", "Why / where used", "Qty", "Unit ($)", "Line ($)", "Price source"]
TOP = PatternFill("solid", fgColor="374151"); TOPF = Font(name="Arial", size=11, bold=True, color="FFFFFF")

wb = Workbook(); ws = wb.active; ws.title = "BOM"
ws["A1"] = "GTR70E WYVERN — bill of materials (rev 4)"; ws["A1"].font = FH
ws["A2"] = ("To buy. Already owned (not listed): solder, wire, capacitors, heat-shrink, epoxy, Kapton, cable ties, foam tape, ballast BBs, CA, USB data cable, LiPo bags, "
            "soldering iron, multimeter, calipers, strippers, flush cutters, hot glue gun, scale, the launch rail, servo extensions, jumpers, PETG, PETG-CF, XT30s, microSD cards, LEDs, perfboard, "
            "6 mm buttons, thread, M2-M5 screws. No angle gauge: the AS5600 rig and the printed fin zero jigs replace it. "
            "Shared items are bought once under Rocket. The ejection ground-test charge comes from your club / mentor.")
ws["A2"].font = Font(name="Arial", size=9, italic=True, color="4B5563")
for i, (c, w) in enumerate(zip(COLS, WIDTH), 1):
    cell = ws.cell(row=4, column=i, value=c); cell.font = HDRF; cell.fill = HDR
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A5"
r = 5; totals = {}
for top, sections in (("ROCKET", ROCKET), ("WIND TUNNEL", TUNNEL), ("FLOW-VIS", OPTIONAL_VIS)):
    ws.cell(row=r, column=1, value=top).font = TOPF
    for c in range(1, 10): ws.cell(row=r, column=c).fill = TOP
    r += 1; subs = []
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
        ws.cell(row=r, column=7, value="Subtotal").font = F
        c = ws.cell(row=r, column=8, value=f"=SUM(H{first}:H{r-1})"); c.font = F; c.number_format = "$#,##0.00"
        subs.append(f"H{r}"); r += 1
    ws.cell(row=r, column=7, value=f"{top.title()} total").font = FB
    c = ws.cell(row=r, column=8, value="=" + "+".join(subs)); c.font = FB; c.number_format = "$#,##0.00"
    totals[top] = f"H{r}"; r += 2
summary = [("Rocket", f"={totals['ROCKET']}"), ("Wind Tunnel", f"={totals['WIND TUNNEL']}"), ("Flow-Vis", f"={totals['FLOW-VIS']}"),
           ("Rocket + Wind Tunnel", f"={totals['ROCKET']}+{totals['WIND TUNNEL']}"),
           ("Everything (incl. Flow-Vis)", f"={totals['ROCKET']}+{totals['WIND TUNNEL']}+{totals['FLOW-VIS']}")]
ws.cell(row=r, column=1, value="SUMMARY").font = TOPF
for c in range(1, 10): ws.cell(row=r, column=c).fill = TOP
r += 1
for a, f in summary:
    ws.cell(row=r, column=7, value=a).font = FB if "+" in a or "Every" in a else F
    c = ws.cell(row=r, column=8, value=f); c.font = FB if "+" in a or "Every" in a else F; c.number_format = "$#,##0.00"
    r += 1
r += 1
ws.cell(row=r, column=1, value="Blue = inputs (qty, unit price); line, subtotals and totals are formulas. Stores: Adafruit, SparkFun, Amazon, except the 2810 (Pololu), motors (eRockets), the Nomex blanket (Fruity Chutes) and fog fluid (Arts Cameras, only if the CF3 ships without it).").font = Font(name="Arial", size=9, italic=True)
wb.save(OUT); print("wrote", OUT)
