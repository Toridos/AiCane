import numpy as np
from math import hypot

grid = np.loadtxt('grid_map.txt', dtype=int)
wall_cells = np.argwhere(grid==1)  # array of (y,x)
pts = []
with open('path.txt') as f:
    for l in f:
        if l.strip():
            x,y = map(int, l.strip().split(','))
            pts.append((x,y))

# compute min distance from each path point to any wall cell (in grid units)
if len(wall_cells)==0:
    print('No wall cells in grid')
else:
    min_dist = float('inf')
    for x,y in pts:
        # compute distances to all wall cells (could be large), but we can compute squared distances
        dx = wall_cells[:,1] - x
        dy = wall_cells[:,0] - y
        d2 = dx*dx + dy*dy
        dmin = int(np.sqrt(d2.min()))
        if dmin < min_dist:
            min_dist = dmin
    print('Minimum grid distance from path to nearest wall cell:', min_dist)

# Also show how many wall cells exist overall
print('Total wall cells:', len(wall_cells))
