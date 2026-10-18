"""Silkscreen clean-up for JLC: refs 1.0 mm / 0.15 mm (JLC min legend), no silk on pads (0.15 mm),
no overlapping legends, values moved to Fab. Usage: python3 silk2.py board.kicad_pcb [cx cy R]"""
import sys,math,pcbnew
from shapely.geometry import box,LineString,Point,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
T=pcbnew.ToMM; M=pcbnew.FromMM
def V(x,y): return pcbnew.VECTOR2I(M(x),M(y))
PAD_CLR=0.15      # JLC pad-to-silkscreen
def pad_geoms(b,side):
    out=[]
    cu=pcbnew.F_Cu if side=='F' else pcbnew.B_Cu
    for f in b.GetFootprints():
        for p in f.Pads():
            if not (p.IsOnLayer(cu) or p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD): continue
            ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,cu if p.IsOnLayer(cu) else pcbnew.F_Cu,0,M(0.01),pcbnew.ERROR_INSIDE)
            for i in range(ps.OutlineCount()):
                o=ps.Outline(i); pts=[(T(o.CPoint(k).x),T(o.CPoint(k).y)) for k in range(o.PointCount())]
                if len(pts)>2: out.append(Polygon(pts).buffer(0))
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH,pcbnew.PAD_ATTRIB_PTH):
                out.append(Point(T(p.GetPosition().x),T(p.GetPosition().y)).buffer(T(max(p.GetDrillSizeX(),p.GetDrillSizeY()))/2))
    return out
def clip_footprint_silk(b,padsF,padsB,own_only=False):
    """split silk lines around pads, drop small silk shapes that sit on pads"""
    nclip=ndrop=0
    for side,pads in (('F',padsF),('B',padsB)):
        tree0=STRtree(pads)
        L=pcbnew.F_SilkS if side=='F' else pcbnew.B_SilkS
        for f in b.GetFootprints():
            if own_only:
                pads=[]
                cu=pcbnew.F_Cu if side=='F' else pcbnew.B_Cu
                for p in f.Pads():
                    ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu,0,M(0.01),pcbnew.ERROR_INSIDE)
                    for i in range(ps.OutlineCount()):
                        o=ps.Outline(i); pts=[(T(o.CPoint(k).x),T(o.CPoint(k).y)) for k in range(o.PointCount())]
                        if len(pts)>2: pads.append(Polygon(pts).buffer(0))
                    if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH,pcbnew.PAD_ATTRIB_PTH):
                        pads.append(Point(T(p.GetPosition().x),T(p.GetPosition().y)).buffer(T(max(p.GetDrillSizeX(),p.GetDrillSizeY()))/2))
                if not pads: continue
                tree=STRtree(pads)
            else: tree=tree0
            for g in list(f.GraphicalItems()):
                if g.GetLayer()!=L or g.GetClass()!='PCB_SHAPE': continue
                w=T(g.GetWidth()); sh=g.GetShape()
                if sh==pcbnew.SHAPE_T_SEGMENT:
                    s,e=g.GetStart(),g.GetEnd(); ln=LineString([(T(s.x),T(s.y)),(T(e.x),T(e.y))])
                    hit=[pads[i] for i in tree.query(ln.buffer(w/2+PAD_CLR)) if pads[i].distance(ln)<w/2+PAD_CLR]
                    if not hit: continue
                    rest=ln.difference(unary_union(hit).buffer(w/2+PAD_CLR,8))
                    parts=[rest] if rest.geom_type=='LineString' else list(getattr(rest,'geoms',[]))
                    parts=[p for p in parts if p.geom_type=='LineString' and p.length>=0.3]
                    for p in parts:
                        n=pcbnew.PCB_SHAPE(f); n.SetShape(pcbnew.SHAPE_T_SEGMENT); n.SetLayer(L); n.SetWidth(g.GetWidth())
                        c=list(p.coords); n.SetStart(V(*c[0])); n.SetEnd(V(*c[-1])); f.Add(n)
                    f.Delete(g); nclip+=1
                else:
                    bb=g.GetBoundingBox(); gb=box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
                    if sh in (pcbnew.SHAPE_T_CIRCLE,pcbnew.SHAPE_T_ARC):
                        c=g.GetCenter(); r=T(g.GetRadius())
                        geom=Point(T(c.x),T(c.y)).buffer(r+w/2).exterior.buffer(w/2) if sh==pcbnew.SHAPE_T_CIRCLE and not g.IsSolidFill() else Point(T(c.x),T(c.y)).buffer(r+w/2)
                        if sh==pcbnew.SHAPE_T_ARC: geom=gb
                    else: geom=gb
                    if any(pads[i].distance(geom)<PAD_CLR for i in tree.query(geom.buffer(PAD_CLR))):
                        f.Delete(g); ndrop+=1
    return nclip,ndrop
