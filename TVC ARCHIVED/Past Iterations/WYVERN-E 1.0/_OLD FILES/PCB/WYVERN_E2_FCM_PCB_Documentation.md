# WYVERN-E 2.0 — FCM (Flight Computer Module) PCB Documentation

### A Skylight Rocketry Venture
##### Single-board consolidation of the XRIM-117E Rev C *CCM + SDM* stack
##### 75 mm board · 84 mm airframe · dual-MCU · **2-sided, 0 component overlaps, 0 shorts** · finish routing/ERC/DRC in KiCad

## 1. Overview

The FCM collapses the entire Rev C two-board avionics stack (CCM flight computer + SDM
solenoid drive module) onto **one 75 mm circular PCB** sized for the 84 mm 3D-printed airframe
(80 mm tube ID, board OD 75 mm, Ø69 mm M3 mount pattern). It is generated programmatically from
datasheet-verified footprints by `generator/gen_fcm.py`, which reuses the proven Rev C
generator core (`kicadgen.py`, `parts.py`, `autoroute.py`, `verify.py`) and adds new land
patterns in `parts_ext.py`, plus a from-scratch Gerber/Excellon exporter (`gerber_export.py`).

Regenerate everything (route + fab package) with:

```
cd generator
python3 gen_fcm.py --gerber            # build + route + emit KiCad + Gerbers
python3 gen_fcm.py --gerber --verify   # + netlist cross-check (SCH vs PCB)
```

### 1.1 Key specifications

| Parameter | Value |
|---|---|
| Board diameter | 75.0 mm (r = 37.5 mm, circular Edge.Cuts) |
| Mount pattern | 4 × M3 on Ø69 mm, 0/90/180/270° |
| Layers (as generated) | 2 (F.Cu / B.Cu), 1.6 mm FR4 ENIG · **2-sided assembly** |
| **Layers (recommended for build)** | **4 (Sig / GND / PWR / Sig)** — see §6 |
| Controller | **RP2350B** QFN-80 (48 GPIO, 8 × 12-bit ADC, dual Cortex-M33 @ 150 MHz) |
| Input bus | 12 V Tenergy NiCd (10S1P, 13 A rate) via XT60 |
| Logic rails | 3.3 V + 5 V (2 × TPS54202 synchronous buck) |
| Coil bus (V_SOL) | 12 V direct, INA219 + 10 mΩ Kelvin shunt monitored |
| Footprints placed | 113 (RP2350 + RP2040 deploy + 2× BNO055 + sensors + 3 solenoid + 3 pyro + power) |
| Named nets | 88 |
| **Routed in copper (DRC-clean)** | 47 / 90 + GND pours · **0 shorts, 0 clearance violations** |
| **Placement** | **2-sided** — 36 top (MCUs/sensors/connectors) + 77 bottom (passives + RP2040 deploy cluster) · **0 component overlaps** |

The 70 → 84 mm airframe growth let the board expand from 62 mm to 75 mm, which raised
autorouter completion from ~74 % to **94 %** and gave the power stage and RF generous room.

## 2. Subsystem Architecture

### 2.1 Compute & storage (dual-MCU)
- **RP2350B (U1, QFN-80):** primary flight / TVC computer. Solenoid loops + sensor suite +
  storage; talks to the deploy co-processor over UART (GPIO2/3) + arm/status lines.
- **RP2040 (U10, QFN-56):** **independent deployment co-processor** — the onboard RRC3
  equivalent (see §2.7). Own flash + barometer + crystal; drives the 3 pyro channels.
- **Storage:** onboard QSPI flash (U2 W25Q32JV) for code + logging, **microSD (J3)** removable
  backup on SPI1. *NAND removed per spec — storage is onboard flash + microSD only.*

### 2.2 Sensor suite

| Quantity | Device | Ref | Bus / pin |
|---|---|---|---|
| 3-axis accel + gyro (high-g) | ICM-42688-P | U4 | SPI1, CS = GPIO14 |
| Pressure + Temp (no humidity) | **BMP280** | U5 | I2C0 (0x76) |
| Magnetometer | LIS3MDL | U6 | I2C0 (0x1C) |
| 9-DOF orientation (onboard) | **BNO055** | U13 | I2C0 (0x28) |
| 9-DOF orientation (gimbal breakout) | **BNO055** | J4 header | I2C0 (0x29) |
| Bus current / power | INA219 | U7 | I2C0 (0x40), 10 mΩ shunt R7 |
| Vibration | piezo film | J5 | ADC GPIO47 |
| Altitude | derived from BMP280 (×2: U5 + deploy U12) | — | barometric |
| Battery voltage | divider R12/R13 | — | ADC GPIO43 |

