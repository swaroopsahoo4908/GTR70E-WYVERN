#!/usr/bin/env python3
"""
Generate XRIM-117 CCM KiCAD 7 Schematic
PDR-002 Rev A | RP2040 + ICM-42688-P + BMP388 + E22-900M22S LoRa + 3x Pyro
62mm Circular 2-Layer FR4 ENIG
"""

import uuid as _uuid_mod

_uid_counter = [0]

def u():
    return str(_uuid_mod.uuid4())

# ─── LOW-LEVEL S-EXPR HELPERS ─────────────────────────────────────────────────

def _indent(s, n=2):
    pad = ' ' * n
    return '\n'.join(pad + l if l.strip() else l for l in s.split('\n'))

def pin_def(name, num, x, y, angle, ptype="bidirectional", style="line"):
    return (f'(pin {ptype} {style} (at {x:.3f} {y:.3f} {angle}) (length 2.54)\n'
            f'  (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'  (number "{num}" (effects (font (size 1.27 1.27))))\n'
            f')')

def rect_def(x1, y1, x2, y2, lw=0.254):
    return (f'(rectangle (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'  (stroke (width {lw}) (type default))\n'
            f'  (fill (type background))\n'
            f')')

def prop_def(key, val, x, y, angle=0, hide=False, bold=False, size=1.27):
    hide_str = ' (hide yes)' if hide else ''
    bold_str = ' bold' if bold else ''
    return (f'(property "{key}" "{val}" (at {x:.3f} {y:.3f} {angle})\n'
            f'  (effects (font (size {size} {size}){bold_str}){hide_str})\n'
            f')')

# ─── LIB SYMBOL BUILDER ──────────────────────────────────────────────────────

def make_ic_symbol(sym_name, ref_prefix, default_value, footprint,
                   left_pins, right_pins,
                   top_pins=None, bot_pins=None,
                   body_w=12.7, extra_height=0):
    """
    left_pins, right_pins, top_pins, bot_pins:
        list of (pin_name, pin_num, pin_type)
        pin_type: 'input','output','bidirectional','power_in','power_out','passive','no_connect'
    Pins spaced 2.54mm vertically. Body centered at (0,0).
    """
    n_l = len(left_pins)
    n_r = len(right_pins)
    body_h = max(n_l, n_r, 2) * 2.54 + extra_height
    hw = body_w / 2
    hh = body_h / 2

    parts = []

    # Symbol header
    parts.append(f'(symbol "{sym_name}"')
    parts.append('  (pin_names (offset 0.508))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", ref_prefix, 0, hh + 2.0, 0))
    parts.append(prop_def("Value", default_value, 0, -(hh + 2.0), 0))
    parts.append(prop_def("Footprint", footprint, 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))

    sn = sym_name.split(":")[-1]

    # Body rectangle in _0_1 sub-symbol
    parts.append(f'  (symbol "{sn}_0_1"')
    parts.append(_indent(rect_def(-hw, -hh, hw, hh), 4))
    parts.append('  )')

    # Pins in _1_1 sub-symbol
    parts.append(f'  (symbol "{sn}_1_1"')

    # Left pins: connect from left → angle=0, x = -(hw+2.54)
    for i, (pname, pnum, ptype) in enumerate(left_pins):
        py = hh - 1.27 - i * 2.54
        parts.append(_indent(pin_def(pname, pnum, -(hw + 2.54), py, 0, ptype), 4))

    # Right pins: connect from right → angle=180, x = +(hw+2.54)
    for i, (pname, pnum, ptype) in enumerate(right_pins):
        py = hh - 1.27 - i * 2.54
        parts.append(_indent(pin_def(pname, pnum, hw + 2.54, py, 180, ptype), 4))

    # Top pins: angle=270 (pin points down from top edge)
    if top_pins:
        n_t = len(top_pins)
        for i, (pname, pnum, ptype) in enumerate(top_pins):
            px = -((n_t - 1) * 2.54) / 2 + i * 2.54
            parts.append(_indent(pin_def(pname, pnum, px, hh + 2.54, 270, ptype), 4))

    # Bottom pins: angle=90 (pin points up from bottom edge)
    if bot_pins:
        n_b = len(bot_pins)
        for i, (pname, pnum, ptype) in enumerate(bot_pins):
            px = -((n_b - 1) * 2.54) / 2 + i * 2.54
            parts.append(_indent(pin_def(pname, pnum, px, -(hh + 2.54), 90, ptype), 4))

    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)


def make_connector_symbol(sym_name, ref_prefix, default_value, footprint, pins):
    """Simple single-column connector. pins: list of (name, num)."""
    n = len(pins)
    body_h = n * 2.54
    hw = 5.08
    hh = body_h / 2
    parts = []
    parts.append(f'(symbol "{sym_name}"')
    parts.append('  (pin_names (offset 1.016))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", ref_prefix, 0, hh + 1.5, 0))
    parts.append(prop_def("Value", default_value, 0, -(hh + 1.5), 0))
    parts.append(prop_def("Footprint", footprint, 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))
    sn = sym_name.split(":")[-1]
    parts.append(f'  (symbol "{sn}_0_1"')
    parts.append(_indent(rect_def(-hw, -hh, hw, hh), 4))
    parts.append('  )')
    parts.append(f'  (symbol "{sn}_1_1"')
    for i, (pname, pnum) in enumerate(pins):
        py = hh - 1.27 - i * 2.54
        parts.append(_indent(pin_def(pname, pnum, -(hw + 2.54), py, 0, "passive"), 4))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)


# ─── DEFINE ALL LIB SYMBOLS ──────────────────────────────────────────────────

RP2040_LEFT = [
    ("VDD",       "1",  "power_in"),
    ("DVDD",      "2",  "power_in"),
    ("GND",       "3",  "power_in"),
    ("USB_DP",    "4",  "bidirectional"),
    ("USB_DM",    "5",  "bidirectional"),
    ("SPI0_SCK",  "6",  "input"),
    ("SPI0_MOSI", "7",  "output"),
    ("SPI0_MISO", "8",  "input"),
    ("I2C0_SDA",  "9",  "bidirectional"),
    ("I2C0_SCL",  "10", "output"),
    ("LORA_SCK",  "11", "output"),
    ("LORA_MOSI", "12", "output"),
    ("LORA_MISO", "13", "input"),
    ("LORA_BUSY", "14", "input"),
    ("LORA_IRQ",  "15", "input"),
    ("SWCLK",     "16", "input"),
    ("SWDIO",     "17", "bidirectional"),
    ("RUN",       "18", "input"),
]

