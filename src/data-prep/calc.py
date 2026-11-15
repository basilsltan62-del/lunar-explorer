import numpy as np, json, time
from scipy import ndimage as ndi
R = 1737400.0; D2R = np.pi/180
dem = np.fromfile('data/LDEM_80S_80M.IMG', dtype='<i2').reshape(7600, 7600).astype(np.float32) * 0.5
# ---- ephemeris
rows = []
on = False
for l in open('data/eph2027.txt'):
    if '$$SOE' in l: on = True; continue
    if '$$EOE' in l: break
    if on:
        p = l.split(','); rows.append([float(x) for x in p[3:10:1] if x.strip()][:7] + [p[0].strip()])
eph = np.array([r[:7] for r in rows]); dates = [r[7] for r in rows]
eL, eB, sL, sB, rAU, _, dAU = eph.T
def vec(lat, lon): return np.stack([np.cos(lat*D2R)*np.cos(lon*D2R), np.cos(lat*D2R)*np.sin(lon*D2R), np.sin(lat*D2R)], -1)
U = vec(sB, sL); UE = vec(eB, eL) * (dAU * 1.495978707e11)[:, None]
def azel(lat, lon, h=0):
    s = vec(lat, lon); n = np.array([-np.sin(lat*D2R)*np.cos(lon*D2R), -np.sin(lat*D2R)*np.sin(lon*D2R), np.cos(lat*D2R)]); e = np.array([-np.sin(lon*D2R), np.cos(lon*D2R), 0])
    out = []
    for V in (U, (UE - s*(R+h)) / np.linalg.norm(UE - s*(R+h), axis=1)[:, None]):
        out += [np.degrees(np.arctan2(V@e, V@n)) % 360, np.degrees(np.arcsin(V@s))]
    return out  # sunAz, sunEl, earthAz, earthEl
def xy(lat, lon): r = 2*R*np.tan((90+lat)*D2R/2); return r*np.sin(lon*D2R), r*np.cos(lon*D2R)
def rc(x, y): return 3799.5 - y/80, 3799.5 + x/80
def ll(x, y): return 2*np.degrees(np.arctan(np.hypot(x, y)/(2*R))) - 90, np.degrees(np.arctan2(x, y))
def horizon(lat, lon, mast=2.0):
    x0, y0 = xy(lat, lon); r0, c0 = rc(x0, y0); h0 = dem[int(round(r0)), int(round(c0))] + mast
    d = np.concatenate([np.arange(80, 4000, 40), np.arange(4000, 30000, 80), np.arange(30000, 260000, 240)]).astype(np.float64)
    az = np.arange(360) * D2R; nx, ny = np.sin(lon*D2R), np.cos(lon*D2R); ex, ey = np.cos(lon*D2R), -np.sin(lon*D2R)
    dx = np.cos(az)[:, None]*nx + np.sin(az)[:, None]*ex; dy = np.cos(az)[:, None]*ny + np.sin(az)[:, None]*ey
    X = x0 + dx*d; Y = y0 + dy*d; rr, cc = rc(X, Y); rr = np.clip(np.round(rr).astype(int), 0, 7599); cc = np.clip(np.round(cc).astype(int), 0, 7599)
    ht = dem[rr, cc]; ang = np.degrees(np.arctan2(ht - h0 - d*d/(2*R), d)); k = ang.argmax(1)
    return ang.max(1), d[k], float(h0 - mast)
def snap(lat, lon, rad_m):
    x0, y0 = xy(lat, lon); r0, c0 = rc(x0, y0); n = int(rad_m/80); r0, c0 = int(r0), int(c0)
    w = dem[r0-n:r0+n+1, c0-n:c0+n+1]; i, j = np.unravel_index(w.argmax(), w.shape); r, c = r0-n+i, c0-n+j
    return ll((c-3799.5)*80, (3799.5-r)*80)
def runs(b):
    best = cur = 0
    for v in b:
        cur = cur+1 if v else 0; best = max(best, cur)
    return best
SITES = [('A', 'Shackleton rim', 'حافة Shackleton', -89.67, 129.78, 14000), ('B', 'Connecting Ridge', 'Connecting Ridge', -89.45, 222.69, 1500), ('C', 'Malapert massif', 'جبل Malapert', -85.99, -2.93, 9000), ('D', 'Mons Mouton', 'Mons Mouton', -84.6, 31.0, 20000), ('E', 'de Gerlache rim', 'حافة de Gerlache', -88.5, -87.1, 20000), ('F', 'Nobile rim', 'حافة Nobile', -85.2, 53.5, 30000)]
out = {'dates': dates[::1][:1], 'sites': []}
g240 = dem[:7599, :7599].reshape(2533, 3, 2533, 3).mean((1, 3))
gy, gx = np.gradient(g240, 240.0); slope240 = np.degrees(np.arctan(np.hypot(gx, gy)))
for key, en, ar, la, lo, rad in SITES:
    lat, lon = snap(la, lo, rad); hz, hd, h0 = horizon(lat, lon); sa, se, ea, ee = azel(lat, lon, h0)
    hs = hz[np.round(sa).astype(int) % 360]; he = hz[np.round(ea).astype(int) % 360]
    lit = np.clip((se + 0.266 - hs) / 0.533, 0, 1); com = (ee - he) > 0.5
    S = 1361.0 / rAU**2
    x0, y0 = xy(lat, lon); r0, c0 = rc(x0, y0); sl = float(slope240[int(r0/3), int(c0/3)])
    d = dict(key=key, en=en, ar=ar, lat=float(lat), lon=float(lon % 360), elev=h0, slope=sl, hz=hz.round(2).tolist(), hd=hd.round(0).tolist(), sa=sa.round(1).tolist(), se=se.round(2).tolist(), ea=ea.round(1).tolist(), ee=ee.round(2).tolist(), lit=lit.round(2).tolist(), com=com.astype(int).tolist(),
             illum=float(lit.mean()*100), comm=float(com.mean()*100), both=float(((lit > .5) & com).mean()*100), maxlight=runs(lit > .5), maxdark=runs(lit < .05), maxnocom=runs(~com))
    out['sites'].append(d); print(key, en, round(lat, 3), round(lon % 360, 2), 'h', round(h0), 'slope', round(sl, 1), 'illum%', round(d['illum'], 1), 'comm%', round(d['comm'], 1), 'both%', round(d['both'], 1), 'maxlight_h', d['maxlight'], 'maxdark_h', d['maxdark'], 'maxnocom_h', d['maxnocom'])
out['S'] = (1361.0 / rAU**2).round(1).tolist(); out['alldates'] = dates; out['sB'] = sB.round(3).tolist(); out['sL'] = sL.round(2).tolist(); out['eB'] = eB.round(3).tolist(); out['eL'] = eL.round(3).tolist()
json.dump(out, open('data/sites.json', 'w')); np.save('data/g240.npy', g240.astype(np.float32)); print('S range', out['S'][0], min(out['S']), max(out['S']), 'sunlat range', sB.min(), sB.max())
