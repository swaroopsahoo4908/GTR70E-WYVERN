#!/usr/bin/env python3
"""GTR70E WYVERN, single-stage F15-4 finned TVC sustainer (motor-ejection recovery): mass/CG/inertia,
trajectory, TVC control authority + maneuver, recovery, dispersion -> plots4/."""
import os, json, numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"plots4"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT,exist_ok=True)
g=9.80665; rho0=1.225; OD=0.070; A=np.pi*(OD/2)**2
# ---------- 1. MASS / CG / INERTIA (station = m from nose tip; two-body-tube architecture) ----------
# (name, mass_kg, station_m)
#
# Two-BT architecture: Upper BT + Lower BT + ONE bulkhead, with the Pico 2 W perfboard avionics
# stack carried on two slotted card-carrier disks in the Upper BT.
#
# Structural masses (first 8 rows) are real, from 3D parts/_generator/mass_report.json (current
# CAD run, `gen_rocket4.py`) -- not estimates. The Lower BT tube is ASA-Aero, hoop-stress-checked
# at SF ~6-10x under the 140 kPa ejection pulse (gen_rocket4.py docstring). Motor mount/gimbal use
# PC-FR (thermal duty next to the nozzle); bulkhead uses PETG-CF (direct gas-exposure part).
# Station values for non-structural items (recovery/avionics/actuation) are placement estimates
# within the two-BT geometry (nose=0 stations over a 672 mm vehicle), not CAD-extracted centroids
# -- same "confirmed vs. best-effort" caveat this project applies elsewhere. Perfboard mass is
# computed from 50x70x1.6 mm FR4; breakout and UBEC masses are vendor figures. No bench scale
# weight exists for the assembled stack or the LiPo pack yet.
ITEMS=[
 # ---- printed structure (real, mass_report.json) --------------------------------------------
 ("Nose cone (ASA-Aero)",0.0209,0.060),
 ("Upper BT tube (ASA-Aero)",0.0443,0.215),
 ("FC card carriers x2 (ASA-Aero, slotted)",0.0104,0.235),
 ("Lower BT tube (ASA-Aero)",0.0782,0.4974),
 ("Bulkhead joint (PETG-CF)",0.0172,0.316),
 ("Motor mount (PC-FR)",0.0577,0.5984),
 ("TVC gimbal assy (PC-FR)",0.1056,0.5484),
 ("4 fins (PETG-CF, 87 mm)",0.0708,0.6284),
 ("Rail buttons x2 (PETG-CF)",0.0012,0.4784),
 # ---- recovery (motor ejection; no RRC3/9V/e-match) ------------------------------------------
 ("Chute (24 in) + cord + swivel",0.058,0.340),("Nomex chute protector",0.006,0.340),
 ("Recovery wadding",0.006,0.300),
 # ---- avionics (Pico 2 W perfboard stack) -----------------------------------------------------
 # 2S LiPo -> PPTC -> arming switch -> 5 V switching UBEC -> Pico VSYS + servo rail.
 # Sensors run off the Pico's own 3V3 regulator. Breakout masses are vendor/comparable-product
 # figures; the perfboard is computed from 50x70x1.6 mm FR4 at 1.85 g/cm3 plus copper and headers.
 ("Perfboard 20x24 (50x70 mm) + headers",0.011,0.250),
 ("Raspberry Pi Pico 2 W",0.004,0.250),
 ("BNO085 bay breakout (0x4B)",0.003,0.245),
 ("BME688 breakout (0x76)",0.002,0.255),
 ("BMP388 breakout (0x77)",0.0015,0.255),
 ("microSD breakout + card",0.0025,0.245),
 ("BNO085 gimbal breakout + STEMMA-QT cable",0.005,0.5284),
 ("5 V 3 A switching UBEC",0.009,0.280),
 ("Arming switch + PPTC + passives",0.005,0.270),
 ("i3 4K thumb cam",0.036,0.180),
 ("2S LiPo (450mAh, comparable-product estimate)",0.027,0.250),
 ("Wiring/connectors",0.012,0.400),
 # ---- actuation --------------------------------------------------------------------------------
 ("2x TVC servo (EMAX ES08MA II, 12g ea, datasheet)",0.024,0.5284)]
