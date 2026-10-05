import numpy as np, json, collections
PROJ="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket"
d=json.load(open(PROJ+"/data/blanket.json")); COLS,ROWS=72,90
NAMES=[r["name"] for r in d["regions"]]; RID={n:i+1 for i,n in enumerate(NAMES)}
g=np.array(d["cells"],dtype=np.int16).reshape(ROWS,COLS)
def nbrs(r,c):
    o=[(r-1,c),(r+1,c)]
    o+=[(r,c-1),(r,c+1),(r+1,c-1),(r+1,c+1)] if c%2==0 else [(r-1,c-1),(r-1,c+1),(r,c-1),(r,c+1)]
    return [(a,b) for a,b in o if 0<=a<ROWS and 0<=b<COLS]
NB=[[nbrs(r,c) for c in range(COLS)] for r in range(ROWS)]
cal,bas=RID["Calabria"],RID["Basilicata"]
def comp_ok(cs):
    if not cs: return True
    s=next(iter(cs)); seen={s}; st=[s]
    while st:
        r,c=st.pop()
        for n in NB[r][c]:
            if n in cs and n not in seen: seen.add(n); st.append(n)
    return len(seen)==len(cs)
def cells(v): return {(r,c) for r,c in zip(*np.where(g==v))}
# an ocean cell touching both Calabria and Basilicata bridges the strait
bridges=[]
for r in range(ROWS):
    for c in range(COLS):
        if g[r,c]!=0: continue
        ns={int(g[n]) for n in NB[r][c]}
        if cal in ns and bas in ns: bridges.append((r,c))
print("ocean cells touching both Calabria and Basilicata:",bridges)
if not bridges:
    # widen: allow a 2-step bridge via a cell adjacent to Calabria and to a Basilicata-adjacent cell
    for r in range(ROWS):
        for c in range(COLS):
            if g[r,c]!=0: continue
            if cal not in {int(g[n]) for n in NB[r][c]}: continue
            for n in NB[r][c]:
                if g[n]==0 and bas in {int(g[m]) for m in NB[n[0]][n[1]]}:
                    bridges.append((r,c)); break
    print("two-step bridge candidates:",bridges[:5])
b=bridges[0]
g[b]=bas
print("bridged at",b,"-> Basilicata now",int((g==bas).sum()))
# give a cell back so Basilicata keeps its count of 24
got=False
for r,c in sorted(cells(bas), key=lambda p:-sum(1 for n in NB[p[0]][p[1]] if g[n]==0)):
    if (r,c)==b: continue
    if 0 not in {int(g[n]) for n in NB[r][c]}: continue
    cs=cells(bas)-{(r,c)}
    if not comp_ok(cs): continue
    g[r,c]=0; got=True; print("returned",(r,c),"to ocean -> Basilicata",int((g==bas).sum())); break
assert got, "could not rebalance Basilicata"
mainland=[RID[n] for n in NAMES if n not in ("Sicily","Sardinia")]
print("mainland one piece:", comp_ok({(r,c) for r,c in zip(*np.where(np.isin(g,mainland)))}))
print("Calabria touches Basilicata:", any(g[n]==bas for p in cells(cal) for n in NB[p[0]][p[1]]))
cnt=collections.Counter(g.ravel().tolist())
TARGET={"Abruzzo":34,"Basilicata":24,"Calabria":42,"Campania":39,"Emilia-Romagna":64,
 "Friuli-Venezia Giulia":24,"Lazio":47,"Liguria":20,"Lombardy":84,"Marche":29,"Molise":12,
 "Piedmont":81,"Puglia":49,"Sardinia":65,"Sicily":65,"Tuscany":82,"Trentino-Alto Adige":42,
 "Umbria":27,"Aosta Valley":15,"Veneto":62}
print("all counts still exact:", all(cnt[RID[k]]==v for k,v in TARGET.items()))
print("every region one piece:", all(comp_ok(cells(RID[k])) for k in TARGET))
np.save("cal_fixed.npy",g)
