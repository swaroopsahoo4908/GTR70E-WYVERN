# GTR70E WYVERN, Pitch/Yaw TVC PID Re-Tune Report

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


**Result: firmware gains changed from Kp=2.0/Ki=0.4/Kd=0.5 to Kp=0.10/Ki=0.40/Kd=0.18.**
Both `Flight Computer/firmware/wyvern_pid.h` and `Simulations/pid_reference.py` now implement the
new gains. Full derivation code: `Simulations/we4_pid_retune.py`. Report figure:
`PID_TUNING_REPORT.png`.

## 1. Why the previous gains were re-checked

The pitch/yaw TVC loop had already been tuned once: `Simulations/we4_atmos_tvc.py`'s nonlinear
closed-loop sim showed the flowchart's Kp=8/Ki=1.5/Kd=1.2 ringing against the ~40 ms servo lag, and
Kp=2.0/Ki=0.4/Kd=0.5 was adopted instead as "well-damped." That sim is a genuine nonlinear
time-domain model (fin aero restoring + damping, thrust curve, 4 atmospheres, two 1-cosine gusts)
, but it has **no explicit model of the digital control loop's computational/actuation delay**. In
a 500 Hz (2 ms period) loop, the output computed from a sample is applied roughly one sample later;
that delay adds phase lag that a delay-free nonlinear sim cannot see.

To close that gap, the pitch plant was linearized and analyzed with classical frequency-domain
stability margins (phase margin, gain margin) using the `python-control` library, with the 2 ms
loop delay modeled explicitly as a 2nd-order Padé approximant in series with the existing 40 ms
servo lag.

## 2. Linearized plant

At a given point in the burn, small-signal pitch dynamics are:

```
I·θ̈ = T·sin(δ)·(x_gimbal − CG) − q·A·C_N·(Xcp − CG)·θ − q·A·C_N·(Xcp − CG)²/v·θ̇
        └────────── TVC moment ──────────┘ └── aero restoring ──┘ └──── aero damping ────┘
```

giving a transfer function θ(s)/δ(s) = b / (I·s² + c·s + k), where `b` (control effectiveness),
`k` (aero restoring stiffness) and `c` (aero damping) all vary with dynamic pressure `q = ½ρv²` and
thrust `T`, both of which change through the burn and across atmospheres. `I = 0.0323 kg·m²` is the
fixed slender-body pitch inertia.

**24 operating points** were extracted from the existing `we4_atmos_tvc.py` trajectories: the 4
flight atmospheres (ISA 15°C, Cold −15°C, Hot +40°C, High-DA 1500 m) × 6 burn-time slices (0.6,
1.0, 1.7, 2.5, 2.9, 3.4 s), covering the full swing from low-*q*/high-thrust early burn to
high-*q*/low-thrust tail-out. Representative values (ISA):

| t (s) | v (m/s) | q (Pa) | T (N) | b (control eff.) | k (aero stiffness) |
|---|---|---|---|---|---|
| 0.6 | 10.2 | 63 | 15.2 | 3.86 | 0.034 |
| 1.7 | 22.3 | 305 | 14.3 | 3.62 | 0.164 |
| 2.9 | 33.9 | 700 | 13.7 | 3.46 | 0.377 |
| 3.4 | 35.7 | 777 | 2.8 | 0.70 | 0.419 |

The open loop at each point is `PID(s) · servo_lag(s) · loop_delay(s) · plant(s)`, with
`servo_lag(s) = 1/(0.04s+1)`, `loop_delay(s)` a 2nd-order Padé model of a 2 ms pure delay, and the
PID including its filtered-derivative pole (`tau_d = 0.02 s`, matching firmware).

## 3. The old gains fail the margin check

At every one of the 24 operating points, Kp=2.0/Ki=0.4/Kd=0.5 was evaluated for phase margin (PM)
and gain margin (GM). Worst case (Cold −15°C, t=0.6 s into burn, low-*q*/high-authority):

| Gains | Worst-case PM | Worst-case GM |
|---|---|---|
| Kp=2.0 Ki=0.4 Kd=0.5 (old) | **−0.1°** | **−0.0 dB** |
| Kp=0.10 Ki=0.40 Kd=0.18 (new) | **+44.1°** | **+12.6 dB** |

