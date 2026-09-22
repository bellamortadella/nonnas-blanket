import os
PROJ = os.environ.get("BLANKET_PROJ", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_PHOTO = os.path.join(PROJ, "reference", "blanket-2026-09-13.jpeg")
SRC_ESTIMATES = os.path.join(PROJ, "reference", "italy-region-hex-counts.json")
import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage

COLS,ROWS=72,90
SRC=SRC_PHOTO
img=Image.open(SRC).convert("RGB"); A=np.asarray(img).astype(float)
Ih,Iw,_=A.shape
main=np.load("mask_full.npy").copy(); main[:168,:]=False
lab,n=ndimage.label(main); sz=ndimage.sum(main,lab,range(1,n+1))
main=(lab==1+int(np.argmax(sz)))
P=np.load("corners.npy")

REG=json.load(open(SRC_ESTIMATES))["regions"]
names=[r["region"] for r in REG]
pal=np.array([[int(r["colour"][i:i+2],16) for i in (1,3,5)] for r in REG],float)

# ---------- illumination correction ----------
# model: observed = gain(x,y) * true ; estimate gain from ocean pixels (known constant navy)
hsv=np.asarray(img.convert("HSV")).astype(float)
Hh,Ss,Vv=hsv[:,:,0]*360/255, hsv[:,:,1]/255, hsv[:,:,2]/255
navy = main & ((((Hh>170)&(Hh<260)) | (Ss<0.20)) & (Vv<0.62))
navy = ndimage.binary_erosion(navy, np.ones((9,9)))
ys,xs=np.where(navy)
# quadratic surface per channel
def fit_surface(vals):
    Mx=np.stack([np.ones_like(xs),xs,ys,xs*xs,xs*ys,ys*ys],1).astype(float)
    c,*_=np.linalg.lstsq(Mx,vals,rcond=None); return c
yy,xx=np.mgrid[0:Ih,0:Iw].astype(float)
B=np.stack([np.ones_like(xx),xx,yy,xx*xx,xx*yy,yy*yy],-1)
gain=np.zeros_like(A)
ref=np.array([A[ys,xs,k].mean() for k in range(3)])
print("mean ocean rgb in photo:",np.round(ref,1))
for k in range(3):
    c=fit_surface(A[ys,xs,k]); s=B@c
    gain[:,:,k]=np.clip(s,20,None)
corr=A/gain*ref            # normalised so ocean is flat at `ref`
TARGET_OCEAN=np.array([44,58,78],float)   # navy we will render with
corr=corr*(TARGET_OCEAN/ref)
np.save("corr.npy",corr)
print("corrected ocean rgb:",np.round(corr[navy].mean(0),1))
# check a few region colours after correction
for nm,cc in (("Sicily",None),):
    pass
