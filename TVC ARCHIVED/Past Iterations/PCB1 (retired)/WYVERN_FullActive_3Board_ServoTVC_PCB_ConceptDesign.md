# WYVERN, Full Active-Control Avionics Stack, Rev 2

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


##### Three 75 mm circular boards, stacked: Camera/Sensor/Airbrake, Compute/Power/Storage, TVC/Fin/Sensor
##### Concept + component-level BOM only. No schematic, footprint, or routing generated, staged for the AI PCB design tool.

## 0. What changed from Rev 1

Board diameter is fixed at 75 mm (matching the GTR70E WYVERN 2.0 FCM/B1/B2 precedent, Ø69 mm
4×M3 mount pattern, 2-layer or 4-layer FR4, ENIG). Stack order and board assignments are now
fixed per Sky's spec below. The Pocket Geiger module is cut, it's a pre-built breakout board,
not a placeable component, and Sky's rule this pass is that only the camera, the NVMe drive,
and the servos are allowed to live off the PCB as connectorized modules. Everything else has to
be a real part JLCPCB can place. Radiation sensing can come back later as a bare PIN photodiode
+ discrete charge-amp front end (a real from-scratch circuit, not a module) if it's wanted, not
included here since it wasn't asked for this pass.

## 1. Stack order and board roles

```
   ┌─────────────────────────────┐
   │ BOARD 1, Camera / Sensor / │ (top disc)
   │ Airbrake Driver │
   ├─────────────────────────────┤ 2x10 stack header (B1↔B2) + CSI flex jumper
   │ BOARD 2, Compute / Power / │ (middle disc)
   │ Storage / Comms │
   ├─────────────────────────────┤ 2x10 stack header (B2↔B3)
   │ BOARD 3, TVC / Fin Driver / │ (bottom disc)
   │ Remaining Sensors / Mic │
   └─────────────────────────────┘
```

All three boards: Ø75.0 mm (r = 37.5 mm) circular Edge.Cuts, 4×M3 mounts on Ø69 mm at
0/90/180/270°, matching the GTR70E WYVERN 2.0 stack so the same disc-mount hardware carries over.

## 2. Board 1, Camera / Sensor / Airbrake driver (top)

### 2.1 Camera interface
Raspberry Pi Camera Module 3 (12 MP, autofocus, CSI-2) plugs into a 22-pin, 0.5 mm pitch FPC
connector on Board 1. Because CSI-2 is a high-speed differential MIPI link and the camera's
actual processor (CM5) sits one disc down on Board 2, the connector-to-connector run is a
dedicated short FPC/flex jumper between B1 and B2, kept physically and electrically separate
from the general-purpose 2×10 stack header, since MIPI shouldn't share a connector with slow
GPIO/I2C nets. This is the one interconnect on the stack that needs real signal-integrity
attention from the AI PCB tool (controlled length, controlled impedance, minimal stack gap).

### 2.2 Sensor suite (most of the suite lives here)
| Function | Part | Interface | Package |
|---|---|---|---|
| Barometric altimeter | Bosch BMP390, ±3 cm resolution | I2C | LGA-10 |
| Temp / humidity / gas (VOC index) | Bosch BME680 | I2C | LGA-8 |
| Calibrated CO2 (NDIR) | Sensirion SCD41, 400–5000 ppm, ±(50 ppm+5%) | I2C | 10.1×10.1×6.5 mm LGA |
| Redundant magnetometer | ST LIS3MDL | I2C | LGA-12 |
| Bus current/voltage, airbrake rail | TI INA226, 16-bit, 0.1% gain error, 10 mΩ shunt | I2C | SOT-23-8 |

### 2.3 Airbrake servo drive (2 channels)
The PWM origin is the RP2350B on Board 3 (keeps a single deterministic timing source for every
servo on the vehicle). Board 1 hosts the physical actuator interface per channel: JR/Futaba
3-pin connector, local 100 nF + 10 µF decoupling at the connector, and a gate-driven low-side
FET stage if current limiting is wanted per channel. PWM commands cross the stack from Board 3
through Board 2 on two dedicated single-ended lines in the general 2×10 headers, a GPIO toggle
at ≤50 Hz update rate has no bandwidth concern crossing two connectors (same principle validated
in the GTR70E WYVERN 2.0 two-board spec for the solenoid PWM lines).

