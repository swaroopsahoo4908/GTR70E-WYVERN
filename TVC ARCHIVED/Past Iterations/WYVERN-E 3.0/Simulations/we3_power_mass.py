#!/usr/bin/env python3
"""WYVERN-E 3.0 — power, mass, and motor feasibility analysis (Pi-5 off-the-shelf FC)."""
import numpy as np
print("="*70); print("WYVERN-E 3.0  POWER + MASS + MOTOR FEASIBILITY"); print("="*70)

# ---------- POWER BUDGET (W) ----------
# (component, idle_W, active_W, mass_g)
P=[
 ("Raspberry Pi 5 (4GB) + active cooler", 3.5, 6.5, 66),
 ("Camera Module 3 (recording)",          0.05,0.30, 12),
 ("3x BNO085 (TVC/FC/nose)",              0.12,0.12, 9),
 ("LSM6DSO32 IMU",                         0.01,0.01, 1.3),
 ("LIS2MDL magnetometer",                  0.005,0.005,1.3),
 ("BMP280 barometer",                      0.005,0.005,1.3),
 ("BME688 gas/T/P/RH",                     0.02,0.04, 2.0),
 ("2x microSD breakout (writing)",         0.10,0.70, 4),
 ("RRC3+ deployment/ignition controller",  0.02,0.05, 17),
 ("buck/PD/BMS power electronics",         0.40,0.60, 40),
 ("harness + connectors",                  0.0, 0.0, 35),
]
idle=sum(x[1] for x in P); active=sum(x[2] for x in P)
print("\n-- Continuous electronics load --")
for n,i,a,m in P: print(f"  {n:42} idle {i:4.2f} W   active {a:4.2f} W")
print(f"  {'TOTAL (continuous)':42} idle {idle:4.2f} W   active {active:4.2f} W")

# TVC power is intermittent (burn only) -> energy negligible, drives peak current only
sol_peak=3*1.0*11.1; svo_peak=3*1.2*6.0
print(f"\n-- TVC peak draw (burn only, ~3 s) --  solenoid {sol_peak:.0f} W   servo {svo_peak:.0f} W (energy negligible vs idle)")

# ---------- ENERGY for 5 flights + 2 hr+ idle ----------
idle_hr=2.5                      # pad/standby
ops_min_per_flight=10; flights=5 # boot/arm/fly/recover/save active recording
E_idle=idle*idle_hr
E_ops=active*(ops_min_per_flight/60.0)*flights
E_tvc=sol_peak*3*flights/3600.0  # all-burn solenoid energy across flights
E=E_idle+E_ops+E_tvc; Emargin=E*1.35
print(f"\n-- Energy budget --")
print(f"  idle  {idle:.1f} W x {idle_hr} h            = {E_idle:5.1f} Wh")
print(f"  ops   {active:.1f} W x {ops_min_per_flight} min x {flights} fl = {E_ops:5.1f} Wh")
print(f"  TVC pulses (all flights)         = {E_tvc:5.2f} Wh")
print(f"  TOTAL {E:.1f} Wh  -> +35% margin = {Emargin:.1f} Wh")

# Battery: 3S Li-ion
for mah in (2600,3000,3500):
    wh=11.1*mah/1000.0; print(f"  3S Li-ion {mah} mAh = {wh:.1f} Wh  ->  margin x{wh/E:.2f}  ({'OK' if wh>=Emargin else 'tight'})")
batt_g=150  # 3x 18650 ~ 150 g

# ---------- MASS BUDGET ----------
M_avionics=sum(x[3] for x in P)+batt_g
print(f"\n-- Mass: flight-computer + power = {M_avionics:.0f} g (incl. {batt_g} g 3S pack)")
TVC_sol=90+60   # 3 solenoids + gimbal hardware
TVC_svo=180+70  # 3 hi-torque servos + linkages + gimbal
struct=560      # printed bays + bulkhead (heavier than 2.0's 420 g sustainer struct)
nose_bno=9; chute_hw=70; F25_load=62
sus_sol = M_avionics+TVC_sol+struct+chute_hw+F25_load
sus_svo = M_avionics+TVC_svo+struct+chute_hw+F25_load
print(f"  Sustainer all-up (solenoid TVC) = {sus_sol/1000:.2f} kg")
print(f"  Sustainer all-up (servo TVC)    = {sus_svo/1000:.2f} kg")

# ---------- MOTOR FEASIBILITY ----------
g=9.81
F25=dict(name="AeroTech F25W",It=77.9,Favg=25.6,Fmax=46.8,tb=3.1)
print(f"\n-- F25W feasibility (sustainer standalone, TVC active off the rod) --")
for nm,m in [("solenoid",sus_sol/1000),("servo",sus_svo/1000)]:
    tw_avg=F25['Favg']/(m*g); tw_pk=F25['Fmax']/(m*g)
    print(f"  {nm:9} m={m:.2f} kg:  T/W avg {tw_avg:.2f}  peak {tw_pk:.2f}   "
          f"({'UNSAFE <5' if tw_avg<5 else 'ok'})")
# what motor is needed for T/W>=5 on the servo (heavier) case
m=sus_svo/1000; need_Favg=5*m*g
print(f"\n  For T/W>=5 at {m:.2f} kg need Favg >= {need_Favg:.0f} N  (F25 gives 25.6 N)")
# candidate 29mm motors
cands=[("AeroTech F67W",94.6,67,1.4),("AeroTech G78",110,79.9,1.4),
       ("AeroTech H128W",163,128,1.3),("AeroTech H100W",186,100,1.9),("CTI H143",163,143,1.1)]
print("  candidate sustainer motors (29 mm):")
for nm,It,Favg,tb in cands:
    print(f"    {nm:14} It {It:5.0f} Ns  Favg {Favg:5.0f} N  tb {tb:.1f}s  -> T/W {Favg/(m*g):.1f}  {'OK' if Favg/(m*g)>=5 else 'no'}")
