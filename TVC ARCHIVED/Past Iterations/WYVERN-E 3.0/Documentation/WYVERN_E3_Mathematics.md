# WYVERN-E 3.0 — Engineering Mathematics

### Skylight Rocketry · 84 mm two-stage Pi-5 TVC vehicle (no-waiver)
##### Reproducible: `Simulations/we3_analysis.py`, `Simulations/run_sims.py`. All figures reconcile.
## 1. Mass budget (g)

| Group | Solenoid | Servo |
|---|---:|---:|
| Sustainer avionics (Pi 5 + camera + 3× BNO085 + LSM6DSO32 + LIS2MDL + BMP280 + BME688 + 2× µSD + RRC3+ + harness) | 189 | 189 |
| Sustainer power (3S 3000 mAh + BMS/PD + bucks) | 190 | 190 |
| Sustainer structure (PC-FR) | 300 | 300 |
| Sustainer recovery + nose BNO085 | 116 | 116 |
| TVC mechanism | 120 | 220 |
| Sustainer motor (G25W-10A loaded) | 124 | 124 |
| Booster (PC-FR struct 180 + F reload 70) | 250 | 250 |
| **Liftoff $m_0$** | **1289** | **1389** |

Both < **1500 g** Class-1 ceiling. Total propellant = F (~16 g) + G25W (62 g) = **78 g < 125 g**.

## 2. Thrust-to-weight & rod clearance

Booster F32-class, Favg = 32 N (worst case servo build, $m_0$ = 1.389 kg):

$$\text{T/W} = \frac{F}{m_0 g} = \frac{32}{1.389\times 9.81} = 2.35\;? $$

— that is the *average*; an F32-class peaks ~50–60 N. Sizing the booster to **Favg ≥ 5·m₀·g
= 68 N** (a punchy F) gives T/W ≥ 5 off the rod. The fins (oversized) provide passive
stability during the booster phase (TVC is on the unlit sustainer). *Design rule:* booster
selected for **Favg ≈ 70 N**, T/W ≈ 5.1–5.3.

Sustainer G25W ignites post-staging at ~36 m/s, so it needs no high T/W:
$$\text{T/W}_{sus} = \frac{25}{1.039\times 9.81} = 2.45\;(\text{fine — vehicle already moving}).$$

## 3. Apogee (two-stage, RK4 point-mass)

Model: $m\dot v = F(t) - \tfrac12\rho(h)C_d A v|v| - mg$, $\rho(h)=1.225e^{-h/8500}$,
$A=\pi(0.042)^2=5.54\times10^{-3}$ m², **Cd = 0.90** (oversized fins), staging coast 0.4 s.

| Phase | Result |
|---|---|
| Booster burnout | ~12 m, ~30 m/s |
| Staging | ~13 m (42 ft) |
| Sustainer burnout (4.7 s) | ~58 m/s |
| **Apogee** | **~310 m (1015 ft)** |

The oversized fins (Cd 0.90 vs 0.55 baseline) are what hold apogee **under the ~1100 ft cap**
despite the long burn; a bigger booster would push past 1800 ft (see `Power_Mass_Motor` §3).

## 4. Static stability (Barrowman)

CP ≈ 0.70 L (oversized fins move it aft), CG ≈ 0.50–0.53 L (shifts forward as propellant
burns), L = 0.95 m, 1 cal = 84 mm:

$$\text{margin} = \frac{x_{CP}-x_{CG}}{D} = \mathbf{1.9\text{–}2.3\ cal}$$

Slightly above the classic 1.0–2.0 band — intentionally over-stable for a long, low-speed
sustainer burn where the TVC is the primary controller and the fins are passive backup.

## 5. Recovery (descent)

24″ (0.610 m) main, $C_d\approx 0.97$, descent mass ≈ 1.15 kg (no booster):
$$v_{term}=\sqrt{\frac{2 m g}{\rho C_d A_c}} = \sqrt{\frac{2(1.15)(9.81)}{1.225(0.97)(0.292)}}=8.1\ \text{m/s}\ (26.6\ \text{ft/s}).$$
Acceptable on sod for the PC-FR airframe; upsize to 30″ → 6.5 m/s if landing loads warrant.

## 6. Power & energy

Continuous load 4.23 W idle / 8.33 W active. Energy for 2.5 h idle + 5 flights × 10 min active:
$$E = 4.23(2.5) + 8.33\tfrac{10}{60}(5) = 17.7\ \text{Wh} \Rightarrow 23.8\ \text{Wh (×1.35 margin)}.$$
3S 3000 mAh = **33.3 Wh → 1.9× margin.** USB-C PD recharge ~1 h.

## 7. TVC actuator sizing

Gimbal-axis torque at ±5°, G25W peak ~100 N, pivot offset 45 mm, ×1.6 (friction+dynamic):
$$\tau = 100(0.045)\sin5°\times1.6 = 0.63\ \text{N·m} \Rightarrow \text{servo (SF 2.5, 1:1)} = 1.57\ \text{N·m} = \mathbf{16\ kg\cdot cm}.$$
Selected servos **~35 kg·cm** (margin) — ~8× BPS Space's 9 g micro servos (~2 kg·cm). Solenoid
system: 3× 12 V pull-coils, PWM 3-coil mixing, peak ~33 W.

## 8. No-waiver compliance summary

| Gate | Limit | 3.0 | Pass |
|---|---|---|---|
| Liftoff weight | ≤ 1500 g | 1289–1389 g | ✓ |
| Total propellant | ≤ 125 g | 78 g | ✓ |
| Motor class | ≤ G | F (booster) + G25W (sustainer) | ✓ |

**No FAA waiver, no Level-1 certification required.**
