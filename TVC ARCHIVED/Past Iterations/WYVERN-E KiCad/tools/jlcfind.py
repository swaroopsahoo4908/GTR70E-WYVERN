import jlc,sys
def find(kw,pkg,must=(),n=50):
    r=[x for x in jlc.search(kw,n) if x['pkg']==pkg and all(m.lower() in (x['desc'] or '').lower()+x['model'].lower() for m in must)]
    r.sort(key=lambda x:(x['type']!='base',not x['pref'],-(x['stock'] or 0)))
    return r
if __name__=='__main__':
    for q in sys.argv[1:]:
        kw,pkg=q.split('@'); 
        print('###',q)
        for x in find(kw,pkg)[:4]: print('  ',x['code'],x['type'],x['pref'],x['stock'],x['model'],'|',(x['desc'] or '')[:70])
