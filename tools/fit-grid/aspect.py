import numpy as np
# Zhang & He: aspect ratio + focal length of an imaged rectangle, principal point = image centre
W,H=1542,2047
cx,cy=W/2.0,H/2.0
TL=(310.1,177.6); TR=(1337.2,179.0); BR=(1516.0,1543.6); BL=(56.9,1501.1)
m1=np.array([TL[0]-cx,TL[1]-cy,1.0])
m2=np.array([TR[0]-cx,TR[1]-cy,1.0])
m3=np.array([BL[0]-cx,BL[1]-cy,1.0])
m4=np.array([BR[0]-cx,BR[1]-cy,1.0])
k2=np.dot(np.cross(m1,m4),m3)/np.dot(np.cross(m2,m4),m3)
k3=np.dot(np.cross(m1,m4),m2)/np.dot(np.cross(m3,m4),m2)
n2=k2*m2-m1
n3=k3*m3-m1
num=-(n2[0]*n3[0]+n2[1]*n3[1])
den=n2[2]*n3[2]
f2=num/den
print("k2,k3",round(k2,4),round(k3,4),"  f^2",round(f2,1))
if f2>0:
    f=np.sqrt(f2); print("focal length ~ %.0f px (%.0f mm equiv on 35mm)"%(f, f*36/W))
    Ai=np.diag([1/f,1/f,1.0])
    def q(n): 
        v=Ai@n; return v@v
    ar2=q(n2)/q(n3)
    ar=np.sqrt(ar2)
    print("rectangle width/height aspect = %.4f"%ar)
    # flat-top hex grid: aspect = (1.5C+0.5)/(sqrt(3)*(Rows+0.5))
    total=6480
    best=None
    for C in range(20,200):
        if total%C: continue
        R=total//C
        a=(1.5*C+0.5)/(np.sqrt(3)*(R+0.5))
        if best is None or abs(a-ar)<abs(best[2]-ar): best=(C,R,a)
        print(f"   {C} x {R}: aspect {a:.4f}   err {a-ar:+.4f}")
    print("closest divisor pair:",best)
    # free solve
    C=np.sqrt(total*ar*np.sqrt(3)/1.5); print("free solve: C=%.1f rows=%.1f"%(C,total/C))
