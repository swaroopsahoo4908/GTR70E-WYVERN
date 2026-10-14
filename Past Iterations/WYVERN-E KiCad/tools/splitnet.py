import pcbnew,sys,math
T=pcbnew.ToMM; M=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]); nets=set(sys.argv[2].split(',')); step=float(sys.argv[3]) if len(sys.argv)>3 else 1.0
n=0
for t in list(b.GetTracks()):
    if t.GetClass()!='PCB_TRACK' or t.GetNetname() not in nets: continue
    L=T(t.GetLength())
    if L<1.6*step: continue
    s,e=T(t.GetStart()),T(t.GetEnd()); k=int(L/step)
    pts=[(s[0]+(e[0]-s[0])*i/k,s[1]+(e[1]-s[1])*i/k) for i in range(k+1)]
    for a,c in zip(pts,pts[1:]):
        u=pcbnew.PCB_TRACK(b); u.SetStart(pcbnew.VECTOR2I(M(a[0]),M(a[1]))); u.SetEnd(pcbnew.VECTOR2I(M(c[0]),M(c[1]))); u.SetWidth(t.GetWidth()); u.SetLayer(t.GetLayer()); u.SetNet(t.GetNet()); b.Add(u)
    b.Remove(t); n+=1
b.Save(sys.argv[1]); print('split',n)
