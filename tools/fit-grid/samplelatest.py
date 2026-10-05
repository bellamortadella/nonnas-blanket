import numpy as np, json
from PIL import Image, ImageDraw
COLS,ROWS=72,90; S3=np.sqrt(3)
bl=np.load("latest_mask.npy"); P=np.load("latest_corners.npy")
Hh,W=bl.shape
def homography(src,dst):
    M=[]
    for (x,y),(X,Y) in zip(src,dst):
        M.append([x,y,1,0,0,0,-X*x,-X*y,-X]); M.append([0,0,0,x,y,1,-Y*x,-Y*y,-Y])
    _,_,V=np.linalg.svd(np.array(M,float)); h=V[-1].reshape(3,3); return h/h[2,2]
Hm=homography([(0,0),(COLS,0),(COLS,ROWS),(0,ROWS)],[tuple(p) for p in P])
def to_img(u,v):
    q=Hm@np.array([u,v,1.0]); return q[0]/q[2], q[1]/q[2]
YS=ROWS/(ROWS+0.5)
cen=np.zeros((ROWS,COLS,2))
for c in range(COLS):
    off=0.5 if c%2==0 else 0.0
    for r in range(ROWS):
        cen[r,c]=to_img(c+0.5,(r+0.5+off)*YS)
xi=np.clip(cen[:,:,0].astype(int),0,W-1); yi=np.clip(cen[:,:,1].astype(int),0,Hh-1)
sewn=bl[yi,xi]
print("sewn %d of %d = %.1f%%   unsewn %d"%(sewn.sum(),COLS*ROWS,100*sewn.mean(),(~sewn).sum()))
print("\nunsewn by column:")
for c in range(COLS):
    n=int((~sewn[:,c]).sum())
    if n:
        rr=np.where(~sewn[:,c])[0]
        print(f"  col {c:>2}: {n:>3}  rows {rr.min()}-{rr.max()}")
np.save("latest_sewn.npy",sewn)
im=Image.open("latest.jpg").convert("RGB"); d=ImageDraw.Draw(im)
for c in range(COLS):
    for r in range(ROWS):
        x,y=cen[r,c]
        d.ellipse([x-2,y-2,x+2,y+2], fill=(0,255,0) if sewn[r,c] else (255,0,0))
im.save("latest_cells.png"); print("\nwrote latest_cells.png")
