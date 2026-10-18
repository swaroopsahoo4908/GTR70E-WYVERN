import sys,json,math,collections,importlib
sys.path.insert(0,'/tmp/w/conv')
import pcbnew,epru
from pcbbuild import V,MM
MIL=0.0254
def legacy_copper(b,D,des,off,removed,layer_map,drop_layers=(),exclude=()):
    pcb=[d for d in D if d['head']['docType']=='PCB'][0]; epru.resolve(pcb)
    ref={}
    for h,bb in epru.live(pcb,'ATTR'):
        if bb['key']=='Designator': ref[bb['parentId']]=bb['value']
    epins=collections.defaultdict(set)
    for h,bb in epru.live(pcb,'PAD_NET'):
        _,cid,num,_=json.loads(h['id'])
        if bb['padNet']: epins[bb['padNet']].add(f"{ref.get(cid,'?')}.{num}")
    final=des['nets']
    nmap={}
    for en,ps in epins.items():
        ps2=[p for p in ps if p.split('.')[0] not in removed]
        fn={final.get(p) for p in ps2}
        if len(fn)==1 and None not in fn:
            fv=fn.pop()
            if fv not in exclude: nmap[en]=fv
    keep=collections.Counter();drop=collections.Counter()
    def P(x,y): return (x*MIL+off[0],-y*MIL+off[1])
    for h,bb in epru.live(pcb,'LINE'):
        en=bb['netName']; L=bb['layerId']
        if L in drop_layers or L not in layer_map or en not in nmap: drop[en]+=1; continue
        t=pcbnew.PCB_TRACK(b); t.SetStart(V(*P(bb['startX'],bb['startY']))); t.SetEnd(V(*P(bb['endX'],bb['endY'])))
        t.SetWidth(MM(bb['width']*MIL)); t.SetLayer(layer_map[L]); t.SetNet(b.FindNet(nmap[en])); b.Add(t); keep[en]+=1
    for h,bb in epru.live(pcb,'ARC'):
        en=bb['netName']; L=bb['layerId']
        if L in drop_layers or L not in layer_map or en not in nmap: drop[en]+=1; continue
        t=pcbnew.PCB_TRACK(b); t.SetStart(V(*P(bb['startX'],bb['startY']))); t.SetEnd(V(*P(bb['endX'],bb['endY'])))
        t.SetWidth(MM(bb['width']*MIL)); t.SetLayer(layer_map[L]); t.SetNet(b.FindNet(nmap[en])); b.Add(t); keep[en]+=1
    for h,bb in epru.live(pcb,'VIA'):
        en=bb['netName']
        if en not in nmap: drop[en]+=1; continue
        v=pcbnew.PCB_VIA(b); v.SetPosition(V(*P(bb['centerX'],bb['centerY']))); v.SetWidth(MM(bb['viaDiameter']*MIL)); v.SetDrill(MM(bb['holeDiameter']*MIL))
        v.SetNet(b.FindNet(nmap[en])); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); keep[en]+=1
    return sum(keep.values()),sum(drop.values()),sorted(e for e in drop if e)
