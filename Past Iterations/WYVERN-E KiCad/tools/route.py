import sys,os,subprocess,math,json
sys.path.insert(0,'/tmp/w/conv')
import pcbnew
from pcbbuild import V,MM
def circle_poly(cx,cy,r,n=180):
    return [(cx+r*math.cos(2*math.pi*i/n),cy+r*math.sin(2*math.pi*i/n)) for i in range(n)]
def add_zone(b,layer,netname,pts,prio=0,clear=0.25,minw=0.2,thermal=True,name=''):
    z=pcbnew.ZONE(b); z.SetLayer(layer); 
    ni=b.FindNet(netname); z.SetNet(ni)
    o=z.Outline(); o.NewOutline()
    for x,y in pts: o.Append(MM(x),MM(y))
    z.SetAssignedPriority(prio); z.SetLocalClearance(MM(clear)); z.SetMinThickness(MM(minw))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name or f'{netname}_{b.GetLayerName(layer)}')
    b.Add(z); return z
def fill(b):
    zs=[b.GetArea(i) for i in range(b.GetAreaCount())]
    pcbnew.ZONE_FILLER(b).Fill(zs)
def freeroute(dsn,ses,passes=40,threads=4,timeout=3600):
    cmd=['java','-Xmx6g','-jar','/opt/fr/freerouting.jar','-de',dsn,'-do',ses,'-mp',str(passes),'-mt',str(threads),'--gui.enabled=false','-dct','0']
    print(' '.join(cmd),flush=True)
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    log=r.stdout+r.stderr
    open(ses+'.log','w').write(log)
    return log