MOTOR=("Estes F15-4 (loaded)",0.102,0.6084); PROP=0.060; Ln=0.672; PIVOT=0.5484 # gimbal pivot station
dry=ITEMS; m_dry=sum(m for _,m,_ in dry); m_lift=m_dry+MOTOR[1]
def cg(items): 
    M=sum(m for _,m,_ in items); return sum(m*x for _,m,x in items)/M, M
cg_dry,_=cg(dry); cg_lift,_=cg(dry+[MOTOR]); cg_burn,_=cg(dry+[(MOTOR[0],MOTOR[1]-PROP,MOTOR[2])])
def Iyy(items,c): return sum(m*(x-c)**2 for _,m,x in items) # pitch inertia (point masses on axis) + slender add
Iyy_lift=Iyy(dry+[MOTOR],cg_lift)+ (m_lift*(OD/2)**2)/4 # + thin-rod radial term approx
arm_lift=PIVOT-cg_lift; arm_burn=PIVOT-cg_burn
TW_avg=14.4/(m_lift*g); TW_pk=25.3/(m_lift*g)
# ---------- 2. F15-4 THRUST CURVE (same F15 propellant/curve; -4 = 4 s delay + ejection) (digitized, scaled to 49.6 Ns / 3.45 s) ----------
tc=np.array([0,0.05,0.12,0.2,0.3,0.5,1.0,1.5,2.0,2.5,3.0,3.3,3.45])
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
Fc=np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0])
Itot=_TRAPZ(Fc,tc); Fc*= 49.6/Itot # normalize to 49.6 Ns
def thrust(t): return float(np.interp(t,tc,Fc,left=0,right=0)) if 0<=t<=3.45 else 0.0
# ---------- 3. TRAJECTORY (RK4 point mass, Cd=0.539, mass loss) ----------
# Cd 0.539 is the componentwise Barrowman buildup value shared with we4_flightsim.py and
# wyvern_datagen/core.py (was 0.50 here and 0.58 in we4_stability.py -- three different numbers
# for the same vehicle). dt tightened 2e-3 -> 5e-4 in the 2026-08 fidelity pass.
# motor-ejection recovery: the F15-4 charge fires 4 s AFTER BURNOUT (t=7.45 s), not at t=4.0 s
T_DEPLOY=3.45+4.0
Cd=0.539; mdot=PROP/3.45; dt=5e-4
def rho(h): return rho0*np.exp(-h/8500)
t=0;v=0;h=0;m=m_lift; T=[];H=[];V=[];AC=[]
while True:
    Fth=thrust(t); m=max(m_dry, m_lift-mdot*min(t,3.45))
    D=0.5*rho(h)*Cd*A*v*abs(v); a=(Fth-D-m*g)/m
    v+=a*dt; h+=v*dt; t+=dt; T.append(t);H.append(h);V.append(v);AC.append(a/g)
    if h<0 and t>3.45: break
    if t>=T_DEPLOY: break
T=np.array(T);H=np.array(H);V=np.array(V);AC=np.array(AC)
bo=np.argmin(np.abs(T-3.45)); ap=np.argmax(H)
dep=np.argmin(np.abs(T-T_DEPLOY))
res=dict(m_lift_g=round(m_lift*1000,1),m_dry_g=round(m_dry*1000,1),prop_g=PROP*1000,
 cg_lift_cm=round(cg_lift*100,1),cg_burn_cm=round(cg_burn*100,1),Iyy_lift=round(Iyy_lift,4),
 control_arm_lift_cm=round(arm_lift*100,1),control_arm_burn_cm=round(arm_burn*100,1),
 TW_avg=round(TW_avg,2),TW_peak=round(TW_pk,2),
 burnout_alt_m=round(H[bo],1),burnout_v=round(V[bo],1),
 apogee_m=round(H[ap],1),apogee_ft=round(H[ap]*3.281,0),apogee_t=round(T[ap],2),
 deploy_v=round(V[dep],1),deploy_t=round(T_DEPLOY,2))
