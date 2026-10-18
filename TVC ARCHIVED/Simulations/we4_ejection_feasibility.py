import os, json, numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"plots_eject"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT,exist_ok=True)
BLU,RED,GRN,ORG,PUR="#2a6f97","#bc4749","#386641","#e09f3e","#6d597a"
g,rho0=9.80665,1.225; D=0.070; A=np.pi*(D/2)**2; m_lift,m_dry,PROP,tb=0.7203,0.6603,0.060,3.45; Cd0=0.539
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
mass=lambda t: max(m_dry,m_lift-(PROP/tb)*min(max(t,0),tb)); rho=lambda h: rho0*np.exp(-h/8500)
def traj(dt=1e-3):
    s=np.array([0.,0.]); t=0.; T=[];H=[];V=[]
    while True:
        def dz(st,tt):
            h,v=st; Dr=0.5*rho(h)*Cd0*A*v*abs(v); return np.array([v,(thrust(tt)-Dr-mass(tt)*g)/mass(tt)])
        k1=dz(s,t);k2=dz(s+.5*dt*k1,t+.5*dt);k3=dz(s+.5*dt*k2,t+.5*dt);k4=dz(s+dt*k3,t+dt)
        s=s+dt/6*(k1+2*k2+2*k3+k4); t+=dt; T.append(t);H.append(s[0]);V.append(s[1])
        if s[0]<0 and t>tb: break
        if t>14: break
    return np.array(T),np.array(H),np.array(V)
T,H,V=traj(); ap=int(np.argmax(H)); t_ap=float(T[ap]); h_ap=float(H[ap])
res={"apogee_m":round(h_ap,1),"apogee_t_s":round(t_ap,2),"burnout_s":tb}
delays={"F15-4":4.0,"F15-6":6.0,"F15-8":8.0}; timing={}
for name,d in delays.items():
    te=tb+d; ve=float(np.interp(te,T,V)) if te<=T[-1] else float(V[-1]); he=float(np.interp(te,T,H)) if te<=T[-1] else 0.0
    timing[name]=dict(t_eject_s=round(te,2),dt_vs_apogee_s=round(te-t_ap,2),v_at_eject_ms=round(ve,1),h_at_eject_m=round(he,1),
        verdict=("near-optimal" if abs(te-t_ap)<=1.0 else ("late/hard" if te-t_ap>0 else "early")))
opt=t_ap-tb; res["optimal_delay_s"]=round(opt,2); res["timing"]=timing; res["recommend"]=min(delays,key=lambda n:abs(delays[n]-opt))
fig,ax=plt.subplots(figsize=(10,5)); ax.plot(T,H,c=BLU,lw=2,label="altitude"); ax.axvline(tb,ls=':',c='gray'); ax.text(tb+.05,5,"burnout",fontsize=8)
ax.plot(t_ap,h_ap,'ko'); ax.annotate(f"apogee {h_ap:.0f}m @ {t_ap:.1f}s",(t_ap,h_ap),textcoords="offset points",xytext=(6,6),fontsize=8)
cols={"F15-4":GRN,"F15-6":RED,"F15-8":PUR}
for name,d in delays.items():
    te=tb+d; ax.axvline(te,ls='--',c=cols[name]); ax.text(te,h_ap*0.5,f"{name}\n{te:.1f}s\n{timing[name]['v_at_eject_ms']:+.0f}m/s",color=cols[name],fontsize=7,ha="center")
ax.set_xlabel("t (s)"); ax.set_ylabel("altitude (m)"); ax.grid(alpha=.3); ax.legend()
ax.set_title(f"Deploy timing - optimal {opt:.1f}s (->{res['recommend']}); F15-6 ejects {timing['F15-6']['dt_vs_apogee_s']:+.1f}s past apogee")
fig.tight_layout(); fig.savefig(f"{OUT}/A_deploy_timing.png",dpi=130); plt.close()
# bay pressurization + loads (compact). Recovery is a bulkhead joint exposed to ejection gas
# directly -- there is no discrete flow-restriction tube in the current architecture, so the
# duct-loss curve below is a legacy proxy for flow-path pressure drop, not a real geometric
# feature. Left in place as a conservative loss estimate pending a re-derivation against the
# bulkhead's actual wiring pass-through holes (see Documentation/WYVERN_E4_Recovery.md §6).
L=0.16; rho_g=0.35; Vb=np.pi*0.033**2*0.10; Qd=Vb/0.10; ids=np.linspace(.006,.020,29)
dP=np.array([0.03*(L/d)*0.5*rho_g*(Qd/(np.pi*(d/2)**2))**2 for d in ids])/1000.0
dp12=float(np.interp(0.012,ids,dP)); res["flow_path_loss"]=dict(dP_12mm_kPa=round(dp12,2),proxy_id_mm=12,**{"pass":bool(dp12<10)})
pdel=140.0-dp12; res["bay_pressure"]=dict(delivered_kPa=round(pdel,1),release_kPa=[14,41],margin_x=round(pdel/41,1),**{"pass":bool(pdel>41*1.5)})
Ac=np.pi*(0.457/2)**2; loads={n:dict(v=abs(timing[n]["v_at_eject_ms"]),F=round(0.5*rho0*abs(timing[n]["v_at_eject_ms"])**2*1.5*Ac*1.8)) for n in delays}
res["opening_loads"]=loads
fig,ax=plt.subplots(1,2,figsize=(12,4.2))
ax[0].plot(ids*1000,dP,c=ORG,lw=2); ax[0].axvline(12,ls='--',c=GRN); ax[0].axhline(10,ls=':',c=RED); ax[0].set_xlabel("proxy flow-path ID (mm)"); ax[0].set_ylabel("pulse dP (kPa)"); ax[0].set_title(f"Flow-path loss proxy: 12mm->{dp12:.1f} kPa"); ax[0].grid(alpha=.3)
ax[1].bar(["delivered","release max"],[pdel,41],color=[BLU,GRN]); ax[1].set_ylabel("dP (kPa)"); ax[1].set_title(f"Bay: {pdel:.0f} kPa vs 41 ({res['bay_pressure']['margin_x']:.1f}x)"); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/B_tube_bay.png",dpi=130); plt.close()
res["verdict"]=f"FEASIBLE. F15-6 ejects {timing['F15-6']['dt_vs_apogee_s']:+.1f}s past apogee at {abs(timing['F15-6']['v_at_eject_ms']):.0f} m/s (hard/late). Optimal delay {opt:.1f}s -> {res['recommend']}."
json.dump(res,open(f"{OUT}/ejection_feasibility.json","w"),indent=2)
print(json.dumps(res,indent=2))
