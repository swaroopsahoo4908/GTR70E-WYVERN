#!/usr/bin/env python3
"""WYVERN-E 3.0 -- parametric 3D-print generator (STL + STEP).
84 mm 2-stage Pi-5 TVC rocket (solenoid/servo) + FC/TVC bulkhead + wind-tunnel + test stand.
All-PC-FR structure; oversized fins (Cd~0.9 caps apogee)."""
import os, math, json
from wcad import (S, cyl, tube, cone, box, sphere, ogive_nose,
                  export_step, export_stl)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Pnt, gp_Vec

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # WYVERN-E 3.0 root
DIRS = {"Rocket": os.path.join(ROOT,"3D parts"),
        "WindTunnel": os.path.join(ROOT,"Wind Tunnel"),
        "TestStand": os.path.join(ROOT,"Motor Test Stand")}
for d in DIRS.values(): os.makedirs(d, exist_ok=True)

P = dict(
    OD=84.0, R=42.0, WALL=2.0, ID=80.0, RI=40.0,
    COUP_OD=79.2, COUP_RO=39.6, COUP_WALL=2.4,
    MOT_BORE=29.6, MMT_OD=33.0,
    TVC_OD=62.0, TVC_RO=31.0,                # internal TVC mechanism 62mm dia (excl. solenoids)
    FIN_ROOT=120.0, FIN_TIP=55.0, FIN_SPAN=76.0, FIN_SWEEP=70.0, FIN_THK=4.5, FIN_N=4,  # oversized (Cd~0.9)
    NOSE_L=202.0, RECOV_L=160.0, AVI_L=110.0, TVC_L=160.0, BOOST_L=244.0,
    VENT_D=3.5,
)
DENS = dict(PETGCF=1.30, ASA=1.07, PC=1.20, PCFR=1.25, PLA=1.24)  # RQ2 fin candidates: PC/PETG-CF/ASA/PLA Basic
report = []

def save(shape, folder, name, material):
    stem = os.path.join(DIRS[folder], name)
    v = shape.volume_cm3()
    export_step(shape, stem+".step"); export_stl(shape, stem+".stl")
    m = v*DENS[material]
    report.append((folder, name, round(v,1), material, round(m,1)))
    print(f"  {folder:10s}/{name:30s} {v:7.1f} cm3  ~{m:6.1f} g ({material})")
    return shape

def vent_ring(zc, n=4, d=None, r=None):
    d = d or P["VENT_D"]; r = r or P["R"]; holes=None
    for i in range(n):
        a = 360*i/n
        h = cyl(d/2,14).rotate("y",90).translate(r-7,0,zc).rotate("z",a)
        holes = h if holes is None else holes.fuse(h)
    return holes

def body_fin(root_c, tip_c, span, sweep, thk, root_r, tab=6.0):
    poly = BRepBuilderAPI_MakePolygon()
    for (x,z) in [(-tab,0),(-tab,root_c),(span,sweep+tip_c),(span,sweep)]:
        poly.Add(gp_Pnt(x,0,z))
    poly.Close()
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    pr = BRepPrimAPI_MakePrism(face, gp_Vec(0,thk,0)).Shape()
    return S(pr).translate(root_r,-thk/2,0)

def coupler(length, z=0, slot=False):
    c = tube(P["COUP_RO"], P["COUP_RO"]-P["COUP_WALL"], length, z)
    # external alignment shelf at mid
    return c

def centering_ring(z=0):
    return tube(P["RI"]+0.6, P["MMT_OD"]/2, 4.0, z)

# ---------------- ROCKET PARTS ----------------
def make_nose():
    n = ogive_nose(P["R"], P["NOSE_L"], wall=P["WALL"])
    shoulder = tube(P["COUP_RO"], P["COUP_RO"]-P["COUP_WALL"], 28).translate(0,0,-28)
    bulk = cyl(P["COUP_RO"]-1, 3).translate(0,0,-3)
    eye = (cyl(3.5,10).cut(cyl(2.0,12).translate(0,0,-1))).rotate("y",90).translate(0,0,-16)
    n = n.fuse(shoulder).fuse(bulk).fuse(eye)
    return save(n,"Rocket","01_nose_cone","ASA")

