import cv2, numpy as np, os
rng=np.random.default_rng(21)
im=cv2.imread("prev/img/main.jpg"); H,W=im.shape[:2]
BW,BH,CW,CH=2560,423,2560,1440
xa,xb=int(0.03*W),int(0.97*W); hh=int((xb-xa)/(BW/BH)); y0=int(0.447*H-hh/2)
c=cv2.resize(im[y0:y0+hh,xa:xb],(BW,BH),interpolation=cv2.INTER_LANCZOS4)
g=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
g=np.clip((g-0.22)/0.70,0,1)**1.75                                  # the paper goes dark, only the light stays
yy,xx=np.mgrid[0:BH,0:BW].astype(np.float32)
def fbm(hh,ww,seed,base=3,oct=5):
    r=np.random.default_rng(seed); out=np.zeros((hh,ww),np.float32); amp=1; tot=0
    for o in range(oct):
        k=base*2**o; a=r.standard_normal((k+2,max(3,int(k*ww/hh))+2)).astype(np.float32)
        out+=amp*cv2.resize(a,(ww,hh),interpolation=cv2.INTER_CUBIC); tot+=amp; amp*=0.5
    out/=tot; return (out-out.min())/(out.max()-out.min())
bone=np.array([165,200,232],np.float32); ember=np.array([10,30,120],np.float32); hot=np.array([120,170,255],np.float32)
d=np.hypot((xx-BW/2)/(BW*0.5),(yy-BH/2)/(BH*1.4))                   # distance from the sun in the middle
glow=np.exp(-(d/0.16)**2)
band=g[...,None]*(bone*(0.55+0.45*np.exp(-(d/0.5)**2))[...,None]) + (g**0.6)[...,None]*ember*0.35*(0.4+fbm(BH,BW,5)[...,None]) + glow[...,None]*hot*0.25*g[...,None]
side=np.clip(1-np.abs(xx-BW/2)/(BW/2),0,1); side=np.clip(side/0.26,0,1)**1.4
edge=np.clip(np.minimum(yy,BH-1-yy)/46.0,0,1)**0.8
band*=(side*edge)[...,None]
canvas=np.zeros((CH,CW,3),np.float32); Y=(CH-BH)//2
canvas[Y:Y+BH]=band
YY,XX=np.mgrid[0:CH,0:CW].astype(np.float32)
br=fbm(40,CW,11,base=4)[20]; sidec=np.clip(1-np.abs(XX[0]-CW/2)/(CW/2),0,1); sidec=np.clip(sidec/0.20,0,1)**1.2
for yl,seed in ((Y-5,9),(Y+BH+5,10)):                               # the two burning lines, like the ring of the avatar
    nz=fbm(40,CW,seed,base=2)[20]; yline=yl+(nz-0.5)*9
    dd=YY-yline[None,:]; width=1.4+4.5*br[None,:]**2
    core=np.exp(-(dd/width)**2)*(0.25+1.0*br[None,:])*sidec[None,:]
    halo=np.exp(-np.abs(dd)/34.0)*0.20*sidec[None,:]
    canvas+=core[...,None]*(np.array([90,150,255],np.float32)*0.55+np.array([16,15,243],np.float32)*0.75)+halo[...,None]*np.array([16,15,243],np.float32)
canvas+=rng.standard_normal(canvas.shape).astype(np.float32)*3.0
out=canvas.clip(0,255).astype(np.uint8)
cv2.imwrite("banner.jpg",out,[cv2.IMWRITE_JPEG_QUALITY,94])
tv=cv2.resize(out,(1280,720)); desk=cv2.resize(out[Y:Y+BH],(1280,212)); mob=cv2.resize(out[Y:Y+BH,(CW-1546)//2:(CW+1546)//2],(774,212))
pv=np.full((720+20+212+20+212,1280,3),40,np.uint8); pv[:720]=tv; pv[740:952]=desk; pv[972:1184,253:1027]=mob
cv2.imwrite("banner_preview.jpg",pv); print(round(os.path.getsize("banner.jpg")/1e6,2),"MB",out.shape)
