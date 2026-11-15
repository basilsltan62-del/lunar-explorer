import numpy as np, json, os
from scipy import ndimage as ndi
from PIL import Image
N = 2533; O = 1943; LN = 1266
sun = np.fromfile('data/AVGVISIB_65S_240M_201608.IMG', dtype='<i2').reshape(6420, 6420)[O:O+N, O:O+N].astype(np.float32)*0.004
Image.fromarray(np.clip(np.round(sun), 0, 100).astype(np.uint8)).save('pack/nsun.png', optimize=True)
il = np.load('data/w_il.npy'); ns = sun[:2*LN, :2*LN].reshape(LN, 2, LN, 2).mean((1, 3)); d = ndi.gaussian_filter(il - ns, 1.0)
cls = np.digitize(d, [-10, -3, 3, 10]).astype(np.uint8); cls = ndi.median_filter(cls, 3); up = np.pad(np.repeat(np.repeat(cls, 2, 0), 2, 1), ((0, 1), (0, 1)), mode='edge')
Image.fromarray(np.stack([up*50, up*0, up*0], -1).astype(np.uint8)).save('pack/C3.png', optimize=True)
print({f: os.path.getsize('pack/'+f) for f in ('nsun.png', 'C3.png')}, [round(float((cls == k).mean()*100), 1) for k in range(5)])
