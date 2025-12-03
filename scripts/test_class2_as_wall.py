import os
import json
from pathlib import Path
import numpy as np
import cv2
import sys

# ensure repo root on path
proj_root = str(Path(__file__).resolve().parents[1])
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from run_navigation import run_seg, run_ocr, find_room, bfs

IMAGE = r"C:\SW_3_2\toridos\AiCane\s4-1\s4-1_floor1.png"
OUT_DIR = os.path.join(proj_root, 'outputs', 'test_class2_wall')
os.makedirs(OUT_DIR, exist_ok=True)

print('[+] Running segmentation...')
masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_seg(IMAGE)
mask_arr = masks.data.cpu().numpy()
classes = boxes.cls.cpu().numpy().astype(int)
H, W = mask_arr[0].shape

print('[+] Running OCR...')
text_positions = run_ocr(IMAGE)
items = list(text_positions.keys())
print('    OCR texts:', items[:20])

start_name = '117호' if '117호' in items else (items[0] if len(items) > 0 else None)
goal_name = '104호' if '104호' in items else (items[1] if len(items) > 1 else None)
if start_name is None or goal_name is None:
    raise SystemExit('[!] Not enough OCR texts to pick start/goal')

start_pos = find_room(start_name, text_positions)
goal_pos = find_room(goal_name, text_positions)
if start_pos is None or goal_pos is None:
    raise SystemExit('[!] Could not resolve start/goal positions')

def scale_to_mask(p):
    x,y = p
    sx = int(x * (new_w / orig_w))
    sy = int(y * (new_h / orig_h))
    sx = max(0, min(new_w-1, sx))
    sy = max(0, min(new_h-1, sy))
    return (sx, sy)

start_scaled = scale_to_mask(start_pos)
goal_scaled = scale_to_mask(goal_pos)

# Build grid treating class 2 as wall
wall_mask = np.zeros((H, W), dtype=bool)
for seg_np, cls in zip(mask_arr, classes):
    if int(cls) == 2:
        wall_mask = np.logical_or(wall_mask, seg_np > 0.5)

grid = np.zeros((H, W), dtype=np.uint8)
grid[wall_mask] = 1

np.savetxt(os.path.join(OUT_DIR, 'grid_map.txt'), grid, fmt='%d')

path = bfs(grid, start_scaled, goal_scaled)
if path:
    print('[+] Path found, length =', len(path))
    with open(os.path.join(OUT_DIR, 'path.txt'), 'w', encoding='utf-8') as f:
        for x,y in path:
            f.write(f"{x},{y}\n")
else:
    print('[!] No path found (None)')

# Make overlay: draw wall mask and path on original image
img = cv2.imread(IMAGE)
overlay = img.copy()
wall_up = (wall_mask.astype('uint8') * 255)
wall_up = cv2.resize(wall_up, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
red = np.zeros_like(img)
red[:, :, 2] = wall_up
alpha = 0.5
overlay = cv2.addWeighted(overlay, 1.0, red, alpha, 0)

if path:
    pts = [(int(x * (orig_w / float(W))), int(y * (orig_h / float(H)))) for (x,y) in path]
    for p in pts:
        cv2.circle(overlay, p, 4, (255,255,0), -1)
    if len(pts) > 1:
        cv2.polylines(overlay, [np.array(pts, dtype=np.int32)], False, (255,255,0), 3)

out_png = os.path.join(OUT_DIR, 'class2_wall_overlay.png')
cv2.imwrite(out_png, overlay)
print('[+] Wrote overlay to', out_png)

summary = {
    'start': start_name,
    'goal': goal_name,
    'start_point': start_pos,
    'goal_point': goal_pos,
    'start_scaled': start_scaled,
    'goal_scaled': goal_scaled,
    'path_len': len(path) if path else None,
}
with open(os.path.join(OUT_DIR, 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print('[✔] Test complete. Outputs in', OUT_DIR)
