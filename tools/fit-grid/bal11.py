import numpy as np, json, collections
from scipy import ndimage
PROJ="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket"
d=json.load(open(PROJ+"/data/blanket.json")); COLS,ROWS=72,90
NAMES=[r["name"] for r in d["regions"]]; RID={n:i+1 for i,n in enumerate(NAMES)}
TGT={RID[r["name"]]:r["count"] for r in d["regions"]}
g=np.load("g11.npy").astype(np.int16)
cal,sic,bas=RID["Calabria"],RID["Sicily"],RID["Basilicata"]
MAIN=set(TGT)-{sic,RID["Sardinia"]}
def nbrs(r,c):
    o=[(r-1,c),(r+1,c)]
    o+=[(r,c-1),(r,c+1),(r+1,c-1),(r+1,c+1)] if c%2==0 else [(r-1,c-1),(r-1,c+1),(r,c-1),(r,c+1)]
    return [(a,b) for a,b in o if 0<=a<ROWS and 0<=b<COLS]
NB=[[nbrs(r,c) for c in range(COLS)] for r in range(ROWS)]
def cells(v): return {(r,c) for r,c in zip(*np.where(g==v))}
def comp_ok(cs):
    if not cs: return True
    s=next(iter(cs)); seen={s}; st=[s]
    while st:
        r,c=st.pop()
        for n in NB[r][c]:
            if n in cs and n not in seen: seen.add(n); st.append(n)
    return len(seen)==len(cs)
# 1. defragment
for _ in range(5):
    for v in TGT:
        m=(g==v)
        if not m.any(): continue
        lab,n=ndimage.label(m,structure=np.ones((3,3)))
        if n<=1: continue
        sz=[(lab==i).sum() for i in range(1,n+1)]
        keep=1+int(np.argmax(sz))
        for r,c in zip(*np.where(m&(lab!=keep))):
            vs=[g[x] for x in NB[r][c] if g[x]!=v]
            g[r,c]=collections.Counter(vs).most_common(1)[0][0] if vs else 0
def reg_ok(v,skip=None,add=None):
    cs=cells(v)
    if skip: cs.discard(skip)
    if add: cs.add(add)
    return comp_ok(cs)
def main_ok(skip=None,add=None,who=None):
    cs={(r,c) for r,c in zip(*np.where(np.isin(g,list(MAIN))))}
    if skip and g[skip] in MAIN: cs.discard(skip)
    if add and who in MAIN: cs.add(add)
    return comp_ok(cs)
def cal_ok():
    cs=cells(cal)
    nb={int(g[n]) for p in cs for n in NB[p[0]][p[1]]}-{cal}
    return nb<= {0,bas} and bas in nb
def same(r,c,v): return sum(1 for n in NB[r][c] if g[n]==v)
print("after defrag: map",int((g>0).sum()))
for it in range(20000):
    cnt=collections.Counter(g.ravel().tolist())
    diffs={i:cnt[i]-TGT[i] for i in TGT}
    if all(v==0 for v in diffs.values()): break
    under={i for i,v in diffs.items() if v<0}
    done=False
    for rid in sorted((i for i,v in diffs.items() if v>0), key=lambda i:-diffs[i]):
        best=None
        for r,c in zip(*np.where(g==rid)):
            ns=[int(g[n]) for n in NB[r][c]]
            if all(n==rid for n in ns): continue
            for dest in ([n for n in set(ns) if n in under] or ([0] if 0 in ns else [])):
                old=int(g[r,c]); g[r,c]=dest
                good=reg_ok(rid) and (dest==0 or reg_ok(dest)) and main_ok() and cal_ok()
                g[r,c]=old
                if not good: continue
                k=same(r,c,rid)
                if best is None or k<best[0]: best=(k,r,c,dest)
                break
        if best:
            _,r,c,dest=best; g[r,c]=dest; done=True; break
    if done: continue
    for rid in sorted(under,key=lambda i:diffs[i]):
        best=None
        for r,c in zip(*np.where(g==rid)):
            for n in NB[r][c]:
                if g[n]!=0: continue
                old=int(g[n]); g[n]=rid
                good=reg_ok(rid) and main_ok() and cal_ok()
                g[n]=old
                if not good: continue
                k=same(n[0],n[1],rid)
                if best is None or k>best[0]: best=(k,n)
        if best: g[best[1]]=rid; done=True; break
    if not done: print("stuck at",it); break
cnt=collections.Counter(g.ravel().tolist())
print("all exact:",all(cnt[i]==TGT[i] for i in TGT),"| map",sum(cnt[i] for i in TGT),"| ocean",cnt[0])
print("every region one piece:",all(comp_ok(cells(v)) for v in TGT))
print("mainland one piece:",main_ok())
nb={int(g[n]) for p in cells(cal) for n in NB[p[0]][p[1]]}-{cal}
print("Calabria borders:",{NAMES[v-1] if v>0 else 'Ocean' for v in nb})
print("Calabria cells on the Basilicata border:",sum(1 for p in cells(cal) if any(g[n]==bas for n in NB[p[0]][p[1]])))
def ax(r,c): return (c, r-(c-(c&1))//2)
def hd(a,b):
    q1,r1=ax(*a); q2,r2=ax(*b); return (abs(q1-q2)+abs(q1+r1-q2-r2)+abs(r1-r2))//2
print("Calabria-Sicily gap:",min(hd(a,b) for a in cells(cal) for b in cells(sic)))
np.save("g11_bal.npy",g)