| Channel | Connector | Servo (off-board) |
|---|---|---|
| Airbrake 1 | J-AB1, JR/Futaba 3-pin | Savöx SH-0257MG, 3.5 kg·cm, 11.4 g |
| Airbrake 2 | J-AB2, JR/Futaba 3-pin | Savöx SH-0257MG |

### 2.4 Power on Board 1
Local 3.3 V TPS54202 buck off the B1↔B2 stack's 5 V rail, feeding the I2C sensor suite. Servo
connectors draw off the shared 5 V servo rail (sourced on Board 2, see §3.3) passed through the
stack header, with local bulk capacitance (2× 470 µF) at the airbrake connectors to absorb
switching transients without sagging the shared rail.

## 3. Board 2, Compute / Power / Storage / Comms (middle)

Middle position is deliberate: this disc carries the pack input and both USB-C ports, so it
sits at the mechanical/electrical center of the stack, and it's the shortest path for the
CSI flex jumper (up to B1) and the PCIe run to the NVMe socket (local, no stack crossing).

### 3.1 Compute + RAM
Raspberry Pi Compute Module 5 (8 GB LPDDR4X, quad Cortex-A76 @ 2.4 GHz, PCIe Gen2 x1, dual
4-lane MIPI, 2× USB 3.0) [1], mounted via its Hirose DF40C-100DS/DP-0.4 mm edge connector pair, 
this is the JLCPCB-compatible equivalent of the camera/NVMe/servo exception: the CM5 module
itself plugs in, but the connector, PMIC support circuitry, and every passive around it are real
placed parts. *If Sky wants true silicon-level integration instead of a pluggable SoM* (bare
Rockchip RK3588S or similar BGA SoC + discrete LPDDR4X + eMMC boot flash + PMIC sequencing),
that's a legitimate alternate path but is a multi-month professional SI/PCB bring-up in its own
right, not a concept-design-scope swap, flag if that's actually what's wanted and it becomes
its own design pass.

### 3.2 Storage
M.2 Key-M socket (2230/2242/2280 switch-selectable mounting holes, populated with a 2230 drive)
wired to CM5's single PCIe x1 lane, kept local to Board 2, no PCIe crossing the stack.

