import pcbnew
from shapely.geometry import box
from shapely.strtree import STRtree
from pcbbuild import V,MM
import autoplace
TOMM=pcbnew.ToMM
def place_refs(b,center=(100,100),R=33,size=0.7):
    import math
    pads={pcbnew.F_SilkS:[],pcbnew.B_SilkS:[]}
    for f in b.Footprints():
        for p in f.Pads():
            bb=p.GetBoundingBox(); g=box(TOMM(bb.GetLeft()),TOMM(bb.GetTop()),TOMM(bb.GetRight()),TOMM(bb.GetBottom())).buffer(0.15)
            if p.IsOnLayer(pcbnew.F_Cu) or p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD: pads[pcbnew.F_SilkS].append(g)
            if p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD: pads[pcbnew.B_SilkS].append(g)
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA':
            x,y=TOMM(t.GetPosition().x),TOMM(t.GetPosition().y); r=TOMM(t.GetWidth(pcbnew.F_Cu))/2+0.1
            for L in pads: pads[L].append(box(x-r,y-r,x+r,y+r))
    placed={pcbnew.F_SilkS:[],pcbnew.B_SilkS:[]}
    # existing silk graphics of footprints
    for f in b.Footprints():
        for it in f.GraphicalItems():
            if it.GetLayer() in placed and it.GetClass()!='PCB_FIELD':
                bb=it.GetBoundingBox(); placed[it.GetLayer()].append(box(TOMM(bb.GetLeft()),TOMM(bb.GetTop()),TOMM(bb.GetRight()),TOMM(bb.GetBottom())))
    for d in b.GetDrawings():
        if d.GetLayer() in placed:
            bb=d.GetBoundingBox(); placed[d.GetLayer()].append(box(TOMM(bb.GetLeft()),TOMM(bb.GetTop()),TOMM(bb.GetRight()),TOMM(bb.GetBottom())))
    moved=0;fab=0
    fps=sorted(b.Footprints(),key=lambda f:-autoplace.rect_of(f)[2]+autoplace.rect_of(f)[0])
    for f in fps:
        if f.GetReference().startswith('MH'): continue
        rf=f.Reference(); bot=f.GetLayer()==pcbnew.B_Cu
        L=pcbnew.B_SilkS if bot else pcbnew.F_SilkS
        rf.SetLayer(L); rf.SetTextSize(V(size,size)); rf.SetTextThickness(MM(0.12)); rf.SetKeepUpright(True); rf.SetTextAngleDegrees(0)
        x0,y0,x1,y1=autoplace.rect_of(f)
        cx,cy=(x0+x1)/2,(y0+y1)/2
        tw=len(rf.GetText())*size*0.75+0.2; th=size+0.2
        cands=[(cx,y0-th/2-0.05),(cx,y1+th/2+0.05),(x0-tw/2-0.05,cy),(x1+tw/2+0.05,cy)]
        cands+=[(cx+dx,cy+dy) for dx in (-1.5,0,1.5) for dy in (-(y1-y0)/2-th,(y1-y0)/2+th)]
        tp=STRtree(pads[L]+placed[L]) if pads[L]+placed[L] else None
        allg=pads[L]+placed[L]
        ok=None
        for (x,y) in cands:
            g=box(x-tw/2,y-th/2,x+tw/2,y+th/2)
            if math.hypot(x-center[0],y-center[1])>R-1.2-tw/2: continue
            if tp is not None and any(g.intersects(allg[j]) for j in tp.query(g)): continue
            ok=(x,y,g);break
        if ok:
            rf.SetPosition(V(ok[0],ok[1])); placed[L].append(ok[2]); moved+=1
        else:
            rf.SetLayer(pcbnew.B_Fab if bot else pcbnew.F_Fab); rf.SetPosition(V(cx,cy)); fab+=1
    return moved,fab
