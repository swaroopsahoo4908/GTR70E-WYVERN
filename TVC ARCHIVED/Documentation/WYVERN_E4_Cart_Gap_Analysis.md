# GTR70E WYVERN, Cart Gap Analysis

*Authors:* Swaroop Sahoo, Chris Liu, Allison Hong
*Program:* GTR70E WYVERN

Checked 2026-08-14 against the live Amazon cart (25 items, $593.92 list / $582.37 after coupons) and
the live Adafruit cart ($216.95). Both carts reconcile line-for-line with `WYVERN_E4_BOM.xlsx`,
which is the authoritative line-item source. This file is the narrative read of what is still
missing.

No Estes cart was supplied, so every Estes line is unverified rather than confirmed absent.

Scope changes folded in this pass: ABS is dropped from the program entirely, the load-cell bend rig
is replaced by a dead-weight bend-to-fracture fixture (the 20 kg cell stays dropped), and the
BNO085 count is fixed at four.

---

## 1. Flight-blocking, still open

| # | Missing | Why it stops you | Where | Est. |
|---|---|---|---|---|
| 1 | 5 V 3 A switching UBEC | PCB1 is retired, so there is no onboard buck. The Pico VSYS rail and the servo rail have no source. Nothing on the vehicle powers up. Must be switching — a linear BEC dropping 2S to 5 V at 1.9 A dissipates ~4.5 W and cooks. | Amazon | ~$8 |
| 2 | Perfboard 20×24 / 50×70 mm, ×2 | The flight computer card itself, and a second for the ground stand. Mounts on edge in `02b_fc_card_carrier_{fwd,aft}`. Generic equivalent is fine, but the hole count has to be 20×24 or the wiring diagram stops matching. | Adafruit PID 1609 / generic | ~$10 |
| 3 | Lead-free solder | Whole build is through-hole perfboard. | Amazon | ~$12 |

Flight motors are covered: 2 F15-4 on hand plus one 2-ct pack in the cart is 4 total, matching the
planned count.

Two more worth confirming rather than assuming: a handheld anemometer for the launch-day wind
go/no-go gate, and the steel blast deflector plate for the static stand. Both are zeroed in the BOM
and neither has been confirmed on hand.

## 2. Closed since the last pass

The Adafruit cart now carries everything the perfboard build needs on the connector side. STEMMA QT
to male header ×6 (PID 4209) covers all four sensors with two spare. The premium F/M extension pack
(PID 826, 40 leads) replaces the old dupont line and covers the seven leads that cross the bulkhead.
Terminal blocks ×5, USB-C to Micro-B ×1, HX711 ×4.

Confirmed on hand and moved to *Already Acquired*: the 470 µF bulk and 100 nF caps, the 100 kΩ /
47 kΩ divider pair, 24 AWG silicone wire, heat-shrink, Kapton tape, breakaway male header, Nomex
chute protector, and the 1010 rail and pad. The USB OTG adapter set is dropped outright.

One thing to verify before soldering: the divider resistors on hand must actually be 100 kΩ and
47 kΩ. Those exact values are baked into `WYV_VBAT_DIV_TOP` / `WYV_VBAT_DIV_BOT` in
`wyvern_config.h`, and both firmware cutoffs shift if they aren't.

## 3. Cable reach across the separation joint

The gimbal BNO085 sits at the pivot, station 548 mm. The FC card is at roughly station 235 mm. The
run is about 313 mm before routing slack, and a 150 mm PID 4209 plus one 150 mm PID 826 extension is
300 mm — short. Chain two extensions for that run and it becomes 450 mm with slack to spare, and the
extension pair is also what gives the joint its pull-apart behaviour at ejection.

That substitution is why the 400 mm STEMMA QT cable (PID 5385) is no longer carried.

## 4. Load cells and DAQ, resolved

Four cells, four HX711.