def place_refs(b,center,R,size=1.0,thick=0.15,min_size=0.8):
    obst={pcbnew.F_SilkS:[],pcbnew.B_SilkS:[]}
    for side,L in (('F',pcbnew.F_SilkS),('B',pcbnew.B_SilkS)):
        obst[L]+=[g.buffer(PAD_CLR) for g in pad_geoms(b,side)]
    holes=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                holes.append(Point(T(p.GetPosition().x),T(p.GetPosition().y)).buffer(T(p.GetDrillSizeX())/2+0.3))
    for L in obst: obst[L]+=holes
    for f in b.GetFootprints():
        for g in f.GraphicalItems():
            if g.GetLayer() in obst and g.GetClass()=='PCB_SHAPE':
                bb=g.GetBoundingBox(); w=T(g.GetWidth())/2
                if g.GetShape()==pcbnew.SHAPE_T_SEGMENT:
                    s,e=g.GetStart(),g.GetEnd(); obst[g.GetLayer()].append(LineString([(T(s.x),T(s.y)),(T(e.x),T(e.y))]).buffer(w+0.1))
                else: obst[g.GetLayer()].append(box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom())).buffer(0.1))
    for d in b.GetDrawings():
        if d.GetLayer() in obst:
            bb=d.GetBoundingBox(); obst[d.GetLayer()].append(box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom())).buffer(0.15))
    edge=Point(*center).buffer(R-0.6,128)
    def crt(f):
        bb=None
        for lay in (pcbnew.F_CrtYd,pcbnew.B_CrtYd):
            ps=f.GetCourtyard(lay)
            if ps.OutlineCount():
                x=ps.BBox(); bb=x if bb is None else bb.Merge(x) or bb
        if bb is None: bb=f.GetBoundingBox(False)
        return (T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
    stats={'silk':0,'small':0,'fab':0}
    fps=sorted([f for f in b.GetFootprints() if not f.GetReference().startswith(('MH','TP'))],key=lambda f:(crt(f)[2]-crt(f)[0])*(crt(f)[3]-crt(f)[1]),reverse=True)
    for f in fps:
        bot=f.GetLayer()==pcbnew.B_Cu; L=pcbnew.B_SilkS if bot else pcbnew.F_SilkS
        v=f.Value(); v.SetLayer(pcbnew.B_Fab if bot else pcbnew.F_Fab); v.SetVisible(False)
        rf=f.Reference(); txt=rf.GetText()
        x0,y0,x1,y1=crt(f); cx,cy=(x0+x1)/2,(y0+y1)/2
        mine=[]
        for o in b.GetFootprints():
            if o.GetReference()==f.GetReference() or o.GetReference().startswith('MH'): continue
            if (o.GetLayer()==pcbnew.B_Cu)!=bot: continue
            a0,b0,a1,b1=crt(o); mine.append(box(a0+0.15,b0+0.15,a1-0.15,b1-0.15))
        og=obst[L]+mine; tree=STRtree(og)
        ownb=box(x0,y0,x1,y1)
        others=[(o.GetReference(),box(*crt(o))) for o in b.GetFootprints() if o.GetReference()!=f.GetReference() and not o.GetReference().startswith(('MH','TP')) and (o.GetLayer()==pcbnew.B_Cu)==bot]
        otree=STRtree([q for _,q in others])
        def unambiguous(g):
            dm=g.distance(ownb)
            if dm>0.9: return False
            for j in otree.query(g.buffer(dm+0.6)):
                if others[j][1].distance(g)<dm+0.6: return False
            return True
        done=None
        rf.SetLayer(L); rf.SetVisible(True); rf.SetKeepUpright(True); rf.SetMirrored(bot)
        rf.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); rf.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        def tbox():
            bb=rf.GetBoundingBox(); return box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
        for sz in (size,min_size):
            rf.SetTextSize(V(sz,sz)); rf.SetTextThickness(M(thick))
            for ang in (0,90):
                rf.SetTextAngleDegrees(ang); rf.SetPosition(V(0,0)); g0=tbox()
                W,H=g0.bounds[2]-g0.bounds[0],g0.bounds[3]-g0.bounds[1]
                cands=[(cx,y0-H/2-0.1),(cx,y1+H/2+0.1),(x0-W/2-0.1,cy),(x1+W/2+0.1,cy),
                       (x0-W/2-0.1,y0-H/2-0.1),(x1+W/2+0.1,y0-H/2-0.1),(x0-W/2-0.1,y1+H/2+0.1),(x1+W/2+0.1,y1+H/2+0.1)]
                if (x1-x0)>W+1.0 and (y1-y0)>H+1.0:
                    inner=[(cx+fx*(x1-x0-W)/2*0.9,cy+fy*(y1-y0-H)/2*0.9) for fy in (0,-1,1,-0.5,0.5,-0.7,0.7,-0.3,0.3) for fx in (0,-1,1,-0.5,0.5,-0.7,0.7,-0.3,0.3)]
                    cands=inner+cands
                for d in (0.4,0.7):
                    cands+=[(cx,y0-H/2-d),(cx,y1+H/2+d),(x0-W/2-d,cy),(x1+W/2+d,cy)]
                for (x,y) in cands:
                    rf.SetPosition(V(x,y)); g=tbox()
                    if not edge.contains(g): continue
                    if any(g.intersects(og[j]) for j in tree.query(g)): continue
                    if not unambiguous(g): continue
                    done=(x,y,g,sz,ang); break
                if done: break
            if done: break
        if done:
            x,y,g,sz,ang=done
            rf.SetTextSize(V(sz,sz)); rf.SetTextAngleDegrees(ang); rf.SetPosition(V(x,y)); obst[L].append(g.buffer(0.6))
            stats['silk' if sz==size else 'small']+=1
        else:
            rf.SetLayer(pcbnew.B_Fab if bot else pcbnew.F_Fab); rf.SetTextSize(V(0.6,0.6)); rf.SetTextThickness(M(0.1)); rf.SetPosition(V(cx,cy)); stats['fab']+=1
    return stats
