#!/usr/bin/env python3
"""WYVERN-E 3.0 analysis suite -- two-stage F32 + G25W, off-the-shelf Pi-5 vehicle.
Outputs -> Simulations/plots3/ : flight path, stability, TVC A/B comparison,
power budget, Monte-Carlo dispersion. Pure numpy/matplotlib."""
import os, json, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"plots3"); os.makedirs(OUT,exist_ok=True)
g=9.81; rho0=1.225; D=0.084; A=np.pi*(D/2)**2; Cd=0.90; a_snd=340.0
def rho(h): return rho0*np.exp(-h/8500)
# config
BOOST=dict(F=32,tb=1.0,prop=16,load=70); SUS=dict(F=25,tb=4.7,prop=62,load=124)
m_sus_dry=915.0   # sustainer (solenoid) all-up minus G25W
m_sus=m_sus_dry+SUS['load']; m0=m_sus+180+BOOST['load']
def fly(Cd=Cd, full=False, dt=1e-3, stage_coast=0.4):
    def burn(F,tb,prop,m_wet,v,h,T,H,V):
        md=prop/1000/tb; m=m_wet/1000; t=0
        while t<tb:
            dr=0.5*rho(h)*Cd*A*v*abs(v); a=(F-dr-m*g)/m; v+=a*dt;h+=v*dt;m-=md*dt;t+=dt
            T.append(T[-1]+dt if T else dt);H.append(h);V.append(v)
        return v,h
    T=[];H=[];V=[]
    v,h=burn(BOOST['F'],BOOST['tb'],BOOST['prop'],m0,0,0,T,H,V); hb=h
    m=(m0-BOOST['prop'])/1000
    for _ in range(int(stage_coast/dt)):
        dr=0.5*rho(h)*Cd*A*v*abs(v); a=(-dr-m*g)/m; v+=a*dt;h+=v*dt; T.append(T[-1]+dt);H.append(h);V.append(v)
    hs=h
    v,h=burn(SUS['F'],SUS['tb'],SUS['prop'],m_sus,v,h,T,H,V)
    m=(m_sus-SUS['prop'])/1000
    while v>0:
        dr=0.5*rho(h)*Cd*A*v*abs(v); a=(-dr-m*g)/m; v+=a*dt;h+=v*dt; T.append(T[-1]+dt);H.append(h);V.append(v)
    if full: return np.array(T),np.array(H),np.array(V),hb,hs
    return h

# 01 flight path
T,H,V,hb,hs=fly(full=True)
fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.6))
a1.plot(T,H*3.281,lw=2,c="#2a6f97"); a1.axhline(hs*3.281,ls=':',c='g'); a1.text(T[-1]*0.55,hs*3.281+20,f"staging {hs*3.281:.0f} ft",color='g',fontsize=9)
a1.set_xlabel("t (s)"); a1.set_ylabel("altitude (ft)"); a1.set_title(f"Two-stage trajectory — apogee {H.max()*3.281:.0f} ft"); a1.grid(alpha=.3)
a2.plot(T,V,lw=2,c="#d00000"); a2.set_xlabel("t (s)"); a2.set_ylabel("velocity (m/s)"); a2.set_title(f"Velocity (F32 → 4.7 s G25W TVC burn; Vmax {V.max():.0f} m/s)"); a2.grid(alpha=.3)
fig.suptitle("WYVERN-E 3.0 · Flight Path (no-waiver two-stage)",fontweight='bold'); fig.tight_layout(); fig.savefig(f"{OUT}/01_flight_path.png",dpi=130); plt.close(fig)

# 02 stability
L=0.95; cp=0.70*L; t=np.linspace(0,BOOST['tb']+SUS['tb']+2,120)
burnf=np.clip((BOOST['tb']+0.4+SUS['tb']-t)/(BOOST['tb']+SUS['tb']),0,1); cg=(0.50+0.03*burnf)*L
margin=(cp-cg)/D
fig,ax=plt.subplots(figsize=(8.5,4.8)); ax.plot(t,margin,lw=2,c="#386641"); ax.axhspan(1.0,2.0,color="#a7c957",alpha=.3,label="1.0–2.0 cal")
ax.set_xlabel("flight time (s)"); ax.set_ylabel("static margin (cal)"); ax.legend()
ax.set_title(f"WYVERN-E 3.0 · Static Margin (oversized fins, {margin.min():.1f}–{margin.max():.1f} cal)",fontweight='bold'); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/02_stability.png",dpi=130); plt.close(fig)