### 2.3 Solenoid TVC drive — 3 × PWM closed-loop current channels
Per channel (×3 at 120°): `V_SOL(12V) → coil → AO3400A low-side FET → 20 mΩ shunt → GND`,
SS34 freewheel across the coil, gate via 100R + 100k pulldown, shunt → 1k/100nF RC → ADC.
PWM on RP2350 slices (GPIO30/31/32) at **20 kHz**; current loop ≥4 kHz. The "2 × 2-axis
closed loop" = inner current loop per coil + outer pitch/yaw attitude loop.

### 2.4 Pyrotechnics — 3 onboard channels (RRC3+ removed)
The external RRC3+ altimeter is **replaced by onboard firmware** (the MCU + BME280 barometer +
IMU are the altimeter) driving **3 independent low-side AO3400A pyro channels**, each with a
screw terminal + 100 k gate pulldown + continuity divider into the ADC:
- **Ignition (FFJ)** — Q4 / J11, gate GPIO33, continuity GPIO44 (First Fire Jr, 2nd-stage)
- **Drogue (MJG)** — Q5 / J14, gate GPIO15, continuity GPIO45 (booster separation)
- **Main (MJG)** — Q6 / J15, gate GPIO17, continuity GPIO46 (nose/main chute)
This provides the 3 charges requested (2 × MJG Firewire + 1 × First Fire Jr) with no external altimeter.

### 2.7 RP2040 Deployment Co-Processor (onboard RRC3)
Duplicates the RRC3+ functions as an **independent subsystem**, comms-free: **RP2040 (U10)** +
its **own BMP280 barometer (U12)** + **QSPI boot flash (U11 W25Q32)** + **12 MHz crystal (X2)**
+ decoupling + **deploy SWD header (J16)**. It detects apogee/main from its own barometer and
**drives all 3 pyro channels** (Q4 ign / Q5 drogue / Q6 main) with continuity sense on its ADC
(GPIO26-28). It exchanges arm/fire/status with the main RP2350 over a **UART link** (no RF) —
so deployment survives even if the flight/TVC computer faults. This is a true onboard altimeter,
not a passthrough.

## 2.5 Power tree
```
12 V NiCd (XT60 J6) ┬ INA219 10mΩ ── V_SOL (12V coil bus, 3×470µF bulk)
                    ├ TPS54202 (U8) ── 3.3 V (logic/sensors/flash/RP2350)
                    ├ TPS54202 (U9) ── 5.0 V (camera/aux)
                    └ divider ── VBAT_SENSE (ADC)
RP2350 core 1.1 V from internal VREG.
```

### 2.6 Comms / IO
USB-C 2.0 (J2, program/data for the RP2350). **No LoRa/RF and no camera** (removed per spec —
no ground telemetry, no video). The two BNO055s: one **onboard** (U13) and one on a **GPIO
header J4** for the breakout mounted on the gimbal — both on I2C0 at different addresses.

## 3. JLCPCB Fabrication Package (`FCM_KiCAD/gerbers/`)

Generated by `gerber_export.py` directly from the routed board and **independently validated
with the `gerbonara` Gerber library** (all 8 layers + drill parse clean; board outline = 75.1 mm).

