import numpy as np, json
from PIL import Image, ImageDraw
COLS,ROWS=72,90; S3=np.sqrt(3)
PROJ="/Users/jordanmaccora/Documents/Claude Projects/Nonnas Blanket"
d=json.load(open(PROJ+"/data/blanket.json"))
COL={r["id"]:r["colour"] for r in d["regions"]}; OC=d["config"]["oceanColour"]
def rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
g=np.load("g11_bal.npy"); sewn=np.load("sewn11.npy")
sc=9
W=int((1.5*COLS+0.5)*sc)+2; H=int((ROWS+0.5)*S3*sc)+2
im=Image.new("RGB",(W,H),(12,14,18)); dr=ImageDraw.Draw(im)
for c in range(COLS):
    for r in range(ROWS):
        cx=(1.0+c*1.5)*sc; cy=(r+(0.5 if c%2==0 else 0)+0.5)*S3*sc
        P=lambda k:[(cx+sc*k*np.cos(a), cy+sc*k*0.866*np.sin(a)) for a in np.radians(range(0,360,60))]
        v=int(g[r,c])
        if sewn[r,c]: dr.polygon(P(0.97), fill=rgb(OC) if v==0 else rgb(COL[v]))
        else: dr.polygon(P(0.86), outline=(55,62,76))
im.save("render11.png")
ph=Image.open("zoom11.jpg").convert("RGB")
h=900; ph.thumbnail((h,h)); im.thumbnail((h,h))
sheet=Image.new("RGB",(ph.width+im.width+24, max(ph.height,im.height)+26),(12,14,18))
sheet.paste(ph,(0,22)); sheet.paste(im,(ph.width+24,22))
d2=ImageDraw.Draw(sheet); d2.text((4,4),"photo",fill=(235,235,240)); d2.text((ph.width+28,4),"rebuilt grid",fill=(235,235,240))
sheet.save("cmp11.png"); print(sheet.size)
