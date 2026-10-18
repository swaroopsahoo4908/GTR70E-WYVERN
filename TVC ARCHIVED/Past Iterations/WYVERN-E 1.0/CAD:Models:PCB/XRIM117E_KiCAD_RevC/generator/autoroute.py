#!/usr/bin/env python3
"""Fast grid A* autorouter — 0.1mm grid, numpy occupancy, escape-capable for 0.4mm QFN."""
import math, heapq
import numpy as np
import shapely
from shapely.geometry import Point, LineString
from kicadgen import pad_abs_pos
from verify import pad_shape, pad_layers

GRID = 0.12
VIA_COST = 26
BCU_MULT = 1.0

def dilate(mask, r):
    cur = mask
    for _ in range(r):
        nxt = cur.copy()
        nxt[1:,:]  |= cur[:-1,:]
        nxt[:-1,:] |= cur[1:,:]
        nxt[:,1:]  |= cur[:,:-1]
        nxt[:,:-1] |= cur[:,1:]
        nxt[1:,1:] |= cur[:-1,:-1]
        nxt[1:,:-1]|= cur[:-1,1:]
        nxt[:-1,1:]|= cur[1:,:-1]
        nxt[:-1,:-1]|=cur[1:,1:]
        cur = nxt
    return cur

class Router:
    def __init__(self, board, widths, clearance=0.14, edge_clr=0.55, keepouts=None):
        self.b=board; self.clr=clearance; self.widths=widths
        cx,cy,r = board.cx, board.cy, board.r
        self.n=int(round(2*r/GRID))+5
        self.x0=cx-r-2*GRID; self.y0=cy-r-2*GRID
        xs=self.x0+np.arange(self.n)*GRID
        self.XX,self.YY=np.meshgrid(xs,xs)
        self.inside=(self.XX-cx)**2+(self.YY-cy)**2 <= (r-edge_clr)**2
        self.net_idx={"":0}
        Z=lambda:np.zeros((self.n,self.n),np.int16)
        self.occ={"F.Cu":Z(),"B.Cu":Z()}
        self.occ_rt={"F.Cu":Z(),"B.Cu":Z()}
        self.KEEP=-9
        self.pad_items=[]
        for (ref,fp,x,y,rot,pad_nets) in board.fp_index:
            pos=pad_abs_pos(fp,x,y,rot)
            for p in fp.pads:
                ax,ay=pos[str(p.num)]
                g=pad_shape(p,ax,ay,rot)
                net=pad_nets.get(str(p.num),"")
                th=p.kind in ("thru_hole","np_thru_hole")
                lyrs=("F.Cu","B.Cu") if th else pad_layers(p)
                self.pad_items.append((net,lyrs,g,ax,ay,ref,str(p.num),th))
                if p.kind=="np_thru_hole" or not net: nid=self.KEEP
                else: nid=self._nid(net)
                for l in lyrs:
                    if l in self.occ: self._raster(self.occ[l], g.buffer(0.03), nid)
        for ko,lyrs in (keepouts or []):
            for l in lyrs:
                if l in self.occ: self._raster(self.occ[l], ko, self.KEEP)
        for t in board.tracks:
            x1,y1,x2,y2,w,layer,nid_,net = t
            g=LineString([(x1,y1),(x2,y2)]).buffer(w/2+0.04,4)
            if layer in self.occ:
                self._raster(self.occ[layer], g, self._nid(net))
                self._raster(self.occ_rt[layer], g, self._nid(net))
        for v in board.vias:
            vx,vy,vs,vd,vn,vnet=v
            g=Point(vx,vy).buffer(vs/2+0.06,6)
            for l in ("F.Cu","B.Cu"):
                self._raster(self.occ[l], g, self._nid(vnet))
                self._raster(self.occ_rt[l], g, self._nid(vnet))

    def _nid(self,net):
        if net not in self.net_idx: self.net_idx[net]=len(self.net_idx)+1
        return self.net_idx[net]

    def _raster(self, arr, geom, nid):
        minx,miny,maxx,maxy=geom.bounds
        j1=max(0,int((minx-self.x0)/GRID)); j2=min(self.n-1,int((maxx-self.x0)/GRID)+1)
        i1=max(0,int((miny-self.y0)/GRID)); i2=min(self.n-1,int((maxy-self.y0)/GRID)+1)
        if j2<j1 or i2<i1: return
        sub=shapely.contains_xy(geom, self.XX[i1:i2+1,j1:j2+1].ravel(), self.YY[i1:i2+1,j1:j2+1].ravel())
        sub=sub.reshape(i2-i1+1, j2-j1+1)
        arr[i1:i2+1,j1:j2+1][sub]=nid

    def _blocked(self, net, width):
        me=self._nid(net)
        r=int(math.ceil((self.clr+width/2)/GRID))
        out={}
        for l in ("F.Cu","B.Cu"):
            other=(self.occ[l]!=0)&(self.occ[l]!=me)
            out[l]=dilate(other,r) | ~self.inside
        return out

    def cellxy(self,iy,ix): return (self.x0+ix*GRID, self.y0+iy*GRID)

    def _pad_cells(self, p, B=None):
        """cells inside pad; fallback to nearest cell to pad center (with tie track)."""
        g=p[2]; out=set(); tie=None
        minx,miny,maxx,maxy=g.bounds
        j1=max(0,int((minx-self.x0)/GRID)); j2=min(self.n-1,int((maxx-self.x0)/GRID)+1)
        i1=max(0,int((miny-self.y0)/GRID)); i2=min(self.n-1,int((maxy-self.y0)/GRID)+1)
        if j2>=j1 and i2>=i1:
            sub=shapely.intersects_xy(g.buffer(0.01), self.XX[i1:i2+1,j1:j2+1].ravel(),
                                      self.YY[i1:i2+1,j1:j2+1].ravel()).reshape(i2-i1+1,j2-j1+1)
            lys=[]
            if p[7]: lys=[0,1]
            else:
                for l in p[1]:
                    if l=="F.Cu": lys.append(0)
                    elif l=="B.Cu": lys.append(1)
            for dy,dx in zip(*np.nonzero(sub)):
                for li in lys: out.add((li,int(i1+dy),int(j1+dx)))
        if not out:
            ix=int(round((p[3]-self.x0)/GRID)); iy=int(round((p[4]-self.y0)/GRID))
            lys=[0,1] if p[7] else [0 if "F.Cu" in p[1] else 1]
            for li in lys: out.add((li,iy,ix))
            tie=(p[3],p[4],self.cellxy(iy,ix))
        return out, tie

    def route_net(self, net, width):
        me=self._nid(net)
        B0=self._blocked(net,width)
        B={0:B0["F.Cu"],1:B0["B.Cu"]}
        BV=self._via_checker(net)
        terms=[p for p in self.pad_items if p[0]==net]
        if len(terms)<2: return True
        for li,l in ((0,"F.Cu"),(1,"B.Cu")):
            B[li][self.occ_rt[l]==me]=False   # own copper always traversable
        chain=sorted(terms,key=lambda p:(p[3],p[4]))
        # flood-label same-net copper components (stubs/vias/pads) so a pad's own
        # stub can't masquerade as an already-routed connection
        import collections
        padcells={}
        for p in chain:
            sc,tie=self._pad_cells(p)
            if tie: self._tie(net,width,tie)
            padcells[(p[5],p[6])]=sc
        mask={0:(self.occ_rt["F.Cu"]==me).copy(),1:(self.occ_rt["B.Cu"]==me).copy()}
        for sc in padcells.values():
            for c in sc: mask[c[0]][c[1],c[2]]=True
        label={}; nl=0
        for li in (0,1):
            for iy,ix in zip(*np.nonzero(mask[li])):
                cell=(li,int(iy),int(ix))
                if cell in label: continue
                nl+=1
                dq=collections.deque([cell]); label[cell]=nl
                while dq:
                    l2,y2,x2=dq.popleft()
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            nc=(l2,y2+dy,x2+dx)
                            if 0<=nc[1]<self.n and 0<=nc[2]<self.n and mask[l2][nc[1],nc[2]] and nc not in label:
                                label[nc]=nl; dq.append(nc)
                    oc=(1-l2,y2,x2)
                    if mask[1-l2][y2,x2] and oc not in label:
                        label[oc]=nl; dq.append(oc)
        def pad_comp(sc):
            return set(label[c] for c in sc if c in label)
        comp_cells={}
        for cell,lb in label.items(): comp_cells.setdefault(lb,[]).append(cell)
        first=padcells[(chain[0][5],chain[0][6])]
        connected=pad_comp(first)
        GT={0:np.zeros((self.n,self.n),bool),1:np.zeros((self.n,self.n),bool)}
        for lb in connected:
            for c in comp_cells[lb]: GT[c[0]][c[1],c[2]]=True
        for c in first: GT[c[0]][c[1],c[2]]=True
        for li in (0,1): B[li][GT[li]]=False
        ok=True
        for p in chain[1:]:
            sc=padcells[(p[5],p[6])]
            for c in sc: B[c[0]][c[1],c[2]]=False
            if pad_comp(sc) & connected:
                for lb in pad_comp(sc):
                    if lb not in connected:
                        connected.add(lb)
                        for c in comp_cells[lb]: GT[c[0]][c[1],c[2]]=True; B[c[0]][c[1],c[2]]=False
                for c in sc: GT[c[0]][c[1],c[2]]=True
                continue
            goal_pads=np.array([(q[4],q[3]) for q in chain if q is not p])  # (y,x) mm
            path=None
            for margin in (5.0, 12.0):
                win=self._window(sc,goal_pads,margin)
                path=self._astar(sc,GT,B,goal_pads,win,BV)
                if path is not None: break
            if path is None:
                print(f"    !! unroutable {net} -> {p[5]}.{p[6]}"); ok=False
                for c in sc: GT[c[0]][c[1],c[2]]=True
                continue
            self._emit(net,width,path)
            for c in path: GT[c[0]][c[1],c[2]]=True
            for lb in pad_comp(sc):
                if lb not in connected:
                    connected.add(lb)
                    for c in comp_cells[lb]: GT[c[0]][c[1],c[2]]=True; B[c[0]][c[1],c[2]]=False
            for c in sc: GT[c[0]][c[1],c[2]]=True
        return ok

    route_one = route_net

    def _tie(self,net,width,tie):
        (px,py,(cx,cy))=tie
        if abs(px-cx)>1e-9 or abs(py-cy)>1e-9:
            self.b.track(net,[(px,py),(cx,cy)],"F.Cu",min(width,0.2))

    def _via_checker(self, net):
        from shapely.strtree import STRtree
        from shapely.geometry import Point as _P, LineString as _LS
        me=self._nid(net)
        fastok={}
        for i,l in ((0,"F.Cu"),(1,"B.Cu")):
            other=(self.occ[l]!=0)&(self.occ[l]!=me)
            fastok[i]=~dilate(other,5)
        FAST = fastok[0] & fastok[1] & self.inside
        geoms=[]
        for p in self.pad_items:
            if p[0]!=net: geoms.append(p[2])
        for t in self.b.tracks:
            if t[7]!=net: geoms.append(_LS([(t[0],t[1]),(t[2],t[3])]).buffer(t[4]/2,4))
        for v in self.b.vias:
            if v[5]!=net: geoms.append(_P(v[0],v[1]).buffer(v[2]/2,6))
        tree=STRtree(geoms) if geoms else None
        cache={}
        def ok(iy,ix):
            if FAST[iy,ix]: return True
            key=(iy,ix)
            if key in cache: return cache[key]
            x,y=self.cellxy(iy,ix)
            if (x-self.b.cx)**2+(y-self.b.cy)**2 > (self.b.r-0.9)**2:
                cache[key]=False; return False
            good=True
            if tree is not None:
                pt=_P(x,y)
                for j in tree.query(pt.buffer(0.38)):
                    if geoms[int(j)].distance(pt) < 0.355:
                        good=False; break
            cache[key]=good
            return good
        return ok

    def _window(self, starts, goal_pads, margin):
        ys=[c[1] for c in starts]; xs=[c[2] for c in starts]
        iy1=min(ys); iy2=max(ys); ix1=min(xs); ix2=max(xs)
        gy1=int((goal_pads[:,0].min()-self.y0)/GRID); gy2=int((goal_pads[:,0].max()-self.y0)/GRID)
        gx1=int((goal_pads[:,1].min()-self.x0)/GRID); gx2=int((goal_pads[:,1].max()-self.x0)/GRID)
        m=int(margin/GRID)
        return (max(0,min(iy1,gy1)-m), min(self.n-1,max(iy2,gy2)+m),
                max(0,min(ix1,gx1)-m), min(self.n-1,max(ix2,gx2)+m))

    def _astar(self, starts, GT, B, goal_pads, win=None, BV=None):
        wy1,wy2,wx1,wx2 = win if win else (0,self.n-1,0,self.n-1)
        gy=goal_pads[:,0]; gx=goal_pads[:,1]
        def h(iy,ix):
            x,y=self.x0+ix*GRID, self.y0+iy*GRID
            return (np.abs(gy-y)+np.abs(gx-x)).min()/GRID*0.999
        openq=[]; gsc={}; came={}
        for s in starts:
            if not B[s[0]][s[1],s[2]]:
                gsc[s]=0.0; came[s]=None
                heapq.heappush(openq,(h(s[1],s[2]),0.0,s))
        seen=set()
        DIRS=((1,0,1.0),(-1,0,1.0),(0,1,1.0),(0,-1,1.0),
              (1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414))
        nmax=self.n; pops=0
        while openq:
            f,gv,cur=heapq.heappop(openq)
            if cur in seen: continue
            seen.add(cur); pops+=1
            if pops>45000: return None
            li,iy,ix=cur
            if GT[li][iy,ix]:
                path=[cur]; pp=came[cur]
                while pp is not None: path.append(pp); pp=came[pp]
                return path[::-1]
            bb=B[li]
            for dy,dx,c in DIRS:
                ny,nx=iy+dy,ix+dx
                if ny<wy1 or nx<wx1 or ny>wy2 or nx>wx2 or bb[ny,nx]: continue
                nc=(li,ny,nx); ng=gv+c*(BCU_MULT if li else 1.0)
                if ng<gsc.get(nc,1e18):
                    gsc[nc]=ng; came[nc]=cur
                    heapq.heappush(openq,(ng+h(ny,nx),ng,nc))
            ol=1-li
            if (not B[ol][iy,ix]) and (BV is None or BV(iy,ix)):
                nc=(ol,iy,ix); ng=gv+VIA_COST
                if ng<gsc.get(nc,1e18):
                    gsc[nc]=ng; came[nc]=cur
                    heapq.heappush(openq,(ng+h(iy,ix),ng,nc))
        return None

    def _emit(self, net, width, path):
        me=self._nid(net)
        i=0
        while i<len(path):
            j=i
            while j+1<len(path) and path[j+1][0]==path[i][0]: j+=1
            pts=[self.cellxy(c[1],c[2]) for c in path[i:j+1]]
            pts=self._simplify(pts)
            if len(pts)>1:
                lname=("F.Cu","B.Cu")[path[i][0]]
                self.b.track(net,pts,lname,width)
                g=LineString(pts).buffer(width/2+0.04,4)
                self._raster(self.occ[lname],g,me); self._raster(self.occ_rt[lname],g,me)
            if j+1<len(path):
                x,y=self.cellxy(path[j][1],path[j][2])
                self.b.via(net,x,y,size=0.45,drill=0.25)
                g=Point(x,y).buffer(0.36,6)
                for l in ("F.Cu","B.Cu"):
                    self._raster(self.occ[l],g,me); self._raster(self.occ_rt[l],g,me)
            i=j+1

    @staticmethod
    def _simplify(pts):
        if len(pts)<3: return pts
        out=[pts[0]]
        for i in range(1,len(pts)-1):
            x0,y0=out[-1]; x1,y1=pts[i]; x2,y2=pts[i+1]
            if abs((x1-x0)*(y2-y0)-(y1-y0)*(x2-x0))>1e-9: out.append(pts[i])
        out.append(pts[-1])
        return out

    def commit(self): pass

