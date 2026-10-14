import pcbnew,sexp,re
from pcbbuild import V,MM
def import_ses(b,path):
    T=sexp.parse(open(path).read())
    routes=sexp.find(T,'routes')[0]
    res=sexp.find(routes,'resolution')[0]; scale={'um':1e-3,'mm':1,'mil':0.0254,'inch':25.4}[res[1]]/float(res[2])
    lib={}
    lo=sexp.find(routes,'library_out')
    if lo:
        for ps in sexp.find(lo[0],'padstack'):
            name=ps[1]; m=re.search(r'_(\d+):(\d+)_um',name)
            if m: lib[name]=(int(m.group(1))/1000,int(m.group(2))/1000)
    lname={b.GetLayerName(l):l for l in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]}
    for l in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]: lname[pcbnew.BOARD.GetStandardLayerName(l)]=l
    lname.update({'In1.SIG_GND':pcbnew.In1_Cu,'In1.GND':pcbnew.In1_Cu,'In2.SIG_PWR':pcbnew.In2_Cu,'In2.PWR':pcbnew.In2_Cu})
    nt=nv=0
    for net in sexp.find(sexp.find(routes,'network_out')[0],'net'):
        ni=b.FindNet(net[1])
        for w in sexp.find(net,'wire'):
            p=sexp.find(w,'path')[0]; L=lname[p[1]]; wd=float(p[2])*scale
            c=[float(x)*scale for x in p[3:]]
            pts=[(c[i],-c[i+1]) for i in range(0,len(c),2)]
            for a,z in zip(pts,pts[1:]):
                t=pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*z)); t.SetWidth(MM(wd)); t.SetLayer(L); t.SetNet(ni); b.Add(t); nt+=1
        for v in sexp.find(net,'via'):
            d,dr=lib.get(v[1],(0.6,0.3))
            x,y=float(v[2])*scale,-float(v[3])*scale
            vi=pcbnew.PCB_VIA(b); vi.SetPosition(V(x,y)); vi.SetWidth(MM(d)); vi.SetDrill(MM(dr)); vi.SetNet(ni); vi.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(vi); nv+=1
    return nt,nv