def make_recovery():
    b = tube(P["R"], P["RI"], P["RECOV_L"])
    # internal shock-cord anchor bulkhead near base
    anchor = cyl(P["RI"]-0.2,4,6).cut(cyl(P["RI"]-7,6,5))
    bar = box(P["ID"]-2,5,4,True,8).cut(cyl(2.2,12).rotate("x",90).translate(0,0,10))
    b = b.fuse(anchor).fuse(bar)
    b = b.cut(vent_ring(P["RECOV_L"]-18,4))
    # upper coupler female lip is the tube ID; add lower male coupler stub
    stub = tube(P["COUP_RO"],P["COUP_RO"]-P["COUP_WALL"],22).translate(0,0,-22)
    b = b.fuse(stub)
    return save(b,"Rocket","02_recovery_bay","PCFR")

def make_avionics():
    b = tube(P["R"], P["RI"], P["AVI_L"])
    # two PCB rail slots (diametric) Ø64 board on 1.6mm rails
    rail = box(2.2, 14, P["AVI_L"]-16, True, 8)
    railA = rail.translate(P["RI"]-1.0,0,0); railB = rail.translate(-(P["RI"]-1.0),0,0)
    b = b.fuse(railA).fuse(railB)
    # camera window 12x16 on +X
    win = box(13,18,3,True).rotate("y",90).translate(P["R"]-2,0,P["AVI_L"]/2)
    b = b.cut(win)
    # USB-C side access slot
    usb = box(13,7,4).rotate("y",90).translate(P["R"]-2,-3.5,24)
    b = b.cut(usb)
    b = b.cut(vent_ring(P["AVI_L"]-14,4))
    stub = tube(P["COUP_RO"],P["COUP_RO"]-P["COUP_WALL"],20).translate(0,0,-20)
    b = b.fuse(stub)
    return save(b,"Rocket","03_avionics_bay","PCFR")

def make_fc_mount():
    # Raspberry Pi 5 sled in the 80mm ID tube: tray + 4 standoffs at the Pi5 58x49mm hole pattern
    rt = P["RI"]-2.0
    plate = cyl(rt,3.0).cut(cyl(rt-10,4,-0.5))
    ring = tube(rt,rt-3.0,10)
    tray = plate.fuse(ring)
    for sx in (29,-29):
        for sy in (24.5,-24.5):
            so=(cyl(3.0,8).cut(cyl(1.35,9,-0.5))).translate(sx,sy,3)
            tray=tray.fuse(so)
    for s in (1,-1):                      # rail clips to tube
        tray=tray.fuse(box(6,8,10,True,0).translate(s*(rt+0.5),0,0))
    return save(tray,"Rocket","04_fc_pi5_mount","PCFR")

def make_bulkhead():
    # FC-bay / TVC-bay sealing bulkhead -- PC-FR disc, slotted only for actuator + gimbal-BNO wires
    r=P["RI"]-0.5
    d=cyl(r,4.0)
    for i in range(4):                    # 4 wire pass-through slots near the edge
        slot=box(11,4.5,7,True,0).translate(r-9,0,2).rotate("z",90*i+45)
        d=d.cut(slot)
    d=d.fuse(tube(r,r-3,7).translate(0,0,4))   # locating ring into the tube ID
    return save(d,"Rocket","04b_fc_tvc_bulkhead","PCFR")

