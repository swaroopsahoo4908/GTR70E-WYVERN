# PCB1 Schematic Rewire, Build Sheet

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong
**Program:** GTR70E WYVERN

Written against the restored schematic exporting as `Netlist_Schematic1_2026-08-13 (3).tel`.
Work the batches in order. Export a netlist and run the checker after each one.

```
cd "Flight Computer"
python3 check_netlist.py /path/to/Netlist_Schematic1_<date>.tel
```

Current state: 49 errors. Target: `PASS, netlist matches the build sheet.`

---

## 0. What is already correct

Don't touch any of this. It all verifies clean:

GND (78 pins, no foreign members) · both I²C nets and all address straps · the whole QSPI flash bus
· all four servo signal lines · SWD · the H1 GPIO breakouts · BOOTSEL · RUN with its pull-up and cap
· BNO055 reset pull-up and CAP cap · USB D+/D− including the B6/B7 orientation bridges · CC1/CC2
pulldowns · SD clock, CS, MISO, DAT1, DAT2 with all four pull-ups · U1.40 correctly left floating ·
the avionics buck's SW, BST and feedback nets · DVDD, VREG_LX, VREG_AVDD.

---

## 1. Parts to add

| Ref | Value | Footprint | Part / LCSC | Purpose |
|---|---|---|---|---|
| F2 | 3.0 A / 16 V PPTC | F2920 | SMD2920P300TF/16, C167318 | Servo branch fuse |
| U6 | TPS564201DDCR | SOT-23-6 | same as U15 | Servo buck |
| L3 | 2.2 µH | IND-SMD_L5.7-W5.1 | same as L2 | Servo buck inductor |
| C29 | 10 µF | C0805 | same as C26 | Servo buck input cap |
| C30 | 100 nF | C0402 | same as C6 | Servo buck bootstrap |
| C31 | 22 µF | C0805 | same as C21 | Servo buck output cap |
| C32 | 22 µF | C0805 | same as C22 | Servo buck output cap |
| R22 | 56 kΩ | R0402 | same as R5 | Servo VFB top |
| R23 | 10.2 kΩ | R0402 | same as R6 | Servo VFB bottom |
| R24 | 24.9 kΩ | R0603 | same as R15 | Servo EN divider bottom |
| R25 | 100 kΩ | R0603 | same as R14 | Servo EN divider top |

Ten of the eleven are duplicates of parts already in your BOM, so the library work is one new part.

F1 also wants swapping to 1812L150/16 (1.50 A hold, same 1812 land pattern). With servos moved to
their own branch, F1 only carries camera plus logic, about 0.49 A at the 6.0 V cutoff.

U13 becomes signal-level in Batch C, carrying microamps instead of pack current, so whichever
SS-12D10 variant is placed is fine — the 2 A rating stops mattering.

---

## 2. Batch A, merge the split 3V3 rail

Your 3V3 rail exists as two disconnected islands:

- `$1N406` — U7.5 and most peripheral supply pins
- `$1N496` — the eight MCU IOVDD pins, U1.68, U1.69, and C8.1–C16.1, C23.1

Nothing bridges them, so the RP2350B's IO supply is floating.

Join them. Label both 3V3, or run one wire from U7.5 to U1.5.

Then move two pins onto that rail:

- C18.1 — disconnect from GND, connect to 3V3
- U1.59 — disconnect from GND, connect to 3V3

That fixes the C18 short and gives ADC_AVDD its supply, with C18 becoming its decoupling cap.

---

## 3. Batch B, SD MOSI and BNO055 PS1

Three pins, all quick.

- CARD1.3 — disconnect from 3V3
- U1.9 — disconnect from 3V3
- CARD1.3 → U1.9 as their own net, SD_MOSI

MOSI is currently shorted to the 3V3 rail, so the card can never be written.

- U2.5 → GND

U2.5 is PS1. With U2.6 (PS0) already grounded, this completes the I²C protocol select. It's floating
right now.

---

## 4. Batch C, battery path and buck enables

