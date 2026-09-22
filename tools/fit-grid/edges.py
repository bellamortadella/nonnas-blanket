import numpy as np
b=np.load("blanket_mask.npy"); h,w=b.shape; S=2
rows={}
for y in range(h):
    xs=np.where(b[y])[0]
    if len(xs)>20: rows[y]=(xs.min(),xs.max(),len(xs))
ys=sorted(rows)
print("y range of any blanket px:", ys[0]*S, ys[-1]*S)
# separate loose patch (narrow, top) from main body: main body = width > 300px(small)
main=[y for y in ys if rows[y][1]-rows[y][0] > 300]
loose=[y for y in ys if rows[y][1]-rows[y][0] <= 300]
print("loose patch y:", loose[0]*S, loose[-1]*S, " x:", min(rows[y][0] for y in loose)*S, max(rows[y][1] for y in loose)*S)
print("main body y:", main[0]*S, main[-1]*S)
print()
print("LEFT edge transitions (y, x0):")
prev=None
for y in main:
    x0=rows[y][0]
    if prev is not None and abs(x0-prev)>15: print(f"  jump at y={y*S}: {prev*S} -> {x0*S}")
    prev=x0
print("RIGHT edge transitions (y, x1):")
prev=None
for y in main:
    x1=rows[y][1]
    if prev is not None and abs(x1-prev)>15: print(f"  jump at y={y*S}: {prev*S} -> {x1*S}")
    prev=x1
