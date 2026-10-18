import pcbnew,sys,collections,json
T=pcbnew.ToMM
p=sys.argv[1]; b=pcbnew.LoadBoard(p)
R={}
tr=[t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK']; vi=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
R['tracks']=len(tr); R['min_track_mm']=min(T(t.GetWidth()) for t in tr)
R['tracks_below_0.127']=sum(1 for t in tr if T(t.GetWidth())<0.127-1e-6)
R['vias']=collections.Counter(f"{T(v.GetWidth(pcbnew.F_Cu)):.2f}/{T(v.GetDrillValue()):.2f}" for v in vi)
R['min_via_annular_mm']=min((T(v.GetWidth(pcbnew.F_Cu))-T(v.GetDrillValue()))/2 for v in vi)
pth=[];npth=[];ring=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.GetAttribute()==pcbnew.PAD_ATTRIB_PTH:
            d=min(T(q.GetDrillSizeX()),T(q.GetDrillSizeY())); pth.append(d)
            ring.append((min(T(q.GetSize(pcbnew.F_Cu).x)-T(q.GetDrillSizeX()),T(q.GetSize(pcbnew.F_Cu).y)-T(q.GetDrillSizeY()))/2,f.GetReference(),q.GetNumber()))
        elif q.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: npth.append(T(q.GetDrillSizeX()))
R['min_pth_drill_mm']=min(pth) if pth else None; R['min_npth_mm']=min(npth) if npth else None
R['min_pth_ring_mm']=min(ring)[:1]+min(ring)[1:] if ring else None
# silkscreen
lw=[];th=[]
for f in b.GetFootprints():
    for g in f.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_SilkS,pcbnew.B_SilkS) and g.GetClass()=='PCB_SHAPE': lw.append(T(g.GetWidth()))
    r=f.Reference()
    if r.IsVisible() and r.GetLayer() in (pcbnew.F_SilkS,pcbnew.B_SilkS): th.append((T(r.GetTextHeight()),T(r.GetTextThickness())))
for d in b.GetDrawings():
    if d.GetLayer() in (pcbnew.F_SilkS,pcbnew.B_SilkS):
        if d.GetClass()=='PCB_TEXT': th.append((T(d.GetTextHeight()),T(d.GetTextThickness())))
        else: lw.append(T(d.GetWidth()))
R['silk_min_line_mm']=min(lw) if lw else None; R['silk_lines_below_0.15']=sum(1 for w in lw if w<0.15-1e-6)
R['silk_min_text_h_mm']=min(h for h,t in th); R['silk_min_text_stroke_mm']=min(t for h,t in th); R['silk_texts']=len(th)
ds=b.GetDesignSettings()
R['copper_layers']=b.GetCopperLayerCount(); R['board_thickness_mm']=T(ds.GetBoardThickness())
R['zones']=len(list(b.Zones())); R['zone_min_width_mm']=min(T(z.GetMinThickness()) for z in b.Zones())
bb=b.GetBoardEdgesBoundingBox(); R['outline_mm']=(round(T(bb.GetWidth()),2),round(T(bb.GetHeight()),2))
R['smd_parts_top']=sum(1 for f in b.GetFootprints() if f.GetLayer()==pcbnew.F_Cu); R['parts_bottom']=sum(1 for f in b.GetFootprints() if f.GetLayer()==pcbnew.B_Cu)
print(json.dumps(R,indent=1,default=str))
