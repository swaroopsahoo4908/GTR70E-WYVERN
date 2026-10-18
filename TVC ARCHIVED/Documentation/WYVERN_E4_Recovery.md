# GTR70E WYVERN, Recovery

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


Recovery runs entirely on the F15-4's own ejection charge: no CO2 system, no solenoids, drivers,
cartridges, or needles, no recovery battery, no altimeter-triggered deploy. The flight computer does
not actuate recovery at all — it only logs. The airframe is two separate body tubes (Lower BT, Upper
BT) joined at a single bulkhead, and the ejection charge separates the two tubes at that joint, a
traditional dual-deploy-style break, not a friction-fit nose pop off a single continuous tube.

## 1. Bay layout (nose to tail)

| Body tube | Contents (fwd → aft within the tube) |
|---|---|
| **Upper BT** | Nose cone, Camera, Flight Computer (custom PCB), Battery, Recovery Wadding |
| **Lower BT** | Parachute + Shock Cord, Recovery Wadding, TVC Bay (gimbal, servos, motor mount, motor) |

The two tubes meet at **one bulkhead**, friction-fit/shear-pinned so the ejection charge parts them
cleanly. The bulkhead carries **pass-through holes** for the servo signal/power extensions and the
STEMMA-QT cable running from the flight computer (Upper BT) to the **single external BNO085**
mounted right at the TVC-bay/electronics boundary — the fwd end of the Lower BT / aft end of the
Upper BT, immediately adjacent to the bulkhead joint itself, not deep in the TVC bay on the gimbal.
The custom flight computer PCB is a **circular Ø62 mm board**, sized for the Upper BT: 70 mm OD
airframe less the 1.6 mm wall gives a ~66.8 mm ID, so Ø62 mm clears with **~2.4 mm radial clearance
per side**.

The flight computer PCB carries exactly **one** STEMMA-QT port, so there is one external IMU plus
one onboard body IMU — two physical BNO085s total, voted against each other for attitude. The
bulkhead pass-throughs are wiring holes, not gas seals, so the FC bay sees no gas isolation beyond
the joint itself. Wadding is placed on **both** sides of the bulkhead (aft face of the Upper BT's
contents, fwd face of the Lower BT's parachute pack) as thermal/soot protection for whatever gas
reaches either side of the joint during the brief separation event.

**Open question worth flagging:** mounting the external IMU at the bulkhead boundary rather than on
the gimbal itself means it senses vehicle/joint attitude, not gimbal-relative nozzle deflection
directly. If RQ1's magnetic-vs-servo TVC comparison needs a direct gimbal-deflection measurement,
that's covered by the 3-axis load balance on the ground rigs (per `WYVERN_E4_GSE_TestStands.md`),
not this IMU in flight — confirm that's sufficient for the comparison before treating it as settled.

## 2. Why F15-4

Apogee is at **7.0 s** (burnout 3.45 s + 3.53 s coast), so the ideal ejection delay is ~3.5 s. Of the
off-the-shelf F15 delays, **F15-4** is the closest:

| Motor | Ejection | vs apogee | Deploy speed | Opening load | Verdict |
|---|---|---|---|---|---|
| **F15-4** | 7.45 s | **+0.47 s** | **~4.7 m/s** | ~6 N | near-optimal ✅ |
| F15-6 | 9.45 s | +2.47 s | ~23 m/s | ~147 N | late/hard |
| F15-8 | 11.45 s | +4.47 s | ~39 m/s, only 51 m AGL | ~408 N | unsafe (too low) |

F15-4 deploys just after apogee at a gentle ~4.7 m/s, the softest opening of the three.

## 3. Separation sequence

```
Nose --- Upper BT (Cam / FC / Battery / Wadding) ---[ BULKHEAD JOINT ]--- Lower BT (Wadding / Chute+Cord / TVC Bay) --- Motor
```
1. At t = 7.45 s the F15-4 fires its forward ejection charge, inside the Lower BT's TVC bay region.
2. Gas pressurizes the Lower BT against the recovery wadding and parachute pack, driving pressure up
   against the bulkhead joint.
3. The bulkhead joint releases (friction-fit / shear-pin, sized per §4) and the **two body tubes
   separate**.
4. The parachute, packed at the fwd end of the Lower BT, deploys into the gap. The shock cord
   tethers both halves (anchored in the Lower BT near the TVC bay, and in the Upper BT past the
   wadding) so the vehicle descends as one linked assembly, not two free-falling halves.
5. The servo extensions and STEMMA-QT cable running through the bulkhead holes carry the separation
   event too — see §5.

## 4. Separation force target

The bulkhead joint should release in the **50–150 N** band, soft enough to separate reliably off
the ejection charge's pressure pulse, tight enough that handling/flight vibration doesn't pop it
early. This is an open design item, not a settled number: `WYVERN_E4_FEA_Structural.md` §4.1 has the
491 N/140 kPa driving-load figure the friction-fit or shear-pin sizing needs to be calibrated
against, but the sizing pass itself hasn't been done.

## 5. Open item: cable slack through the bulkhead

The servo extensions are continuous runs from the FC (Upper BT) to the gimbal servos deeper in the
Lower BT; the STEMMA-QT cable runs only as far as the external BNO085 mounted right at the joint
itself (§1), a short run, but it still physically crosses the separation plane. Two ways to handle
the crossing, neither yet decided:
- **Service-loop slack:** enough coiled cable on both sides that the two halves can separate their
  full shock-cord tether length without the harness going taut and yanking a connector loose or
  snapping a wire.
- **Breakaway connector at the bulkhead:** a connector pair mounted flush at the joint that
  disconnects cleanly on separation, so no wire crosses the break at all.
Given TVC control authority is already zero by the time recovery fires (thrust → 0 at burnout, well
before the 7.45 s ejection), the servos don't need to keep functioning post-separation — the only
requirement is that the cable doesn't cause a *mechanical* problem (snag, incomplete separation,
torn connector) during the event. This needs a decision and a bench pull-test before flight.

