import sys,importlib
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,post
from shapely.geometry import Point
cfg=importlib.import_module(sys.argv[1]).cfg; p=sys.argv[2]
b=pcbnew.LoadBoard(p)
R=pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetWidth())/2
cm={k:0.17 for k in cfg['pcb']['netclasses']}; cm['Default']=0.13
print('widened',post.widen(b,cfg['pcb']['widen'],Point(100,100).buffer(R-0.3,256),clrmap=cm))
b.SetLayerName(pcbnew.In1_Cu,'In1.GND_SIG')
pcbnew.SaveBoard(p,b)
