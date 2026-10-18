#!/usr/bin/env python3
"""GTR70E WYVERN, PCB1 netlist checker.

Compares an EasyEDA .tel netlist export against the target connectivity in
`Documentation/PCB1_REWIRE_BUILD_SHEET.md`. Reports merged nets, shorted two-terminal parts,
misplaced pins, and unconnected pins that should be connected.

Usage:  python3 check_netlist.py Netlist_Schematic1_2026-08-13.tel
"""
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------------------------
# TARGET CONNECTIVITY
# Each entry maps a net name to the exact set of pins that belong on it.
# ---------------------------------------------------------------------------------------------

TARGET = {
    "GND": """
        C1.2 C2.2 C3.2 C4.2 C5.2 C7.2 C8.2 C9.2 C10.2 C11.2 C12.2 C13.2 C14.2 C15.2 C16.2
        C17.2 C18.2 C19.2 C20.2 C21.2 C22.2 C23.2 C24.2 C25.2 C26.2 C27.2 C28.2 C29.2
        C31.2 C32.2 C33.2 C34.2
        U1.62 U1.81
        U2.2 U2.5 U2.6 U2.10 U2.15 U2.16 U2.17 U2.18 U2.25
        U3.1 U3.5 U3.7
        U4.1 U4.2 U4.7
        U5.2 U5.3 U5.9 U5.12
        U6.1 U7.2 U15.1 U13.3
        U8.3 U9.3 U10.3 U11.3
        U12.3 U12.4 U14.4
        CARD1.6 CARD1.9 CARD1.10 CARD1.11
        CN1.1 CN2.1 USBC1.A1B12 USBC1.B1A12
        H1.2 H1.6 H1.11 H1.14 H2.2
        R6.2 R12.2 R13.2 R15.2 R17.1 R23.2
        D1.2 SW2.3 SW2.4
    """,
    "3V3": """
        U7.5
        U1.5 U1.15 U1.24 U1.29 U1.41 U1.50 U1.60 U1.76
        U1.59 U1.64 U1.68 U1.69
        C8.1 C9.1 C10.1 C11.1 C12.1 C13.1 C14.1 C15.1 C16.1 C18.1 C23.1 C24.1 C33.1
        U2.3 U2.4 U2.28
        U3.2 U3.6 U3.8
        U4.6
        U5.5 U5.6 U5.10
        U14.8 CARD1.4 CN2.2
        H1.1 H1.5
        R2.2 R9.2 R16.1 R18.1 R19.1 R20.1 R21.1 R25.2 R26.2
    """,
    "VBUCK_5V": "L2.2 C21.1 C22.1 D2.1 R5.1 U7.1 U7.3 H1.12",
    "VSRV_5V": "L3.2 C31.1 C32.1 R22.1 U8.2 U9.2 U10.2 U11.2",
    "VBAT": "CN1.2 R10.1 U4.8 U4.10",
    "VBAT_SW": "R10.2 U4.9 F1.2 F2.2 U13.1",
    "VAVI_IN": "F1.1 U15.3 C26.1",
    "VSRV_IN": "F2.1 U6.3 C29.1",
    "EN_SRC": "U13.2 R14.1 R24.1",
    "EN_AVI": "R14.2 R15.1 U15.5",
    "EN_SRV": "R24.2 R17.2 U6.5",
    "SW_AVI": "C6.2 L2.1 U15.2",
    "BST_AVI": "C6.1 U15.6",
    "VFB_AVI": "R5.2 R6.1 U15.4",
    "SW_SRV": "C30.2 L3.1 U6.2",
    "BST_SRV": "C30.1 U6.6",
    "VFB_SRV": "R22.2 R23.1 U6.4",
    "VREG_LX": "L1.1 U1.63",
    "DVDD": "C17.1 C19.1 C20.1 C34.1 L1.2 U1.10 U1.32 U1.51 U1.65",
    "VREG_AVDD": "C3.1 C4.1 C5.1 C7.1 R2.1 U1.61",
    "XIN": "U1.30 U12.1 C1.1",
    "XOUT": "U1.31 R1.1",
    "XTAL_B": "R1.2 U12.2 C2.1",
    "SDA": "CN2.3 R25.1 U1.77 U2.20 U3.3 U4.4 U5.11",
    "SCL": "CN2.4 R26.1 U1.78 U2.19 U3.4 U4.5 U5.1",
    "SD_CLK": "CARD1.5 U1.8",
    "SD_CS": "CARD1.2 R21.2 U1.7",
    "SD_MISO": "CARD1.7 R18.2 U1.6",
    "SD_MOSI": "CARD1.3 U1.9",
    "SD_DAT1": "CARD1.8 R19.2",
    "SD_DAT2": "CARD1.1 R20.2",
    "QSPI_SS": "R11.1 U1.75 U14.1",
    "QSPI_SD1": "U1.74 U14.2",
    "QSPI_SD2": "U1.73 U14.3",
    "QSPI_SD0": "U1.72 U14.5",
    "QSPI_SCLK": "U1.71 U14.6",
    "QSPI_SD3": "U1.70 U14.7",
    "BOOTSEL": "R11.2 SW2.1 SW2.2",
    "RUN": "C28.1 R16.2 U1.35",
    "SWDIO": "H1.3 H2.3 U1.34",
    "SWCLK": "H1.4 H2.1 U1.33",
    "RBF": "H1.13 U1.11",
    "SERVO1_SIG": "U1.79 U8.1",
    "SERVO2_SIG": "U1.80 U9.1",
    "SERVO3_SIG": "U1.1 U10.1",
    "SERVO4_SIG": "U1.2 U11.1",
    "H1_GP37": "H1.7 U1.46",
    "H1_GP36": "H1.8 U1.45",
    "H1_GP35": "H1.9 U1.44",
    "H1_GP34": "H1.10 U1.43",
    "BNO_RESET": "R9.1 U2.11",
    "BNO_CAP": "C27.1 U2.9",
    "MAG_CAP": "C25.1 U5.4",
    "USB_DP": "D1.3 D1.4 R7.2 USBC1.A6 USBC1.B6",
    "USB_DM": "D1.1 D1.6 R8.2 USBC1.A7 USBC1.B7",
    "USB_DP_MCU": "R7.1 U1.67",
    "USB_DM_MCU": "R8.1 U1.66",
    "USB_VBUS": "D1.5 D2.2 USBC1.A4B9 USBC1.B4A9",
    "CC1": "R12.1 USBC1.A5",
    "CC2": "R13.1 USBC1.B5",
}

