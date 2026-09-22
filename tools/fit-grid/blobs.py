import os
PROJ = os.environ.get("BLANKET_PROJ", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_PHOTO = os.path.join(PROJ, "reference", "blanket-2026-09-13.jpeg")
SRC_ESTIMATES = os.path.join(PROJ, "reference", "italy-region-hex-counts.json")
import numpy as np, json
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
corr=np.load("corr.npy")
cm=np.asarray(Image.open("colourmask.png").convert("L"))>128
Ih,Iw=cm.shape
ys,xs=np.where(cm)
pts=corr[ys,xs]
# k-means with many clusters
K=34
rng=np.random.default_rng(3)
cen=pts[rng.choice(len(pts),K,replace=False)]
for it in range(30):
    d=((pts[:,None,:]-cen[None,:,:])**2).sum(-1); a=d.argmin(1)
    for k in range(K):
        if (a==k).sum(): cen[k]=pts[a==k].mean(0)
labimg=np.full((Ih,Iw),-1); labimg[ys,xs]=a
# connected components per cluster
comp=np.zeros((Ih,Iw),int); nxt=1; info=[]
for k in range(K):
    m=(labimg==k)
    if m.sum()<200: continue
    l,nn=ndimage.label(m)
    for i in range(1,nn+1):
        mm=(l==i); s=mm.sum()
        if s<600: continue
        comp[mm]=nxt
        yy,xx=np.where(mm)
        info.append(dict(id=nxt,size=int(s),cx=float(xx.mean()),cy=float(yy.mean()),
                         rgb=np.round(corr[mm].mean(0)).astype(int).tolist()))
        nxt+=1
# absorb unassigned map pixels into nearest comp
un=cm&(comp==0)
print("blobs:",len(info)," unassigned px:",int(un.sum()))
idx=ndimage.distance_transform_edt(comp==0,return_distances=False,return_indices=True)
comp2=comp[tuple(idx)]; comp2[~cm]=0
for d in info: d["size"]=int((comp2==d["id"]).sum())
info.sort(key=lambda d:-d["size"])
for d in info: print(f"  blob {d['id']:>3}  size {d['size']:>6}  centre ({d['cx']:.0f},{d['cy']:.0f})  rgb {d['rgb']}")
np.save("comp.npy",comp2); json.dump(info,open("blobs.json","w"),indent=1)
# render labelled
out=Image.open(SRC_PHOTO).convert("RGB")
d=ImageDraw.Draw(out)
try: font=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",26)
except: font=None
for b in info:
    d.text((b["cx"]-10,b["cy"]-10),str(b["id"]),fill=(0,0,0),font=font,stroke_width=4,stroke_fill=(255,255,255))
out.crop((330,180,1300,1250)).save("blobs_labelled.png")
