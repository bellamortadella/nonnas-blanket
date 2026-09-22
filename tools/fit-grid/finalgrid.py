import os
PROJ = os.environ.get("BLANKET_PROJ", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_PHOTO = os.path.join(PROJ, "reference", "blanket-2026-09-13.jpeg")
SRC_ESTIMATES = os.path.join(PROJ, "reference", "italy-region-hex-counts.json")
import numpy as np, json
from scipy import ndimage
BLOB2REG={23:"Aosta Valley",16:"Piedmont",5:"Lombardy",22:"Trentino-Alto Adige",
 3:"Veneto",8:"Veneto",7:"Friuli-Venezia Giulia",
 1:"Emilia-Romagna",2:"Emilia-Romagna",28:"Emilia-Romagna",29:"Emilia-Romagna",30:"Emilia-Romagna",
 15:"Liguria",19:"Tuscany",27:"Tuscany",11:"Marche",17:"Umbria",10:"Lazio",21:"Abruzzo",
 14:"Molise",6:"Campania",12:"Campania",13:"Campania",4:"Puglia",24:"Puglia",25:"Puglia",
 20:"Basilicata",26:"Calabria",18:"Sicily",9:"Sardinia"}
REGJ=json.load(open(SRC_ESTIMATES))["regions"]
names=[r["region"] for r in REGJ]
rid={n:i+1 for i,n in enumerate(names)}   # 0 = ocean
comp=np.load("comp.npy"); C=np.load("centres72.npy"); sewn=np.load("sewn72.npy"); ismap=np.load("ismap72.npy")
ROWS,COLS=sewn.shape; Ih,Iw=comp.shape
xi=np.clip(C[:,:,0].astype(int),0,Iw-1); yi=np.clip(C[:,:,1].astype(int),0,Ih-1)
cells=np.zeros((ROWS,COLS),int)
mapcell=(ismap>0.5)
# majority blob within a small disc per cell
for r in range(ROWS):
    for c in range(COLS):
        if not mapcell[r,c]: continue
        x,y=xi[r,c],yi[r,c]
        w=comp[max(0,y-4):y+5, max(0,x-4):x+5].ravel()
        w=w[w>0]
        if len(w)==0: mapcell[r,c]=False; continue
        b=np.bincount(w).argmax()
        cells[r,c]=rid.get(BLOB2REG.get(int(b),""),0)
        if cells[r,c]==0: mapcell[r,c]=False

# clean: keep each region as its single largest connected blob on the hex grid (hex adjacency)
def hex_neighbours(r,c):
    par=c%2   # parity=0 -> even cols shifted down by 0.5 (from phase search parity=0 means off applied when c%2==0)
    d=+1 if par==0 else -1
    yield r,c-1; yield r,c+1; yield r-1,c; yield r+1,c
    yield r+d,c-1; yield r+d,c+1
def components(mask):
    seen=np.zeros_like(mask,bool); comps=[]
    for r in range(ROWS):
        for c in range(COLS):
            if mask[r,c] and not seen[r,c]:
                st=[(r,c)]; seen[r,c]=True; acc=[]
                while st:
                    y,x=st.pop(); acc.append((y,x))
                    for ny,nx in hex_neighbours(y,x):
                        if 0<=ny<ROWS and 0<=nx<COLS and mask[ny,nx] and not seen[ny,nx]:
                            seen[ny,nx]=True; st.append((ny,nx))
                comps.append(acc)
    return comps
for k,n in enumerate(names,1):
    comps=components(cells==k)
    if len(comps)<=1: continue
    comps.sort(key=len,reverse=True)
    for acc in comps[1:]:
        for y,x in acc: cells[y,x]=0   # drop stray fragments to ocean, refilled below
# refill dropped map cells from nearest labelled map neighbour
for _ in range(6):
    holes=[(r,c) for r in range(ROWS) for c in range(COLS) if mapcell[r,c] and cells[r,c]==0]
    if not holes: break
    for r,c in holes:
        vals=[cells[y,x] for y,x in hex_neighbours(r,c) if 0<=y<ROWS and 0<=x<COLS and cells[y,x]>0]
        if vals: cells[r,c]=max(set(vals),key=vals.count)
    else: pass
np.save("cells.npy",cells)
cnt=np.bincount(cells.ravel(),minlength=21)
print(f"{'region':<24}{'photo':>7}{'est':>6}{'range':>9}{'diff':>7}  flag")
tot=0
for k,n in enumerate(names,1):
    r=REGJ[k-1]; d=cnt[k]-r["estimate"]; tot+=cnt[k]
    print(f"{n:<24}{cnt[k]:>7}{r['estimate']:>6}{str(r['low'])+'-'+str(r['high']):>9}{d:>+7}  {'<<' if abs(d)>3 else ''}")
print(f"{'MAP TOTAL':<24}{tot:>7}{464:>6}")
print(f"{'ocean cells':<24}{cnt[0]:>7}")
print("sewn",int(sewn.sum()),"unsewn",int((~sewn).sum()))
print("ratio photo/est %.2f"%(tot/464))
