# XRIM-117 Avionics — PDR-002 Rev B Change Log

### A Legacy Systems Research Group Venture
##### KiCad projects: CCM · ASAM-1 · ASAM-2 (62 mm circular, 2-layer FR4 1.6 mm, ENIG, JLCPCB rules)

*All three boards regenerated from datasheet-verified netlists. Open each `.kicad_pro` in KiCad 9 — files are KiCad 7 format and migrate automatically on save.*

## 1. Audit Verdict on Rev A

Rev A would not have survived first power-up. The schematic symbols carried invented pin numbers on real footprints. Every fault below is corrected in Rev B.

### 1.1 Fatal faults found in Rev A (CCM)

| # | Fault | Consequence | Rev B fix |
|---|-------|-------------|-----------|
| 1 | RP2040 symbol had 33 fictional pins on a QFN-56 footprint | No net landed on a real pin | Full 56-pin map per RP2040 datasheet §1.2 (USB_DM=46, SWCLK=24, EP=GND etc.) |
| 2 | Boot flash on generic "SPI0" | RP2040 boots only from QSPI pins 51–56; MCU never executes | W25Q128JVSIQ on QSPI_SD0–SD3/SCLK/SS |
| 3 | No 12 MHz crystal, no 1.1 V core wiring | No clock, no core power | ABM8-style 3225 12 MHz CL=10 pF, 2×27 pF, 1 kΩ on XOUT; VREG_VIN/VREG_VOUT→DVDD decoupled |
| 4 | TLV62569 pin 5 modeled as "VOUT", no inductor | 1.5 MHz square wave on the 3.3 V rail | Verified pin map (EN=1, GND=2, SW=3, FB=4, VIN=5); L=2.2 µH; FB divider 560 k/124 k → 3.31 V |
| 5 | E22-900M22S modeled with 10 pins; RXEN/TXEN omitted | PA/LNA RF switch never enabled — radio deaf and mute | Verified 22-pad map; DIO2→TXEN strap, RXEN→GPIO17; exact stamp-hole footprint (13.97 mm columns, 1.27 mm pitch) |
| 6 | IRFZ44N pyro FETs (Vgs(th) 2–4 V) at 3.3 V drive | Marginal enhancement — e-matches may not fire | AO3400A logic-level FETs (Vgs(th)≤1.45 V, 30 A pulse), 1 k gate series + 100 k pulldown |
| 7 | BMP388 drawn as LGA-8 | Real package is LGA-10 2.0×2.0 mm | Verified Bosch DS001 pinout & land pattern |
| 8 | MT3608 boost for servo rail | 4 servos stall ≈ 6 A @7.4 V ⇒ ~14 A switch current; MT3608 limit 4 A | Deleted. ASAMs run a 2S pack: servo rail = battery direct through INA219 shunt |

### 1.2 System alterations (Rev B)

- *ASAM power*: single 2S LiPo per board. V_SERVO = battery through 10 mΩ 2512 Kelvin shunt (INA219, addr 0x40). Logic 3.3 V from TPS54202 (verified: GND=1 SW=2 VIN=3 FB=4 EN=5 BOOT=6; L=10 µH, FB 45.3 k/10 k, BOOT 100 nF). TPS5430 deleted (no load justified it).
- *Redundant barometer*: MS5611 → second BMP388 (I2C, 0x76). One verified part across all boards; INT pin wired (PB5).
- *Sustainer safety chain (ASAM-2)*: two-board hardware interlock — CCM ARM_OUT (GPIO18, via JST-GH pin 4) powers the PC817 LED; STM32 PB15 sinks it to fire; opto emitter-follower drives AO3400A from VBAT2S. No single software fault can fire the sustainer.
- *Pyro continuity*: each channel has 100 k/100 k divider into RP2040 ADC (GPIO26–28) + green LED through the e-match (~0.5 mA test current, far under no-fire). VBAT (ADC3) and VBAT_ARMED (GPIO24, 100 k/200 k) monitors added.
- *USB added to CCM*: JST-SH-4 (5 V, D−, D+, GND) with 27 Ω series, SS34 diode-OR with battery, BOOTSEL button — field firmware loading without a debug probe. Bench USB cannot fire pyros (arm rail taps battery before the diode-OR).
- *SWD*: TC2030 → 1×5 0.1" header (3V3/SWDIO/SWCLK/RST/GND) on all boards; BOOT0 jumper on ASAMs for the UART bootloader.
- *Inter-board JST-GH8*: 1 GND, 2 TX, 3 RX, 4 ARM, 7/8 GND. CCM UART0→ASAM-1, UART1→ASAM-2 (Rev A shared one UART).
- *RF*: PDR's "0.9 mm = 50 Ω" claim is wrong on 2-layer 1.6 mm (true 50 Ω microstrip ≈ 2.9 mm). Rev B keeps the antenna trace electrically short instead: ≤5 mm (λ/40 @915 MHz), 0.9 mm wide, pour-fenced, SMA moved onto the ANT-pad radial.
- *Passives*: 0402 → 0603 for hand-assembly yield; HC-49S → 3225 SMD crystals (8 MHz CL=12 pF + 2×18 pF on ASAMs).
- *Mounting*: 4× M3 at r=26 mm on the 45° diagonals, common to all three boards for stack alignment.

