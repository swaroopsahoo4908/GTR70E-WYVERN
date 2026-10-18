#!/usr/bin/env python3
"""GTR70E WYVERN -- SimScale CFD package: geometry for every case, the model's predictions to
compare against, and a manifest. The setup itself is in SIMSCALE_SETUP.md next to this file.

The SimScale Community plan allows 10 unrestricted simulations, so the matrix is exactly ten:
  A1-A4  Phase A tunnel: one NACA0006 H40 fin on the reflection plate, delta = 0 / 5 / 10 / 15 deg, 12 m/s
  A5-A7  Phase A tunnel at delta = 10 deg: double wedge, NACA0012, flat plate          (RQ1 profiles)
  R1     full rocket, alpha 0, pitch pair at +10 deg, stabilizers on, 60 m/s           (installed authority)
  R2     as R1 with the stabilizers removed                                            (SQ1 increment)
  R3     full rocket, alpha 4 deg, fins neutral, 60 m/s                                (normal-force slope, CP)

For every case two geometries are written (mm, STEP + STL):
  <case>_fluid.step   the flow region, ready to use as uploaded (a box / duct with the body cut out)
  <case>_solids.step  the solid bodies only (to build the flow region in SimScale's CAD Edit instead)
plus per-part STLs of the solids so the force groups are easy to identify.

Coordinates. Tunnel cases: flow along +X, the reflection plate is the wall y = 0, the hinge line is
the Y axis (x = 0, z = 0), the duct is y 0..100, z -50..50. Rocket cases: the CAD frame (+Z along the
axis, nose up, z = L - station), flow along -Z, CG on the axis at z = L - x_cg.

    python3 gen_simscale.py            (about 1-2 minutes; needs cadquery)
"""
from __future__ import annotations
import csv, json, math, os, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
CFD = os.path.dirname(HERE)
SIM = os.path.dirname(CFD)
for p in (SIM, CFD, os.path.join(SIM, "wyvern_finsim")):
    if p not in sys.path: sys.path.insert(0, p)
import wf_core as C                                   # noqa: E402
from airfoil_profiles import section_points           # noqa: E402

OUT = os.path.join(HERE, "geometry"); os.makedirs(OUT, exist_ok=True)
CF = C.CFIN; c_root = CF["root"]; hf = CF["hinge_frac"]
V_TUNNEL, V_FLIGHT, RHO = 12.0, 60.0, 1.204
DUCT = dict(x0=-250.0, x1=600.0, y1=100.0, zh=50.0)
H_A = 40.0

# --------------------------------------------------------------------------------- fin solids
def fin_local(profile, H, tip_min=4.0, spans=(0.0, 0.25, 0.5, 0.75, 0.93)):
    """Triangular control fin in a local frame: chord along +X (flow), span along +Y from the
    root (y = 0), hinge at x = 0 (45 % of the root chord behind the LE), straight trailing edge."""
    x_te = (1 - hf) * c_root
    wires = []
    for f in spans:
        cl = max(c_root * (1 - f), tip_min)
        pts = section_points(profile, cl, n=36)
        pl = cq.Plane(origin=(x_te - cl, f * H, 0), xDir=(1, 0, 0), normal=(0, 1, 0))
        w = cq.Workplane(pl).polyline(pts).close().val()
        wires.append(w if isinstance(w, cq.Wire) else cq.Wire.assembleEdges(w.Edges()))
    return cq.Workplane("XY").add(cq.Solid.makeLoft(wires, True))

def tunnel_case(profile, delta):
    """Fin on the plate: root 1.0 mm off the wall, joined to it by the 8 mm hub, rotated about the
    hinge (Y axis). +delta turns the leading edge toward +Z, so the fin's normal force is +Z."""
    fin = fin_local(profile, H_A).translate((0, CF["gap"], 0))
    hub = cq.Workplane("XZ").circle(CF["hub_d"] / 2).extrude(-(CF["gap"] + 4.0)).translate((0, -1.0, 0))
    body = fin.union(hub).rotate((0, 0, 0), (0, 1, 0), delta)
    duct = cq.Workplane("XY").box(DUCT["x1"] - DUCT["x0"], DUCT["y1"], 2 * DUCT["zh"], centered=(False, False, True)).translate((DUCT["x0"], 0, 0))
    return duct.cut(body), {"fin_and_hub": body}

# --------------------------------------------------------------------------------- rocket solids
L = C.L_TOTAL
def zx(x): return L - x

