import cv2, numpy as np
N=800; rng=np.random.default_rng(13)
yy,xx=np.mgrid[0:N,0:N].astype(np.float32); cx=cy=N/2
r=np.hypot(xx-cx,yy-cy)/(N/2); th=np.arctan2(yy-cy,xx-cx)
def fbm(n=N,oct=6,seed=0,base=4):
    g=np.random.default_rng(seed); out=np.zeros((n,n),np.float32); amp=1.0; tot=0
    for o in range(oct):
        k=base*2**o; a=g.standard_normal((k+2,k+2)).astype(np.float32)
        out+=amp*cv2.resize(a,(n,n),interpolation=cv2.INTER_CUBIC); tot+=amp; amp*=0.5
    out/=tot; return (out-out.min())/(out.max()-out.min())
def warp(img,amount,seed):
    dx=(fbm(seed=seed)-0.5)*amount; dy=(fbm(seed=seed+1)-0.5)*amount
    return cv2.remap(img,(xx+dx).astype(np.float32),(yy+dy).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
def grain(img,s=5.0): return (img+rng.standard_normal(img.shape).astype(np.float32)*s).clip(0,255)
RED=np.array([16,15,243],np.float32); HOT=np.array([90,150,255],np.float32); EMBER=np.array([10,40,150],np.float32)

def ring(r0=0.50,seed=3,strength=1.0):
    ang=fbm(seed=seed,base=3); ang2=fbm(seed=seed+7,base=6)
    rr=warp(r,70,seed+20)                                            # the ring is not a clean circle
    width=0.006+0.045*ang**2.2
    gaps=np.clip((ang2-0.22)/0.25,0.05,1)                            # the line of light breaks and thins
    core=np.exp(-((rr-r0)/width)**2)*(0.25+1.0*ang2)*gaps
    halo=np.exp(-np.clip(rr-r0,0,None)/0.10)*(rr>r0)*0.30*(0.3+ang)   # light leaking outward
    smoke=warp(fbm(seed=seed+40,base=3),120,seed+60)**2.2*np.exp(-((rr-r0-0.06)/0.26)**2)*1.1
    img=core[...,None]*(HOT*0.55+RED*0.75)+halo[...,None]*RED+smoke[...,None]*EMBER
    return img*strength, rr

# A: the black sun with a slit
imgA,rr=ring()
slit=np.exp(-((xx-cx)/(N*0.006))**2)*np.exp(-((yy-cy)/(N*0.16))**2)
slit_glow=np.exp(-((xx-cx)/(N*0.03))**2)*np.exp(-((yy-cy)/(N*0.20))**2)*0.25
A=imgA+slit[...,None]*(HOT*0.5+RED*0.6)+slit_glow[...,None]*EMBER
A*= (1-np.clip((r-0.80)/0.25,0,1)**1.5)[...,None]
cv2.imwrite("dark_A_black_sun.png",grain(A,4).astype(np.uint8))

# the painted eye, nearly lost in the dark
im=cv2.imread("fa.jpg").astype(np.float32); H,W=im.shape[:2]
bx0,by0,bw,bh=int(0.22*W),int(0.12*H),1045,841; ex,ey=bx0+0.455*bw,by0+0.645*bh
def eyecrop(size,out=N):
    c=im[int(ey-size*0.5):int(ey-size*0.5)+size,int(ex-size*0.5):int(ex-size*0.5)+size]
    c=cv2.resize(c,(out,out),interpolation=cv2.INTER_LANCZOS4)
    c=cv2.detailEnhance(c.clip(0,255).astype(np.uint8),sigma_s=8,sigma_r=0.10).astype(np.float32)
    g=cv2.cvtColor(c.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    return g
# B: one eye through a crack of light
g=eyecrop(420)
band=np.exp(-((yy-cy*1.02)/(N*0.075))**2)*np.exp(-((xx-cx)/(N*0.34))**4)
band=warp(band,26,5)
B=((g/255.0)**1.25*255)[...,None]*np.array([0.50,0.70,1.0],np.float32)*(0.02+1.5*band[...,None])
B+=fbm(seed=77,base=3)[...,None]**3*EMBER*0.10
B*=(1-np.clip((r-0.75)/0.3,0,1)**1.5)[...,None]
cv2.imwrite("dark_B_crack.png",grain(B,5).astype(np.uint8))

# C: the eye inside the black sun
imgC,rr=ring(r0=0.56,seed=9)
g=eyecrop(430)
inner=np.clip((0.52-rr)/0.16,0,1)**1.1
hole=np.exp(-((xx-cx)/(N*0.30))**4)*np.exp(-((yy-cy*1.02)/(N*0.10))**2)
C=imgC+((g/255.0)**1.3*255)[...,None]*np.array([0.42,0.58,1.0],np.float32)*(inner*hole*1.15)[...,None]
C*=(1-np.clip((r-0.86)/0.2,0,1)**1.5)[...,None]
cv2.imwrite("dark_C_eye_in_sun.png",grain(C,4).astype(np.uint8))

def circ(x,n):
    s=cv2.resize(x,(n,n),interpolation=cv2.INTER_AREA); m=np.zeros((n,n),np.uint8); cv2.circle(m,(n//2,n//2),n//2,255,-1,cv2.LINE_AA); return (s*(m[...,None]/255.)+40*(1-m[...,None]/255.)).astype(np.uint8)
row=[]
for f in ("dark_A_black_sun","dark_B_crack","dark_C_eye_in_sun"):
    x=cv2.imread(f+".png"); t=np.full((800,1040,3),40,np.uint8); t[:,:800]=x; t[40:216,832:1008]=circ(x,176); t[260:356,872:968]=circ(x,96); t[400:448,896:944]=circ(x,48); row.append(t)
cv2.imwrite("dark_preview.jpg",cv2.resize(np.hstack(row),(1560,400)))
