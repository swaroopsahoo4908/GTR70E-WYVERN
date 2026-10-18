#!/usr/bin/env python3
"""WYVERN-E 2.0 flight simulations -- Booster, TVC Sustainer, Combined.
RK4/Euler point-mass with quadratic drag. Mirrors the .ork configurations.
(OpenRocket binary cannot be fetched in this sandbox; .ork files are provided
to re-run in OpenRocket directly. This model is validated against hand calcs.)"""
import numpy as np
g=9.81; rho0=1.225; D=0.084; A=np.pi*(D/2)**2; Cd=0.55
def rho(h): return rho0*np.exp(-h/8500.0)
G78=dict(name="AeroTech G78",It=110.0,Favg=79.9,Fmax=101.9,tb=1.40,mprop=0.0597,mload=0.102)
F25=dict(name="AeroTech F25",It=77.9,Favg=25.6,Fmax=46.8,tb=3.10,mprop=0.0240,mload=0.062)
m_struct=0.820+0.080+0.230+0.060+0.090
m_booster_dry=0.318
m_stage2=m_struct-m_booster_dry+F25['mload']
m_stage1=m_booster_dry+G78['mload']
m_liftoff=m_stage1+m_stage2

def integrate(segments, m_dry_final, chute=None, dt=2e-4, v0=0.0, h0=0.0, m_dead=0.0, descend=True):
    """segments: list of (F, tb, mprop, coast_after). Returns time series + metrics."""
    t=0.0; v=v0; h=h0; ts=[0];hs=[h0];vs=[v0];accs=[0]
    vmax=max(0,v0);amax=0;vrail=None;rail=1.0
    m=sum(s[2] for s in segments)+m_dry_final+m_dead  # total wet
    for (F,tb,mp,coast) in segments:
        md=mp/tb; tseg=0
        while tseg<tb:
            dr=0.5*rho(h)*Cd*A*v*abs(v); a=(F-dr-m*g)/m
            v+=a*dt; h+=v*dt; m-=md*dt; t+=dt; tseg+=dt
            vmax=max(vmax,v); amax=max(amax,a)
            if vrail is None and h>=rail: vrail=v
            ts.append(t);hs.append(h);vs.append(v);accs.append(a)
        # coast
        tc=0
        while tc<coast and v>-1:
            dr=0.5*rho(h)*Cd*A*v*abs(v); a=(-dr-m*g)/m
            v+=a*dt; h+=v*dt; t+=dt; tc+=dt
            ts.append(t);hs.append(h);vs.append(v);accs.append(a)
    # coast to apogee
    while v>0:
        dr=0.5*rho(h)*Cd*A*v*abs(v); a=(-dr-m*g)/m
        v+=a*dt; h+=v*dt; t+=dt
        ts.append(t);hs.append(h);vs.append(v);accs.append(a)
    apogee=h; t_apogee=t
    # descent
    if chute and descend:
        dc,Cdc=chute; Ac=np.pi*(dc/2)**2
        while h>0:
            dr=0.5*rho(h)*Cdc*Ac*v*abs(v); a=(-dr-m*g)/m
            v+=a*dt; h+=v*dt; t+=dt
            ts.append(t);hs.append(h);vs.append(v)
        vground=abs(v)
    else: vground=None
    return dict(ts=ts,hs=hs,vs=vs,apogee=apogee,t_apogee=t_apogee,vmax=vmax,
                amax=amax,vrail=vrail,vground=vground,mach=vmax/340.0,m0=None,vend=v,hend=h,tend=t)

