import numpy as np, json, time, os
from scipy import ndimage as ndi
from PIL import Image
R = 1737400.0; D2R = np.pi/180; N = 2533; PX = 240.0; C0 = 1266.17; LN = 1266
g = np.load('data/g240.npy'); ax = (np.arange(N, dtype=np.float32) - C0)*PX; z = (g - (ax[None, :]**2 + ax[:, None]**2)/(2*R)).astype(np.float32)
zf = {1: z, 3: ndi.maximum_filter(z, 3), 9: ndi.maximum_filter(z, 9), 27: ndi.maximum_filter(z, 27)}
ks = [1]
while ks[-1] < 1300: ks.append(max(ks[-1]+1, int(ks[-1]*1.06)))
zc = z[0:2*LN:2, 0:2*LN:2]; ND = 48; H = np.zeros((ND, LN, LN), np.float32); t0 = time.time()
for i in range(ND):
    lam = i*360/ND*D2R; dc, dr = np.sin(lam), -np.cos(lam); best = np.full(zc.shape, -1e9, np.float32); prev = 0
    for k in ks:
        gap = k-prev; prev = k; s = 1 if gap <= 1 else 3 if gap <= 4 else 9 if gap <= 12 else 27; oc, orr = int(round(k*dc)), int(round(k*dr))
        a0 = max(0, -(-max(0, -orr)//2)); a1 = min(LN-1, (N-1-orr)//2); b0 = max(0, -(-max(0, -oc)//2)); b1 = min(LN-1, (N-1-oc)//2)
        if a1 < a0 or b1 < b0: continue
        sub = zf[s][2*a0+orr:2*a1+orr+1:2, 2*b0+oc:2*b1+oc+1:2]; tgt = (slice(a0, a1+1), slice(b0, b1+1)); np.maximum(best[tgt], (sub - zc[tgt])/(k*PX), out=best[tgt])
    H[i] = np.degrees(np.arctan(best))
print('horizons', round(time.time()-t0, 1))
E1 = json.load(open('data/eph_2027-01-01_2029-01-01.json')); sB = np.array(E1['sB'][:8760]); sL = np.array(E1['sL'][:8760]); eB = np.array(E1['eB'][:8760]); eL = np.array(E1['eL'][:8760])
acc = np.zeros((LN, LN), np.float32); mx = acc.copy(); ev = acc.copy(); cur = acc.copy(); best = acc.copy(); n = 0
for i in range(0, 8760, 6):
    l = np.clip((-sB[i] + 0.266 - H[int(round(sL[i] % 360/7.5)) % 48])/0.533, 0, 1); acc += l; np.maximum(mx, l, out=mx); ev += ((-eB[i]-0.26) - H[int(round(eL[i] % 360/7.5)) % 48]) > 0.5; cur = np.where(l < 0.05, cur+6, 0); np.maximum(best, cur, out=best); n += 1
il = acc/n*100; ea = ev/n*100; psr = mx <= 0
gy, gx = np.gradient(g, PX); sl = np.degrees(np.arctan(np.hypot(gx, gy)))[0:2*LN, 0:2*LN].reshape(LN, 2, LN, 2).mean((1, 3))
lab, k = ndi.label(psr); sz = ndi.sum(psr, lab, range(1, k+1)); big = np.isin(lab, 1+np.where(sz >= 9)[0])
ice = np.zeros((LN, LN), np.uint8); ice[il < 20] = 1; ice[(best > 90*24) | (il < 5)] = 2; ice[psr] = 3; ice[big] = 4
np.save('data/w_il.npy', il); np.save('data/w_ea.npy', ea); np.save('data/w_dark.npy', best); np.save('data/w_psr.npy', psr)
print('shares', [round(float((ice == c).mean()*100), 1) for c in range(5)], 'illum mean', float(il.mean()))
L1 = np.stack([np.round(np.clip(il, 0, 100))*2.55, np.round(np.clip(ea, 0, 100))*2.55, np.round(np.clip(sl, 0, 63))*4], -1); L2 = np.stack([np.round(np.clip(np.sqrt(best)*2.7, 0, 255)/3)*3, psr*255, ice*60], -1)
Image.fromarray(np.clip(np.round(L1), 0, 255).astype(np.uint8)).save('pack/L1w.png', optimize=True); Image.fromarray(np.clip(L2, 0, 255).astype(np.uint8)).save('pack/L2w.png', optimize=True)
gs = ndi.gaussian_filter(g, 0.7); gy, gx = np.gradient(gs, PX)
def hs(az, alt): a = az*D2R; l = np.sqrt(gx*gx+gy*gy+1); return np.clip((-gx*np.sin(a)*np.cos(alt*D2R) + gy*np.cos(a)*np.cos(alt*D2R) + np.sin(alt*D2R))/l, 0, 1)
soft = hs(315, 40)*.5 + hs(45, 40)*.25 + hs(225, 45)*.25; el = np.clip((g-np.percentile(g, 1))/(np.percentile(g, 99)-np.percentile(g, 1)), 0, 1); tone = np.stack([150+70*el, 146+68*el, 140+64*el], -1)
Image.fromarray(np.clip(tone*(0.35+0.9*soft)[..., None], 0, 255).astype(np.uint8)).save('pack/basew.jpg', quality=84); print({f: os.path.getsize('pack/'+f) for f in ('L1w.png', 'L2w.png', 'basew.jpg')})
