import numpy as np, json, os
from scipy import ndimage as ndi
from PIL import Image
N = 2533; O = 1943; D2R = np.pi/180; R = 1737400.0; C0 = 1266.17
rd = lambda f: np.fromfile(f'data/{f}.IMG', dtype='<i2').reshape(6420, 6420)[O:O+N, O:O+N].astype(np.float32)
sun = rd('AVGVISIB_65S_240M_201608')*0.00004*100; ear = rd('AVGVISIB_65S_240M_201608_EARTH')*0.00004*100; psr = rd('LPSR_65S_240M_201608') > 0
print('NASA sun max', sun.max(), 'earth max', ear.max(), 'psr share', psr.mean())
# ---- validation of our own computation against NASA's published maps
il = np.load('data/w_il.npy'); ea = np.load('data/w_ea.npy'); mypsr = np.load('data/w_psr.npy'); LN = 1266
ns = sun[:2*LN, :2*LN].reshape(LN, 2, LN, 2).mean((1, 3)); ne = ear[:2*LN, :2*LN].reshape(LN, 2, LN, 2).mean((1, 3)); npsr = psr[:2*LN, :2*LN].reshape(LN, 2, LN, 2).mean((1, 3)) > .5
yy, xx = np.mgrid[0:LN, 0:LN]; rad = np.hypot(xx*2-C0, yy*2-C0)*240; lat = 2*np.degrees(np.arctan(rad/(2*R))) - 90
def cmp(m): a, b = il[m], ns[m]; return dict(corr=float(np.corrcoef(a, b)[0, 1]), bias=float((a-b).mean()), mad=float(np.abs(a-b).mean()))
inner = lat < -85; allm = lat < -80.5
V = dict(inner=cmp(inner), all=cmp(allm), earth_inner=dict(corr=float(np.corrcoef(ea[inner], ne[inner])[0, 1]), bias=float((ea[inner]-ne[inner]).mean())), psr_ours_km2=float((mypsr & inner).sum()*0.48*0.48), psr_nasa_km2=float((npsr & inner).sum()*0.48*0.48), psr_overlap=float((mypsr & npsr & inner).sum()/max(1, (npsr & inner).sum())))
S = json.load(open('pack/sites.json')); sites = []
for s in S:
    r = 2*R*np.tan((90+s['lat'])*D2R/2); rr = int(round(C0 - r*np.cos(s['lon']*D2R)/240)); cc = int(round(C0 + r*np.sin(s['lon']*D2R)/240)); w = sun[rr-1:rr+2, cc-1:cc+2]; sites.append(dict(k=s['k'], nasa_cell=float(sun[rr, cc]), nasa_max3=float(w.max()), nasa_earth=float(ear[rr, cc])))
V['sites'] = sites; json.dump(V, open('pack/valid.json', 'w')); print(json.dumps(V, indent=0)[:1500])
# ---- class rasters at 240 m, smoothed and despeckled
def classes(f, ed, sig=1.0):
    c = np.digitize(ndi.gaussian_filter(f, sig), ed).astype(np.uint8); c = ndi.median_filter(c, 3); return ndi.median_filter(c, 3)
up = lambda a: ndi.gaussian_filter(np.pad(ndi.zoom(a, 2, order=1), ((0, 1), (0, 1)), mode='edge'), 1.5)
g = np.load('data/g240.npy'); gy, gx = np.gradient(ndi.gaussian_filter(g, 0.8), 240.0); slope = np.degrees(np.arctan(np.hypot(gx, gy)))
dark = up(np.load('data/w_dark.npy'))/24.0
cI = classes(sun, [5, 20, 35, 50]); cE = classes(ear, [5, 25, 50, 75]); cS = classes(slope, [5, 10, 15, 25], .6); cD = classes(dark, [2, 7, 14, 90], .8)
ps = ndi.binary_opening(psr, iterations=1) | psr; lab, k = ndi.label(psr); sz = ndi.sum(psr, lab, range(1, k+1)); big = np.isin(lab, 1+np.where(sz >= 35)[0])
ice = np.zeros((N, N), np.uint8); ss = ndi.gaussian_filter(sun, 1.0); ice[ss < 20] = 1; ice[(dark > 90) | (ss < 5)] = 2; ice = ndi.median_filter(ice, 3); ice[psr] = 3; ice[big] = 4
cP = psr.astype(np.uint8)
Image.fromarray(np.stack([cI, cE, cS], -1)*50).save('pack/C1.png', optimize=True); Image.fromarray(np.stack([cD, cP, ice], -1)*50).save('pack/C2.png', optimize=True)
json.dump(dict(illum=[float((cI == c).mean()*100) for c in range(5)]), open('pack/shares.json', 'w'))
# ---- sharper base relief: 160 m for the whole region, 80 m for 88-90 S
dem = np.fromfile('data/LDEM_80S_80M.IMG', dtype='<i2').reshape(7600, 7600).astype(np.float32)*0.5
def relief(z, px, q, name):
    zs = ndi.gaussian_filter(z, 0.6); gy, gx = np.gradient(zs, px)
    def hs(az, alt): a = az*D2R; l = np.sqrt(gx*gx+gy*gy+1); return np.clip((-gx*np.sin(a)*np.cos(alt*D2R) + gy*np.cos(a)*np.cos(alt*D2R) + np.sin(alt*D2R))/l, 0, 1)
    soft = hs(315, 38)*.55 + hs(45, 40)*.25 + hs(225, 45)*.2; el = np.clip((z+4500)/11000, 0, 1); tone = np.stack([150+70*el, 146+68*el, 140+64*el], -1); Image.fromarray(np.clip(tone*(0.3+0.95*soft)[..., None], 0, 255).astype(np.uint8)).save('pack/'+name, quality=q)
relief(dem.reshape(3800, 2, 3800, 2).mean((1, 3)), 160.0, 80, 'base160.jpg'); relief(dem[3042:4558, 3042:4558], 80.0, 84, 'inner80.jpg')
print({f: os.path.getsize('pack/'+f) for f in ('C1.png', 'C2.png', 'base160.jpg', 'inner80.jpg')}, 'ice shares', [round(float((ice == c).mean()*100), 1) for c in range(5)])
