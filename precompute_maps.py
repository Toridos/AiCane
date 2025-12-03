import cv2
import numpy as np
import json

FLOORS = {
    1: ("static/s4_1-1.png", 101, 118),
    2: ("static/s4_1-2.png", 201, 223),
    3: ("static/s4_1-3.png", 301, 332),
}

from route_planner import extract_red_mask, extract_blue_mask, find_stair_centroids
from match_rooms import match_floor_rooms
import run_navigation as rn

for f, (imgpath, rstart, rend) in FLOORS.items():
    print(f"Processing Floor {f}")

    img = cv2.imread(imgpath)
    texts = rn.run_ocr(imgpath)
    cleaned = match_floor_rooms(texts, rstart, rend, max_dist=5)

    red_mask = extract_red_mask(img)
    grid = (red_mask > 0).astype(np.uint8)  # 1=wall, 0=free

    blue_mask = extract_blue_mask(img)
    stairs = find_stair_centroids(blue_mask)

    np.save(f"static/grid_f{f}.npy", grid)

    with open(f"static/cleaned_f{f}.json", "w") as f2:
        json.dump(cleaned, f2)

print("DONE precompute.")
