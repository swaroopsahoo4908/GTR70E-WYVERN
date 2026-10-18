#!/usr/bin/env python3
"""GTR70E WYVERN, FLIGHT VALIDATION SUITE
================================================================================
Eight independent simulations, each with a hard PASS/FAIL gate, that together
answer one question: will the vehicle fly safely and predictably on an F15-4?

  1. Trajectory (RK4 + Barrowman drag) -> apogee, v_max, a_max, max-Q, Mach
  2. Static stability margin vs burn time -> CG shift; must stay >= 1.0 cal
  3. Rail departure -> rail-exit velocity & T/W
  4. TVC control authority -> gimbal restoring moment vs gust
  5. Wind weathercock + drift sweep -> tilt & downrange vs wind
  6. Monte-Carlo dispersion (N=25000, vectorized RK4 core) -> apogee/stability/deploy spread
  7. Recovery descent + opening shock -> descent rate, shock-cord load
  8. Structural axial load -> body-tube compressive safety factor

Run: python3 we4_validation.py (writes plots_val/*.png + validation_summary.json)
Engine is the same RK4+Barrowman build as we4_flightsim.py; constants mirrored below. The
Monte-Carlo section (6) delegates to wyvern_datagen/core.py so the gates and the released
datasets are scored by one engine, not two.
"""
import os, json, numpy as np
_TRAPZ=getattr(np,"trapezoid",getattr(np,"trapz",None)) # NumPy 2.x renamed trapz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),"plots_val"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT, exist_ok=True)
BLU, RED, GRN, ORG, PUR = "#2a6f97", "#bc4749", "#386641", "#e09f3e", "#6d597a"

# ----------------------------- vehicle constants (mirror we4_flightsim.py) -----------------------------
g, rho0 = 9.80665, 1.225
D = 0.070; Rb = D/2; A = np.pi*Rb**2 # 70 mm airframe
Lnose, Ltot = 0.12, 0.74
m_lift, m_dry, PROP, tb = 0.7203, 0.6603, 0.060, 3.45 # canonical mass
# Canonical liftoff CG (we4_sim mass stack / we4_flightsim / core.py). This file carried 0.467,
# the pre-ASA-Aero, pre-i3-camera value, so every margin gate below was scored against a
# vehicle that no longer exists -- and reported 1.44 cal where the real margin is 1.10.
CG_wet = 0.484 # liftoff CG (m from nose); dry CG moves fwd as prop burns
x_prop = 0.70 # propellant centroid (aft, in motor)
CG_dry = (m_lift*CG_wet - PROP*x_prop)/m_dry # ~0.447 m -> margin grows through the burn
a_sound = 343.0

# F15-4 thrust curve, scaled to 49.6 N*s total impulse
tc = np.array([0,0.05,0.12,0.2,0.3,0.5,1,1.5,2,2.5,3,3.3,3.45])
# F15 thrust curve CORRECTED 2026-08. The digitized shape integrated to 41.97 N.s, so the
# 49.6 N.s renormalization below scaled the whole curve by 1.1817 and pushed peak thrust to
# 29.9 N -- against Estes' published 25.3 N peak, and against the 3.26 peak T/W quoted
# throughout this repo (29.9 N gives 4.32). The sustain block (t >= 0.3 s) has been lifted by
# +2.4408 N so the curve now matches ALL THREE published values simultaneously:
# total impulse 49.6 N.s, peak 25.3 N, average 14.4 N. The renormalization is retained as a
# guard (it is now a ~1.0000 no-op) so any future re-digitization still lands on 49.6 N.s.
Fc = np.array([0, 12, 25.3, 22, 18.441, 15.441, 14.941, 14.641, 14.441, 14.241, 13.941, 9.441, 0]); Fc *= 49.6/_TRAPZ(Fc, tc)
thrust = lambda t: float(np.interp(t, tc, Fc, left=0, right=0)) if 0 <= t <= tb else 0.0
mass = lambda t: max(m_dry, m_lift-(PROP/tb)*min(max(t,0),tb))
CG = lambda t: CG_wet + (CG_dry-CG_wet)*min(max(t,0),tb)/tb
rho = lambda h: rho0*np.exp(-h/8500)

