#!/usr/bin/env python3
"""
wcad.py -- WYVERN-E 2.0 thin CAD helper over the OpenCASCADE (OCP) kernel.
Exports both STEP (B-rep, CAD-editable) and STL (mesh, printable) from one solid.
All units mm. +Z is the rocket long axis (nose up).
"""
import math
from OCP.BRepPrimAPI import (BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeBox, BRepPrimAPI_MakeSphere, BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeRevol)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import (BRepBuilderAPI_Transform, BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon)
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.gp import gp_Pnt, gp_Ax1, gp_Ax2, gp_Dir, gp_Trsf, gp_Vec, gp_Pln
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.Interface import Interface_Static
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

class S:
    def __init__(self, shape): self.shape = shape
    def translate(self, x=0, y=0, z=0):
        t = gp_Trsf(); t.SetTranslation(gp_Vec(x, y, z))
        return S(BRepBuilderAPI_Transform(self.shape, t, True).Shape())
    def rotate(self, axis, deg, origin=(0,0,0)):
        ax = {"x":gp_Dir(1,0,0),"y":gp_Dir(0,1,0),"z":gp_Dir(0,0,1)}[axis]
        t = gp_Trsf(); t.SetRotation(gp_Ax1(gp_Pnt(*origin), ax), math.radians(deg))
        return S(BRepBuilderAPI_Transform(self.shape, t, True).Shape())
    def cut(self, o):    return S(BRepAlgoAPI_Cut(self.shape, o.shape).Shape())
    def fuse(self, o):   return S(BRepAlgoAPI_Fuse(self.shape, o.shape).Shape())
    def common(self, o): return S(BRepAlgoAPI_Common(self.shape, o.shape).Shape())
    def fillet_all(self, r):
        try:
            mk = BRepFilletAPI_MakeFillet(self.shape)
            exp = TopExp_Explorer(self.shape, TopAbs_EDGE)
            while exp.More(): mk.Add(r, exp.Current()); exp.Next()
            return S(mk.Shape())
        except Exception: return self
    def volume_cm3(self):
        p = GProp_GProps(); BRepGProp.VolumeProperties_s(self.shape, p)
        return p.Mass()/1000.0

def cyl(r, h, z=0):
    return S(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,0,z), gp_Dir(0,0,1)), r, h).Shape())
def tube(ro, ri, h, z=0):
    return cyl(ro, h, z).cut(cyl(ri, h+2, z-1))
def cone(rb, rt, h, z=0):
    return S(BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,0,z), gp_Dir(0,0,1)), rb, rt, h).Shape())
def box(dx, dy, dz, center_xy=True, z=0):
    return S(BRepPrimAPI_MakeBox(gp_Pnt(-dx/2 if center_xy else 0,
        -dy/2 if center_xy else 0, z), dx, dy, dz).Shape())
def sphere(r, z=0):
    return S(BRepPrimAPI_MakeSphere(gp_Pnt(0,0,z), r).Shape())

def _revolve(pts, z, wall):
    def build(profile):
        poly = BRepBuilderAPI_MakePolygon()
        for (r,x) in profile: poly.Add(gp_Pnt(r,0,z+x))
        poly.Close()
        face = BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,0,0), gp_Dir(0,1,0)), poly.Wire()).Face()
        return S(BRepPrimAPI_MakeRevol(face, gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1))).Shape())
    outer = [(0.0, pts[0][1])] + pts + [(0.0, pts[-1][1])]
    solid = build(outer)
    if wall:
        ip = [(max(r-wall,0.0), x) for (r,x) in pts]
        solid = solid.cut(build([(0.0, ip[0][1])] + ip + [(0.0, ip[-1][1])]))
    return solid

def ogive_nose(base_r, length, wall=None, z=0):
    R, L = base_r, length
    rho = (R**2 + L**2)/(2*R); n = 60; pts = []
    for i in range(n+1):
        x = L*i/n; xt = L - x
        y = math.sqrt(max(rho**2 - (L - xt)**2, 0.0)) + R - rho
        pts.append((max(y,0.0), x))
    return _revolve(pts, z, wall)

def fin(root_chord, tip_chord, span, sweep, thickness):
    p = [(0,0),(root_chord,0),(sweep+tip_chord,span),(sweep,span)]
    poly = BRepBuilderAPI_MakePolygon()
    for (x,zz) in p: poly.Add(gp_Pnt(x,0,zz))
    poly.Close()
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    pr = BRepPrimAPI_MakePrism(face, gp_Vec(0, thickness, 0)).Shape()
    return S(pr).translate(0, -thickness/2, 0)

def export_step(shapes, path):
    Interface_Static.SetCVal_s("write.step.unit","MM")
    w = STEPControl_Writer()
    if isinstance(shapes, S): shapes = [shapes]
    for sh in shapes: w.Transfer(sh.shape, STEPControl_AsIs)
    w.Write(path)
def export_stl(shape, path, lin=0.20, ang=0.4):
    BRepMesh_IncrementalMesh(shape.shape, lin, False, ang, True)
    sw = StlAPI_Writer(); sw.ASCIIMode = False; sw.Write(shape.shape, path)
def export_both(shape, stem):
    export_step(shape, stem + ".step"); export_stl(shape, stem + ".stl")
    return shape.volume_cm3()
