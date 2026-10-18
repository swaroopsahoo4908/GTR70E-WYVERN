import sys,json,subprocess
sys.path.insert(0,'/tmp/w/conv')
import striptracks
p=sys.argv[1]
def drc():
    subprocess.run(['kicad-cli','pcb','drc','--severity-all','--refill-zones','--save-board','--format','json','-o','/tmp/w/_tidy.json',p],capture_output=True)
    return json.load(open('/tmp/w/_tidy.json'))
d=drc(); base=len(d['unconnected_items'])
for it in range(12):
    rm=set()
    for v in d['violations']:
        t=v['type']
        if t in ('track_dangling','via_dangling'):
            rm.add(v['items'][0]['uuid'])
        elif t in ('holes_co_located','hole_to_hole'):
            vias=[i for i in v['items'] if i['description'].startswith('Via')]
            if len(vias)==2: rm.add(vias[1]['uuid'])
    if not rm: break
    import shutil; shutil.copy(p,p+'.bak')
    n=striptracks.remove_uuids(p,p,rm)
    d=drc()
    print('round',it,'removed',n,'unconnected',len(d['unconnected_items']),flush=True)
    if len(d['unconnected_items'])>base:
        shutil.copy(p+'.bak',p); print('reverted round'); d=drc(); break
import os
if os.path.exists(p+'.bak'): os.remove(p+'.bak')
