"""Balance to Nonna's counts, peeling ragged cells first and growing compactly."""
import numpy as np, json, collections
P="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket/data/blanket.json"
d=json.load(open(P)); COLS,ROWS=72,90
NAME={r["id"]:r["name"] for r in d["regions"]}; ID={v:k for k,v in NAME.items()}
TARGET={ "Abruzzo":34,"Basilicata":24,"Calabria":42,"Campania":39,
 "Emilia-Romagna":64,"Friuli-Venezia Giulia":24,"Lazio":47,"Liguria":20,
 "Lombardy":84,"Marche":29,"Molise":12,"Piedmont":81,"Puglia":49,
 "Sardinia":65,"Sicily":65,"Tuscany":82,"Trentino-Alto Adige":42,
 "Umbria":27,"Aosta Valley":15,"Veneto":62 }
TGT={ID[k]:v for k,v in TARGET.items()}
g=np.load("shrunk.npy").copy()

def nbrs(r,c):
    o=[(r-1,c),(r+1,c)]
    o += [(r,c-1),(r,c+1),(r+1,c-1),(r+1,c+1)] if c%2==0 else [(r-1,c-1),(r-1,c+1),(r,c-1),(r,c+1)]
    return [(a,b) for a,b in o if 0<=a<ROWS and 0<=b<COLS]
NB=[[nbrs(r,c) for c in range(COLS)] for r in range(ROWS)]
def same(r,c,v): return sum(1 for n in NB[r][c] if g[n]==v)
def connected(v, skip=None, add=None):
    cs={(r,c) for r,c in zip(*np.where(g==v))}
    if skip: cs.discard(skip)
    if add: cs.add(add)
    if not cs: return True
    s=next(iter(cs)); seen={s}; st=[s]
    while st:
        r,c=st.pop()
        for n in NB[r][c]:
            if n in cs and n not in seen: seen.add(n); st.append(n)
    return len(seen)==len(cs)

for it in range(6000):
    cnt=collections.Counter(g.ravel().tolist())
    diffs={i:cnt[i]-TGT[i] for i in TGT}
    if all(v==0 for v in diffs.values()): break
    under={i for i,v in diffs.items() if v<0}
    done=False
    # shrink the most over-target region by peeling its most ragged edge cell
    for rid in sorted((i for i,v in diffs.items() if v>0), key=lambda i:-diffs[i]):
        best=None
        for r,c in zip(*np.where(g==rid)):
            ns=[g[n] for n in NB[r][c]]
            if all(n==rid for n in ns): continue
            takers=[n for n in set(ns) if n in under]
            dest = takers[0] if takers else (0 if 0 in ns else None)
            if dest is None: continue
            if not connected(rid, skip=(r,c)): continue
            k=same(r,c,rid)
            if best is None or k<best[0]: best=(k,r,c,dest)
        if best:
            _,r,c,dest=best; g[r,c]=dest; done=True; break
    if done: continue
    # otherwise let an under-target region take the ocean cell it hugs most
    for rid in sorted(under, key=lambda i:diffs[i]):
        best=None
        for r,c in zip(*np.where(g==rid)):
            for n in NB[r][c]:
                if g[n]!=0: continue
                k=same(n[0],n[1],rid)
                if best is None or k>best[0]: best=(k,n)
        if best: g[best[1]]=rid; done=True; break
    if not done: print("stuck",it); break

cnt=collections.Counter(g.ravel().tolist())
ok=all(cnt[i]==TGT[i] for i in TGT)
tend=sum(1 for i in TGT for r,c in zip(*np.where(g==i)) if same(r,c,i)<=1)
print("all counts exact:", ok)
print("map", sum(cnt[i] for i in NAME), " ocean", cnt[0], " total", sum(cnt[i] for i in NAME)+cnt[0])
print("cells with <=1 same-region neighbour (tendrils):", tend)
for i in TGT:
    if not connected(i): print("NOT CONNECTED", NAME[i])
np.save("balanced.npy", g)
