# GTR70E WYVERN, PCB1 Engineering Change Order 1 — power monitor and SD card fixes

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


Six net changes on PCB1, all downstream of the 2026-08-11 netlist trace in `CONFLICTS.md` sections
3 and 4. Every change below is a rewire, not a redesign: no new parts, no footprint changes, same
component count. Ordered by priority. Each entry gives the net as fabricated, the net it should be,
and the reasoning, so this can be executed either as bodge wires on PCB1 as it sits now or folded
into a PCB2 respin's schematic.

## 1. Root cause: R10 sits in parallel with U13, not in series with pack current

Every INA226 problem in `battery.h`'s file header traces back to one layout mistake: R10 (the
10 mΩ, 2512 shunt resistor) and U13 (the SS-12D00-G3 slide switch) both bridge the same two nodes —
call them NET_X and VBUCK — instead of sitting in series with each other in the battery-to-buck
path. A 10 mΩ resistor in parallel with a switch is functionally a short around that switch: U13
can't meaningfully gate anything with R10 bypassing it, and R10 can't shunt-sense load current
because it isn't in that current's path at all. Fixing this one placement mistake resolves items
2 through 5 below as a side effect — they're really one fix, not four independent ones.

_Fabricated:_ `CN1.2 (battery+) -> U15.3, U15.5 (buck VIN) direct`, `R10.1 -- U4.1, U4.8, U13.1`,
`R10.2 -- U13.2 -- VBUCK`.

_Corrected:_ `CN1.2 -> U13.1` (switch first), `U13.2 -> R10.1` (into the shunt), `R10.2 -> U15.3,
U15.5` (shunt output feeds the buck). Battery current now flows through the switch, then the shunt,
then the buck — in that order, matching what a power switch and a current shunt are each for.

## 2. INA226 VIN+ / VIN- — wire across the real shunt

_Fabricated:_ `U4.10 (VIN+) -- GND`, `U4.9 (VIN-) -- VBUCK` (the buck's regulated output, not the
shunt at all).

_Corrected:_ `U4.10 (VIN+) -> R10.1` (pack side of the shunt, downstream of U13), `U4.9 (VIN-) ->
R10.2` (buck side of the shunt). This is the change that makes `getCurrent()`/`getPower()` in
`battery.h` physically meaningful for the first time — right now those calls have nothing real to
measure and the class doesn't even call them.

## 3. INA226 VBUS — reference pack voltage, not the buck rail

_Fabricated:_ `U4.8 (VBUS) -- NET_X` (same node as the old A1 strap and U13.1, which itself traces
to the ~5 V VBUCK rail through R10).

_Corrected:_ `U4.8 (VBUS) -> R10.1`, the same node as the new VIN+ (item 2) — the pack side of the
shunt, upstream of the switch's voltage drop and the buck's regulation entirely. TI's own INA226
application notes usually tie VBUS to the load side of the shunt (VIN-'s node) for current-monitor
designs, but that isn't what this board needs: the point of measuring battery voltage here is to
catch a weak or over-discharged pack, which means reading voltage as close to the cells as possible,
before a switch or a regulator has a chance to hide the sag. Tying VBUS to the pack side is the
correct choice for that purpose, not the generic default.

## 4. INA226 A1 — strap to a valid address level

_Fabricated:_ `U4.1 (A1) -- NET_X` (~5 V, not one of the four supported strap levels — GND / VS+ /
SDA / SCL — and higher than this chip's own 3.3 V supply).

_Corrected:_ `U4.1 (A1) -> GND` (join U4.2's net, which is already GND). Resulting address: 0x40
(A0=GND, A1=GND) — matches the value `battery.h` already assumes as its bench-scan starting point,
so no firmware change is needed once this trace is fixed. If a second I2C device ever needs 0x40
freed up, A1 can instead go to VS+ (U4.6's 3.3 V net) for 0x41 — either is a valid strap, unlike the
current one.

## 5. U13 restored as the master power switch

Covered by item 1's rewire: once R10 moves into series with U13 instead of parallel to it, U13 goes
back to actually switching pack current to the rest of the board, which is presumably what a
SW-TH_3P slide switch in this position was meant to do in the first place. No separate change beyond
item 1.

## 6. CARD1 pin 4 — route to 3V3, not GND

_Fabricated:_ `CARD1.4 -- GND` (shares the net with CARD1.6, CARD1.9, and every other ground pin on
the board).

_Corrected:_ `CARD1.4 -> 3V3` (the same rail as U7's LDO output, U2/U3/U4/U5's VDD pins). Pin 4 is
the microSD socket's VDD pin on the standard TF-01A pinout; every other pin on CARD1 matches that
standard pinout exactly (pin1/8 unused DAT1/DAT2 reserved pins, pin2/3/5/7 the four SPI signals,
pin6/9 additional grounds), which is why this one pin reading GND instead of 3V3 stands out as a
likely fabrication or layout error rather than an intentional design choice. As wired now, the card
has no power pin connected and `SD.begin()` will not succeed regardless of which GPIOs the SPI lines
use. Confirm with a multimeter (continuity from CARD1 pin 4 to the 3V3 rail vs. to GND) before
committing to a respin or bodge wire — this is the one item on this list worth a five-minute bench
check before touching the board, since if the multimeter disagrees with the netlist trace, the
netlist is wrong instead and nothing needs fixing here.

## Execution options

_Bodge wires on PCB1 as fabricated:_ items 2 through 4 all involve cutting a trace near U4's pins
1/8/9/10 and running a short jumper to R10's exposed pads or the GND plane — feasible with a hobby
knife and 30 AWG wire given U4 is a MSOP-10 package (0.5 mm pitch, tight but workable under
magnification). Item 1/5's rewire (inserting U13 into the CN1-to-U15 path) is harder as a bodge
since it means lifting CN1.2's existing trace to U15 entirely, not just adding a jumper — this one
is a stronger candidate for waiting on a respin unless the whole power-on behavior needs fixing
before the next bench session. Item 6 (CARD1 pin 4) is a single trace cut and a jumper to the
nearest 3V3 via, low-risk either way.

_PCB2 respin:_ fold all six into the schematic before the next fab run. None of them touch placement
or footprints, so this is a same-layout re-route, not a redesign.

## What does not need to change

Every other net traced in the 2026-08-11 pass checks out: SDA0/SCL0 (GP0/GP1) shared bus, BNO055
address (0x28, COM3 to GND), BME680 address (0x76, SDO to GND), LIS3MDL address (0x1C, SDO/SA1 to
GND), the four SD data/clock/chip-select pins (GP8/9/10/11), the H1 header's four general-purpose
GPIOs (37/36/35/34) and its power/QSPI pins, and the servo JST connectors on GP2-5. None of those
need a board change — see `CONFLICTS.md` section 4 for the full confirmed table.