def stitch_gnd(board, spacing=5.5, avoid=None):
    import math as m
    from shapely.geometry import Point as P
    avoid=avoid or []
    occupied=[]
    for (ref,fp,x,y,rot,pad_nets) in board.fp_index:
        pos=pad_abs_pos(fp,x,y,rot)
        for p in fp.pads:
            ax,ay=pos[str(p.num)]
            occupied.append((ax,ay,max(p.w,p.h)/2+0.55,pad_nets.get(str(p.num),"")))
    segs=[(t[0],t[1],t[2],t[3],t[4],t[7]) for t in board.tracks]
    vias=[(v[0],v[1],v[5]) for v in board.vias]
    placed=[]
    def free(px,py):
        if m.hypot(px-board.cx,py-board.cy)>board.r-1.2: return False
        for g in avoid:
            if g.contains(P(px,py)): return False
        for (ax,ay,rr,net) in occupied:
            lim = rr+0.1 if net=="GND" else rr+0.35
            if m.hypot(px-ax,py-ay)<lim: return False
        for (x1,y1,x2,y2,w,net) in segs:
            if net=="GND": continue
            dx,dy=x2-x1,y2-y1
            L2=dx*dx+dy*dy
            t=0 if L2==0 else max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L2))
            if m.hypot(px-(x1+t*dx),py-(y1+t*dy)) < w/2+0.65: return False
        for (vx,vy,net) in vias:
            if m.hypot(px-vx,py-vy)< (0.65 if net=="GND" else 0.85): return False
        for (vx,vy) in placed:
            if m.hypot(px-vx,py-vy)<spacing*0.55: return False
        return True
    rr=board.r-1.6
    nv=int(2*m.pi*rr/spacing)
    for i in range(nv):
        a=2*m.pi*i/nv
        px,py=board.cx+rr*m.cos(a),board.cy+rr*m.sin(a)
        if free(px,py):
            board.via("GND",px,py); placed.append((px,py))
    steps=int(2*board.r/spacing)
    for i in range(steps):
        for j in range(steps):
            px=board.cx-board.r+spacing*(i+0.5); py=board.cy-board.r+spacing*(j+0.5)
            if free(px,py):
                board.via("GND",px,py); placed.append((px,py))
    return len(placed)
