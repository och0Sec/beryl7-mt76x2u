import sys,re,difflib,collections
k=sys.argv[1]
a=open(f'/build/cmp/{k}.mine.n').read().split('\n'); b=open(f'/build/cmp/{k}.gl.n').read().split('\n')
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
pairs=collections.Counter(); other=[]; funcs=collections.Counter()
def fn(i):
    while i>=0 and not a[i].startswith('FUNC'): i-=1
    return a[i][5:] if i>=0 else '?'
num=re.compile(r'#(-?\d+|0x[0-9a-f]+)')
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if tag=='replace' and i2-i1==j2-j1:
        for x,y in zip(a[i1:i2],b[j1:j2]):
            if 'R_AARCH64' in x: continue
            nx,ny=num.findall(x),num.findall(y)
            if num.sub('#N',x)==num.sub('#N',y) and len(nx)==len(ny):
                for p,q in zip(nx,ny):
                    if p!=q: pairs[(p,q,int(q,0)-int(p,0))]+=1
            else: other.append((fn(i1),x,y)); funcs[fn(i1)]+=1
    else:
        other.append((fn(i1),'|'.join(a[i1:i2])[:150],'|'.join(b[j1:j2])[:150])); funcs[fn(i1)]+=1
d=collections.Counter()
for (p,q,dl),c in pairs.items(): d[dl]+=c
print(k,'offset deltas:',d.most_common(8))
print('top pairs:',[(p,q,c) for (p,q,_),c in pairs.most_common(14)])
print('non-offset diffs:',len(other),'in funcs:',funcs.most_common(12))
for o in other[:int(sys.argv[2]) if len(sys.argv)>2 else 6]: print('  ',o)
