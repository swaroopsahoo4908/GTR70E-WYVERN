import pcbnew
mm=pcbnew.ToMM; MM=pcbnew.FromMM; DY=-3.13
B='WYVERN-E_FC100.kicad_pcb'; b=pcbnew.LoadBoard(B)
P=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
near=lambda a,x,y: abs(mm(a)[0]-x)<0.01 and abs(mm(a)[1]-y)<0.01
gnd=b.GetNetInfo().GetNetItem('GND')
A=(92.9592,59.3775+DY);Bp=(92.9592,60.5062+DY);C=(91.4794,61.986+DY)
for t in list(b.GetTracks()):
    if t.GetClass()!='PCB_TRACK' or t.GetNetname()!='GND' or t.GetLayerName()!='F.Cu': continue
    s,e=t.GetStart(),t.GetEnd()
    if (near(s,*A) and near(e,*Bp)) or (near(s,*Bp) and near(e,*C)): print('remove'); b.Remove(t)
    elif near(s,*C): t.SetStart(P(91.4794,61.5)); print('shorten')
    elif near(e,*C): t.SetEnd(P(91.4794,61.5)); print('shorten')
v=pcbnew.PCB_VIA(b); v.SetPosition(P(91.4794,61.5)); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(gnd); b.Add(v)
b.Save(B)
import pcbnew
mm=pcbnew.ToMM; MM=pcbnew.FromMM
B='WYVERN-E_FC100.kicad_pcb'; b=pcbnew.LoadBoard(B)
P=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
u=b.FindFootprintByReference('USBC1')
for m in u.Models():
    m.m_Rotation.z=0.0; m.m_Offset.y=0.247975; print('model fixed')
for g in list(u.GraphicalItems()):
    if 'Silk' not in g.GetLayerName() or g.GetClass()!='PCB_SHAPE': continue
    s,e=mm(g.GetStart()),mm(g.GetEnd())
    if (abs(s[1]-e[1])<0.3 and min(s[1],e[1])<55.5) or max(s[1],e[1])<55.5: u.Remove(g); print('rm silk',s,e)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(B)
f=pcbnew.FOOTPRINT(u); f.SetOrientationDegrees(0); f.SetPosition(P(0,0)); f.SetReference('REF**')
pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP).FootprintSave('WYVERN_FC100.pretty', f)
print('USB pos',mm(u.GetPosition()))
for g in u.GraphicalItems():
    if g.GetLayerName()=='F.Fab' and g.GetClass()=='PCB_SHAPE':
        bb=g.GetBoundingBox(); print('fab',mm(bb.GetOrigin()),mm(bb.GetEnd()))
