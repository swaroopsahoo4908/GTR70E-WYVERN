import sys,pcbnew
p=sys.argv[1]; b=pcbnew.LoadBoard(p)
for i in range(b.GetAreaCount()):
    z=b.GetArea(i)
    if not z.GetZoneName().startswith('HC_'): z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
pcbnew.SaveBoard(p,b)
