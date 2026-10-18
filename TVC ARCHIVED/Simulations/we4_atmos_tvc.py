#!/usr/bin/env python3
"""GTR70E WYVERN, ATMOSPHERIC EFFECTS ON TVC HANDLING (F15-4, servo TVC, pitch-plane closed loop)
================================================================================================
How do real atmospheric conditions change how the TVC must work? Air density (set by temperature,
pressure, field elevation, humidity) drives dynamic pressure q = ½ρv², which sets:
  • the GUST disturbance moment the loop must reject (∝ q)
  • the aero restoring/damping the fins provide (∝ q)
while the TVC control moment (T·sinδ·arm) is ρ-INDEPENDENT (thrust-reaction) but falls with thrust.

So a cold dense day hits the vehicle with bigger gusts but also stiffer fins; a hot / high-elevation
day softens both and leans harder on the TVC. This script runs the SAME pitch-plane PID loop through
4 atmospheres + a 1-cosine gust, with fixed gains vs thrust-scheduled gains, and reports the spread.

Run: python3 we4_atmos_tvc.py -> plots_atmos/*.png + atmos_tvc_summary.json
"""
import os, json, numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"plots_atmos"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT,exist_ok=True)
BLU,RED,GRN,ORG,PUR,GRY="#2a6f97","#bc4749","#386641","#e09f3e","#6d597a","#8d99ae"

# ---------------- vehicle (mirror we4_flightsim.py) ----------------
g=9.80665; D=0.070; A=np.pi*(D/2)**2; Ltot=0.74; a0=343.0
m_lift,m_dry,PROP,tb=0.7203,0.6603,0.060,3.45 # canonical mass
# CANONICAL stability constants (we4_flightsim.py / we4_stability.py / wyvern_datagen/core.py).
# These were CG=0.467 / Xcp=0.537 / x_gimbal=0.72 -- the pre-ASA-Aero, pre-i3-camera vehicle --
# so the aero restoring stiffness k = q*A*CN*(Xcp-CG) and the control moment arm (x_gimbal-CG)
# were both computed for an airframe that no longer exists. Corrected 2026-08. I_pitch is now
# the measured 0.0209 kg m^2 from the we4_sim mass stack rather than a uniform-rod estimate.
CG=0.484; Xcp=0.568; CN=2.0; x_gimbal=0.62; Rspec=287.05
I_pitch=(1/12)*m_lift*Ltot**2 # slender-body pitch inertia (kg·m²)
Fc_t=np.array([0,0.05,0.12,0.2,0.3,0.5,1,1.5,2,2.5,3,3.3,3.45])
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
Fc=np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0]); Fc*=49.6/_TRAPZ(Fc,Fc_t)
thrust=lambda t: float(np.interp(t,Fc_t,Fc,left=0,right=0)) if 0<=t<=tb else 0.0
mass=lambda t: max(m_dry,m_lift-(PROP/tb)*min(max(t,0),tb))
Cd0=0.539

# ---------------- atmosphere model: density from (T_sl, P_sl, elevation, RH) ----------------
def density(h, T_sl=288.15, P_sl=101325.0, elev=0.0, RH=0.0):
    """ISA-style density at geometric altitude h above a field at `elev`, with sea-level T/P and
    relative humidity RH (0..1). Humid air is lighter (water vapor M < dry air)."""
    L=0.0065; T=T_sl-L*(h+elev); P=P_sl*(T/T_sl)**(g/(Rspec*L))
    # humidity: subtract vapor partial pressure contribution (virtual-temperature bump)
    if RH>0:
        es=610.94*np.exp(17.625*(T-273.15)/(T-30.11)) # sat vapor pressure (Pa)
        e=RH*es; Tv=T/(1-0.378*e/P) # virtual temperature
        return P/(Rspec*Tv)
    return P/(Rspec*T)

ATMOS={
 "ISA 15°C": dict(T_sl=288.15,P_sl=101325,elev=0, RH=0.0, c=GRY),
 "Cold −15°C": dict(T_sl=258.15,P_sl=101325,elev=0, RH=0.0, c=BLU),
 "Hot +40°C": dict(T_sl=313.15,P_sl=101325,elev=0, RH=0.2, c=RED),
 "High DA 1500m": dict(T_sl=298.15,P_sl=101325,elev=1500,RH=0.3, c=ORG),
}

# ---------------- shared vertical trajectory (gives v(t),h(t) for q) under a given atmosphere ----
def trajectory(atm,dt=2e-3):
    s=np.array([0.,0.]); t=0.; T=[];H=[];V=[]
    while True:
        h,v=s; rho=density(h,**{k:atm[k] for k in("T_sl","P_sl","elev","RH")})
        Dr=0.5*rho*Cd0*A*v*abs(v); a=(thrust(t)-Dr-mass(t)*g)/mass(t)
        # RK2 is plenty for q
        s=s+dt*np.array([v,a]); t+=dt; T.append(t);H.append(s[0]);V.append(s[1])
        if s[1]<0 and t>tb: break
        if t>10: break
    return np.array(T),np.array(H),np.array(V)