RP2040_RIGHT = [
    ("UART0_TX",    "19", "output"),
    ("UART0_RX",    "20", "input"),
    ("IMU_CS",      "21", "output"),
    ("FLASH_CS",    "22", "output"),
    ("LORA_CS",     "23", "output"),
    ("LORA_NRST",   "24", "output"),
    ("PYRO1_GATE",  "25", "output"),
    ("PYRO2_GATE",  "26", "output"),
    ("PYRO3_GATE",  "27", "output"),
    ("PYRO1_CONT",  "28", "input"),
    ("PYRO2_CONT",  "29", "input"),
    ("PYRO3_CONT",  "30", "input"),
    ("LED_STATUS",  "31", "output"),
    ("IMU_INT1",    "32", "input"),
    ("IMU_INT2",    "33", "input"),
]

SYM_RP2040 = make_ic_symbol(
    "CCM:RP2040", "U", "RP2040",
    "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm",
    RP2040_LEFT, RP2040_RIGHT, body_w=20.32
)

W25Q128_LEFT = [
    ("VCC",  "8", "power_in"),
    ("GND",  "4", "power_in"),
    ("/HOLD","7", "input"),
    ("/WP",  "3", "input"),
]
W25Q128_RIGHT = [
    ("/CS",  "1", "input"),
    ("CLK",  "6", "input"),
    ("DO",   "2", "output"),
    ("DI",   "5", "input"),
]
SYM_W25Q128 = make_ic_symbol(
    "CCM:W25Q128", "U", "W25Q128JVSIQ",
    "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    W25Q128_LEFT, W25Q128_RIGHT, body_w=10.16
)

ICM_LEFT = [
    ("VDD",    "1",  "power_in"),
    ("VDDIO",  "2",  "power_in"),
    ("GND",    "3",  "power_in"),
    ("AP_AD0", "10", "input"),
    ("CLKIN",  "9",  "input"),
]
ICM_RIGHT = [
    ("CS",    "4", "input"),
    ("SCLK",  "5", "input"),
    ("MOSI",  "6", "input"),
    ("MISO",  "7", "output"),
    ("INT1",  "8", "output"),
    ("INT2",  "11","output"),
]
SYM_ICM42688 = make_ic_symbol(
    "CCM:ICM-42688-P", "U", "ICM-42688-P",
    "Sensor_IMU:InvenSense_ICM-42688-P_LGA-14",
    ICM_LEFT, ICM_RIGHT, body_w=10.16
)

BMP388_LEFT = [
    ("VDD",   "1", "power_in"),
    ("VDDIO", "2", "power_in"),
    ("GND",   "3", "power_in"),
    ("SDO",   "6", "input"),
    ("CSB",   "5", "input"),
]
BMP388_RIGHT = [
    ("SDI",   "4", "bidirectional"),
    ("SCK",   "7", "input"),
]
SYM_BMP388 = make_ic_symbol(
    "CCM:BMP388", "U", "BMP388",
    "Sensor_Pressure:Bosch_LGA-8_2x2.5mm",
    BMP388_LEFT, BMP388_RIGHT, body_w=10.16
)

TLV_LEFT = [
    ("VIN",  "1", "power_in"),
    ("GND",  "2", "power_in"),
    ("EN",   "3", "input"),
    ("FB",   "4", "input"),
]
TLV_RIGHT = [
    ("VOUT", "5", "power_out"),
]
SYM_TLV62569 = make_ic_symbol(
    "CCM:TLV62569", "U", "TLV62569",
    "Package_TO_SOT_SMD:SOT-23-5",
    TLV_LEFT, TLV_RIGHT, body_w=10.16
)

E22_LEFT = [
    ("VCC",  "1", "power_in"),
    ("GND",  "2", "power_in"),
    ("SCLK", "3", "input"),
    ("MOSI", "4", "input"),
    ("MISO", "5", "output"),
    ("NSS",  "6", "input"),
    ("BUSY", "7", "output"),
    ("DIO1", "8", "output"),
    ("NRST", "9", "input"),
]
E22_RIGHT = [
    ("RFIO", "10", "bidirectional"),
]
SYM_E22 = make_ic_symbol(
    "CCM:E22-900M22S", "U", "E22-900M22S",
    "RF_Module:Ebyte_E22-900M22S",
    E22_LEFT, E22_RIGHT, body_w=12.7
)

# IRFZ44N MOSFET symbol
def make_mosfet_symbol():
    hw, hh = 5.08, 6.35
    parts = []
    parts.append('(symbol "CCM:IRFZ44N"')
    parts.append('  (pin_names (offset 0.508))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", "Q", 0, hh + 1.5, 0))
    parts.append(prop_def("Value", "IRFZ44N", 0, -(hh + 1.5), 0))
    parts.append(prop_def("Footprint", "Package_TO_SOT_SMD:TO-263-3_TabEP", 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))
    parts.append('  (symbol "IRFZ44N_0_1"')
    parts.append('    ' + rect_def(-hw, -hh, hw, hh).replace('\n', '\n    '))
    parts.append('  )')
    parts.append('  (symbol "IRFZ44N_1_1"')
    # Gate: left side, mid
    parts.append('    ' + pin_def("G", "1", -(hw+2.54),  2.54, 0, "input").replace('\n', '\n    '))
    # Drain: right top
    parts.append('    ' + pin_def("D", "2",  hw+2.54,  2.54, 180, "passive").replace('\n', '\n    '))
    # Source: right bottom
    parts.append('    ' + pin_def("S", "3",  hw+2.54, -2.54, 180, "passive").replace('\n', '\n    '))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)

SYM_IRFZ44N = make_mosfet_symbol()

