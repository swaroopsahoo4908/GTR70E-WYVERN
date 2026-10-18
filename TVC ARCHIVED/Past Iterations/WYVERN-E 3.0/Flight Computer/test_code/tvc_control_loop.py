#!/usr/bin/env python3
"""WYVERN-E 3.0 core TVC PID gimbal loop (200 Hz). Shared by both TVC systems;
the actuator backend is swapped (servo via PCA9685, or solenoid bang-bang via lgpio).
This module is import-safe for unit testing the control math without hardware."""
import time, math
class PID:
    def __init__(s,kp,ki,kd,lim=math.radians(5)):
        s.kp,s.ki,s.kd,s.lim=kp,ki,kd,lim; s.i=0.0; s.prev=0.0; s.t=None
    def step(s,err,now=None):
        now=now or time.monotonic(); dt=0.005 if s.t is None else max(1e-4,now-s.t); s.t=now
        s.i=max(-s.lim,min(s.lim,s.i+err*dt)); d=(err-s.prev)/dt; s.prev=err
        u=s.kp*err+s.ki*s.i+s.kd*d
        return max(-s.lim,min(s.lim,u))
def setpoint(phase,t):
    # stabilize to vertical for first 2.5 s, then a 3 deg pitch maneuver to demo authority
    if phase=="stabilize" or t<2.5: return 0.0
    return math.radians(3.0)*math.sin((t-2.5)*math.pi/2.2)
# gains: tuned for ~0.63 N.m authority / 16 kg.cm gimbal (see Mathematics.md, TVC_Comparison.md)
PITCH=PID(2.2,0.4,0.18); YAW=PID(2.2,0.4,0.18)
def update(meas_pitch,meas_yaw,t,phase="maneuver"):
    sp=setpoint(phase,t)
    return PITCH.step(sp-meas_pitch), YAW.step(0.0-meas_yaw)
if __name__=="__main__":
    # dry sim: prove the loop converges with a simple 1st-order gimbal->attitude model
    p=0.0; print("t   setpoint  pitch_cmd  pitch")
    for k in range(0,5200,400):
        t=k/1000; uc,_=update(p,0.0,t); p+=0.25*(uc-0.0)  # crude plant
        print(f"{t:4.1f}  {math.degrees(setpoint('maneuver',t)):+5.2f}    {math.degrees(uc):+5.2f}     {math.degrees(p):+5.2f}")
