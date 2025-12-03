import cv2
import numpy as np
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
image_path = Path(r"C:\SW_3_2\toridos\AiCane\s4-1\s4-1_floor1.png")
# use existing grid file
grid_file = repo_root / "grid_map.txt"
path_file = repo_root / "path.txt"
out_file = repo_root / "mask_and_path_overlay.png"

if not grid_file.exists():
    print(f"[!] grid file not found: {grid_file}")
    sys.exit(1)

# load grid
grid = np.loadtxt(str(grid_file), dtype=np.uint8)
H, W = grid.shape
blocked = np.sum(grid == 1)
free = np.sum(grid == 0)
print(f"Grid shape: {grid.shape}  blocked={blocked}  free={free}  blocked_pct={blocked/(H*W):.3f}")

# read image
img = cv2.imread(str(image_path))
if img is None:
    print(f"[!] cannot open image at {image_path}")
    sys.exit(1)
orig_h, orig_w = img.shape[:2]

# resize grid to image size (nearest)
mask = (grid == 1).astype('uint8') * 255
mask_up = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

# color overlay: red for blocked
overlay = img.copy()
red = np.zeros_like(img)
red[:, :] = (0,0,255)
alpha = 0.5
mask_bool = mask_up.astype(bool)
overlay[mask_bool] = cv2.addWeighted(img, 1-alpha, red, alpha, 0)[mask_bool]

# draw grid contours
contours, _ = cv2.findContours(mask_up, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(overlay, contours, -1, (0,255,255), 2)

# read path points if exist
if path_file.exists():
    pts = []
    with open(path_file, 'r', encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln: continue
            x,y = ln.split(',')
            gx, gy = int(x), int(y)
            # scale from grid coords (W x H) to image coords
            x_orig = int(gx * (orig_w / W))
            y_orig = int(gy * (orig_h / H))
            pts.append((x_orig, y_orig))
    if pts:
        for p in pts:
            cv2.circle(overlay, p, 6, (255,0,0), -1)
        cv2.polylines(overlay, [np.array(pts, dtype=np.int32)], False, (255,0,0), 3)
else:
    print("[!] No path.txt found; not drawing path.")

cv2.imwrite(str(out_file), overlay)
print(f"Saved overlay -> {out_file}")
