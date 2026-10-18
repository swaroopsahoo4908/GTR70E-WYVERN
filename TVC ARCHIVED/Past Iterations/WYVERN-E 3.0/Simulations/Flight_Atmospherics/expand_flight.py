#!/usr/bin/env python3
"""WYVERN-E 2.0 -- expanded flight + atmospheric dataset.

Takes the *exact* combined two-stage trajectory produced by ../run_sims.py (so
apogee/Mach reconcile with the OpenRocket .ork configs and the Mathematics doc,
combined ~386 m) and enriches every point of the ascent with a large set of
atmospheric and flight quantities derived from the U.S. Standard Atmosphere 1976
model: temperature, pressure, density, speed of sound, viscosity, kinematic
viscosity, the atmospheric ratios, Mach number, dynamic pressure, body and fin
Reynolds numbers, and the thrust/drag/weight balance.

Outputs (this folder):
  flight_state.csv        -- ascent time history, all derived columns
  isa_reference.csv       -- standalone ISA table (fine 0-2 km + coarse to 30 km)
  flight_atmospherics.png -- 6-panel flight + atmosphere figure
"""
import os, sys, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from atmosphere_isa import state, g0

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import run_sims as RS                      # reuse the project trajectory engine (baseline)

# ---- vehicle geometry for the derived aero columns ----
D     = 0.084                              # body diameter [m]
A     = np.pi*(D/2)**2                     # frontal area [m^2]
Cd0   = RS.Cd                              # 0.55, same Cd as run_sims
C_FIN = 0.075                              # mean fin chord [m] (fin Reynolds)
# masses consistent with run_sims combined model
m_boost_wet = RS.m_booster_dry + RS.m_stage2          # 1.342 kg dynamic boost mass
m_stage2    = RS.m_stage2                             # 1.024 kg sustainer all-up

def run(sample=0.05):
    """Resample run_sims' combined ASCENT and derive the enriched state."""
    comb = RS.comb
    ts, hs, vs = comb["ts"], comb["hs"], comb["vs"]
    t_apogee   = comb["t_apogee"]
    ph1_tend   = RS.ph1["tend"]            # booster coasts to apogee, then sustainer ignites
    tb1, tb2   = RS.G78["tb"], RS.F25["tb"]
    md1, md2   = RS.G78["mprop"]/tb1, RS.F25["mprop"]/tb2

    rows=[]; next_s=0.0; vmax=0.0; amax=0.0
    for t,h,v in zip(ts,hs,vs):
        if t > t_apogee + 1e-9: break                 # ascent only
        # phase / thrust / mass (mirrors run_sims combined staging)
        if t < tb1:
            F=RS.G78["Favg"]; m=m_boost_wet-md1*t;            phase="boost"
        elif t < ph1_tend:
            F=0.0;           m=m_boost_wet-RS.G78["mprop"];   phase="coast-to-staging"
        elif t < ph1_tend+tb2:
            F=RS.F25["Favg"]; m=m_stage2-md2*(t-ph1_tend);    phase="sustain"
        else:
            F=0.0;           m=m_stage2-RS.F25["mprop"];      phase="coast-to-apogee"
        atm = state(h)
        q   = 0.5*atm["rho"]*v*abs(v)
        drag= q*Cd0*A
        W   = m*g0
        a   = (F-drag-W)/m
        vmax=max(vmax,v); amax=max(amax,a)
        if t>=next_s:
            rows.append(dict(t=t, phase=phase, h=h, v=v,
                mach=abs(v)/atm["a"], q=q, drag=drag, thrust=F, weight=W, mass=m,
                accel=a, accel_g=a/g0, TW=(F/W if W>0 else 0.0),
                T=atm["T"], T_C=atm["T_C"], p=atm["p"], p_kPa=atm["p_kPa"],
                rho=atm["rho"], a_snd=atm["a"], mu=atm["mu"], nu=atm["nu"],
                sigma=atm["sigma"], delta=atm["delta"],
                Re_body=atm["rho"]*abs(v)*D/atm["mu"],
                Re_fin=atm["rho"]*abs(v)*C_FIN/atm["mu"]))
            next_s += sample
    summ = dict(apogee=comb["apogee"], vmax=vmax, amax=amax,
                mach_max=vmax/state(0)["a"], t_apogee=t_apogee,
                stage_h=comb["stage_h"], stage_v=comb["stage_v"])
    return rows, summ