# ---------- 4. TVC PITCH CONTROL (rigid body, gimbal lag, PID) ----------
Iyy=Iyy_lift; th=0.02; q=0.0; dt2=2e-3; gim=0.0; lim=np.radians(8) # ±8° gimbal (matches firmware OUT_LIM_DEG)
# Gains frozen by the 24-point phase/gain-margin sweep (CONFLICTS.md 5, PID_TUNING_REPORT.md),
# matching the firmware and every other sim in the repo.
KP,KI,KD=0.10,0.40,0.18; integ=0; prev=0; TH=[];GI=[];SP=[];TT=[]
def setp(t): return 0.0 if t<2.0 else np.radians(4)*np.sin((t-2.0)*np.pi/1.2)
tau_servo=0.04 # 1st-order servo lag (~0.04s -> fast digital micro)
tt=0
while tt<3.45:
    Fth=thrust(tt); arm=PIVOT-(cg_lift+(cg_burn-cg_lift)*min(tt/3.45,1))
    sp=setp(tt); e=sp-th; integ=np.clip(integ+e*dt2,-0.5,0.5); d=(e-prev)/dt2; prev=e
    cmd=np.clip(KP*e+KI*integ+KD*d,-lim,lim)
    gim+=(cmd-gim)*dt2/tau_servo # servo slew lag
    dist=Fth*np.sin(np.radians(1.0))*arm # ~1deg thrust misalignment disturbance
    M=Fth*np.sin(gim)*arm - dist
    q+=M/Iyy*dt2; th+=q*dt2; tt+=dt2
    TT.append(tt);TH.append(np.degrees(th));GI.append(np.degrees(gim));SP.append(np.degrees(sp))
res["tvc_max_dev_deg"]=round(max(abs(x) for x in TH),2)
# control authority over burn
# Evaluate control authority over the TVC-ACTIVE window only. Sweeping from t=0 to t=3.45 
# includes both thrust-zero endpoints, where control moment and disturbance moment are both
# identically zero -- so the reported 'minimum margin' was always exactly 0.0 mN.m and carried
# no information. The controller is inhibited before t=0.5 s and thrust has collapsed by 3.3 s.
tb=np.linspace(0.5,3.3,400); Fb=np.array([thrust(x) for x in tb])
armb=PIVOT-(cg_lift+(cg_burn-cg_lift)*np.clip(tb/3.45,0,1))
M_ctrl=Fb*np.sin(np.radians(5))*armb; M_dist=Fb*np.sin(np.radians(2))*armb
res["ctrl_margin_min_mNm"]=round(float((M_ctrl-M_dist).min()*1000),2)
# ---------- 5. RECOVERY (deploy @4s, chute descent) ----------
# Chute 18 in -> 24 in (2026-08). 0.6096 m canopy: slower descent, more drift.
Cd_c=1.5; d_chute=0.6096; Ac=np.pi*(d_chute/2)**2
vt=np.sqrt(2*(m_dry)*g/(rho0*Cd_c*Ac)); res["chute_in"]=round(d_chute/0.0254,0); res["descent_v"]=round(vt,1)
# ---------- PLOTS ----------
def save(fig,n): fig.tight_layout(); fig.savefig(f"{OUT}/{n}.png",dpi=130); plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5)); ax.plot(T,H,c="#2a6f97",label="altitude (m)"); ax.set_xlabel("t (s)"); ax.set_ylabel("altitude (m)",color="#2a6f97")
ax2=ax.twinx(); ax2.plot(T,V,c="#bc4749",label="velocity"); ax2.set_ylabel("velocity (m/s)",color="#bc4749")
ax.axvline(3.45,ls=':',c='g'); ax.axvline(T_DEPLOY,ls='--',c='k'); ax.text(3.46,5,"burnout"); ax.text(T_DEPLOY+.05,H[ap]*0.6,f"motor eject {T_DEPLOY:.2f}s")
ax.set_title(f"GTR70E WYVERN · F15-4 trajectory · apogee {res['apogee_ft']:.0f} ft @ {res['apogee_t']}s",fontweight='bold'); ax.grid(alpha=.3); save(fig,"01_trajectory")
fig,ax=plt.subplots(figsize=(9,5)); tt2=np.linspace(0,3.45,200); ax.plot(tt2,[thrust(x) for x in tt2],c="#386641")
ax.fill_between(tt2,[thrust(x) for x in tt2],alpha=.2,color="#a7c957"); ax.set_xlabel("t (s)"); ax.set_ylabel("thrust (N)")
ax.set_title(f"Estes F15-4 thrust curve · {Itot if False else 49.6:.1f} N·s · avg 14.4 N / peak 25.3 N",fontweight='bold'); ax.grid(alpha=.3); save(fig,"02_f15_thrust")
fig,ax=plt.subplots(figsize=(9,5)); ax.plot(TT,SP,'k:',label="setpoint"); ax.plot(TT,TH,c="#2a6f97",label="pitch θ"); ax.plot(TT,GI,c="#bc4749",label="gimbal δ")
ax.axhline(5,ls='--',c='r',lw=.7); ax.axhline(-5,ls='--',c='r',lw=.7); ax.set_xlabel("burn time (s)"); ax.set_ylabel("deg"); ax.legend()
ax.set_title("GTR70E WYVERN · TVC pitch control, stabilize then maneuver (δ within ±8°)",fontweight='bold'); ax.grid(alpha=.3); save(fig,"03_tvc_control")
fig,ax=plt.subplots(figsize=(9,5)); ax.plot(tb,M_ctrl*1000,lw=2,c="#386641",label="restoring @±8° gimbal"); ax.plot(tb,M_dist*1000,lw=2,c="#bc4749",label="disturbance @2°")
ax.fill_between(tb,M_ctrl*1000,M_dist*1000,where=(M_ctrl>=M_dist),color="#a7c957",alpha=.3,label="margin"); ax.set_xlabel("burn time (s)"); ax.set_ylabel("pitch moment (mN·m)"); ax.legend()
ax.set_title(f"GTR70E WYVERN · TVC control authority (min margin {res['ctrl_margin_min_mNm']} mN·m)",fontweight='bold'); ax.grid(alpha=.3); save(fig,"04_control_authority")
# mass/CG stack
fig,ax=plt.subplots(figsize=(10,3.2))
for n,m,x in dry+[MOTOR]:
    ax.barh(0,0.02,left=x,height=min(0.8,m*6),align='center',color="#5a7d9a",alpha=.7)
