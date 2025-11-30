# precompute.py
import cv2, json, numpy as np
from route_core import compute_room_coords, extract_red_mask, extract_blue_mask, find_stairs

FLOORS = {
    1: ("static/s4_1-1.png", 101, 118),
    2: ("static/s4_1-2.png", 201, 223),
    3: ("static/s4_1-3.png", 301, 332)
}

for f,(imgpath,rstart,rend) in FLOORS.items():
    img=cv2.imread(imgpath)

    cleaned = compute_room_coords(imgpath, rstart, rend)
    red_mask = extract_red_mask(img)
    blue_mask = extract_blue_mask(img)
    stairs = find_stairs(blue_mask)

    np.save(f"static/grid_f{f}.npy", red_mask)
    with open(f"static/cleaned_f{f}.json","w") as fp:
        json.dump(cleaned, fp)
    with open(f"static/stairs_f{f}.json","w") as fp:
        json.dump(stairs, fp)

print("DONE.")
