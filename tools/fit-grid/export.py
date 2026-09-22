import os
PROJ = os.environ.get("BLANKET_PROJ", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_PHOTO = os.path.join(PROJ, "reference", "blanket-2026-09-13.jpeg")
SRC_ESTIMATES = os.path.join(PROJ, "reference", "italy-region-hex-counts.json")
import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage
COLS,ROWS=72,90
cells=np.load("cells.npy").copy()
corr=np.load("corr.npy"); C=np.load("centres72.npy")
REGJ=json.load(open(SRC_ESTIMATES))["regions"]
names=[r["region"] for r in REGJ]

# ---- clean missing sections to exact rectangles measured from the photo ----
MISS_ROWS=34
sewn=np.ones((ROWS,COLS),bool)
sewn[0:MISS_ROWS, 0:6]=False        # left  section, 6 wide
sewn[0:MISS_ROWS, COLS-8:COLS]=False# right section, 8 wide
cells[~sewn]=0                      # unsewn is ocean-to-be

# ---- representative colour per region, from the corrected photo ----
Ih,Iw,_=corr.shape
xi=np.clip(C[:,:,0].astype(int),0,Iw-1); yi=np.clip(C[:,:,1].astype(int),0,Ih-1)
cols_out=[]
for k,n in enumerate(names,1):
    m=(cells==k)
    if m.sum()==0: cols_out.append(REGJ[k-1]["colour"]); continue
    px=corr[yi[m],xi[m]]
    med=np.median(px,0)
    cols_out.append("#%02x%02x%02x"%tuple(np.clip(med,0,255).astype(int)))
OCEAN="#2c3a4e"
cnt=np.bincount(cells.ravel(),minlength=21)
print(f"{'region':<24}{'grid':>6}{'est':>6}{'ratio':>7}   photo colour / table colour")
for k,n in enumerate(names,1):
    e=REGJ[k-1]["estimate"]
    print(f"{n:<24}{cnt[k]:>6}{e:>6}{cnt[k]/e:>7.2f}   {cols_out[k-1]}  {REGJ[k-1]['colour']}")
print(f"{'MAP TOTAL':<24}{cnt[1:].sum():>6}{464:>6}{cnt[1:].sum()/464:>7.2f}")
print(f"ocean {cnt[0]}   sewn {int(sewn.sum())}   unsewn {int((~sewn).sum())}")
np.save("cells_clean.npy",cells); np.save("sewn_clean.npy",sewn)
json.dump({"colours":cols_out,"counts":cnt.tolist()},open("regioncolours.json","w"),indent=1)

# ---- render the digital blanket to compare with the photo ----
S=9.0
Wpx=int(COLS*S*1.5+S)+20; Hpx=int((ROWS+0.5)*S*1.7321)+20
im=Image.new("RGB",(Wpx,Hpx),(17,20,26)); d=ImageDraw.Draw(im)
def hexpts(cx,cy,R):
    return [(cx+R*np.cos(np.radians(60*k)), cy+R*np.sin(np.radians(60*k))) for k in range(6)]
for c in range(COLS):
    for r in range(ROWS):
        cx=10+S+c*1.5*S
        cy=10+(r+0.5+(0.5 if c%2==0 else 0.0))*1.7321*S
        v=cells[r,c]
        if not sewn[r,c]:
            d.polygon(hexpts(cx,cy,S*0.94),outline=(60,70,88))
        else:
            col=cols_out[v-1] if v>0 else OCEAN
            rgb=tuple(int(col[i:i+2],16) for i in (1,3,5))
            d.polygon(hexpts(cx,cy,S*0.97),fill=rgb)
im.save("render.png"); print("rendered",im.size)