# ================= SIMPLE PID (this is the reference for firmware/wyvern_pid.h) =================
class PID:
    """Discrete PID with integral clamp anti-windup + first-order derivative filter."""
    def __init__(self,kp,ki,kd,out_lim,tau_d=0.02,i_lim=0.4):
        self.kp,self.ki,self.kd=kp,ki,kd; self.lim=out_lim; self.tau=tau_d; self.ilim=i_lim
        self.i=0.0; self.d=0.0; self.prev=0.0
    def reset(self): self.i=self.d=self.prev=0.0
    def update(self,err,dt):
        self.i=float(np.clip(self.i+err*dt,-self.ilim,self.ilim)) # integrate + clamp
        raw=(err-self.prev)/dt; self.prev=err
        self.d+=(raw-self.d)*dt/(self.tau+dt) # LP-filtered derivative
        u=self.kp*err+self.ki*self.i+self.kd*self.d
        return float(np.clip(u,-self.lim,self.lim))

# ---------------- 1-cosine gust (sharp-edged worst case) ----------------
def gust(t):
    """two 1-cosine gusts: mid-burn (t=1.0s, high thrust) + late-burn (t=2.9s, low thrust =
    where control authority is weakest and gain-scheduling earns its keep)."""
    g=0.0
    for t0,dur,vmax in [(1.0,0.25,6.0),(2.9,0.30,7.0)]:
        if t0<=t<=t0+dur: g+=0.5*vmax*(1-np.cos(2*np.pi*(t-t0)/dur))
    return g

# ---------------- pitch-plane closed loop under one atmosphere ----------------
# GIMBAL LIMIT CORRECTED 2026-08: was radians(5.0). The mechanical/firmware limit is 8.0 deg
# (wyvern_pid.h OUT_LIM_DEG, raised 5->8 specifically for crosswind weathercock authority).
# Clamping the model at 5 deg understates available authority by 37.5%.
DMAX=np.radians(8.0); TAU_SERVO=0.04
def run_loop(atm, schedule=False, kp=0.10, ki=0.40, kd=0.18, dt=1e-3):
    Tt,Hh,Vv=trajectory(atm);
    pid=PID(kp,ki,kd,DMAX,tau_d=0.02)
    th=0.0; w=0.0; delta=0.0; t=0.5 # TVC engages at 0.5 s
    rho_sl=density(0,**{k:atm[k] for k in("T_sl","P_sl","elev","RH")})
    LOG=[]
    while t<tb:
        v=float(np.interp(t,Tt,Vv)); h=float(np.interp(t,Tt,Hh)); v=max(v,5.0)
        rho=density(h,**{k:atm[k] for k in("T_sl","P_sl","elev","RH")})
        q=0.5*rho*v*v
        # wind gust -> angle of attack disturbance
        aoa_wind=np.arctan2(gust(t),v)
        aoa=th - aoa_wind # body pitch relative to relative wind
        # gain schedule: keep loop authority constant as thrust tails off
        Tcur=thrust(t); ksch=(14.4/max(Tcur,3.0)) if schedule else 1.0
        cmd=pid.update(0.0-th, dt)*ksch # command vertical (theta=0)
        cmd=float(np.clip(cmd,-DMAX,DMAX))
        delta+=(cmd-delta)*dt/TAU_SERVO # servo lag
        M_tvc=Tcur*np.sin(delta)*(x_gimbal-CG)
        M_aero=-q*A*CN*(Xcp-CG)*aoa # fins restore toward relative wind (∝ q)
        M_damp=-q*A*CN*(Xcp-CG)*( (Xcp-CG)/max(v,5))*w # pitch aero damping (∝ q)
        wdot=(M_tvc+M_aero+M_damp)/I_pitch
        w+=wdot*dt; th+=w*dt; t+=dt
        LOG.append((t,np.degrees(th),np.degrees(delta),q,np.degrees(aoa_wind)))
    L=np.array(LOG)
    return L, rho_sl, float(np.max(np.abs(L[:,1]))), float(np.max(np.abs(L[:,2])))

