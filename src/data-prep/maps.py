import numpy as np, json, time
from scipy import ndimage as ndi
R = 1737400.0; D2R = np.pi/180; N = 2533; PX = 240.0; C0 = (N-1)/2
g = np.load('data/g240.npy'); yy, xx = np.mgrid[0:N, 0:N]; X = (xx-C0)*PX; Y = (C0-yy)*PX
z = (g - (X*X+Y*Y)/(2*R)).astype(np.float32); del X, Y, xx, yy
zf = {1: z, 3: ndi.maximum_filter(z, 3), 9: ndi.maximum_filter(z, 9), 27: ndi.maximum_filter(z, 27)}
ks = [1]
while ks[-1] < 1300: ks.append(max(ks[-1]+1, int(ks[-1]*1.06)))
A0, A1 = 516, 2016  # crop 1500
ND = 48; H = np.zeros((ND, A1-A0, A1-A0), np.float32); t0 = time.time()
zc = z[A0:A1, A0:A1]
for i in range(ND):
    lam = i*360/ND*D2R; dc, dr = np.sin(lam), -np.cos(lam); best = np.full(zc.shape, -1e9, np.float32); prev = 0
    for k in ks:
        gap = k - prev; prev = k; s = 1 if gap <= 1 else 3 if gap <= 4 else 9 if gap <= 12 else 27
        oc, orr = int(round(k*dc)), int(round(k*dr)); r0, r1, c0, c1 = A0+orr, A1+orr, A0+oc, A1+oc
        rr0, rr1, cc0, cc1 = max(r0, 0), min(r1, N), max(c0, 0), min(c1, N)
        if rr1 <= rr0 or cc1 <= cc0: continue
        sub = zf[s][rr0:rr1, cc0:cc1]; tgt = (slice(rr0-r0, rr0-r0+sub.shape[0]), slice(cc0-c0, cc0-c0+sub.shape[1]))
        v = (sub - zc[tgt]) / (k*PX); np.maximum(best[tgt], v, out=best[tgt])
    H[i] = np.degrees(np.arctan(best))
print('horizons', time.time()-t0)
np.save('data/H48.npy', H)
S = json.load(open('data/sites.json')); sB = np.array(S['sB']); sL = np.array(S['sL']); eB = np.array(S['eB']); eL = np.array(S['eL'])
def lit(i): return np.clip((-sB[i] + 0.266 - H[int(round(sL[i] % 360 / (360/ND))) % ND]) / 0.533, 0, 1)
acc = np.zeros(zc.shape, np.float32); mx = np.zeros(zc.shape, np.float32); ev = np.zeros(zc.shape, np.float32); n = 0
for i in range(0, len(sB), 6):
    l = lit(i); acc += l; np.maximum(mx, l, out=mx); ev += ((-eB[i] - 0.26) - H[int(round(eL[i] % 360 / (360/ND))) % ND]) > 0.5; n += 1
np.save('data/illum.npy', acc/n); np.save('data/psr.npy', (mx <= 0)); np.save('data/earth.npy', ev/n)
gy, gx = np.gradient(g[A0:A1, A0:A1], PX); np.save('data/slope.npy', np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)); np.save('data/crop.npy', g[A0:A1, A0:A1])
i0 = int(np.argmin(sB)); print('summer idx', i0, S['alldates'][i0])
for j, i in enumerate([i0, i0+168, i0+336]): np.save(f'data/lit{j}.npy', lit(i)); print(S['alldates'][i], sL[i], sB[i])
print('mean illum', float((acc/n).mean()), 'psr %', float((mx <= 0).mean()*100), 'earth mean', float((ev/n).mean()))