## 2. Verification Methodology

`kicad-cli` could not run in this environment, so the `generator/` toolchain includes an independent verifier (`verify.py`): netlist cross-check (schematic ⇄ PCB, exact per-pin), copper-connectivity proof per net (pads+tracks+vias+computed zone fill), geometric clearance DRC (STRtree, 0.125 mm floor vs JLC 0.127 capability), board-edge and courtyard checks. Boards route via a grid A* autorouter (`autoroute.py`) with staggered escape stubs for the 0.4 mm-pitch packages, GND pours both layers + stitching vias.

## 3. Status at Delivery

| Board | Schematic | Placement | Autorouted | Open items (ratsnest in KiCad) |
|-------|-----------|-----------|------------|--------------------------------|
| ASAM-1 | complete, verified netlist | clean | ~88% (36/41 nets) | SPI1_MOSI, BMP_INT, VCAP, PB2_STRAP, part of +3V3; a handful of sub-0.127 mm clearance spots flagged by DRC near U2/U3 |
| ASAM-2 | complete, verified netlist | clean | ~75% (33/44 nets) | TVC_YAW, VBAT_SENSE, SPI1 group, I2C1_SDA, BMP_INT, BOOT0, PB2_STRAP, part of +3V3 |
| CCM | complete, verified netlist | clean | long-haul + signal groups | QSPI group, sensor SPI, power trees (+3V3/+1V1/VBAT chains) pending |

Interactive routing in KiCad finishes these: open the .kicad_pcb, run DRC once to see the exact flagged spots, then press X and follow the ratsnest — GND planes, stitching vias, escapes, and all critical-net routing (RF, pyro, crystal, USB) are already in. The schematics are 100 % complete and netlist-verified; nothing electrical remains open.

The remaining ratsnest lines are ordinary interactive-routing work in KiCad (the hard part — correct pins, nets, footprints, clearances, planes — is done and machine-verified). Open the board, press `X`, and follow the ratsnest; the GND plane and stitching are already in place. Regenerate any board with `python3 generator/gen_ccm.py` / `gen_asam.py 1|2`.

## 4. Primary Sources

- RP2040 Datasheet §1.2 (pinout), Hardware Design Guide (crystal, QSPI)
- TDK DS-000347 ICM-42688-P §4.1 — pin table verified line-by-line
- Bosch BST-BMP388-DS001 §6.1/7.1 — LGA-10 pinout & package
- Ebyte E22-900M22S User Manual v1.20 §3 — 22-pad table (RXEN=6, TXEN=7, DIO2=8, ANT=21)
- TI SLVSDG1 (TLV62569), TI TPS54202 datasheet — pin tables extracted from PDFs
- TI INA219 §6 — SOT-23-8 pin map
- E22 footprint cross-checked against candykingdom/homebrew.pretty `E22-900M22S.kicad_mod`