def move_board_texts(b,center,R):
    moved=0
    for side,L in (('F',pcbnew.F_SilkS),('B',pcbnew.B_SilkS)):
        og=[g.buffer(PAD_CLR) for g in pad_geoms(b,side)]
        for f in b.GetFootprints():
            for g in f.GraphicalItems():
                if g.GetLayer()==L and g.GetClass()=='PCB_SHAPE':
                    bb=g.GetBoundingBox(); og.append(box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom())).buffer(0.1))
            rf=f.Reference()
            if rf.GetLayer()==L and rf.IsVisible():
                bb=rf.GetBoundingBox(); og.append(box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom())).buffer(0.1))
        tree=STRtree(og); edge=Point(*center).buffer(R-0.6,128)
        for d in b.GetDrawings():
            if d.GetLayer()!=L or d.GetClass()!='PCB_TEXT': continue
            p0=d.GetPosition(); x0,y0=T(p0.x),T(p0.y)
            bb=d.GetBoundingBox(); g0=box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
            from shapely.affinity import translate
            def ok(dx=0,dy=0):
                g=translate(g0,dx,dy)
                return edge.contains(g) and not any(g.intersects(og[j]) for j in tree.query(g)),g
            good,g=ok()
            if good: og.append(g); tree=STRtree(og); continue
            found=False
            sz0=d.GetTextSize(); th0=d.GetTextThickness()
            for scale in (1.0,0.85,0.72,0.6):
                if scale<1.0:
                    d.SetTextSize(pcbnew.VECTOR2I(int(sz0.x*scale),int(sz0.y*scale))); d.SetTextThickness(max(M(0.15),int(th0*scale)))
                    bb=d.GetBoundingBox(); g0=box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
                for r in [0.5*k for k in range(0,50)]:
                    for a in range(0,360,15):
                        dx,dy=r*math.cos(math.radians(a)),r*math.sin(math.radians(a))
                        good,g=ok(dx,dy)
                        if good: found=True; d.SetPosition(V(x0+dx,y0+dy)); break
                    if found: break
                if found: break
            if not found: d.SetTextSize(sz0); d.SetTextThickness(th0)
            if found: og.append(g); tree=STRtree(og); moved+=1
            else: d.SetPosition(p0)
    return moved
if __name__=='__main__':
    p=sys.argv[1]; cx,cy,R=(float(a) for a in sys.argv[2:5]) if len(sys.argv)>4 else (100,100,33.05)
    b=pcbnew.LoadBoard(p)
    print('clip own',clip_footprint_silk(b,pad_geoms(b,'F'),pad_geoms(b,'B'),own_only=True))
    if '--lib' in sys.argv:
        lib=sys.argv[sys.argv.index('--lib')+1]; io=pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP); seen=set()
        for f in b.GetFootprints():
            nm=str(f.GetFPID().GetLibItemName())
            if nm in seen or f.GetReference().startswith('MH'): continue
            seen.add(nm); c=pcbnew.FOOTPRINT(f); c.SetParent(None)
            if c.GetLayer()==pcbnew.B_Cu: c.Flip(c.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            c.SetOrientationDegrees(0); c.SetPosition(V(0,0)); c.SetReference('REF**')
            io.FootprintSave(lib,c)
        print('lib saved',len(seen))
    print('clip cross',clip_footprint_silk(b,pad_geoms(b,'F'),pad_geoms(b,'B')))
    b.Save(p)
    b=pcbnew.LoadBoard(p)
    print('refs',place_refs(b,(cx,cy),R))
    print('board texts moved',move_board_texts(b,(cx,cy),R))
    ds=b.GetDesignSettings(); ds.m_MinSilkTextHeight=M(0.8); ds.m_SilkClearance=M(0.0)
    b.Save(p)
