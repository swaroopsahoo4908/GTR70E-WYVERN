import sys,pcbnew,collections,json
b=pcbnew.LoadBoard(sys.argv[1])
fp=list(b.Footprints()); real=[f for f in fp if not f.GetReference().startswith('MH')]
top=sum(1 for f in real if f.GetLayer()==pcbnew.F_Cu); bot=len(real)-top
tr=[t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK']; vi=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
L=sum(t.GetLength() for t in tr)/1e6
cls=collections.defaultdict(list)
for t in tr: cls[t.GetNetClassName()].append(round(pcbnew.ToMM(t.GetWidth()),3))
nets=set(p.GetNetname() for f in fp for p in f.Pads() if p.GetNetname())
lay=collections.Counter(b.GetLayerName(t.GetLayer()) for t in tr)
vs=collections.Counter((round(pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)),2),round(pcbnew.ToMM(v.GetDrillValue()),2)) for v in vi)
gndv=sum(1 for v in vi if v.GetNetname()=='GND')
out=dict(parts=len(real),top=top,bottom=bot,holes=len(fp)-len(real),nets=len(nets),segments=len(tr),track_m=round(L/1000,3),vias=len(vi),gnd_vias=gndv,via_sizes={str(k):v for k,v in vs.items()},
  layers=dict(lay),widths={k:dict(min=min(v),max=max(v),n=len(v),hist=collections.Counter(v).most_common(4)) for k,v in cls.items()},
  zones=[(b.GetArea(i).GetNetname(),b.GetLayerName(b.GetArea(i).GetLayer())) for i in range(b.GetAreaCount())],
  size=round(pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetWidth()),2))
print(json.dumps(out,indent=1))
