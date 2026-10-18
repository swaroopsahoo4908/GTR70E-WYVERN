# WYVERN-E 2.0 — Mathematics & Performance Calculations

### A Skylight Rocketry Venture
##### 84 mm 2-Stage Magnetic-TVC 3D-Printed Research Vehicle
##### Companion to *WYVERN-E 2.0 Technical Document*. Figures reproduced by `Sims/run_sims.py`.

## 1. Propulsion Data (manufacturer / ThrustCurve)

| Parameter | Booster (G78 Mojave Green) | Sustainer (F25 White Lightning) |
|---|---|---|
| Designation | AeroTech G78-G, 29 × 124 mm | AeroTech F25-W, 29 × 98 mm |
| Total impulse $I_t$ | 110 N·s | 77.9 N·s |
| Average thrust $\bar{F}$ | 79.9 N | 25.6 N |
| Peak thrust $F_{max}$ | 101.9 N | 46.8 N |
| Burn time $t_b$ | 1.40 s | 3.10 s |
| Propellant mass $m_p$ | 59.7 g | 24.0 g |
| Loaded mass | ~102 g | ~62 g |

Combined stack impulse $I_{t,\text{stack}} = 187.9$ N·s (a *combined-G* flight). $I_{sp,G78} = I_t/(m_p g) = 188$ s.

## 2. Mass Budget (liftoff) — 84 mm airframe

| Item | Mass (g) |
|---|---|
| Printed airframe (PETG-CF / ASA / PC-FR, ~35% infill) | 820 |
| Two-board avionics stack (B1 + B2) + components | 95 |
| Tenergy 12 V NiCd 10S1P pack | 230 |
| Recovery (18″ chute, 6′ Kevlar, hardware) | 60 |
| Wiring/harness, fasteners, igniters | 90 |
| Sustainer motor F25 (loaded) | 62 |
| Booster motor G78 (loaded) | 102 |
| **Liftoff total $m_0$** | **1444** |

Stage decomposition: stage-1 (booster body + fins + G78) ≈ 420 g; stage-2 all-up
(sustainer airframe + avionics + F25) ≈ 1024 g. *The 84 mm airframe is ~18% heavier than the
70 mm baseline; mass is the dominant performance driver (see §4–5).*

## 3. Reference Geometry

$$ D = 84\ \text{mm},\quad R = 42\ \text{mm},\quad A = \pi R^2 = 55.4\ \text{cm}^2 = 5.54\times10^{-3}\ \text{m}^2 $$

Internal TVC mechanism Ø62 mm (excluding the three solenoids, which sit in the 62→84 mm
annulus). Avionics: two stacked Ø80 mm boards (Board 1 TVC Actuator + Board 2 Main FC).
Overall length ≈ 876 mm.

## 4. Thrust-to-Weight

$$ \frac{T}{W}\bigg|_{avg} = \frac{79.9}{1.444 \times 9.81} = 5.6 \qquad \frac{T}{W}\bigg|_{peak} = \frac{101.9}{14.16} = 7.2 $$

Both exceed the $T/W \ge 5$ criterion, but with less margin than the 70 mm build — the larger,
heavier airframe is near the lower bound. *Reducing printed mass (20% infill, 1.6 mm walls)
restores margin and altitude.*

## 5. Trajectory (numerical, exponential atmosphere, drag, $dt=0.2$ ms)

$\rho(h) = 1.225\,e^{-h/8500}$, $C_d = 0.55$, $A = 5.54\times10^{-3}\ \text{m}^2$.

| Event | Combined 2-stage |
|---|---|
| Rail exit (Pro Series II) | 10.0 m/s |
| Booster burnout (≈1.4 s) | ~63 m/s |
| Sustainer burnout | ~68 m/s (peak, Mach 0.20) |
| Max acceleration | 50 m/s² (5.1 g) |
| **Apogee** | **386 m (1 266 ft)**, t ≈ 14.4 s |

Single-config results (see `Sims/WYVERN_E2_Simulation_Results.md`): booster-only (full stack,
sustainer inert) 206 m; TVC-sustainer-only (stage-2 standalone) 155 m. Peak Mach 0.20 — firmly
subsonic, validating the incompressible $C_d$ and the ogive nose.

> *Finding:* the 84 mm vehicle is drag- and mass-limited; apogee falls from 605 m (70 mm) to
> 386 m. To recover altitude on the same 29 mm G/F motors: minimize printed mass, or step the
> booster to an H-class 29 mm (requires HPR certification + waiver).

## 6. Rail Exit (Estes Pro Series II, $L_{rail} \approx 1.0$ m)

$$ v_{rail} = 10.0\ \text{m/s} $$

