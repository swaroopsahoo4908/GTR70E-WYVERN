#!/usr/bin/env python3
"""WYVERN-E 2.0 — engineering analysis suite (84 mm 2-stage TVC research vehicle).

Regenerates, for the 2.0 architecture, the analysis plots that carried over from the
1.0 (XRIM-117E interceptor) program. The interceptor-specific 1.0 plots
(05_engagement_paths_3d, 06_pk_curves, 07_pk_envelope) are intentionally NOT
reproduced — 2.0 is a research/TVC-demonstration vehicle, not a guided interceptor,
so probability-of-kill and engagement geometry have no 2.0 analogue.

Outputs -> Simulations/plots/:
  01_drag_buildup.png       02_aero_stability.png      03_fea_loads.png
  04_flight_paths.png       08_thermal.png             09_dispersion.png
  10_sensitivity_tornado.png   + results_summary.json

Pure numpy/matplotlib. Trajectory physics mirror run_sims.py (84 mm, G78->F25).
"""
import os, json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import run_sims as rs   # reuse the canonical 84 mm integrator (apogee reconciles to 386 m)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "plots"); os.makedirs(OUT, exist_ok=True)

g=9.81; D=rs.D; A=rs.A; Cd0=rs.Cd; a_sound=340.0
G78=rs.G78; F25=rs.F25; m_booster_dry=rs.m_booster_dry; m_stage2=rs.m_stage2
m_liftoff=rs.m_liftoff; CAL=D  # 1 caliber = body diameter

def combined_apogee(Cd=None, mscale=1.0, g78=1.0, f25=1.0, rhoscale=1.0, coast=0.5, full=False, dt=2e-4):
    """Combined G78->F25 trajectory via run_sims.integrate (exact canonical model),
    with optional ±scale perturbations for sensitivity/Monte-Carlo. Coarser dt for
    the MC/sensitivity sweeps (apogee converges by ~2e-3)."""
    Cd_s, rho0_s = rs.Cd, rs.rho0
    if Cd is not None: rs.Cd = Cd
    rs.rho0 = rho0_s*rhoscale
    try:
        ph1=rs.integrate([(G78['Favg']*g78,G78['tb'],G78['mprop'],coast)],
                         (m_booster_dry+m_stage2)*mscale-G78['mprop'], chute=None, descend=False, dt=dt)
        ph2=rs.integrate([(F25['Favg']*f25,F25['tb'],F25['mprop'],0)],
                         m_stage2*mscale-F25['mprop'], chute=None, descend=False,
                         v0=ph1['vend'], h0=ph1['hend'], dt=dt)
    finally:
        rs.Cd, rs.rho0 = Cd_s, rho0_s
    if full:
        T=np.array(list(ph1['ts'])+[t+ph1['tend'] for t in ph2['ts']])
        H=np.array(list(ph1['hs'])+list(ph2['hs']))
        V=np.array(list(ph1['vs'])+list(ph2['vs']))
        return T,H,V
    return ph2['apogee']

# ===================================================================== 01 DRAG
def plot_drag():
    # Hoerner-style subsonic Cd buildup, components sum ~ Cd0 at flight Mach
    comps={"Body skin friction":0.18,"Base drag":0.14,"Fin profile+friction":0.12,
           "Interface/interference":0.06,"Launch-lug + protrusions":0.05}
    M=np.linspace(0,0.45,80)
    # weak compressibility rise (Prandtl-Glauert-ish) below drag-divergence
    Cd=sum(comps.values())/(np.sqrt(1-np.minimum(M,0.5)**2))
    fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.6))
    a1.bar(comps.keys(),comps.values(),color="#2a6f97"); a1.set_ylabel("Cd contribution")
    a1.set_title("Subsonic Cd buildup (84 mm, power-off)"); a1.tick_params(axis='x',rotation=25)
    a1.axhline(Cd0,ls='--',c='k',lw=1); a1.text(0.02,Cd0+0.005,f"ΣCd = {sum(comps.values()):.2f}",fontsize=9)
    a2.plot(M,Cd,lw=2,c="#d00000"); a2.axvline(0.20,ls=':',c='g'); a2.text(0.205,Cd.min(),"flight Mmax 0.20",color='g',fontsize=9)
    a2.set_xlabel("Mach"); a2.set_ylabel("Cd"); a2.set_title("Cd vs Mach (Prandtl-Glauert)"); a2.grid(alpha=.3)
    fig.suptitle("WYVERN-E 2.0 · Aerodynamic Drag Buildup",fontweight='bold')
    fig.tight_layout(); fig.savefig(f"{OUT}/01_drag_buildup.png",dpi=130); plt.close(fig)