# ----------------------------- Barrowman aero (ellipsoid nose + 4x 72 mm fins) -----------------------------
def barrowman():
    CNn = 2.0; Xn = 0.333*Lnose
    cr, ct, sw, sp = 0.070, 0.035, 0.025, 0.072
    Lf = np.sqrt(sp**2+(sw+(ct-cr)/2)**2); k = 1+Rb/(sp+Rb)
    CNf = k*(4*4*(sp/D)**2)/(1+np.sqrt(1+(2*Lf/(cr+ct))**2)); xr = Ltot-cr
    Xf = xr+(sw/3)*(cr+2*ct)/(cr+ct)+(1/6)*((cr+ct)-cr*ct/(cr+ct))
    return (CNn*Xn+CNf*Xf)/(CNn+CNf), CNn+CNf
Xcp, CN = barrowman()
x_gimbal = 0.62 # gimbal pivot (nozzle), m from nose (matches core.PIVOT)

def Cd(M): # Barrowman-style drag buildup
    Cf = 0.0040; Swet = np.pi*D*Ltot
    cd = Cf*Swet/A + 0.12 + 0.10 + 0.150 # friction + base + pressure + fins
    return cd*(1+0.25*max(M-0.8,0)) # mild compressibility rise near M=0.8

# ----------------------------- shared RK4 trajectory -----------------------------
def fly(m0=m_lift, cd_k=1.0, imp_k=1.0, dt=5e-4):
    """Integrate [h,v]; returns time/alt/vel/acc arrays. cd_k, imp_k scale drag & impulse."""
    T=[];H=[];V=[];Ac=[]; t=0.0; s=np.array([0.0,0.0])
    th = lambda tt: thrust(tt)*imp_k
    ms = lambda tt: max(m0-PROP, m0-(PROP/tb)*min(max(tt,0),tb))
    def dz(st,tt):
        h,v=st; m=ms(tt); Dr=0.5*rho(h)*Cd(abs(v)/a_sound)*cd_k*A*v*abs(v)
        return np.array([v,(th(tt)-Dr-m*g)/m])
    while True:
        k1=dz(s,t);k2=dz(s+.5*dt*k1,t+.5*dt);k3=dz(s+.5*dt*k2,t+.5*dt);k4=dz(s+dt*k3,t+dt)
        s=s+dt/6*(k1+2*k2+2*k3+k4); t+=dt
        T.append(t);H.append(s[0]);V.append(s[1]);Ac.append(k1[1]/g)
        if s[0]<0 and t>tb: break
        if t>tb+4.0: break
    return map(np.array,(T,H,V,Ac))

gates = {} # name -> dict(value, limit, pass)

# ===================================================================================================
# 1. TRAJECTORY
# ===================================================================================================
T,H,V,Ac = fly()
bo=int(np.argmin(np.abs(T-tb))); ap=int(np.argmax(H))
v_max=float(np.max(V)); M_max=v_max/a_sound; a_max=float(np.max(Ac))
q=0.5*rho(H)*V**2; maxQ=float(np.max(q)); apogee=float(H[ap])
gates["mach_subsonic"]=dict(value=round(M_max,3), limit="< 0.85 (Barrowman valid)", **{"pass":bool(M_max<0.85)})
gates["apogee_ceiling_m"]=dict(value=round(apogee,1), limit="< 305 m (1000 ft NAR ceiling)", **{"pass":bool(apogee<305)})

fig,ax=plt.subplots(figsize=(9,5)); ax.plot(T,H,c=BLU,lw=2,label="altitude")
ax.set_xlabel("t (s)"); ax.set_ylabel("altitude (m)",color=BLU); ax.grid(alpha=.3)
a2=ax.twinx(); a2.plot(T,V,c=RED,lw=1.5,label="velocity"); a2.set_ylabel("velocity (m/s)",color=RED)
T_DEPLOY=tb+4.0 # F15-4 motor ejection: 4 s after burnout, not 4 s after liftoff
ax.axvline(tb,ls=':',c=GRN); ax.axvline(T_DEPLOY,ls='--',c='k')
ax.text(tb+.05,8,"burnout",color=GRN); ax.text(T_DEPLOY+.05,apogee*.45,f"motor eject {T_DEPLOY:.2f} s")
ax.set_title(f"1 · Trajectory, apogee {apogee*3.281:.0f} ft @ {T[ap]:.1f} s · v_max {v_max:.0f} m/s (M{M_max:.2f}) · a_max {a_max:.1f} g")
fig.tight_layout(); fig.savefig(f"{OUT}/01_trajectory.png",dpi=130); plt.close()

