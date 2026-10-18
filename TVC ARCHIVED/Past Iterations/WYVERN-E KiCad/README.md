# WYVERN-E KiCad Flight Computer Boards

| Project | Board | State |
|---|---|---|
| `FC100/WYVERN-E_FC100` | Ø92.1 mm round, 4 layers, for the 100 mm airframe | Rev 3.2, JLCPCBA release: 0 DRC violations (errors and warnings), 0 unconnected, 0 parity issues, ERC 0. Order files in `FC100/jlcpcb/` |
| `FC70/WYVERN-E_FC70` | Ø66.1 mm round, 4 layers, for the 70 mm airframe | Rev 3.2, JLCPCBA release: same checks all at 0. Order files in `FC70/jlcpcb/` |

Open either `.kicad_pro` in KiCad 10. Symbol and footprint libraries live inside each project.

## FC100 rev 3: JLCPCBA release

Rev 3 is FC100 re-issued for a turnkey JLCPCB assembly order. The schematic was corrected, the board re-placed and re-routed, and every placed part carries an LCSC number that was checked against JLCPCB's live assembly stock (JLCPCB parts API) on 2026-10-04. The order files are in `FC100/jlcpcb/`.

### What changed electrically

| # | Block | Rev 2 problem | Rev 3 fix | Source |
|---|---|---|---|---|
| 1 | USB-C / PD | CH224K (U2) was out of stock at JLC (0 pcs). Its VBUS pin was floating and its D+/D− shared the RP2350 USB pair. | U2 removed. CC1/CC2 get 5.1 kΩ Rd (R40, R41), so the board sinks plain 5 V at up to 3 A. The BQ25798 is a buck-boost, so it charges the 2S pack from 5 V with no PD needed. | CH224K datasheet; BQ25798 DS §8.3 |
| 2 | Charger | PROG R12 = 100 Ω (not in the PROG table) | R12 = 8.2 kΩ → 2S, 750 kHz | BQ25798 DS, PROG table |
| 3 | Charger | L4 3.3 µH | L4 2.2 µH FHD4020S-2R2MT (the 750 kHz value) | BQ25798 DS, inductor selection |
| 4 | Charger | TS had only the NTC to GND, so it would read "cold" and block charging | RT1 5.1 kΩ (REGN→TS), RT2 30 kΩ (TS→GND) with the 10 kΩ NTC R1 | BQ25798 DS, TS section |
| 5 | Charger | No VBUS, PMID, SYS or BAT capacitors besides C10 and one 100 nF | VBUS 2×10 µF + 100 nF, PMID 3×10 µF + 100 nF, SYS 3×10 µF + 100 nF + 10 µF at each buck input, BAT 2×10 µF (all 25 V X5R 0805) | BQ25798 DS §9.2.2 |
| 6 | Charger | BTST caps 100 nF | 47 nF, 50 V | BQ25798 DS |
| 7 | Charger LED | LED2 anode went to GND through R8, so it could never light | R8 (2.2 kΩ) now feeds LED2 from REGN, STAT sinks the cathode | — |
| 8 | 3V3 buck | TPS563201 EN floating. EN has an internal pull-down, so the 3V3 rail would never start. | EN tied to VSYS (EN abs max 19 V) | TPS563201 DS |
| 9 | 3V3 buck | No output capacitors; FB 330k/100k | 2×22 µF out; FB 33k/10k → 3.302 V | TPS563201 DS table 7-2 |
| 10 | Servo buck | L3 2.2 µH (TI table says 15 µH at 5 V/500 kHz), no output caps, FB 748k/100k | L3 10 µH SWPA6045 (Isat 3.5 A), 2×22 µF out, 75 pF feed-forward, FB (47k+27k)/10k → 5.006 V | TPS54202 DS table 7-2 |
| 11 | RP2350 | PSRAM CS on GPIO33. QMI CS1n only exists on GPIO0/8/19/47, so the PSRAM was unreachable. | PSRAM_CS → GPIO47, U32 pin 3 → GPIO40/ADC0. The other GPIO functions moved in the pin swap (see `fc100_board.h`). | RP2350 DS, GPIO function table |
| 12 | RP2350 | VREG_AVDD direct to 3V3, no 4.7 µF on VREG_VIN or DVDD, 1 µH core inductor | 33 Ω + 4.7 µF AVDD filter, 4.7 µF on VREG_VIN and DVDD, L1 = 3.3 µH Abracon AOTA-B201610S3R3 | Hardware design with RP2350 |
| 13 | RP2350 | No USB series resistors | 27 Ω on D+/D− at the MCU (R42, R43) | Hardware design with RP2350 |
| 14 | RP2350 | 12 MHz HC-49 crystal, 18 pF, no drive limiting | ABM8-272-T3 (the reference crystal), 15 pF, 1 kΩ in XOUT | Hardware design with RP2350 |
| 15 | RP2350 | No BOOTSEL button | U35 + 1 kΩ on QSPI_SS | Hardware design with RP2350 |
| 16 | RP2350 | W25Q32JVSSIQ: 1 pc in stock | W25Q128JVSIQ (16 MB, JLC Basic, same SOIC-8 208 mil) | — |
| 17 | Status LED | LED1 anode to GND, cathode to GPIO via R9, so it could never light | LED1 anode via 330 Ω from GPIO32, cathode to GND: active high | — |
| 18 | INA226 | U8 and U9 both A0=A1=GND → both 0x40 | U9 A0 → VS → 0x41. ALERT pins left open (they were shorted to GND). | INA226 DS address table |
| 19 | ADAU1450 | DVDD (1.2 V) pins had only C35 bulk | 4×100 nF on DVDD pins 20/35/53/71 plus 100 nF on each IOVDD, AVDD and PVDD | ADAU1450 DS |
| 20 | LSM9DS1 | CAP pin 100 nF | 10 nF | ST LSM9DS1 DS §4.1 |
| 21 | Decoupling | Sensors and memories had no local cap | 100 nF at U6, U7, U8, U9, U10, U11, U12, U13, U14 (×2), U15 (×2), U17; 10 µF at the microSD socket | — |
| 22 | Charger | Bootstrap caps were cross-wired: C17 (BTST1) sat on SW2 and C18 (BTST2) on SW1. The high-side gate drives would have been referenced to the wrong switch node. | C17: BTST1→SW1, C18: BTST2→SW2, 47 nF each | BQ25798 DS pin table |
| 23 | USB | D+/D− were shared three ways (USB-C, RP2350, BQ25798 BC1.2 detection) | BQ25798 D+/D− left open, so the pair runs point-to-point. Firmware sets the input limit over I²C instead. | — |