This is the substantial one. Present state has the fuse shorting pack positive to ground, the shunt
stranded on a dead-end net, and the avionics buck's enable tied to its own input so the divider does
nothing.

### Disconnect first

- F1.1 from GND
- F1.2 from CN1.2
- U13.1 from GND
- U13.2 from `$1N470`
- R14.1 from 3V3
- U4.9 from 3V3

### Then build these five nets

| Net | Pins |
|---|---|
| VBAT | CN1.2 · R10.1 · U4.8 · U4.10 |
| VBAT_SW | R10.2 · U4.9 · F1.2 · F2.2 · U13.1 |
| VAVI_IN | F1.1 · U15.3 · C26.1 |
| EN_SRC | U13.2 · R14.1 · R25.1 |
| EN_AVI | R14.2 · R15.1 · U15.5 |

U15.3 and C26.1 currently sit on `$1N470` together with U15.5 and the divider. Splitting VAVI_IN
away from EN_AVI is what makes the divider work — right now EN is strapped straight to VIN and R14
and R15 do nothing.

U13 is SPDT with the centre pin common:

- U13.2 (common) → EN_SRC
- U13.1 (throw, ON position) → VBAT_SW
- U13.3 (throw, OFF position) → GND

Switch OFF pulls both enables down through R15 and R24, so nothing powers up until armed.

### Resulting power tree

```
CN1.2 ─ R10 (10 mΩ shunt) ─ VBAT_SW ─┬─ F1 ─ VAVI_IN ─ U15 ─ VBUCK_5V ─ U7 ─ 3V3
                                     ├─ F2 ─ VSRV_IN ─ U6  ─ VSRV_5V ─ servos
                                     └─ U13 ─ EN_SRC ─ both enable dividers
```

INA226 spans the shunt: IN+ (U4.10) on VBAT, IN− (U4.9) on VBAT_SW, VBUS (U4.8) on VBAT. It reads
true pack voltage and total pack current.

$$I_{max} = \frac{81.92\ \text{mV}}{10\ \text{m}\Omega} = 8.19\ \text{A}, \qquad \text{LSB} = 250\ \mu\text{A}$$

Divider output is 1.20 V at a 6.0 V pack and 1.68 V at 8.4 V — above the ~1.2 V EN threshold across
the whole usable window, well under the 19 V EN maximum.

---

## 5. Batch D, crystal series resistor

R1 currently sits on the XIN side. It belongs in series with XOUT, the driver output.

- Remove R1 from between U1.30 and U12.1
- U1.30 → U12.1 → C1.1 direct (net XIN)
- U1.31 → R1.1 (net XOUT)
- R1.2 → U12.2 → C2.1 (net XTAL_B)

Load caps stay at the crystal terminals: C1 on the XIN node, C2 on the far side of R1.

---

## 6. Batch E, servo buck

Place the eleven new parts, then wire these nets. This mirrors the U15 circuit exactly — same
topology, same values, same 4.985 V output.

| Net | Pins |
|---|---|
| VSRV_IN | F2.1 · U6.3 · C29.1 |
| SW_SRV | U6.2 · L3.1 · C30.2 |
| BST_SRV | U6.6 · C30.1 |
| VFB_SRV | U6.4 · R22.2 · R23.1 |
| EN_SRV | U6.5 · R25.2 · R24.1 |
| VSRV_5V | L3.2 · C31.1 · C32.1 · R22.1 · U8.2 · U9.2 · U10.2 · U11.2 |
| GND | U6.1 · C29.2 · C31.2 · C32.2 · R23.2 · R24.2 |
| VBAT_SW | F2.2 (from Batch C) |
| EN_SRC | R25.1 (from Batch C) |

Move the servo power pins off the avionics rail as part of this:

- U8.2, U9.2, U10.2, U11.2 — disconnect from `$1N485`, connect to VSRV_5V

VBUCK_5V then keeps only L2.2, C21.1, C22.1, D2.1, R5.1, U7.1, U7.3, H1.12.

$$V_{out} = 0.768 \times \left(1 + \frac{56}{10.2}\right) = 4.985\ \text{V}$$