# ===================================================================================================
# 2. STABILITY MARGIN vs TIME (CG shifts forward as propellant burns -> margin grows)
# ===================================================================================================
tt=np.linspace(0,tb,200); marg=np.array([(Xcp-CG(x))/D for x in tt])
m_lift_cal=(Xcp-CG_wet)/D; m_dry_cal=(Xcp-CG_dry)/D
gates["margin_liftoff_cal"]=dict(value=round(m_lift_cal,2), limit=">= 1.0 cal", **{"pass":bool(m_lift_cal>=1.0-1e-9)})
gates["margin_max_cal"]=dict(value=round(float(marg.max()),2), limit="<= 2.5 cal (not over-stable)", **{"pass":bool(marg.max()<=2.5)})
fig,ax=plt.subplots(figsize=(9,4.5)); ax.plot(tt,marg,c=PUR,lw=2)
ax.axhspan(1.0,2.0,color=GRN,alpha=.12,label="1.0-2.0 cal target"); ax.axhline(1.0,ls='--',c=GRN); ax.axhline(2.0,ls='--',c=ORG)
ax.set_xlabel("t (s)"); ax.set_ylabel("static margin (cal)")
ax.set_title(f"2 · Static stability, {m_lift_cal:.2f} cal liftoff -> {m_dry_cal:.2f} cal burnout (CG moves fwd)")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(f"{OUT}/02_stability_margin.png",dpi=130); plt.close()

# ===================================================================================================
# 3. RAIL DEPARTURE, integrate boost over the rail length; rail-exit velocity is the real gate
# ===================================================================================================
L_rail=1.0 # Estes Pro Series II rail, usable ~1.0 m
twr_peak=float(np.max(Fc))/(m_lift*g); twr_avg=float(np.mean(Fc[Fc>0]))/(m_lift*g)
x=0.0; v=0.0; t=0.0; dt=1e-4; xs=[];vs=[]
while x<L_rail and t<tb:
    a=(thrust(t)-0.5*rho(0)*Cd(v/a_sound)*A*v*v-mass(t)*g)/mass(t)
    v+=a*dt; x+=v*dt; t+=dt; xs.append(x); vs.append(v)
v_rail=v; t_rail=t
gates["rail_exit_v_ms"]=dict(value=round(v_rail,1), limit=">= 15 m/s (fins effective)", **{"pass":bool(v_rail>=15.0)})
gates["thrust_to_weight_peak"]=dict(value=round(twr_peak,2), limit=">= 5 (rule of thumb)", **{"pass":bool(twr_peak>=5.0)})
fig,ax=plt.subplots(figsize=(9,4.5)); ax.plot(np.array(xs)*100,vs,c=BLU,lw=2)
ax.axhline(15,ls='--',c=RED); ax.text(2,15.5,"15 m/s safe-exit floor",color=RED)
ax.axvline(L_rail*100,ls=':',c='k'); ax.text(L_rail*100-22,2,f"rail end {L_rail} m")
ax.set_xlabel("distance up rail (cm)"); ax.set_ylabel("velocity (m/s)")
ax.set_title(f"3 · Rail departure, exit {v_rail:.1f} m/s @ {t_rail*1000:.0f} ms · T/W peak {twr_peak:.1f}, avg {twr_avg:.1f}")
ax.grid(alpha=.3)
# inset: rail-exit velocity vs rail length (mitigation quantified)
axi=ax.inset_axes([0.55,0.12,0.4,0.42]); Ls=np.linspace(0.5,3.0,18); Vex=[]
for Lr in Ls:
    xx=0.0;vv2=0.0;tt2=0.0
    while xx<Lr and tt2<tb:
        aa=(thrust(tt2)-0.5*rho(0)*Cd(vv2/a_sound)*A*vv2*vv2-mass(tt2)*g)/mass(tt2)
        vv2+=aa*1e-4; xx+=vv2*1e-4; tt2+=1e-4
    Vex.append(vv2)