def rocket_parts(delta_A=0.0, stabilizers=True):
    R = C.R; Ln = C.NOSE["L"]; rho = (R * R + Ln * Ln) / (2 * R)
    prof = [(0.0, zx(0.0))]
    for i in range(1, 61):
        xx = Ln * i / 60
        prof.append((math.sqrt(max(rho * rho - (Ln - xx) ** 2, 0)) + R - rho, zx(xx)))
    prof += [(R, 0.0), (0.0, 0.0)]
    body = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    parts = {"body": body}
    zh = zx(C.X_HINGE); r_root = R + CF["gap"]
    for az in (0, 90, 180, 270):
        # local fin: chord +X, span +Y  ->  rocket: chord -Z, span radial (+X at az 0)
        f = fin_local("NACA0006", C.CFIN_H_NOMINAL)
        hub = cq.Workplane("XZ").circle(CF["hub_d"] / 2).extrude(-(CF["gap"] + 5.0)).translate((0, -2.0, 0))
        f = f.union(hub)
        # same-direction normal force on both fins of the pitch pair (fin_mixer.h: fin0 = fin1 = +u_a,
        # mirrored servo mounting): the az 180 fin turns the other way before it is spun round
        d = delta_A if az == 0 else (-delta_A if az == 180 else 0.0)
        f = f.rotate((0, 0, 0), (0, 1, 0), d)                    # deflect about the span (hinge) axis
        f = f.rotate((0, 0, 0), (0, 0, 1), -90)                   # span +Y -> +X ; chord +X -> -Y
        f = f.rotate((0, 0, 0), (1, 0, 0), 90)                    # chord -Y -> -Z
        f = f.translate((r_root, 0, zh)).rotate((0, 0, 0), (0, 0, 1), az)
        parts[f"cfin_az{az}"] = f
    if stabilizers:
        rf = C.RECT_FIN; zt = zx(C.X_RECT_LE)
        for i in range(4):
            az = rf["az0_deg"] + 90 * i
            s = (cq.Workplane("XY").box(rf["span"] + 2.0, rf["t"], rf["root"]).edges("|Y").fillet(0.6)
                 .translate((R - 2.0 + (rf["span"] + 2.0) / 2, 0, zt - rf["root"] / 2)).rotate((0, 0, 0), (0, 0, 1), az))
            parts[f"stab_az{int(az)}"] = s
    return parts

def rocket_case(delta_A=0.0, stabilizers=True, alpha=0.0, cg_z=None):
    parts = rocket_parts(delta_A, stabilizers)
    u = None
    for k, p in parts.items(): u = p if u is None else u.union(p)
    if alpha:
        u = u.rotate((0, 0, cg_z), (0, 1, 0), alpha)
        parts = {k: p.rotate((0, 0, cg_z), (0, 1, 0), alpha) for k, p in parts.items()}
    box = cq.Workplane("XY").box(1000, 1000, L + 2500, centered=(True, True, False)).translate((0, 0, -1800))
    return box.cut(u), parts

def export(case, fluid, parts):
    cq.exporters.export(fluid, os.path.join(OUT, f"{case}_fluid.step"))
    cq.exporters.export(fluid, os.path.join(OUT, f"{case}_fluid.stl"), tolerance=0.05, angularTolerance=0.15)
    asm = cq.Assembly()
    for k, p in parts.items():
        asm.add(p, name=k)
        cq.exporters.export(p, os.path.join(OUT, f"{case}_part_{k}.stl"), tolerance=0.02, angularTolerance=0.1)
    asm.save(os.path.join(OUT, f"{case}_solids.step"))
    v = fluid.val().Volume() / 1e9
    print(f"  {case}: fluid {v * 1000:.2f} L, {len(fluid.val().Faces())} faces, parts {list(parts)}")