| Cell | Qty | Role |
|---|---|---|
| 1 kg (PID 4540) | 2 | Lateral X and Y on the TVC balance. Side force at ±8° is $25.3\sin 8° = 3.5$ N = 0.36 kgf, 36 % of full scale. |
| 5 kg (PID 4541) | 2 | Axial thrust. F15 peak 25.3 N = 2.58 kgf, 52 % of full scale. One static stand, one TVC balance Z. |
| 10 kg (PID 4542) | 0 | Dropped. Nothing needs it. |
| 20 kg (PID 4543) | 0 | Dropped. The bend test now uses hanging dead weight, not a cell. |

One HX711 per axis is required, not preferred. The part multiplexes both channels through a single
ADC and needs settling time after a channel switch, so a three-axis balance cannot sample
simultaneously off one chip. Three for the TVC balance, one for the static stand.

Strap RATE high for 80 SPS rather than the 10 SPS default. Even at 80 SPS only about 16 samples land
on the ignition transient of a 3.45 s F15 burn, so report total impulse as the solid number and peak
thrust as a lower bound.

## 5. RQ2 bend test, re-scoped

Resolved 2026-08-14. The test is now load-to-fracture on a 2 mm slab under a single mid-span point
load, applied as hanging dead weight rather than through a load cell. Full spec is
`WYVERN_E4_GSE_TestStands.md` §5.

Hardware cost is zero. The supports and hanger yoke print from filament already in the BOM, the
rollers are 6 mm rod, and the weight comes from known masses. Gravity is the force reference, which
is a stronger standard than a bridge amplifier that would itself have been calibrated against known
masses.

For this exact geometry — 2.0 × 15 mm coupon on an 80 mm span — flexural strength reduces to
$\sigma_f\,[\text{MPa}] = 19.6\,m\,[\text{kg}]$. The fixture is built to a 6 kg ceiling
against a worst case near 5 kg, so it cannot be the limiting element.

What changed against the proposal: it no longer reports flexural modulus, because modulus needs
deflection measurement and this test only records the mass at failure. It reports flexural strength
instead, which is arguably the more direct answer to "which material can carry the TVC assembly."
That wording is updated in both the proposal Markdown and DOCX.

## 6. Terminal block count

Five is correct, which is what the cart has. Two per flight computer card — pack input and UBEC 5 V
output — across two cards, flight and ground stand, is four, plus one spare. The arming switch stays
soldered and heat-shrunk into the pack harness rather than blocked, since it carries full pack
current and inrush.

## 7. Schedule risk

| Item | Delivery | Status |
|---|---|---|
| Rod ends, re-sourced to uxcell B07Q2WHMWK ×2 (8 pcs) | Aug 19 | Resolved. Same M2 × 15 mm part as the original B07Q2V3R61, red instead of blue, in stock. |
| Loc-Line hose kit | Aug 17–18 | Third-party seller, earliest item in the cart. |
| 80 / 40 mesh SS screen | 15 and 10 left | Order before they go out. |

The rod ends stay at M2 × 15 mm, so the original linkage sizing holds and no pushrod rework is
needed. Eight pieces against the two the gimbal uses.

## 8. Materials the carts add that do not fly

ELEGOO Rapid PETG (B0CPF7FDTG) is plain PETG, not the PETG-CF the lower body tube and fins are
specified in. The PETG-CF is already on hand. Use for prototyping, jigs and fixtures.

ELEGOO PLA-CF (B0D86M3RM4) has a heat-deflection temperature near 55 °C, below the predicted
engine-bay wall temperature. Tooling only.

iSANMATE plain ASA (B0DB16JG74) is not Bambu ASA-Aero. ASA-Aero is the foamed low-density grade the
mass cascade assumes for the body tubes, it lives in the Bambu Lab cart, and it has no Amazon
substitute in this BOM.

## 9. Parachute, 24 in

`CHUTE_D = 0.6096 m` is set in `wyvern_datagen/core.py`, `we4_sim.py`, and `we4_validation.py`, and
every descent number derives from it: descent rate 4.8 m/s, inside the 3–7 m/s safe-landing gate.
The trade against a smaller canopy is drift, since a slower descent from the same altitude spends
longer in the wind. Carry that into recovery-area sizing on launch day.