# ================================================================ 02 STABILITY
def plot_stability():
    L=0.876  # overall length m
    cp=0.685*L  # Barrowman CP aft of nose (~constant, low Mach) -> ~1.7 cal margin
    # CG shifts forward as propellant burns (motor aft). approx CG path over flight time
    t=np.linspace(0,F25['tb']+G78['tb']+2,120)
    cg0=0.525*L; cg_dry=0.505*L
    burn=np.clip((G78['tb']+0.5+F25['tb']-t)/(G78['tb']+F25['tb']),0,1)
    cg=cg_dry+(cg0-cg_dry)*burn
    margin=(cp-cg)/CAL
    fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.6))
    a1.axhline(cp*100,c="#d00000",lw=2,label=f"CP {cp*100:.1f} cm")
    a1.plot(t,cg*100,c="#2a6f97",lw=2,label="CG (propellant burn)")
    a1.set_xlabel("flight time (s)"); a1.set_ylabel("station from nose (cm)")
    a1.legend(); a1.set_title("CP / CG stations"); a1.grid(alpha=.3)
    a2.plot(t,margin,c="#386641",lw=2); a2.axhspan(1.0,2.0,color="#a7c957",alpha=.3,label="1.0–2.0 cal band")
    a2.set_xlabel("flight time (s)"); a2.set_ylabel("static margin (cal)")
    a2.set_title(f"Static margin (min {margin.min():.2f}, max {margin.max():.2f} cal)")
    a2.legend(); a2.grid(alpha=.3)
    fig.suptitle("WYVERN-E 2.0 · Static Stability (Barrowman)",fontweight='bold')
    fig.tight_layout(); fig.savefig(f"{OUT}/02_aero_stability.png",dpi=130); plt.close(fig)
    return float(margin.min()),float(margin.max())

# ================================================================== 03 FEA/LOADS
def plot_loads():
    maxq=2850.0  # Pa (atmospherics)
    n_g=5.1
    # axial compressive stress in body wall at max thrust
    F_ax=G78['Fmax']; t_w=2.0e-3; circ=np.pi*D
    sig_axial=F_ax/(circ*t_w)/1e6   # MPa
    # bending from max-q at small AoA on fin -> root bending moment
    fin_area=0.5*(0.104+0.046)*0.056; Cn=0.10
    Mb=maxq*fin_area*Cn*0.030          # N·m at root (0.03 m arm)
    sig_fin=6*Mb/(0.104*0.0045**2)/1e6 # MPa, root bending
    items=["Body wall\n(axial, G78 peak)","Fin root\n(max-q bending)","Coupler\n(separation shear)"]
    stress=[sig_axial,sig_fin,3.2]
    allow=[55,62,55]   # PETG-CF / PC yield-ish MPa
    x=np.arange(len(items)); fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.6))
    a1.bar(x-0.18,stress,0.36,label="applied",color="#bc4749")
    a1.bar(x+0.18,allow,0.36,label="material allowable",color="#386641")
    a1.set_xticks(x); a1.set_xticklabels(items,fontsize=8); a1.set_ylabel("stress (MPa)")
    a1.legend(); a1.set_title("Structural margins (worst-case flight loads)")
    for i,(s,al) in enumerate(zip(stress,allow)): a1.text(i,max(s,al)+1,f"SF {al/s:.1f}",ha='center',fontsize=8)
    # load timeline
    T,H,V=combined_apogee(full=True)
    dt=np.maximum(np.diff(T),1e-6); acc=np.concatenate([[0],np.diff(V)/dt])/g
    a2.plot(T,acc,c="#2a6f97",lw=1.5); a2.axhline(n_g,ls='--',c='r'); a2.text(T[-1]*0.5,n_g+0.1,f"peak {n_g} g",color='r',fontsize=9)
    a2.set_xlabel("time (s)"); a2.set_ylabel("axial load (g)"); a2.set_title("Inertial load timeline"); a2.grid(alpha=.3)
    fig.suptitle("WYVERN-E 2.0 · Structural Loads & Margins",fontweight='bold')
    fig.tight_layout(); fig.savefig(f"{OUT}/03_fea_loads.png",dpi=130); plt.close(fig)
    return [allow[i]/stress[i] for i in range(3)]

