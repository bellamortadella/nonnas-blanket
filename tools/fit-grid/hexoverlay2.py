import os
PROJ = os.environ.get("BLANKET_PROJ", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_PHOTO = os.path.join(PROJ, "reference", "blanket-2026-09-13.jpeg")
SRC_ESTIMATES = os.path.join(PROJ, "reference", "italy-region-hex-counts.json")
import numpy as np, json
from PIL import Image, ImageDraw
P=np.load("corners.npy")
def homography(src,dst):
    M=[]
    for (x,y),(X,Y) in zip(src,dst):
        M.append([x,y,1,0,0,0,-X*x,-X*y,-X]); M.append([0,0,0,x,y,1,-Y*x,-Y*y,-Y])
    _,_,V=np.linalg.svd(np.array(M,float)); h=V[-1].reshape(3,3); return h/h[2,2]
def render(COLS,ROWS,tag,parity=0,du=0.0,dv=0.0):
    Hm=homography([(0,0),(COLS,0),(COLS,ROWS),(0,ROWS)],[tuple(p) for p in P])
    def to_img(u,v):
        p=Hm@np.array([u,v,1.0]); return (p[0]/p[2],p[1]/p[2])
    img=Image.open(SRC_PHOTO).convert("RGB")
    d=ImageDraw.Draw(img)
    for c in range(COLS):
        off=0.5 if (c%2)==parity else 0.0
        for r in range(ROWS):
            u=c+0.5+du; v=r+0.5+off+dv
            pts=[to_img(u+0.6667*np.cos(np.radians(60*k)), v+0.5774*np.sin(np.radians(60*k))) for k in range(6)]
            d.line(pts+[pts[0]],fill=(0,255,255),width=1)
    img.crop((430,700,620,980)).resize((190*5,280*5),Image.LANCZOS).save(f"hx_{tag}.png")
render(72,90,"72x90",parity=0,du=-0.30,dv=0.40)
render(48,60,"48x60")
print("done")
