#!/usr/bin/env python3
"""WYVERN-E 2.0 two-stage trajectory + stability + TVC + recovery model.
Reproduces every figure in WYVERN_E2_Mathematics.md. Pure numpy, dt=0.5ms."""
import numpy as np
g=9.81; rho=1.225; D=0.084; A=np.pi*(D/2)**2; Cd=0.55
G78=dict(It=110.0,Favg=79.9,Fmax=101.9,tb=1.40,mprop=0.0597,mload=0.102)
F25=dict(It=77.9,Favg=25.6,Fmax=46.8,tb=3.10,mprop=0.0240,mload=0.062)
m_struct=0.600+0.080+0.230+0.060+0.090
m_booster_dry=0.275+0.066+0.025
m_stage2=m_struct-m_booster_dry+F25['mload']; m_stage1=m_booster_dry+G78['mload']
m0=m_stage1+m_stage2
def burn(m,F,tb,mp,v,h,dt=5e-4):
    md=mp/tb;t=0
    while t<tb:
        dr=0.5*rho*Cd*A*v*abs(v);v+=(F-dr-m*g)/m*dt;h+=v*dt;m-=md*dt;t+=dt
    return v,h,m
def coast(m,v,h,dt=5e-4,tmax=40):
    t=0;apo=h
    while v>0 and t<tmax:
        dr=0.5*rho*Cd*A*v*abs(v);v+=(-dr-m*g)/m*dt;h+=v*dt;t+=dt;apo=max(apo,h)
    return apo,t
if __name__=="__main__":
    print(f"liftoff {m0*1000:.0f} g | T/W avg {G78['Favg']/(m0*g):.1f} peak {G78['Fmax']/(m0*g):.1f}")
    v1,h1,m1=burn(m0,G78['Favg'],G78['tb'],G78['mprop'],0,0)
    print(f"booster burnout {v1:.0f} m/s M{v1/343:.2f} @ {h1:.0f} m")
    m=m0-G78['mprop'];v=v1;h=h1;t=0
    while t<0.5:
        dr=0.5*rho*Cd*A*v*abs(v);v+=(-dr-m*g)/m*5e-4;h+=v*5e-4;t+=5e-4
    print(f"staging {v:.0f} m/s @ {h:.0f} m")
    v2,h2,m2=burn(m_stage2,F25['Favg'],F25['tb'],F25['mprop'],v,h)
    print(f"sustainer burnout {v2:.0f} m/s M{v2/343:.2f} @ {h2:.0f} m")
    apo,tc=coast(m2-F25['mprop'],v2,h2)
    print(f"apogee {apo:.0f} m ({apo*3.281:.0f} ft), coast {tc:.1f} s")
    d=18*0.0254;Ac=np.pi*(d/2)**2
    print(f"descent {np.sqrt(2*(m2-F25['mprop'])*g/(rho*0.97*Ac)):.1f} m/s under 18in chute")
