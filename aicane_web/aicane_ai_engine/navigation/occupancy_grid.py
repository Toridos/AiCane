import numpy as np

def build_grid(mask):
    # mask: 1=벽, 0=통로
    grid = mask.astype(np.uint8)

    # 저장
    np.save("uploads/grid.npy", grid)

    return grid
