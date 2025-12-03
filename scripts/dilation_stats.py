import numpy as np
import os

OUT = 'dilation_sweep_outputs'
RADII = [1,3,5,7]

for r in RADII:
    grid_path = os.path.join(OUT, f'grid_map_dilate_{r}.txt')
    path_path = os.path.join(OUT, f'path_dilate_{r}.txt')
    grid = np.loadtxt(grid_path, dtype=int)
    wall_cells = np.argwhere(grid==1)
    wall_count = len(wall_cells)

    pts = []
    with open(path_path) as f:
        for l in f:
            if l.strip():
                x,y = map(int, l.strip().split(','))
                pts.append((x,y))
    path_len = len(pts)

    # min distance from path to any wall (grid units)
    if wall_count==0 or path_len==0:
        min_grid_dist = None
    else:
        dmin = float('inf')
        wy = wall_cells[:,0]; wx = wall_cells[:,1]
        for x,y in pts:
            dx = wx - x
            dy = wy - y
            d2 = dx*dx + dy*dy
            d = int(np.sqrt(d2.min()))
            if d < dmin:
                dmin = d
        min_grid_dist = dmin

    print(f'radius={r:2d} | wall_cells={wall_count:6d} | path_len={path_len:3d} | min_dist_to_wall={min_grid_dist}')
