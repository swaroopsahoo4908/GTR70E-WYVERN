# GTR70E WYVERN, canonical numbers

Single source of truth for the Pico 2 W perfboard revision. Every doc, sim and firmware comment
should agree with this table. Produced by `Simulations/we4_sim.py` off the CAD masses in
`3D parts/_generator/mass_report.json`.

## Vehicle

| Quantity | Value | Was (PCB1 / 744 mm) |
|---|---|---|
| Overall length | 672 mm | 744 mm |
| Body diameter | 70 mm | 70 mm |
| Upper BT | 198.4 mm | 198.4 mm |
| Lower BT | 350 mm | 421.6 mm |
| Liftoff mass | 720.3 g | 698 g |
| Dry mass (with spent casing) | 660.3 g | 638 g |
| Airframe dry (no motor) | 618.3 g | 596.0 g |
| CG, liftoff | 45.0 cm | 50.1 cm |
| CG, burnout | 43.5 cm | — |
| CP (Barrowman, 87 mm fins) | 53.3 cm | 59.3 cm |
| Static margin | 1.14 cal | 1.31 cal |
| Pitch inertia Iyy | 0.0201 kg·m² | 0.02624 |
| Gimbal pivot station | 54.84 cm | 62.0 cm |
| Control arm, liftoff | 9.9 cm | 12.6 cm |
| Pitch authority | 17.2 rad/s² | 15.9 |

## Flight

| Quantity | Value |
|---|---|
| T/W average / peak | 2.04 / 3.58 |
| Burnout | 70.1 m at 34.4 m/s, t = 3.45 s |
| Apogee | 124.6 m (409 ft) at t = 6.72 s |
| Deploy | t = 7.45 s, 7.1 m/s descending |
| Descent under 24 in chute | 4.8 m/s |
| Max TVC pitch deviation | 5.73° |

## Avionics

Raspberry Pi Pico 2 W on a 20×24 (50×70 mm) perfboard, mounted as an axial card in two slotted
carrier disks (`02b_fc_card_carrier_{fwd,aft}_ASAAero`).

| Device | Bus | Address | Strap |
|---|---|---|---|
| BNO085, bay | I²C0 | 0x4B | DI wired to 3V3 |
| BNO085, gimbal | I²C0 | 0x4A | DI unconnected |
| BME688 | I²C0 | 0x76 | SDO wired to GND |
| BMP388 | I²C0 | 0x77 | SDO unconnected |
| microSD breakout | SPI1 | — | — |

Pins: SDA GP0, SCL GP1, servos GP2/GP3, SD MISO/CS/SCK/MOSI GP8/9/10/11, battery sense GP26.

Power: 2S LiPo 450 mAh → PPTC 2.6 A → arming switch → 5 V 3 A switching UBEC → Pico VSYS and the
servo rail. Sensors run off the Pico's 3V3 regulator. 470 µF bulk at the servo feed. Battery sense
is a 100k/47k divider with 100 nF on the tap.

## Separation

Seven leads cross the bulkhead on dupont male-female extensions and part at ejection:
SERVO1_SIG, SERVO2_SIG, +5V, GND, SDA, SCL, 3V3. Only the aramid shock cord is retained.
After `WYV_DEPLOY_T_MS` the gimbal IMU dropping off the bus is expected, not a fault
(`TriImu::mark_separated()`).

## Retired

PCB1 and everything specific to it: the Ø62 mm board, RP2350B QFN-80, TPS564201 buck, AP2112K LDO,
INA226, LIS3MDL, W25Q32JV, USB-C front end, BNO055 body IMU, BME680.
