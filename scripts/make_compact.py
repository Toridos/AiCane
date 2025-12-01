import numpy as np, os

npy='static/grid_f1.npy'
out='static/grid_f1_compact.txt'

if not os.path.exists(npy):
    print('ERROR: grid not found', npy)
    raise SystemExit(1)

g=np.load(npy).astype(int)
with open(out,'w',encoding='utf-8',newline='\n') as f:
    for row in g:
        f.write(''.join(map(str,row))+'\n')
size=os.path.getsize(out)
with open(out,'r',encoding='utf-8') as f:
    first=f.readline().rstrip('\n')
    rows=1+sum(1 for _ in f)
print('WROTE', out)
print('FILE_SIZE_BYTES', size)
print('ROWS', rows)
print('FIRST_LINE_LEN', len(first))
print('EXPECTED_PER_LINE', g.shape[1])
print('EXPECTED_TOTAL_CHARS', g.shape[1]*g.shape[0])