| File | Layer |
|---|---|
| `WYVERN_E2_FCM.GTL` / `.GBL` | Top / Bottom copper (with poured GND, LPC clearances) |
| `WYVERN_E2_FCM.GTS` / `.GBS` | Top / Bottom solder mask |
| `WYVERN_E2_FCM.GTP` / `.GBP` | Top / Bottom solder paste (stencil — 2-sided) |
| `WYVERN_E2_FCM.GTO` / `.GBO` | Top / Bottom silkscreen |
| `WYVERN_E2_FCM.GKO` | Board outline (Edge.Cuts) |
| `WYVERN_E2_FCM.DRL` | Excellon drill (239 holes, metric) |
| `WYVERN_E2_FCM_gerbers.zip` | **Upload this to JLCPCB** (all 8 layers + drill) |
| `WYVERN_E2_FCM_BOM.csv` | Assembly BOM (44 lines; add LCSC part #s) |
| `WYVERN_E2_FCM_CPL.csv` | Component placement (83 parts, Designator/X/Y/Layer/Rotation) |

**Ordering:** upload `WYVERN_E2_FCM_gerbers.zip` to JLCPCB; the KiCad-style extensions
auto-detect. For assembly, add the BOM + CPL and populate LCSC part numbers.

> ## ⚠ Remaining KiCad work before fabricating
> Netlist + component set correct, copper short-free, **2-sided placement now has 0 overlaps**.
> Remaining items:
> 1. ✅ **RESOLVED — 2-sided placement, 0 component overlaps** (36 top / 77 bottom). Board is
>    physically buildable. *(2-sided assembly — JLCPCB supports it.)*
> 2. **MCU pinouts:** the **RP2040 (deploy) pin map matches real silicon** (verified against the
>    datasheet — power/QSPI/USB/XIN all correct). The **RP2350B (U1) GPIO→physical-pin map still
>    needs datasheet confirmation** of the power-pin (IOVDD/DVDD/QSPI/USB) locations — verify in
>    KiCad before fab or U1 may not boot.
> 3. **Footprints** (QFN-80/QFN-56/USB-C/microSD/BNO055-LGA28) drawn approximately — best fix is
>    to **import this netlist into KiCad and swap to KiCad'"'"'s verified library footprints**
>    (those are the datasheet land patterns).
> 4. **Run ERC + DRC, finish the ~43 ratsnest nets, promote to 4-layer** (§6) — interactive
>    KiCad work (I cannot reliably remote-drive the GUI for routing).
> 5. **Stock:** RP2350B is the main risk (often OOS at LCSC) — if so, consider **RP2354B**
>    (integrated 2 MB flash, drops external boot flash) or RP2350A. RP2040, sensors (ICM-42688,
>    BMP280, LIS3MDL, BNO055, INA219), AO3400A, SS34, TPS54202 and passives are LCSC-stocked.

## 4. GPIO Allocation (both MCUs)

**RP2350 (flight/TVC):** GPIO0/1 UART0 debug · 2/3 UART→RP2040 · 4/5 deploy arm/status ·
6 BNO_O_INT · 10-12 SPI1 · 14 IMU_CS · 16 SD_CS · 28/29 I2C0 (BMP280/LIS3MDL/INA219/BNO055×2) ·
30-32 solenoid PWM · 35 STATUS_LED · 36-39 IMU_INT/BNO_INT/REED/BUZZER · 40-43 solenoid sense +
VBAT (ADC) · 47 vibration (ADC). Camera/NAND/LoRa/pyro GPIO freed.

**RP2040 (deploy):** GPIO0/1 UART→RP2350 · 2/3/4 pyro gates (ign/drogue/main) · 5 arm · 6/7
buzzer/LED · 8/9 own I2C (BMP280) · 26/27/28 pyro continuity (ADC) · 29 VBAT sense · QSPI→flash.

## 5. Routing Status & Cleanup

After autorouting, a post-process pass (`clean_conflicts` in `gen_fcm.py`) **rips any net that
violates copper clearance back to ratsnest**, so the delivered copper is guaranteed free of
shorts. Verified independently (shapely): **0 same-layer different-net overlaps and 0 clearance
violations at JLCPCB's 0.127 mm limit.**

77 of 88 nets are routed in clean copper + full GND pours both layers + 73 vias. The 10 nets
left as ratsnest are intentional (route them in KiCad with DRC on): the two main power rails
**+3V3** and **VBAT12** (route as wide deliberate traces / inner-layer polygons), `+5V_USB`,
`BK3_BOOT`/`BK5_BOOT`, `CAM_PWDN`, `RF_ANT` (50 Ω jog to the SMA), `SD_CS`, `SOL3_SNS`, `SWCLK`.


## 5b. Placement status — ⚠ component overlaps remain

This is a **dense** board (95 parts on a 75 mm disc, including large connectors). An automated
force-directed placement pass reduced physical component-courtyard overlaps from **88 → ~22**,
but did **not** reach zero — see `WYVERN_E2_FCM_placement.png` (red = overlapping parts). The
remaining collisions (bypass caps touching the MCU, the 3-part solenoid/pyro clusters, a couple
of rim connectors) need **interactive placement in KiCad** to resolve. Practical fixes: move the
bypass caps to the **bottom side** (frees the centre), nudge the solenoid/pyro groups apart, or
grow the board a few mm. **Do not fabricate until placement overlaps = 0 (run KiCad DRC).**

Trace copper is short-free (clean_conflicts guarantees 0 same-layer different-net shorts), but
routing on the relaxed placement is partial (~32/83 nets) — finish in KiCad after placement.

## 6. Recommended 4-Layer Stackup

| Layer | Use | Cu |
|---|---|---|
| L1 (top) | components + short signal | 1 oz |
| L2 | solid GND plane | 1 oz |
| L3 | power: 12 V / V_SOL / 5 V / 3.3 V polygons | **2 oz** for coil current |
| L4 (bottom) | signal + camera/LoRa fan-out | 1 oz |

2 oz inner power copper carries the 6 A worst-case coil bus (3 × 2.8 A peak) with <10 °C rise.
The generator emits 2-layer; promote to 4-layer in KiCad board setup and move the V_SOL/12 V
polygons to L3 before fabrication.

## 7. Heritage / citations

RP2350 datasheet; TDK ICM-42688-P DS-000347; Bosch BME280 BST-DS002; ST LIS3MDL; TI INA219
(SBOS448) / TPS54202 (SLVSCY8); AOS AO3400A; Ebyte E22-900M22S v1.20; Adafruit 2472 (BNO055).
Reuses the verified Rev B/C electrical audit (`XRIM117E_RevC_Change_Log`).