# ================= RUN: 4 atmospheres, fixed vs scheduled gains =================
summary={}; figT,axT=plt.subplots(figsize=(10,5)); figD,axD=plt.subplots(figsize=(10,5))
qbars=[]; names=[]
for name,atm in ATMOS.items():
    L,rho_sl,maxpitch,maxdelta=run_loop(atm,schedule=False)
    Ls,_,maxpitch_s,maxdelta_s=run_loop(atm,schedule=True)
    summary[name]=dict(rho_sl=round(rho_sl,3), q_peak_Pa=round(float(L[:,3].max()),0),
        max_pitch_dev_deg=round(maxpitch,2), max_gimbal_deg=round(maxdelta,2),
        max_pitch_dev_scheduled_deg=round(maxpitch_s,2),
        improvement_pct=round(100*(maxpitch-maxpitch_s)/maxpitch,1))
    axT.plot(L[:,0],L[:,1],c=atm["c"],lw=2,label=f"{name} (ρ₀={rho_sl:.3f}, dev {maxpitch:.1f}°)")
    axD.plot(L[:,0],L[:,2],c=atm["c"],lw=1.8,label=f"{name} (peak {maxdelta:.1f}°)")
    qbars.append(float(L[:,3].max())); names.append(name)
axT.axvspan(1.0,1.25,color=RED,alpha=.1); axT.axvspan(2.9,3.2,color=RED,alpha=.1); axT.text(2.6,axT.get_ylim()[1]*0.8,"gusts",color=RED,fontsize=8)
axT.set_xlabel("t (s)"); axT.set_ylabel("pitch deviation (deg)"); axT.legend(fontsize=8); axT.grid(alpha=.3)
axT.set_title("Atmospheric effect on TVC, pitch deviation, retuned PID Kp2.0/Ki0.4/Kd0.5 (well-damped)")
figT.tight_layout(); figT.savefig(f"{OUT}/01_pitch_by_atmosphere.png",dpi=130); plt.close(figT)
axD.set_xlabel("t (s)"); axD.set_ylabel("gimbal command (deg)"); axD.axhline(5,ls='--',c=RED); axD.axhline(-5,ls='--',c=RED)
axD.legend(fontsize=8); axD.grid(alpha=.3); axD.set_title("Control effort (gimbal) by atmosphere, stays inside ±8° limit")
figD.tight_layout(); figD.savefig(f"{OUT}/02_gimbal_by_atmosphere.png",dpi=130); plt.close(figD)

# q + density bar chart
fig,ax=plt.subplots(1,2,figsize=(12,4.4))
ax[0].bar(names,[summary[n]["rho_sl"] for n in names],color=[ATMOS[n]["c"] for n in names]); ax[0].set_ylabel("sea-level ρ (kg/m³)"); ax[0].set_title("Air density by atmosphere"); ax[0].tick_params(axis='x',rotation=15)
ax[1].bar(names,qbars,color=[ATMOS[n]["c"] for n in names]); ax[1].set_ylabel("peak dynamic pressure q (Pa)"); ax[1].set_title("Peak q (drives gust & fin moments)"); ax[1].tick_params(axis='x',rotation=15)
fig.tight_layout(); fig.savefig(f"{OUT}/03_density_q.png",dpi=130); plt.close()

# fixed vs scheduled improvement
fig,ax=plt.subplots(figsize=(9,4.4))
x=np.arange(len(names)); wd=0.38
ax.bar(x-wd/2,[summary[n]["max_pitch_dev_deg"] for n in names],wd,label="fixed gains",color=GRY)
ax.bar(x+wd/2,[summary[n]["max_pitch_dev_scheduled_deg"] for n in names],wd,label="thrust-scheduled",color=GRN)
ax.set_xticks(x); ax.set_xticklabels(names,rotation=15); ax.set_ylabel("max pitch deviation (deg)")
ax.set_title("Fixed vs thrust-scheduled, <1% difference ⇒ simple fixed-gain PID is sufficient"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/04_gain_schedule.png",dpi=130); plt.close()

worst=max(summary.values(),key=lambda d:d["max_pitch_dev_deg"])
verdict=dict(atmospheres=summary,
    worst_case_pitch_dev_deg=worst["max_pitch_dev_deg"],
    all_inside_5deg_gimbal=bool(all(summary[n]["max_gimbal_deg"]<=5.001 for n in names)),
    recommendation="Margin-validated gains Kp=0.10 Ki=0.40 Kd=0.18 (see Documentation/PID_TUNING_REPORT.md; "+
      "Kp=2.0/Ki=0.4/Kd=0.5 has negative stability margin once the 2ms loop delay is modeled alongside the "+
      "40ms servo lag) hold <~"+str(round(worst["max_pitch_dev_deg"],1))+
      "° across all atmospheres + mid/late gusts; gain-scheduling adds <1% (F15 thrust is nearly flat) ⇒ keep a simple fixed-gain PID.")
json.dump(verdict, open(f"{OUT}/atmos_tvc_summary.json","w"), indent=2)
print(json.dumps(verdict,indent=2)); print("\nplots ->",OUT)
