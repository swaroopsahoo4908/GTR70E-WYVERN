# XRIM-117E Avionics — PDR-003 Rev C Change Log

### A Legacy Systems Research Group Venture
##### Finless Airframe · Magnetic Solenoid TVC · 127 mm body · 100 mm avionics stack
##### Master document: *XRIM-117E WYVERN-E V3 (Solenoid TVC)* · Supersedes PDR-002 Rev B

## 1. What Rev C Changes

Rev C deletes all aerodynamic fin control and converts the vehicle to pure electromagnetic thrust vectoring: three custom LSRG-S25 proportional pull solenoids at 120°, acting on a gimbaled motor cradle (±5° authority, spring-return fail-safe neutral). The airframe grows from 70 mm to 127 mm; the avionics stack grows from three 62 mm boards to two 100 mm boards.

### 1.1 Board lineup

| Rev B (retired) | Rev C | Notes |
|---|---|---|
| ASAM-1 (4× fin servos) | — deleted | No fins, no servos |
| ASAM-2 (TVC servos + sustainer) | **SDM** — Solenoid Drive Module | 3× solenoid channels + sustainer + redundant sensors, one board |
| CCM (62 mm) | **CCM** (100 mm) | Electronics unchanged; disc enlarged, connectors moved to the rim |

### 1.2 SDM solenoid drive channels (×3)

Per channel: V_SOL (2S direct) → coil terminal (5.08 mm screw) → AO3400A low-side FET, 20 kHz PWM (TIM1 CH1–CH3 on PA8/PA9/PA10) → 20 mΩ 2512 low-side shunt → GND; SS34 freewheel diode across the coil; shunt voltage RC-filtered (1 kΩ/100 nF) into ADC (PA0/PA1/PB0) for 4 kHz closed-loop current control. Channel hardware sized for 2.0 A continuous / 2.8 A peak per the LSRG-S25 coil spec (3.7 Ω, 16 mH, 480 turns AWG 26). Bus: INA219 + 10 mΩ Kelvin shunt, 3× 470 µF bulk, worst case 6 A.

Pin reallocation vs ASAM-2 (STM32F411): IMU_CS PA4→PB12, ARM_IN PB12→PB13, SUS_CONT PB0→PA4 (ADC4), solenoid senses on PA0/PA1/PB0, PWM on PA8–PA10. Everything else (SPI1, I2C1, USART2, SWD, BOOT0, reed PB10, SUS_FIRE PB15, PC817 interlock) carries over from the verified Rev B netlist.

### 1.3 Mechanical / stack

- Boards: 100 mm circular, 2-layer FR4 1.6 mm ENIG; M3 × 4 on Ø88 mm diagonal pattern (both boards identical — stack alignment)
- CCM rim hardware moved to r = 44 mm: XT30, arm key terminal, 3× pyro terminals, both JST-GH8 links; SMA edge-launch relocated to the new rim above the E22 (RF jog unchanged, ≤5 mm, pour-fenced)
- The Rev B electrical audit (8 fatal Rev A faults, all datasheet citations) remains valid — see *XRIM117_RevB_Change_Log*; no IC pinout changed in Rev C

### 1.4 Rev C2 — OV7670 camera (CCM)

J11 (2×9 socket, board east edge, faces the +X camera pod): pin-compatible with the stock OV7670 module header. D0–D7 → GPIO2–9 (contiguous for PIO), XCLK GPIO23, PCLK GPIO24, VSYNC GPIO28, HREF GPIO22-bank; SCCB on I2C0 (shared with BMP388 — different addresses); RESET pulled up, PWDN pulled down. Funded by deleting pyro CH3, the AUX UART port, sensor INT lines (polling), and the status LED; IMU moved onto the shared LoRa SPI bus with independent CS. Pyro is now CH1=drogue, CH2=main.

## 2. Status at Delivery

| Board | Schematic | Placement | Routing |
|---|---|---|---|
| SDM | complete, netlist-verified | clean, 120° power stage on the annulus | 31/47 nets in copper (all PWM/gate/shunt/drain stage); 16 open as ratsnest incl. power trees |
| CCM | complete, netlist-verified | clean | signal groups in copper; ~37 nets/segments open as ratsnest (mostly the long rim runs + power trees) |

GND pours (both layers) + stitching vias are in. Open nets are ordinary interactive routing in KiCad (press `X`, follow ratsnest) — the new 100 mm discs have generous clearance everywhere. Regenerate with `python3 generator/gen_ccm.py` / `generator/gen_sdm.py` (flags: `--resume`, `--finish`, `--verify`).

## 3. Retired by Rev C

ASAM-1/ASAM-2 KiCad projects (kept under `XRIM117_KiCAD_RevB/` for reference), fin rings 1/2, all servo BOM lines, JR/Futaba headers, TIM-servo firmware paths.
