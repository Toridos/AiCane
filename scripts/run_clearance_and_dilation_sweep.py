import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path

# Ensure project root is on sys.path so we can import run_navigation when
# executing this script from the scripts/ directory.
proj_root = str(Path(__file__).resolve().parents[1])
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from run_navigation import run_seg, run_ocr, mask_to_grid, bfs, find_room, draw_overlay

# Configure image to test (same sample used previously)
IMAGE_PATH = r"C:\SW_3_2\ai\AI_lab\yolo_dataset\images\APT_FP_OCR_230087881.PNG"
OUT_DIR = "dilation_and_clearance_outputs"
os.makedirs(OUT_DIR, exist_ok=True)

print("[+] Running segmentation once...")
masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_seg(IMAGE_PATH)
print(f"    seg sizes: orig=({orig_w},{orig_h}) new=({new_w},{new_h})")

print("[+] Running OCR once...")
text_positions = run_ocr(IMAGE_PATH)
items = list(text_positions.keys())
if len(items) < 2:
    print("[!] Not enough OCR texts detected to pick start/goal automatically.")
    print("    Detected:", items)
    raise SystemExit(1)

start_name = items[0]
goal_name = items[1]
print(f"[+] Using start='{start_name}', goal='{goal_name}' (first two OCR detections)")

start_pos = find_room(start_name, text_positions)
goal_pos = find_room(goal_name, text_positions)
if start_pos is None or goal_pos is None:
    print("[!] Could not resolve start/goal positions via `find_room`")
    raise SystemExit(1)

# helper to scale original image coords -> mask coords
def scale_point(p):
    x, y = p
    sx = int(x * (new_w / orig_w))
    sy = int(y * (new_h / orig_h))
    sx = max(0, min(new_w-1, sx))
    sy = max(0, min(new_h-1, sy))
    return (sx, sy)

start_scaled = scale_point(start_pos)
goal_scaled = scale_point(goal_pos)

# experiments
dilations = [9, 11, 13, 17]
clearances = [5, 9, 13, 17]

summary = []

print("[+] Running dilation experiments...")
for r in dilations:
    grid = mask_to_grid(masks, boxes, wall_dilate=r, clearance_px=None)
    path = bfs(grid, start_scaled, goal_scaled)

    wall_cells = int(np.sum(grid == 1))
    path_len = len(path) if path else None

    # compute min distance from path to wall (in mask pixels)
    wall_uint = (grid == 1).astype('uint8') * 255
    inv = 255 - wall_uint
    dt = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    min_dist = None
    if path:
        dvals = [float(dt[pt[1], pt[0]]) for pt in path]
        min_dist = float(np.min(dvals))

    fname = os.path.join(OUT_DIR, f"dilate_{r}")
    np.savetxt(fname + "_grid.txt", grid, fmt="%d")
    if path:
        with open(fname + "_path.txt", "w") as f:
            for (x, y) in path:
                f.write(f"{x},{y}\n")

    result_full = {
        "start_point": start_pos,
        "goal_point": goal_pos,
        "start_scaled": start_scaled,
        "goal_scaled": goal_scaled,
        "path": path,
        "orig_size": (orig_w, orig_h),
        "new_size": (new_w, new_h)
    }
    with open(fname + ".json", "w", encoding="utf-8") as f:
        json.dump(result_full, f, ensure_ascii=False, indent=2)

    draw_overlay(IMAGE_PATH, text_positions, result_full, out_path=fname + ".png")

    summary.append({"mode": "dilate", "r": r, "wall_cells": wall_cells, "path_len": path_len, "min_dist_to_wall": min_dist})
    print(f"  - dilate={r}: wall_cells={wall_cells} path_len={path_len} min_dist={min_dist}")

print("[+] Running clearance (distance-transform) experiments...")
for c in clearances:
    grid = mask_to_grid(masks, boxes, wall_dilate=0, clearance_px=c)
    path = bfs(grid, start_scaled, goal_scaled)

    wall_cells = int(np.sum(grid == 1))
    path_len = len(path) if path else None

    wall_uint = (grid == 1).astype('uint8') * 255
    inv = 255 - wall_uint
    dt = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    min_dist = None
    if path:
        dvals = [float(dt[pt[1], pt[0]]) for pt in path]
        min_dist = float(np.min(dvals))

    fname = os.path.join(OUT_DIR, f"clearance_{c}")
    np.savetxt(fname + "_grid.txt", grid, fmt="%d")
    if path:
        with open(fname + "_path.txt", "w") as f:
            for (x, y) in path:
                f.write(f"{x},{y}\n")

    result_full = {
        "start_point": start_pos,
        "goal_point": goal_pos,
        "start_scaled": start_scaled,
        "goal_scaled": goal_scaled,
        "path": path,
        "orig_size": (orig_w, orig_h),
        "new_size": (new_w, new_h)
    }
    with open(fname + ".json", "w", encoding="utf-8") as f:
        json.dump(result_full, f, ensure_ascii=False, indent=2)

    draw_overlay(IMAGE_PATH, text_positions, result_full, out_path=fname + ".png")

    summary.append({"mode": "clearance", "clearance_px": c, "wall_cells": wall_cells, "path_len": path_len, "min_dist_to_wall": min_dist})
    print(f"  - clearance={c}: wall_cells={wall_cells} path_len={path_len} min_dist={min_dist}")

# write summary
with open(os.path.join(OUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("[✔] Experiments complete. Outputs in:", OUT_DIR)
print(json.dumps(summary, indent=2, ensure_ascii=False))
