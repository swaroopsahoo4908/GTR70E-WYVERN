#!/usr/bin/env python3
"""WYVERN-E 2.0 -- 2D airfoil CFD (vortex panel method) for the fin profiles.

A constant-strength vortex-panel method (Kuethe & Chow, *Foundations of
Aerodynamics*) solves the inviscid incompressible flow about each RQ1 fin
section, returning the surface pressure coefficient Cp and the lift coefficient
Cl. The method is validated against thin-airfoil theory (dCl/dalpha = 2*pi/rad).
A flat-plate skin-friction model adds a viscous profile-drag estimate so L/D is
meaningful for fin selection (RQ1) and future control-vane work.

The angle sweep uses 0.5 deg increments -- the same deflection resolution as the
RQ1 wind-tunnel campaign -- so the polars are directly comparable to tunnel data.

Outputs (this folder):
  airfoil_polars.csv  -- Cl, Cd, L/D vs alpha for every profile, at tunnel + flight Re
  cl_alpha.png        -- Cl(alpha) for all four profiles + thin-airfoil reference
  cp_distribution.png -- Cp(x) at alpha = 5 deg for all four profiles

Inviscid caveat: the panel method captures Cl and pressure distribution but not
viscous separation/stall or pressure drag; real Cd and stall onset come from the
wind tunnel (RQ1/RQ2) and are what this code is meant to be validated against.
"""
import os, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from airfoil_profiles import PROFILES

HERE = os.path.dirname(os.path.abspath(__file__))
RE_TUNNEL = 2.0e5     # representative wind-tunnel Reynolds (fin chord)
RE_FLIGHT = 3.4e5     # representative powered-ascent fin Reynolds

def solve_panels(XB, YB, alpha):
    """Vortex panel method. Returns Cl, Cp[], control points, panel lengths."""
    M = len(XB)-1
    X = 0.5*(XB[:-1]+XB[1:]); Y = 0.5*(YB[:-1]+YB[1:])
    dx = XB[1:]-XB[:-1]; dy = YB[1:]-YB[:-1]
    S = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    sn, cs = np.sin(th), np.cos(th)
    # vectorized influence coefficients: rows i = control points, cols j = panels
    Xi=X[:,None]; Yi=Y[:,None]; XBj=XB[:-1][None,:]; YBj=YB[:-1][None,:]
    thi=th[:,None]; thj=th[None,:]; Sj=S[None,:]; snj=sn[None,:]; csj=cs[None,:]
    A=-(Xi-XBj)*csj-(Yi-YBj)*snj
    B=(Xi-XBj)**2+(Yi-YBj)**2
    C=np.sin(thi-thj); Dd=np.cos(thi-thj)
    E=(Xi-XBj)*snj-(Yi-YBj)*csj
    np.fill_diagonal(B, 1.0)                      # avoid /0 on diagonal (overwritten below)
    F=np.log(1.0+(Sj**2+2*A*Sj)/B)
    G=np.arctan2(E*Sj, B+A*Sj)
    P=(Xi-XBj)*np.sin(thi-2*thj)+(Yi-YBj)*np.cos(thi-2*thj)
    Q=(Xi-XBj)*np.cos(thi-2*thj)-(Yi-YBj)*np.sin(thi-2*thj)
    CN2=Dd+0.5*Q*F/Sj-(A*C+Dd*E)*G/Sj
    CN1=0.5*Dd*F+C*G-CN2
    CT2=C+0.5*P*F/Sj+(A*Dd-C*E)*G/Sj
    CT1=0.5*C*F-Dd*G-CT2
    di=np.diag_indices(M)
    CN1[di]=-1.0; CN2[di]=1.0; CT1[di]=0.5*np.pi; CT2[di]=0.5*np.pi
    AN=np.zeros((M+1,M+1)); AT=np.zeros((M,M+1))
    AN[:M,0]=CN1[:,0]; AN[:M,M]=CN2[:,M-1]; AN[:M,1:M]=CN1[:,1:M]+CN2[:,0:M-1]
    AT[:,0]=CT1[:,0];  AT[:,M]=CT2[:,M-1];  AT[:,1:M]=CT1[:,1:M]+CT2[:,0:M-1]
    AN[M,0]=AN[M,M]=1.0                          # Kutta condition
    RHS=np.zeros(M+1); RHS[:M]=np.sin(th-alpha)
    gamma=np.linalg.solve(AN, RHS)
    V=np.cos(th-alpha)+AT@gamma                  # tangential surface velocity / Vinf
    Cp=1.0-V**2
    Cl=2.0*np.sum(V*S)                           # circulation Gamma=sum(V*S); clockwise nodes -> +Cl for +alpha
    return Cl, Cp, X, S

