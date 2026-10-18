import pcbnew,math
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
from pcbbuild import V,MM
import post
TOMM=pcbnew.ToMM
def fanout(b,netname,center,R,via=0.6,drill=0.3,tw=0.3,clr=0.2,maxd=2.2):
    ni=b.FindNet(netname); code=ni.GetNetCode()
    layers=[pcbnew.F_Cu,pcbnew.B_Cu]+[l for l in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu] if l not in (pcbnew.F_Cu,pcbnew.B_Cu)]
    def build():
        geo=[];own=[]
        for l in layers:
            for n,g,o in post.copper_items(b,l):
                if n!=code or True: geo.append((l,n,g))
        return geo
    geo=build()
    # all-layer obstacles for vias (vias span all layers): other-net copper on any layer except plane layer of same net
    def tree_for(filter_fn):
        gs=[g for l,n,g in geo if filter_fn(l,n)]
        return STRtree(gs),gs
    cx,cy=center
    added=0;fail=[]
    # obstacle sets
    via_obs=[g for l,n,g in geo if n!=code]
    vt=STRtree(via_obs)
    placed=[]
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetNetCode()!=code: continue
            if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD: continue
            L=pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            _ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(_ps,L,0,MM(0.01),pcbnew.ERROR_INSIDE)
            if post.polyset_to_shapely(_ps).area>=4.0: continue
            px,py=TOMM(p.GetPosition().x),TOMM(p.GetPosition().y)
            # pad already near an existing same-net via?
            if any(math.hypot(px-a,py-c)<0.9 for a,c in placed): continue
            sz=p.GetSize(L) if hasattr(p,'GetSize') else p.GetSize()
            hw=max(TOMM(sz.x),TOMM(sz.y))/2
            lay_obs=[g for l,n,g in geo if l==L and n!=code]
            lt=STRtree(lay_obs)
            best=None
            for d in [hw+via/2+0.12+k*0.15 for k in range(10)]:
                if d>maxd+hw: break
                for k in range(16):
                    a=2*math.pi*k/16
                    vx,vy=px+d*math.cos(a),py+d*math.sin(a)
                    if math.hypot(vx-cx,vy-cy)>R-1.0: continue
                    vg=Point(vx,vy).buffer(via/2+clr,12)
                    if any(vg.intersects(via_obs[j]) for j in vt.query(vg)): continue
                    if any(math.hypot(vx-a2,vy-c2)<via+0.2 for a2,c2 in placed): continue
                    tg=LineString([(px,py),(vx,vy)]).buffer(tw/2+clr,8)
                    if any(tg.intersects(lay_obs[j]) for j in lt.query(tg)): continue
                    best=(vx,vy);break
                if best: break
            if not best: fail.append(f'{f.GetReference()}.{p.GetNumber()}'); continue
            vx,vy=best
            v=pcbnew.PCB_VIA(b); v.SetPosition(V(vx,vy)); v.SetWidth(MM(via)); v.SetDrill(MM(drill)); v.SetNet(ni); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
            t=pcbnew.PCB_TRACK(b); t.SetStart(p.GetPosition()); t.SetEnd(V(vx,vy)); t.SetWidth(MM(tw)); t.SetLayer(L); t.SetNet(ni); b.Add(t)
            vg=Point(vx,vy).buffer(via/2,12)
            for l in layers: geo.append((l,code,vg))
            geo.append((L,code,LineString([(px,py),(vx,vy)]).buffer(tw/2)))
            placed.append((vx,vy)); added+=1
    return added,fail
def ep_vias(b,netname,pitch=1.1,via=0.6,drill=0.3,min_area=4.0,check=False,clr=0.2):
    ni=b.FindNet(netname); n=0
    obst=[]
    if check:
        for L in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]:
            obst+=[g for nn,g,o in post.copper_items(b,L) if nn!=ni.GetNetCode()]
        from shapely.strtree import STRtree
        tree=STRtree(obst) if obst else None
        existing=[(TOMM(t.GetPosition().x),TOMM(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
    for f in b.Footprints():
        for p in f.Pads():
            if p.GetNetname()!=netname or p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD: continue
            L=pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,L,0,MM(0.005),pcbnew.ERROR_INSIDE)
            g=post.polyset_to_shapely(ps)
            if g.area<min_area: continue
            inner=g.buffer(-(via/2+0.05))
            x0,y0,x1,y1=inner.bounds
            cx,cy=(x0+x1)/2,(y0+y1)/2
            nx=max(1,int((x1-x0)/pitch)+1); ny=max(1,int((y1-y0)/pitch)+1)
            for i in range(nx):
                for j in range(ny):
                    x=cx+(i-(nx-1)/2)*pitch; y=cy+(j-(ny-1)/2)*pitch
                    if inner.contains(Point(x,y)):
                        if check:
                            vg=Point(x,y).buffer(via/2+clr,12)
                            if tree is not None and any(vg.intersects(obst[k]) for k in tree.query(vg)): continue
                            if any(math.hypot(x-a,y-c)<via+0.2 for a,c in existing): continue
                        v=pcbnew.PCB_VIA(b); v.SetPosition(V(x,y)); v.SetWidth(MM(via)); v.SetDrill(MM(drill)); v.SetNet(ni); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); n+=1
    return n
