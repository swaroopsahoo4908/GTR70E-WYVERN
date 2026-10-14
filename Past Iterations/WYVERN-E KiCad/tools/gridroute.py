import pcbnew,math,heapq,numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Point,LineString
import post
from pcbbuild import V,MM
TOMM=pcbnew.ToMM
class Router:
    def __init__(s,b,center,R,res=0.05,layers=None,tw=0.15,clr=0.13,via=0.5,drill=0.3,clr_check=0.152):
        s.clr_check=clr_check; s.fine_clr=0.1; s.b=b;s.res=res;s.cx,s.cy=center;s.R=R;s.tw=tw;s.clr=clr;s.via=via;s.drill=drill
        s.layers=layers or [pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
        s.vlayers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
        s.x0=s.cx-R;s.y0=s.cy-R;s.N=int(2*R/res)+1
        s.refresh()
    def refresh(s):
        s.items={L:post.copper_items(s.b,L) for L in s.vlayers}
        # holes (NPTH and PTH drill) block all layers
    def ij(s,x,y): return int(round((x-s.x0)/s.res)),int(round((y-s.y0)/s.res))
    def xy(s,i,j): return s.x0+i*s.res,s.y0+j*s.res
    def raster(s,geoms,infl):
        im=Image.new('1',(s.N,s.N),0); d=ImageDraw.Draw(im)
        W=getattr(s,'_win',None)
        for g in geoms:
            extra=0
            if isinstance(g,tuple): g,extra=g
            if W is not None:
                bx=g.bounds; m=infl+extra+0.1
                if bx[2]+m<W[0] or bx[0]-m>W[2] or bx[3]+m<W[1] or bx[1]-m>W[3]: continue
            g=g.buffer(infl+extra,6)
            polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
            for p in polys:
                pts=[((x-s.x0)/s.res,(y-s.y0)/s.res) for x,y in p.exterior.coords]
                if len(pts)>2: d.polygon(pts,fill=1)
        a=np.array(im,dtype=bool).T  # a[i,j]
        return a
    def route(s,code,a_xy,b_xy,margin=8.0,w=None,lock=False,a_lay=None,b_lay=None):
        o=(s.x0,s.y0,s.N)
        x0=max(s.cx-s.R,min(a_xy[0],b_xy[0])-margin-1); y0=max(s.cy-s.R,min(a_xy[1],b_xy[1])-margin-1)
        x1=min(s.cx+s.R,max(a_xy[0],b_xy[0])+margin+1); y1=min(s.cy+s.R,max(a_xy[1],b_xy[1])+margin+1)
        s.x0,s.y0=x0,y0; s.N=int(max(x1-x0,y1-y0)/s.res)+2; s._win=(x0,y0,x0+s.N*s.res,y0+s.N*s.res)
        try: return s._route(code,a_xy,b_xy,margin,w,lock,a_lay,b_lay)
        finally:
            s.x0,s.y0,s.N=o; s._win=None
    def _route(s,code,a_xy,b_xy,margin=8.0,w=None,lock=False,a_lay=None,b_lay=None):
        w=w or s.tw
        obs={};viaobs=None
        fz=getattr(s,'fine_zones',None)
        if fz is not None:
            zm=np.zeros((s.N,s.N),bool)
            im=Image.new('1',(s.N,s.N),0); d=ImageDraw.Draw(im)
            for (x0,y0,x1,y1) in fz: d.rectangle([(x0-s.x0)/s.res,(y0-s.y0)/s.res,(x1-s.x0)/s.res,(y1-s.y0)/s.res],fill=1)
            zm=np.array(im,dtype=bool).T
        def ishc(o):
            try: return 'HighCurrent' in o.GetNetClassName()
            except Exception: return False
        selfhc=False
        try: selfhc='HighCurrent' in s.b.FindNet(s.b.GetNetInfo().GetNetItem(code).GetNetname()).GetNetClassName()
        except Exception: pass
        def og(L): return [(g,(0.025 if (selfhc or ishc(o)) else 0.0)) for n,g,o in s.items[L] if n!=code]
        for L in s.layers:
            obs[L]=s.raster(og(L),s.clr+w/2)
            if fz is not None:
                fine=s.raster(og(L),s.fine_clr+w/2)
                obs[L]=np.where(zm,fine,obs[L])
        for L in s.layers:
            ownr=s.raster([g for n,g,o in s.items[L] if n==code],-0.02)
            obs[L]&=~ownr
        vo=[s.raster(og(L),s.clr+s.via/2) for L in s.vlayers]
        viaobs=np.logical_or.reduce(vo)
        def _isvia(o):
            try: return o is not None and (o.GetClass()=='PCB_VIA' or (o.GetClass()=='PAD' and o.GetAttribute()==pcbnew.PAD_ATTRIB_PTH))
            except Exception: return False
        s._ownvias=[g.centroid for n,g,o in s.items[pcbnew.F_Cu] if n==code and _isvia(o)]
        if s._ownvias:
            ownv=s.raster([g.buffer(0.001) for g in s._ownvias],0.12)
            viaobs&=~ownv
        # board edge
        ii,jj=np.meshgrid(np.arange(s.N),np.arange(s.N),indexing='ij')
        out=np.hypot(s.x0+ii*s.res-s.cx,s.y0+jj*s.res-s.cy)>s.R-0.35-w/2
        for L in s.layers: obs[L]|=out
        viaobs|=out
        # start/goal: allow own pad area: cells inside own copper are free since only other nets are obstacles
        si,sj=s.ij(*a_xy); gi,gj=s.ij(*b_xy)
        def layers_at(xy):
            P=Point(*xy); r=[]
            for k,L in enumerate(s.layers):
                if any(n==code and g.buffer(0.01).contains(P) for n,g,o in s.items[L]): r.append(k)
            return r or list(range(len(s.layers)))
        SL=layers_at(a_xy); GL=set(layers_at(b_xy))
        if a_lay is not None and a_lay in s.layers: SL=[s.layers.index(a_lay)]
        if b_lay is not None and b_lay in s.layers: GL={s.layers.index(b_lay)}
        lo_i=max(0,min(si,gi)-int(margin/s.res)); hi_i=min(s.N-1,max(si,gi)+int(margin/s.res))
        lo_j=max(0,min(sj,gj)-int(margin/s.res)); hi_j=min(s.N-1,max(sj,gj)+int(margin/s.res))
        from shapely.geometry import LineString
        from shapely.strtree import STRtree
        others={L:[g for n,g,o in s.items[L] if n!=code] for L in s.vlayers}
        otherhc={L:[(selfhc or ishc(o)) for n,g,o in s.items[L] if n!=code] for L in s.vlayers}
        trees={L:(STRtree(others[L]) if others[L] else None) for L in s.vlayers}
        fzp=[__import__('shapely.geometry',fromlist=['box']).box(*z) for z in (fz or [])]
        def req_clr(geom):
            if fzp and any(z.contains(geom) for z in fzp): return s.fine_clr-0.005
            return s.clr_check
        for attempt in range(8):
            path=s._astar(obs,viaobs,si,sj,gi,gj,SL,GL,lo_i,hi_i,lo_j,hi_j)
            if not path: return False
            # build primitives
            prims=[]  # (kind, layer_k, geom_params)
            pts=[(a_xy,path[0][2])]+[(s.xy(p[0],p[1]),p[2]) for p in path]+[(b_xy,path[-1][2])]
            segs=[];vias=[]
            for (p,k),(q,k2) in zip(pts,pts[1:]):
                if k!=k2: vias.append(p)
                elif p!=q: segs.append((p,q,k))
            bad=[]
            for p,q,k in segs:
                g=LineString([p,q]).buffer(w/2,8)
                L=s.layers[k]; t=trees[L]
                if t is None: continue
                rc0=req_clr(LineString([p,q]))
                for idx in t.query(g.buffer(rc0+0.03)):
                    rc=max(rc0,0.152) if otherhc[L][idx] else rc0
                    if g.distance(others[L][idx])<rc: bad.append(((p[0]+q[0])/2,(p[1]+q[1])/2,k)); break
            for v in vias:
                if any(Point(*v).distance(g)<0.35 for g in getattr(s,'_ownvias',[])): continue
                g=Point(*v).buffer(s.via/2,12)
                for k,L in enumerate(s.vlayers):
                    t=trees[L]
                    if t is None: continue
                    if any(g.distance(others[L][idx])<(0.152 if otherhc[L][idx] else s.clr_check) for idx in t.query(g.buffer(0.2))): bad.append((v[0],v[1],-1)); break
            if not bad: break
            for x,y,k in bad:
                ci,cj=s.ij(x,y); rr=3
                if k<0: viaobs[max(0,ci-rr):ci+rr+1,max(0,cj-rr):cj+rr+1]=True
                else: obs[s.layers[k]][max(0,ci-rr):ci+rr+1,max(0,cj-rr):cj+rr+1]=True
                obs_ok=True
            # never block start/goal cell
            for L in s.layers: obs[L][si,sj]=False; obs[L][gi,gj]=False
        else:
            return False
        # string-pull each same-layer run (removes A* stair-steps), clearance-checked
        if getattr(s,'smooth',True) and segs:
            runs=[];cur=None
            for p,q,k in segs:
                if cur and cur[0]==k and cur[1][-1]==p: cur[1].append(q)
                else:
                    cur=[k,[p,q]]; runs.append(cur)
            edge=Point(s.cx,s.cy).buffer(s.R-0.35-w/2,256)
            def free(a,c,k):
                ln=LineString([a,c]); 
                if not edge.contains(ln): return False
                g=ln.buffer(w/2,8); L=s.layers[k]; t=trees[L]
                if t is None: return True
                rc0=req_clr(ln)
                for idx in t.query(g.buffer(rc0+0.2)):
                    rc=max(rc0,0.152) if otherhc[L][idx] else rc0
                    if g.distance(others[L][idx])<rc+0.002: return False
                return True
            nsegs=[]
            for k,pts_ in runs:
                i=0
                while i<len(pts_)-1:
                    j=len(pts_)-1
                    while j>i+1 and not free(pts_[i],pts_[j],k): j-=1
                    nsegs.append((pts_[i],pts_[j],k)); i=j
            segs=nsegs
        # merge collinear segments & emit
        merged=[]
        for p,q,k in segs:
            if merged and merged[-1][2]==k and merged[-1][1]==p:
                a0=merged[-1][0]
                d1=(p[0]-a0[0],p[1]-a0[1]); d2=(q[0]-p[0],q[1]-p[1])
                if abs(d1[0]*d2[1]-d1[1]*d2[0])<1e-9 and d1[0]*d2[0]+d1[1]*d2[1]>0:
                    merged[-1]=(a0,q,k); continue
            merged.append((p,q,k))
        for p,q,k in merged:
            t=pcbnew.PCB_TRACK(s.b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetWidth(MM(w)); t.SetLayer(s.layers[k]); t.SetNetCode(code); t.SetLocked(lock); s.b.Add(t)
        for v in vias:
            if any(Point(*v).distance(g)<0.35 for g in getattr(s,'_ownvias',[])): continue
            vi=pcbnew.PCB_VIA(s.b); vi.SetPosition(V(*v)); vi.SetWidth(MM(s.via)); vi.SetDrill(MM(s.drill)); vi.SetNetCode(code); vi.SetViaType(pcbnew.VIATYPE_THROUGH); vi.SetLocked(lock); s.b.Add(vi)
        s.refresh()
        return True
    def _astar(s,obs,viaobs,si,sj,gi,gj,SL,GL,lo_i,hi_i,lo_j,hi_j):
        H=lambda i,j: math.hypot(i-gi,j-gj)
        dirs=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]
        viacost=int(1.5/s.res)
        openh=[];g={};prev={}
        for k in SL:
            st=(si,sj,k); g[st]=0; heapq.heappush(openh,(H(si,sj),st))
        nL=len(s.layers); found=None; it=0
        while openh:
            f,cur=heapq.heappop(openh); it+=1
            if it>8_000_000: break
            i,j,k=cur
            if (i,j)==(gi,gj) and k in GL: found=cur;break
            gc=g[cur]
            if f-H(i,j)>gc+1e-9: continue
            for di,dj,c in dirs:
                ni,nj=i+di,j+dj
                if ni<lo_i or ni>hi_i or nj<lo_j or nj>hi_j: continue
                if obs[s.layers[k]][ni,nj] and not ((ni,nj)==(gi,gj)): continue
                nx=(ni,nj,k); ng=gc+c
                if ng<g.get(nx,1e18): g[nx]=ng; prev[nx]=cur; heapq.heappush(openh,(ng+H(ni,nj),nx))
            if not viaobs[i,j]:
                for k2 in range(nL):
                    if k2==k: continue
                    nx=(i,j,k2); ng=gc+viacost
                    if ng<g.get(nx,1e18): g[nx]=ng; prev[nx]=cur; heapq.heappush(openh,(ng+H(i,j),nx))
        if not found: return None
        path=[found]
        while path[-1] in prev: path.append(prev[path[-1]])
        path.reverse()
        return path

def route_any(r,code,a_xy,maxtries=6,**kw):
    from shapely.geometry import Point
    P=Point(*a_xy)
    cands=[]
    for L in r.layers:
        for n,g,o in r.items[L]:
            if n!=code or g.buffer(0.02).contains(P): continue
            c=g.centroid; cands.append((P.distance(g),(c.x,c.y)))
    cands.sort()
    seen=set()
    for d,c in cands:
        k=(round(c[0],1),round(c[1],1))
        if k in seen: continue
        seen.add(k)
        if r.route(code,a_xy,c,**kw): return True
        if len(seen)>=maxtries: break
    return False

LN={'F.Cu':pcbnew.F_Cu,'B.Cu':pcbnew.B_Cu,'In1.GND':pcbnew.In1_Cu,'In1.SIG_GND':pcbnew.In1_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.SIG_PWR':pcbnew.In2_Cu,'In2.Cu':pcbnew.In2_Cu}
def lay_of(desc):
    if desc.startswith(('Via','PTH')): return None
    import re
    m=re.search(r' on ([^ ,]+)',desc)
    return LN.get(m.group(1)) if m else None