def make_tvc_bay():
    b = tube(P["R"], P["RI"], P["TVC_L"])
    # three solenoid mounting bosses at 120 deg, upper third
    for i in range(3):
        boss = cyl(8,18).rotate("y",90).translate(P["RI"]-2,0,P["TVC_L"]-45).rotate("z",120*i)
        bore = cyl(5.2,24).rotate("y",90).translate(P["RI"]-5,0,P["TVC_L"]-45).rotate("z",120*i)
        b = b.fuse(boss).cut(bore)
    # gimbal pivot bosses (2-axis) at lower third on X and Y
    for ax in (0,90):
        pv = cyl(6,P["ID"]+4).rotate("y",90).translate(-(P["RI"]+1),0,46).rotate("z",ax)
        b = b.fuse(pv)
        b = b.cut(cyl(2.6,P["ID"]+8).rotate("y",90).translate(-(P["RI"]+4),0,46).rotate("z",ax))
    b = b.cut(vent_ring(P["TVC_L"]-12,4))
    # PDR-005: fixed fin can on the SUSTAINER (moved from booster) -- aft of the TVC bay
    finset = None
    for i in range(P["FIN_N"]):
        fi = body_fin(P["FIN_ROOT"],P["FIN_TIP"],P["FIN_SPAN"],P["FIN_SWEEP"],P["FIN_THK"],P["RI"]-6).translate(0,0,6).rotate("z",90*i)
        finset = fi if finset is None else finset.fuse(fi)
    b = b.fuse(finset)
    stub = tube(P["COUP_RO"],P["COUP_RO"]-P["COUP_WALL"],20).translate(0,0,-20)
    b = b.fuse(stub)
    return save(b,"Rocket","05_stage2_tvc_bay","PCFR")

def make_gimbal():
    # 62mm OD gimbal mechanism (excl. solenoids): inner cradle holds 29mm motor,
    # outer 62mm gimbal ring on 2-axis pivots; 3 pull-arms at 120 deg for solenoids.
    cradle = tube(17.5,14.8,76)
    flange = tube(21,14.8,5,72); cradle = cradle.fuse(flange)
    for s in (1,-1):                                  # inner X trunnions
        cradle = cradle.fuse(cyl(3.0,9).rotate("y",90).translate(s*16.5,0,32))
    ring = tube(P["TVC_RO"], P["TVC_RO"]-4, 18, 26)   # 62mm OD gimbal ring
    for s in (1,-1):                                  # outer Y trunnions
        ring = ring.fuse(cyl(3.0,9).rotate("x",90).translate(0,s*(P["TVC_RO"]-1),34))
    # spider connecting cradle to ring on X axis (bearing for inner gimbal)
    for s in (1,-1):
        spider = box(2*(P["TVC_RO"]-1),6,5,True,30).common(cyl(P["TVC_RO"]-1,40))
        ring = ring.fuse(spider)
    gimbal = cradle.fuse(ring)
    for i in range(3):                                # 3 pull-arms (solenoid plungers act here)
        arm = box(12,5,6,True,0).translate(P["TVC_RO"]-8,0,70).rotate("z",120*i)
        hole = cyl(1.8,9).translate(P["TVC_RO"]-3,0,73).rotate("z",120*i)
        gimbal = gimbal.fuse(arm).cut(hole)
    return save(gimbal,"Rocket","06_tvc_gimbal_mech","PCFR")

def make_interstage():
    c = tube(P["COUP_RO"], P["COUP_RO"]-P["COUP_WALL"], 84)
    shelf = tube(P["R"], P["COUP_RO"]-0.3, 4, 40)   # external register step
    c = c.fuse(shelf)
    # ematch / 2nd-stage igniter channel + ejection canister boss
    can = (cyl(7,16).cut(cyl(5.2,17,-0.5))).translate(0,0,4)
    c = c.fuse(can)
    chan = cyl(1.8,90).translate(20,0,-2)
    c = c.cut(chan)
    c = c.cut(vent_ring(70,3,P["VENT_D"],P["COUP_RO"]))
    return save(c,"Rocket","07_interstage_coupler","PCFR")

def make_fin():
    f = body_fin(P["FIN_ROOT"],P["FIN_TIP"],P["FIN_SPAN"],P["FIN_SWEEP"],P["FIN_THK"],0)
    return save(f,"Rocket","08_fin_single","PC")

