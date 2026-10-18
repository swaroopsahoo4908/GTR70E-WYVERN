#!/usr/bin/env python3
"""GTR70E WYVERN, MOTOR TRADE STUDY
================================================================================
Question: is the F15-4 the right motor choice, or does a higher-thrust single-stage motor or a
two-stage configuration do better against the <1000 ft no-waiver ceiling and the TVC window?

This script recomputes, with the same RK4 + Barrowman engine as we4_flightsim/we4_validation, 
the apogee, rail-exit velocity, peak T/W, TVC window, max-Q and Mach for:

  baseline F15-4 (24 mm) 49.6 N·s curve as-flown
  single G74W (29 mm) 82.8 N·s White Lightning, 1.1 s
  single G80T (29 mm) 135.6 N·s Blue Thunder, 1.7 s
  single G64W (29 mm) 118.8 N·s White Lightning, 2.1 s <-- best off-line thrust + long burn
  two-stage G80T booster -> F15-4 sustainer (+150 g ASA booster + bigger fins)

Motor specs are from ThrustCurve.org / manufacturer certs (see comments). Curve SHAPES are
representative normalized profiles rescaled to each motor's certified total impulse + burn time.
Run: python3 we4_motor_tradestudy.py -> plots_motor/*.png + motor_tradestudy.json
"""
import os, json, numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"plots_motor"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT,exist_ok=True)
BLU,RED,GRN,ORG,PUR,GRY="#2a6f97","#bc4749","#386641","#e09f3e","#6d597a","#8d99ae"

# ---------------- airframe (shared) ----------------
g,rho0=9.80665,1.225; D=0.070; Rb=D/2; A=np.pi*Rb**2; Ltot=0.74; a_snd=343.0
M_AIRFRAME=0.603 # dry airframe WITHOUT motor (705 g liftoff - 102 g F15 = 603 g)
def Cd(M): return (0.0040*np.pi*D*Ltot/A + 0.12+0.10+0.150)*(1+0.25*max(M-0.8,0))

# ---------------- motors: (Itot Ns, m_loaded kg, m_prop kg, tb s, [(t_frac,thrust_N)... shape]) ----------------
# specs: F15 Estes; G74W/G80T/G64W AeroTech (ThrustCurve.org certs)
MOTORS={
 "F15-4": dict(I=49.6, m=0.102, mp=0.060, tb=3.45, dia=24, prop="BP",
   shape=[(0,0),(0.014,12),(0.035,25.3),(0.06,22),(0.09,16),(0.14,13),(0.29,12.5),(0.43,12.2),(0.58,12),(0.72,11.8),(0.87,11.5),(0.96,7),(1.0,0)]),
 "G74W": dict(I=82.8, m=0.087, mp=0.040, tb=1.10, dia=29, prop="White Lightning",
   shape=[(0,75),(0.05,95),(0.10,90),(0.30,80),(0.55,70),(0.80,58),(0.95,30),(1.0,0)]),
 "G80T": dict(I=135.6,m=0.108, mp=0.062, tb=1.70, dia=29, prop="Blue Thunder",
   shape=[(0,40),(0.06,115),(0.18,108),(0.45,92),(0.70,84),(0.88,72),(0.96,45),(1.0,0)]),
 "G64W": dict(I=118.8,m=0.151, mp=0.063, tb=2.10, dia=29, prop="White Lightning",
   shape=[(0,96),(0.05,98.3),(0.18,80),(0.40,66),(0.65,58),(0.85,50),(0.93,34),(1.0,0)]),
 "F67W": dict(I=61.1, m=0.081, mp=0.030, tb=0.90, dia=29, prop="White Lightning",
   shape=[(0,83),(0.05,86),(0.20,75),(0.50,64),(0.80,45),(0.95,20),(1.0,0)]),
}
def curve(spec):
    """return thrust(t) callable scaled so integral == certified total impulse."""
    tb=spec["tb"]; pts=np.array(spec["shape"]); ts=pts[:,0]*tb; Fs=pts[:,1]
    scale=spec["I"]/_TRAPZ(Fs,ts); Fs=Fs*scale
    return (lambda t: float(np.interp(t,ts,Fs,left=0,right=0)) if 0<=t<=tb else 0.0), float(Fs.max()), float(Fs[0] if Fs[0]>0 else Fs[1])

def fly(thrust,m_load,m_prop,tb,dt=1e-3):
    m0=M_AIRFRAME+m_load; mdry=m0-m_prop
    ms=lambda t: max(mdry, m0-(m_prop/tb)*min(max(t,0),tb))
    def dz(s,t):
        h,v=s; Dr=0.5*rho0*np.exp(-h/8500)*Cd(abs(v)/a_snd)*A*v*abs(v)
        return np.array([v,(thrust(t)-Dr-ms(t)*g)/ms(t)])
    s=np.array([0.,0.]); t=0.; T=[];H=[];V=[]
    while True:
        k1=dz(s,t);k2=dz(s+.5*dt*k1,t+.5*dt);k3=dz(s+.5*dt*k2,t+.5*dt);k4=dz(s+dt*k3,t+dt)
        s=s+dt/6*(k1+2*k2+2*k3+k4); t+=dt; T.append(t);H.append(s[0]);V.append(s[1])
        if s[1]<0 and t>tb: break
        if t>30: break
    return np.array(T),np.array(H),np.array(V),m0,mdry

