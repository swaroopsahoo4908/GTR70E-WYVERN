import sys,pcbnew
src,dst=sys.argv[1],sys.argv[2]
b=pcbnew.LoadBoard(src)
print(pcbnew.ExportSpecctraDSN(b,dst))
s=open(dst).read(); i=s.index('(class HighCurrent'); j=s.index('(use_via',i)
s=s[:j]+'(use_layer F.Cu B.Cu)\n        '+s[j:]; open(dst,'w').write(s)
