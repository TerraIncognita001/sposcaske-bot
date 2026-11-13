"""Camera-path meter: registers every frame of a video (stage crop) against the source picture (SIFT + RANSAC)
and prints hold (H) / glide (M) / jump (J) segments with zoom and centre. Usage:
    python tools/campath.py <video.mp4> <out.json> <picture.jpg | @seconds> <asr.json | file with {"segments": []}>
The measuring tool behind docs/FORMAT.md section 7; the base of tools/conform.py."""
import cv2, numpy as np, sys, json, subprocess, math
path, out, ref, asr = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
FPS, W = 8, 640
pr = subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',path],capture_output=True,text=True).stdout.strip().split(',')
SW, SH = int(pr[0]), int(pr[1]); H = int(round(SH*W/SW/2)*2)
raw = subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f'fps={FPS},scale={W}:{H}:flags=area','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout
fr = np.frombuffer(raw,np.uint8).reshape(-1,H,W); N = len(fr)
mask = np.full((H,W),255,np.uint8); mask[int(H*0.74):int(H*0.97),:] = 0
if ref.startswith('@'):
    raw1 = subprocess.run(['ffmpeg','-v','error','-ss',ref[1:],'-i',path,'-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout
    rimg = cv2.imdecode(np.frombuffer(raw1,np.uint8), cv2.IMREAD_GRAYSCALE); rmask = np.full(rimg.shape,255,np.uint8); rmask[int(rimg.shape[0]*0.74):int(rimg.shape[0]*0.97),:] = 0
else:
    rimg = cv2.imread(ref, cv2.IMREAD_GRAYSCALE); rmask = None
k = 1600/rimg.shape[1]; rimg = cv2.resize(rimg,(1600,int(rimg.shape[0]*k)),interpolation=cv2.INTER_AREA)
if rmask is not None: rmask = cv2.resize(rmask,(rimg.shape[1],rimg.shape[0]),interpolation=cv2.INTER_NEAREST)
RW, RH = rimg.shape[1], rimg.shape[0]
rk, rd = cv2.SIFT_create(nfeatures=12000).detectAndCompute(rimg,rmask)
flann = cv2.FlannBasedMatcher(dict(algorithm=1,trees=4),dict(checks=48)); sift = cv2.SIFT_create(nfeatures=1200)
P = []
for f in fr:
    kp, d = sift.detectAndCompute(f,mask); row = None
    if d is not None and len(kp) >= 10:
        good = [m[0] for m in flann.knnMatch(d,rd,k=2) if len(m)==2 and m[0].distance < 0.72*m[1].distance]
        if len(good) >= 10:
            p1 = np.float32([kp[g.queryIdx].pt for g in good]); p2 = np.float32([rk[g.trainIdx].pt for g in good])
            M, inl = cv2.estimateAffinePartial2D(p1,p2,method=cv2.RANSAC,ransacReprojThreshold=4.0)
            if M is not None and int(inl.sum()) >= 10:
                s = math.hypot(M[0,0],M[1,0])
                if 0.02 < s < 20:
                    X = M[0,0]*W/2+M[0,1]*H/2+M[0,2]; Y = M[1,0]*W/2+M[1,1]*H/2+M[1,2]
                    row = (W*s/RW, X/RW, Y/RH, int(inl.sum()))
    P.append(row)
lum = [float(f.mean()) for f in fr]
# speed per frame pair, in "visible frames per second"
sp = []
for i in range(N-1):
    a, b = P[i], P[i+1]
    if a is None or b is None: sp.append(None); continue
    dz = math.log(b[0]/a[0]); dx = (b[1]-a[1])/a[0]; dy = (b[2]-a[2])*RH/RW/(a[0]*H/W)
    sp.append(math.sqrt(dz*dz+dx*dx+dy*dy)*FPS)
lab = ['X' if s is None else ('J' if s > 2.5 else ('M' if s > 0.10 else 'H')) for s in sp]
# smooth labels: runs shorter than 3 frames adopt neighbours
segs, i = [], 0
while i < len(lab):
    j = i
    while j < len(lab) and lab[j] == lab[i]: j += 1
    segs.append([lab[i], i, j]); i = j
merged = []
for s in segs:
    if merged and (s[2]-s[1] < 3 and s[0] != 'J') and merged[-1][0] != 'J': merged[-1][2] = s[2]
    elif merged and merged[-1][0] == s[0]: merged[-1][2] = s[2]
    else: merged.append(s)
words = [w for s in json.load(open(asr))['segments'] for w in s['words']]
outsegs = []
for kind, a, b in merged:
    pa = next((P[x] for x in range(a, b+1) if P[x]), None); pb = next((P[x] for x in range(b, a-1, -1) if P[x]), None)
    t0, t1 = a/FPS, b/FPS; txt = ' '.join(w['w'] for w in words if t0 <= (w['s']+w['e'])/2 < t1)
    v = [x for x in sp[a:b] if x is not None]
    d = {'kind': kind, 't0': round(t0,2), 't1': round(t1,2), 'zoom0': round(1/pa[0],2) if pa else None, 'zoom1': round(1/pb[0],2) if pb else None,
         'c0': [round(pa[1],3), round(pa[2],3)] if pa else None, 'c1': [round(pb[1],3), round(pb[2],3)] if pb else None, 'speed': round(float(np.mean(v)),3) if v else None, 'words': txt}
    outsegs.append(d)
json.dump({'src': [SW,SH], 'ref': [RW,RH], 'fps': FPS, 'path': [list(map(lambda x: round(x,4), p)) if p else None for p in P], 'lum': [round(x,1) for x in lum], 'segments': outsegs}, open(out,'w'))
print(f"== {path.split('/')[-1]} {SW}x{SH} {N/FPS:.1f}s registered {sum(p is not None for p in P)}/{N} segs {len(outsegs)}")
for d in outsegs:
    print(f"{d['t0']:6.2f}-{d['t1']:6.2f} {d['kind']} z {d['zoom0']}->{d['zoom1']} c{d['c0']}->{d['c1']} v={d['speed']} | {d['words'][:95]}")
