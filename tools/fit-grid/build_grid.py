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
corr=np.load("corr.npy")
main=np.load("mask_full.npy").copy(); main[:168,:]=False
lab,n=ndimage.label(main); sz=ndimage.sum(main,lab,range(1,n+1))
main=(lab==1+int(np.argmax(sz)))
colourmask=np.asarray(Image.open("colourmask.png").convert("L"))>128
P=np.load("corners.npy")

def homography(src,dst):
    M=[]
    for (x,y),(X,Y) in zip(src,dst):
        M.append([x,y,1,0,0,0,-X*x,-X*y,-X]); M.append([0,0,0,x,y,1,-Y*x,-Y*y,-Y])
    _,_,V=np.linalg.svd(np.array(M,float)); h=V[-1].reshape(3,3); return h/h[2,2]
Hm=homography([(0,0),(COLS,0),(COLS,ROWS),(0,ROWS)],[tuple(p) for p in P])
def to_img(u,v):
    p=Hm@np.array([u,v,1.0]); return p[0]/p[2],p[1]/p[2]

YS=ROWS/(ROWS+0.5)
def centres_for(par,du,dv):
    C=np.zeros((ROWS,COLS,2))
    for c in range(COLS):
        off=0.5 if (c%2)==par else 0.0
        for r in range(ROWS):
            C[r,c]=to_img(c+0.5+du,(r+0.5+off+dv)*YS)
    return C

# ---- phase search: maximise purity of the map/ocean mask inside each cell ----
def purity(C):
    xi=np.clip(C[:,:,0].astype(int),0,Iw-1); yi=np.clip(C[:,:,1].astype(int),0,Ih-1)
    s=0.0; cnt=0
    for dx,dy in ((0,0),(2,0),(-2,0),(0,2),(0,-2),(2,2),(-2,-2),(2,-2),(-2,2)):
        s+=colourmask[np.clip(yi+dy,0,Ih-1),np.clip(xi+dx,0,Iw-1)].astype(float); cnt+=1
    f=s/cnt
    return float(np.mean(np.abs(f-0.5)*2))   # 1 = every sample agrees

best=None
for par in (0,1):
    for du in np.arange(-0.4,0.45,0.1):
        for dv in np.arange(-0.4,0.45,0.1):
            sc=purity(centres_for(par,du,dv))
            if best is None or sc>best[0]: best=(sc,par,du,dv)
print("best phase: score %.4f parity=%d du=%.2f dv=%.2f"%best)
sc,par,du,dv=best
C=centres_for(par,du,dv)
np.save("centres72.npy",C); json.dump({"parity":par,"du":du,"dv":dv},open("phase.json","w"))

xi=np.clip(C[:,:,0].astype(int),0,Iw-1); yi=np.clip(C[:,:,1].astype(int),0,Ih-1)
sewn=main[yi,xi]
print("sewn",int(sewn.sum()),"unsewn",int((~sewn).sum()))

# cell radius
rad=np.zeros((ROWS,COLS))
for c in range(COLS):
    for r in range(ROWS):
        x0,y0=to_img(c+0.5,(r+0.5)*YS); x1,y1=to_img(c+1.5,(r+0.5)*YS)
        rad[r,c]=max(1.5,np.hypot(x1-x0,y1-y0)*0.34)
samp=np.zeros((ROWS,COLS,3)); ismap=np.zeros((ROWS,COLS))
for c in range(COLS):
    for r in range(ROWS):
        cx,cy=C[r,c]; R=rad[r,c]
        x0=max(0,int(cx-R)); x1=min(Iw,int(cx+R+1)); y0=max(0,int(cy-R)); y1=min(Ih,int(cy+R+1))
        if x1<=x0 or y1<=y0: continue
        yy,xx=np.mgrid[y0:y1,x0:x1]
        m=((xx-cx)**2+(yy-cy)**2)<=R*R
        if m.sum()<3: m=np.ones_like(m)
        samp[r,c]=corr[y0:y1,x0:x1][m].mean(0)
        ismap[r,c]=colourmask[y0:y1,x0:x1][m].mean()
np.save("samp72.npy",samp); np.save("sewn72.npy",sewn); np.save("ismap72.npy",ismap)
print("cells with ismap>0.5:",int((ismap>0.5).sum()), " (map hexagons)")
print("ocean sewn:",int(((ismap<=0.5)&sewn).sum()))
