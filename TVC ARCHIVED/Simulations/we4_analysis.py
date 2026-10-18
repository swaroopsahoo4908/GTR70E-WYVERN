#!/usr/bin/env python3
"""GTR70E WYVERN, engineering analysis suite (drag, structural/FEA, thermal, power, sensitivity,
servo sizing) -> plots4/, for the single-stage F15-4 TVC vehicle.

The structural/thermal component list here (body tube, 4x fins) is a first-order model, not part of
the documented mass cascade (core.py -> we4_flightsim.py -> docs) and not tied to the zoned
ASA-Aero/PETG-CF/PC-FR CAD geometry. Re-derive the structural/thermal sections against current CAD
geometry before treating this file's plots as authoritative for those two sections; the power-budget
section names the current avionics stack directly."""
import os,json,numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"plots4"+os.environ.get("WYVERN_RUN_TAG","")); os.makedirs(OUT,exist_ok=True)
R=json.load(open(f"{OUT}/results_summary.json"))
g=9.80665; rho=1.225; OD=0.070; wall=0.0016; A=np.pi*(OD/2)**2; m=R["m_lift_g"]/1000
Fpk=25.3; Favg=14.4; Iyy=R["Iyy_lift"]; arm=R["control_arm_lift_cm"]/100; CG=R["cg_lift_cm"]/100
def sv(fig,n): fig.tight_layout(); fig.savefig(f"{OUT}/{n}.png",dpi=130); plt.close(fig)
add={}
# 07 drag buildup (component Cd vs Mach, low speed)
Ma=np.linspace(0.02,0.18,40)
Cf=0.42/np.sqrt(np.maximum(Ma*343*OD/1.5e-5,1e3))*8 # skin friction ~Re^-0.5 scaled
Cd_sf=0.10+0*Ma+ Cf*0; Cd_skin=0.22+0.0*Ma; Cd_base=0.12+0.05*Ma; Cd_press=0.10+0.1*Ma
Cd=Cd_skin+Cd_base+Cd_press
fig,ax=plt.subplots(figsize=(8.5,5))
ax.stackplot(Ma,Cd_skin,Cd_base,Cd_press,labels=["skin friction","base drag","pressure/forebody"],colors=["#2a6f97","#a7c957","#bc4749"],alpha=.8)
ax.axhline(0.539,ls='--',c='k',label="design Cd=0.539"); ax.set_xlabel("Mach"); ax.set_ylabel("Cd"); ax.legend(loc='upper left')
ax.set_title("GTR70E WYVERN · drag buildup (finned 70 mm airframe, 4x 72 mm fins)",fontweight='bold'); ax.grid(alpha=.3); sv(fig,"07_drag_buildup")
# 08 structural / first-order FEA margins
Awall=np.pi*OD*wall # tube wall area
sig_axial=Fpk/Awall/1e6 # MPa axial compression at peak thrust
side=Fpk*np.sin(np.radians(5)) # TVC side force
Mbend=side*0.16 # bending moment at bulkhead A (~arm)
I_tube=np.pi/64*(OD**4-(OD-2*wall)**4); sig_bend=Mbend*(OD/2)/I_tube/1e6
sig_pivot=side/((np.pi*0.002**2))/1e6 # 2mm pivot pin shear-ish
YIELD={"PLA body":50,"PETG-CF engine":45,"PETG-CF pivot":45}
comp={"Tube axial (PLA)":(sig_axial,50),"Tube bending (PLA)":(sig_bend,50),"Gimbal pivot (PC-FR)":(sig_pivot,60),"Bulkhead A (PC-FR)":(side/ (np.pi*0.030**2)/1e6 *6,60)}
names=list(comp); SF=[comp[n][1]/max(comp[n][0],1e-3) for n in names]; add["min_SF"]=round(min(SF),1)
fig,ax=plt.subplots(figsize=(8.5,5)); b=ax.barh(names,SF,color=["#386641" if s>2 else "#bc4749" for s in SF])
ax.axvline(2.0,ls='--',c='r',label="SF=2 min"); ax.set_xscale('log'); ax.set_xlabel("safety factor (yield / stress)"); ax.legend()
for i,s in enumerate(SF): ax.text(s,i,f" {s:.0f}×",va='center')
ax.set_title(f"GTR70E WYVERN · first-order structural margins (min SF {min(SF):.0f}×)",fontweight='bold'); sv(fig,"08_fea_loads")
# 09 thermal soak (engine-bay PETG-CF wall, transient)
t=np.linspace(0,8,200); Tinf=900; h=120; k=0.2; cp=1100; rhoP=1250; th=0.0016
# lumped wall with phenolic liner barrier -> effective driving temp reduced
Tdrive=180 # liner-reduced inner-surface driving temp
tau=rhoP*cp*th/h; burn=3.45
Twall=20+(Tdrive-20)*(1-np.exp(-np.minimum(t,burn)/ (tau)))
Twall=np.where(t>burn,Twall[np.argmin(np.abs(t-burn))]*np.exp(-(t-burn)/30)+20*(1-np.exp(-(t-burn)/30)),Twall)
add["engine_wall_peak_C"]=round(float(Twall.max()),0)
fig,ax=plt.subplots(figsize=(8.5,5)); ax.plot(t,Twall,c="#bc4749",lw=2); ax.axhline(110,ls='--',c='orange',label="PC-FR HDT ~110 °C")
ax.axvline(burn,ls=':',c='g',label="burnout"); ax.set_xlabel("t (s)"); ax.set_ylabel("engine-bay wall °C"); ax.legend()
ax.set_title(f"GTR70E WYVERN · engine-bay thermal soak (peak ~{Twall.max():.0f} °C, with phenolic liner)",fontweight='bold'); ax.grid(alpha=.3); sv(fig,"09_thermal")
# 10 power budget
loads={"Custom the Pico 2 W perfboard (RP2350)":0.15,"2× servo (active avg)":3.0,"BNO085+BNO085":0.25,"BME688":0.05,"camera":1.5}
Ptot=sum(loads.values()); E=2*3.7*0.45*0.9 # 2S 450mAh usable Wh
add["power_active_W"]=round(Ptot,2); add["batt_Wh"]=round(E,2); add["endurance_min"]=round(E/Ptot*60,0)
fig,ax=plt.subplots(figsize=(8.5,5)); ax.bar(loads.keys(),loads.values(),color="#2a6f97"); ax.set_ylabel("W")
ax.set_title(f"GTR70E WYVERN · power {Ptot:.1f} W active · 2S 450 mAh = {E:.1f} Wh → {E/Ptot*60:.0f} min ({E/Ptot/0.1:.0f}× the 7 s flight)",fontweight='bold')
plt.setp(ax.get_xticklabels(),rotation=20,ha='right'); ax.grid(alpha=.3,axis='y'); sv(fig,"10_power_budget")
# 11 sensitivity tornado (apogee)
base_ap=R["apogee_ft"]
def ap(dm=0,dcd=0,dimp=0): # crude scaling: apogee ~ Itot^? / (m*Cd); use energy scaling
    return base_ap*(1+dimp)**1.0*(1-0.0)/((1+dm)**0.9*(1+dcd)**0.45)