# Resistor (standard Device:R-like)
def make_resistor_symbol():
    parts = []
    parts.append('(symbol "CCM:R"')
    parts.append('  (pin_numbers (hide yes))')
    parts.append('  (pin_names (offset 0) (hide yes))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", "R", 1.524, 0, 90))
    parts.append(prop_def("Value", "R", -1.524, 0, 90))
    parts.append(prop_def("Footprint", "", 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))
    parts.append('  (symbol "R_0_1"')
    parts.append('    (rectangle (start -1.016 -2.032) (end 1.016 2.032)\n'
                 '      (stroke (width 0.254) (type default))\n'
                 '      (fill (type none))\n'
                 '    )')
    parts.append('  )')
    parts.append('  (symbol "R_1_1"')
    parts.append('    ' + pin_def("~", "1", 0,  3.81, 270, "passive").replace('\n', '\n    '))
    parts.append('    ' + pin_def("~", "2", 0, -3.81,  90, "passive").replace('\n', '\n    '))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)

SYM_R = make_resistor_symbol()

# Capacitor (non-polarized)
def make_cap_symbol():
    parts = []
    parts.append('(symbol "CCM:C"')
    parts.append('  (pin_numbers (hide yes))')
    parts.append('  (pin_names (offset 0.508) (hide yes))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", "C", 1.524, 0, 90))
    parts.append(prop_def("Value", "C", -1.524, 0, 90))
    parts.append(prop_def("Footprint", "", 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))
    parts.append('  (symbol "C_0_1"')
    parts.append('    (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508))\n'
                 '      (stroke (width 0.508) (type default)) (fill (type none)))\n'
                 '    (polyline (pts (xy -1.524  0.508) (xy 1.524  0.508))\n'
                 '      (stroke (width 0.508) (type default)) (fill (type none)))')
    parts.append('  )')
    parts.append('  (symbol "C_1_1"')
    parts.append('    ' + pin_def("~", "1", 0,  2.032, 270, "passive").replace('\n', '\n    '))
    parts.append('    ' + pin_def("~", "2", 0, -2.032,  90, "passive").replace('\n', '\n    '))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)

SYM_C = make_cap_symbol()

# Polarized Capacitor
def make_cpol_symbol():
    parts = []
    parts.append('(symbol "CCM:C_Polarized"')
    parts.append('  (pin_numbers (hide yes))')
    parts.append('  (pin_names (offset 0.508) (hide yes))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", "C", 1.524, 0, 90))
    parts.append(prop_def("Value", "C", -1.524, 0, 90))
    parts.append(prop_def("Footprint", "", 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))
    parts.append('  (symbol "C_Polarized_0_1"')
    parts.append('    (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508))\n'
                 '      (stroke (width 0.508) (type default)) (fill (type none)))\n'
                 '    (polyline (pts (xy -1.524  0.508) (xy 1.524  0.508))\n'
                 '      (stroke (width 0.508) (type default)) (fill (type background)))\n'
                 '    (text "+" (at -0.762 1.27 0)\n'
                 '      (effects (font (size 1.27 1.27))))')
    parts.append('  )')
    parts.append('  (symbol "C_Polarized_1_1"')
    parts.append('    ' + pin_def("+", "1", 0,  2.032, 270, "passive").replace('\n', '\n    '))
    parts.append('    ' + pin_def("-", "2", 0, -2.032,  90, "passive").replace('\n', '\n    '))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)

SYM_CPOL = make_cpol_symbol()

# LED
def make_led_symbol():
    parts = []
    parts.append('(symbol "CCM:LED"')
    parts.append('  (pin_numbers (hide yes))')
    parts.append('  (pin_names (offset 0.508) (hide yes))')
    parts.append('  (in_bom yes) (on_board yes)')
    parts.append(prop_def("Reference", "LED", 1.524, 0, 90))
    parts.append(prop_def("Value", "LED", -1.524, 0, 90))
    parts.append(prop_def("Footprint", "LED_SMD:LED_0805_2012Metric", 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "~", 0, 0, 0, hide=True))
    parts.append('  (symbol "LED_0_1"')
    parts.append('    (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27) (xy 1.27 0) (xy -1.27 -1.27))\n'
                 '      (stroke (width 0.254) (type default)) (fill (type none)))\n'
                 '    (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27))\n'
                 '      (stroke (width 0.254) (type default)) (fill (type none)))')
    parts.append('  )')
    parts.append('  (symbol "LED_1_1"')
    parts.append('    ' + pin_def("K", "1", -3.81, 0, 0, "passive").replace('\n', '\n    '))
    parts.append('    ' + pin_def("A", "2",  3.81, 0, 180, "passive").replace('\n', '\n    '))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)

SYM_LED = make_led_symbol()

# XT30 connector
SYM_XT30 = make_connector_symbol(
    "CCM:XT30", "J", "XT30-M",
    "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    [("VBAT", "1"), ("GND", "2")]
)

# 2-pin header (arm switch)
SYM_SW2 = make_connector_symbol(
    "CCM:SW_2pin", "J", "ARM_SWITCH",
    "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    [("IN", "1"), ("OUT", "2")]
)

# 2-pin screw terminal
SYM_SCREW2 = make_connector_symbol(
    "CCM:Screw_2", "J", "Pyro_Terminal",
    "TerminalBlock:TerminalBlock_bornier-2_P5.08mm",
    [("HV", "1"), ("OUT", "2")]
)

# JST-GH 8-pin
SYM_JSTGH8 = make_connector_symbol(
    "CCM:JST_GH_8", "J", "JST-GH-8",
    "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal",
    [("P1","1"),("P2","2"),("P3","3"),("P4","4"),
     ("P5","5"),("P6","6"),("P7","7"),("P8","8")]
)

# SMA edge connector
SYM_SMA = make_connector_symbol(
    "CCM:SMA_Edge", "J", "SMA_Edge",
    "Connector_Coaxial:SMA_Molex_0732511150_Horizontal",
    [("RF","1"),("GND","2")]
)

# TC2030 SWD header (6-pin)
SYM_TC2030 = make_connector_symbol(
    "CCM:TC2030", "SW", "TC2030-SWD",
    "Tag-Connect:TC2030-IDC-FP_2x03_P1.27mm_Vertical",
    [("SWCLK","1"),("SWDIO","2"),("VCC","3"),
     ("GND","4"),("UART_TX","5"),("UART_RX","6")]
)