axi.plot(Ls,Vex,c=PUR); axi.axhline(15,ls='--',c=RED,lw=.8); axi.set_title("exit v vs rail len",fontsize=7)
axi.set_xlabel("m",fontsize=6); axi.set_ylabel("m/s",fontsize=6); axi.tick_params(labelsize=6)
fig.tight_layout(); fig.savefig(f"{OUT}/03_rail_departure.png",dpi=130); plt.close()

# ===================================================================================================
# 4. TVC CONTROL AUTHORITY, available gimbal moment vs the moment required for the design maneuver.
# Gust rejection is carried by the FINS (gate 2, 1.0+ cal). TVC adds commanded control on top and,
# unlike fins, its authority does NOT depend on airspeed (it is thrust-reaction based).
# GIMBAL LIMIT CORRECTED 2026-08: was radians(5.0). The mechanical/firmware limit is 8.0 deg
# (wyvern_pid.h OUT_LIM_DEG, raised 5->8 specifically for crosswind weathercock authority).
# Clamping the model at 5 deg understates available authority by 37.5%.
# (The plot below already SAID '+-8 deg gimbal' while this computed at 5 -- the
# label was updated when the limit was raised, the number was not.)
TVC_ON=0.5; dmax=np.radians(8.0)
I_pitch=(1/12)*m_lift*Ltot**2 # slender-body pitch inertia
ang_target=np.radians(5.0) # design authority: 5 deg/s^2 commanded pitch accel
M_req=I_pitch*ang_target # required control moment (N*m)
ts=np.linspace(TVC_ON,3.2,300) # TVC active window (thrust meaningful, pre-burnout)
M_tvc=np.array([thrust(t)*np.sin(dmax)*(x_gimbal-CG(t)) for t in ts])
min_auth=float(np.min(M_tvc)); auth_ratio=min_auth/M_req
gates["tvc_authority_ratio"]=dict(value=round(auth_ratio,1), limit=">= 2x required maneuver moment", **{"pass":bool(auth_ratio>=2)})
hh=np.interp(ts,T,H); vv=np.interp(ts,T,V); qd=0.5*rho(hh)*vv**2
M_gust=qd*A*CN*np.radians(5.0)*(Xcp-np.array([CG(t) for t in ts])) # gust moment the FINS see (context)
fig,ax=plt.subplots(figsize=(9,4.5))
ax.plot(ts,M_tvc,c=GRN,lw=2,label="TVC available (±8° gimbal)")
ax.axhline(M_req,ls='--',c=BLU,label=f"required maneuver moment ({M_req*1000:.1f} mN·m)")
ax.plot(ts,M_gust,c=ORG,lw=1.3,ls=':',label="5° gust moment (handled by fins)")
ax.set_xlabel("t (s, TVC active)"); ax.set_ylabel("moment (N·m)")
ax.set_title(f"4 · TVC authority, {auth_ratio:.0f}x the required maneuver moment (airspeed-independent)")
ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/04_tvc_authority.png",dpi=130); plt.close()

# ===================================================================================================
# 5. WIND WEATHERCOCK + DRIFT SWEEP
# ===================================================================================================
winds=np.linspace(0,12,13)
# equilibrium weathercock tilt ~ atan(wind / rail-exit v), capped; drift ~ wind * descent_time
tilt=np.degrees(np.arctan2(winds, max(v_rail,1e-3)))
chute_Cd, chute_d = 1.5, 0.6096 # 24 in chute (was 18 in; changed 2026-08)
A_c=np.pi*(chute_d/2)**2
v_desc=np.sqrt(2*m_dry*g/(rho0*chute_Cd*A_c))
t_desc=apogee/max(v_desc,1e-3)
drift=winds*t_desc
gates["weathercock_max_deg"]=dict(value=round(float(tilt.max()),1), limit="<= 30 deg @ 10 m/s", **{"pass":bool(tilt.max()<=30)})
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
ax[0].plot(winds,tilt,'o-',c=ORG); ax[0].axhline(30,ls='--',c=RED); ax[0].set_xlabel("wind (m/s)"); ax[0].set_ylabel("weathercock tilt (deg)"); ax[0].set_title("5a · Wind-cocking vs wind"); ax[0].grid(alpha=.3)
ax[1].plot(winds,drift,'s-',c=BLU); ax[1].set_xlabel("wind (m/s)"); ax[1].set_ylabel("downrange drift under chute (m)"); ax[1].set_title(f"5b · Drift ({v_desc:.1f} m/s descent, {t_desc:.0f} s)"); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/05_wind_weathercock.png",dpi=130); plt.close()

