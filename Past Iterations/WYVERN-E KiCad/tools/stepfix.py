import re,json,glob,os
import cadquery as cq
SH='/tmp/w/m3d/lib.3dshapes'
out={}
for w in sorted(glob.glob(f'{SH}/*.wrl')):
    st=w[:-4]+'.step'
    if not os.path.exists(st): continue
    s=open(w).read(); pts=[]
    for blk in re.findall(r'point \[(.*?)\]',s,re.S):
        n=[float(v) for v in re.findall(r'-?[\d.]+(?:e-?\d+)?',blk)]; pts+=[n[i:i+3] for i in range(0,len(n)-2,3)]
    wx=[(min(p[0] for p in pts)+max(p[0] for p in pts))/2*2.54,(min(p[1] for p in pts)+max(p[1] for p in pts))/2*2.54,min(p[2] for p in pts)*2.54]
    bb=cq.importers.importStep(st).val().BoundingBox()
    sx=[(bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,bb.zmin]
    d=[round(wx[i]-sx[i],3) for i in range(3)]
    out[os.path.basename(st)]=d
    if max(abs(v) for v in d)>0.05: print(os.path.basename(st),d, 'wrl',[round(v,2) for v in wx],'step',[round(v,2) for v in sx])
json.dump(out,open('/tmp/w/m3d/stepfix.json','w'),indent=1)
