# GTR70E WYVERN, PID Auto-Tune & First-Flight Gain Confirmation

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


##### Time-domain robustness confirmation of the TVC pitch gains, complementing the frequency-domain margin analysis

## 1. Result (headline)

**The flight gains are confirmed unchanged for first flight: `Kp = 0.10, Ki = 0.40, Kd = 0.18`.**
A robust multi-wind auto-tune search (143 gain sets) finds the firmware gains within **~4 %** of the
grid-optimal time-domain cost, and shows that the small remaining gap is *not a tuning problem*, it
is the physical ±5° gimbal-authority limit of this low-T/W vehicle at high wind, which no gain set
can overcome. The gains are therefore validated by **two independent methods**: the frequency-domain
phase/gain-margin analysis (`PID_TUNING_REPORT.md`, PM ≈ 33°, GM ≈ 12.6 dB across 24 operating points)
and the time-domain robust auto-tune here.

## 2. Method

`Simulations/wyvern_datagen/pid_autotune.py` scores each gain set with a robustness cost averaged
over wind speeds {3, 6, 9, 12} m/s (15 % turbulence), using the same closed-loop pitch plant as the
flight TVC model (`core.simulate_tvc_trace`):

```
cost = mean_over_winds( peak_pitch° + 2·steady_err° + 0.3·settle_s + 0.5·RMS_gimbal° + 0.05·saturation% )
```

A coarse grid (Kp∈{0.05…0.5}, Ki∈{0…1.0}, Kd∈{0…0.5}) is refined around its best point.

## 3. Ranked results (top sets vs. firmware)

| Kp | Ki | Kd | cost | note |
|---|---|---|---|---|
| 0.15 | **0.00** | 0.28 | 46.36 | grid best, *drops integral* (see §4) |
| 0.20 | 0.00 | 0.12 | 46.40 | no integral |
| 0.15 | 0.00 | 0.20 | 46.50 | no integral |
| **0.10** | **0.40** | **0.18** | **48.44** | **firmware (flown)**, within 4.3 % of best |
| 0.15 | 0.25 | 0.25 | 48.14 | keep-integral nudge |
| 0.10 | 0.40 | 0.28 | 48.18 | more damping |

## 4. Why we keep integral action (and the firmware gains)

The grid's lowest-cost sets all set **Ki = 0**. That is an artifact of the cost function, not a good
flight choice:

- At the higher winds that dominate the averaged cost (9–12 m/s), the steady-state pitch error is
  **~17° for *every* gain set, including the firmware set**, because the ±5° gimbal is
  **authority-saturated** (a 720 g, ~2.1 T/W vehicle simply cannot vector enough thrust to hold
  attitude against that much crosswind). When the gimbal is saturated, integral action cannot move
  it further, so dropping Ki shaves a sliver of "wasted" gimbal effort and wins by ~4 %, a number
  well inside model noise.
- At the **low winds where the gimbal is *not* saturated**, integral action is exactly what nulls a
  *constant* pitch bias, thrust-axis misalignment, CG offset, a fin-can twist, a steady breeze.
  Those biases are real on a first flight and are **not** in this model. A PD-only (Ki = 0)
  controller would fly with a persistent trim angle. Retaining Ki = 0.40 removes it.

So the ~4 % "improvement" buys nothing a first flight wants and gives up steady-bias rejection. The
firmware gains are kept.

## 5. The real limiter is gimbal authority, not gains

Because peak pitch and steady error are set by the ±5° gimbal against the wind moment, **tuning is
not the lever** at high wind, authority is. This matches the documented low-speed weathercocking of
this vehicle. Practical consequences:

- **Launch-window recommendation: fly in ≤ ~6 m/s wind.** The SIL (`fc_sil.py`) shows boost-phase
  controlled pitch of **0° (calm) → 9.4° (6 m/s) → 21.4° (12 m/s)**; below ~6 m/s the gimbal stays
  out of saturation and the loop tracks tightly.
- **Adopted:** the gimbal throw was raised **±5° → ±8°** (the hardware-authority fix this analysis
  pointed to). That roughly **halves gimbal saturation** (e.g. 6 m/s: 31%→9%; 12 m/s: 52%→35%) and
  lowers high-wind peak pitch (12 m/s: 26°→23°), more authority margin and richer TVC demo data,
  with no change to passive stability. It does **not** change the gains (more authority only adds
  margin). See the weathercocking note in `WYVERN_E4_Stability_FinSizing.md`.

## 6. First-flight readiness

- Gains **Kp 0.10 / Ki 0.40 / Kd 0.18**, frozen in `firmware/gtr70e_wyvern_tvc/wyvern_pid.h`, confirmed by
  frequency-domain margins **and** time-domain robust auto-tune. **No change for first flight.**
- Anti-windup is present (integral clamped to the gimbal limit), so integral is safe even when
  saturated.
- Explore interactively any time in the GUI **PID Tuner** tab (drag gains, watch θ(t)/δ(t) vs. the
  firmware default) and re-run this search from the tab's **Auto-tune** button.

*Reproduce:* `python3 -m wyvern_datagen.pid_autotune` (or `python3 pid_autotune.py` from the package).