# ===================================================================================================
# 6. MONTE-CARLO DISPERSION (N=3000): mass ±3%, Cd ±10%, impulse ±5%, wind 0-8 m/s
# ===================================================================================================
# The dispersion is now run on the vectorized RK4 core in wyvern_datagen/core.py rather than a
# 3000-iteration scalar Python loop over this file's own `fly()`. Two reasons, both substantive:
# - Volume: the vectorized core does ~40,000 draws in the time the scalar loop did ~3,000, so
# the tails that actually decide the >=99% gates are resolved instead of estimated from a
# few dozen samples.
# - Consistency: the scalar loop dispersed mass/Cd/impulse but flew a bare exponential
# atmosphere with no wind shear, no turbulence and no CG dispersion, and it approximated the
# static margin as `(Xcp-CG)/D/mass_ratio` -- a proxy, not a computed CG. The core disperses
# the CG station directly and reports the true margin. This file and the Monte-Carlo datasets
# in wyvern_datagen/datasets/ are now produced by the same engine.
import sys as _sys; _sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "wyvern_datagen"))
import core as _core
N=25000
_env=dict(wind_ms=(0.0,8.0)) # match this suite's historical 0-8 m/s wind band
rng=np.random.default_rng(42)
_o=_core.simulate_outcomes(N, seed=42, envelope=_env, dt=2e-3, disperse_vehicle=True)
ap_s = _o["apogee_m"]
dep_s = np.abs(_o["deploy_vspeed_ms"]) # vertical speed at the motor-ejection event
mar_s = _o["static_margin_cal"] # from the dispersed CG, not a mass-ratio proxy
land = _o["drift_from_pad_m"]
p_stable=float(np.mean(mar_s>=0.5)); p_safedeploy=float(np.mean(dep_s<35))
gates["mc_p_stable_pct"]=dict(value=round(100*p_stable,1), limit=">= 99% margin>=0.5 cal", **{"pass":bool(p_stable>=0.99)})
gates["mc_p_safe_deploy_pct"]=dict(value=round(100*p_safedeploy,1), limit=">= 99% deploy < 35 m/s", **{"pass":bool(p_safedeploy>=0.99)})
fig,ax=plt.subplots(1,3,figsize=(13,4))
ax[0].hist(ap_s*3.281,bins=40,color=BLU,alpha=.85); ax[0].set_xlabel("apogee (ft)"); ax[0].set_ylabel("count"); ax[0].set_title(f"6a · Apogee µ={ap_s.mean()*3.281:.0f}±{ap_s.std()*3.281:.0f} ft")
ax[1].hist(dep_s,bins=40,color=RED,alpha=.85); ax[1].axvline(35,ls='--',c='k'); ax[1].set_xlabel("deploy speed (m/s)"); ax[1].set_title(f"6b · Deploy v {100*p_safedeploy:.1f}% < 35 m/s")
ax[2].hist(mar_s,bins=40,color=PUR,alpha=.85); ax[2].axvline(0.5,ls='--',c=RED); ax[2].set_xlabel("static margin (cal)"); ax[2].set_title(f"6c · Stability {100*p_stable:.1f}% >= 0.5 cal")
fig.tight_layout(); fig.savefig(f"{OUT}/06_montecarlo.png",dpi=130); plt.close()

