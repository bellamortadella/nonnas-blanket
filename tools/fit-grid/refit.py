"""Re-fit the 5 Oct photo: left edge = full height (incl. the top-left strip),
bottom edge = full width. The true top line shares the bottom's vanishing point."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
bl=np.load("latest_mask.npy"); H,W=bl.shape
def robust(xs,ys,it=6):
    xs=np.asarray(xs,float); ys=np.asarray(ys,float); w=np.ones_like(xs)
    for _ in range(it):
        p=np.polyfit(xs,ys,1,w=w); r=ys-np.polyval(p,xs)
        s=1.4826*np.median(np.abs(r-np.median(r)))+1e-6; w=1/(1+(r/(2*s))**2)
    return p
rows={}
for y in range(H):
    xs=np.where(bl[y])[0]
    if len(xs)>40: rows[y]=(xs.min(),xs.max())
ys=sorted(rows); ytop,ybot=ys[0],ys[-1]
print("blanket spans rows %d..%d"%(ytop,ybot))
# LEFT edge: every row, including the strip at the very top
pl=robust(ys,[rows[y][0] for y in ys])
# RIGHT edge: only where the blanket is full width (below the top gap)
lowy=[y for y in ys if y>ytop+0.25*(ybot-ytop)]
pr=robust(lowy,[rows[y][1] for y in lowy])
cols={}
for x in range(W):
    yy=np.where(bl[:,x])[0]
    if len(yy)>40: cols[x]=(yy.min(),yy.max())
xs_=sorted(cols); x0,x1=xs_[0],xs_[-1]
BX=[x for x in xs_ if x0+0.05*(x1-x0)<=x<=x1-0.05*(x1-x0)]
pb=robust(BX,[cols[x][1] for x in BX])
tops=np.array([cols[x][0] for x in BX]); med=np.median(tops)
TX=[x for x,t in zip(BX,tops) if abs(t-med)<0.05*(ybot-ytop)]
pt_main=robust(TX,[cols[x][0] for x in TX])
def inter(pxy,pyx):
    a,b=pxy; c,d=pyx; y=(a*d+b)/(1-a*c); return (c*y+d, y)
def inter_ll(p1,p2):                      # two y=mx+c lines
    m1,c1=p1; m2,c2=p2; x=(c2-c1)/(m1-m2); return (x, m1*x+c1)
Vh=inter_ll(pb,pt_main)
print("horizontal vanishing point: (%.0f, %.0f)"%Vh)
# topmost blanket point (the strip) -> the true top line through it and Vh
strip=np.argwhere(bl[:ytop+40]); 
sy,sx = strip[strip[:,0].argmin()]
print("topmost blanket pixel: (%d,%d)"%(sx,sy))
m=(Vh[1]-sy)/(Vh[0]-sx); pt=(m, sy-m*sx)
print("true top line  y=%.5fx+%.1f   (main sewn top was y=%.5fx+%.1f)"%(*pt,*pt_main))
P=np.array([inter(pt,pl),inter(pt,pr),inter(pb,pr),inter(pb,pl)])
print("corners TL %s TR %s BR %s BL %s"%tuple(np.round(P,1).tolist()))
np.save("refit_corners.npy",P); np.save("refit_lines.npy",np.array([pt,pb,pl,pr],dtype=object),allow_pickle=True)
im=Image.open("latest.jpg").convert("RGB"); d=ImageDraw.Draw(im)
for a,b in zip(P,np.roll(P,-1,axis=0)): d.line([tuple(a),tuple(b)],fill=(255,230,0),width=4)
for x in (0,W):
    d.line([(x,pt_main[0]*x+pt_main[1]),(W-x,pt_main[0]*(W-x)+pt_main[1])],fill=(255,80,80),width=2)
im.save("refit.png"); print("wrote refit.png (yellow = full grid, red = sewn top edge)")
