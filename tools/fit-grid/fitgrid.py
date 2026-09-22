import numpy as np
from PIL import Image
from scipy import ndimage
blanket=np.load("mask_full.npy")
main=blanket.copy(); main[:168,:]=False
lab,n=ndimage.label(main); sz=ndimage.sum(main,lab,range(1,n+1))
main=(lab==1+int(np.argmax(sz)))
H,W=main.shape

def robust_line(xs,ys,iters=5):
    xs=np.asarray(xs,float); ys=np.asarray(ys,float)
    w=np.ones_like(xs)
    for _ in range(iters):
        p=np.polyfit(xs,ys,1,w=w)
        r=ys-np.polyval(p,xs)
        s=1.4826*np.median(np.abs(r-np.median(r)))+1e-6
        w=1.0/(1.0+(r/(2*s))**2)
    return p  # y = p0*x + p1

# bottom edge: for each x, max y
bx=[];by=[]
for x in range(150,1500):
    ys=np.where(main[:,x])[0]
    if len(ys)>200: bx.append(x); by.append(ys.max())
pb=robust_line(bx,by); print("bottom line y = %.5f x + %.2f"%tuple(pb))

# top edge of upper section: for each x, min y
tx=[];ty=[]
for x in range(420,1180):
    ys=np.where(main[:,x])[0]
    if len(ys)>200: tx.append(x); ty.append(ys.min())
pt=robust_line(tx,ty); print("top    line y = %.5f x + %.2f"%tuple(pt))

# left edge of LOWER section: for each y, min x  (y from 600 to 1480)
ly=[];lx=[]
for y in range(600,1485):
    xs=np.where(main[y])[0]
    if len(xs)>200: ly.append(y); lx.append(xs.min())
pl=robust_line(ly,lx); print("left   line x = %.5f y + %.2f"%tuple(pl))

ry=[];rx=[]
for y in range(620,1485):
    xs=np.where(main[y])[0]
    if len(xs)>200: ry.append(y); rx.append(xs.max())
pr=robust_line(ry,rx); print("right  line x = %.5f y + %.2f"%tuple(pr))

def inter_xy(pxy, pyx):
    # pxy: y = a x + b ; pyx: x = c y + d
    a,b=pxy; c,d=pyx
    y=(a*d+b)/(1-a*c); x=c*y+d
    return (x,y)
P00=inter_xy(pt,pl); P10=inter_xy(pt,pr); P11=inter_xy(pb,pr); P01=inter_xy(pb,pl)
print("corners TL",np.round(P00,1),"TR",np.round(P10,1),"BR",np.round(P11,1),"BL",np.round(P01,1))
np.save("corners.npy", np.array([P00,P10,P11,P01]))
# also record step corners
for y in range(500,650):
    xs=np.where(main[y])[0]
    if len(xs)>200:
        pass
# find step rows precisely
prevL=prevR=None
for y in range(200,700):
    xs=np.where(main[y])[0]
    if len(xs)<100: continue
    x0,x1=xs.min(),xs.max()
    if prevL is not None and x0-prevL < -30: print("LEFT step at y=",y, prevL,"->",x0)
    if prevR is not None and x1-prevR > 30: print("RIGHT step at y=",y, prevR,"->",x1)
    prevL,prevR=x0,x1
