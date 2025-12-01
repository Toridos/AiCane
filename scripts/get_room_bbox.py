import argparse
import json
import sys
from pathlib import Path
import cv2
import numpy as np

# make repo root importable (so we can import scripts.red_bfs)
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
from scripts.red_bfs import extract_red_mask


def find_free_component_bbox(red_mask, cx, cy):
    # red_mask: 8-bit mask where walls>0
    h, w = red_mask.shape
    if not (0 <= cx < w and 0 <= cy < h):
        raise ValueError("centroid outside image")

    free = (red_mask == 0).astype('uint8') * 255

    num_labels, labels = cv2.connectedComponents(free)
    label = labels[cy, cx]
    if label == 0:
        return None

    comp_mask = (labels == label).astype('uint8') * 255
    cnts, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    x, y, w_box, h_box = cv2.boundingRect(c)
    return x, y, x + w_box, y + h_box, w_box, h_box, c


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--image', required=True)
    p.add_argument('--centroid', nargs=2, type=int, required=True)
    p.add_argument('--out', default='outputs/room_bbox.png')
    p.add_argument('--kernel', type=int, default=9, help='morphology kernel size for red mask')
    p.add_argument('--min-area', type=int, default=400, help='min contour area to keep in red mask')
    args = p.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        raise SystemExit(f"Image not found: {img_path}")

    img = cv2.imread(str(img_path))
    if img is None:
        raise SystemExit(f"Failed to load image: {img_path}")

    cx, cy = args.centroid

    red_mask = extract_red_mask(img, kernel_size=args.kernel, min_area=args.min_area)

    res = find_free_component_bbox(red_mask, cx, cy)
    if res is None:
        print("[!] No free component found at the given centroid")
        raise SystemExit(1)

    x0, y0, x1, y1, w_box, h_box, contour = res

    print(f"Centroid: ({cx},{cy})")
    print(f"BBox: x0={x0}, y0={y0}, x1={x1}, y1={y1}")
    print(f"Width: {w_box} px, Height: {h_box} px")

    # draw overlay
    vis = img.copy()
    cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 255, 0), 3)
    cv2.circle(vis, (cx, cy), 6, (255, 0, 0), -1)
    cv2.drawContours(vis, [contour], -1, (0, 0, 255), 2)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(outp), vis)
    print(f"Wrote overlay to {outp}")
