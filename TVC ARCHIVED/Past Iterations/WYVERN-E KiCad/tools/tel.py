import re
def parse(f):
    t=open(f,encoding='utf-8',errors='replace').read()
    pk=t.split('$NETS')[0].split('$PACKAGES')[1].replace(',\n',' ')
    parts={}
    for line in pk.split('\n'):
        if ';' in line:
            a,b=line.split(';',1)
            fs=[x.strip().strip("'") for x in a.split('!')]
            for r in b.split():
                r=r.strip(',')
                if r: parts[r]={'fp':fs[0],'dev':fs[1],'val':fs[2]}
    nets={}
    body=t.split('$NETS')[1].split('$SCHEDULE')[0].split('$END')[0].replace(',\n',' ')
    for line in body.split('\n'):
        if ';' in line:
            a,b=line.split(';',1)
            n=a.strip().strip("'")
            nets[n]=sorted(x.strip(',') for x in b.split() if x.strip(','))
    return parts,nets
def canon(nets):
    return set(frozenset(v) for v in nets.values())