# Power symbols (GND, +3V3, VBAT, VBAT_ARMED)
def make_power_symbol(name, ref_prefix="PWR"):
    is_gnd = ("GND" in name.upper())
    parts = []
    parts.append(f'(symbol "power:{name}"')
    parts.append('  (pin_numbers (hide yes))')
    parts.append('  (pin_names (offset 0) (hide yes))')
    parts.append('  (in_bom no) (on_board no)')
    parts.append(prop_def("Reference", f"#{ref_prefix}", 0, -1.905 if is_gnd else 1.905, 0, hide=True))
    parts.append(prop_def("Value", name, 0, -3.81 if is_gnd else 3.81, 0))
    parts.append(prop_def("Footprint", "", 0, 0, 0, hide=True))
    parts.append(prop_def("Datasheet", "", 0, 0, 0, hide=True))
    parts.append(f'  (symbol "{name}_0_1"')
    if is_gnd:
        parts.append('    (polyline (pts (xy 0 0) (xy 0 -1.27))\n'
                     '      (stroke (width 0) (type default)) (fill (type none)))\n'
                     '    (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27))\n'
                     '      (stroke (width 0) (type default)) (fill (type none)))\n'
                     '    (polyline (pts (xy -0.762 -1.905) (xy 0.762 -1.905))\n'
                     '      (stroke (width 0) (type default)) (fill (type none)))\n'
                     '    (polyline (pts (xy -0.381 -2.54) (xy 0.381 -2.54))\n'
                     '      (stroke (width 0) (type default)) (fill (type none)))')
    else:
        parts.append('    (polyline (pts (xy 0 0) (xy 0 1.27))\n'
                     '      (stroke (width 0) (type default)) (fill (type none)))\n'
                     '    (polyline (pts (xy -0.762 1.27) (xy 0 2.032) (xy 0.762 1.27))\n'
                     '      (stroke (width 0) (type default)) (fill (type none)))')
    parts.append('  )')
    parts.append(f'  (symbol "{name}_1_1"')
    if is_gnd:
        parts.append('    ' + pin_def("~", "1", 0, 0, 270, "power_in").replace('\n', '\n    '))
    else:
        parts.append('    ' + pin_def("~", "1", 0, 0, 270, "power_in").replace('\n', '\n    '))
    parts.append('  )')
    parts.append(')')
    return '\n'.join(parts)

SYM_GND      = make_power_symbol("GND")
SYM_3V3      = make_power_symbol("+3V3")
SYM_VBAT     = make_power_symbol("VBAT")
SYM_VBAT_ARM = make_power_symbol("VBAT_ARMED")

ALL_SYMBOLS = [
    SYM_RP2040, SYM_W25Q128, SYM_ICM42688, SYM_BMP388,
    SYM_TLV62569, SYM_E22, SYM_IRFZ44N,
    SYM_R, SYM_C, SYM_CPOL, SYM_LED,
    SYM_XT30, SYM_SW2, SYM_SCREW2, SYM_JSTGH8, SYM_SMA, SYM_TC2030,
    SYM_GND, SYM_3V3, SYM_VBAT, SYM_VBAT_ARM,
]

# ─── SCHEMATIC ELEMENT BUILDERS ──────────────────────────────────────────────

_pwr_uid = [0]

def place_symbol(lib_id, x, y, angle=0, mirror="", unit=1, **props):
    """Place a component instance at (x, y)."""
    m = f'\n  (mirror {mirror})' if mirror else ''
    lines = [f'(symbol (lib_id "{lib_id}") (at {x:.3f} {y:.3f} {angle}){m} (unit {unit})']
    lines.append('  (in_bom yes) (on_board yes)')
    lines.append(f'  (uuid "{u()}")')
    for k, (val, px, py, pa, hide) in props.items():
        h = ' (hide yes)' if hide else ''
        lines.append(f'  (property "{k}" "{val}" (at {px:.3f} {py:.3f} {pa})\n'
                     f'    (effects (font (size 1.27 1.27)){h})\n  )')
    lines.append(')')
    return '\n'.join(lines)

def wire(x1, y1, x2, y2):
    return (f'(wire (pts (xy {x1:.3f} {y1:.3f}) (xy {x2:.3f} {y2:.3f}))\n'
            f'  (stroke (width 0) (type default))\n'
            f'  (uuid "{u()}")\n)')

def net_label(name, x, y, angle=0):
    """Net label for local connections."""
    return (f'(label "{name}" (at {x:.3f} {y:.3f} {angle})\n'
            f'  (effects (font (size 1.27 1.27)) (justify left))\n'
            f'  (uuid "{u()}")\n)')

def power_port(name, x, y, angle=0):
    """Place a power flag / power port."""
    _pwr_uid[0] += 1
    ref = f"#PWR{_pwr_uid[0]:04d}"
    return (f'(symbol (lib_id "power:{name}") (at {x:.3f} {y:.3f} {angle}) (unit 1)\n'
            f'  (in_bom yes) (on_board yes)\n'
            f'  (uuid "{u()}")\n'
            f'  (property "Reference" "{ref}" (at {x:.3f} {y:.3f} 0)\n'
            f'    (effects (font (size 1.27 1.27)) (hide yes))\n  )\n'
            f'  (property "Value" "{name}" (at {x:.3f} {y:.3f} 0)\n'
            f'    (effects (font (size 1.27 1.27)))\n  )\n'
            f'  (pin "1" (uuid "{u()}"))\n'
            f')')

def no_connect(x, y):
    return f'(no_connect (at {x:.3f} {y:.3f}) (uuid "{u()}"))'

def text_note(txt, x, y, size=1.5, bold=False):
    b = " bold" if bold else ""
    return (f'(text "{txt}" (at {x:.3f} {y:.3f} 0)\n'
            f'  (effects (font (size {size} {size}){b}))\n'
            f'  (uuid "{u()}")\n)')

def section_rect(x1, y1, x2, y2, label, color="#aaaaaa"):
    # KiCAD sheet rectangles for visual grouping
    return (f'(rectangle (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'  (stroke (width 0.127) (type dash))\n'
            f'  (fill (type none))\n'
            f'  (uuid "{u()}")\n)')

# ─── COMPONENT PLACEMENT ──────────────────────────────────────────────────────
# Layout on A1 (594 x 841mm). We'll use a 300x200 area starting at (20,20).
# Sections:
#   POWER:     x=20..90,   y=20..70
#   MCU:       x=100..200, y=20..100
#   SENSORS:   x=210..290, y=20..80
#   RF:        x=20..110,  y=110..170
#   PYRO:      x=115..250, y=110..190
#   CONNECTORS:x=255..310, y=20..190

elements = []

def e(s): elements.append(s)

