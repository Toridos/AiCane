import numpy as np
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'

def export(floor):
    npy = STATIC / f'grid_f{floor}.npy'
    stairs_json = STATIC / f'stairs_f{floor}.json'
    out_txt = STATIC / f'grid_f{floor}.txt'

    if not npy.exists():
        print(f'missing {npy}')
        return

    grid = np.load(npy)

    # ensure integer grid
    grid = grid.astype(int)

    # load stairs and mark as 2
    if stairs_json.exists():
        with open(stairs_json,'r',encoding='utf-8') as fh:
            stairs = json.load(fh)
        for s in stairs:
            try:
                x,y = int(s[0]), int(s[1])
                # guard boundaries (grid[y,x])
                if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
                    grid[y,x] = 2
            except Exception:
                continue

    # write as CSV (comma separated values) with rows = Y
    np.savetxt(out_txt, grid, fmt='%d')
    print(f'Wrote {out_txt} ({grid.shape[1]}x{grid.shape[0]})')

def main():
    for f in [1,2,3]:
        export(f)

if __name__ == '__main__':
    main()
