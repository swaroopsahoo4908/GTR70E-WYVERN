#!/usr/bin/env python3
"""Standalone wind-tunnel BOM (Phase A, one servo) -> WYVERN_WindTunnel_BOM.xlsx.
Everything needed to start building the tunnel rig, sorted by storefront, with what is already owned.
Prices and stock were checked on the vendor pages on 2026-11-01. Recalculate with the xlsx skill's
recalc.py after building."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "WYVERN_WindTunnel_BOM.xlsx")
CHK = "2026-11-01"
F = "Arial"
BLUE = Font(name=F, size=10, color="0000FF")
BLK = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
HEAD = Font(name=F, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=F, size=13, bold=True)
NOTE = Font(name=F, size=9, italic=True, color="555555")
HFILL = PatternFill("solid", fgColor="404040")
SFILL = PatternFill("solid", fgColor="E7E6E6")
YFILL = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
USD = '$#,##0.00;($#,##0.00);"-"'
WRAP = Alignment(wrap_text=True, vertical="top")

# (item, part no., link, role, qty needed, qty on hand, unit price or None, checked/stock, note)
STORES = [
 ("Adafruit", [
  ("Adafruit Metro M4 feat. Microchip ATSAMD51", "PID 3382", "https://www.adafruit.com/product/3382",
   "The one tunnel controller: servo, both HX711s, BME688, CSV over USB (wt_balance_daq v3.0)", 1, 0, 27.50, f"{CHK}, 17 in stock",
   "Set 'on hand' to 1 if you already own one. Micro-USB, 3.3 V logic"),
  ("STEMMA QT to male header cable, 150 mm", "PID 4209", "https://www.adafruit.com/product/4209",
   "BME688 to the Metro's SDA / SCL / 3.3V / GND header (the Metro has no STEMMA QT port)", 1, 0, 0.95, "2026-10-16, in stock", ""),
  ("Adafruit BME688 temperature / humidity / pressure / gas, STEMMA QT", "PID 5046", "https://www.adafruit.com/product/5046",
   "Room temperature, pressure, humidity -> air density for q", 1, 0, 19.95, f"{CHK}, in stock", ""),
  ("Female DC power adapter, 2.1 mm jack to screw terminal", "PID 368", "https://www.adafruit.com/product/368",
   "Breaks the 5 V supply out to the servo lead and the Metro GND", 1, 0, 2.00, f"{CHK}, in stock", ""),
 ]),
 ("SparkFun", [
  ("Mini load cell 100 g, straight bar (TAL221)", "SEN-14727", "https://www.sparkfun.com/mini-load-cell-100g-straight-bar-tal221.html",
   "Two under the servo cradle, 60 mm apart: normal force (sum) and chordwise CP (difference)", 2, 0, 14.50, f"{CHK}, in stock",
   "Four M3 through-holes per cell"),
  ("SparkFun Load Cell Amplifier - HX711", "SEN-13879", "https://www.sparkfun.com/sparkfun-load-cell-amplifier-hx711.html",
   "One per TAL221 (gain 128); separate VCC and VDD pins, both to the Metro's 3.3V", 2, 0, 4.95, f"{CHK}, in stock", ""),
 ]),
 ("Amazon", [
  ("6 in inline duct fan, 405 CFM, EC motor, 0-100 % speed controller", "B08JZM1KHX", "https://www.amazon.com/dp/B08JZM1KHX",
   "Tunnel drive, on the printed 100 sq -> 6 in transition (drive option A, see 'Drive Options')", 1, 0, 64.99, f"{CHK}, only 3 left",
   "EC motor holds speed better than an AC fan; if it sells out, any 6 in EC inline fan with a speed controller fits the same transition"),
  ("AC Infinity stainless duct clamps 6 in, 2-pack", "B07L4S62Q6", "https://www.amazon.com/dp/B07L4S62Q6",
   "Clamps the printed transition's socket onto the fan collar", 1, 0, 7.99, CHK, ""),
  ("40 mesh 304 stainless woven mesh, 2 x 31 x 115 cm", "B0BBMTDK88", "https://www.amazon.com/dp/B0BBMTDK88",
   "Coarse turbulence screen (embed in Jerrod's Screen Frame at the print pause)", 1, 0, 15.99, f"{CHK}, only 1 left", ""),
  ("80 mesh 304 stainless woven mesh, 5 x 20 x 30 cm", "B09VNKDS9R", "https://www.amazon.com/dp/B09VNKDS9R",
   "Fine turbulence screen (second Screen Frame)", 1, 0, 7.99, f"{CHK}, in stock", ""),
  ("Jadeshay differential pitot tube kit with silicone hose", "B07Q6126B6", "https://www.amazon.com/dp/B07Q6126B6",
   "Total + static ports upstream of the fin; hoses go to the printed manometer", 1, 0, 10.39, f"{CHK}, only 9 left",
   "Use the pitot and hose; the dial gauge in the kit is not needed"),
  ("DERNORD clear PVC tubing 1/8 in ID x 1/4 in OD, 25 ft", "B0D2CR3322", "https://www.amazon.com/dp/B0D2CR3322",
   "Manometer leg in the 1:10 ramp groove, plus pitot lines", 1, 0, 9.99, f"{CHK}, in stock", ""),
  ("Clear acrylic sheet 3 mm, 12 x 12 in, 5-pack", "B0GY1GB12W", "https://www.amazon.com/dp/B0GY1GB12W",
   "Test-section windows (80 x 130 mm) to watch the tufts; spares", 1, 0, 18.99, f"{CHK}, in stock", ""),
  ("JR servo extension leads, 30 cm, 10-pack", "B07NJB58XC", "https://www.amazon.com/dp/B07NJB58XC",
   "Reaches from the cradle to the Metro; cut one to break out servo +/- to the 5 V terminal", 1, 0, 8.99, f"{CHK}, only 19 left", ""),
  ("ELEGOO Dupont jumper wires, 120 pcs (M-F, M-M, F-F)", "B01EV70C78", "https://www.amazon.com/dp/B01EV70C78",
   "HX711 and BME688 to the Metro headers", 1, 0, 6.98, f"{CHK}, in stock", ""),
  ("GemRed DAG-V1 digital angle gauge", "B00WQLHG2G", "https://www.amazon.com/dp/B00WQLHG2G",
   "Checks 0 and +/-10 deg fin deflection before each session", 1, 0, 19.99, f"{CHK}, in stock",
   "Also on the flight BOM: buy once"),
  ("Mywish M2-M5 stainless screw and nut kit, 1290 pcs", "B0CQWYFTXC", "https://www.amazon.com/dp/B0CQWYFTXC",
   "M3 for cells / cradle / panel, M5 pulley axle", 1, 0, 17.99, f"{CHK}, in stock",
   "Also on the flight BOM: buy once"),
  ("EMAX ES9251 II digital micro servo (single)", "B07R3S2NBY", "https://www.amazon.com/dp/B07R3S2NBY",
   "Drives the half-model fin in the cradle with the flight hub, so every test fin fits unchanged", 1, 0, 13.95, f"{CHK}, in stock",
   "Rev 3f flight servo too: if you buy the flight 4-packs, take one from there and set on-hand to 1"),
  ("5 V 3 A wall power supply, 5.5 x 2.1 mm plug, UL listed", "B09JW38H3X", "https://www.amazon.com/dp/B09JW38H3X",
   "Servo power: the ES9251 II runs on 4.5-6 V, so no LiPo in the tunnel", 1, 0, 8.95, f"{CHK}", ""),
  ("Bekith precision calibration weights, 10 mg-100 g, 17 pcs", "B07K7F7D8K", "https://www.amazon.com/dp/B07K7F7D8K",
   "Thread-and-pulley calibration of both cells, 5 loads up and down (stay under the 100 g cell rating)", 1, 0, 8.99, f"{CHK}, in stock", ""),
  ("uxcell MR105ZZ bearings 5 x 10 x 4 mm, 10 pcs", "B0DP7FYPDV", "https://www.amazon.com/dp/B0DP7FYPDV",
   "Presses into the printed calibration pulley wheel", 1, 0, 8.39, f"{CHK}, only 15 left", ""),
  ("Heat-set insert kit M2-M6, 400 pcs", "B0CLKDPN65", "https://www.amazon.com/dp/B0CLKDPN65",
   "M5 junction rings and M2.5 window tabs on Jerrod's tunnel", 1, 0, 15.97, f"{CHK}, in stock", ""),
 ]),
 ("Filament and basic essentials (no purchase)", [
  ("PETG filament (~5.5 kg) and PETG-CF (~0.3 kg)", "", "", "Jerrod's tunnel modules + WTA parts; 20 test fins + hub in PETG-CF", 1, 1, None, "owned", "See 'Printed Parts'"),
  ("Sewing thread, tape, water + food colouring, micro-USB cable, laptop", "", "", "Tufts, calibration thread, manometer fluid, Metro link", 1, 1, None, "household", ""),
 ]),
]

DRIVE_B = [  # BLDC option, Amazon, checked 2026-11-01
  ("Flycolor 30 A ESC, 2-4S, 5 V BEC, XT60", "B0C2Z15C2B", "https://www.amazon.com/dp/B0C2Z15C2B", 1, 16.99, f"{CHK}, in stock"),
  ("12 V 10 A (120 W) power supply, 5.5 x 2.1 mm plug", "B0G31W3J97", "https://www.amazon.com/dp/B0G31W3J97", 1, 24.99, CHK),
  ("XT60 female to 5.5 x 2.1 mm female cable, 14 AWG", "B0G6T5YMDJ", "https://www.amazon.com/dp/B0G6T5YMDJ", 1, 4.99, CHK),
  ("Gemfan Hurricane 6045 3-blade props, 8 pcs", "B0CL9VLQT9", "https://www.amazon.com/dp/B0CL9VLQT9", 1, 18.98, f"{CHK}, only 3 left"),
]

def hdr(ws, row, cols, widths=None):
    for j, c in enumerate(cols, 1):
        x = ws.cell(row=row, column=j, value=c); x.font = HEAD; x.fill = HFILL; x.alignment = WRAP; x.border = BOX
    if widths:
        for j, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(j)].width = w

wb = Workbook()

# ------------------------------------------------------------------ BOM by Storefront
ws = wb.active; ws.title = "BOM by Storefront"
ws["A1"] = "GTR70E WYVERN wind tunnel, Phase A (one servo): everything to start building"; ws["A1"].font = TITLE
ws["A2"] = ("Blue cells are inputs: change 'Qty on hand' for anything you already own and the to-buy totals update. "
            f"Prices and stock checked on the vendor pages {CHK}.")
ws["A2"].font = NOTE
cols = ["Store", "Item", "Part no. / ASIN", "Link", "Role in the tunnel", "Qty needed", "Qty on hand", "Qty to buy",
        "Unit price", "Line total", "Price / stock checked", "Notes"]
hdr(ws, 4, cols, [12, 44, 14, 40, 52, 9, 9, 9, 11, 11, 20, 46])
r = 5; sub_cells = {}
for store, items in STORES:
    c = ws.cell(row=r, column=1, value=store); c.font = BOLD
    for j in range(1, 13): ws.cell(row=r, column=j).fill = SFILL
    r += 1; first = r
    for it, pn, link, role, need, have, price, chk, note in items:
        vals = [store, it, pn, link, role, need, have, None, price, None, chk, note]
        for j, v in enumerate(vals, 1):
            x = ws.cell(row=r, column=j, value=v); x.font = BLK; x.alignment = WRAP; x.border = BOX
        ws.cell(row=r, column=6).font = BLUE; ws.cell(row=r, column=7).font = BLUE
        ws.cell(row=r, column=8, value=f"=MAX(0,F{r}-G{r})")
        if price is not None: ws.cell(row=r, column=9).font = BLUE
        ws.cell(row=r, column=9).number_format = USD
        ws.cell(row=r, column=10, value=f"=H{r}*N(I{r})").number_format = USD
        if link: ws.cell(row=r, column=4).hyperlink = link
        r += 1
    last = r - 1
    ws.cell(row=r, column=9, value=f"{store} subtotal").font = BOLD
    ws.cell(row=r, column=10, value=f"=SUM(J{first}:J{last})").number_format = USD
    ws.cell(row=r, column=10).font = BOLD
    sub_cells[store] = f"J{r}"; r += 2
ws.cell(row=r, column=9, value="TOTAL to buy").font = BOLD
ws.cell(row=r, column=10, value="=" + "+".join(sub_cells.values())).number_format = USD
ws.cell(row=r, column=10).font = BOLD; ws.cell(row=r, column=10).fill = YFILL
total_cell = f"'BOM by Storefront'!J{r}"
r += 2
ws.cell(row=r, column=1, value=("Shared with the flight BOM (buy once): angle gauge, screw kit, and the servo if you order the flight "
                                "ES9251 II 4-packs. Set their 'Qty on hand' to 1 once the flight order lands.")).font = NOTE
ws.freeze_panes = "C5"

# ------------------------------------------------------------------ Drive options
wd = wb.create_sheet("Drive Options")
wd["A1"] = "Tunnel drive: three ways to pull air through the 100 x 100 mm section"; wd["A1"].font = TITLE
wd["A2"] = ("Speeds are estimates from each fan's free-air rating against a tunnel loss of about 0.85 x the test-section dynamic "
            "pressure (screens, contraction, transition); treat them as +/-30 %. The pitot and manometer measure the real value.")
wd["A2"].font = NOTE
hdr(wd, 4, ["Option", "Drive", "Est. test-section speed", "Electrical power", "Speed control", "Steadiness over a 3-min sweep",
            "Parts cost", "Printed parts", "Verdict"], [8, 34, 14, 14, 26, 30, 11, 34, 50])
opts = [
 ("A", "6 in EC inline fan, 405 CFM (B08JZM1KHX)", "~12 m/s", "60 W, mains", "0-100 % knob", "Good: EC motor holds its speed",
  "='BOM by Storefront'!J{a1}+'BOM by Storefront'!J{a2}", "100 sq -> 6 in transition (done)",
  "Recommended default. Smaller than the 8 in, quiet, plugs into the wall, and fast enough for the RQ (12-46 mN fin loads)."),
 ("B", "Your BLDC motor + 6 in prop in a printed 6 in shroud", "~15-20 m/s", "60-110 W from a 12 V brick", "Metro PWM -> ESC (programmable)",
  "Good on a mains brick; poor on a LiPo (voltage sag)", "=G12", "Same 6 in transition + a motor shroud (needs your motor's size)",
  "Smallest and fastest, and the Metro can set the throttle itself. Needs the motor's model / KV before it can be specified; louder, and the prop needs a guard."),
 ("C", "8 in AC inline fan, 750 CFM (VEVOR B0BV1ND9MB, $54.45)", "~16 m/s", "126 W, mains", "Knob", "Fair: AC speed drifts with line voltage",
  54.45 + 7.99, "Needs the old 100 sq -> 8 in transition back (250 mm, larger print)",
  "Most flow of the duct fans but the biggest unit; only worth it if you want speed without the BLDC."),
]
# row numbers of the fan + clamp in the BOM sheet
amz_rows = [i for i in range(1, ws.max_row + 1) if ws.cell(row=i, column=3).value in ("B08JZM1KHX", "B07L4S62Q6")]
for k, o in enumerate(opts):
    rr = 5 + k
    for j, v in enumerate(o, 1):
        if isinstance(v, str) and v.startswith("='BOM"):
            v = v.format(a1=amz_rows[0], a2=amz_rows[1])
        x = wd.cell(row=rr, column=j, value=v); x.font = BLK; x.alignment = WRAP; x.border = BOX
    wd.cell(row=rr, column=7).number_format = USD
wd.cell(row=9, column=1, value="Option B parts (only if you go with the BLDC; motor already owned)").font = BOLD
hdr(wd, 10, ["", "Item", "ASIN", "Link", "Qty", "Unit price", "Line total", "Checked", ""])
for k, (it, asin, link, q, p, chk) in enumerate(DRIVE_B):
    rr = 11 + k
    vals = ["", it, asin, link, q, p, f"=E{rr}*F{rr}", chk, ""]
    for j, v in enumerate(vals, 1):
        x = wd.cell(row=rr, column=j, value=v); x.font = BLK; x.alignment = WRAP; x.border = BOX
    wd.cell(row=rr, column=5).font = BLUE; wd.cell(row=rr, column=6).font = BLUE
    wd.cell(row=rr, column=6).number_format = USD; wd.cell(row=rr, column=7).number_format = USD
    wd.cell(row=rr, column=4).hyperlink = link
endB = 11 + len(DRIVE_B) - 1
# Option B parts cost lives in G12? put a subtotal and point the option row at it
sb = endB + 1
wd.cell(row=sb, column=6, value="Option B subtotal").font = BOLD
wd.cell(row=sb, column=7, value=f"=SUM(G11:G{endB})").number_format = USD
wd.cell(row=sb, column=7).font = BOLD
wd.cell(row=6, column=7, value=f"=G{sb}")
wd.cell(row=sb + 2, column=1, value=("Option B swaps out the fan and its clamps (keep one 6 in clamp for the shroud). The props suit 2306-2806 "
                                      "class motors with a 5 mm shaft; confirm against your motor before ordering. Use the 12 V brick, "
                                      "not a LiPo, so the speed does not sag during a sweep.")).font = NOTE
wd.cell(row=sb + 3, column=1, value=("Speed estimate method: fan curve taken as linear from max static pressure (0.6 x 0.5 rho U_tip^2) to the "
                                      "free-air rating, intersected with a system curve p = 0.85 x 0.5 rho V^2; V = Q / 0.01 m^2.")).font = NOTE

# ------------------------------------------------------------------ Printed parts
wp = wb.create_sheet("Printed Parts")
wp["A1"] = "What to print (filament is owned)"; wp["A1"].font = TITLE
hdr(wp, 3, ["Part", "File", "Material", "Qty", "Approx. mass each (g)", "Notes"], [44, 58, 10, 6, 12, 60])
P = [
 ("Inlet bell", "Wind Tunnel/STEM...stls/Body1.stl", "PETG", 1, None, "Jerrod H, unchanged"),
 ("Honeycomb / basic duct section", "3 - Basic Duct Section.stl", "PETG", 1, None, "Jerrod H, unchanged"),
 ("Screen frames", "Screen Frame (pause to embed mesh).stl", "PETG", 2, None, "Pause the print and lay in the 40 mesh (one) and 80 mesh (other)"),
 ("4:1 contraction", "Body4.stl", "PETG", 1, None, "Jerrod H, unchanged"),
 ("Test-section frame", "6 - Test Section Frame.stl", "PETG", 1, None, "Takes the acrylic windows"),
 ("Junction rings, large (4-piece)", "Junction Ring - Large - 4pc.stl", "PETG", 20, None, "Counts as exported in Jerrod's file"),
 ("Junction rings, small (2-piece)", "Junction Ring - Small - 2pc.stl", "PETG", 4, None, ""),
 ("Test-section quick-release latches", "Test Section Quick-Release Latch.stl", "PETG", 16, None, ""),
 ("Stand feet and crossbars", "Stand Foot / Stand Crossbar (upstream + test section)", "PETG", 16, None, "4 of each of the four parts"),
 ("Reflection-plane wall panel", "3D parts/wind_tunnel/WTA_reflection_plane_wall_panel_PETG.stl", "PETG", 1, 88.6, "Replaces one test-section side wall; check the corner holes against Jerrod's part 4"),
 ("Servo balance cradle", "WTA_servo_balance_cradle_PETG.stl", "PETG", 1, 19.1, "Sits on the two TAL221s"),
 ("Transition, 100 sq -> 6 in round", "WTA_diffuser_100sq_to_6in_round_PETG.stl", "PETG", 1, 341.1, "190 x 158 x 158 mm; replaces Jerrod's diffuser, extension and fan guard"),
 ("Inclined manometer ramp + lid", "WTA_inclined_manometer_ramp_PETG.stl / _lid_PETG.stl", "PETG", 1, 174.6, "1:10 ramp, 40 mm reservoir"),
 ("Calibration pulley wheel + bracket", "WTA_calibration_pulley_wheel_PETG.stl / _bracket_PETG.stl", "PETG", 1, 23.0, "New: MR105 presses into the wheel, M5 axle in the bracket slot"),
 ("Servo hub", "3D parts/flight/06_servo_hub_PETGCF_x4.stl", "PETG-CF", 1, None, "Print one of the flight hub"),
 ("Test fins: 4 sections x 5 heights", "3D parts/control_fins/<section>/cfin_<section>_H20..H40_PETGCF.stl", "PETG-CF", 20, None, "100 % infill, flat on the bed; caliper the thickness at 3 chord stations"),
]
for k, row in enumerate(P):
    for j, v in enumerate(row, 1):
        x = wp.cell(row=4 + k, column=j, value=v); x.font = BLK; x.alignment = WRAP; x.border = BOX
wp.cell(row=5 + len(P), column=1, value="Skip from Jerrod's set: 7 - Diffuser, 8 - Diffuser Extension, 9 - Fan Guard, the half-span wall, and the model bases / LED / laser / smoke parts.").font = NOTE

# ------------------------------------------------------------------ Wiring
ww = wb.create_sheet("Metro M4 Wiring")
ww["A1"] = "Metro M4 pin map (matches wt_balance_daq v3.0)"; ww["A1"].font = TITLE
hdr(ww, 3, ["From", "Pin / wire", "To (Metro M4 header)", "Note"], [22, 18, 24, 60])
W = [
 ("Fore HX711", "VCC / VDD", "3.3V", "VDD to 3.3 V keeps DT at 3.3 V logic"),
 ("Fore HX711", "GND", "GND", ""), ("Fore HX711", "DT", "D2", ""), ("Fore HX711", "SCK", "D3", ""),
 ("Aft HX711", "VCC / VDD", "3.3V", ""), ("Aft HX711", "GND", "GND", ""), ("Aft HX711", "DT", "D4", ""), ("Aft HX711", "SCK", "D5", ""),
 ("BME688", "VIN / GND", "3.3V / GND", "STEMMA QT to male header cable"), ("BME688", "SDA / SCL", "SDA / SCL", "The I2C pins next to AREF"),
 ("EMAX ES9251 II", "Signal (orange)", "D9", "Through a 30 cm extension"),
 ("EMAX ES9251 II", "+ (red)", "5 V supply + (screw terminal)", "Never from the Metro's 5 V pin, never from a 2S LiPo"),
 ("EMAX ES9251 II", "- (brown)", "5 V supply - and Metro GND", "Common ground for the signal"),
 ("TAL221 (each)", "Red / Black / White / Green", "E+ / E- / A- / A+ on its HX711", "If a cell reads negative under load, swap A- and A+"),
]
for k, row in enumerate(W):
    for j, v in enumerate(row, 1):
        x = ww.cell(row=4 + k, column=j, value=v); x.font = BLK; x.alignment = WRAP; x.border = BOX

# ------------------------------------------------------------------ Summary (first)
s = wb.create_sheet("Summary", 0)
s["A1"] = "Wind-tunnel BOM summary"; s["A1"].font = TITLE
s["A2"] = f"Phase A, one servo, drive option A, assuming nothing is owned except filament and basic essentials. Prices checked {CHK}."; s["A2"].font = NOTE
hdr(s, 4, ["Store", "To buy"], [42, 14])
k = 5
for store, cell in sub_cells.items():
    s.cell(row=k, column=1, value=store).font = BLK
    s.cell(row=k, column=2, value=f"='BOM by Storefront'!{cell}").number_format = USD
    k += 1
s.cell(row=k, column=1, value="Total to buy").font = BOLD
s.cell(row=k, column=2, value=f"={total_cell}").number_format = USD
s.cell(row=k, column=2).font = BOLD; s.cell(row=k, column=2).fill = YFILL
s.cell(row=k + 2, column=1, value="Change in total if you build option B (BLDC) instead").font = BLK
s.cell(row=k + 2, column=2, value=f"='Drive Options'!G{sb}-'BOM by Storefront'!J{amz_rows[0]}").number_format = USD
s.cell(row=k + 3, column=1, value="(option B parts minus the 6 in fan; keep the clamps for the shroud)").font = NOTE

wb.save(OUT); print("wrote", OUT)
