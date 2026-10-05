"""Rescale the fitted cell map to Nonna's own per-region hexagon counts."""
import numpy as np, json, collections
P="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket/data/blanket.json"
d=json.load(open(P)); COLS,ROWS=d["config"]["grid"]["cols"], d["config"]["grid"]["rows"]
cells=np.array(d["cells"],dtype=np.int16).reshape(ROWS,COLS)
NAME={r["id"]:r["name"] for r in d["regions"]}; ID={v:k for k,v in NAME.items()}

TARGET={ "Abruzzo":34,"Basilicata":24,"Calabria":42,"Campania":39,
 "Emilia-Romagna":64,"Friuli-Venezia Giulia":24,"Lazio":47,"Liguria":20,
 "Lombardy":84,"Marche":29,"Molise":12,"Piedmont":81,"Puglia":49,
 "Sardinia":65,"Sicily":65,"Tuscany":82,"Trentino-Alto Adige":42,
 "Umbria":27,"Aosta Valley":15,"Veneto":62 }
assert set(TARGET)==set(ID), set(TARGET)^set(ID)
print("Nonna's map total:", sum(TARGET.values()))
cur=collections.Counter(cells.ravel().tolist())
print("fitted map total :", sum(cur[i] for i in NAME))
print()
print(f"{'region':<24}{'fitted':>7}{'Nonna':>7}{'diff':>7}")
for n,t in sorted(TARGET.items(), key=lambda kv:-kv[1]):
    print(f"{n:<24}{cur[ID[n]]:>7}{t:>7}{cur[ID[n]]-t:>+7}")

# ---- step 1: shrink the whole map about its centroid to the right area ----
S3=np.sqrt(3)
def centre(r,c): return (1.0+c*1.5, (r + (0.5 if c%2==0 else 0.0) + 0.5)*S3)
ys,xs=np.where(cells>0)
pts=np.array([centre(r,c) for r,c in zip(ys,xs)])
cen=pts.mean(0)
scale=np.sqrt(sum(TARGET.values())/ (cells>0).sum())
print(f"\nlinear shrink factor {scale:.4f}")

# nearest fitted cell lookup for arbitrary hex-space points
allc=[(r,c) for r in range(ROWS) for c in range(COLS)]
allp=np.array([centre(r,c) for r,c in allc])
new=np.zeros_like(cells)
for (r,c),p in zip(allc,allp):
    q=cen+(p-cen)/scale                      # sample the OLD map, expanded
    k=np.argmin(((allp-q)**2).sum(1))
    rr,cc=allc[k]
    new[r,c]=cells[rr,cc]
cur2=collections.Counter(new.ravel().tolist())
print("after shrink, map total:", sum(cur2[i] for i in NAME))
np.save("shrunk.npy",new); np.save("fitted.npy",cells)
