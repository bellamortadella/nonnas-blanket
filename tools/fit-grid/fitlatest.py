"""Segment the newest photo and fit the 72x90 grid to it, as per 13 Sep."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
im=Image.open("latest.jpg").convert("RGB")
a=np.asarray(im).astype(np.int16); H,W,_=a.shape
R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]
hsv=np.asarray(im.convert("HSV")).astype(float)
Hh,S,V=hsv[:,:,0]*360/255, hsv[:,:,1]/255, hsv[:,:,2]/255
warm=(R-B)>18
pale=(S<0.16)&(V>0.55)
cand=warm|pale
lab,n=ndimage.label(cand)
edge=set(lab[0].tolist())|set(lab[-1].tolist())|set(lab[:,0].tolist())|set(lab[:,-1].tolist()); edge.discard(0)
bg=np.isin(lab,list(edge))
bl=~bg
bl=ndimage.binary_opening(bl,np.ones((5,5)))
lab,n=ndimage.label(bl); sz=ndimage.sum(bl,lab,range(1,n+1))
bl=(lab==1+int(np.argmax(sz)))
bl=ndimage.binary_fill_holes(bl)
print("blanket covers %.1f%% of frame"%(100*bl.mean()))
np.save("latest_mask.npy",bl)

def robust(xs,ys,it=6):
    xs=np.asarray(xs,float); ys=np.asarray(ys,float); w=np.ones_like(xs)
    for _ in range(it):
        p=np.polyfit(xs,ys,1,w=w); r=ys-np.polyval(p,xs)
        s=1.4826*np.median(np.abs(r-np.median(r)))+1e-6
        w=1/(1+(r/(2*s))**2)
    return p
rows={}
for y in range(H):
    xs=np.where(bl[y])[0]
    if len(xs)>60: rows[y]=(xs.min(),xs.max())
ys=sorted(rows); y0,y1=ys[0],ys[-1]
print("blanket rows %d..%d"%(y0,y1))
# left/right edges away from the top notches; bottom and top edges
lo,hi=y0+int(0.35*(y1-y0)), y1-int(0.04*(y1-y0))
LY=[y for y in ys if lo<=y<=hi]
pl=robust(LY,[rows[y][0] for y in LY]); pr=robust(LY,[rows[y][1] for y in LY])
cols={}
for x in range(W):
    yy=np.where(bl[:,x])[0]
    if len(yy)>60: cols[x]=(yy.min(),yy.max())
xs_=sorted(cols); x0,x1=xs_[0],xs_[-1]
BX=[x for x in xs_ if x0+0.06*(x1-x0)<=x<=x1-0.06*(x1-x0)]
pb=robust(BX,[cols[x][1] for x in BX])
# top edge: use the widest flat run (between the two notches)
tops=np.array([cols[x][0] for x in BX]); med=np.median(tops)
TX=[x for x,t in zip(BX,tops) if abs(t-med)<0.05*(y1-y0)]
pt=robust(TX,[cols[x][0] for x in TX])
print("top line y=%.4fx+%.1f   bottom y=%.4fx+%.1f"%(*pt,*pb))
print("left x=%.4fy+%.1f  right x=%.4fy+%.1f"%(*pl,*pr))
def inter(pxy,pyx):
    a_,b_=pxy; c_,d_=pyx
    y=(a_*d_+b_)/(1-a_*c_); return (c_*y+d_, y)
P=np.array([inter(pt,pl),inter(pt,pr),inter(pb,pr),inter(pb,pl)])
print("corners TL %s TR %s BR %s BL %s"%tuple(np.round(P,1).tolist()))
np.save("latest_corners.npy",P)
d=ImageDraw.Draw(im)
for p,q in zip(P,np.roll(P,-1,axis=0)): d.line([tuple(p),tuple(q)],fill=(255,230,0),width=4)
im.save("latest_corners.png")
