import os
PROJ = os.environ.get("BLANKET_PROJ", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_PHOTO = os.path.join(PROJ, "reference", "blanket-2026-09-13.jpeg")
SRC_ESTIMATES = os.path.join(PROJ, "reference", "italy-region-hex-counts.json")
import numpy as np
from PIL import Image
from collections import deque

SRC=SRC_PHOTO
im=Image.open(SRC).convert("RGB")
W,H=im.size
# downsample for speed
scale=2
small=im.resize((W//scale,H//scale), Image.LANCZOS)
a=np.asarray(small).astype(np.int16)
h,w,_=a.shape
R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]
# wood floor: warm, R noticeably > B
warm = (R-B) > 25
# flood fill from border over warm pixels
vis=np.zeros((h,w),bool)
dq=deque()
for x in range(w):
    for y in (0,h-1):
        if warm[y,x] and not vis[y,x]: vis[y,x]=True; dq.append((y,x))
for y in range(h):
    for x in (0,w-1):
        if warm[y,x] and not vis[y,x]: vis[y,x]=True; dq.append((y,x))
while dq:
    y,x=dq.popleft()
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
        ny,nx=y+dy,x+dx
        if 0<=ny<h and 0<=nx<w and warm[ny,nx] and not vis[ny,nx]:
            vis[ny,nx]=True; dq.append((ny,nx))
blanket = ~vis
print("blanket px frac", blanket.mean())
# per-row extents
rows=[]
for y in range(h):
    xs=np.where(blanket[y])[0]
    if len(xs)>50: rows.append((y,xs.min(),xs.max(),len(xs)))
print("first rows", rows[:5])
print("last rows", rows[-5:])
np.save("blanket_mask.npy", blanket)
Image.fromarray((blanket*255).astype(np.uint8)).save("mask.png")
# print extents every 20 rows
for y,x0,x1,n in rows[::25]:
    print(f"y={y*scale:5d} x0={x0*scale:5d} x1={x1*scale:5d} width={(x1-x0)*scale:5d} n={n*scale}")
