#!/usr/bin/env python3
"""GTR70E WYVERN, extra analysis plots: deploy-vs-timer, dynamic pressure / Reynolds, in-flight
static margin (CG shift during burn), TVC step response -> plots4/ (17-20)."""
import os,json,numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"plots4"+os.environ.get("WYVERN_RUN_TAG",""))
g=9.80665;rho0=1.225;D=0.070;A=np.pi*(D/2)**2;m_lift=0.7203;m_dry=0.6603;tb=3.45  # canonical mass
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
tc=np.array([0,0.05,0.12,0.2,0.3,0.5,1,1.5,2,2.5,3,3.3,3.45]);Fc=np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0]);Fc*=49.6/_TRAPZ(Fc,tc)
thr=lambda t: float(np.interp(t,tc,Fc,left=0,right=0)) if 0<=t<=tb else 0.0
def fly():
    dt=2e-3;h=0;v=0;t=0;T=[];H=[];V=[];Q=[]
    while True:
        F=thr(t);m=max(m_dry,m_lift-(0.060/tb)*min(t,tb));rho=rho0*np.exp(-h/8500)
        Dr=0.5*rho*0.54*A*v*abs(v);v+=(F-Dr-m*g)/m*dt;h+=v*dt;t+=dt
        T.append(t);H.append(h);V.append(v);Q.append(0.5*rho*v*v)
        if v<0 and t>tb: break
        if t>14: break
    return map(np.array,(T,H,V,Q))
T,H,V,Qd=fly()
def sv(fig,n): fig.tight_layout();fig.savefig(f"{OUT}/{n}.png",dpi=130);plt.close(fig)
# 17 deploy velocity vs timer
fig,ax=plt.subplots(figsize=(8.5,5)); tt=np.linspace(3.5,7.0,40); vv=np.interp(tt,T,V)
ax.plot(tt,vv,c="#2a6f97",lw=2); ax.axvline(4.0,ls='--',c='k',label="chosen 4.0 s → %.0f m/s"%np.interp(4.0,T,V))
ax.axhline(15,ls=':',c='g',label="gentle ≤15 m/s"); ax.axvspan(tb,4.0,color='r',alpha=.06)
ax.set_xlabel("motor ejection delay after burnout (s)"); ax.set_ylabel("velocity at deploy (m/s)"); ax.legend()
ax.set_title("GTR70E WYVERN · deploy velocity vs timer (earlier=faster but less tumble)",fontweight='bold'); ax.grid(alpha=.3); sv(fig,"17_deploy_vs_timer")
# 18 dynamic pressure + Reynolds
fig,ax=plt.subplots(figsize=(8.5,5)); ax.plot(T,Qd,c="#bc4749",lw=2,label="dynamic pressure q (Pa)")
ax.set_xlabel("t (s)"); ax.set_ylabel("q (Pa)",color="#bc4749"); a2=ax.twinx()
Re=rho0*V*D/1.81e-5; a2.plot(T,Re/1e5,c="#386641",label="Reynolds /1e5"); a2.set_ylabel("Re (×10⁵)",color="#386641")
ax.axvline(tb,ls=':',c='g'); ax.set_title("GTR70E WYVERN · dynamic pressure & Reynolds number",fontweight='bold'); ax.grid(alpha=.3); sv(fig,"18_q_reynolds")
# 19 in-flight static margin (CG moves aft as propellant burns)
tt=np.linspace(0,tb,60); CGb=0.4350-0.0 # finned no-ballast; prop is aft so CG moves slightly aft during burn
CG=0.4500-0.015*np.clip(tt/tb,0,1) # 45.0 -> 43.5 cm: CG moves FORWARD as propellant burns
CP=0.5327; marg=(CP-CG)/D
fig,ax=plt.subplots(figsize=(8.5,5)); ax.plot(tt,marg,c="#2a6f97",lw=2); ax.axhline(1.0,ls=':',c='g',label="1.0 cal min")
ax.axvline(0.5,ls='--',c='orange',label="TVC engages 0.5 s"); ax.set_xlabel("burn time (s)"); ax.set_ylabel("static margin (cal)"); ax.legend()
ax.set_title("GTR70E WYVERN · in-flight static margin (passive cover until TVC at 0.5 s)",fontweight='bold'); ax.grid(alpha=.3); sv(fig,"19_margin_inflight")
# 20 TVC step response (2nd order)
t=np.linspace(0,0.6,300); wn=18;z=0.65;wd=wn*np.sqrt(1-z*z)
resp=1-np.exp(-z*wn*t)*(np.cos(wd*t)+z/np.sqrt(1-z*z)*np.sin(wd*t))
fig,ax=plt.subplots(figsize=(8.5,5)); ax.plot(t,resp*4,c="#bc4749",lw=2,label="pitch response to 4° cmd")
ax.axhline(4,ls=':',c='k'); ax.axhline(4*1.05,ls=':',c='g',lw=.6); ax.axhline(4*0.95,ls=':',c='g',lw=.6)
st=t[np.argmax(np.abs(resp-1)<0.05)] if np.any(np.abs(resp-1)<0.05) else 0
ax.set_xlabel("t (s)"); ax.set_ylabel("pitch (deg)"); ax.legend(); ax.set_title(f"GTR70E WYVERN · TVC step response (settle ~{st*1000:.0f} ms, ζ=0.65)",fontweight='bold'); ax.grid(alpha=.3); sv(fig,"20_step_response")
print("extra plots: 17_deploy_vs_timer, 18_q_reynolds, 19_margin_inflight, 20_step_response")
