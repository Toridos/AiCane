import numpy as np, glob, os
from PIL import Image

grid_path='static/grid_f1.npy'
if not os.path.exists(grid_path):
    print('ERROR: GRID_NOT_FOUND', grid_path)
else:
    g=np.load(grid_path)
    print('GRID_SHAPE', g.shape)  # (H, W)

imgs=sorted(glob.glob('static/*.png'))
if not imgs:
    print('NO_PNGS_FOUND in static')
else:
    for p in imgs:
        try:
            im=Image.open(p)
            print('IMG', p, im.size)  # (W, H)
        except Exception as e:
            print('IMG', p, 'ERROR', e)

# Check txt file lines
txt_path='static/grid_f1.txt'
if not os.path.exists(txt_path):
    print('ERROR: TXT_NOT_FOUND', txt_path)
else:
    with open(txt_path,'r',encoding='utf-8') as f:
        lines=f.read().splitlines()
    print('TXT_LINES', len(lines))
    if len(lines)>0:
        print('SAMPLE_LINE0_LEN', len(lines[0]))
        print('SAMPLE_LINE0_PREVIEW', lines[0][:500])
