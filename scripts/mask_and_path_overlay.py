import sys
from pathlib import Path
import os
import cv2
import numpy as np

# ensure repo root on path
repo_root = str(Path(__file__).resolve().parents[1])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from run_navigation import run_seg

# Configuration - match the last run parameters
IMAGE = r"C:\SW_3_2\ai\AI_lab\yolo_dataset\images\APT_FP_OCR_230087881.PNG"
PATH_FILE = Path(repo_root) / "path.txt"
OUT_FILE = Path(repo_root) / "mask_and_path_overlay.png"
WALL_DILATE = 0
CLEARANCE_PX = 9

print(f"Loading image: {IMAGE}")
# run segmentation to get masks and sizes
masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_seg(IMAGE)

# build wall mask same as mask_to_grid logic
mask_arr = masks.data.cpu().numpy()
classes = boxes.cls.cpu().numpy().astype(int)
H, W = mask_arr[0].shape
wall_mask = np.zeros((H, W), dtype=bool)
for seg_np, cls in zip(mask_arr, classes):
    if int(cls) == 0:
        wall_mask = np.logical_or(wall_mask, seg_np > 0.5)

# dilation if requested
if WALL_DILATE and wall_mask.any():
    wall_uint = (wall_mask.astype('uint8') * 255)
    ksize = max(1, 2 * int(WALL_DILATE) + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    wall_dilated = cv2.dilate(wall_uint, kernel)
    wall_mask = wall_dilated > 0

# clearance via distance transform
if CLEARANCE_PX and wall_mask.any():
    wall_uint2 = (wall_mask.astype('uint8') * 255)
    inv = 255 - wall_uint2
    dt = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    close_mask = dt < float(CLEARANCE_PX)
    wall_mask = np.logical_or(wall_mask, close_mask)

# Load original image (use orig size if available)
img = cv2.imread(IMAGE)
if img is None:
    raise SystemExit(f"Cannot open image: {IMAGE}")
orig_h_img, orig_w_img = img.shape[:2]

# Scale wall_mask to original image size
wall_mask_up = cv2.resize((wall_mask.astype('uint8')*255), (orig_w_img, orig_h_img), interpolation=cv2.INTER_NEAREST) > 0

# Create overlay: tint walls red with alpha
overlay = img.copy()
red = np.zeros_like(img)
red[:, :] = (0, 0, 255)  # BGR red
alpha = 0.5
overlay = np.where(wall_mask_up[..., None], cv2.addWeighted(img, 1-alpha, red, alpha, 0), img)

# Read path points from path.txt if exists
path_points = []
if PATH_FILE.exists():
    with open(PATH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                x,y = line.split(',')
                gx = int(x); gy = int(y)
                # scale grid coords (mask coords) back to orig image coords
                x_orig = int(gx * (orig_w_img / new_w))
                y_orig = int(gy * (orig_h_img / new_h))
                path_points.append((x_orig, y_orig))
            except Exception:
                continue
else:
    print("[!] path.txt not found in repo root; no path overlay will be drawn.")

# Draw path on overlay
if path_points:
    for p in path_points:
        cv2.circle(overlay, p, 6, (255, 0, 0), -1)  # blue points
    cv2.polylines(overlay, [np.array(path_points, dtype=np.int32)], False, (255,0,0), 3)

# Draw wall mask contour for clarity
contours, _ = cv2.findContours((wall_mask_up.astype('uint8')*255), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(overlay, contours, -1, (0,255,255), 2)  # cyan contours

cv2.imwrite(str(OUT_FILE), overlay)
print(f"Saved overlay to: {OUT_FILE}")
