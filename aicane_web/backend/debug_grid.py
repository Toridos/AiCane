import numpy as np
import matplotlib.pyplot as plt

grid = np.load("uploads/S4_1_grid.npy")

plt.figure(figsize=(8,8))
plt.imshow(grid, cmap="gray")
plt.title("Occupancy Grid (0=free, 1=wall)")
plt.show()
