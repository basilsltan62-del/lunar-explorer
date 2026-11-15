import numpy as np, json, subprocess, io, base64, urllib.parse, urllib.request, os
from PIL import Image
from scipy import ndimage as ndi
R = 1737400.0; D2R = np.pi/180
def horizons(params):
    q = dict(format='text', MAKE_EPHEM="'YES'", EPHEM_TYPE="'OBSERVER'", CSV_FORMAT="'YES'"); q.update(params)
    out = subprocess.run(['curl', '-sS', '-m', '180', '-G', 'https://ssd.jpl.nasa.gov/api/horizons.api'] + sum([['--data-urlencode', f'{k}={v}'] for k, v in q.items()], []), capture_output=True, text=True).stdout
    rows = []; on = False
    for l in out.splitlines():
        if '$$SOE' in l: on = True; continue
        if '$$EOE' in l: break
        if on: rows.append(l.split(','))
    return rows
def eph(a, b):
    f = f'data/eph_{a}_{b}.json'
    if os.path.exists(f): return json.load(open(f))
    rows = horizons(dict(COMMAND="'301'", CENTER="'500@399'", START_TIME=f"'{a}'", STOP_TIME=f"'{b}'", STEP_SIZE="'1 h'", QUANTITIES="'14,15,19,20'"))
    d = dict(t0=a, n=len(rows), eL=[float(r[3]) for r in rows], eB=[float(r[4]) for r in rows], sL=[float(r[5]) for r in rows], sB=[float(r[6]) for r in rows], r=[float(r[7]) for r in rows], d=[float(r[9]) for r in rows]); json.dump(d, open(f, 'w')); return d
E1 = eph('2027-01-01', '2029-01-01'); E0 = eph('2025-03-01', '2025-03-22'); print(E1['n'], E0['n'])
dem = np.fromfile('data/LDEM_80S_80M.IMG', dtype='<i2').reshape(7600, 7600).astype(np.float32)*0.5
def vec(lat, lon): lat = np.asarray(lat)*D2R; lon = np.asarray(lon)*D2R; return np.stack([np.cos(lat)*np.cos(lon), np.cos(lat)*np.sin(lon), np.sin(lat)], -1)
def xy(lat, lon): r = 2*R*np.tan((90+lat)*D2R/2); return r*np.sin(lon*D2R), r*np.cos(lon*D2R)
def rc(x, y): return 3799.5 - y/80, 3799.5 + x/80
def ll(x, y): return 2*np.degrees(np.arctan(np.hypot(x, y)/(2*R))) - 90, np.degrees(np.arctan2(x, y))
def horizon(lat, lon, mast=2.0):
    x0, y0 = xy(lat, lon); r0, c0 = rc(x0, y0); h0 = dem[int(round(r0)), int(round(c0))] + mast
    d = np.concatenate([np.arange(80, 4000, 40), np.arange(4000, 30000, 80), np.arange(30000, 300000, 240)]).astype(np.float64); az = np.arange(360)*D2R
    nx, ny, ex, ey = np.sin(lon*D2R), np.cos(lon*D2R), np.cos(lon*D2R), -np.sin(lon*D2R)
    X = x0 + (np.cos(az)[:, None]*nx + np.sin(az)[:, None]*ex)*d; Y = y0 + (np.cos(az)[:, None]*ny + np.sin(az)[:, None]*ey)*d; rr, cc = rc(X, Y)
    ok = (rr > 0) & (rr < 7599) & (cc > 0) & (cc < 7599); ht = dem[np.clip(np.round(rr).astype(int), 0, 7599), np.clip(np.round(cc).astype(int), 0, 7599)]
    ang = np.where(ok, np.degrees(np.arctan2(ht - h0 - d*d/(2*R), d)), -90); return ang.max(1), float(h0 - mast)
def snap(lat, lon, rad):
    if not rad: return lat, lon
    x0, y0 = xy(lat, lon); r0, c0 = [int(v) for v in rc(x0, y0)]; n = int(rad/80); w = dem[r0-n:r0+n+1, c0-n:c0+n+1]; i, j = np.unravel_index(w.argmax(), w.shape); return ll((c0-n+j-3799.5)*80, (3799.5-(r0-n+i))*80)
sm = ndi.uniform_filter(dem, 3); 
def slope_at(lat, lon):
    r0, c0 = [int(round(v)) for v in rc(*xy(lat, lon))]; return float(np.degrees(np.arctan(np.hypot(sm[r0, c0+2]-sm[r0, c0-2], sm[r0+2, c0]-sm[r0-2, c0])/320)))
