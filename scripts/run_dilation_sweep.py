import os
import sys
import json
import cv2
import numpy as np

# ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import run_navigation

IMAGE = r"C:\SW_3_2\ai\AI_lab\yolo_dataset\images\APT_FP_OCR_230087881.PNG"
RADII = [1, 3, 5, 7]
OUT_DIR = 'dilation_sweep_outputs'
os.makedirs(OUT_DIR, exist_ok=True)

print('Running OCR once...')
text_positions = run_navigation.run_ocr(IMAGE)
print('Detected texts:', list(text_positions.keys())[:10])
run_navigation.text_positions_global = text_positions

# select start/goal automatically
keys = [k for k in text_positions.keys() if k and len(k.strip())>0]
if len(keys) < 2:
    raise SystemExit('Not enough OCR texts detected to pick start/goal')
start_name = keys[0]
goal_name  = keys[1]
print('Auto-select start,goal ->', start_name, goal_name)

print('Running segmentation once...')
masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_navigation.run_seg(IMAGE)

for r in RADII:
    print('\n--- radius =', r, '---')
    # build grid with dilation r
    grid = run_navigation.mask_to_grid(masks, boxes, wall_dilate=r)
    grid_path = os.path.join(OUT_DIR, f'grid_map_dilate_{r}.txt')
    np.savetxt(grid_path, grid, fmt='%d')
    print('Saved', grid_path)

    # scale start/goal
    def scale_point(p):
        x,y = p
        sx = int(x * (new_w / orig_w))
        sy = int(y * (new_h / orig_h))
        sx = max(0, min(new_w-1, sx))
        sy = max(0, min(new_h-1, sy))
        return (sx, sy)

    start_pos = run_navigation.find_room(start_name, text_positions)
    goal_pos  = run_navigation.find_room(goal_name, text_positions)
    start_scaled = scale_point(start_pos)
    goal_scaled  = scale_point(goal_pos)

    # BFS
    path = run_navigation.bfs(grid, start_scaled, goal_scaled)

    # save path
    path_path = os.path.join(OUT_DIR, f'path_dilate_{r}.txt')
    if path:
        with open(path_path, 'w') as f:
            for x,y in path:
                f.write(f"{x},{y}\n")
    else:
        open(path_path, 'w').close()
    print('Saved', path_path, 'path length:', len(path) if path else 0)

    # result JSON
    result = {
        'start': start_name,
        'goal': goal_name,
        'start_point': start_pos,
        'goal_point': goal_pos,
        'start_scaled': start_scaled,
        'goal_scaled': goal_scaled,
        'path': path,
        'orig_size': (orig_w, orig_h),
        'new_size': (new_w, new_h),
        'dilate': r
    }
    json_path = os.path.join(OUT_DIR, f'result_dilate_{r}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('Saved', json_path)

    # Draw overlay (uses original image coordinates for start/goal)
    out_png = os.path.join(OUT_DIR, f'overlay_dilate_{r}.png')
    run_navigation.draw_overlay(IMAGE, text_positions, result, out_path=out_png)
    print('Saved', out_png)

print('\nSweep complete. Outputs in folder:', OUT_DIR)