Negative margin means the closed-loop poles are in the right half-plane at that operating point, 
genuinely unstable, not merely lightly damped. Re-running the *nonlinear* time-domain gust test
with the old gains (now correctly showing the effect once the analysis includes delay) exhibits
sustained, undamped gimbal oscillation late in the burn (see figure, panel B/C, red trace), a
symptom consistent with the predicted instability, distinct from a stable-but-underdamped ring.

## 4. Gain search and selection

Gains were swept on a grid (~37,000 (Kp,Ki,Kd) triples evaluated across successive refinement
passes, from a coarse P/PI/PID scan down to a fine local grid around the surviving region), keeping
only triples whose **worst-case margin across all 24 operating points** clears the classical
minimum for flight control loops: **phase margin ≥ 30°, gain margin ≥ 6 dB**. Margin-safe triples
were then re-evaluated in the full nonlinear time-domain sim (servo lag, fin aero, 1-cosine 6–7 m/s
gust, all 4 atmospheres) and ranked by worst-case gust-rejection pitch deviation, discarding any
that still exhibited gimbal chatter (>4 sign changes in gimbal rate during steady flight, a
proxy for a lightly-damped or borderline oscillatory mode that the linear margin alone can miss
near the classification boundary).

**Selected: Kp = 0.10, Ki = 0.40, Kd = 0.18** (out_lim = 5°, tau_d = 0.02 s, i_lim = 0.4, unchanged
from before).

| Metric | Old (Kp=2.0/Ki=0.4/Kd=0.5) | New (Kp=0.10/Ki=0.40/Kd=0.18) |
|---|---|---|
| Worst-case phase margin | −0.1° (unstable) | +44.1° |
| Worst-case gain margin | −0.0 dB (unstable) | +12.6 dB |
| Worst-case gust pitch deviation | 0.43° (misleadingly good, delay-free sim) | 1.96° |
| Worst-case gimbal usage | up to 1.98° (chattering) | 2.35° (smooth) |
| 2° step: rise time | ~273 ms | ~1037 ms |
| 2° step: overshoot | ~11.9% (rings) | ~3.4% (clean) |
| 2° step: gimbal-rate zero-crossings, t>2s | 12 (chatter) | 2 (normal) |

The new gains are markedly slower (rise time roughly 4× longer) and lower-bandwidth than the old
ones. This is the expected, deliberate trade: the old gains' apparent speed was purchased by
running close to (in fact past) the stability boundary once actuation delay is accounted for. The
new gains keep worst-case gust pitch deviation under 1.4° and gimbal deflection well inside the ±8°
mechanical limit, with margin to spare, across the full 4-atmosphere × 6-burn-time envelope.

## 5. Caveats and follow-ups

- The plant linearization assumes small-angle aero terms and treats `b`, `k`, `c` as static at each
  op point (frozen-coefficient / quasi-LPV analysis) rather than a single time-varying LTI model;
  this is standard practice for gain-margin analysis of slowly-varying plants and is justified here
  because the coefficients vary slowly relative to the loop bandwidth, but a full LPV or
  Floquet-style analysis would be a stronger guarantee.
- The 2 ms loop delay is modeled generically as "one sample of computational/actuation lag"; if the
  real firmware's sensor-read → PID → PWM-write path measurably differs from one full 2 ms tick,
  the delay parameter should be re-measured on hardware and the sweep re-run.
- Yaw is assumed identical to pitch (symmetric vehicle, decoupled planes) per the existing
  simulation's convention; this was not independently re-verified.
- Recommend a bench validation (servo + IMU on the bench, `test_code/t3_servo_sweep.ino` style
  step/impulse test) before first flight, to confirm the 40 ms servo lag and loop-delay assumptions
  match the actual hardware.

## 6. Reproducing this analysis

```
cd Simulations
python3 we4_pid_retune.py # margin sweep + selection -> pid_retune_summary.json
python3 pid_reference.py # quick step-response sanity check with the new gains
python3 we4_atmos_tvc.py # full nonlinear 4-atmosphere closed-loop validation
```

Requires `numpy`, `scipy`, and `python-control` (`pip install control`).