ax.axvline(cg_lift,c='r',lw=2,label=f"CG {cg_lift*100:.1f} cm"); ax.axvline(PIVOT,c='g',ls='--',label=f"gimbal pivot {PIVOT*100:.0f} cm")
ax.set_xlim(0,Ln); ax.set_yticks([]); ax.set_xlabel("station from nose (m)"); ax.legend(loc='upper left')
ax.set_title(f"GTR70E WYVERN mass stack · liftoff {m_lift*1000:.0f} g · CG {cg_lift*100:.1f} cm · control arm {arm_lift*100:.1f} cm",fontweight='bold'); save(fig,"05_mass_cg")
# dispersion (apogee Monte Carlo on mass+Cd)
rng=np.random.default_rng(4); aps=[]
for _ in range(1000): # 400 -> 1000 draws (2026-08 fidelity pass; dt=5e-4 makes each draw ~4x costlier)
    mm=m_lift*rng.normal(1,0.05); cc=Cd*rng.normal(1,0.15); v=0;h=0;t=0;m=mm; dtm=2e-3
    while True:
        Fth=thrust(t); m=max(m_dry,mm-mdot*min(t,3.45)); D=0.5*rho(h)*cc*A*v*abs(v); v+=(Fth-D-m*g)/m*dtm; h+=v*dtm; t+=dtm
        if v<0 and t>3.45: break
        if t>12: break
    aps.append(h*3.281)
fig,ax=plt.subplots(figsize=(8.5,5)); ax.hist(aps,bins=30,color="#2a6f97",alpha=.8); ax.axvline(np.mean(aps),c='r',label=f"mean {np.mean(aps):.0f} ft")
ax.axvspan(204,401,color="#a7c957",alpha=.2,label="spec range 204–401 ft"); ax.set_xlabel("apogee (ft)"); ax.set_ylabel("count"); ax.legend()
ax.set_title("GTR70E WYVERN · apogee dispersion, N=1000 (±5% mass, ±15% Cd)",fontweight='bold'); ax.grid(alpha=.3); save(fig,"06_dispersion")
res["apogee_disp_ft"]=[round(np.percentile(aps,5),0),round(np.percentile(aps,95),0)]
json.dump(res,open(f"{OUT}/results_summary.json","w"),indent=1)
print(json.dumps(res,indent=1))
