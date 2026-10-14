import sys; sys.path.insert(0,'/tmp/w/conv')
import stripzones,pcbnew,striptracks,shutil
src,dst=sys.argv[1],sys.argv[2]
stripzones.strip(src,dst)
b=pcbnew.LoadBoard(dst)
ends=set()
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_TRACE_T: ends.add((t.GetStart().x,t.GetStart().y)); ends.add((t.GetEnd().x,t.GetEnd().y))
pads=[p for f in b.Footprints() for p in f.Pads() if p.GetNetname()=='GND']
rm=set()
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='GND' and not t.IsLocked():
        pos=t.GetPosition()
        if (pos.x,pos.y) in ends or any(p.HitTest(pos) for p in pads): continue
        rm.add(t.m_Uuid.AsString())
striptracks.remove_uuids(dst,dst,rm)
shutil.copy(src.replace('.kicad_pcb','.kicad_pro'),dst.replace('.kicad_pcb','.kicad_pro')); shutil.copy(src.replace('.kicad_pcb','.kicad_dru'),dst.replace('.kicad_pcb','.kicad_dru'))
print('removed stitch',len(rm))