# 03 TVC A/B comparison
metrics=["Mass (g)","Peak power (W)","Bandwidth (rel)","Smoothness (rel)","Backlash (rel,↓)"]
sol=[120,33,9,4,1]; svo=[220,22,5,9,5]
x=np.arange(len(metrics)); fig,ax=plt.subplots(figsize=(10,4.8))
ax.bar(x-0.2,sol,0.4,label="A — solenoid",color="#bc4749"); ax.bar(x+0.2,svo,0.4,label="B — servo",color="#2a6f97")
ax.set_xticks(x); ax.set_xticklabels(metrics,fontsize=9); ax.legend(); ax.set_title("WYVERN-E 3.0 · TVC A/B (solenoid vs servo)",fontweight='bold'); ax.grid(alpha=.3,axis='y')
fig.tight_layout(); fig.savefig(f"{OUT}/03_tvc_comparison.png",dpi=130); plt.close(fig)

# 04 power/energy
labels=["Pi 5","µSD ×2","sensors","RRC3+/elec","TVC (burst)"]; idle=[3.5,0.1,0.18,0.42,0]; active=[6.5,0.7,0.2,0.65,33]
x=np.arange(len(labels)); fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.4))
a1.bar(x-0.2,idle,0.4,label="idle",color="#888"); a1.bar(x+0.2,active,0.4,label="active",color="#2a6f97")
a1.set_xticks(x); a1.set_xticklabels(labels,fontsize=8,rotation=15); a1.set_ylabel("W"); a1.legend(); a1.set_title("Power by subsystem"); a1.grid(alpha=.3,axis='y')
flights=np.arange(0,6); Wh=10.6+np.cumsum(np.full(6,8.3*10/60)); cap=33.3
a2.plot(flights,Wh,'o-',c="#386641"); a2.axhline(cap,ls='--',c='r'); a2.text(0.1,cap-3,"3S 3000 mAh = 33 Wh",color='r',fontsize=9)
a2.set_xlabel("flights (after 2.5 h idle)"); a2.set_ylabel("cumulative Wh"); a2.set_title("Energy vs battery (1.9× margin)"); a2.grid(alpha=.3)
fig.suptitle("WYVERN-E 3.0 · Power Budget",fontweight='bold'); fig.tight_layout(); fig.savefig(f"{OUT}/04_power_budget.png",dpi=130); plt.close(fig)

# 05 dispersion
rng=np.random.default_rng(3); xs=[];ys=[];apos=[]
for _ in range(300):
    cd=Cd*(1+rng.normal(0,0.08)); apo=fly(Cd=cd,dt=2e-3)
    wind=abs(rng.normal(2.5,1.2)); wd=rng.uniform(0,2*np.pi); drift=wind*(apo/6.5)*0.9
    xs.append(drift*np.cos(wd));ys.append(drift*np.sin(wd));apos.append(apo*3.281)
xs=np.array(xs);ys=np.array(ys);r=np.hypot(xs,ys);cep=np.percentile(r,50)
fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.8)); a1.scatter(xs,ys,s=10,alpha=.5,c="#2a6f97")
th=np.linspace(0,2*np.pi,100)
for rr,c,l in [(cep,'g','CEP'),(np.percentile(r,95),'r','95%')]: a1.plot(rr*np.cos(th),rr*np.sin(th),c=c,lw=1.5,label=f"{l} {rr:.0f} m")
a1.set_aspect('equal');a1.set_xlabel("downwind (m)");a1.set_ylabel("crosswind (m)");a1.legend();a1.set_title("Landing dispersion");a1.grid(alpha=.3)
a2.hist(apos,25,color="#386641",alpha=.8);a2.axvline(np.mean(apos),c='k',ls='--');a2.set_xlabel("apogee (ft)");a2.set_ylabel("count");a2.set_title(f"Apogee {np.mean(apos):.0f} ± {np.std(apos):.0f} ft");a2.grid(alpha=.3)
fig.suptitle("WYVERN-E 3.0 · Monte-Carlo Dispersion",fontweight='bold'); fig.tight_layout(); fig.savefig(f"{OUT}/05_dispersion.png",dpi=130); plt.close(fig)

summary=dict(apogee_ft=round(float(H.max()*3.281)),staging_ft=round(float(hs*3.281)),vmax_ms=round(float(V.max()),1),
             liftoff_g=round(m0),tvc_burn_s=SUS['tb'],margin_cal=[round(float(margin.min()),1),round(float(margin.max()),1)])
json.dump(summary,open(f"{OUT}/results_summary.json","w"),indent=2); print(json.dumps(summary,indent=2))