> *Finding:* below the 15 m/s passive-stability guideline. Use the rail extension (≈1.5 m →
> ~12 m/s) and/or reduce mass. The active TVC engages from ignition, so the controlled vehicle
> tolerates lower rail-exit speed than a passive one — but the fins must still provide static
> margin (§8).

## 7. Recovery (descent)

18″ (0.457 m) chute, $C_d \approx 0.97$, descent mass (stage-2 dry) $m_d \approx 0.96$ kg:

$$ v_{term} = \sqrt{\frac{2 m_d g}{\rho C_d A_c}} = 10.0\ \text{m/s}\ (32.9\ \text{ft/s}) $$

> *Finding:* the heavier 84 mm descent mass pushes landing speed to 10 m/s on the 18″ chute.
> **Upsize to a 24″ main** ($v \propto 1/d$ → $10 \times 18/24 = 7.5$ m/s) for the flight
> vehicle; land on sod (MDRA Coverdale).

## 8. Static Stability (Barrowman)

Fins (84 mm build): root $c_r = 104$, tip $c_t = 46$, span $s = 56$, sweep 66, $N = 4$.

$$ (C_{N\alpha})_{fin} = \frac{4N(s/d)^2}{1+\sqrt{1+\left(\frac{2 l_f}{c_r+c_t}\right)^2}}\left(1+\frac{r}{s+r}\right) = 4.3 $$

with mid-chord line $l_f = 67$ mm. Combined with the nose ($C_{N\alpha,nose}=2$):

$$ X_{cp} \approx 578\ \text{mm from the tip},\quad X_{cg} \approx 438\ \text{mm},\quad SM = \frac{X_{cp}-X_{cg}}{d} = \frac{578-438}{84} \approx 1.7\ \text{cal} $$

within the 1.0–2.0 cal target band. *The wind-tunnel campaign (one fin at a time, custom
mount) refines $C_{N\alpha}$ and confirms $X_{cp}$ for the chosen geometry.*

## 9. Magnetic-Solenoid TVC Authority

Gimbaled sustainer cradle, 3 pull-solenoids at 120°, pull-arm radius $r_c \approx 23$ mm
(on the Ø62 mm gimbal). Commanded gimbal torque at ±5° (sustainer thrust $F=25.6$ N, nozzle-to-CG
$L \approx 0.22$ m):

$$ \tau_{cmd} = F L \sin(5°) = 25.6 \times 0.22 \times 0.0872 = 0.491\ \text{N·m} $$

Per-solenoid force (two active per 120° set): $F_s = \tau_{cmd}/(r_c k_{geom}) \approx 0.491/(0.023\times1.5) = 14\ \text{N}$.
The TOMSHIELE 12 V electromagnets supply 10–25 N at small air-gap — authority margin ≈1.0 at
full deflection, with spring-return fail-safe neutral.

### 9.1 PWM current loop
20 kHz low-side PWM (AO3400A). Coil $R\approx8\ \Omega$, $L\approx12$ mH → $\tau=1.5$ ms; at
20 kHz ($T=50\ \mu s \ll \tau$) current ripple <0.05 A. Peak $I = 12/8 = 1.5$ A; 20 mΩ shunt
→ 30 mV at 1.5 A on the 12-bit ADC (≈37 LSB), 1 k/100 nF anti-alias ($f_c = 1.6$ kHz),
inner loop ≥4 kHz.

## 10. Structural — Airframe Bending

84 mm tube, $D_o=84$, $D_i=80$, $t=2.0$ mm. Max-Q bending at $v_{max}=68$ m/s, $\alpha=2°$:
$q = \tfrac12\rho v^2 = 2.83$ kPa, $N = qAC_{N\alpha}\alpha = 2.4$ N.

$$ I = \frac{\pi}{64}(D_o^4-D_i^4) = 4.33\times10^{5}\ \text{mm}^4,\quad \sigma = \frac{(2.4\times0.30)(42)}{I} \approx 0.07\ \text{MPa} $$

far below PETG-CF flexural strength (~70 MPa) — SF > 900. The larger-diameter tube is far
stiffer; the airframe remains stiffness- (not strength-) driven.

## 11. Test-Stand Calibration

PC-FR stand → Wishiot 10 kg bar cell (HX711, Metro M4). Calibrate with Estes E16-4
($I_t=32.5$ N·s, $\bar F=16$ N): $k = \bar F_{ref}/\overline{ADC}_{ref}$ [N/count];
$I_t = \sum k(\text{ADC}_i)\Delta t$. *The 10 kg cell (98 N) is below the G78 peak (101.9 N) —
re-zero and watch for clipping; swap to a 20 kg cell if clipped.*

---

*Reproducibility:* `Sims/run_sims.py` (point-mass RK4, exponential atmosphere). Manufacturer
impulse/thrust: AeroTech/RCS data sheets, ThrustCurve.org. Barrowman & Barrowman (1966).
