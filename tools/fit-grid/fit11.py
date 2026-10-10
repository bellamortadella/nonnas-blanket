"""Fit the 72x90 grid to the new flat top-down shot (zoom11)."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
im=Image.open("zoom11.jpg").convert("RGB"); W,H=im.size
a=np.asarray(im).astype(np.int16); R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]
hsv=np.asarray(im.convert("HSV")).astype(float)
Hh,S,V=hsv[:,:,0]*360/255, hsv[:,:,1]/255, hsv[:,:,2]/255
warm=(R-B)>20; pale=(S<0.16)&(V>0.55)
cand=warm|pale
lab,n=ndimage.label(cand)
edge=set(lab[0].tolist())|set(lab[-1].tolist())|set(lab[:,0].tolist())|set(lab[:,-1].tolist()); edge.discard(0)
bg=np.isin(lab,list(edge))
bl=ndimage.binary_opening(~bg,np.ones((5,5)))
lab,n=ndimage.label(bl); sz=ndimage.sum(bl,lab,range(1,n+1))
bl=ndimage.binary_fill_holes(lab==1+int(np.argmax(sz)))
print("blanket %.1f%% of frame"%(100*bl.mean()))
np.save("m11.npy",bl)
def robust(x,y,it=6):
    x=np.asarray(x,float); y=np.asarray(y,float); w=np.ones_like(x)
    for _ in range(it):
        p=np.polyfit(x,y,1,w=w); r=y-np.polyval(p,x)
        s=1.4826*np.median(np.abs(r-np.median(r)))+1e-6; w=1/(1+(r/(2*s))**2)
    return p
rows={}
for yy in range(H):
    xs=np.where(bl[yy])[0]
    if len(xs)>60: rows[yy]=(xs.min(),xs.max())
ys=sorted(rows); y0,y1=ys[0],ys[-1]
pl=robust(ys,[rows[y][0] for y in ys])                       # left edge: full height
lowy=[y for y in ys if y>y0+0.22*(y1-y0)]
pr=robust(lowy,[rows[y][1] for y in lowy])
cols={}
for xx in range(W):
    yy2=np.where(bl[:,xx])[0]
    if len(yy2)>60: cols[xx]=(yy2.min(),yy2.max())
xs_=sorted(cols); x0,x1=xs_[0],xs_[-1]
BX=[x for x in xs_ if x0+0.05*(x1-x0)<=x<=x1-0.05*(x1-x0)]
pb=robust(BX,[cols[x][1] for x in BX])
tops=np.array([cols[x][0] for x in BX]); med=np.median(tops)
TX=[x for x,t in zip(BX,tops) if abs(t-med)<0.05*(y1-y0)]
pt_main=robust(TX,[cols[x][0] for x in TX])
def ill(p1,p2):
    m1,c1=p1; m2,c2=p2; x=(c2-c1)/(m1-m2); return (x,m1*x+c1)
Vh=ill(pb,pt_main)
st=np.argwhere(bl[:y0+40]); sy,sx=st[st[:,0].argmin()]
m=(Vh[1]-sy)/(Vh[0]-sx); pt=(m, sy-m*sx)
def inter(pxy,pyx):
    A,Bc=pxy; C,D=pyx; y=(A*D+Bc)/(1-A*C); return (C*y+D,y)
P=np.array([inter(pt,pl),inter(pt,pr),inter(pb,pr),inter(pb,pl)])
print("corners",np.round(P,1).tolist())
np.save("P11.npy",P)
d=ImageDraw.Draw(im)
for p,q in zip(P,np.roll(P,-1,axis=0)): d.line([tuple(p),tuple(q)],fill=(255,230,0),width=4)
im.save("fit11.png"); print("wrote fit11.png")
