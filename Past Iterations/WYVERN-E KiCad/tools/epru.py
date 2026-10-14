import json,collections
def load(path):
    docs=[];cur=None
    for ln in open(path,encoding='utf-8'):
        ln=ln.rstrip('\n')
        if not ln.strip(): continue
        h,_,rest=ln.partition('||')
        hj=json.loads(h)
        body=rest[:-1] if rest.endswith('|') else rest
        try: bj=json.loads(body) if body else None
        except Exception: bj=body
        if hj['type']=='DOCHEAD':
            cur={'head':bj,'recs':[]};docs.append(cur)
        else: cur['recs'].append((hj,bj))
    return docs
def bytype(doc,t): return [(h,b) for h,b in doc['recs'] if h['type']==t]

def resolve(doc):
    """log-structured: keep highest ticket per id; drop deleted (None)"""
    best={}
    order=[]
    for h,b in doc['recs']:
        k=(h['type'],h['id'])
        if k not in best: order.append(k)
        if k not in best or h['ticket']>=best[k][0]['ticket']:
            best[k]=(h,b)
    out=[best[k] for k in order if best[k][1] is not None]
    doc['live']=out
    return out
def live(doc,t): return [(h,b) for h,b in doc['live'] if h['type']==t]
