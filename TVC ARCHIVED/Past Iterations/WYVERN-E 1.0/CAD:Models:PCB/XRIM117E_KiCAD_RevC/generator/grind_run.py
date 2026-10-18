#!/usr/bin/env python3
"""Drive grind() on a gen_*.py board build. Usage: grind_run.py <gen.py> <NAME> <out_dir> <base|budget>"""
import sys, os, types, time, pickle
sys.path.insert(0, os.path.dirname(__file__))
from grind import grind
from verify import verify

GEN=sys.argv[1]; NAME=sys.argv[2]; OUT=sys.argv[3]
BUDGET=float(sys.argv[4]) if len(sys.argv)>4 else 38.0

src=open(GEN).read()
# capture the order/widths/sn build by executing up to the Router construction
cut=src.index("    rt=Router(brd,widths)")
body=src[:cut] + "    globals()['_BRD']=brd\n    globals()['_NL']=sch.netlist\n    globals()['_W']=widths\n    globals()['_ORDER']=order if 'order' in dir() else []\n    return\n"
# 'order' defined after Router in originals; grab it too -> include a few lines after cut
after=src[cut:]
import re
m=re.search(r"order=\[(.*?)\]", after, re.S)
order_src = "order=["+m.group(1)+"]" if m else "order=[]"

mod=types.ModuleType("genmod"); mod.__dict__['__file__']=GEN
def build_fn():
    g={'__file__':GEN}
    exec(compile(body,'genbody','exec'), g)
    g['main']()
    brd=g['_BRD']; nl=g['_NL']; w=g['_W']
    allnets=set(n for n in brd.nets if n and n!="GND")
    build_fn.netlist=nl; build_fn.widths=w
    return brd, nl, allnets

# discover order + widths once
g0={'__file__':GEN}; exec(compile(body,'genbody','exec'), g0); g0['main']()
WIDTHS=g0['_W']
exec(compile(order_src,'ord','exec'), g0)
ORDER=g0.get('order',[])

brd, netlist, fails = grind(build_fn, ORDER, WIDTHS, NAME, time_budget=BUDGET)
ok=verify(brd, netlist, NAME)
os.makedirs(OUT, exist_ok=True)
# locate base filename from gen
import re as _re
base=_re.search(r'base\s*=\s*[\'"]([^\'"]+)[\'"]', src)
if base: base=base.group(1)
else:
    base={"CCM":"CCM_Central_Command_Module","SDM":"SDM_Solenoid_Drive_Module"}[NAME]
from kicadgen import project_file
# need the schematic text — re-exec full main once to emit sch
open(os.path.join(OUT,base+".kicad_pcb"),"w").write(brd.emit())
pickle.dump((brd,netlist,fails),open(os.path.join(OUT,"chk.pkl"),"wb"))
print(f"GRIND {NAME}: {len(fails)} fails, verify_ok={ok}")
print("FAILS:", fails)