SITES = [('A', 'Shackleton rim', 'حافة Shackleton', -89.67, 129.78, 14000, 'Rim of Shackleton crater, next to the pole.', 'حافة فوهة Shackleton الملاصقة للقطب.'), ('B', 'Connecting Ridge', 'Connecting Ridge', -89.45, 222.69, 1500, 'Ridge between Shackleton and de Gerlache craters.', 'الحافة الواصلة بين فوهتي Shackleton و de Gerlache.'), ('C', 'Malapert massif', 'جبل Malapert', -85.99, -2.93, 9000, 'High massif facing Earth.', 'كتلة جبلية عالية مواجهة للأرض.'), ('D', 'Mons Mouton', 'Mons Mouton', -84.6, 31.0, 8000, 'Broad flat-topped mountain.', 'جبل واسع مسطح القمة.'), ('E', 'de Gerlache rim', 'حافة de Gerlache', -88.5, -87.1, 20000, 'Rim of de Gerlache crater.', 'حافة فوهة de Gerlache.'), ('F', 'Nobile rim', 'حافة Nobile', -85.2, 53.5, 8000, 'Rim of Nobile crater.', 'حافة فوهة Nobile.'), ('G', 'IM-2 landing area', 'منطقة هبوط IM-2', -84.7906, 29.1957, 0, 'Approximate IM-2 (Athena) landing point on Mons Mouton, 6/3/2025. Coordinates to be confirmed.', 'نقطة هبوط IM-2 (Athena) التقريبية على Mons Mouton، 6/3/2025. الإحداثيات تحتاج تأكيداً.')]
out = []
for k, en, ar, la, lo, rad, den, dar in SITES:
    lat, lon = snap(la, lo, rad); hz, h0 = horizon(lat, lon); out.append(dict(k=k, en=en, ar=ar, lat=round(float(lat), 4), lon=round(float(lon % 360), 3), elev=round(h0), slope=round(slope_at(lat, lon), 1), hz=[round(float(v), 2) for v in hz], den=den, dar=dar, src=80)); print(k, out[-1]['lat'], out[-1]['lon'], out[-1]['elev'], out[-1]['slope'])
json.dump(out, open('pack/sites.json', 'w'))
# independent check vs Horizons topocentric (site B)
B = out[1]; rows = horizons(dict(COMMAND="'10'", CENTER="'coord@301'", COORD_TYPE="'GEODETIC'", SITE_COORD=f"'{B['lon']},{B['lat']},{B['elev']/1000}'", START_TIME="'2027-01-01'", STOP_TIME="'2027-12-31'", STEP_SIZE="'30 d'", QUANTITIES="'4'"))
rowsE = horizons(dict(COMMAND="'399'", CENTER="'coord@301'", COORD_TYPE="'GEODETIC'", SITE_COORD=f"'{B['lon']},{B['lat']},{B['elev']/1000}'", START_TIME="'2027-01-01'", STOP_TIME="'2027-12-31'", STEP_SIZE="'30 d'", QUANTITIES="'4'"))
print(rows[:2]); s = vec(B['lat'], B['lon']); la, lo = B['lat']*D2R, B['lon']*D2R; n = np.array([-np.sin(la)*np.cos(lo), -np.sin(la)*np.sin(lo), np.cos(la)]); e = np.array([-np.sin(lo), np.cos(lo), 0]); chk = []
for i, (r, re) in enumerate(zip(rows, rowsE)):
    j = i*720; u = vec(E1['sB'][j], E1['sL'][j]); ue = vec(E1['eB'][j], E1['eL'][j])*E1['d'][j]*1.495978707e11 - s*(R+B['elev']); ue /= np.linalg.norm(ue)
    f = [r[3], r[4]]; fe = [re[3], re[4]]
    chk.append(dict(date=r[0].strip(), saz=round(float(np.degrees(np.arctan2(u@e, u@n)) % 360), 2), sel=round(float(np.degrees(np.arcsin(u@s))), 3), hsaz=float(f[0]), hsel=float(f[1]), eaz=round(float(np.degrees(np.arctan2(ue@e, ue@n)) % 360), 2), eel=round(float(np.degrees(np.arcsin(ue@s))), 3), heaz=float(fe[0]), heel=float(fe[1])))
for c in chk[:13]: print(c)
json.dump(chk, open('pack/check.json', 'w'))
# ephemeris pack
def f32(a): return base64.b64encode(np.asarray(a, np.float32).tobytes()).decode()
json.dump([dict(t0=E['t0'], n=E['n'], **{k: f32(E[k]) for k in ('sL', 'sB', 'eL', 'eB', 'r', 'd')}) for E in (E0, E1)], open('pack/eph.json', 'w'))
# DEM 240 m
g = np.load('data/g240.npy'); u = np.clip(np.round(g + 10000), 0, 65535).astype(np.uint16); rgb = np.zeros((2533, 2533, 3), np.uint8); rgb[..., 0] = u >> 8; rgb[..., 1] = u & 255
Image.fromarray(rgb).save('pack/dem.png', optimize=True); print('dem png', os.path.getsize('pack/dem.png'), g.min(), g.max())
# layers
H = np.load('data/H48.npy'); sB = np.array(E1['sB'][:8760]); sL = np.array(E1['sL'][:8760]); cur = np.zeros(H.shape[1:], np.float32); best = cur.copy()
for i in range(0, 8760, 6):
    dk = (-sB[i] + 0.266 - H[int(round(sL[i] % 360/7.5)) % 48]) < 0.027; cur = np.where(dk, cur+6, 0); np.maximum(best, cur, out=best)
il = np.load('data/illum.npy')*100; ev = np.load('data/earth.npy')*100; sl = np.load('data/slope.npy'); psr = np.load('data/psr.npy')
L1 = np.stack([np.clip(il*2.55, 0, 255), np.clip(ev*2.55, 0, 255), np.clip(sl*4, 0, 255)], -1).astype(np.uint8); L2 = np.stack([np.clip(np.sqrt(best)*2.7, 0, 255), psr*255, np.zeros_like(il)], -1).astype(np.uint8)
Image.fromarray(L1).save('pack/L1.png', optimize=True); Image.fromarray(L2).save('pack/L2.png', optimize=True)
Image.open('mock/base.jpg').save('pack/base.jpg', quality=86); print({f: os.path.getsize('pack/'+f) for f in os.listdir('pack')}, 'dark max', best.max(), 'psr share', psr.mean())