# landing scatter (drift azimuth random)
ang=rng.uniform(0,2*np.pi,N)
fig,ax=plt.subplots(figsize=(6,6)); ax.scatter(land*np.cos(ang),land*np.sin(ang),s=4,alpha=.3,c=BLU)
cep=float(np.median(land)); ax.add_patch(plt.Circle((0,0),cep,fill=False,ec=RED,lw=2,ls='--'))
ax.set_aspect('equal'); ax.set_xlabel("downrange (m)"); ax.set_ylabel("crossrange (m)")
ax.set_title(f"7 · Landing scatter, CEP {cep:.0f} m (wind 0-8 m/s)"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/07_landing_scatter.png",dpi=130); plt.close()

# ===================================================================================================
# 8. RECOVERY, descent rate + opening-shock load on the shock cord
# ===================================================================================================
v_open=float(abs(V[int(np.argmax(H))])) # speed at apogee (F15-4 motor ejection)
dt_open=0.15 # canopy fill time
F_shock=m_dry*abs(v_open)/dt_open + m_dry*g # impulse-momentum opening load
CORD_RATING=900.0 # 1/8" tubular Kevlar ~ 900 N (200 lb) working
SF_cord=CORD_RATING/F_shock
gates["descent_rate_ms"]=dict(value=round(v_desc,1), limit="3-7 m/s safe landing", **{"pass":bool(3<=v_desc<=7)})
gates["shock_cord_SF"]=dict(value=round(SF_cord,2), limit=">= 2.0", **{"pass":bool(SF_cord>=2.0)})
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
ax[0].bar(["deploy v","descent v"],[abs(v_open),v_desc],color=[RED,GRN]); ax[0].axhline(7,ls='--',c=ORG); ax[0].set_ylabel("m/s"); ax[0].set_title(f"8a · Recovery speeds (descent {v_desc:.1f} m/s)")
ax[1].bar(["opening shock","cord rating"],[F_shock,CORD_RATING],color=[RED,BLU]); ax[1].set_ylabel("force (N)"); ax[1].set_title(f"8b · Shock load {F_shock:.0f} N · SF {SF_cord:.1f}")
fig.tight_layout(); fig.savefig(f"{OUT}/08_recovery.png",dpi=130); plt.close()

# structural axial load (extra check, no plot gate): body tube compressive SF under max thrust+drag
F_axial=float(np.max(Fc))+maxQ*A # peak compressive
wall=0.0018; A_tube=np.pi*((Rb)**2-(Rb-wall)**2) # PC-FR annulus
sigma=F_axial/A_tube; PCFR_yield=60e6 # PC-FR ~60 MPa compressive
gates["structure_SF"]=dict(value=round(PCFR_yield/sigma,1), limit=">= 3", **{"pass":bool(PCFR_yield/sigma>=3)})

# ===================================================================================================
# VERDICT
# ===================================================================================================
npass=sum(1 for v in gates.values() if v["pass"]); ntot=len(gates)
verdict="GO, all gates pass" if npass==ntot else f"REVIEW, {ntot-npass} gate(s) flagged"
summary=dict(vehicle="GTR70E WYVERN (70 mm, F15-4, ellipsoid nose + 72 mm fins, no ballast)",
             liftoff_mass_kg=m_lift, apogee_m=round(apogee,1), apogee_ft=round(apogee*3.281,0),
             v_max_ms=round(v_max,1), mach_max=round(M_max,3), a_max_g=round(a_max,2),
             maxQ_Pa=round(maxQ,0), descent_ms=round(v_desc,1), CEP_m=round(cep,0),
             gates=gates, gates_passed=f"{npass}/{ntot}", verdict=verdict)
json.dump(summary, open(f"{OUT}/validation_summary.json","w"), indent=2)

# verdict figure (table)
fig,ax=plt.subplots(figsize=(10,6)); ax.axis("off")
ax.set_title(f"GTR70E WYVERN, Flight Validation [{npass}/{ntot} gates pass] {verdict}", fontweight="bold", fontsize=12)
rows=[[k, str(v["value"]), v["limit"], "PASS" if v["pass"] else "FLAG"] for k,v in gates.items()]
tb_=ax.table(cellText=rows, colLabels=["gate","value","limit","result"], loc="center", cellLoc="left")
tb_.auto_set_font_size(False); tb_.set_fontsize(9); tb_.scale(1,1.5)
for i,(k,v) in enumerate(gates.items(),1):
    tb_[(i,3)].set_facecolor(GRN if v["pass"] else RED); tb_[(i,3)].set_text_props(color="white",fontweight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/09_verdict.png",dpi=130); plt.close()

print(json.dumps(summary, indent=2))
print(f"\n{npass}/{ntot} gates pass -> {verdict}")
print(f"plots + validation_summary.json written to {OUT}")
