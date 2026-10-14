import sys,re,pcbnew,subprocess
proj=sys.argv[1]; name=sys.argv[2]
pcbf=f'{proj}/{name}.kicad_pcb'; schf=f'{proj}/{name}.kicad_sch'
subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o','/tmp/w/_sync.net',schf],capture_output=True)
t=open('/tmp/w/_sync.net').read()
pinnet={}
for m in re.finditer(r'\(net\s*\(code "\d+"\)\s*\(name "([^"]*)"\)(.*?)\n\t\t\)',t,re.S):
    for r,p in re.findall(r'\(ref "([^"]*)"\)\s*\(pin "([^"]*)"',m.group(2)): pinnet[(r,p)]=m.group(1)
comps={}
for m in re.finditer(r'\(comp\s*\(ref "([^"]*)"\)\s*\(value "([^"]*)"\)(.*?)\n\t\t\)\n',t,re.S):
    d=re.search(r'\(description "([^"]*)"\)',m.group(3))
    flds=dict(re.findall(r'\(field\s*\(name "([^"]*)"\)\s*"([^"]*)"\)',m.group(3)))
    comps[m.group(1)]=dict(value=m.group(2),desc=d.group(1) if d else '',fields=flds)
b=pcbnew.LoadBoard(pcbf)
nets=b.GetNetInfo()
def net(nm):
    n=nets.GetNetItem(nm)
    if n is None or n.GetNetCode()<=0 and nm:
        n=pcbnew.NETINFO_ITEM(b,nm); b.Add(n)
    return n
chg=[]
for f in b.GetFootprints():
    r=f.GetReference()
    if r not in comps:
        if r.startswith('MH') or r.startswith('TP'):
            f.SetBoardOnly(True); f.SetExcludedFromBOM(True); f.SetExcludedFromPosFiles(True)
        continue
    c=comps[r]
    if f.GetValue()!=c['value']: chg.append(('value',r,f.GetValue(),c['value'])); f.SetValue(c['value'])
    fld=f.GetField('Description') if f.HasField('Description') else None
    if fld is not None and fld.GetText()!=c['desc']: fld.SetText(c['desc'])
    for k,v in c['fields'].items():
        if k in ('Footprint','Description','Reference','Value'): continue
        if f.HasField(k):
            if f.GetField(k).GetText()!=v: f.GetField(k).SetText(v)
        else:
            fd=pcbnew.PCB_FIELD(f,f.GetNextFieldOrdinal() if hasattr(f,'GetNextFieldOrdinal') else len(f.GetFields()),k); fd.SetText(v); fd.SetVisible(False); fd.SetLayer(f.GetLayer()==pcbnew.F_Cu and pcbnew.F_Fab or pcbnew.B_Fab); f.Add(fd)
    for p in f.Pads():
        k=(r,p.GetNumber())
        if not p.GetNumber(): continue
        want=pinnet.get(k)
        if want is None: continue
        have=p.GetNetname()
        if have!=want:
            if not want.startswith('unconnected-') or have: chg.append(('net',r,p.GetNumber(),have,want))
            p.SetNet(net(want))
for c in chg: print(c)
b.Save(pcbf)
