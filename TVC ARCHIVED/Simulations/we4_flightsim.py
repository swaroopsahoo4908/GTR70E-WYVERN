#!/usr/bin/env python3
"""GTR70E WYVERN, unified RK4 + Barrowman flight engine (single-stage F15-4, FINNED TVC, fly-light).
RK4 (4th-order) integration of [altitude, velocity] with Barrowman drag buildup and CP/CN reporting."""
import os,json,numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"plots4"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT,exist_ok=True)
g=9.80665; rho0=1.225; D=0.070; Rb=D/2; A=np.pi*Rb**2; Lnose=0.12; Ltot=0.672
m_lift=0.7203; m_dry=0.6603; PROP=0.060; tb=3.45; CG=0.4500 # finned 87mm, zoned ASA-Aero (upper+lower)/PETG-CF (fins+bulkhead)/PC-FR (TVC), NO ballast
# --- Barrowman aero (nose + 4x 87 mm fin span, PETG-CF, sized to hold margin against the zoned mass stack) ---
def barrowman_cp():
    CNn=2.0; Xn=0.333*Lnose; cr,ct,sw,sp=0.070,0.035,0.025,0.087; Rb_=0.035 # ellipsoid nose, 87mm fins
    Lf=np.sqrt(sp**2+(sw+(ct-cr)/2)**2); k=1+Rb_/(sp+Rb_)
    CNf=k*(4*4*(sp/D)**2)/(1+np.sqrt(1+(2*Lf/(cr+ct))**2)); xr=Ltot-cr
    Xf=xr+(sw/3)*(cr+2*ct)/(cr+ct)+(1/6)*((cr+ct)-cr*ct/(cr+ct))
    return (CNn*Xn+CNf*Xf)/(CNn+CNf), CNn+CNf # FINNED: CP aft -> +1.5 cal (stable; TVC after t=0.5s)
Xcp,CN=barrowman_cp(); margin=(Xcp-CG)/D # negative -> unstable -> active TVC
# --- Barrowman-style Cd buildup ---
def Cd(M):
    Cf=0.0040 # turbulent skin-friction coeff (low Re)
    Swet=np.pi*D*Ltot; Cd_fric=Cf*Swet/A # friction
    Cd_base=0.12; Cd_press=0.10; Cd_fins=0.150 # + 4x 72mm fins (ellipsoid nose)
    return Cd_fric+Cd_base+Cd_press+Cd_fins
# --- F15-4 thrust curve (49.6 Ns / 3.45 s) ---
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
tc=np.array([0,0.05,0.12,0.2,0.3,0.5,1,1.5,2,2.5,3,3.3,3.45]);Fc=np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0]);Fc*=49.6/_TRAPZ(Fc,tc)
thrust=lambda t: float(np.interp(t,tc,Fc,left=0,right=0)) if 0<=t<=tb else 0.0
mass=lambda t: max(m_dry, m_lift-(PROP/tb)*min(max(t,0),tb))
rho=lambda h: rho0*np.exp(-h/8500)
# --- RK4 integrator: state=[h,v] ---
def deriv(s,t):
    h,v=s; m=mass(t); Md=thrust(t); Dr=0.5*rho(h)*Cd(v/343)*A*v*abs(v)
    return np.array([v,(Md-Dr-m*g)/m])
# Recovery is the F15-4 motor ejection charge, fired 4 s AFTER BURNOUT -> t = 3.45 + 4.0 = 7.45 s.
# This file previously stopped integrating at apogee and sampled "deploy" at t=4.0 s, i.e. 0.55 s
# after burnout -- the retired finless-era electronic-timer deploy. That reported a 29 m/s deploy
# velocity against the Recovery doc's ~6.5 m/s: same vehicle, two different recovery architectures.
T_DEPLOY=tb+4.0
# integration step tightened 1e-3 -> 2e-4 in the 2026-08 fidelity pass
dt=2e-4; t=0.0; s=np.array([0.0,0.0]); T=[];H=[];V=[];Acc=[]
while True:
    k1=deriv(s,t);k2=deriv(s+0.5*dt*k1,t+0.5*dt);k3=deriv(s+0.5*dt*k2,t+0.5*dt);k4=deriv(s+dt*k3,t+dt)
    s=s+dt/6*(k1+2*k2+2*k3+k4); t+=dt; T.append(t);H.append(s[0]);V.append(s[1]);Acc.append(k1[1]/g)
    if s[0]<0 and t>tb: break # back on the ground
    if t>=T_DEPLOY: break # integrate THROUGH apogee to the ejection event
T,H,V,Acc=map(np.array,(T,H,V,Acc))
bo=np.argmin(np.abs(T-tb)); ap=np.argmax(H); dep=np.argmin(np.abs(T-T_DEPLOY))
res=dict(engine="RK4(2e-4) + Barrowman drag buildup", Cd_nominal=round(float(Cd(0.05)),3), dt_s=2e-4,
 cp_from_nose_cm=round(Xcp*100,1), CN_total=CN, static_margin_cal=round(margin,2),
 note="Ellipsoid nose, FINNED 87mm, no ballast: passively stable (+1.0 cal) for launch + first 0.5s spike; TVC engages at t=0.5s on the smooth curve",
 burnout_t=tb, burnout_alt_m=round(H[bo],1), burnout_v=round(V[bo],1),
 apogee_m=round(H[ap],1), apogee_ft=round(H[ap]*3.281,0), apogee_t=round(T[ap],2),
 max_accel_g=round(float(np.max(Acc)),2), deploy_t=round(T_DEPLOY,2), deploy_alt_m=round(H[dep],1), deploy_v=round(V[dep],1),
 deploy_past_apogee_s=round(float(T_DEPLOY-T[ap]),2))
json.dump(res,open(f"{OUT}/flightsim_summary.json","w"),indent=1)
fig,ax=plt.subplots(figsize=(9,5)); ax.plot(T,H,c="#2a6f97",label="altitude (m)"); ax.set_xlabel("t (s)"); ax.set_ylabel("altitude (m)",color="#2a6f97")
a2=ax.twinx(); a2.plot(T,V,c="#bc4749"); a2.set_ylabel("velocity (m/s)",color="#bc4749")
ax.axvline(tb,ls=':',c='g'); ax.axvline(T_DEPLOY,ls='--',c='k'); ax.text(tb+.05,5,"burnout"); ax.text(T_DEPLOY+.05,H[ap]*0.5,f"motor eject {T_DEPLOY:.2f} s")
ax.set_title(f"GTR70E WYVERN · RK4+Barrowman · apogee {res['apogee_ft']:.0f} ft @ {res['apogee_t']} s · deploy {res['deploy_v']} m/s",fontweight='bold'); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/01_trajectory.png",dpi=130); plt.close()
print(json.dumps(res,indent=1))