def viscous_cd(Re, tc):
    """Profile drag estimate: flat-plate Cf x thickness form factor, both sides."""
    Cf = 1.328/np.sqrt(Re) if Re < 5e5 else 0.074/Re**0.2   # laminar / turbulent
    FF = 1.0 + 2.0*tc + 60.0*tc**4                          # thickness form factor
    return 2.0*Cf*FF

def sweep(alphas_deg=np.arange(0.0, 12.01, 0.5)):
    rows=[]; cl_curves={}
    for name, fn in PROFILES.items():
        XB, YB = fn(); tc = float(2*YB.max())
        cl_curves[name]=[]
        for ad in alphas_deg:
            Cl,_,_,_ = solve_panels(XB, YB, np.radians(ad))
            cdt = viscous_cd(RE_TUNNEL, tc); cdf = viscous_cd(RE_FLIGHT, tc)
            rows.append(dict(profile=name, alpha_deg=round(float(ad),2), tc=round(tc,4),
                Cl_panel=round(float(Cl),4), Cl_thin=round(float(2*np.pi*np.radians(ad)),4),
                Cd_tunnel=round(float(cdt),5), Cd_flight=round(float(cdf),5),
                LD_tunnel=round(float(Cl/cdt),2) if cdt>0 else 0.0,
                LD_flight=round(float(Cl/cdf),2) if cdf>0 else 0.0))
            cl_curves[name].append(float(Cl))
    return rows, alphas_deg, cl_curves

def validate():
    """Cl slope of NACA0012 vs the 2*pi/rad thin-airfoil benchmark."""
    XB,YB = PROFILES["NACA0012"]()
    a=np.radians([0,2,4,6]); cl=[solve_panels(XB,YB,ai)[0] for ai in a]
    slope=np.polyfit(a,cl,1)[0]            # per radian
    return slope, 2*np.pi

def cp_plot(alpha_deg=5.0):
    fig,ax=plt.subplots(figsize=(8,5))
    for name,fn in PROFILES.items():
        XB,YB=fn(); Cl,Cp,X,S=solve_panels(XB,YB,np.radians(alpha_deg))
        ax.plot(X,Cp,label=f"{name} (Cl={Cl:.2f})",lw=1.3)
    ax.invert_yaxis(); ax.set(title=f"Surface Cp at alpha = {alpha_deg:.0f} deg",
        xlabel="x/c", ylabel="Cp"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(HERE,"cp_distribution.png"),dpi=110); plt.close(fig)

def cl_plot(alphas, curves, slope):
    fig,ax=plt.subplots(figsize=(8,5))
    for name,cl in curves.items(): ax.plot(alphas,cl,marker=".",ms=4,label=name)
    ax.plot(alphas,2*np.pi*np.radians(alphas),"k--",lw=1,label="thin-airfoil 2πα")
    ax.set(title="Fin profile lift curves (vortex panel method, 0.5° increments)",
        xlabel="angle of attack / deflection [deg]", ylabel="Cl"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(HERE,"cl_alpha.png"),dpi=110); plt.close(fig)

if __name__=="__main__":
    slope, ref = validate()
    print(f"validation: NACA0012 dCl/dalpha = {slope:.3f} /rad ({slope*np.pi/180:.4f}/deg)  "
          f"vs thin-airfoil 2*pi = {ref:.3f} /rad  -> {100*slope/ref:.1f}% of ideal")
    rows, alphas, curves = sweep()
    with open(os.path.join(HERE,"airfoil_polars.csv"),"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    cp_plot(); cl_plot(alphas, curves, slope)
    print(f"profiles: {', '.join(PROFILES)}")
    print(f"wrote airfoil_polars.csv ({len(rows)} rows), cl_alpha.png, cp_distribution.png")
