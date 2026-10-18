#!/usr/bin/env python3
"""WYVERN-E 3.0 — TVC control & design-sweep analyses -> plots3/.
Adds: fin-size/Cd apogee sweep, TVC control authority vs aero disturbance over the burn,
and a solenoid-vs-servo closed-loop step-response comparison."""
import os, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"plots3"); os.makedirs(OUT,exist_ok=True)
g=9.81; rho0=1.225; D=0.084; A=np.pi*(D/2)**2; a_snd=340.0
def rho(h): return rho0*np.exp(-h/8500)
BOOST=dict(F=32,tb=1.0,prop=16); SUS=dict(F=25,tb=4.7,prop=62)
m_sus=915.0+124; m0=m_sus+250
def apogee(Cd,dt=1e-3):
    def burn(F,tb,prop,m_wet,v,h):
        md=prop/1000/tb; m=m_wet/1000; t=0
        while t<tb:
            dr=0.5*rho(h)*Cd*A*v*abs(v); v+=(F-dr-m*g)/m*dt; h+=v*dt; m-=md*dt; t+=dt
        return v,h
    v,h=burn(BOOST['F'],BOOST['tb'],BOOST['prop'],m0,0,0); m=(m0-BOOST['prop'])/1000
    for _ in range(400): dr=0.5*rho(h)*Cd*A*v*abs(v); v+=(-dr-m*g)/m*dt; h+=v*dt
    v,h=burn(SUS['F'],SUS['tb'],SUS['prop'],m_sus,v,h); m=(m_sus-SUS['prop'])/1000
    while v>0: dr=0.5*rho(h)*Cd*A*v*abs(v); v+=(-dr-m*g)/m*dt; h+=v*dt
    return h*3.281

# 06 fin-size / Cd -> apogee sweep (design rationale for oversized fins)
Cds=np.linspace(0.45,1.1,14); apos=[apogee(c) for c in Cds]
fig,ax=plt.subplots(figsize=(8.5,5)); ax.plot(Cds,apos,'o-',c="#2a6f97")
ax.axhline(1000,ls='--',c='r'); ax.axhline(1100,ls=':',c='r'); ax.axvspan(0.85,0.95,color="#a7c957",alpha=.3,label="chosen fins (Cd≈0.9)")
ax.text(0.46,1020,"1000 ft cap",color='r',fontsize=9)
ax.set_xlabel("vehicle Cd (fin size →)"); ax.set_ylabel("apogee (ft)"); ax.legend()
ax.set_title("WYVERN-E 3.0 · Oversized fins set the apogee (G25W burn fixed)",fontweight='bold'); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/06_fin_apogee_sweep.png",dpi=130); plt.close(fig)

# 07 TVC control authority vs aero disturbance over sustainer burn
t=np.linspace(0,SUS['tb'],100); v=30+ (58-30)*t/SUS['tb']  # approx airspeed during sustain
q=0.5*rho(300)*v**2                       # dynamic pressure
F=SUS['F']
tau_tvc=F*0.045*np.sin(np.radians(5))*np.ones_like(t)   # gimbal restoring moment @5deg
Cn_a=2.0; Sref=A; d_cp_cg=0.12
tau_dist=q*Sref*Cn_a*np.radians(2)*d_cp_cg              # 2deg AoA disturbance
fig,ax=plt.subplots(figsize=(9,5))
ax.plot(t,tau_tvc*1000,lw=2,c="#386641",label="TVC restoring moment @±5°")
ax.plot(t,tau_dist*1000,lw=2,c="#bc4749",label="aero disturbance @2° AoA")
ax.fill_between(t,tau_tvc*1000,tau_dist*1000,where=(tau_tvc>=tau_dist),color="#a7c957",alpha=.3,label="control margin")
ax.set_xlabel("sustainer burn time (s)"); ax.set_ylabel("moment (mN·m)"); ax.legend()
ax.set_title("WYVERN-E 3.0 · TVC Control Authority vs Disturbance",fontweight='bold'); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/07_control_authority.png",dpi=130); plt.close(fig)

# 08 closed-loop step response: solenoid bang-bang vs servo proportional (illustrative 2nd-order)
T=np.linspace(0,1.0,400)
# servo: 2nd order, wn=18 rad/s, zeta=0.6
wn,z=18,0.6; wd=wn*np.sqrt(1-z**2)
servo=1-np.exp(-z*wn*T)*(np.cos(wd*T)+z/np.sqrt(1-z**2)*np.sin(wd*T))
# solenoid: faster but limit-cycle ripple around setpoint
sol=1-np.exp(-32*T); sol+=0.04*np.sin(2*np.pi*25*T)*np.exp(-3*T)
fig,ax=plt.subplots(figsize=(9,5))
ax.plot(T,sol,lw=2,c="#bc4749",label="solenoid (fast, limit-cycle ripple)")
ax.plot(T,servo,lw=2,c="#2a6f97",label="servo (smooth, slower, slight overshoot)")
ax.axhline(1,ls=':',c='k'); ax.set_xlabel("time (s)"); ax.set_ylabel("normalized gimbal angle"); ax.legend()
ax.set_title("WYVERN-E 3.0 · TVC Step Response (illustrative model)",fontweight='bold'); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/08_tvc_step_response.png",dpi=130); plt.close(fig)
print("control min margin (mN·m):",round(float((tau_tvc-tau_dist).min()*1000),2))
print("wrote 06_fin_apogee_sweep, 07_control_authority, 08_tvc_step_response")
