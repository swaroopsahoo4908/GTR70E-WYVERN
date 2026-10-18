# GTR70E WYVERN, 3-Month Project Timeline (2026-08-10 → 2026-12-01)

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


*Budget: 3 man-hours/week. Does not include 3D-print run time (parts print unattended in the
background) but does include CAD/design time, starting/queuing prints, and all post-processing
(support removal, heat-set inserts, sanding, assembly fit-checks). ~13 weeks of scheduled work, ~40 hrs, plus buffer.*

## Target dates (fixed, work backward from these)
- **Launch weekend 1**: Sat–Sun **Nov 7–8, 2026**
- **Launch weekend 2**: Sat–Sun **Nov 14–15, 2026**
- **All data collected by**: **Dec 1, 2026**, with buffer, Nov 30–Dec 1 is slack, not a work day.
- Everything else (electronics, four ground-test stands, four RQ campaigns, airframe, full-stack
  rehearsal) must be done before Nov 7.

## Why two launch weekends, not one
Weekend 1 (Nov 7–8) is the primary flight window, both the F15-4 recovery flight and the RQ
data it produces are the goal. Weekend 2 (Nov 14–15) is the built-in contingency: weather scrub,
hardware anomaly, or a repeat flight if weekend 1's data has a gap. Data collection isn't
"complete" until whichever weekend actually produces a clean flight, hence the Dec 1 cutoff sitting
well past both dates rather than immediately after weekend 1, leaving genuine margin for data reduction.

## Phase map (13 scheduled weeks, 3 hrs/wk = 39 hrs, plus three weeks of end-of-schedule buffer)

| Phase | Weeks | Dates | Hrs | Focus |
|---|---|---|---|---|
| 0. Design lock + ordering | 1–2 | Aug 10 – Aug 23 | 6 | Freeze BOM/CAD, place every order (long-lead items first) |
| 1. Electronics bring-up | 2–4 | Aug 17 – Sep 6 | 9 | Perfboard assembly, firmware smoke test, sensor bus checks |
| 2. Test-stand CAD + builds | 3–6 | Aug 24 – Sep 20 | 12 | CAD, print-queue, and assemble all 4 ground rigs |
| 3. Ground campaigns | 6–10 | Sep 7 – Oct 11 | 15 | Static-fire/jetvane, servo TVC, magnetic TVC, wind tunnel, data collection starts here |
| 4. Airframe build | 8–11 | Sep 21 – Oct 18 | 9 | Print (background), post-process, assemble both body tubes, recovery, avionics bay |
| 5. Integration + rehearsal | 11–13 | Oct 12 – Nov 1 | 9 | Full-stack integration, SIL/HIL checks, dry-run countdown, go/no-go review |
| 6. Launch weekend 1 | 14 | **Nov 7–8** | on-site | Primary flight, F15-4, RQ1–RQ5 flight data |
| 7. Contingency buffer | 15 (partial) | Nov 9–13 | 3 | Data triage from weekend 1; repack/repair if a repeat flight is needed |
| 8. Launch weekend 2 | 15 | **Nov 14–15** | on-site | Contingency/repeat flight only if weekend 1 left a gap |
| 9. Data reduction + report | 16–17 | Nov 16 – **Dec 1** | buffer | Final data pull, cross-check against all 5 RQs, close out |

Phases overlap on purpose, CAD for the wind tunnel can start while the static-fire stand is
already collecting data, for instance. The week ranges are outer bounds, not a rigid sequence.

## Week-by-week (3 hrs/week, Mon-anchored weeks)

