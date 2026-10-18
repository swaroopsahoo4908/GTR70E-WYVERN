import sys,os,pickle
sys.path.insert(0,os.path.dirname(__file__))
from verify import verify
brd,netlist,fails=pickle.load(open(sys.argv[1],"rb"))
ok=verify(brd,netlist,sys.argv[2])
print("verify_ok=",ok,"routing_fails=",fails)
sys.exit(0 if ok and not fails else 1)