def make_booster():
    b = tube(P["R"], P["RI"], P["BOOST_L"])
    # PDR-005: fins moved to the sustainer (stage-2 TVC bay) -- booster is now finless
    # aft motor retainer + centering rings (G78 124mm)
    b = b.fuse(centering_ring(8)).fuse(centering_ring(132))
    b = b.fuse(tube(P["MMT_OD"]/2, P["MOT_BORE"]/2, 146, 0))
    retainer = tube(P["RI"]+0.6, P["MOT_BORE"]/2-1.0, 6, 0)
    b = b.fuse(retainer)
    b = b.cut(vent_ring(P["BOOST_L"]-20,4))
    # top female coupler register
    return save(b,"Rocket","09_stage1_booster_body","PCFR")

def make_camera_pod():
    pod = cone(9,6,26).fuse(cyl(9,10))
    pod = pod.cut(cyl(5.5,40,-2))
    lens = cyl(3.5,6).rotate("y",90).translate(7,0,18)
    pod = pod.cut(lens)
    base = box(20,16,3,True)
    pod = pod.fuse(base.translate(0,0,0))
    return save(pod,"Rocket","10_camera_pod_fairing","ASA")

def make_outer_shell():
    # full external skin (visual / wind-tunnel master) nose->tail
    z=0; shell = tube(P["R"],P["R"]-1.2,P["BOOST_L"],z); z+=P["BOOST_L"]
    shell = shell.fuse(tube(P["R"],P["R"]-1.2,P["TVC_L"],z)); z+=P["TVC_L"]
    shell = shell.fuse(tube(P["R"],P["R"]-1.2,P["AVI_L"],z)); z+=P["AVI_L"]
    shell = shell.fuse(tube(P["R"],P["R"]-1.2,P["RECOV_L"],z)); z+=P["RECOV_L"]
    nose = ogive_nose(P["R"],P["NOSE_L"],wall=1.2).translate(0,0,z)
    shell = shell.fuse(nose)
    # fins
    for i in range(P["FIN_N"]):
        fi = body_fin(P["FIN_ROOT"],P["FIN_TIP"],P["FIN_SPAN"],P["FIN_SWEEP"],P["FIN_THK"],P["R"]-3).translate(0,0,6).rotate("z",90*i)
        shell = shell.fuse(fi)
    return save(shell,"Rocket","11_outer_shell_full","PCFR")

# ---------------- WIND TUNNEL ----------------
def make_wt_finmount():
    # turntable disc that seats in the Printables modular test section floor,
    # holds ONE fin upright; AoA index every 5 deg.
    base = cyl(58,8)
    base = base.cut(cyl(50,5,3))
    turn = cyl(40,10,8)
    # fin root pocket
    slot = box(P["FIN_THK"]+0.4,16,P["FIN_ROOT"]*0.6,True,12)
    turn = turn.cut(slot)
    mount = base.fuse(turn)
    # AoA index holes around rim
    for k in range(0,360,15):
        h = cyl(1.6,6).translate(46,0,2).rotate("z",k)
        mount = mount.cut(h)
    # cable/balance pass-through
    mount = mount.cut(cyl(4,30).translate(0,0,-1))
    # locating feet (clip into 120mm test-section floor 100x100)
    for sx in (1,-1):
        for sy in (1,-1):
            mount = mount.fuse(box(8,8,6,True).translate(sx*48,sy*48,0))
    return save(mount,"WindTunnel","WT_fin_test_mount","PLA")

def make_wt_fan_adapter_ref():
    # simplified 120mm fan -> 100mm tunnel transition collar (reference companion
    # to the Printables 120mm fan adapter; printable as-is)
    a = box(124,124,6,True)
    a = a.cut(cyl(58,8,-1))
    coll = tube(52,49,40,6)
    a = a.fuse(coll)
    for sx in (1,-1):
        for sy in (1,-1):
            a = a.cut(cyl(2.6,8,-1).translate(sx*55,sy*55,0))
    return save(a,"WindTunnel","WT_120mm_fan_collar","PLA")

