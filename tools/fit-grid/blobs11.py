import numpy as np, json
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
im=Image.open("zoom11.jpg").convert("RGB"); W,H=im.size
arr=np.asarray(im).astype(float)
bl=np.load("m11.npy")
hsv=np.asarray(im.convert("HSV")).astype(float)
Hh,S,V=hsv[:,:,0]*360/255, hsv[:,:,1]/255, hsv[:,:,2]/255
navy=V<0.50          # ocean sits at V 0.24-0.36; every map colour is above 0.6
mp=bl&~navy
mp=ndimage.binary_opening(mp,np.ones((5,5))); mp=ndimage.binary_closing(mp,np.ones((7,7)))
lab,n=ndimage.label(mp); sz=ndimage.sum(mp,lab,range(1,n+1))
mp=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>800])
print("map %.2f%% of blanket"%(100*mp.sum()/bl.sum()))
ys,xs=np.where(mp); pts=arr[ys,xs]
K=26; rng=np.random.default_rng(4)
cen=pts[rng.choice(len(pts),K,replace=False)]
for _ in range(40):
    a=((pts[:,None,:]-cen[None,:,:])**2).sum(-1).argmin(1)
    for k in range(K):
        if (a==k).sum(): cen[k]=pts[a==k].mean(0)
L=np.full((H,W),-1); L[ys,xs]=a
comp=np.zeros((H,W),int); nxt=1; info=[]
for k in range(K):
    m=(L==k)
    if m.sum()<500: continue
    l2,n2=ndimage.label(m)
    for i in range(1,n2+1):
        b=(l2==i)
        if b.sum()<500: continue
        comp[b]=nxt
        yy,xx=np.where(b)
        info.append(dict(id=nxt,size=int(b.sum()),cx=float(xx.mean()),cy=float(yy.mean()),
                         rgb=[int(v) for v in arr[b].mean(0)]))
        nxt+=1
idx=ndimage.distance_transform_edt(comp==0,return_distances=False,return_indices=True)
comp=comp[tuple(idx)]; comp[~mp]=0
for d in info: d["size"]=int((comp==d["id"]).sum())
info.sort(key=lambda d:-d["size"])
for d in info: print(f"  blob {d['id']:>3} size {d['size']:>6} at ({d['cx']:.0f},{d['cy']:.0f}) rgb {d['rgb']}")
np.save("comp11.npy",comp); json.dump(info,open("blobs11.json","w"))
out=im.copy(); dr=ImageDraw.Draw(out)
try: f=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",30)
except: f=None
for b in info:
    dr.text((b["cx"]-12,b["cy"]-14),str(b["id"]),fill=(0,0,0),font=f,stroke_width=4,stroke_fill=(255,255,255))
out.crop((180,220,1000,1180)).save("blobs11.png"); print("wrote blobs11.png")
