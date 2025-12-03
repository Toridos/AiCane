import cv2
import numpy as np

# sample point from path
xg, yg = 362, 261

# load grid
grid = np.loadtxt('grid_map.txt', dtype=int)
print('grid[yg,xg]=', grid[yg, xg])

# load sizes from run_seg printed values (if needed)
orig_w, orig_h = 2667, 1500
new_w, new_h = 800, 480

# compute original coords
x_orig = int(xg * (orig_w / new_w))
y_orig = int(yg * (orig_h / new_h))
print('scaled back to orig:', x_orig, y_orig)

# sample mask_overlay.png
img = cv2.imread('mask_overlay.png')
if img is None:
    print('mask_overlay.png not found')
else:
    h,w = img.shape[:2]
    print('mask_overlay size:', w,h)
    if 0 <= x_orig < w and 0 <= y_orig < h:
        b,g,r = img[y_orig,x_orig]
        print('mask_overlay pixel BGR:', (b,g,r))
    else:
        print('point outside mask_overlay')

# Also sample overlay_with_path.png
img2 = cv2.imread('overlay_with_path.png')
if img2 is None:
    print('overlay_with_path.png not found')
else:
    h2,w2 = img2.shape[:2]
    print('overlay_with_path size:', w2,h2)
    if 0 <= x_orig < w2 and 0 <= y_orig < h2:
        b,g,r = img2[y_orig,x_orig]
        print('overlay_with_path pixel BGR:', (b,g,r))
    else:
        print('point outside overlay_with_path')