# --------------------------------------------------------------------------------- predictions
def predictions():
    import bench
    rows = []
    for case, prof, d in (("A1", "NACA0006", 0), ("A2", "NACA0006", 5), ("A3", "NACA0006", 10), ("A4", "NACA0006", 15),
                          ("A5", "double_wedge", 10), ("A6", "NACA0012", 10), ("A7", "flat_plate", 10)):
        m = bench.fin_model(prof, H_A)
        try: bl, _ = C.bl_effectiveness(H_A, bench.X_PLATE_A, V_TUNNEL)
        except Exception: bl = 1.0
        N = bench.fin_force(m, d, V_TUNNEL) * bl
        rows.append(dict(case=case, what=f"{prof} H{H_A:.0f} delta {d} deg, {V_TUNNEL:.0f} m/s, one fin on the plate",
                         force_N=round(N, 5), quantity="fin normal force Fz (fin + hub faces)",
                         moment_Nm=round(N * m["x_cp_mm"] / 1000, 6), moment_about="hinge axis (Y) at the origin",
                         cp_mm_aft_of_hinge=round(m["x_cp_mm"], 2), q_Pa=round(0.5 * RHO * V_TUNNEL ** 2, 1),
                         ref_area_m2=round(c_root * H_A / 2 * 1e-6, 7), note="potential-flow model + Polhamus vortex lift; no stall"))
    # rocket cases from the flight-sim vehicle
    import wf_flightsim as F
    veh = F.Vehicle(C.FLIGHT_MOTOR); q = 0.5 * RHO * V_FLIGHT ** 2; A = C.A_REF; cg = veh.cg0
    bl, _ = C.bl_effectiveness(veh.H, veh.x_cA / 1000, V_FLIGHT)
    d = math.radians(10)
    f_pair = q * A * 2 * veh.cna_1 * veh.k_defl * bl * d
    m_pair = f_pair * (veh.x_cA - cg) / 1000
    f_int = veh.interf * f_pair; m_int = f_int * (veh.x_r - cg) / 1000
    rows.append(dict(case="R1", what="full rocket, alpha 0, pitch pair (az 0/180) at +10 deg, stabilizers on, 60 m/s",
                     force_N=round(f_pair + f_int, 4), quantity="side force on the whole rocket (pair + vortex load on the stabilizers)",
                     moment_Nm=round(m_pair + m_int, 5), moment_about=f"CG, station {cg:.1f} mm (z = {L - cg:.1f})",
                     cp_mm_aft_of_hinge="", q_Pa=round(q, 1), ref_area_m2=round(A, 7),
                     note=f"pair alone {f_pair:.3f} N; stabilizer interference {f_int:+.3f} N (ratio {veh.interf:+.3f}); K_W(B) {veh.k_defl:.3f}, BL {bl:.3f}"))
    rows.append(dict(case="R2", what="as R1, stabilizers removed", force_N=round(f_pair, 4), quantity="side force on the whole rocket",
                     moment_Nm=round(m_pair, 5), moment_about=f"CG, station {cg:.1f} mm", cp_mm_aft_of_hinge="", q_Pa=round(q, 1),
                     ref_area_m2=round(A, 7), note="R1 minus R2 isolates the stabilizer vortex load (SQ1)"))
    st = C.stability(cg); a = math.radians(4)
    rows.append(dict(case="R3", what="full rocket, alpha 4 deg (pitched about the CG), fins neutral, 60 m/s",
                     force_N=round(q * A * st["cna"] * a, 4), quantity="normal force on the whole rocket",
                     moment_Nm=round(-q * A * st["cna"] * a * (st["xcp"] - cg) / 1000, 5), moment_about=f"CG (restoring)",
                     cp_mm_aft_of_hinge="", q_Pa=round(q, 1), ref_area_m2=round(A, 7),
                     note=f"CN_alpha {st['cna']:.2f} /rad, CP station {st['xcp']:.1f} mm, margin {st['margin_cal']:.2f} cal (Barrowman + K_W(B) + interference)"))
    with open(os.path.join(HERE, "predictions.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows, dict(cg_station_mm=round(cg, 1), cg_z_mm=round(L - cg, 1), A_ref_m2=A, L_total_mm=L, D_mm=C.OD)

if __name__ == "__main__":
    rows, ref = predictions()
    print("predictions:"); [print("  ", r["case"], r["force_N"], r["moment_Nm"]) for r in rows]
    for case, prof, d in (("A1", "NACA0006", 0), ("A2", "NACA0006", 5), ("A3", "NACA0006", 10), ("A4", "NACA0006", 15),
                          ("A5", "double_wedge", 10), ("A6", "NACA0012", 10), ("A7", "flat_plate", 10)):
        fl, parts = tunnel_case(prof, d); export(case, fl, parts)
    cg_z = ref["cg_z_mm"]
    for case, kw in (("R1", dict(delta_A=10.0)), ("R2", dict(delta_A=10.0, stabilizers=False)), ("R3", dict(alpha=4.0, cg_z=cg_z))):
        fl, parts = rocket_case(**kw); export(case, fl, parts)
    json.dump(dict(reference=ref, cases=[r["case"] for r in rows], v_tunnel=V_TUNNEL, v_flight=V_FLIGHT, rho=RHO,
                   duct=DUCT, rocket_domain_mm=dict(x=(-500, 500), y=(-500, 500), z=(-1800, L + 700))),
              open(os.path.join(HERE, "manifest.json"), "w"), indent=1)
    print("wrote", OUT)
