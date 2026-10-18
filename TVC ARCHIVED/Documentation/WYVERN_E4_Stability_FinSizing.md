# GTR70E WYVERN, Stability & Fin Sizing (RESOLVED: 87 mm fins, NO ballast)

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


*Barrowman + RK4 apogee sweep, `../Simulations/we4_stability.py`, `plots4/config_optimized.json`.*

## Why fins, why no ballast
TVC engages only **after the first ~0.5 s** (past the F15 ignition spike). For launch + that window
the rocket must be **passively stable**, or it tumbles. So fins are mandatory. **Ballast is not:**
an apogee sweep shows every gram of nose ballast *lowers* apogee (dead weight costs more than the
smaller fins it buys). So we drop ballast entirely and size the fins for the **minimum stable
margin (1.0 cal)** to maximize altitude.

## Apogee vs ballast (fins resized to hold 1.0 cal at each ballast, RK4 + Barrowman)
Every gram of nose ballast costs apogee: the smaller fins it buys never pay back the dead weight.
The relative trend below (every gram of ballast costs more apogee than the smaller fin buys back)
is the reason ballast is dropped entirely; see "Chosen configuration" for the exact flown numbers.

| Ballast | Fin span for 1.0 cal | Trend |
|---|---|---|
| **0 g (chosen)** | **76.2 mm** → flown at **87 mm** for margin | baseline |
| 60 g | 59.4 mm | smaller fin, but net apogee loss |
| 150 g | 46.9 mm | smaller fin still, larger net apogee loss |

The flown fin is 87 mm rather than the 76.2 mm minimum: 76.2 mm sits exactly on the 1.0 cal floor
with no allowance for build tolerance, and the CG-tolerance sweep (`we4_deepsim.py` D) shows 1.0 cal
survives only limited aft CG error. 87 mm buys +1.14 cal nominal and keeps a comparable buffer at the
build-error limit.

## Chosen configuration
| Parameter | Value |
|---|---|
| Ballast | **none** |
| Fins | **4 ×**, root 70 / tip 35 / LE-sweep 25 / **span 87 mm**, PETG-CF 3 mm airfoil (~71 g) |
| CG / CP / margin | 45.0 cm / 53.3 cm / **+1.14 cal** (stable; ASA-Aero upper+lower body + PETG-CF fins) |
| Liftoff / T-W | **720 g** / 2.10 avg, 3.70 peak |
| Apogee (RK4+Barrowman) | **~409 ft / 124.6 m @ 6.72 s**; F15-4 ejects t=7.45 s, +0.58 s past apogee @ ~5.7 m/s |
| v_max / Mach | **37.1 m/s / Mach 0.108** |
| Rail exit (1.0 m rail) | pending re-verify against the new mass stack; see the weathercock discussion below |
| 35 mm fin (rejected) | **UNSTABLE**; 1.0 cal needs ≥76.2 mm, 1.5 cal needs a larger span still |

1.0 cal is the minimum conventionally-stable margin, enough to hold attitude through launch and the
0.5 s pre-TVC window while leaving the TVC free to maneuver, and the lightest path to maximum apogee.

## Weathercocking & TVC, does the TVC prevent it, and how do we manage it?

**Weathercocking** is a *statically-stable* rocket's tendency to rotate its nose into the relative
wind: a crosswind creates an angle of attack, and the fins' restoring moment turns the vehicle to
kill that AoA. It is worst at **low speed** (just off the rail, where a given crosswind is a large
fraction of the airspeed) and in **strong wind**.

**Does the TVC prevent it?** Partially, and only while the motor burns:

- **Powered flight (0.5–3.45 s):** the gimbal produces a control moment that *opposes* the pitch
  deviation, so the TVC actively fights weathercocking, up to its authority. At **±5°** the gimbal
  saturated in wind above ~6 m/s (it could resist, but not fully hold vertical). Raising the throw to
  **±8°** gives authority headroom: gimbal saturation roughly halves and the loop tracks tighter.
- **After burnout (coast to apogee):** thrust → 0, so there is **no** thrust to vector and the TVC
  can do nothing. The vehicle weathercocks/noses over aerodynamically near apogee (the ~90° nose-over
  seen in the SIL). This is normal and harmless, recovery is the motor's ejection charge, not
  attitude-dependent, so it is *not* something we try to "fix."

**How we manage weathercocking without diminishing the TVC demonstration** (the whole point of the
vehicle is to *show* TVC rejecting disturbances and to collect control data, so we must not simply
make it so passively stable that the TVC has little to do):

1. **More control authority, not more fin.** Gimbal throw raised **±5° → ±8°**, directly improves
   boost-phase weathercock rejection and *enriches* the demo (the gimbal works in its linear range
   and can command larger authenticated deflections). Passive stability is unchanged, so the TVC
   still has a real job. *(We deliberately do NOT enlarge the fins / raise the static margin: that
   would suppress weathercocking passively but shrink the disturbance the TVC exists to demonstrate.)*
2. **Higher rail-exit velocity.** A longer launch rail (≈1.5–2 m vs ~1 m) gets the vehicle moving
   faster before it is aerodynamically free, lowering the wind-induced AoA at the critical low-speed
   instant. Operational/GSE change only, no vehicle impact.
3. **Low-wind launch window (≤ ~6 m/s).** The dominant lever, since at high wind the ±8° gimbal is
   still authority-limited on this ~2 T/W vehicle. At ≤6 m/s boost pitch stays under ~10° with the
   gimbal out of saturation.

Net: the 87 mm fins give just enough passive stability to survive the rail + the 0.5 s pre-TVC
window; everything beyond that is handled by the (now higher-authority) TVC, which is exactly the
behaviour the flight is meant to demonstrate and log.