### 3.3 Power front end and servo/logic rails
- XT30 12 V-in connector (matches the project's existing 12 V pack convention), 1812 PPTC
  fuse, high-side reverse-polarity P-FET, SMBJ-class TVS clamp.
- TI BQ25792, I2C 1S–4S buck-boost charger, 5 A max charge, USB-C PD 3.0 sink negotiation,
  96.5% efficiency at 9 V-in/3 A on a multi-cell pack [2]. Charges the same XT30 pack the
  vehicle flies on through USB-C PD, no separate balance port.
- 5 V servo rail: synchronous buck (MP2338-class, 8 A peak) sized for the worst-case 9-servo
  simultaneous stall (~10.8 A instantaneous per Savöx SH-0257MG stall spec, duty-cycled in
  normal flight); 3× 470 µF bulk at the rail's stack-header exit point.
- 5 V compute rail: separate 3 A buck for CM5 + NVMe + camera, isolated from servo rail
  transients.
- 3.3 V logic rail: TPS54202 for RP2350B (Board 3) and both sensor boards' I2C pull-ups.
- INA226 on the battery input (pack-level current/voltage telemetry).

### 3.4 USB-C ports (2×, physically separate)
| Port | Function | Routed to |
|---|---|---|
| USB-C #1 | PD charge-in only | BQ25792 |
| USB-C #2 | Data (ground data pull, flashing) | CM5 USB 3.0 |

Charge and data stay on physically separate connectors and separate silicon, a ground-support
laptop is never electrically in the battery's charge path.

### 3.5 "Critical sensors for control"
Placed on the middle disc deliberately: this is the position closest to the vehicle's
center of gravity, which is where the primary attitude reference belongs for best measurement
fidelity, independent of which board hosts the MCU driving the control loop.

| Function | Part | Interface |
|---|---|---|
| Fast-loop 6-DoF (rate gyro/accel) | TDK ICM-42688-P, 32 kHz ODR | SPI, routed to RP2350B on Board 3 over the B2↔B3 stack header |
| Fused 9-DoF orientation reference | Bosch BNO085, SH-2 fusion, quaternion out | I2C, shared bus to Board 3 |

The ICM-42688-P's SPI link crossing one stack connector (B2→B3) is the one place this Rev
departs from the "keep the fast-loop sensor local to the MCU" principle used in GTR70E WYVERN 2.0, 
that's the direct consequence of Sky's placement call (CG-proximity for the sensor beats
zero-latency wiring). One connector hop at SPI clock rates well under 24 MHz is still a small
fraction of a 500 Hz control loop's budget, but it's worth the AI PCB tool giving that link
priority in the header pinout (short, low-inductance path, adjacent-GND-pin shielding).

## 4. Board 3, TVC / Fin driver / remaining sensors / mic (bottom)

### 4.1 Compute
RP2350B (QFN-80-1EP, dual Cortex-M33 @ 150 MHz, 48 GPIO, 12 PWM slices/24 channels, 520 kB
SRAM) [3], the real-time core for the whole servo stack. Lives here because this disc carries
7 of the 9 servo channels (the highest channel count and the tightest timing requirement, the
3-axis TVC gimbal), so the MCU sits closest to the load it directly times.

### 4.2 Servo drive (7 channels, direct off RP2350B PWM slices)
| Channel group | Qty | GPIO | Servo (off-board) |
|---|---:|---|---|
| TVC gimbal (3-axis) | 3 | GPIO30–32 | Savöx SH-0257MG |
| Active fins (N/E/S/W) | 4 | GPIO33–36 | Savöx SH-0257MG |

Plus GPIO37–38 generating the 2 airbrake PWM signals routed up to Board 1 through Board 2
(§2.3). Each of the 7 local channels: JR/Futaba 3-pin connector, local decoupling, shared 5 V
servo rail (from Board 2) with 3× 470 µF bulk at this board's rail entry point given it carries
the largest simultaneous-load channel group.

### 4.3 Remaining sensors + mic
| Function | Part | Interface |
|---|---|---|
| Bus current/voltage, TVC+fin rail | TI INA226 | I2C |
| Acoustic / launch signature | Infineon IM69D130 MEMS mic, 105 dB dynamic range, up to 130 dB SPL [4] | PDM → ADAU7002 PDM-to-I2S bridge → I2S to RP2350B |

### 4.4 Power on Board 3
3.3 V logic rail entry (from Board 2) for RP2350B and the local sensors; 5 V servo rail entry
(from Board 2) for the 7 local channels. No local regulation beyond decoupling, both rails are
generated once, on Board 2, and distributed through the stack headers to avoid duplicate
converters and duplicate EMI sources.

## 5. Inter-board connectors

| Link | Connector | Carries |
|---|---|---|
| B1 ↔ B2 | 2×10 (20-pin), 2.54 mm, 6 dedicated GND pins interleaved | I2C (shared sensor bus), 2× airbrake PWM, 3V3, 5V_SERVO, GND |
| B1 ↔ B2 (separate) | 22-pin 0.5 mm FPC/flex jumper | MIPI CSI-2 (camera ↔ CM5), kept off the general header, SI-critical |
| B2 ↔ B3 | 2×10 (20-pin), 2.54 mm, 6 dedicated GND pins interleaved | SPI (ICM-42688-P), I2C (BNO085 + shared bus), 3V3, 5V_SERVO, GND, UART (RP2350B ↔ CM5 telemetry handoff) |

## 6. JLCPCB fabrication targets (per board, first-pass, to be confirmed once routed)

| Parameter | Board 1 | Board 2 | Board 3 |
|---|---|---|---|
| Diameter | 75.0 mm | 75.0 mm | 75.0 mm |
| Layers | 2 | 4 (Sig/GND/PWR/Sig) | 2 |
| Finish | ENIG | ENIG | ENIG |
| Min trace/space | ≥0.127 mm | ≥0.127 mm | ≥0.127 mm |
| Min via / drill | ≥0.45/0.2 mm | ≥0.45/0.2 mm | ≥0.45/0.2 mm |
| Mount pattern | 4×M3, Ø69 mm | 4×M3, Ø69 mm | 4×M3, Ø69 mm |

Board 2 gets 4 layers because it's carrying PCIe (NVMe), the CM5 high-density edge connector
fanout, and the charger's higher-current power distribution, the same justification the
GTR70E WYVERN 2.0 spec used for its Board 2 (RP2350B + camera board) 4-layer stackup.

## 7. Power budget

| Rail | Source (Board 2) | Continuous | Peak |
|---|---|---:|---:|
| 5 V servo (all 9 channels) | MP2338-class buck, 8 A peak | ~2–3 A duty-cycled | 10.8 A (9× simultaneous stall) |
| 5 V compute | Dedicated 3 A buck | 1.5–2 A | 3 A |
| 3.3 V logic | TPS54202 | 250 mA | 400 mA |
| USB-C PD charge-in | BQ25792, 5 A max | — | 3 A @ 9 V, 96.5% eff. |

## 8. What's deliberately not done yet

No schematic, no footprints, no routed copper, this document is the component list, board
assignment, physical stack geometry, and inter-board net list only, per the instruction to hand
this straight to the AI PCB design tool rather than hand-drafting KiCad. The one item that tool
should be told to treat specially is the CSI flex jumper in §2.1/§5, everything else is
conventional 2.54 mm header + standard passive/IC placement.

## 9. Citations

[1] Raspberry Pi Ltd, Compute Module 5 Datasheet, PCIe Gen2 x1, dual MIPI, 8 GB LPDDR4X, 
https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf
[2] Texas Instruments BQ25792 datasheet, 1–4 cell buck-boost charger, USB PD 3.0, 
https://www.ti.com/lit/ds/symlink/bq25792.pdf
[3] Raspberry Pi Ltd, RP2350 Datasheet, PWM (12 slices/24 channels), GPIO, 520 kB SRAM, 
https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
[4] Infineon IM69D130 datasheet, 105 dB dynamic range MEMS microphone, 
https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf

Other parts (BMP390, BME680, SCD41, LIS3MDL, ICM-42688-P, BNO085, INA226, Savöx SH-0257MG,
TPS54202) carry forward from Rev 1's citation list and the GTR70E WYVERN 2.0 board precedent, same
parts, same sourcing, just reassigned across the new three-board split.

## References

CEVA, Inc. (2023). *BNO08X datasheet* (Rev. 1.17). https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf

EMAX. (n.d.). *ES08MA II 12 g mini metal gear analog servo* [Product specification]. Retrieved August 12, 2026, from https://www.getfpv.com/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model.html

Estes Industries. (n.d.). *F15-4 engines* [Product specification]. Retrieved August 12, 2026, from https://estesrockets.com/products/f15-4-engines

Federal Aviation Administration. (n.d.). *14 CFR Part 101 — Moored balloons, kites, amateur rockets, and unmanned free balloons*. Electronic Code of Federal Regulations. https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101

National Fire Protection Association. (2018). *NFPA 1122: Code for model rocketry*. https://www.nfpa.org/product/nfpa-1122-code/p1122code

Raspberry Pi Ltd. (2024). *RP2350 datasheet*. https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

Texas Instruments. (n.d.). *TPS564201: 4.5-V to 17-V input, 4-A synchronous step-down voltage regulator* (SLVSFB5) [Datasheet]. https://www.ti.com/lit/ds/symlink/tps564201.pdf
