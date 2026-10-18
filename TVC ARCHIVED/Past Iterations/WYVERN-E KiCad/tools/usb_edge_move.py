import pcbnew, math
mm=pcbnew.ToMM; MM=pcbnew.FromMM
B='/tmp/w/final4/FC100/WYVERN-E_FC100.kicad_pcb'
b=pcbnew.LoadBoard(B)
DY=-3.13
u=b.FindFootprintByReference('USBC1')
# new courtyard area after move
X0,X1=91.9,102.7; NY0,NY1=54.0+0.0,63.0
# region of the existing USB cluster to translate
RX0,RX1,RY0,RY1=90.9,103.0,58.8,66.6
inside=lambda x,y: RX0<=x<=RX1 and RY0<=y<=RY1
# 1) delete GND stitching vias that will sit under the moved receptacle and are outside the cluster
dele=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        x,y=mm(t.GetPosition())
        if not inside(x,y) and X0-0.6<=x<=X1+0.6 and 53.5<=y<RY0:
            dele.append(t)
for t in dele: print('del via',t.GetNetname(),mm(t.GetPosition())); b.Remove(t)
# 2) translate/stretch tracks
d=pcbnew.VECTOR2I(0,MM(DY))
nm=ns=0
for t in list(b.GetTracks()):
    if t.GetClass()=='PCB_VIA':
        x,y=mm(t.GetPosition())
        if inside(x,y): t.SetPosition(t.GetPosition()+d); nm+=1
        continue
    s,e=t.GetStart(),t.GetEnd()
    si,ei=inside(*mm(s)),inside(*mm(e))
    if si and ei: t.Move(d); nm+=1
    elif si: t.SetStart(s+d); ns+=1; print('stretch',t.GetNetname(),t.GetLayerName(),mm(s),'->',mm(e))
    elif ei: t.SetEnd(e+d); ns+=1; print('stretch',t.GetNetname(),t.GetLayerName(),mm(s),'->',mm(e))
u.Move(d)
# reshape VBUS escape so it clears the moved shell pad 2
P=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
close=lambda a,x,y: abs(mm(a)[0]-x)<0.01 and abs(mm(a)[1]-y)<0.01
for t in list(b.GetTracks()):
    if t.GetClass()!='PCB_TRACK' or t.GetNetname()!='VBUS': continue
    s_,e_=t.GetStart(),t.GetEnd()
    if close(s_,93.3363,58.2046) and close(e_,83.4052,58.2046):
        t.SetStart(P(93.3363,58.4546)); t.SetEnd(P(83.6552,58.4546))
        n=pcbnew.PCB_TRACK(b); n.SetLayer(t.GetLayer()); n.SetNet(t.GetNet()); n.SetWidth(t.GetWidth())
        n.SetStart(P(83.6552,58.4546)); n.SetEnd(P(83.4052,58.2046)); b.Add(n); print('vbus long fixed')
    elif close(s_,93.8577,58.726) and close(e_,93.3363,58.2046):
        t.SetStart(P(93.8577,58.976)); t.SetEnd(P(93.3363,58.4546)); print('vbus jog fixed')
    elif close(e_,93.8577,58.726) or close(s_,93.8577,58.726):
        if close(e_,93.8577,58.726): t.SetEnd(P(93.8577,58.976))
        else: t.SetStart(P(93.8577,58.976))
        print('vbus vert fixed')
print('moved',nm,'stretched',ns)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(B)