# ── SECTION LABELS ──
e(text_note("POWER SECTION", 22, 18, size=2.0, bold=True))
e(text_note("MCU — RP2040 + W25Q128", 102, 18, size=2.0, bold=True))
e(text_note("SENSORS — ICM-42688-P / BMP388", 212, 18, size=2.0, bold=True))
e(text_note("RF — Ebyte E22-900M22S 915MHz", 22, 108, size=2.0, bold=True))
e(text_note("PYRO CHANNELS — 3x IRFZ44N", 117, 108, size=2.0, bold=True))
e(text_note("I/O CONNECTORS", 257, 18, size=2.0, bold=True))

# ════════════════════════════════════════════════════════════════════════
# POWER SECTION
# ════════════════════════════════════════════════════════════════════════

# J4: XT30 battery input  @ (30, 35)
e(place_symbol("CCM:XT30", 30, 35, **{
    "Reference": ("J4", 33, 32, 0, False),
    "Value":     ("XT30-M BAT IN", 33, 38, 0, False),
}))
e(wire(30, 30, 30, 28)); e(net_label("VBAT", 30, 28, 90))
e(wire(30, 40, 30, 42)); e(power_port("GND", 30, 44))

# C1: 47uF input bulk cap @ (45, 35)
e(place_symbol("CCM:C_Polarized", 45, 35, **{
    "Reference": ("C1", 47, 32, 0, False),
    "Value":     ("47uF 10V", 47, 38, 0, False),
}))
e(wire(45, 33, 45, 28)); e(net_label("VBAT", 45, 28, 90))
e(wire(45, 37, 45, 42)); e(power_port("GND", 45, 44))

# U6: TLV62569 buck @ (65, 35)
e(place_symbol("CCM:TLV62569", 65, 35, **{
    "Reference": ("U6", 68, 24, 0, False),
    "Value":     ("TLV62569 3V3", 68, 48, 0, False),
}))
# VIN ← VBAT
e(wire(52.46, 36.27, 50, 36.27)); e(net_label("VBAT", 50, 36.27, 0))
# GND
e(wire(52.46, 33.73, 50, 33.73)); e(power_port("GND", 50, 33.73))
# EN ← VCC3V3 (tied high)
e(wire(52.46, 31.19, 50, 31.19)); e(net_label("+3V3", 50, 31.19, 0))
# FB ← feedback resistor divider (simplified, label)
e(wire(52.46, 28.65, 50, 28.65)); e(net_label("FB_3V3", 50, 28.65, 0))
# VOUT → +3V3
e(wire(77.54, 36.27, 80, 36.27)); e(net_label("+3V3", 80, 36.27, 180))

# C2: 22uF output cap @ (85, 35)
e(place_symbol("CCM:C_Polarized", 85, 35, **{
    "Reference": ("C2", 87, 32, 0, False),
    "Value":     ("22uF 6.3V", 87, 38, 0, False),
}))
e(wire(85, 33, 85, 28)); e(net_label("+3V3", 85, 28, 90))
e(wire(85, 37, 85, 42)); e(power_port("GND", 85, 44))

# J5: Arm switch @ (50, 60)
e(place_symbol("CCM:SW_2pin", 50, 60, **{
    "Reference": ("J5", 53, 55, 0, False),
    "Value":     ("ARM SWITCH", 53, 65, 0, False),
}))
e(wire(50, 56.27, 50, 54)); e(net_label("VBAT", 50, 54, 90))
e(wire(50, 63.73, 50, 66)); e(net_label("VBAT_ARMED", 50, 66, 270))

# ════════════════════════════════════════════════════════════════════════
# MCU SECTION — RP2040 + W25Q128
# ════════════════════════════════════════════════════════════════════════

# U1: RP2040 @ (155, 65)   (large component, ~45mm tall)
e(place_symbol("CCM:RP2040", 155, 65, **{
    "Reference": ("U1", 155, 18, 0, False),
    "Value":     ("RP2040 QFN-56", 155, 112, 0, False),
}))

# Left pin connections (all as net labels)
rp_lx = 155 - 10.16 - 2.54  # left connection x
rp_hh = 18 * 2.54 / 2        # half height based on 18 left pins
# Pins start at hh - 1.27 from center, spaced 2.54
def rp_left_y(i):
    hh = max(18, 15) * 2.54 / 2
    return 65 - hh + 1.27 + i * 2.54

def rp_right_y(i):
    hh = max(18, 15) * 2.54 / 2
    return 65 - hh + 1.27 + i * 2.54

LEFT_NETS = ["VBAT", "+3V3", "GND", "USB_DP", "USB_DM",
             "SPI0_SCK", "SPI0_MOSI", "SPI0_MISO",
             "I2C0_SDA", "I2C0_SCL",
             "LORA_SCK", "LORA_MOSI", "LORA_MISO", "LORA_BUSY", "LORA_IRQ",
             "SWCLK", "SWDIO", "~RESET~"]

RIGHT_NETS = ["UART0_TX", "UART0_RX", "IMU_CS", "FLASH_CS",
              "LORA_CS", "LORA_NRST",
              "PYRO1_GATE", "PYRO2_GATE", "PYRO3_GATE",
              "PYRO1_CONT", "PYRO2_CONT", "PYRO3_CONT",
              "LED_STATUS", "IMU_INT1", "IMU_INT2"]

rp_body_hw = 10.16
rp_body_lx = 155 - rp_body_hw - 2.54
rp_body_rx = 155 + rp_body_hw + 2.54

for i, net in enumerate(LEFT_NETS):
    py = rp_left_y(i)
    e(wire(rp_body_lx, py, rp_body_lx - 2.54, py))
    if net == "GND":
        e(power_port("GND", rp_body_lx - 2.54, py))
    elif net in ("+3V3", "VBAT"):
        e(net_label(net, rp_body_lx - 2.54, py, 0))
    elif net == "~RESET~":
        e(net_label("NRST", rp_body_lx - 2.54, py, 0))
    else:
        e(net_label(net, rp_body_lx - 2.54, py, 0))

for i, net in enumerate(RIGHT_NETS):
    py = rp_right_y(i)
    e(wire(rp_body_rx, py, rp_body_rx + 2.54, py))
    e(net_label(net, rp_body_rx + 2.54, py, 180))