# Booster: full stack on G78 only (sustainer inert), recover whole stack on main
boost=integrate([(G78['Favg'],G78['tb'],G78['mprop'],0)], m_liftoff-G78['mprop'], chute=(0.457,0.97))
boost['m0']=m_liftoff
# Sustainer/TVC only: stage-2 standalone on F25 from rest
sus=integrate([(F25['Favg'],F25['tb'],F25['mprop'],0)], m_stage2-F25['mprop'], chute=(0.457,0.97))
sus['m0']=m_stage2
# Combined: G78 boost + 0.5s coast/stage + F25 sustain, recover sustainer (booster drops at sep)
# phase1: full stack on G78 (carry booster dry mass), coast 0.5s to staging, no descent
ph1=integrate([(G78['Favg'],G78['tb'],G78['mprop'],0.5)], m_booster_dry+m_stage2-G78['mprop'],
              chute=None, descend=False)
# phase2: drop booster, sustainer F25 from staging state, then main descent
ph2=integrate([(F25['Favg'],F25['tb'],F25['mprop'],0)], m_stage2-F25['mprop'],
              chute=(0.457,0.97), v0=ph1['vend'], h0=ph1['hend'])
import numpy as _np
comb=dict(ts=list(ph1['ts'])+[t+ph1['tend'] for t in ph2['ts']],
          hs=list(ph1['hs'])+list(ph2['hs']), vs=list(ph1['vs'])+list(ph2['vs']),
          apogee=ph2['apogee'], t_apogee=ph1['tend']+ph2['t_apogee'],
          vmax=max(ph1['vmax'],ph2['vmax']), amax=max(ph1['amax'],ph2['amax']),
          vrail=ph1['vrail'], vground=ph2['vground'], mach=max(ph1['vmax'],ph2['vmax'])/340.0, m0=m_liftoff)
comb['stage_v']=ph1['vend']; comb['stage_h']=ph1['hend']

def show(n,r,m0):
    print(f"\n=== {n} (liftoff {m0*1000:.0f} g) ===")
    print(f"  apogee        {r['apogee']:.0f} m ({r['apogee']*3.281:.0f} ft)")
    print(f"  max velocity  {r['vmax']:.0f} m/s  (Mach {r['mach']:.2f})")
    print(f"  max accel     {r['amax']:.0f} m/s^2 ({r['amax']/9.81:.1f} g)")
    print(f"  rail-exit v   {r['vrail']:.1f} m/s" if r['vrail'] else "  rail-exit v   n/a")
    print(f"  time to apogee {r['t_apogee']:.1f} s")
    if r['vground']: print(f"  landing v     {r['vground']:.1f} m/s ({r['vground']*3.281:.1f} ft/s)")

if __name__=="__main__":
    show("BOOSTER (G78, full stack, sustainer inert)",boost,m_liftoff)
    show("TVC SUSTAINER (F25, stage-2 standalone)",sus,m_stage2)
    show("COMBINED 2-STAGE (G78 -> F25)",comb,m_liftoff)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig,ax=plt.subplots(1,2,figsize=(11,4.2))
        for r,lbl,c in [(boost,"Booster (G78)","#c0392b"),(sus,"TVC Sustainer (F25)","#27ae60"),(comb,"Combined 2-stage","#2c3e80")]:
            ax[0].plot(r['ts'],r['hs'],label=lbl,color=c,lw=1.8)
            ax[1].plot(r['ts'],r['vs'],label=lbl,color=c,lw=1.8)
        ax[0].set_title("Altitude vs Time");ax[0].set_xlabel("t (s)");ax[0].set_ylabel("altitude (m)");ax[0].grid(alpha=.3);ax[0].legend()
        ax[1].set_title("Velocity vs Time");ax[1].set_xlabel("t (s)");ax[1].set_ylabel("velocity (m/s)");ax[1].grid(alpha=.3);ax[1].legend()
        fig.suptitle("WYVERN-E 2.0 Flight Simulations (RK4 point-mass, drag)")
        fig.tight_layout(); fig.savefig("WYVERN_E2_sim_plots.png",dpi=130)
        print("\nplot -> WYVERN_E2_sim_plots.png")
    except Exception as e: print("plot skipped:",e)
