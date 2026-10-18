import json,subprocess,os,sys,hashlib,time
CACHE='/tmp/w/jlc/cache.json'
C=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def _post(body):
    k=json.dumps(body,sort_keys=True)
    if k in C: return C[k]
    for i in range(3):
        r=subprocess.run(['curl','-sS','-m','30','-X','POST','-H','Content-Type: application/json','-d',k,
          'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'],capture_output=True,text=True)
        try:
            d=json.loads(r.stdout); break
        except Exception: time.sleep(2)
    else: raise RuntimeError(r.stdout[:300]+r.stderr)
    C[k]=d; json.dump(C,open(CACHE,'w')); return d
def rows(d):
    L=((d.get('data') or {}).get('componentPageInfo') or {}).get('list') or []
    out=[]
    for x in L:
        out.append(dict(code=x.get('componentCode'),model=x.get('componentModelEn'),pkg=x.get('componentSpecificationEn'),
            type=x.get('componentLibraryType'),pref=x.get('preferredComponentFlag'),stock=x.get('stockCount'),
            desc=x.get('describe') or x.get('erpComponentName'),brand=x.get('componentBrandEn'),price=(x.get('componentPrices') or [{}])[0].get('productPrice')))
    return out
def lookup(code):
    r=[x for x in rows(_post({"keyword":code,"currentPage":1,"pageSize":10})) if x['code']==code]
    return r[0] if r else None
def search(kw,n=25):
    return rows(_post({"keyword":kw,"currentPage":1,"pageSize":n}))
if __name__=='__main__':
    if sys.argv[1]=='s':
        for x in search(' '.join(sys.argv[2:])): print(x)
    else:
        for c in sys.argv[1:]: print(lookup(c))