# U2: W25Q128 QSPI Flash @ (120, 35)
e(place_symbol("CCM:W25Q128", 120, 35, **{
    "Reference": ("U2", 123, 24, 0, False),
    "Value":     ("W25Q128JVSIQ", 123, 46, 0, False),
}))
e(wire(107.46, 36.27, 105, 36.27)); e(net_label("+3V3", 105, 36.27, 0))
e(wire(107.46, 33.73, 105, 33.73)); e(power_port("GND", 105, 33.73))
e(wire(107.46, 31.19, 105, 31.19)); e(net_label("+3V3", 105, 31.19, 0))  # /HOLD
e(wire(107.46, 28.65, 105, 28.65)); e(net_label("+3V3", 105, 28.65, 0))  # /WP
e(wire(132.54, 36.27, 135, 36.27)); e(net_label("FLASH_CS", 135, 36.27, 180))
e(wire(132.54, 33.73, 135, 33.73)); e(net_label("SPI0_SCK", 135, 33.73, 180))
e(wire(132.54, 31.19, 135, 31.19)); e(net_label("SPI0_MISO", 135, 31.19, 180))
e(wire(132.54, 28.65, 135, 28.65)); e(net_label("SPI0_MOSI", 135, 28.65, 180))

# Decoupling caps near MCU
# C10: 100nF @ (135, 80)
e(place_symbol("CCM:C", 135, 80, **{
    "Reference": ("C10", 137, 77, 0, False),
    "Value":     ("100nF 0402", 137, 83, 0, False),
}))
e(wire(135, 78, 135, 76)); e(net_label("+3V3", 135, 76, 90))
e(wire(135, 82, 135, 84)); e(power_port("GND", 135, 85))

# C11: 10uF @ (140, 80)
e(place_symbol("CCM:C", 140, 80, **{
    "Reference": ("C11", 142, 77, 0, False),
    "Value":     ("10uF 0402", 142, 83, 0, False),
}))
e(wire(140, 78, 140, 76)); e(net_label("+3V3", 140, 76, 90))
e(wire(140, 82, 140, 84)); e(power_port("GND", 140, 85))

# C12: 100nF RESET filter @ (130, 90)
e(place_symbol("CCM:C", 130, 90, **{
    "Reference": ("C12", 132, 87, 0, False),
    "Value":     ("100nF 0402", 132, 93, 0, False),
}))
e(wire(130, 88, 130, 86)); e(net_label("NRST", 130, 86, 90))
e(wire(130, 92, 130, 94)); e(power_port("GND", 130, 95))

# R1: 10k RESET pull-up @ (135, 90)
e(place_symbol("CCM:R", 135, 90, **{
    "Reference": ("R1", 137, 87, 0, False),
    "Value":     ("10k 0402", 137, 93, 0, False),
}))
e(wire(135, 86.19, 135, 84)); e(net_label("+3V3", 135, 84, 90))
e(wire(135, 93.81, 135, 95)); e(net_label("NRST", 135, 95, 270))

# ════════════════════════════════════════════════════════════════════════
# SENSORS SECTION
# ════════════════════════════════════════════════════════════════════════

# U3: ICM-42688-P IMU @ (235, 38)
e(place_symbol("CCM:ICM-42688-P", 235, 38, **{
    "Reference": ("U3", 238, 22, 0, False),
    "Value":     ("ICM-42688-P", 238, 54, 0, False),
}))
# Left pins
e(wire(222.46, 39.27, 220, 39.27)); e(net_label("+3V3", 220, 39.27, 0))
e(wire(222.46, 36.73, 220, 36.73)); e(net_label("+3V3", 220, 36.73, 0))
e(wire(222.46, 34.19, 220, 34.19)); e(power_port("GND", 220, 34.19))
e(wire(222.46, 31.65, 220, 31.65)); e(power_port("GND", 220, 31.65))  # AP_AD0 → GND
e(wire(222.46, 29.11, 220, 29.11)); e(power_port("GND", 220, 29.11))  # CLKIN → GND
# Right pins
e(wire(247.54, 39.27, 250, 39.27)); e(net_label("IMU_CS", 250, 39.27, 180))
e(wire(247.54, 36.73, 250, 36.73)); e(net_label("SPI0_SCK", 250, 36.73, 180))
e(wire(247.54, 34.19, 250, 34.19)); e(net_label("SPI0_MOSI", 250, 34.19, 180))
e(wire(247.54, 31.65, 250, 31.65)); e(net_label("SPI0_MISO", 250, 31.65, 180))
e(wire(247.54, 29.11, 250, 29.11)); e(net_label("IMU_INT1", 250, 29.11, 180))
e(wire(247.54, 26.57, 250, 26.57)); e(net_label("IMU_INT2", 250, 26.57, 180))

# C20: 100nF IMU decoupling @ (218, 28)
e(place_symbol("CCM:C", 218, 28, **{
    "Reference": ("C20", 220, 25, 0, False),
    "Value":     ("100nF 0402", 220, 31, 0, False),
}))
e(wire(218, 26, 218, 24)); e(net_label("+3V3", 218, 24, 90))
e(wire(218, 30, 218, 32)); e(power_port("GND", 218, 33))

# C21: 100nF IMU decoupling @ (223, 28)
e(place_symbol("CCM:C", 223, 28, **{
    "Reference": ("C21", 225, 25, 0, False),
    "Value":     ("100nF 0402", 225, 31, 0, False),
}))
e(wire(223, 26, 223, 24)); e(net_label("+3V3", 223, 24, 90))
e(wire(223, 30, 223, 32)); e(power_port("GND", 223, 33))

# U4: BMP388 barometer @ (235, 68)
e(place_symbol("CCM:BMP388", 235, 68, **{
    "Reference": ("U4", 238, 54, 0, False),
    "Value":     ("BMP388", 238, 82, 0, False),
}))
# Left: VDD, VDDIO, GND, SDO→GND, CSB→VCC
e(wire(222.46, 69.27, 220, 69.27)); e(net_label("+3V3", 220, 69.27, 0))
e(wire(222.46, 66.73, 220, 66.73)); e(net_label("+3V3", 220, 66.73, 0))
e(wire(222.46, 64.19, 220, 64.19)); e(power_port("GND", 220, 64.19))
e(wire(222.46, 61.65, 220, 61.65)); e(power_port("GND", 220, 61.65))   # SDO → GND (addr 0x76)
e(wire(222.46, 59.11, 220, 59.11)); e(net_label("+3V3", 220, 59.11, 0)) # CSB → +3V3 (I2C mode)
# Right: SDI (SDA), SCK (SCL)
e(wire(247.54, 69.27, 250, 69.27)); e(net_label("I2C0_SDA", 250, 69.27, 180))
e(wire(247.54, 66.73, 250, 66.73)); e(net_label("I2C0_SCL", 250, 66.73, 180))

