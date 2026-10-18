# WYVERN-E 3.0 — Booster Motor & Rail-Exit Velocity Analysis

### Single-use vs reload, F25W/F40W/F50T/G80T, and the sustainer — June 2026 revision

## 1. The question

Can we (a) move to single-use motors (no reload casings), (b) revert to an F25W booster, and
(c) clear the rail safely? Short answer: the **vehicle is mass-limited** — at ~1.29 kg liftoff,
*no* F-class booster clears the rail with comfortable margin, and the long-burn G25W sustainer
**cannot** be made single-use.

## 2. Method

Rail-exit velocity by the energy method, $v_{exit}=\sqrt{2\,a\,L}$ with
$a=(T-m g)/m$, evaluated at both **average** thrust (conservative) and **peak/initial** thrust
(optimistic, and closest to the real first-0.3 s rail phase). $m_0 = 1.20\ \mathrm{kg}$
(dry vehicle + installed G25W sustainer) + booster mass. Rails: 6 ft (1.83 m) and 8 ft (2.44 m)
1010. Thrust data from ThrustCurve/NAR certification.

Threshold (standard practice): **≥ 15 m/s (50 ft/s)** safe; 12–15 marginal; < 12 unsafe (the
booster flies on *fixed fins* — TVC is only on the sustainer — so it needs real passive
stability velocity off the rail).

## 3. Results

| Motor (SU) | total | avg / peak N | m₀ kg | T/W | v, 6 ft (avg–pk) | v, 8 ft (avg–pk) | prop + G25W | verdict |
|---|---|---|---|---|---|---|---|---|
| **F25W** | 77.9 N·s | 25.6 / 50.6 | 1.29 | 2.0 | 6.1–10.4 m/s | 7.0–12.0 m/s | 98 g | ✗ unsafe — too slow |
| **F40W** | 78.1 N·s | 37.9 / 68.1 | 1.33 | 2.9 | 8.3–12.3 | 9.6–14.2 | 102 g | ✗ marginal, < 15 |
| **F50T** | 76.8 N·s | 53.7 / 68.5 | 1.29 | 4.3 | 10.8–12.6 | 12.5–14.6 | 100 g | △ borderline — best F |
| **G80T** | 129.5 N·s | 71.6 / 102.2 | 1.33 | 5.5 | 12.7–15.7 | 14.7–18.1 | 125 g | ✓ clears, but G-class |

## 4. Reading the table

- **Reverting to F25W: no.** T/W 2.0, rail exit 6–12 m/s — it would weathercock/land-shark off
  the rail. (The F25W is fine as a *sustainer* once already moving, but not as a booster.)
- **F40W: marginal** (≤ 14 m/s even on an 8-ft rail at peak thrust) — below the 15 m/s bar.
- **F50T (Blue Thunder): the best ARC-legal F** — high initial thrust (68.5 N), T/W 4.3, ~14.6 m/s
  on an 8-ft rail at peak. *Acceptable but not comfortable.* Use an 8-ft (or 10-ft) rail and trim
  mass; do **not** fly it off a 6-ft rod.
- **G80T (single-use Blue Thunder G): the only motor that clears with margin** (15–18 m/s), but it
  is **G-class** (not an ARC booster under the 80 N·s / F-class rule) and with the G25W it hits the
  **125 g** no-waiver propellant cap *exactly* (zero margin), and it raises apogee well past 1000 ft.

## 5. Recommendation

For an **ARC-legal, single-use booster**: **AeroTech F50T (single-use) on an 8-ft 1010 rail.** It is
the only F that reaches ~15 m/s with this stack, it is on the ARC certified list (one F50T = 76.8 N·s
< 80), and single-use means **no booster casing**. To buy margin, shave ~100–150 g off the dry
vehicle and/or use a 10-ft rail. If ARC-legality can flex and you accept a higher apogee, the **G80T**
single-use clears best — but it maxes the 125 g propellant limit.

## 6. The sustainer — stays G25W (reload-only)

The TVC demonstration needs the long burn: **G25W = 117 N·s over 4.7 s** (avg 25 N). Post-staging
the sustainer is already at ~45 m/s, so its low thrust is fine. *There is no single-use long-burn
G* — every DMS single-use G (G72, G80T, G125T) is a short 1.5–2 s high-thrust motor. So the
sustainer **must** remain the G25W *reload*, which needs **one** RMS-29/40-120 casing (reusable).

## 7. Single-use vs reload — cost reality (8 flights + 2 ground each)

| Path | Booster | Sustainer | Casings | 8-flight motor cost |
|---|---|---|---|---|
| **Chosen — SU booster** | F50T SU 8×$42.36 = $338.88 | G25W reload 8×$33.30 = $266.40 | 1×$100.34 | **$705.62** + igniters |
| Reload booster (alt) | F40W reload 8×$22.99 = $183.92 | G25W reload 8×$33.30 = $266.40 | 2×$100.34 = $200.68 | $651.00 + igniters |

Single-use is **~$55 more** over 8 flights (the $42 SU F50T outweighs the saved casing) — but it
removes a casing, simplifies range ops, and keeps the booster ARC-legal. If raw cost over many
flights is the priority, the reloadable F booster (2 casings) is cheaper; for fewer flights or
simplicity, single-use wins. *Cheapest single-use option to investigate: an EconoJet F-class
(~$15) — but verify its rail-exit before committing.*

## 8. Net config (now in the BOM)

Booster **F50T single-use** (Apogee, $42.36) · sustainer **G25W-10 reload** (Apogee, $33.30) +
**one** RMS-29/40-120 casing ($100.34) · 8-ft rail. Re-sim apogee with these (≈194 N·s total) — it
may land ~1100–1400 ft; add nose mass or fin area to hold ≤ ~1100 ft if needed.
