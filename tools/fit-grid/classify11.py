import numpy as np, json, collections
from PIL import Image
from scipy import ndimage
COLS,ROWS=72,90
BLOB2REG={21:"Trentino-Alto Adige",2:"Friuli-Venezia Giulia",14:"Veneto",15:"Aosta Valley",
 5:"Lombardy",19:"Piedmont",20:"Emilia-Romagna",9:"Liguria",7:"Marche",22:"Tuscany",
 10:"Umbria",16:"Abruzzo",23:"Abruzzo",17:"Abruzzo",18:"Abruzzo",8:"Lazio",13:"Molise",
 6:"Puglia",11:"Campania",3:"Basilicata",1:"Sardinia",4:"Calabria",12:"Sicily"}
info={d["id"]:d for d in json.load(open("blobs11.json"))}
PROJ="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket"
d=json.load(open(PROJ+"/data/blanket.json"))
NAMES=[r["name"] for r in d["regions"]]; RID={n:i+1 for i,n in enumerate(NAMES)}
assert set(BLOB2REG.values())==set(NAMES), set(BLOB2REG.values())^set(NAMES)
# average the fragments where one region split across several blobs
PAL={}
acc={}
for b,nm in BLOB2REG.items():
    acc.setdefault(RID[nm],[]).append((info[b]["size"], np.array(info[b]["rgb"],float)))
for k,v in acc.items():
    w=np.array([s for s,_ in v],float); c=np.array([c for _,c in v])
    PAL[k]=(c*w[:,None]).sum(0)/w.sum()
im=Image.open("zoom11.jpg").convert("RGB"); W,H=im.size
arr=np.asarray(im).astype(float)
bl=np.load("m11.npy"); P=np.load("P11.npy")
hsv=np.asarray(im.convert("HSV")).astype(float)
Hh,S,V=hsv[:,:,0]*360/255, hsv[:,:,1]/255, hsv[:,:,2]/255
navy=V<0.50          # ocean sits at V 0.24-0.36; every map colour is above 0.6
mp=bl&~navy
mp=ndimage.binary_opening(mp,np.ones((5,5))); mp=ndimage.binary_closing(mp,np.ones((7,7)))
lab,n=ndimage.label(mp); sz=ndimage.sum(mp,lab,range(1,n+1))
mp=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>800])
def homography(src,dst):
    M=[]
    for (x,y),(X,Y) in zip(src,dst):
        M.append([x,y,1,0,0,0,-X*x,-X*y,-X]); M.append([0,0,0,x,y,1,-Y*x,-Y*y,-Y])
    _,_,Vv=np.linalg.svd(np.array(M,float)); h=Vv[-1].reshape(3,3); return h/h[2,2]
Hm=homography([(0,0),(COLS,0),(COLS,ROWS),(0,ROWS)],[tuple(p) for p in P])
def ti(u,v):
    q=Hm@np.array([u,v,1.0]); return q[0]/q[2],q[1]/q[2]
YS=ROWS/(ROWS+0.5)
cen=np.zeros((ROWS,COLS,2)); rad=np.zeros((ROWS,COLS))
for c in range(COLS):
    off=0.5 if c%2==0 else 0.0
    for r in range(ROWS):
        cen[r,c]=ti(c+0.5,(r+0.5+off)*YS)
        p0=ti(c+0.5,(r+0.5+off)*YS); p1=ti(c+1.5,(r+0.5+off)*YS)
        rad[r,c]=max(1.5,np.hypot(p1[0]-p0[0],p1[1]-p0[1])*0.34)
xi=np.clip(cen[:,:,0].astype(int),0,W-1); yi=np.clip(cen[:,:,1].astype(int),0,H-1)
sewn=bl[yi,xi]
g=np.zeros((ROWS,COLS),int)
ids=sorted(PAL); PM=np.array([PAL[i] for i in ids])
for c in range(COLS):
    for r in range(ROWS):
        cx,cy=cen[r,c]; R=rad[r,c]
        x0=max(0,int(cx-R));x1=min(W,int(cx+R+1));y0=max(0,int(cy-R));y1=min(H,int(cy+R+1))
        if x1<=x0 or y1<=y0: continue
        yg,xg=np.mgrid[y0:y1,x0:x1]
        msk=((xg-cx)**2+(yg-cy)**2)<=R*R
        if msk.sum()<3: continue
        if mp[y0:y1,x0:x1][msk].mean()<=0.5: continue
        col=arr[y0:y1,x0:x1][msk].mean(0)
        g[r,c]=ids[int(((PM-col)**2).sum(1).argmin())]
cnt=collections.Counter(g.ravel().tolist())
TARGET={r["name"]:r["count"] for r in d["regions"]}
print(f"{'region':<24}{'found':>7}{'Nonna':>7}{'diff':>7}")
tot=0
for nm in NAMES:
    k=RID[nm]; tot+=cnt[k]
    print(f"{nm:<24}{cnt[k]:>7}{TARGET[nm]:>7}{cnt[k]-TARGET[nm]:>+7}")
print(f"{'TOTAL':<24}{tot:>7}{sum(TARGET.values()):>7}")
print("sewn %d unsewn %d"%(sewn.sum(),(~sewn).sum()))
np.save("g11.npy",g); np.save("sewn11.npy",sewn)