def rail_exit(thrust,m_load,m_prop,tb,L=1.0):
    m0=M_AIRFRAME+m_load; ms=lambda t: max(m0-m_prop, m0-(m_prop/tb)*min(max(t,0),tb))
    x=0.;v=0.;t=0.;dt=1e-4
    while x<L and t<tb:
        a=(thrust(t)-0.5*rho0*Cd(v/a_snd)*A*v*v-ms(t)*g)/ms(t); v+=a*dt; x+=v*dt; t+=dt
    return v

# ---------------- single-stage evaluation ----------------
rows={}; traj={}
for name,spec in MOTORS.items():
    th,pk,init=curve(spec)
    T,H,V,m0,mdry=fly(th,spec["m"],spec["mp"],spec["tb"])
    ap=int(np.argmax(H)); vmax=float(V.max());
    twr_pk=pk/(m0*g); twr_init=init/(m0*g); vrail=rail_exit(th,spec["m"],spec["mp"],spec["tb"])
    tvc_window=max(spec["tb"]-0.5,0)
    rows[name]=dict(stage="single", dia_mm=spec["dia"], Itot_Ns=spec["I"], burn_s=spec["tb"],
        liftoff_g=round(m0*1000), apogee_m=round(float(H[ap]),1), apogee_ft=round(float(H[ap])*3.281),
        vmax_ms=round(vmax,1), mach=round(vmax/a_snd,2), peak_thrust_N=round(pk,1),
        TW_initial=round(twr_init,1), TW_peak=round(twr_pk,1), rail_exit_ms=round(vrail,1),
        tvc_window_s=round(tvc_window,2),
        rail_ok=bool(vrail>=15), tw_ok=bool(twr_pk>=5))
    traj[name]=(T,H,V)

# ---------------- two-stage estimate: G80T booster -> F15-4 sustainer ----------------
# Stack = sustainer(705 g, F15 aboard) + booster section(150 g ASA + fins) + booster motor(G80T 108 g)
m_sus=0.792; m_boost_struct=0.150; thG80,pkG80,initG80=curve(MOTORS["G80T"])
m_stack=m_sus+m_boost_struct+MOTORS["G80T"]["m"]
# phase 1: full stack on G80T (extra drag: booster adds length, use 1.25x Cd*A proxy)
def fly2(boost="G80T"):
    m_stack=m_sus+m_boost_struct+MOTORS[boost]["m"]
    dt=1e-3; t=0.;s=np.array([0.,0.]); tb1=MOTORS[boost]["tb"]; mp1=MOTORS[boost]["mp"]
    ms=lambda tt: max(m_stack-mp1, m_stack-(mp1/tb1)*min(tt,tb1))
    T=[];H=[];V=[]
    while t<tb1:
        thB,_,_=curve(MOTORS[boost])
        def dz(st,tt):
            h,v=st; Dr=0.5*rho0*np.exp(-h/8500)*Cd(abs(v)/a_snd)*1.25*A*v*abs(v)
            return np.array([v,(thB(tt)-Dr-ms(tt)*g)/ms(tt)])
        k1=dz(s,t);k2=dz(s+.5*dt*k1,t+.5*dt);k3=dz(s+.5*dt*k2,t+.5*dt);k4=dz(s+dt*k3,t+dt)
        s=s+dt/6*(k1+2*k2+2*k3+k4); t+=dt; T.append(t);H.append(s[0]);V.append(s[1])
    # separation + 0.5 s coast, then F15-4 sustainer ignites (electronic), sustainer mass 705 g
    thF,_,_=curve(MOTORS["F15-4"]); tbF=MOTORS["F15-4"]["tb"]; mpF=MOTORS["F15-4"]["mp"]
    msF=lambda tt: max(0.792-mpF, 0.792-(mpF/tbF)*min(max(tt,0),tbF))
    for _ in range(int(0.5/dt)): # coast
        h,v=s; Dr=0.5*rho0*np.exp(-h/8500)*Cd(abs(v)/a_snd)*A*v*abs(v)
        s=s+dt*np.array([v,(-Dr-0.792*g)/0.792]); t+=dt; T.append(t);H.append(s[0]);V.append(s[1])
    t2=0.
    while True:
        def dz(st,tt):
            h,v=st; Dr=0.5*rho0*np.exp(-h/8500)*Cd(abs(v)/a_snd)*A*v*abs(v)
            return np.array([v,(thF(tt)-Dr-msF(tt)*g)/msF(tt)])
        k1=dz(s,t2);k2=dz(s+.5*dt*k1,t2+.5*dt);k3=dz(s+.5*dt*k2,t2+.5*dt);k4=dz(s+dt*k3,t2+dt)
        s=s+dt/6*(k1+2*k2+2*k3+k4); t+=dt; t2+=dt; T.append(t);H.append(s[0]);V.append(s[1])
        if s[1]<0 and t2>tbF: break
        if t>40: break
    return np.array(T),np.array(H),np.array(V)