ILIM_HIZ tied to REGN is correct and stays. VILIM_HIZ = 1 V + 0.8 Ω·IINDPM, so REGN (5 V) gives the hardware maximum. HIZ only happens below 0.75 V. The rev 2 note that called it an HIZ bug was wrong. The input limit is set in firmware (REG06).

### FC100 rev 3 status

| Check | Result |
|---|---|
| ERC | 0 violations |
| DRC errors (clearance, short, hole, edge, thermal, courtyard) | 0 |
| Open connections | 0 |
| Schematic ↔ PCB parity | 0 issues |
| DRC warnings left | 0 (rev 3.2 silkscreen clean-up) |
| Parts | 166 placed (all top side): 165 assembled + TP1 (bare SWD pad, DNP), plus 4 mounting holes |
| Copper | 2,611 track segments; 533 vias; 40 zones |
| BOM | 64 lines, 165 placements, every line has an LCSC number |

### Routing, layers, widths

| Layer | Use | Cu |
|---|---|---|
| F.Cu | parts, signals, GND pour, high-current pours | 1 oz |
| In1.GND_SIG | GND pour, with short signal escapes under the RP2350/ADAU1450 where the pour flows around them | 0.5 oz |
| In2.SIG_PWR | signals + +3V3 pour | 0.5 oz |
| B.Cu | signals, GND pour, high-current pours | 1 oz |

