"""Move the known-good cell map onto the corrected grid, using the map's
measured position in the 5 Oct photo. Shapes and identities are preserved."""
import numpy as np, json, collections
PROJ="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket"
d=json.load(open(PROJ+"/data/blanket.json")); COLS,ROWS=72,90
old=np.array(d["cells"],dtype=np.int16).reshape(ROWS,COLS)
ys,xs=np.where(old>0)
print("old map spans rows %d-%d, cols %d-%d"%(ys.min(),ys.max(),xs.min(),xs.max()))
ismap=np.load("grid_ismap.npy"); sewn=np.load("grid_sewn.npy")
m=ismap&sewn; ys2,xs2=np.where(m)
R0,R1,C0,C1=ys2.min(),ys2.max(),xs2.min(),xs2.max()
print("measured map spans rows %d-%d, cols %d-%d (from the 5 Oct photo)"%(R0,R1,C0,C1))
sr=(R1-R0)/(ys.max()-ys.min()); sc=(C1-C0)/(xs.max()-xs.min())
print("vertical scale %.3f, horizontal scale %.3f"%(sr,sc))
new=np.zeros_like(old)
for r in range(ROWS):
    orow=(r-R0)/sr+ys.min()
    if orow< -0.5 or orow>ROWS-0.5: continue
    for c in range(COLS):
        ocol=(c-C0)/sc+xs.min()
        if ocol<-0.5 or ocol>COLS-0.5: continue
        v=old[int(round(orow))%ROWS, int(round(ocol))%COLS]
        if v>0: new[r,c]=v
cnt=collections.Counter(new.ravel().tolist())
NAMES=[r["name"] for r in d["regions"]]
TARGET={"Abruzzo":34,"Basilicata":24,"Calabria":42,"Campania":39,"Emilia-Romagna":64,
 "Friuli-Venezia Giulia":24,"Lazio":47,"Liguria":20,"Lombardy":84,"Marche":29,"Molise":12,
 "Piedmont":81,"Puglia":49,"Sardinia":65,"Sicily":65,"Tuscany":82,"Trentino-Alto Adige":42,
 "Umbria":27,"Aosta Valley":15,"Veneto":62}
print(f"\n{'region':<24}{'moved':>7}{'Nonna':>7}")
tot=0
for i,n in enumerate(NAMES,1):
    tot+=cnt[i]; print(f"{n:<24}{cnt[i]:>7}{TARGET[n]:>7}")
print(f"{'TOTAL':<24}{tot:>7}{sum(TARGET.values()):>7}")
ys3,xs3=np.where(new>0)
print("\nnew map spans rows %d-%d, cols %d-%d"%(ys3.min(),ys3.max(),xs3.min(),xs3.max()))
np.save("remapped.npy",new)