# ================================================================ 04 FLIGHT PATHS
def plot_flight():
    T,H,V=combined_apogee(full=True)
    fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.6))
    a1.plot(T,H,lw=2,c="#2a6f97"); a1.fill_between(T,H,alpha=.15,color="#2a6f97")
    a1.set_xlabel("time (s)"); a1.set_ylabel("altitude (m)")
    a1.set_title(f"Combined 2-stage trajectory (apogee {H.max():.0f} m)"); a1.grid(alpha=.3)
    a2.plot(T,V,lw=2,c="#d00000"); a2.set_xlabel("time (s)"); a2.set_ylabel("velocity (m/s)")
    a2.set_title(f"Velocity (twin-peak; Vmax {V.max():.0f} m/s, M {V.max()/a_sound:.2f})"); a2.grid(alpha=.3)
    fig.suptitle("WYVERN-E 2.0 · Flight Path (G78 → F25)",fontweight='bold')
    fig.tight_layout(); fig.savefig(f"{OUT}/04_flight_paths.png",dpi=130); plt.close(fig)
    return float(H.max()),float(V.max())

# ===================================================================== 08 THERMAL
def plot_thermal():
    # lumped TVC-bay wall temp from F25 case soak after burn; aero heating negligible at M0.2
    t=np.linspace(0,120,400); Tcase=250.0  # F25 case post-burn ~250C
    tau_in=8.0; tau_out=60.0
    bay=20+ (Tcase-20)*(1-np.exp(-t/tau_in))*np.exp(-t/tau_out)*0.35  # PC-FR bay through 1.5mm gap
    fig,ax=plt.subplots(figsize=(8.5,5))
    ax.plot(t,bay,lw=2,c="#bc4749",label="TVC bay wall (PC-FR)")
    for nm,hdt,c in [("PETG-CF HDT 78°C",78,"#888"),("PC-FR HDT 140°C",140,"#386641")]:
        ax.axhline(hdt,ls='--',c=c,lw=1); ax.text(95,hdt+1,nm,fontsize=8,color=c)
    ax.set_xlabel("time after sustainer burnout (s)"); ax.set_ylabel("temperature (°C)")
    ax.set_title(f"WYVERN-E 2.0 · TVC-Bay Thermal Soak (peak {bay.max():.0f}°C, PC-FR margin {140-bay.max():.0f}°C)",fontweight='bold')
    ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(f"{OUT}/08_thermal.png",dpi=130); plt.close(fig)
    return float(bay.max())

