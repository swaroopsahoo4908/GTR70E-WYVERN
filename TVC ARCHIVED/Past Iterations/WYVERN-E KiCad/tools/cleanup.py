import sys,json,subprocess,importlib
sys.path.insert(0,'/tmp/w/conv')
import pcbnew
def cleanup(path,rounds=1):
    for r in range(rounds):
        subprocess.run(['kicad-cli','pcb','drc','--format','json','-o','/tmp/w/_cl.json',path],capture_output=True)
        d=json.load(open('/tmp/w/_cl.json'))
        bad=set()
        for v in d['violations']:
            if v['type'] in ('clearance','shorting_items','tracks_crossing','hole_clearance','copper_edge_clearance','track_dangling','via_dangling','hole_to_hole','holes_co_located'):
                for it in v['items']:
                    if it['description'].startswith(('Track','Via','Arc')): bad.add(it['uuid'])
        b=pcbnew.LoadBoard(path)
        n=0
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in bad: b.Remove(t); n+=1
        pcbnew.SaveBoard(path,b)
        print('cleanup round',r,'removed',n,flush=True)
        if n==0: break
if __name__=='__main__':
    cleanup(sys.argv[1])
