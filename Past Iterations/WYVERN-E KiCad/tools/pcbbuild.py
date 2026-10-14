import pcbnew,json,math,collections,epru
MM=pcbnew.FromMM
def V(x,y): return pcbnew.VECTOR2I(MM(x),MM(y))
MIL=0.0254
def comp_placement(D):
    pcb=[d for d in D if d['head']['docType']=='PCB'][0]
    attrs=collections.defaultdict(dict)
    for h,b in epru.live(pcb,'ATTR'): attrs[b['parentId']][b['key']]=b
    pl={}
    for h,b in epru.live(pcb,'COMPONENT'):
        a=attrs[h['id']]; ref=a.get('Designator',{}).get('value')
        if ref: pl[ref]=dict(x=b['x']*MIL,y=-b['y']*MIL,angle=b['angle'],side='B' if b['layerId']==2 else 'F')
    return pl,pcb
def outline_holes(pcb):
    circ=[];holes=[];strings=[];lines=[]
    for h,b in epru.live(pcb,'POLY'):
        if b['layerId']==11: 
            p=b['path']
            if p[0]=='CIRCLE': circ.append((p[1]*MIL,-p[2]*MIL,p[3]*MIL))
            else: lines.append(p)
    for h,b in epru.live(pcb,'FILL'):
        if b['layerId']==12:
            for sp in (b['path'] if isinstance(b['path'][0],list) else [b['path']]):
                if sp[0]=='CIRCLE': holes.append((sp[1]*MIL,-sp[2]*MIL,2*sp[3]*MIL))
    for h,b in epru.live(pcb,'PAD'):
        if b.get('hole') and b['hole'].get('width'):
            holes.append((b['centerX']*MIL,-b['centerY']*MIL,b['hole']['width']*MIL,b['defaultPad'].get('width',0)*MIL,b.get('plated')))
    for h,b in epru.live(pcb,'STRING'):
        strings.append(dict(text=b['text'],x=b['x']*MIL,y=-b['y']*MIL,size=b['fontSize']*MIL,w=b['strokeWidth']*MIL,layer=b['layerId'],angle=b['angle']))
    return circ,lines,holes,strings
def setup_board(b,cfg):
    ds=b.GetDesignSettings()
    nl=cfg['layers']
    b.SetCopperLayerCount(nl)
    ds.SetBoardThickness(MM(1.6))
    ds.m_TrackMinWidth=MM(cfg.get('min_track',0.127)); ds.m_ViasMinSize=MM(0.45); ds.m_MinThroughDrill=MM(0.25)
    ds.m_MinClearance=MM(cfg.get('min_clear',0.127)); ds.m_CopperEdgeClearance=MM(0.3); ds.m_HoleClearance=MM(0.2); ds.m_HoleToHoleMin=MM(0.25)
    ds.m_MinSilkTextHeight=MM(0.6); ds.m_SilkClearance=MM(0.0)
    ns=ds.m_NetSettings
    def nc(name,w,clr,via,drill,dpw=None,dpg=None):
        c=pcbnew.NETCLASS(name)
        c.SetTrackWidth(MM(w)); c.SetClearance(MM(clr)); c.SetViaDiameter(MM(via)); c.SetViaDrill(MM(drill))
        if dpw: c.SetDiffPairWidth(MM(dpw)); c.SetDiffPairGap(MM(dpg))
        return c
    dflt=ns.GetDefaultNetclass()
    dt=cfg.get('default_track',(0.15,0.127)); dflt.SetTrackWidth(MM(dt[0])); dflt.SetClearance(MM(dt[1])); dv=cfg.get('default_via',(0.6,0.3)); dflt.SetViaDiameter(MM(dv[0])); dflt.SetViaDrill(MM(dv[1]))
    for n,(w,clr,via,drill,*dp) in cfg['netclasses'].items():
        ns.SetNetclass(n,nc(n,w,clr,via,drill,*dp))
    for pat,cls in cfg['netclass_assign'].items():
        ns.SetNetclassPatternAssignment(pat,cls)
    ds.m_TrackWidthList.clear() if hasattr(ds.m_TrackWidthList,'clear') else None
def add_outline(b,circ,lines,off):
    for cx,cy,r in circ:
        s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(V(cx+off[0],cy+off[1])); s.SetEnd(V(cx+off[0]+r,cy+off[1])); s.SetWidth(MM(0.1)); b.Add(s)
def add_hole(b,x,y,d,pad=None,plated=False,ref='MH'):
    f=pcbnew.FOOTPRINT(b); f.SetReference(ref); f.SetValue('MountingHole'); f.Reference().SetVisible(False); f.Value().SetVisible(False)
    p=pcbnew.PAD(f)
    if plated and pad:
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetSize(V(pad,pad)); p.SetLayerSet(pcbnew.PAD.PTHMask())
    else:
        p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetSize(V(d,d)); p.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetDrillSize(V(d,d)); p.SetNumber('1' if plated else '')
    f.Add(p); f.SetPosition(V(x,y)); f.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM|pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    p.SetPosition(V(x,y))
    for lay in (pcbnew.F_CrtYd,pcbnew.B_CrtYd):
        s=pcbnew.PCB_SHAPE(f); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(lay); s.SetCenter(V(x,y)); s.SetEnd(V(x+d/2+1.2,y)); s.SetWidth(MM(0.05)); f.Add(s)
    b.Add(f); return f
