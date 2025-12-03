import cv2
import numpy as np
import os
import json
import argparse
from pathlib import Path

# import local a_star
import sys
sys.path.append(str(Path(__file__).parents[1] / 'aicane_ai_engine'))
from navigation.astar import a_star

try:
    import pytesseract
    HAS_TESSERACT = True
except Exception:
    pytesseract = None
    HAS_TESSERACT = False


def ensure_uploads():
    os.makedirs('uploads', exist_ok=True)


def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    denoised = cv2.medianBlur(gray, 3)
    # adaptive threshold inverted: walls/text become white
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 8)
    # morphological clean
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_large, iterations=1)
    walls = cv2.dilate(closed, np.ones((3, 3), np.uint8), iterations=1)
    return walls


def build_grid_from_walls(walls):
    # walls: binary 0/255
    wall_mask = (walls == 255).astype(np.uint8)
    grid = wall_mask.copy()
    # invert: grid=1 for wall, 0 for free
    grid = grid.astype(np.uint8)
    return grid


def find_text_candidates(img_gray):
    # simple threshold to find small blobs that may be text
    _, th = cv2.threshold(img_gray, 200, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    h, w = th.shape[:2]
    for c in cnts:
        x, y, cw, ch = cv2.boundingRect(c)
        if cw < 8 or ch < 8:
            continue
        if cw > w * 0.5 or ch > h * 0.5:
            continue
        candidates.append((x, y, cw, ch))
    return candidates


def ocr_candidates(img, candidates):
    results = []
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img_gray.shape[:2]
    debug = img.copy()
    for (x, y, cw, ch) in candidates:
        pad = 4
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(w, x + cw + pad)
        y1 = min(h, y + ch + pad)
        crop = img_gray[y0:y1, x0:x1]
        # scale small
        if max(cw, ch) < 40:
            crop = cv2.resize(crop, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        text = ''
        if HAS_TESSERACT:
            try:
                conf = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(crop, config=conf)
                text = text.strip()
            except Exception:
                text = ''
        results.append({'raw': text, 'bbox': [x0, y0, x1, y1], 'centroid': [(x0 + x1) // 2, (y0 + y1) // 2]})
        # draw
        color = (0, 255, 0) if text else (0, 0, 255)
        cv2.rectangle(debug, (x0, y0), (x1, y1), color, 1)
        if text:
            cv2.putText(debug, text, (x0, max(0, y0 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return results, debug


def overlay_path_on_image(img, path):
    # path: list of (row, col) tuples
    out = img.copy()
    if len(path) == 0:
        return out
    pts = [(c, r) for (r, c) in path]
    for i in range(len(pts) - 1):
        cv2.line(out, pts[i], pts[i + 1], (0, 0, 255), 2)
    for p in pts:
        cv2.circle(out, p, 2, (0, 255, 0), -1)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--image', required=True)
    p.add_argument('--start', default=None, help='start as "x,y" pixels')
    p.add_argument('--target', default=None, help='target room number string or "x,y"')
    args = p.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        print('image not found:', args.image)
        return

    ensure_uploads()
    walls = preprocess(img)
    cv2.imwrite('uploads/preprocessed.png', walls)

    grid = build_grid_from_walls(walls)
    np.save('uploads/grid.npy', grid)

    # OCR candidates
    candidates = find_text_candidates(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    ocr_results, debug_img = ocr_candidates(img, candidates)
    try:
        json.dump(ocr_results, open('uploads/ocr_debug.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    except Exception:
        pass
    cv2.imwrite('uploads/ocr_debug.png', debug_img)

    # build room_positions from OCR results (digits only)
    room_positions = {}
    for r in ocr_results:
        raw = r['raw']
        digits = ''.join([c for c in raw if c.isdigit()])
        if digits:
            room_positions[digits] = r['centroid']
    if room_positions:
        try:
            json.dump(room_positions, open('uploads/room_positions.json', 'w', encoding='utf-8'), indent=2)
        except Exception:
            pass
    else:
        print('No OCR-detected room labels. You can pass target as coordinates e.g. "200,80"')

    # determine start
    h, w = grid.shape
    if args.start:
        sx, sy = [int(x) for x in args.start.split(',')]
    else:
        # default: center bottom (approx front door)
        sx, sy = w // 2, int(h * 0.9)

    # determine target
    goal_xy = None
    if args.target:
        if ',' in args.target:
            gx, gy = [int(x) for x in args.target.split(',')]
            goal_xy = (gx, gy)
        else:
            if args.target in room_positions:
                goal_xy = tuple(room_positions[args.target])
            else:
                print('Target room not found in OCR results:', args.target)

    if goal_xy is None:
        print('No goal found, aborting path find')
        return

    # convert to grid (row,col) i.e., (y,x)
    start_yx = (int(sy), int(sx))
    goal_yx = (int(goal_xy[1]), int(goal_xy[0]))

    # ensure within bounds
    start_yx = (max(0, min(h - 1, start_yx[0])), max(0, min(w - 1, start_yx[1])))
    goal_yx = (max(0, min(h - 1, goal_yx[0])), max(0, min(w - 1, goal_yx[1])))

    path = a_star(grid, start_yx, goal_yx)
    print('path length', len(path))

    # overlay path on original image
    overlay = overlay_path_on_image(img, path)
    cv2.circle(overlay, (sx, sy), 6, (255, 0, 0), -1)
    cv2.circle(overlay, (int(goal_xy[0]), int(goal_xy[1])), 6, (0, 255, 255), -1)
    cv2.imwrite('uploads/path_overlay.png', overlay)
    print('Saved: uploads/preprocessed.png, uploads/grid.npy, uploads/ocr_debug.png, uploads/path_overlay.png')


if __name__ == '__main__':
    main()
