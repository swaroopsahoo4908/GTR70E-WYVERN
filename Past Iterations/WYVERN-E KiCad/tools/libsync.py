import pcbnew,sys,re,subprocess
p,lib=sys.argv[1],sys.argv[2]
subprocess.run(['kicad-cli','pcb','drc','-o','/tmp/w/_ls.rpt',p],capture_output=True)
refs=set(re.findall(r'Footprint (\S+)\n',open('/tmp/w/_ls.rpt').read().split('lib_footprint_mismatch',1)[1] if 'lib_footprint_mismatch' in open('/tmp/w/_ls.rpt').read() else ''))
txt=open('/tmp/w/_ls.rpt').read()
refs=set(m.group(1) for m in re.finditer(r'\[lib_footprint_mismatch\].*?\n.*?\n\s+@\([^)]*\): Footprint (\S+)',txt))
b=pcbnew.LoadBoard(p); io=pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
for f in b.GetFootprints():
    if f.GetReference() in refs:
        c=pcbnew.FOOTPRINT(f); c.SetParent(None)
        if c.GetLayer()==pcbnew.B_Cu: c.Flip(c.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        c.SetOrientationDegrees(0); c.SetPosition(pcbnew.VECTOR2I(0,0)); c.SetReference('REF**'); io.FootprintSave(lib,c)
print('lib synced',sorted(refs))