def isa_table():
    zs = list(range(0,2001,25)) + list(range(2250,30001,250))
    out=[]
    for z in zs:
        s=state(z)
        out.append(dict(z_m=z, h_geopot_m=round(s["h"],1), T_K=s["T"], T_C=s["T_C"],
            p_Pa=s["p"], p_kPa=s["p_kPa"], p_atm=s["p_atm"], rho_kgm3=s["rho"],
            a_ms=s["a"], mu_Pas=s["mu"], nu_m2s=s["nu"], sigma=s["sigma"],
            delta=s["delta"], theta=s["theta"]))
    return out

def write_csv(path, rows):
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows:
            w.writerow({k:(round(v,6) if isinstance(v,float) else v) for k,v in r.items()})

def plots(flt, isa, summ):
    t=[r["t"] for r in flt]
    fig,ax=plt.subplots(2,3,figsize=(15,8))
    ax[0,0].plot(t,[r["h"] for r in flt]);                 ax[0,0].set(title="Altitude",xlabel="t [s]",ylabel="h [m]")
    ax[0,1].plot(t,[r["v"] for r in flt],"tab:orange");    ax[0,1].set(title="Velocity",xlabel="t [s]",ylabel="v [m/s]")
    ax[0,2].plot(t,[r["mach"] for r in flt],"tab:green");  ax[0,2].set(title="Mach number",xlabel="t [s]",ylabel="M")
    ax[1,0].plot(t,[r["q"] for r in flt],"tab:red");       ax[1,0].set(title="Dynamic pressure",xlabel="t [s]",ylabel="q [Pa]")
    ax[1,1].plot(t,[r["Re_fin"] for r in flt],"tab:purple");ax[1,1].set(title="Fin Reynolds number",xlabel="t [s]",ylabel="Re_fin")
    z=[r["z_m"] for r in isa]
    ax[1,2].plot([r["sigma"] for r in isa],z,label="rho/rho0")
    ax[1,2].plot([r["delta"] for r in isa],z,label="p/p0")
    ax[1,2].plot([r["theta"] for r in isa],z,label="T/T0")
    ax[1,2].set(title="ISA ratios vs altitude",xlabel="ratio",ylabel="alt [m]"); ax[1,2].legend()
    fig.suptitle(f"WYVERN-E 2.0 flight atmospherics  |  apogee {summ['apogee']:.0f} m, "
                 f"Vmax {summ['vmax']:.0f} m/s (M {summ['mach_max']:.2f}), amax {summ['amax']/g0:.1f} g  "
                 f"[trajectory = run_sims combined]", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(HERE,"flight_atmospherics.png"),dpi=110); plt.close(fig)

if __name__=="__main__":
    flt,summ = run(); isa = isa_table()
    write_csv(os.path.join(HERE,"flight_state.csv"), flt)
    write_csv(os.path.join(HERE,"isa_reference.csv"), isa)
    plots(flt, isa, summ)
    print(f"flight rows={len(flt)}  isa rows={len(isa)}")
    print(f"apogee={summ['apogee']:.1f} m  Vmax={summ['vmax']:.1f} m/s  "
          f"Mmax={summ['mach_max']:.3f}  amax={summ['amax']/g0:.1f} g  "
          f"t_apogee={summ['t_apogee']:.1f} s  staging@{summ['stage_h']:.0f} m / {summ['stage_v']:.1f} m/s")
    print("wrote flight_state.csv, isa_reference.csv, flight_atmospherics.png")
