import os
import cv2
import numpy as np
from pathlib import Path

# ensure repo root on path
import sys
proj_root = str(Path(__file__).resolve().parents[1])
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from run_navigation import run_seg, run_ocr, mask_to_grid, bfs, find_room

IMAGE_PATH = r"C:\SW_3_2\toridos\AiCane\s4-1\s4-1_floor1.png"
OUT_DIR = "dilation_overlays_s4_1"
os.makedirs(OUT_DIR, exist_ok=True)

print('[+] Running segmentation...')
masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_seg(IMAGE_PATH)
print(f'    seg sizes: orig=({orig_w},{orig_h}) new=({new_w},{new_h})')

print('[+] Running OCR...')
text_positions = run_ocr(IMAGE_PATH)
items = list(text_positions.keys())
print('    OCR texts:', items[:20])

# prefer explicit start/goal if present from earlier run; otherwise take first two
preferred_start = '117호'
preferred_goal = '104호'
start_name = preferred_start if preferred_start in items else (items[0] if len(items) > 0 else None)
goal_name = preferred_goal if preferred_goal in items else (items[1] if len(items) > 1 else None)

if not start_name or not goal_name:
    raise SystemExit('[!] Not enough OCR texts found to choose start/goal')

print(f'[+] Using start="{start_name}", goal="{goal_name}"')

start_pos = find_room(start_name, text_positions)
goal_pos = find_room(goal_name, text_positions)
if start_pos is None or goal_pos is None:
    raise SystemExit('[!] Could not resolve start/goal positions')

def scale_point_to_mask(p):
    x, y = p
    sx = int(x * (new_w / orig_w))
    sy = int(y * (new_h / orig_h))
    sx = max(0, min(new_w-1, sx))
    sy = max(0, min(new_h-1, sy))
    return (sx, sy)

start_scaled = scale_point_to_mask(start_pos)
goal_scaled = scale_point_to_mask(goal_pos)

# reconstruct wall_mask (un-dilated) from segmentation outputs
mask_arr = masks.data.cpu().numpy()
classes = boxes.cls.cpu().numpy().astype(int)
H, W = mask_arr[0].shape

# Determine which class(es) to treat as wall. If class 0 exists, use it.
# Otherwise fall back to the most frequent class in the segmentation output (likely class 2 in this image).
unique, counts = np.unique(classes, return_counts=True)
class_counts = dict(zip(unique.tolist(), counts.tolist()))
print('[+] Segmentation classes found:', class_counts)
if 0 in class_counts:
    wall_classes = [0]
    print('[+] Using class 0 as wall')
else:
    # choose the most common class as wall fallback
    most_common = max(class_counts.items(), key=lambda x: x[1])[0]
    wall_classes = [int(most_common)]
    print(f"[!] class 0 not found — falling back to class {most_common} as wall")

wall_mask_base = np.zeros((H, W), dtype=bool)
for seg_np, cls in zip(mask_arr, classes):
    if int(cls) in wall_classes:
        wall_mask_base = np.logical_or(wall_mask_base, seg_np > 0.5)

def make_overlay_for_dilate(r):
    # apply dilation to wall mask
    wall_uint = (wall_mask_base.astype('uint8') * 255)
    ksize = max(1, 2 * int(r) + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    wall_dilated = cv2.dilate(wall_uint, kernel)
    wall_dilated_bool = wall_dilated > 0

    # build grid from wall_dilated_bool
    grid = np.zeros_like(wall_dilated_bool, dtype=np.uint8)
    grid[wall_dilated_bool] = 1

    path = bfs(grid, start_scaled, goal_scaled)

    # scale dilated mask to original image size
    mask_resized = cv2.resize((wall_dilated_bool.astype('uint8') * 255), (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

    img = cv2.imread(IMAGE_PATH)
    over = img.copy()

    # overlay mask (red, semi-transparent)
    red = np.zeros_like(img)
    red[:, :, 2] = mask_resized
    alpha = 0.5
    mask_bool = mask_resized > 0
    over = cv2.addWeighted(over, 1.0, red, alpha, 0)

    # draw path scaled back to original coords
    if path:
        pts = []
        for (gx, gy) in path:
            x_orig = int(gx * (orig_w / float(W)))
            y_orig = int(gy * (orig_h / float(H)))
            pts.append((x_orig, y_orig))

        for p in pts:
            cv2.circle(over, p, 4, (255, 255, 0), -1)
        if len(pts) > 1:
            cv2.polylines(over, [np.array(pts, dtype=np.int32)], False, (255, 255, 0), 3)

    out_png = os.path.join(OUT_DIR, f'dilate_{r}_overlay.png')
    cv2.imwrite(out_png, over)

    # save grid and path
    np.savetxt(os.path.join(OUT_DIR, f'dilate_{r}_grid.txt'), grid, fmt='%d')
    if path:
        with open(os.path.join(OUT_DIR, f'dilate_{r}_path.txt'), 'w', encoding='utf-8') as f:
            for x,y in path:
                f.write(f"{x},{y}\n")

    print(f'[+] Saved {out_png} (path_len={len(path) if path else None})')
    return out_png, grid, path

if __name__ == '__main__':
    dilations = [9,11,13,17]
    results = []
    for r in dilations:
        out_png, grid, path = make_overlay_for_dilate(r)
        results.append({'r': r, 'overlay': out_png, 'path_len': len(path) if path else None})

    summary_path = os.path.join(OUT_DIR, 'dilation_summary.json')
    import json
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('[✔] All done. Outputs in', OUT_DIR)
