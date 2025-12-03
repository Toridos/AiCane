import numpy as np

grid = np.loadtxt('grid_map.txt', dtype=int)
pts = []
with open('path.txt') as f:
    for l in f:
        if l.strip():
            x,y = map(int, l.strip().split(','))
            pts.append((x,y))
blocked = [(x,y,grid[y,x]) for x,y in pts]

cnt_blocked = sum(1 for _,_,v in blocked if v==1)
cnt_free = sum(1 for _,_,v in blocked if v==0)
print('Total path points:', len(blocked))
print('Blocked along path (grid==1):', cnt_blocked)
print('Free along path (grid==0):', cnt_free)
if cnt_blocked>0:
    print('\nExample blocked cells on path (first 10):')
    for e in blocked:
        if e[2]==1:
            print(e)
            break
else:
    print('\nNo blocked cells on path')