Stackup JLC04161H-7628, 1.6 mm. Order it as 4 layers, 1.6 mm, ENIG, "specified stackup: JLC04161H-7628".

| Class | Routed / widened to | Clearance | Via | Notes |
|---|---|---|---|---|
| Default (logic) | 0.10–0.15 mm | 0.10 mm | 0.5 / 0.3 mm | JLC multilayer standard capability is 0.09/0.09 mm, so 0.10/0.10 is inside the no-surcharge envelope |
| Power (+3V3, +1V1, +1V2_DSP, REGN, VREG, GND) | up to 0.5 mm | 0.127 mm | 0.5 / 0.3 mm | +3V3 also on the In2 pour; GND on three pours |
| HighCurrent (VBAT, VBUS, VSYS, PMID, SW nodes, VSERVO, pyro outputs) | up to 1.5 mm + priority-5 copper pours hugging every track | 0.15 mm | 0.8 / 0.4 mm | Routed on outer layers only |
| USB | 0.25–0.28 mm, point-to-point USB-C ↔ 27 Ω ↔ RP2350 | 0.10 mm | 0.5 / 0.3 mm | Full-speed 12 Mb/s |

The BQ25798 power stage is hand-placed and pre-routed in the TI EVM pattern: L4 sits directly over the PMID/SW1/GND/SW2/SYS bars, PMID caps on the left, SYS caps on the right, VBUS and BAT caps below them. The GND bar drops straight into three vias between the inductor pads, and pins 10/11/13/27 join under the package (the RQM package has no exposed pad). The RP2350 got a 1.3 mm escape ring with no parts in it.

GPIO pin swap: every freely assignable GPIO (H1 header, 9 servo outputs, aux header, interrupts, LED, card-detect, PDM audio) was re-assigned to the RP2350B pin nearest its destination. This is a Hungarian assignment on pad distance, and it cut total wirelength from 1001 mm to 769 mm. Nets are now named by function (`SERVO_U19`, `HDR_P1`…). `firmware/fc100_bringup/fc100_board.h` is generated from the netlist by `tools/gen_fwpins.py`, so code and copper can't drift apart.

### JLCPCB order