# R10: I2C SDA pull-up @ (256, 62)
e(place_symbol("CCM:R", 256, 62, **{
    "Reference": ("R10", 258, 59, 0, False),
    "Value":     ("4.7k 0402", 258, 65, 0, False),
}))
e(wire(256, 58.19, 256, 56)); e(net_label("+3V3", 256, 56, 90))
e(wire(256, 65.81, 256, 67)); e(net_label("I2C0_SDA", 256, 67, 270))

# R11: I2C SCL pull-up @ (261, 62)
e(place_symbol("CCM:R", 261, 62, **{
    "Reference": ("R11", 263, 59, 0, False),
    "Value":     ("4.7k 0402", 263, 65, 0, False),
}))
e(wire(261, 58.19, 261, 56)); e(net_label("+3V3", 261, 56, 90))
e(wire(261, 65.81, 261, 67)); e(net_label("I2C0_SCL", 261, 67, 270))

# ════════════════════════════════════════════════════════════════════════
# RF SECTION — Ebyte E22-900M22S
# ════════════════════════════════════════════════════════════════════════

# U5: E22-900M22S @ (70, 140)
e(place_symbol("CCM:E22-900M22S", 70, 140, **{
    "Reference": ("U5", 73, 118, 0, False),
    "Value":     ("E22-900M22S", 73, 162, 0, False),
}))
# Left side: VCC, GND, SCLK, MOSI, MISO, NSS, BUSY, DIO1, NRST
e(wire(57.46, 151.27, 55, 151.27)); e(net_label("+3V3", 55, 151.27, 0))
e(wire(57.46, 148.73, 55, 148.73)); e(power_port("GND", 55, 148.73))
e(wire(57.46, 146.19, 55, 146.19)); e(net_label("LORA_SCK", 55, 146.19, 0))
e(wire(57.46, 143.65, 55, 143.65)); e(net_label("LORA_MOSI", 55, 143.65, 0))
e(wire(57.46, 141.11, 55, 141.11)); e(net_label("LORA_MISO", 55, 141.11, 0))
e(wire(57.46, 138.57, 55, 138.57)); e(net_label("LORA_CS", 55, 138.57, 0))
e(wire(57.46, 136.03, 55, 136.03)); e(net_label("LORA_BUSY", 55, 136.03, 0))
e(wire(57.46, 133.49, 55, 133.49)); e(net_label("LORA_IRQ", 55, 133.49, 0))
e(wire(57.46, 130.95, 55, 130.95)); e(net_label("LORA_NRST", 55, 130.95, 0))
# Right side: RFIO → SMA
e(wire(82.54, 151.27, 85, 151.27)); e(net_label("RF_ANT", 85, 151.27, 180))

# C30: 100nF LoRa decoupling @ (58, 128)
e(place_symbol("CCM:C", 58, 128, **{
    "Reference": ("C30", 60, 125, 0, False),
    "Value":     ("100nF 0402", 60, 131, 0, False),
}))
e(wire(58, 126, 58, 124)); e(net_label("+3V3", 58, 124, 90))
e(wire(58, 130, 58, 132)); e(power_port("GND", 58, 133))

# J3: SMA edge connector @ (35, 140)
e(place_symbol("CCM:SMA_Edge", 35, 140, **{
    "Reference": ("J3", 38, 135, 0, False),
    "Value":     ("SMA 915MHz", 38, 145, 0, False),
}))
e(wire(35, 136.27, 35, 134)); e(net_label("RF_ANT", 35, 134, 90))
e(wire(35, 143.73, 35, 146)); e(power_port("GND", 35, 147))

# RF keepout note
e(text_note("NOTE: RF trace RFIO-SMA = 50Ω CPW, 0.9mm on 1.6mm FR4.", 22, 168, size=1.27))
e(text_note("10mm copper-free keepout around E22 antenna pad.", 22, 171, size=1.27))

# ════════════════════════════════════════════════════════════════════════
# PYRO CHANNELS — 3x IRFZ44N
# ════════════════════════════════════════════════════════════════════════

for ch in range(3):
    cx = 130 + ch * 40   # Q1=130, Q2=170, Q3=210

    # Gate resistor (100R): at (cx-10, 120)
    e(place_symbol("CCM:R", cx - 10, 120, **{
        "Reference": (f"R{20+ch}", cx - 8, 117, 0, False),
        "Value":     ("100R 0402",   cx - 8, 123, 0, False),
    }))
    e(wire(cx - 10, 116.19, cx - 10, 114))
    e(net_label(f"PYRO{ch+1}_GATE", cx - 10, 114, 90))
    e(wire(cx - 10, 123.81, cx - 10, 126))  # to gate pull-down

    # Gate pull-down (10k): at (cx-10, 130)
    e(place_symbol("CCM:R", cx - 10, 130, **{
        "Reference": (f"R{23+ch}", cx - 8, 127, 0, False),
        "Value":     ("10k 0402",    cx - 8, 133, 0, False),
    }))
    e(wire(cx - 10, 126.19, cx - 10, 126))  # connected to gate resistor output above
    e(wire(cx - 10, 133.81, cx - 10, 136)); e(power_port("GND", cx - 10, 137))

    # Q: IRFZ44N @ (cx, 145)
    e(place_symbol("CCM:IRFZ44N", cx, 145, **{
        "Reference": (f"Q{ch+1}", cx + 3, 136, 0, False),
        "Value":     ("IRFZ44N D2PAK", cx + 3, 155, 0, False),
    }))
    # Gate wire from pull-down junction to MOSFET gate
    e(wire(cx - 10, 126, cx - 7.62, 126))
    e(wire(cx - 7.62, 126, cx - 7.62, 147.54))
    # Drain ← VBAT_ARMED via screw terminal
    e(wire(cx + 7.62, 147.54, cx + 12, 147.54))
    e(net_label(f"PYRO{ch+1}_D", cx + 12, 147.54, 180))
    # Source → GND
    e(wire(cx + 7.62, 142.46, cx + 12, 142.46))
    e(power_port("GND", cx + 12, 142.46))

    # J screw terminal @ (cx, 168)
    e(place_symbol("CCM:Screw_2", cx, 168, **{
        "Reference": (f"J{6+ch}", cx + 3, 163, 0, False),
        "Value":     (f"Pyro CH{ch+1} E-Match", cx + 3, 173, 0, False),
    }))
    e(wire(cx, 164.27, cx, 162)); e(net_label("VBAT_ARMED", cx, 162, 90))
    e(wire(cx, 171.73, cx, 174)); e(net_label(f"PYRO{ch+1}_D", cx, 174, 270))

    # LED continuity indicator @ (cx, 183)
    e(place_symbol("CCM:LED", cx, 183, **{
        "Reference": (f"LED{ch+1}", cx + 3, 179, 0, False),
        "Value":     ("Bicolor LED 0805", cx + 3, 187, 0, False),
    }))
    e(wire(cx - 3.81, 183, cx - 6, 183)); e(net_label(f"PYRO{ch+1}_CONT", cx - 6, 183, 0))
    e(wire(cx + 3.81, 183, cx + 6, 183)); e(power_port("GND", cx + 6, 183))