Servo branch worst case, both servos stalled: 1.6 A at 5 V is 8.0 W, 9.1 W in at 88% efficiency,
1.42 A drawn from the pack at the 6.4 V cutoff. F2 holds 1.99 A at 60 °C — 40% margin.

---

## 7. Batch F, cleanup

R17 (10 kΩ) currently runs from 3V3 to GND and does nothing but draw 330 µA. Mark DNP or delete it.

---

## 8. Complete net reference

Everything above, consolidated. 312 pins across 60 nets.

### GND, 84 pins

C1.2 C2.2 C3.2 C4.2 C5.2 C7.2 C8.2 C9.2 C10.2 C11.2 C12.2 C13.2 C14.2 C15.2 C16.2 C17.2 C18.2
C19.2 C20.2 C21.2 C22.2 C23.2 C24.2 C25.2 C26.2 C27.2 C28.2 C29.2 C31.2 C32.2 · U1.62 U1.81 ·
U2.2 U2.5 U2.6 U2.10 U2.15 U2.16 U2.17 U2.18 U2.25 · U3.1 U3.5 U3.7 · U4.1 U4.2 U4.7 ·
U5.2 U5.3 U5.9 U5.12 · U6.1 U7.2 U15.1 U13.3 · U8.3 U9.3 U10.3 U11.3 · U12.3 U12.4 · U14.4 ·
CARD1.6 CARD1.9 CARD1.10 CARD1.11 · CN1.1 CN2.1 USBC1.A1B12 USBC1.B1A12 ·
H1.2 H1.6 H1.11 H1.14 H2.2 · R6.2 R12.2 R13.2 R15.2 R23.2 R24.2 · D1.2 SW2.3 SW2.4

### 3V3, 49 pins

U7.5 · U1.5 U1.15 U1.24 U1.29 U1.41 U1.50 U1.60 U1.76 · U1.59 U1.64 U1.68 U1.69 ·
C8.1 C9.1 C10.1 C11.1 C12.1 C13.1 C14.1 C15.1 C16.1 C18.1 C23.1 C24.1 · U2.3 U2.4 U2.28 ·
U3.2 U3.6 U3.8 · U4.6 · U5.5 U5.6 U5.10 · U14.8 · CARD1.4 · CN2.2 · H1.1 H1.5 ·
R2.2 R3.2 R4.2 R9.2 R16.1 R18.1 R19.1 R20.1 R21.1

### Power rails

| Net | Pins |
|---|---|
| VBAT | CN1.2 · R10.1 · U4.8 · U4.10 |
| VBAT_SW | R10.2 · U4.9 · F1.2 · F2.2 · U13.1 |
| VAVI_IN | F1.1 · U15.3 · C26.1 |
| VSRV_IN | F2.1 · U6.3 · C29.1 |
| VBUCK_5V | L2.2 · C21.1 · C22.1 · D2.1 · R5.1 · U7.1 · U7.3 · H1.12 |
| VSRV_5V | L3.2 · C31.1 · C32.1 · R22.1 · U8.2 · U9.2 · U10.2 · U11.2 |
| EN_SRC | U13.2 · R14.1 · R25.1 |
| EN_AVI | R14.2 · R15.1 · U15.5 |
| EN_SRV | R25.2 · R24.1 · U6.5 |

### Regulator support

| Net | Pins |
|---|---|
| SW_AVI | C6.2 · L2.1 · U15.2 |
| BST_AVI | C6.1 · U15.6 |
| VFB_AVI | R5.2 · R6.1 · U15.4 |
| SW_SRV | C30.2 · L3.1 · U6.2 |
| BST_SRV | C30.1 · U6.6 |
| VFB_SRV | R22.2 · R23.1 · U6.4 |
| VREG_LX | L1.1 · U1.63 |
| DVDD | C17.1 · C19.1 · C20.1 · L1.2 · U1.10 · U1.32 · U1.51 · U1.65 |
| VREG_AVDD | C3.1 · C4.1 · C5.1 · C7.1 · R2.1 · U1.61 |