for boost in ["G80T","G74W"]:
    Tb,Hb,Vb=fly2(boost); apb=int(np.argmax(Hb)); spc=MOTORS[boost]
    thb,pkb,initb=curve(spc); mstk=m_sus+m_boost_struct+spc["m"]
    vrailb=rail_exit(thb, spc["m"]+m_boost_struct+m_sus-M_AIRFRAME, spc["mp"], spc["tb"])
    key=f"2-stage {boost}→F15"
    rows[key]=dict(stage="two", dia_mm=29, Itot_Ns=round(spc["I"]+49.6,1), burn_s=round(spc["tb"]+0.5+3.45,2),
        liftoff_g=round(mstk*1000), apogee_m=round(float(Hb[apb]),1), apogee_ft=round(float(Hb[apb])*3.281),
        vmax_ms=round(float(Vb.max()),1), mach=round(float(Vb.max())/a_snd,2), peak_thrust_N=round(pkb,1),
        TW_initial=round(initb/(mstk*g),1), TW_peak=round(pkb/(mstk*g),1), rail_exit_ms=round(vrailb,1),
        tvc_window_s=round(MOTORS["F15-4"]["tb"]-0.5,2), rail_ok=bool(vrailb>=15), tw_ok=bool(pkb/(mstk*g)>=5),
        note="adds separation+sustainer-ignition electronics, booster recovery, bigger fins, +150 g")
    traj[key]=(Tb,Hb,Vb)

for n in rows: rows[n]["under_1000ft"]=bool(rows[n]["apogee_ft"]<1000)
json.dump(rows, open(f"{OUT}/motor_tradestudy.json","w"), indent=2)

# ---------------- plots ----------------
# 1. trajectory overlay
fig,ax=plt.subplots(figsize=(10,5.5)); cmap={"F15-4":GRY,"F67W":"#43aa8b","G74W":ORG,"G80T":BLU,"G64W":GRN,"2-stage G80T→F15":RED,"2-stage G74W→F15":"#9d4edd"}
for n,(T,H,V) in traj.items():
    ax.plot(T,H,c=cmap[n],lw=2,label=f"{n} ({rows[n]['apogee_ft']} ft)")
ax.set_xlabel("t (s)"); ax.set_ylabel("altitude (m)"); ax.grid(alpha=.3); ax.legend()
ax.set_title("GTR70E WYVERN, apogee by motor option (RK4 + Barrowman)")
fig.tight_layout(); fig.savefig(f"{OUT}/01_apogee_overlay.png",dpi=130); plt.close()

# 2. metric bars: rail-exit v and T/W
names=list(rows.keys())
fig,ax=plt.subplots(1,2,figsize=(13,5))
re_=[rows[n]["rail_exit_ms"] for n in names]; tw=[rows[n]["TW_peak"] for n in names]
ax[0].bar(names,re_,color=[GRN if rows[n]["rail_ok"] else RED for n in names]); ax[0].axhline(15,ls='--',c='k'); ax[0].set_ylabel("rail-exit velocity (m/s)"); ax[0].set_title("Rail-exit velocity (≥15 floor)"); ax[0].tick_params(axis='x',rotation=20)
ax[1].bar(names,tw,color=[GRN if rows[n]["tw_ok"] else RED for n in names]); ax[1].axhline(5,ls='--',c='k'); ax[1].set_ylabel("peak T/W"); ax[1].set_title("Peak thrust-to-weight (≥5 floor)"); ax[1].tick_params(axis='x',rotation=20)
fig.tight_layout(); fig.savefig(f"{OUT}/02_railexit_tw.png",dpi=130); plt.close()

# 3. comparison table
fig,ax=plt.subplots(figsize=(13,4.2)); ax.axis("off")
cols=["motor","stage","Itot Ns","burn s","liftoff g","apogee ft","Mach","T/W pk","rail-exit","TVC win s"]
cell=[[n,rows[n]["stage"],rows[n]["Itot_Ns"],rows[n]["burn_s"],rows[n]["liftoff_g"],rows[n]["apogee_ft"],
       rows[n]["mach"],rows[n]["TW_peak"],rows[n]["rail_exit_ms"],rows[n]["tvc_window_s"]] for n in names]
tb_=ax.table(cellText=cell,colLabels=cols,loc="center",cellLoc="center"); tb_.auto_set_font_size(False); tb_.set_fontsize(9); tb_.scale(1,1.6)
for i,n in enumerate(names,1):
    ok=rows[n]["rail_ok"] and rows[n]["tw_ok"]; tb_[(i,8)].set_facecolor(GRN if rows[n]["rail_ok"] else RED); tb_[(i,8)].set_text_props(color="white")
    tb_[(i,7)].set_facecolor(GRN if rows[n]["tw_ok"] else RED); tb_[(i,7)].set_text_props(color="white")
ax.set_title("Motor trade, green = passes rail-exit / T/W gate",fontweight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/03_tradetable.png",dpi=130); plt.close()

print(json.dumps(rows,indent=2))
print("\nplots + motor_tradestudy.json ->",OUT)