| Wk | Dates | Hrs | Work |
|---|---|---|---|
| 1 | Aug 10–16 | 3 | Freeze BOM against the live carts; place Amazon/Adafruit/Estes/Bambu orders now, everything downstream waits on parts arriving. |
| 2 | Aug 17–23 | 3 | Order any remaining long-lead items (motors, breakouts). Lay out the perfboard against the wiring diagram while parts are in transit. |
| 3 | Aug 24–30 | 3 | Parts arrive → solder the perfboard, power-on, I²C scan (expect 0x4A, 0x4B, 0x76, 0x77), microSD logger smoke test. |
| 4 | Aug 31–Sep 6 | 3 | Firmware SIL pass; start CAD on servo TVC + static-fire stands (parallel). |
| 5 | Sep 7–13 | 3 | Queue prints for static-fire + servo TVC stands; CAD the magnetic TVC stand and wind tunnel rig. First static-fire commissioning firing if the stand is ready. |
| 6 | Sep 14–20 | 3 | Post-process + assemble static-fire and servo TVC stands. First static-fire calibration firing (E16-4 commissioning). |
| 7 | Sep 21–27 | 3 | Queue prints for magnetic TVC stand + jetvane/coupon set; start servo TVC campaign (F15-0 firings, load-cell logging). |
| 8 | Sep 28–Oct 4 | 3 | Assemble magnetic TVC stand; begin airframe body-tube prints (background), post-process as they finish. |
| 9 | Oct 5–11 | 3 | Magnetic TVC campaign (RQ1 A/B data collection, mirrors week 7's servo runs). Jetvane/coupon firings on static-fire stand. |
| 10 | Oct 12–18 | 3 | Assemble wind tunnel rig; RQ3/RQ4 aerofoil runs start. Continue airframe post-processing. |
| 11 | Oct 19–25 | 3 | Finish wind tunnel campaign; recovery system (bulkhead joint, chute, wadding) assembly + ground-ejection test. |
| 12 | Oct 12–18 | 3 | Avionics bay integration into the Upper BT (card carriers, separation leads); full-stack power-on with the airframe closed up. |
| 13 | Oct 19–25 | 3 | HIL/SIL regression on the integrated stack; PID gain sweep (RQ5) on the servo TVC stand using the flight avionics stack itself. |
| 14 | Oct 26–Nov 1 | 3 | Dry-run countdown procedure end-to-end; fix whatever the rehearsal exposes. |
| 15 | Nov 2–8 | 3 (+ on-site) | Final go/no-go review early in the week; **launch weekend 1, Nov 7–8**. |
| 16 | Nov 9–15 | 3 (+ on-site if flying) | Triage weekend-1 data against all 5 RQs; repair/repack only if needed; **contingency launch weekend 2, Nov 14–15**. |
| 17 | Nov 16–Dec 1 | buffer | Final data pull and cross-check against all 5 RQs. Nothing new gets built, this is pure margin, and it is now two full weeks rather than two days. |

## Explicit buffer accounting
- **Week 16 exists only as contingency**, if weekend 1 (Nov 7–8) produces clean data across all
  five RQs, week 16 and the Nov 14–15 flight are optional, not required, and that time rolls
  straight into slack.
- **Weeks 16–17 (Nov 16–Dec 1) are unscheduled on purpose**, it exists so "all data by Dec 1" is true
  even if weekend 2 is the one that actually flies.
- Any phase that slips should eat into week 17's buffer first, then week 16's, before pushing the
  Nov 7 launch date, the launch dates are fixed, the schedule bends around them, not the reverse.

## Cross-reference
- Ground-rig build/test detail: `WYVERN_E4_GSE_TestStands.md` (four stands, RQ mapping, motor counts).
- Scope context: `CONFLICTS.md` §6 (wind tunnel + RQ3/RQ4), and the
  jetvane restoration note in `WYVERN_E4_GSE_TestStands.md` §1 / `WYVERN_E4_Build_Guide.md`.
- Procedure-level detail for any given work session: `WYVERN_E4_Timeline_14Day.md` (the original
  day-by-day plan, use it for *what to actually do* in a session; use this doc for *when*).
- Go/no-go criteria: `FLIGHT_READINESS.md`, `WYVERN_E4_BUILD_READINESS.md`.
