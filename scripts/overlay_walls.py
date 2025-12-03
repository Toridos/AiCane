import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import run_navigation as rn
import cv2
import numpy as np

imgs = [
    r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-1.png",
    r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-2.png",
    r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-3.png",
]

outdir = Path("outputs/wall_overlays")
outdir.mkdir(parents=True, exist_ok=True)

for i,p in enumerate(imgs):
    print(f"Processing: {p}")
    masks, boxes, (orig_w, orig_h), (new_w, new_h) = rn.run_seg(p)
    red_mask = rn.extract_red_mask_from_image(p)
    # build grid preferring red-only to see user walls
    grid, room_mask = rn.grid_from_masks_and_optional_red(masks, boxes, red_mask=red_mask, wall_dilate=1, clearance_px=None, use_red_only=True)
    out_path = outdir / f"wall_overlay_floor_{i+1}.png"
    rn.draw_wall_overlay(p, grid, str(out_path))

print("Done. Overlays written to:")
for f in sorted(outdir.iterdir()):
    print(f)