# Pins that must be left floating.
MUST_BE_FLOATING = {"U1.40"}

# Parts intentionally left unstuffed.
DNP = set()


def parse_tel(path):
    """Parse an EasyEDA .tel netlist into {net_name: set(pins)}."""
    text = open(path, encoding="utf-8", errors="replace").read()
    body = text.split("$NETS", 1)[1].split("$SCHEDULE", 1)[0]

    nets, current, buf = {}, None, []
    for line in body.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        m = re.match(r"\s*'([^']+)'\s*;\s*(.*)$", line)
        if m:
            if current:
                nets[current] = set(" ".join(buf).split())
            current = m.group(1)
            buf = [m.group(2).rstrip(",")]
        elif current:
            buf.append(line.strip().rstrip(","))
    if current:
        nets[current] = set(" ".join(buf).split())
    return nets


def expand(spec):
    return set(spec.split())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    actual = parse_tel(sys.argv[1])
    target = {name: expand(spec) for name, spec in TARGET.items()}

    # Map every pin to the net it actually sits on.
    pin_actual = {}
    for net, pins in actual.items():
        for p in pins:
            pin_actual[p] = net

    pin_target = {}
    for net, pins in target.items():
        for p in pins:
            pin_target[p] = net

    errors = warnings = 0
    print(f"netlist : {sys.argv[1]}")
    print(f"nets    : {len(actual)} found, {len(target)} expected")
    print(f"pins    : {len(pin_actual)} connected, {len(pin_target)} expected")
    print()

    # --- 1. oversized nets (merge detector) -------------------------------------------------
    gnd_size = len(target["GND"])
    for net, pins in sorted(actual.items(), key=lambda kv: -len(kv[1])):
        if len(pins) > gnd_size:
            print(f"MERGE   {net} has {len(pins)} pins (max expected {gnd_size} on GND)")
            errors += 1
            break

    # --- 2. two-terminal parts shorted end to end -------------------------------------------
    # Infer pin count per refdes across the whole netlist rather than guessing from the prefix,
    # so multi-pin parts that share a designator style (D1, the 6-pin ESD array) aren't flagged.
    pins_per_ref = defaultdict(set)
    for pin in pin_actual:
        if "." in pin:
            ref, num = pin.rsplit(".", 1)
            pins_per_ref[ref].add(num)

    shorted = []
    for net, pins in actual.items():
        by_ref = defaultdict(set)
        for p in pins:
            if "." not in p:
                continue
            ref, pin = p.rsplit(".", 1)
            by_ref[ref].add(pin)
        for ref, pset in by_ref.items():
            if len(pins_per_ref[ref]) == 2 and len(pset) == 2:
                shorted.append((ref, net))
    for ref, net in sorted(set(shorted)):
        print(f"SHORT   {ref} has both terminals on {net}")
        errors += 1

    # --- 2b. one target net spread across several actual nets (split detector) ---------------
    # A rail broken into two islands still "matches" per-pin, so check it explicitly.
    carriers = defaultdict(set)
    for net, pins in actual.items():
        overlap = {n: len(pins & ps) for n, ps in target.items()}
        best = max(overlap, key=overlap.get)
        if overlap[best] > 0:
            carriers[best].add(net)
    for tgt, nets_holding in sorted(carriers.items()):
        if len(nets_holding) > 1:
            print(f"SPLIT   {tgt} is divided across {len(nets_holding)} nets: "
                  f"{', '.join(sorted(nets_holding))}")
            errors += 1

    # --- 3. pins on the wrong net -----------------------------------------------------------
    # Group by (expected net, actual net) so the output stays readable.
    misplaced = defaultdict(list)
    for pin, want in sorted(pin_target.items()):
        got = pin_actual.get(pin)
        if got is None:
            misplaced[(want, "UNCONNECTED")].append(pin)
            continue
        # Build the equivalence: which target net does this actual net mostly correspond to?
        members = actual[got]
        overlap = {n: len(members & ps) for n, ps in target.items()}
        best = max(overlap, key=overlap.get)
        if best != want:
            misplaced[(want, f"{got} (~{best})")].append(pin)

    for (want, got), pins in sorted(misplaced.items()):
        print(f"WRONG   should be on {want}, found on {got}:")
        print(f"          {' '.join(pins)}")
        errors += len(pins)

    # --- 4. pins that must float ------------------------------------------------------------
    for pin in sorted(MUST_BE_FLOATING):
        if pin in pin_actual:
            print(f"WRONG   {pin} must be unconnected, found on {pin_actual[pin]}")
            errors += 1

    # --- 5. connected pins not in the target ------------------------------------------------
    extra = sorted(set(pin_actual) - set(pin_target) - MUST_BE_FLOATING)
    for pin in extra:
        ref = pin.rsplit(".", 1)[0]
        tag = "DNP part" if ref in DNP else "not in the target netlist"
        print(f"EXTRA   {pin} on {pin_actual[pin]}, {tag}")
        warnings += 1

    print()
    if errors == 0 and warnings == 0:
        print("PASS, netlist matches the build sheet.")
        return 0
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