### Crystal

| Net | Pins |
|---|---|
| XIN | U1.30 · U12.1 · C1.1 |
| XOUT | U1.31 · R1.1 |
| XTAL_B | R1.2 · U12.2 · C2.1 |

### Signals

| Net | Pins |
|---|---|
| SDA | CN2.3 · R3.1 · U1.77 · U2.20 · U3.3 · U4.4 · U5.11 |
| SCL | CN2.4 · R4.1 · U1.78 · U2.19 · U3.4 · U4.5 · U5.1 |
| SD_CLK | CARD1.5 · U1.8 |
| SD_CS | CARD1.2 · R21.2 · U1.7 |
| SD_MISO | CARD1.7 · R18.2 · U1.6 |
| SD_MOSI | CARD1.3 · U1.9 |
| SD_DAT1 | CARD1.8 · R19.2 |
| SD_DAT2 | CARD1.1 · R20.2 |
| QSPI_SS | R11.1 · U1.75 · U14.1 |
| QSPI_SD1 | U1.74 · U14.2 |
| QSPI_SD2 | U1.73 · U14.3 |
| QSPI_SD0 | U1.72 · U14.5 |
| QSPI_SCLK | U1.71 · U14.6 |
| QSPI_SD3 | U1.70 · U14.7 |
| BOOTSEL | R11.2 · SW2.1 · SW2.2 |
| RUN | C28.1 · R16.2 · U1.35 |
| SWDIO | H1.3 · H2.3 · U1.34 |
| SWCLK | H1.4 · H2.1 · U1.33 |
| RBF | H1.13 · U1.11 |
| SERVO1_SIG | U1.79 · U8.1 |
| SERVO2_SIG | U1.80 · U9.1 |
| SERVO3_SIG | U1.1 · U10.1 |
| SERVO4_SIG | U1.2 · U11.1 |
| H1_GP37 | H1.7 · U1.46 |
| H1_GP36 | H1.8 · U1.45 |
| H1_GP35 | H1.9 · U1.44 |
| H1_GP34 | H1.10 · U1.43 |
| BNO_RESET | R9.1 · U2.11 |
| BNO_CAP | C27.1 · U2.9 |
| MAG_CAP | C25.1 · U5.4 |
| USB_DP | D1.3 · D1.4 · R7.2 · USBC1.A6 · USBC1.B6 |
| USB_DM | D1.1 · D1.6 · R8.2 · USBC1.A7 · USBC1.B7 |
| USB_DP_MCU | R7.1 · U1.67 |
| USB_DM_MCU | R8.1 · U1.66 |
| USB_VBUS | D1.5 · D2.2 · USBC1.A4B9 · USBC1.B4A9 |
| CC1 | R12.1 · USBC1.A5 |
| CC2 | R13.1 · USBC1.B5 |

### Deliberately unconnected

U1.40 (GPIO32) — must stay floating. It was on the 3V3 rail in an earlier revision, which shorts the
pad driver to the rail the first time firmware drives it low.

R17 — DNP.

---

## 9. Verification

The checker reports five failure classes: merged nets, split nets, two-terminal parts shorted end to
end, pins on the wrong net, and pins that must float but don't.

Run it after every batch. If a batch adds errors you didn't expect, you know which wires to look at
while it's still fresh.

---

## 10. Downstream, after the schematic passes

`Flight Computer/firmware/wyvern4_tvc/battery.h` needs rewriting. Its header documents the INA226
reading the buck rail with current sensing disabled as physically meaningless, and uses rail-sag
thresholds of 4.85 / 4.60 V. Once VBUS sits on VBAT and IN+/IN− properly span the shunt, it reads
true pack voltage and current, so it wants real 2S cell thresholds against the 6.4 / 6.0 V firmware
cutoffs and `setMaxCurrentShunt()` restored.

The layout is a separate job: 4-layer stackup with a solid GND pour on layer 2, 5 mil rules at the
QFN, and both regulators built as tight local islands with their input caps inside 2 mm.