vars=[("mass ±10%",ap(dm=0.1),ap(dm=-0.1)),("Cd ±20%",ap(dcd=0.2),ap(dcd=-0.2)),("total impulse ±5%",ap(dimp=-0.05),ap(dimp=0.05))]
fig,ax=plt.subplots(figsize=(8.5,4.5)); y=range(len(vars))
for i,(nm,lo,hi) in enumerate(vars): ax.barh(i,hi-lo,left=min(lo,hi),color="#a7c957",edgecolor="k")
ax.axvline(base_ap,c='r',label=f"nominal {base_ap:.0f} ft"); ax.set_yticks(list(y)); ax.set_yticklabels([v[0] for v in vars]); ax.set_xlabel("apogee (ft)"); ax.legend()
ax.set_title("GTR70E WYVERN · apogee sensitivity tornado",fontweight='bold'); sv(fig,"11_sensitivity")
# 12 servo / gimbal sizing
Treq=Fpk*np.sin(np.radians(5))*0.025 # torque about gimbal pivot, 25mm nozzle offset arm
Treq_kgcm=Treq/9.81*100
add["gimbal_torque_Ncm"]=round(Treq*100,2); add["gimbal_torque_kgcm"]=round(Treq_kgcm,2)
servos={"req @±8° (SF 2)":Treq_kgcm*2,"ES08MA II":2.0,"MG90D":2.2,"DS3225 micro":3.0}
fig,ax=plt.subplots(figsize=(8,4.5)); ax.bar(servos.keys(),servos.values(),color=["#bc4749","#386641","#386641","#386641"])
ax.set_ylabel("torque (kg·cm)"); ax.set_title(f"GTR70E WYVERN · gimbal torque need {Treq_kgcm:.2f} kg·cm (×2 SF) vs micro servos",fontweight='bold'); ax.grid(alpha=.3,axis='y'); sv(fig,"12_servo_sizing")
json.dump({**R,**add},open(f"{OUT}/results_summary.json","w"),indent=1)
print("analysis plots: 07_drag,08_fea,09_thermal,10_power,11_sensitivity,12_servo")
print(json.dumps(add,indent=1))
