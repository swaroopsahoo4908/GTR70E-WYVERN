import re,sys
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace,BRepBuilderAPI_Sewing
from OCP.gp import gp_Pnt
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
asm=cq.Assembly()
for i,shp in enumerate(re.findall(r'Shape\{(.*?)\n\}',s,re.S)):
    col=[float(v) for v in re.search(r'diffuseColor ([\d.]+) ([\d.]+) ([\d.]+)',shp).groups()]
    nums=[float(v) for v in re.findall(r'-?[\d.]+(?:e-?\d+)?',re.search(r'point \[(.*?)\]',shp,re.S).group(1))]
    P=[(nums[k]*2.54,nums[k+1]*2.54,nums[k+2]*2.54) for k in range(0,len(nums)-2,3)]
    idx=[int(v) for v in re.findall(r'-?\d+',re.search(r'coordIndex \[(.*?)\]',shp,re.S).group(1))]
    faces=[];cur=[]
    for v in idx:
        if v<0:
            if len(cur)>=3: faces.append(cur)
            cur=[]
        else: cur.append(v)
    sew=BRepBuilderAPI_Sewing(1e-4)
    for fc in faces:
        poly=BRepBuilderAPI_MakePolygon()
        for v in fc: poly.Add(gp_Pnt(*P[v]))
        poly.Close()
        mf=BRepBuilderAPI_MakeFace(poly.Wire(),True)
        if mf.IsDone(): sew.Add(mf.Face())
    sew.Perform()
    asm.add(cq.Shape.cast(sew.SewedShape()),name=f's{i}',color=cq.Color(*col))
asm.save(dst)
print('ok',dst)