## 6. Feasibility numbers (`we4_ejection_feasibility.py`)

- **Bay pressurization:** the F15 charge delivers **~140 kPa** into the Lower BT against a
  **14–41 kPa** friction-fit release window → **3.4× margin**. This should hold for a bulkhead-joint
  release calibrated to the same 50–150 N band (§4), but re-verify against the current two-BT
  volume/geometry before treating the margin as final.
- **Deploy dynamics:** ~4.7 m/s at ejection (0.47 s past apogee), ~6 N opening on the 24" chute,
  trivial for the 1/8" Kevlar cord (>1000× SF).

## 7. Sealing & thermal

There is one bulkhead, and it sees combustion gas directly — that's what separates it. Wadding on
both faces is the thermal protection, the same role Nomex/wadding plays in any traditional
dual-deploy rocket. **PETG-CF bulkhead** (HDT ~110 °C) with the ejection pulse being brief (~0.1 s)
should be fine thermally by lumped-wall logic (see `WYVERN_E4_FEA_Structural.md` §4.2), but that
check hasn't been run for the bulkhead's actual geometry yet, not assumed to carry over unchanged
from a generic estimate.

## 8. Ground test (mandatory before flight)

1. **Static separation test:** fire an F15-4 (or a ground-igniter + measured BP sim charge) in the
   built two-BT airframe on the bench, restrained, confirm the bulkhead joint releases cleanly, the
   chute deploys, and the cable pass-through survives the event without damage.
2. **Cable pull-test:** with the joint held at full shock-cord extension, confirm the servo/STEMMA-QT
   harness (whichever solution from §5 is chosen) doesn't bind, snag, or take load it shouldn't.
3. **Release-force check:** confirm the bulkhead joint's actual release force lands in the 50–150 N
   band (§4) — too tight and it won't separate reliably, too loose and flight vibration risks early
   separation.
4. **Chute pack + Nomex/wadding:** verify wadding on both bulkhead faces adequately shields the
   canopy and the Upper BT's electronics bay from the ejection gas.

## 9. Why this is the right recovery approach for GTR70E WYVERN

The motor already carries a perfectly-timed ejection charge, so recovery needs zero electronics,
zero battery, zero pyro handling — just wadding, a chute, cord, and a joint sized to release at the
right force. A friction-fit joint between the two body tubes is a well-proven dual-deploy-style
break, at the cost of the two open items above (§4 release-force sizing, §5 cable slack) that need
closing before this is flight-ready.