# ================================================================= 09 DISPERSION
def plot_dispersion(N=300, seed=7):
    rng=np.random.default_rng(seed)
    xs=[];ys=[];apos=[]
    for _ in range(N):
        Cd=Cd0*(1+rng.normal(0,0.08)); ms=1+rng.normal(0,0.03)
        g78=1+rng.normal(0,0.04); f25=1+rng.normal(0,0.05)
        apo=combined_apogee(Cd=Cd,mscale=ms,g78=g78,f25=f25,dt=2e-3)
        wind=abs(rng.normal(2.5,1.2)); wdir=rng.uniform(0,2*np.pi)
        # weathercock drift on ascent (small) + chute drift on descent (dominant)
        t_desc=apo/7.5  # sustainer main 7.5 m/s
        drift=wind*(t_desc*0.9)  # ~90% of descent exposed to wind
        xs.append(drift*np.cos(wdir)); ys.append(drift*np.sin(wdir)); apos.append(apo)
    xs=np.array(xs);ys=np.array(ys); r=np.hypot(xs,ys); cep=np.percentile(r,50)
    fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.8))
    a1.scatter(xs,ys,s=10,alpha=.5,c="#2a6f97")
    th=np.linspace(0,2*np.pi,100)
    for rr,c,l in [(cep,'g','CEP 50%'),(np.percentile(r,95),'r','95%')]:
        a1.plot(rr*np.cos(th),rr*np.sin(th),c=c,lw=1.5,label=f"{l} = {rr:.0f} m")
    a1.set_aspect('equal'); a1.set_xlabel("downwind (m)"); a1.set_ylabel("crosswind (m)")
    a1.legend(); a1.set_title("Landing dispersion (wind+Cd+thrust+mass MC)"); a1.grid(alpha=.3)
    a2.hist(apos,30,color="#386641",alpha=.8); a2.axvline(np.mean(apos),c='k',ls='--')
    a2.set_xlabel("apogee (m)"); a2.set_ylabel("count")
    a2.set_title(f"Apogee spread (μ {np.mean(apos):.0f} ± {np.std(apos):.0f} m)"); a2.grid(alpha=.3)
    fig.suptitle(f"WYVERN-E 2.0 · Monte-Carlo Dispersion (N={N})",fontweight='bold')
    fig.tight_layout(); fig.savefig(f"{OUT}/09_dispersion.png",dpi=130); plt.close(fig)
    return dict(cep_m=float(cep),drift95_m=float(np.percentile(r,95)),
                apo_mean=float(np.mean(apos)),apo_std=float(np.std(apos)))

# ============================================================== 10 SENSITIVITY
def plot_sensitivity():
    base=combined_apogee(dt=1e-3)
    params=[("Liftoff mass",dict(mscale=1.10),dict(mscale=0.90)),
            ("Drag Cd",dict(Cd=Cd0*1.10),dict(Cd=Cd0*0.90)),
            ("G78 impulse",dict(g78=1.10),dict(g78=0.90)),
            ("F25 impulse",dict(f25=1.10),dict(f25=0.90)),
            ("Air density",dict(rhoscale=1.10),dict(rhoscale=0.90)),
            ("Stage coast",dict(coast=0.75),dict(coast=0.25))]
    rows=[]
    for nm,hi,lo in params:
        a_hi=combined_apogee(dt=1e-3,**hi); a_lo=combined_apogee(dt=1e-3,**lo)
        rows.append((nm,a_lo-base,a_hi-base))
    rows.sort(key=lambda r:abs(r[2]-r[1]))
    fig,ax=plt.subplots(figsize=(9,5)); y=np.arange(len(rows))
    for i,(nm,dlo,dhi) in enumerate(rows):
        ax.barh(i,dhi,color="#2a6f97"); ax.barh(i,dlo,color="#bc4749")
    ax.axvline(0,c='k'); ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("Δ apogee vs baseline (m)")
    ax.set_title(f"WYVERN-E 2.0 · Apogee Sensitivity (±10%, baseline {base:.0f} m)",fontweight='bold')
    ax.text(0.98,0.02,"blue +param  ·  red −param",transform=ax.transAxes,ha='right',fontsize=8)
    ax.grid(alpha=.3,axis='x'); fig.tight_layout(); fig.savefig(f"{OUT}/10_sensitivity_tornado.png",dpi=130); plt.close(fig)
    return base

if __name__=="__main__":
    plot_drag()
    smin,smax=plot_stability()
    sf=plot_loads()
    apo,vmax=plot_flight()
    Tpk=plot_thermal()
    disp=plot_dispersion()
    base=plot_sensitivity()
    summary=dict(apogee_m=round(apo,1), vmax_ms=round(vmax,1), mach=round(vmax/a_sound,3),
                 static_margin_cal=[round(smin,2),round(smax,2)],
                 min_safety_factor=round(min(sf),2), tvc_bay_peak_C=round(Tpk,0),
                 dispersion=disp, liftoff_g=round(m_liftoff*1000,0),
                 retired_interceptor_plots=["05_engagement_paths_3d","06_pk_curves","07_pk_envelope"])
    json.dump(summary, open(f"{OUT}/results_summary.json","w"), indent=2)
    print("wrote plots ->", os.path.relpath(OUT))
    print(json.dumps(summary,indent=2))
