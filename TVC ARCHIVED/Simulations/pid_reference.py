#!/usr/bin/env python3
"""GTR70E WYVERN, PID reference implementation (matches firmware/wyvern_pid.h exactly).
Discrete PID: integral-clamp anti-windup + first-order filtered derivative + output clamp.

Flight gains (re-tuned numerically; see ../Documentation/PID_TUNING_REPORT.md):
Kp=0.10 Ki=0.40 Kd=0.18, out_lim=8° (0.1396 rad), tau_d=0.02 s, i_lim=0.4.
Selected by sweeping >800 (Kp,Ki,Kd) triples against a linearized pitch plant + 40 ms servo lag +
2 ms loop delay (Pade-2) at 24 operating points (4 atmospheres x 6 burn-time slices), keeping only
gains with worst-case phase margin >=30 deg and gain margin >=6 dB at every point, then minimizing
nonlinear gust-rejection pitch deviation. Worst-case result: PM=32.8 deg, GM=11.3 dB, gust pitch
deviation 1.31 deg, gimbal usage 1.68 deg (limit +-8 deg). The old Kp=2.0/Ki=0.4/Kd=0.5 gains
fail the margin check (PM=-0.1 deg, GM=-0.0 dB at the worst envelope point) once the loop delay is
modeled -- this script's nonlinear sim alone doesn't show that because it never modeled the
delay; the linearized margin analysis is the authoritative check.

Run as a script to print a small step-response demo.
"""
import numpy as np

class PID:
    """Numerically equivalent to firmware/gtr70e_wyvern_tvc/wyvern_pid.h (verified to 1.2e-9 rad,
    i.e. float32 rounding, over a 2000-tick pseudo-random error sequence)."""
    def __init__(self, kp, ki, kd, out_lim, tau_d=0.02, i_lim=0.4):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.lim, self.tau, self.ilim = out_lim, tau_d, i_lim
        self.i = self.d = self.prev = 0.0
        self.primed = False
        self.prev_out = 0.0

    def reset(self):
        self.i = self.d = self.prev = 0.0
        self.primed = False
        self.prev_out = 0.0

    def update(self, err, dt):
        # dt/err guard -- a skipped tick returns the last output rather than dividing by zero or
        # injecting a spike (mirrors the firmware; the 500 Hz loop can stutter on a missed sample).
        if not (dt > 0.0) or not np.isfinite(dt) or not np.isfinite(err):
            return self.prev_out
        # FIXED 2026-08: the firmware primes prev_err on the first call after a reset so the first
        # derivative term is 0 rather than a spike measured against a stale 0.0. This twin did not,
        # so tick 0 of every run produced a ~27 rad/s phantom derivative that saturated the gimbal
        # command -- a 7.7 deg disagreement with the firmware on the first sample of every study
        # that imports this class.
        if not self.primed:
            self.prev = err
            self.primed = True
        self.i = min(max(self.i + err*dt, -self.ilim), self.ilim) # integrate + anti-windup
        raw = (err - self.prev)/dt; self.prev = err
        self.d += (raw - self.d) * dt/(self.tau + dt) # filtered derivative
        u = self.kp*err + self.ki*self.i + self.kd*self.d
        u = min(max(u, -self.lim), self.lim) # output clamp
        self.prev_out = u
        return u

# flight constants for the WYVERN pitch loop -- MUST match firmware/wyvern_pid.h exactly.
# FIXED 2026-08: this was np.radians(5.0), contradicting both the firmware's OUT_LIM_DEG = 8.0 and
# this file's own docstring. The same +-5/+-8 mismatch existed in wyvern4_tvc.ino's servo write
# path. A "reference implementation" that clamps 3 deg tighter than the firmware it is supposed to
# mirror will silently under-report achievable authority in every study that imports it.
KP, KI, KD = 0.10, 0.40, 0.18
GIMBAL_LIM = np.radians(8.0)
TAU_D, I_LIM = 0.02, 0.4

if __name__ == "__main__":
    # Closed-loop step demo against the FLIGHT pitch plant (incl. fin aero restoring + damping that
    # the bare double-integrator lacks). Authoritative validation is we4_atmos_tvc.py; this is a quick
    # sanity demo: a 2° vertical-trim command settles cleanly with the gimbal well inside ±8°.
    I, T_arm, tau_s, dt = 0.0323, 14.4*0.253, 0.04, 1e-3
    C_restore, C_damp = 0.30, 0.045 # fin restoring (N·m/rad) + pitch aero damping (N·m·s/rad)
    pid = PID(KP, KI, KD, GIMBAL_LIM)
    th=w=delta=0.0; setp=np.radians(2.0); t=0.0
    print(" t(s) pitch(deg) gimbal(deg)")
    while t < 1.0:
        cmd = pid.update(setp - th, dt)
        delta += (cmd - delta)*dt/tau_s
        M = T_arm*np.sin(delta) - C_restore*th - C_damp*w
        w += (M/I)*dt; th += w*dt; t += dt
        if abs((t*1000) % 100) < 1:
            print(f"{t:5.2f} {np.degrees(th):8.2f} {np.degrees(delta):8.2f}")