# ---------------- TEST STAND ----------------
def make_ts_base():
    base = box(180,140,10,True)
    # four ground stakes sockets
    for sx in (1,-1):
        for sy in (1,-1):
            sock = tube(7,4,60,-50).translate(sx*78,sy*58,0)
            base = base.fuse(sock)
    # central tower mount bolt pattern
    for k in range(4):
        base = base.cut(cyl(2.6,14,-1).translate(22,0,0).rotate("z",90*k))
    return save(base,"TestStand","TS_base_plate","PCFR")

def make_ts_tower():
    # vertical motor cradle that pushes DOWN onto load cell (thrust measured)
    col = box(70,40,140,True,10)
    col = col.cut(box(50,44,150,True,8))
    cradle = tube(17.5,14.9,120,12)
    yoke = box(70,40,16,True,118)
    yoke = yoke.cut(cyl(15,20,116))
    tower = col.fuse(cradle).fuse(yoke)
    # load-cell seat at bottom (Wishiot 10kg: 80x12.7x12.7 beam pocket)
    pocket = box(82,14,14,True,-1)
    tower = tower.cut(pocket)
    for k in range(4):
        tower = tower.cut(cyl(2.6,14,8).translate(24,0,0).rotate("z",90*k))
    return save(tower,"TestStand","TS_motor_tower","PCFR")

def make_ts_loadcell_mount():
    m = box(90,30,12,True)
    # bar load cell screw pattern (M5, 2 ends)
    for s in (1,-1):
        m = m.cut(cyl(2.6,16,-1).translate(s*35,0,0))
        m = m.cut(cyl(2.6,16,-1).translate(s*23,0,0))
    return save(m,"TestStand","TS_loadcell_bracket","PCFR")

# ---------------- ASSEMBLY ----------------
def make_assembly():
    parts=[]
    z=0
    parts.append(("booster", tube(P["R"],P["RI"],P["BOOST_L"],z))); 
    z=P["BOOST_L"]
    parts.append(("inter", tube(P["COUP_RO"],P["COUP_RO"]-2,40,z-20)))
    parts.append(("tvc", tube(P["R"],P["RI"],P["TVC_L"],z)))
    z+=P["TVC_L"]
    parts.append(("avi", tube(P["R"],P["RI"],P["AVI_L"],z))); z+=P["AVI_L"]
    parts.append(("recov", tube(P["R"],P["RI"],P["RECOV_L"],z))); z+=P["RECOV_L"]
    parts.append(("nose", ogive_nose(P["R"],P["NOSE_L"],wall=P["WALL"]).translate(0,0,z)))
    asm = parts[0][1]
    for _,p in parts[1:]: asm = asm.fuse(p)
    for i in range(P["FIN_N"]):                       # PDR-005: fins on the sustainer (aft of TVC bay)
        fi = body_fin(P["FIN_ROOT"],P["FIN_TIP"],P["FIN_SPAN"],P["FIN_SWEEP"],P["FIN_THK"],P["RI"]-4).translate(0,0,P["BOOST_L"]+6).rotate("z",90*i)
        asm = asm.fuse(fi)
    total_len = z + P["NOSE_L"]
    print(f"  [assembly total length = {total_len:.0f} mm]")
    return save(asm,"Rocket","00_full_assembly","PCFR")

if __name__ == "__main__":
    print("== ROCKET ==")
    make_nose(); make_recovery(); make_avionics(); make_fc_mount(); make_bulkhead()
    make_tvc_bay(); make_gimbal(); make_interstage(); make_fin()
    make_booster(); make_camera_pod(); make_outer_shell()
    print("== WIND TUNNEL =="); make_wt_finmount(); make_wt_fan_adapter_ref()
    print("== TEST STAND =="); make_ts_base(); make_ts_tower(); make_ts_loadcell_mount()
    print("== ASSEMBLY =="); make_assembly()
    with open(os.path.join(os.path.dirname(__file__),"mass_report.json"),"w") as f:
        json.dump(report,f,indent=1)
    tot=sum(r[4] for r in report if r[0]=="Rocket" and not r[1].startswith(("11_","00_")))
    print(f"\nFlight-article printed mass (excl. shell/asm dupes): ~{tot:.0f} g")
    print(f"parts written: {len(report)}")
