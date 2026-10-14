import sys,re
def strip(src,dst,keep_layer='In1.Cu'):
    t=open(src).read(); out=[];i=0
    pat=re.compile(r'\n\t\(zone[\s(]')
    while True:
        m=pat.search(t,i)
        if not m: out.append(t[i:]); break
        out.append(t[i:m.start()+1])
        j=m.start()+2; depth=0; k=j
        while True:
            c=t[k]
            if c=='(': depth+=1
            elif c==')':
                depth-=1
                if depth==0: break
            elif c=='"':
                k+=1
                while t[k]!='"':
                    if t[k]=='\\': k+=1
                    k+=1
            k+=1
        blk=t[m.start()+1:k+1]
        if f'(layer "{keep_layer}")' in blk or f'"{keep_layer}"' in blk.split('(hatch')[0]: out.append(blk)
        i=k+1
    open(dst,'w').write(''.join(out))
if __name__=='__main__': strip(sys.argv[1],sys.argv[2])