1. PCB: upload `FC100/jlcpcb/WYVERN-E_FC100_gerbers.zip` (Gerbers + Excellon, PTH and NPTH separate). Options: 4 layers, 1.6 mm, JLC04161H-7628, ENIG. Use "Via covering: epoxy filled & capped" (POFV) if you can, because the RP2350/ADAU1450 exposed pads and a few QFN-adjacent pads have vias in them. Plain tented is the fallback; expect slightly more solder voiding on the EPs.
2. Assembly: top side, upload `WYVERN-E_FC100_BOM.csv` and `WYVERN-E_FC100_CPL.csv`. The CPL is in the Gerber coordinate frame (aux origin at the board's bottom-left corner), rotations 0–359°. EasyEDA-origin footprints carry JLC's own orientation. The KiCad-library ones were corrected (SOT-223 +180°).
3. In the placement preview, check these by eye before confirming: U34 (AMS1117, tab up), L1 (AOTA inductor, polarity dot toward VREG_LX, i.e. toward U1), LED1/LED2 (cathode marks), D1/D2, U3/U1/U18 pin-1 dots.
4. Through-hole parts are in the BOM with LCSC numbers (C10, CN1, H1, U19–U33 connectors). Keep them for JLC's THT assembly, or untick them and hand-solder.
5. The cost estimate at 2026-10-04 prices is about $77/board in parts. 40 of the 64 lines are JLC "extended" parts (about $3 setup each, per order).

Stock is thin on three parts, enough for a prototype run: LPS22HBTR 51 pcs, LSM9DS1TR 71, ADAU1450 79. Everything else is in the hundreds or more. Check again on the day you order.


### 3D models

Every assembled part (165 of 165) carries its manufacturer 3D model, pulled from the LCSC/EasyEDA library for its exact LCSC number. Only TP1 (bare test pad) and the four mounting holes have none, by design.

- Models live in `FC100/3dmodels/` (STEP) and are referenced as `${KIPRJMOD}/3dmodels/…`, so they travel with the project. The project footprint library has the same model links, so "Update footprints from library" keeps them.
- Alignment was computed per footprint, not trusted blindly. Each model's pads were matched to the board footprint's pads to get rotation and offset (the SOT-223 needed 180°). EasyEDA's STEP files were checked against their VRML twins, and 14 had origin shifts (Z on the passives, XY on the 1×4 headers, microSD socket, USB-C and JST-XH), which were corrected. The PSRAM (USON-8) only had a VRML model, so it was converted to STEP.
- `FC100/WYVERN-E_FC100.step` is the full assembled board (all 165 models, no copper) for mechanical fit checks in the airframe CAD.
- Renders: `FC100/renders/*_3d_top.png`, `*_3d_bottom.png`, `*_3d_iso.png`.

### USB-C access (rev 3.1)

USBC1 (TYPE-C-31-M-12, C165948) was moved 3.13 mm toward the board edge. Before the move its receptacle face sat 2.2–2.7 mm inside the 92 mm outline, so the board edge stopped a standard plug overmold before it seated.

- Receptacle face is now at y = 53.67 mm. The outline's closest point under the plug (x = 100) is at 54.00, so the shell overhangs the edge by 0.33 mm at the center and up to 0.9 mm at the left corner, and nothing on the board sits in the plug's path.
- The plug overmold (USB-IF max 12.35 × 8.25 mm) clears both tact switches (U35 BOOTSEL, U16 RUN) and the H1 header, all of which sit behind the receptacle face.
- Routing was dragged with the connector. Three GND stitching vias under the new shell position were removed, the VBUS escape was re-jogged to clear shell leg 2, and the shell-to-R41 GND stub was replaced by a GND via at (91.48, 61.50). DRC: 0 errors, 0 unconnected; ERC 0; parity clean.
- The USB-C 3D model was also fixed. add3d had it 2.4 mm behind its footprint, and it is now pinned at offset (0, −2.448, 0), rotation 180°, with shell legs on their pads.
- In the CPL, only USBC1's Y changed (84.1984 → 87.3284 mm).
- Airframe: the port faces radially outward at the 12 o'clock position of the top view (≈3.4° left of the +Y axis, board-center bearing). It needs an airframe or sled cut-out of at least 14 × 10 mm, centered 1.6 mm above the top copper (receptacle centerline).

## Firmware

`firmware/fc100_bringup/`:

- `fc100_board.h`: the full pin map and every I²C address, generated from the KiCad netlist.
- `fc100_bringup.ino` (arduino-pico): probes both I²C buses against the expected address list, configures the BQ25798 (watchdog off, AUTO_INDET off, 1.0 A charge, 1.5 A input limit, ADC on) and reads VBUS/VBAT/VSYS, reads both INA226s, checks the 8 MB PSRAM on GPIO47, and mounts the SD card.

Run it before the flight code. The current `wyvern4_tvc` firmware targets the Pico 2 W perfboard (BNO085s on GP0/GP1, servos on GP2/GP3), so it needs this header swapped in: sensors are on I2C0 = GPIO12/13 and the system bus on I2C1 = GPIO14/15. The BQ25798 register addresses in the sketch are from the TI register map. Confirm them against section 9.5 of the datasheet before the first powered run.

Flashing: hold BOOTSEL (U35), tap RUN (U16), then drop the UF2. SWD is on H1 pin 14 (SWDIO) and test pad TP1 (SWCLK).

## Regenerating

`tools/` holds the full pipeline (Python 3, KiCad 10 pcbnew, Freerouting 2.1): EasyEDA parser → schematic (`run_sch.py cfg100 geom`) → floorplan placement (`place.py`) → stage/pre-route (`route_stage.py`) → Freerouting → `finalize.py` → repair/rip-up (`targeted.py`, `repair2.py`, `polish3.py`) → `widenonly.py`, `hcpour.py`, `zonecfg.py`, `tidy.py` → `jlc_export.py`. `jlc.py` queries JLCPCB's parts API for stock and Basic/Extended status. The configs reference the extracted EasyEDA files by absolute path, so edit `epru=` in `cfg100.py`/`cfg70.py` before re-running. FC70 rev 3 uses `cfg70r3.py`. The rev 3.2 clean-up scripts are `silk2.py` (silkscreen), `bottleneck.py` (current-path check), `dfm.py` (JLC capability audit), `collide.py` (3D body overlap), `widennet.py`/`splitnet.py`/`addvias.py` (power copper).

## FC70 rev 3: JLCPCBA release

FC70 got the same treatment as FC100: corrected schematic, LCSC part numbers checked against JLCPCB's live stock (2026-10-09, every line in stock), a new floorplan, and a full re-route.

### Schematic fixes

| # | Rev 2 problem | Rev 3 fix | Source |
|---|---|---|---|
| 1 | RP2350 VREG: three 4.7 µF on AVDD, none on VREG_VIN | C4/C5 moved to the 3V3 input, 4.7 µF on AVDD after the 33 Ω, 4.7 µF on DVDD | Raspberry Pi, *Hardware design with RP2350*, §2.3 |
| 2 | Too few IOVDD bypass caps for 8 IOVDD pins | C36–C39 added (100 nF each) | same |
| 3 | No HF bypass at either TPS564201 VIN | C40, C41 100 nF next to VIN/GND | TI TPS564201 DS §8.2.2.4 |
| 4 | AP2112K input had no local cap | C42 1 µF | Diodes AP2112 DS |
| 5 | BNO055 BL_IND (an output) tied to GND | Left unconnected | Bosch BNO055 DS, table 5-1 |
| 6 | microSD shell floating, no card detect | Shell tabs to GND, CD to GPIO13 | Hroparts TF-01A drawing |
| 7 | USB-C shell and JST-SH tabs floating | Tied to GND | |
| 8 | Servo PWM on pins far from the servo connectors | SERVO1–4 on GPIO41/39/38/40 (four separate PWM channels, facing the connectors) | RP2350 DS, PWM table |
| 9 | 12 MHz crystal ~40 mm from the RP2350, XIN not even connected | Crystal next to XIN/XOUT, routed | |
| 10 | No 10 µF bulk at the microSD socket | C35 10 µF | |
| 11 | Slide switch U13 was on LCSC C2884744 (SS-12D10G5, 4.7 mm pitch, 1.7 mm holes) while the footprint is SS12D00G3 (2.5 mm pitch) | Changed to C22355741 SS-12D00-G3, which matches the footprint | LCSC listing |

The firmware pin map is generated from the netlist: `firmware/fc70_pins/fc70_board.h`.

### FC70 JLCPCB order

Same procedure as FC100, using `FC70/jlcpcb/`: 4 layers, 1.6 mm, JLC04161H-7628, ENIG; top-side assembly with `WYVERN-E_FC70_BOM.csv` and `WYVERN-E_FC70_CPL.csv` (aux origin at the bottom-left corner). Through-hole parts with LCSC numbers: XT30 (CN1), four JST-XH servo connectors (U8–U11), H1/H2 headers, slide switch U13. Lowest stock on 2026-10-09 was the AOTA 3.3 µH (L1) at 134 pcs and the 1×14 header at 488. In the placement preview, check L1's polarity dot, D1/D2 cathodes, the TPS564201 (U6/U15) and RP2350 pin-1 dots.

All 95 assembled FC70 parts carry LCSC/EasyEDA STEP models in `FC70/3dmodels/`, checked by exporting each part and comparing its body to its pads; `FC70/WYVERN-E_FC70.step` is the assembled board.

### FC70 layout notes

- USB-C receptacle face sits 0.10 mm past the outline at its closest point, so the plug overmold never touches the board. The fan-out between the 0.5 mm-pitch pads uses a 0.10 mm clearance rule that only applies inside the USBC1 and D1 courtyards (JLC minimum is 0.09 mm).
- Battery path: the XT30 feeds the 10 mΩ shunt through a 1.8 mm bottom-layer bar plus the original top route, with five 0.3 mm vias into the shunt pad.
- Servo buck switch node rebuilt: 0.7–1.2 mm from U6 pin 2 to L3. Its EN line was moved out from under the IC.
- High-current nets have local pours (`HC_*` zones) over their tracks on F.Cu.

## Rev 3.2 checks (both boards, 2026-10-09)

All numbers below are from the files in this package.

| Check | FC100 | FC70 | JLCPCB 4-layer capability |
|---|---|---|---|
| DRC errors / warnings / unconnected / parity | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | |
| ERC errors / warnings | 0 / 0 | 0 / 0 | |
| Min track | 0.10 mm (71 QFN escape segments, rest ≥ 0.127) | 0.15 mm | 0.09 mm |
| Min clearance | 0.10 mm (fine-pitch rules, scoped to courtyards) | 0.10 mm (same) | 0.09 mm |
| Vias | 0.5/0.3, 0.6/0.3, 0.8/0.4 mm | 0.5/0.3, 0.6/0.3, 0.8/0.4 mm | 0.3 mm hole is the no-surcharge size |
| Min via annular ring | 0.10 mm | 0.10 mm | — |
| Min PTH drill / ring | 0.8 mm / 0.20 mm | 0.8 mm / 0.20 mm | — |
| Silkscreen | 0.15 mm lines, refs 1.0 mm (0.8 mm where tight) | same | 0.153 mm line, 0.8 mm text |
| Placed parts with LCSC # / in stock | 165 / 165 | 95 / 95 | |
| 3D bodies overlapping each other | 0 | 0 | |

### Silkscreen

`tools/silk2.py` re-placed every reference designator:

- Outline segments that crossed pads were clipped.
- A ref only goes on silk if it sits next to its own part and clearly closer to it than to any other part. Big parts carry their ref inside the body.
- Refs that can't meet that go to the Fab layer, so the assembly drawing still has them.
- No silk touches a pad, another legend or the board edge.

### Current capacity

`tools/bottleneck.py` finds the widest copper path between the pads that actually carry power. It counts tracks, pours and vias, and ignores the first 2.5 mm at each pin. The design currents are realistic flight loads: 3.5 A battery, 3 A servo rail, 3 A USB. Pass mark is the IPC-2221 external-layer width for a 20 °C rise.

| Path | Narrowest copper | Status |
|---|---|---|
| FC100 USB VBUS → charger caps | 0.5 mm (A-side), 1.5 mm main run | Short necks at the 0.5 mm-pitch connector; most of the 33 mm run along the edge was widened from 0.2 to 1.2–1.5 mm (0.5 mm past the BOOTSEL switch) |
| FC100 VBAT charger ↔ shunt | 4 vias in parallel + pours | OK |
| FC100 VSYS → servo buck | 4 vias + 2.9 mm pour | OK |
| FC100 servo rail branches | 0.2 mm necks ≤ 2.4 mm long (between connector pins and past C57) | Fine for one servo per branch (≈1 A). It is the one place on either board where a long 2-servo stall could warm the trace; nothing larger fit there. |
| FC70 battery → shunt | 1.8 mm B.Cu bar + 5 vias | OK |
| FC70 shunt → servo PTC | 3–4 vias each end + 1.0 mm | OK |
| FC70 servo buck SW / VSERVO | 2.6 mm / 3.0 mm pours | OK |

Narrow tracks that remain on these nets are Kelvin sense lines to the INA226s and bootstrap-cap links, which carry microamps to milliamps.