# ════════════════════════════════════════════════════════════════════════
# I/O CONNECTORS
# ════════════════════════════════════════════════════════════════════════

# J1: ASAM-1 ribbon @ (275, 35)
e(place_symbol("CCM:JST_GH_8", 275, 35, **{
    "Reference": ("J1", 278, 22, 0, False),
    "Value":     ("JST-GH 8p ASAM-1", 278, 48, 0, False),
}))
jst1_pins = ["+3V3","GND","UART0_TX","UART0_RX","I2C0_SDA","I2C0_SCL","SPI0_SCK","PYRO1_GATE"]
jst1_hw = 5.08
for i, net in enumerate(jst1_pins):
    py = 35 - 8*2.54/2 + 1.27 + i*2.54
    e(wire(275 - jst1_hw - 2.54, py, 275 - jst1_hw - 5, py))
    if net == "GND":
        e(power_port("GND", 275 - jst1_hw - 5, py))
    elif net == "+3V3":
        e(net_label("+3V3", 275 - jst1_hw - 5, py, 0))
    else:
        e(net_label(net, 275 - jst1_hw - 5, py, 0))

# J2: ASAM-2 ribbon @ (275, 80)
e(place_symbol("CCM:JST_GH_8", 275, 80, **{
    "Reference": ("J2", 278, 67, 0, False),
    "Value":     ("JST-GH 8p ASAM-2", 278, 93, 0, False),
}))
jst2_pins = ["+3V3","GND","UART0_TX","UART0_RX","I2C0_SDA","I2C0_SCL","SPI0_SCK","PYRO2_GATE"]
for i, net in enumerate(jst2_pins):
    py = 80 - 8*2.54/2 + 1.27 + i*2.54
    e(wire(275 - jst1_hw - 2.54, py, 275 - jst1_hw - 5, py))
    if net == "GND":
        e(power_port("GND", 275 - jst1_hw - 5, py))
    elif net == "+3V3":
        e(net_label("+3V3", 275 - jst1_hw - 5, py, 0))
    else:
        e(net_label(net, 275 - jst1_hw - 5, py, 0))

# SW1: TC2030 SWD @ (275, 130)
e(place_symbol("CCM:TC2030", 275, 130, **{
    "Reference": ("SW1", 278, 118, 0, False),
    "Value":     ("TC2030-SWD", 278, 142, 0, False),
}))
tc_pins = ["SWCLK","SWDIO","+3V3","GND","UART0_TX","UART0_RX"]
tc_hw = 5.08
for i, net in enumerate(tc_pins):
    py = 130 - 6*2.54/2 + 1.27 + i*2.54
    e(wire(275 - tc_hw - 2.54, py, 275 - tc_hw - 5, py))
    if net == "GND":
        e(power_port("GND", 275 - tc_hw - 5, py))
    elif net == "+3V3":
        e(net_label("+3V3", 275 - tc_hw - 5, py, 0))
    else:
        e(net_label(net, 275 - tc_hw - 5, py, 0))

# Status LED @ (275, 160)
e(place_symbol("CCM:LED", 275, 160, **{
    "Reference": ("LED4", 278, 156, 0, False),
    "Value":     ("Status LED 0805", 278, 164, 0, False),
}))
e(wire(275 - 3.81, 160, 275 - 6, 160)); e(net_label("LED_STATUS", 275 - 6, 160, 0))
e(wire(275 + 3.81, 160, 275 + 6, 160)); e(power_port("GND", 275 + 6, 160))

# ─── ASSEMBLE FINAL SCHEMATIC ─────────────────────────────────────────────────

def build_schematic():
    lib_syms_block = '\n'.join(_indent(s, 2) for s in ALL_SYMBOLS)

    body = '\n'.join(elements)

    sch = f"""(kicad_sch (version 20230121) (generator "eeschema")
  (uuid "{u()}")
  (paper "A1")
  (title_block
    (title "XRIM-117 CCM - Central Command Module")
    (rev "Rev A")
    (date "2026-05-28")
    (company "Skylight Industries LLC")
    (comment 1 "PDR-002 | RP2040 QFN-56 + ICM-42688-P + BMP388 + Ebyte E22-900M22S LoRa 915MHz + 3x IRFZ44N Pyro")
    (comment 2 "62mm Circular 2-Layer FR4 ENIG | 1S LiPo 850mAh | TLV62569 3.3V Buck")
    (comment 3 "Skylight Industries LLC / Legacy Systems Research Group")
  )
  (lib_symbols
{lib_syms_block}
  )
{body}
)"""
    return sch

if __name__ == "__main__":
    output = build_schematic()
    out_path = "/sessions/tender-funny-rubin/mnt/outputs/CCM_Central_Command_Module.kicad_sch"
    with open(out_path, "w") as f:
        f.write(output)
    print(f"Written: {out_path}")
    print(f"File size: {len(output):,} bytes")
    # Basic validation
    assert output.startswith("(kicad_sch")
    assert "(lib_symbols" in output
    assert "RP2040" in output
    assert "ICM-42688-P" in output
    assert "E22-900M22S" in output
    assert "IRFZ44N" in output
    print("Basic validation PASSED")
