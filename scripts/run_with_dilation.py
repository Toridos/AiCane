import json
import os
import sys
import cv2

# ensure repo root is on sys.path so we can import run_navigation
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import run_navigation

# image used by navigation
IMAGE = r"C:\SW_3_2\ai\AI_lab\yolo_dataset\images\APT_FP_OCR_230087881.PNG"
# choose dilation radius (in mask pixels)
DILATE = 3

print('Running OCR...')
text_positions = run_navigation.run_ocr(IMAGE)
print('Detected texts:', list(text_positions.keys())[:10])

# set global so get_path can use it
run_navigation.text_positions_global = text_positions

# choose first two detected unique texts as start/goal
keys = [k for k in text_positions.keys() if k and len(k.strip())>0]
if len(keys) < 2:
    raise SystemExit('Not enough OCR texts detected to pick start/goal')
start = keys[0]
goal = keys[1]
print('Auto-select start,goal ->', start, goal)

# call run_seg + get_path but patch mask_to_grid call to use dilation by temporarily wrapping
# We call get_path (it calls mask_to_grid without argument), so we monkeypatch mask_to_grid to pass dilation
orig_mask_to_grid = run_navigation.mask_to_grid

def mask_to_grid_with_dilate(masks, boxes):
    # call original implementation with dilation arg
    return orig_mask_to_grid(masks, boxes, wall_dilate=DILATE)

run_navigation.mask_to_grid = mask_to_grid_with_dilate

result = run_navigation.get_path(IMAGE, start, goal)

# restore
run_navigation.mask_to_grid = orig_mask_to_grid

# save result json
with open('result_dilated.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print('Saved result_dilated.json')

# draw overlay
run_navigation.draw_overlay(IMAGE, text_positions, result, out_path='overlay_dilated.png')
print('Overlay saved: overlay_dilated.png')

# show a quick cv2 window (optional, commented out)
# img = cv2.imread('overlay_dilated.png')
# cv2.imshow('overlay', img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
