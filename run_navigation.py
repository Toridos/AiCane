import os
from pathlib import Path
import glob
import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import easyocr
import json
import re
import argparse

###############################################################
# 0. MODEL PATH
###############################################################

SEG_MODEL_PATH = r"C:\SW_3_2\toridos\AiCane\runs\segment\train7\weights\best.pt"
OCR_MODEL_PATH = r"C:\SW_3_2\toridos\AiCane\runs\detect\train\weights\best.pt"


def resolve_model(path):
    if os.path.exists(path):
        return path
    found = glob.glob("**/best.pt", recursive=True)
    if found:
        print("[!] WARNING: model not found, fallback →", found[0])
        return found[0]
    raise FileNotFoundError(path)


seg_model = YOLO(resolve_model(SEG_MODEL_PATH))
ocr_model = YOLO(resolve_model(OCR_MODEL_PATH))
ocr_reader = easyocr.Reader(["ko", "en"])

# OCR configuration
OCR_CONF_THRESHOLD = 0.25  # accept detections with confidence >= this (EasyOCR returns 0..1)

TEXT_CLASS = 0
ROOM_CLASS = 2


###############################################################
# UTIL FUNCTIONS
###############################################################

def normalize_text(t):
    if t is None:
        return None
    t = t.strip()
    return re.sub(r"[^0-9a-zA-Z\uac00-\ud7a3]+", "", t)


def levenshtein(a, b):
    a, b = a.lower(), b.lower()
    dp = [[0] * (len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)+1): dp[i][0] = i
    for j in range(len(b)+1): dp[0][j] = j

    for i in range(1,len(a)+1):
        for j in range(1,len(b)+1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j]+1,
                dp[i][j-1]+1,
                dp[i-1][j-1] + cost
            )
    return dp[len(a)][len(b)]


###############################################################
# 1. Segmentation
###############################################################

def run_seg(image_path):
    res = seg_model(image_path)[0]

    masks = res.masks
    boxes = res.boxes

    if masks is None:
        raise ValueError("No segmentation masks")

    try:
        orig_h, orig_w = masks.orig_shape
    except:
        img = cv2.imread(image_path)
        orig_h, orig_w = img.shape[:2]

    new_h, new_w = masks.data[0].shape

    return masks, boxes, (orig_w, orig_h), (new_w, new_h)


###############################################################
# 2. OCR (YOLO → EasyOCR)
###############################################################

def run_ocr(image_path):
    img = cv2.imread(image_path)
    res = ocr_model(image_path)[0]

    H, W = img.shape[:2]
    text_positions = {}

    os.makedirs("debug_ocr_boxes", exist_ok=True)

    for i, (xyxy, cls) in enumerate(zip(res.boxes.xyxy, res.boxes.cls)):
        # Some detection models may use a different class index for text.
        # To be robust, attempt OCR on detected boxes regardless of class,
        # but skip very large boxes that likely correspond to full rooms.
        x1,y1,x2,y2 = xyxy.cpu().numpy().astype(int)
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, W-1), min(y2, H-1)

        crop = img[y1:y2, x1:x2]

        # skip empty crops
        if crop.size == 0:
            continue

        # skip huge crops (likely not text)
        crop_area = (x2 - x1) * (y2 - y1)
        img_area = H * W
        if img_area > 0 and (crop_area / float(img_area)) > 0.5:
            # very large box; skip OCR attempt
            continue

        cv2.imwrite(f"debug_ocr_boxes/box_{i}.png", crop)

        ocr_out = ocr_reader.readtext(crop)

        for det in ocr_out:
            # det = (box, text, confidence)
            try:
                conf = det[2] if len(det) > 2 else 1.0
                if conf < OCR_CONF_THRESHOLD:
                    continue
            except Exception:
                conf = 1.0

            raw = det[1]
            norm = normalize_text(raw)

            # EasyOCR returns det[0] as list of 4 points [[x,y],...]
            # these coords are relative to the crop; convert to image coords
            try:
                pts = det[0]
                xs = [int(p[0]) for p in pts]
                ys = [int(p[1]) for p in pts]
                cx_crop = sum(xs) / len(xs)
                cy_crop = sum(ys) / len(ys)
                cx = int(x1 + cx_crop)
                cy = int(y1 + cy_crop)
            except Exception:
                # fallback to YOLO box center
                cx, cy = (x1 + x2)//2, (y1 + y2)//2

            if raw:
                text_positions[raw] = (cx, cy)
            if norm and norm != raw:
                text_positions[norm] = (cx, cy)

    # --- Fallback / multi-scale full-image OCR to improve recall ---
    try:
        # include a larger upscale to capture small fonts
        scales = [1.0, 1.5, 2.0, 3.0]
        for s in scales:
            if s == 1.0:
                img_s = img
                Hs, Ws = H, W
            else:
                Ws, Hs = int(W * s), int(H * s)
                img_s = cv2.resize(img, (Ws, Hs), interpolation=cv2.INTER_LINEAR)

            # run OCR on multiple preprocessed variants to increase recall
            variants = [img_s]
            try:
                gray = cv2.cvtColor(img_s, cv2.COLOR_BGR2GRAY)
                th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
                variants.append(th)
                variants.append(255 - th)
            except Exception:
                pass

            for var in variants:
                ocr_full = ocr_reader.readtext(var)
                for det in ocr_full:
                    try:
                        conf = det[2] if len(det) > 2 else 1.0
                        if conf < OCR_CONF_THRESHOLD:
                            continue
                    except Exception:
                        conf = 1.0

                    raw = det[1]
                    if not raw:
                        continue
                    pts = det[0]
                    xs = [float(p[0]) for p in pts]
                    ys = [float(p[1]) for p in pts]
                    cx_crop = sum(xs) / len(xs)
                    cy_crop = sum(ys) / len(ys)
                    # scale back to original image coordinates
                    cx = int(cx_crop / s)
                    cy = int(cy_crop / s)
                    norm = normalize_text(raw)

                    # merge: avoid duplicates by checking exact or normalized matches
                    duplicate = False
                    for existing in list(text_positions.keys()):
                        try:
                            if existing == raw or normalize_text(existing) == norm:
                                duplicate = True
                                break
                            if levenshtein(normalize_text(existing), norm) <= 1:
                                duplicate = True
                                break
                        except Exception:
                            continue

                    if not duplicate:
                        text_positions[raw] = (cx, cy)
                        if norm and norm != raw:
                            text_positions[norm] = (cx, cy)
    except Exception as e:
        print("[!] OCR fallback error:", e)

    return text_positions


###############################################################
# 3. Print OCR Texts & User Input
###############################################################

def list_texts(text_positions):
    items = []
    seen = set()
    for t,pos in text_positions.items():
        if t not in seen:
            items.append((t,pos))
            seen.add(t)

    print("\n📌 Detected OCR Texts:")
    for i,(t,pos) in enumerate(items):
        print(f"[{i}] '{t}' @ {pos}")

    return items


def ask(prompt, items):
    while True:
        user = input(prompt).strip()

        if user.isdigit():
            idx = int(user)
            if 0 <= idx < len(items):
                return items[idx][0]

        for t,_ in items:
            if user == t:
                return t

        print("❌ Invalid, try again.")


###############################################################
# 4. MASK → GRID (fix)
###############################################################

def mask_to_grid(masks, boxes, wall_dilate=3, clearance_px=None):
    """Convert segmentation masks to a binary grid for pathfinding.

    Parameters:
    - masks, boxes: outputs from ultralytics YOLO segmentation
    - wall_dilate: integer radius (in mask pixels) to dilate wall predictions
      to create a safety margin (0 = no dilation).
    - clearance_px: if provided, additionally block any grid cell that is
      within `clearance_px` pixels of a wall (distance-transform based).
    """
    mask_arr = masks.data.cpu().numpy()
    classes = boxes.cls.cpu().numpy().astype(int)

    H, W = mask_arr[0].shape
    grid = np.zeros((H, W), dtype=np.uint8)

    # Combine all wall masks into a single mask
    wall_mask = np.zeros((H, W), dtype=bool)
    for seg_np, cls in zip(mask_arr, classes):
        if int(cls) == 0:  # wall
            wall_mask = np.logical_or(wall_mask, seg_np > 0.5)

    # Apply dilation to wall mask to create a safety margin
    if wall_dilate and wall_mask.any():
        # cv2 dilation requires uint8
        wall_uint = (wall_mask.astype('uint8') * 255)
        ksize = max(1, 2 * int(wall_dilate) + 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        wall_dilated = cv2.dilate(wall_uint, kernel)
        wall_mask = wall_dilated > 0

    # Apply distance-transform based clearance: block any pixel whose
    # distance to the nearest wall is less than `clearance_px` (in mask pixels).
    if clearance_px and wall_mask.any():
        # distanceTransform computes distance to the nearest zero pixel,
        # so invert the wall mask to make walls zeros and background non-zero.
        wall_uint2 = (wall_mask.astype('uint8') * 255)
        inv = 255 - wall_uint2
        # compute Euclidean distance (float32)
        dt = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
        close_mask = dt < float(clearance_px)
        wall_mask = np.logical_or(wall_mask, close_mask)

    grid[wall_mask] = 1

    # Note: Other classes (room, door) remain 0 = traversable
    return grid


###############################################################
# 6. Overlay: draw OCR texts + path on original image
###############################################################

def draw_overlay(image_path, text_positions, result, out_path="overlay_with_path.png"):
    """Draw detected OCR texts and the path (converted back to original image coords) on the image."""
    img = cv2.imread(image_path)
    if img is None:
        print(f"[!] Cannot open image: {image_path}")
        return

    orig_h, orig_w = img.shape[:2]
    orig_size = result.get("orig_size", (orig_w, orig_h))
    new_size = result.get("new_size", (orig_w, orig_h))
    orig_w2, orig_h2 = int(orig_size[0]), int(orig_size[1])
    new_w, new_h = int(new_size[0]), int(new_size[1])

    # Draw OCR texts
    for t, pos in text_positions.items():
        try:
            x = int(pos[0]); y = int(pos[1])
        except Exception:
            continue
        cv2.circle(img, (x, y), 6, (0, 255, 0), -1)
        cv2.putText(img, str(t), (x + 8, y + 8), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)

    # Draw path (result['path'] is in grid coords -> scale back to original)
    path = result.get("path")
    if path:
        pts = []
        for (gx, gy) in path:
            try:
                gx_i = int(gx); gy_i = int(gy)
            except Exception:
                continue
            x_orig = int(gx_i * (orig_w2 / new_w)) if new_w else gx_i
            y_orig = int(gy_i * (orig_h2 / new_h)) if new_h else gy_i
            pts.append((x_orig, y_orig))

        if len(pts) > 0:
            for p in pts:
                cv2.circle(img, p, 3, (255, 0, 0), -1)
            cv2.polylines(img, [np.array(pts, dtype=np.int32)], False, (255, 0, 0), 2)

    # Draw start/goal markers (original coords)
    sp = result.get("start_point")
    gp = result.get("goal_point")
    if sp:
        try:
            cv2.circle(img, (int(sp[0]), int(sp[1])), 12, (0, 255, 255), -1)
        except Exception:
            pass
    if gp:
        try:
            cv2.circle(img, (int(gp[0]), int(gp[1])), 12, (0, 0, 255), -1)
        except Exception:
            pass

    cv2.imwrite(out_path, img)
    print(f"[✔] Overlay saved → {out_path}")


def draw_debug_overlay(floors, floor_index, start_scaled, goal_scaled, portals, out_path):
    """Draw debug overlays showing grid, room mask contour, stairs, portals, snapped points.
    `floors` is the list of floor dicts; `floor_index` selects which floor to render."""
    floor = floors[floor_index]
    img = cv2.imread(floor['path'])
    if img is None:
        return
    orig_w, orig_h = floor['orig_size']
    new_w, new_h = floor['new_size']

    def to_orig(pt):
        x,y = pt
        ox = int(x * (orig_w / new_w))
        oy = int(y * (orig_h / new_h))
        return (ox, oy)

    # room mask contour
    try:
        rm = floor.get('room_mask')
        if rm is not None and rm.any():
            m_uint = (rm.astype('uint8') * 255)
            cnts, _ = cv2.findContours(m_uint, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts:
                pts = np.array([to_orig((int(p[0][0]), int(p[0][1]))) for p in c.reshape(-1,1,2)])
                if pts.size:
                    cv2.polylines(img, [pts], True, (0,255,255), 2)
    except Exception:
        pass

    # draw stairs on this floor
    try:
        for s in floor.get('stairs', []):
            cv2.circle(img, to_orig(s), 6, (0,0,255), -1)
    except Exception:
        pass

    # draw portals originating from this floor
    try:
        for (fidx, si), dests in portals.items():
            if fidx != floor_index:
                continue
            # origin coordinate (snapped stair)
            try:
                ox, oy = floors[fidx]['stairs'][si]
                o_pt = to_orig((ox, oy))
                cv2.circle(img, o_pt, 8, (255,0,255), -1)
            except Exception:
                o_pt = None
            for (nf, px, py) in dests:
                if o_pt is not None and nf < len(floors):
                    # draw a line to the destination's projected point on this image only if nf == fidx
                    if nf == fidx:
                        d_pt = to_orig((px, py))
                        cv2.line(img, o_pt, d_pt, (0,255,0), 2)
                    else:
                        # mark destination location if it belongs to this floor
                        if nf == floor_index:
                            d_pt = to_orig((px, py))
                            cv2.circle(img, d_pt, 6, (0,255,0), -1)
    except Exception:
        pass

    # draw start/goal
    try:
        if start_scaled and floor_index == 0:
            cv2.circle(img, to_orig(start_scaled), 12, (0,255,0), -1)
        if goal_scaled and floor_index == len(floors)-1:
            cv2.circle(img, to_orig(goal_scaled), 12, (255,0,0), -1)
    except Exception:
        pass

    cv2.imwrite(out_path, img)
    print(f"[debug] Debug overlay saved → {out_path}")


def draw_wall_overlay(image_path, grid, out_path):
    """Overlay detected wall cells (grid==1) on top of the original image as semi-transparent green."""
    img = cv2.imread(image_path)
    if img is None:
        print(f"[!] Cannot open image for wall overlay: {image_path}")
        return
    H_img, W_img = img.shape[:2]
    Hg, Wg = grid.shape
    # resize grid to image size if needed
    if (Hg, Wg) != (H_img, W_img):
        grid_resized = cv2.resize((grid.astype('uint8') * 255), (W_img, H_img), interpolation=cv2.INTER_NEAREST)
        wall_mask = grid_resized > 0
    else:
        wall_mask = grid == 1

    overlay = img.copy()
    # paint walls green (BGR=(0,255,0)) where mask is true
    overlay[wall_mask] = (0, 255, 0)

    alpha = 0.6
    blended = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    cv2.imwrite(out_path, blended)
    print(f"[✔] Wall overlay saved → {out_path}")


###############################################################
# 5. BFS
###############################################################

def bfs(grid, start, goal):
    H, W = grid.shape
    visited = np.zeros_like(grid, dtype=np.uint8)
    q = deque()
    q.append((start, [start]))
    visited[start[1]][start[0]] = 1

    dirs = [(1,0),(-1,0),(0,1),(0,-1)]

    while q:
        (x,y), path = q.popleft()

        if (x,y) == goal:
            return path

        for dx,dy in dirs:
            nx, ny = x+dx, y+dy
            if 0 <= nx < W and 0 <= ny < H:
                # treat non-wall cells (grid != 1) as traversable
                if visited[ny][nx]==0 and grid[ny][nx] != 1:
                    visited[ny][nx] = 1
                    q.append(((nx,ny), path+[(nx,ny)]))

    return None


###############################################################
# 6. Room Matching
###############################################################

def find_room(target, text_positions):
    target_norm = normalize_text(target)
    candidates = []

    for t,pos in text_positions.items():
        t_norm = normalize_text(t)

        if t == target or t_norm == target_norm:
            return pos

        if target_norm in t_norm:
            return pos

        dist = levenshtein(t_norm, target_norm)
        if dist <= 2:
            candidates.append((dist, pos))

    if candidates:
        candidates.sort()
        return candidates[0][1]

    return None


###############################################################
# 8. OCR -> expected room matching
###############################################################
def _extract_digits(tok):
    import re
    if tok is None:
        return None
    m = re.search(r"(\d{2,4})", str(tok))
    if m:
        return m.group(1)
    return None


def match_ocr_to_expected(text_positions, expected_start, expected_end, max_dist=2):
    """Match OCR-detected tokens to an expected numeric range using Levenshtein distance.

    Returns a dict mapping expected_number (int) -> (token, pos, dist) for matched tokens,
    and a list of missing expected_numbers.
    """
    # prepare expected labels as strings
    expected = [str(n) for n in range(expected_start, expected_end + 1)]

    # prepare detected tokens with normalized form (digits if present else normalized text)
    detected = []  # list of (tok, pos, norm)
    for tok, pos in text_positions.items():
        digits = _extract_digits(tok)
        if digits:
            norm = digits
        else:
            norm = normalize_text(tok) or tok
        detected.append((tok, pos, str(norm)))

    used = set()
    mapping = {}

    # For each expected, find best matching detected token by Levenshtein distance
    for exp in expected:
        best = None
        best_d = None
        best_idx = None
        for i, (tok, pos, norm) in enumerate(detected):
            if i in used:
                continue
            try:
                d = levenshtein(str(exp), str(norm))
            except Exception:
                # fallback to simple equality distance
                d = 0 if str(exp) == str(norm) else max(len(exp), len(norm))
            if best_d is None or d < best_d:
                best_d = d
                best = (tok, pos, norm)
                best_idx = i

        # Accept match if within threshold or exact numeric substring
        accept = False
        if best is not None:
            tok, pos, norm = best
            if best_d <= max_dist:
                accept = True
            else:
                # allow match if norm contains expected as substring (e.g., '205' in '2053')
                if str(exp) in str(norm):
                    accept = True

        if accept:
            mapping[int(exp)] = (best[0], best[1], int(best_d))
            used.add(best_idx)

    missing = [int(e) for e in expected if int(e) not in mapping]
    return mapping, missing


###############################################################
# 7. FINAL PATH CONTROLLER
###############################################################

def get_path(image_path, start_name, goal_name, wall_dilate=0, clearance_px=None):

    masks, boxes, (orig_w,orig_h), (new_w,new_h) = run_seg(image_path)

    grid = mask_to_grid(masks, boxes, wall_dilate=wall_dilate, clearance_px=clearance_px)

    # grid 저장
    np.savetxt("grid_map.txt", grid, fmt="%d")

    start_pos = find_room(start_name, text_positions_global)
    goal_pos  = find_room(goal_name, text_positions_global)

    if start_pos is None:
        raise ValueError("START text not found")

    if goal_pos is None:
        raise ValueError("GOAL text not found")

    # OCR → segmentation 좌표로 스케일
    def scale(p):
        x,y = p
        sx = int(x * (new_w / orig_w))
        sy = int(y * (new_h / orig_h))
        sx = max(0, min(new_w-1, sx))
        sy = max(0, min(new_h-1, sy))
        return (sx,sy)

    start_scaled = scale(start_pos)
    goal_scaled  = scale(goal_pos)

    path = bfs(grid, start_scaled, goal_scaled)

    # path 저장
    if path:
        with open("path.txt", "w") as f:
            for (x,y) in path:
                f.write(f"{x},{y}\n")

    return {
        "start": start_name,
        "goal": goal_name,
        "start_point": start_pos,
        "goal_point": goal_pos,
        "start_scaled": start_scaled,
        "goal_scaled": goal_scaled,
        "path": path,
        "orig_size": (orig_w, orig_h),
        "new_size": (new_w, new_h)
    }


###############################################################
# Multi-floor support
###############################################################


def extract_red_mask_from_image(image_path, kernel_size=25, min_area=100):
    img = cv2.imread(image_path)
    if img is None:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Wider HSV ranges to robustly capture user-drawn red (handles anti-aliasing, brush variation)
    lower1 = np.array([0, 50, 20])
    upper1 = np.array([25, 255, 255])
    lower2 = np.array([150, 50, 20])
    upper2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)
    # stronger closing + dilation with larger kernel to fill gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)
    # remove small components
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(out, [c], -1, 255, -1)
    return out


def grid_from_masks_and_optional_red(masks, boxes, red_mask=None, wall_dilate=3, clearance_px=None, use_red_only=False):
    # create wall mask from segmentation (class 0) if present
    mask_arr = masks.data.cpu().numpy()
    classes = boxes.cls.cpu().numpy().astype(int)
    H, W = mask_arr[0].shape
    wall_mask = np.zeros((H, W), dtype=bool)
    for seg_np, cls in zip(mask_arr, classes):
        if int(cls) == 0:
            wall_mask = np.logical_or(wall_mask, seg_np > 0.5)

    # If red_mask provided, either replace segmentation walls or merge depending on `use_red_only`.
    if red_mask is not None:
        rm = red_mask.astype('uint8')
        if rm.shape != wall_mask.shape:
            rm_resized = cv2.resize(rm, (W, H), interpolation=cv2.INTER_NEAREST)
        else:
            rm_resized = rm
        wall_from_red = rm_resized > 0
        if use_red_only:
            wall_mask = wall_from_red
        else:
            wall_mask = np.logical_or(wall_mask, wall_from_red)

    # Apply dilation
    if wall_dilate and wall_mask.any():
        wall_uint = (wall_mask.astype('uint8') * 255)
        ksize = max(1, 2 * int(wall_dilate) + 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        wall_dilated = cv2.dilate(wall_uint, kernel)
        wall_mask = wall_dilated > 0

    # clearance
    if clearance_px and wall_mask.any():
        wall_uint2 = (wall_mask.astype('uint8') * 255)
        inv = 255 - wall_uint2
        dt = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
        close_mask = dt < float(clearance_px)
        wall_mask = np.logical_or(wall_mask, close_mask)

    grid = np.zeros((H, W), dtype=np.uint8)
    grid[wall_mask] = 1

    # also produce a room mask (class == ROOM_CLASS if available)
    room_mask = np.zeros((H, W), dtype=bool)
    try:
        for seg_np, cls in zip(mask_arr, classes):
            if int(cls) == ROOM_CLASS:
                room_mask = np.logical_or(room_mask, seg_np > 0.5)
    except Exception:
        pass

    # mark stair pixels as 2 if segmentation provides them (class == 3)
    try:
        for seg_np, cls in zip(mask_arr, classes):
            if int(cls) == 3:
                stair_pixels = seg_np > 0.5
                grid[stair_pixels] = 2
    except Exception:
        pass

    return grid, room_mask


def stair_centroids_from_segmentation(masks, boxes, orig_size=None, new_size=None):
    # returns list of centroids in the segmentation mask coordinate system (new_size)
    mask_arr = masks.data.cpu().numpy()
    classes = boxes.cls.cpu().numpy().astype(int)
    H, W = mask_arr[0].shape
    centroids = []
    for seg_np, cls in zip(mask_arr, classes):
        if int(cls) == 3:  # stair class index
            m = (seg_np > 0.5).astype('uint8') * 255
            cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts:
                M = cv2.moments(c)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    centroids.append((cx, cy))
    return centroids


def match_stairs_between_floors(stairs_a, stairs_b, max_dist=50):
    # match each stair in A to nearest in B within max_dist
    pairs = []
    used_b = set()
    for i, pa in enumerate(stairs_a):
        best_j = None
        best_d = None
        for j, pb in enumerate(stairs_b):
            if j in used_b:
                continue
            d = (pa[0]-pb[0])**2 + (pa[1]-pb[1])**2
            if best_d is None or d < best_d:
                best_d = d
                best_j = j
        if best_j is not None and best_d <= max_dist*max_dist:
            pairs.append((i, best_j))
            used_b.add(best_j)
    return pairs


def nearest_free_cell(grid, x, y, max_radius=15):
    """Find nearest free cell (grid value 0) to (x,y) within max_radius. Returns (nx,ny) or None."""
    H, W = grid.shape
    from collections import deque
    visited = set()
    q = deque()
    sx, sy = int(x), int(y)
    # treat any cell that is not wall (value != 1) as traversable
    if 0 <= sx < W and 0 <= sy < H and grid[sy][sx] != 1:
        return (sx, sy)
    q.append((sx, sy, 0))
    visited.add((sx, sy))
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    while q:
        cx, cy, d = q.popleft()
        if d >= max_radius:
            continue
        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in visited:
                if grid[ny][nx] != 1:
                    return (nx, ny)
                visited.add((nx, ny))
                q.append((nx, ny, d+1))
    return None


def extract_blue_boxes_from_image(image_path, kernel_size=7, min_area=200):
    img = cv2.imread(image_path)
    if img is None:
        return []
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # blue-ish range (tune if needed)
    lower = np.array([100, 120, 50])
    upper = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    # close + dilate to get solid boxes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        x,y,w,h = cv2.boundingRect(c)
        # accept rectangles roughly (w/h near 1 or elongated)
        boxes.append((x, y, w, h))
    return boxes


def nearest_free_to_mask(grid, mask, max_radius=60):
    """Find a free cell (grid != 1) that is adjacent/nearest to the perimeter of `mask`.
    Returns (x,y) or None."""
    if mask is None or not mask.any():
        return None
    # find contours of the mask
    m_uint = (mask.astype('uint8') * 255)
    cnts, _ = cv2.findContours(m_uint, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # try each contour point and search outward for a free cell
    for c in cnts:
        for p in c.reshape(-1, 2):
            px, py = int(p[0]), int(p[1])
            res = nearest_free_cell(grid, px, py, max_radius=max_radius)
            if res:
                return res
    return None


def multi_floor_path(image_paths, use_red=False, use_blue=False, use_red_only=False, wall_dilate=3, clearance_px=None, stair_match_dist=80):
    floors = []
    all_texts = []
    for p in image_paths:
        masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_seg(p)
        red_mask = None
        if use_red:
            # try to locate a red-thickened image sibling or extract red from the same image
            red_mask = extract_red_mask_from_image(p)
        grid, room_mask = grid_from_masks_and_optional_red(masks, boxes, red_mask=red_mask, wall_dilate=wall_dilate, clearance_px=clearance_px, use_red_only=use_red_only)
        texts = run_ocr(p)
        # stairs: either from blue boxes (user-drawn) or from segmentation class index
        stairs = []
        if use_blue:
            blue_boxes = extract_blue_boxes_from_image(p)
            # convert blue box centers from orig coords to mask coords
            for (bx, by, bw, bh) in blue_boxes:
                cx = bx + bw/2.0
                cy = by + bh/2.0
                sx = int(cx * (new_w / orig_w))
                sy = int(cy * (new_h / orig_h))
                stairs.append((sx, sy))
        if not stairs:
            stairs = stair_centroids_from_segmentation(masks, boxes, orig_size=(orig_w, orig_h), new_size=(new_w, new_h))
        floors.append({
            'path': p,
            'grid': grid,
            'room_mask': room_mask,
            'texts': texts,
            'stairs': stairs,
            'orig_size': (orig_w, orig_h),
            'new_size': (new_w, new_h)
        })
        all_texts.append(texts)
        # debug
        blocked = int(np.sum(grid == 1))
        stairpix = int(np.sum(grid == 2))
        print(f"[debug] Loaded floor {p}: grid {grid.shape}, blocked={blocked}, stairpix={stairpix}, stairs_detected={len(stairs)}, texts={len(texts)}")

    # build portals between consecutive floors
    portals = {}  # map (floor_idx, stair_idx) -> list of (floor_idx2, x,y)
    for i in range(len(floors)-1):
        a = floors[i]['stairs']
        b = floors[i+1]['stairs']
        pairs = match_stairs_between_floors(a, b, max_dist=stair_match_dist)
        for ia, ib in pairs:
            pa = a[ia]; pb = b[ib]
            # snap portal endpoints to nearest free cell on each floor
            pa_snapped = nearest_free_cell(floors[i]['grid'], pa[0], pa[1], max_radius=30)
            pb_snapped = nearest_free_cell(floors[i+1]['grid'], pb[0], pb[1], max_radius=30)
            if pa_snapped and pb_snapped:
                portals.setdefault((i, ia), []).append((i+1, pb_snapped[0], pb_snapped[1]))
                portals.setdefault((i+1, ib), []).append((i, pa_snapped[0], pa_snapped[1]))
                # update stair lists so BFS proximity checks use snapped coordinates
                try:
                    floors[i]['stairs'][ia] = (pa_snapped[0], pa_snapped[1])
                except Exception:
                    pass
                try:
                    floors[i+1]['stairs'][ib] = (pb_snapped[0], pb_snapped[1])
                except Exception:
                    pass
                # ensure a small opening exists around portal endpoints (carve) to aid connectivity
                try:
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            x1 = pa_snapped[0] + dx; y1 = pa_snapped[1] + dy
                            if 0 <= x1 < floors[i]['grid'].shape[1] and 0 <= y1 < floors[i]['grid'].shape[0]:
                                if floors[i]['grid'][y1][x1] == 1:
                                    floors[i]['grid'][y1][x1] = 0
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            x2 = pb_snapped[0] + dx; y2 = pb_snapped[1] + dy
                            if 0 <= x2 < floors[i+1]['grid'].shape[1] and 0 <= y2 < floors[i+1]['grid'].shape[0]:
                                if floors[i+1]['grid'][y2][x2] == 1:
                                    floors[i+1]['grid'][y2][x2] = 0
                    print(f"[debug] Carved small opening around portals {(i,ia)} <-> {(i+1,ib)}")
                except Exception:
                    pass
            else:
                # fallback to raw coords if snapping failed
                portals.setdefault((i, ia), []).append((i+1, pb[0], pb[1]))
                portals.setdefault((i+1, ib), []).append((i, pa[0], pa[1]))
    print(f"[debug] Portals built: {len(portals)} entries")
    # show a compact portal summary
    for k,v in list(portals.items())[:20]:
        print(f"[debug] portal {k} -> {v}")
    # print stair lists per floor
    for fi, floor in enumerate(floors):
        print(f"[debug] floor {fi} stairs (count={len(floor['stairs'])}): {floor['stairs']}")

    # choose start on first floor and goal on last floor (numeric heuristics)
    def pick_text_on_floor(texts):
        # choose leftmost numeric if possible
        items = []
        for t,pos in texts.items():
            if any(ch.isdigit() for ch in t):
                items.append((t,pos))
        if items:
            items.sort(key=lambda it: it[1][0])
            return items[0][0]
        # fallback to any
        items2 = list(texts.items())
        if items2:
            items2.sort(key=lambda it: it[1][0])
            return items2[0][0]
        return None

    start_text = pick_text_on_floor(floors[0]['texts'])
    goal_text = pick_text_on_floor(floors[-1]['texts'])
    if start_text is None or goal_text is None:
        print("[!] Could not pick start/goal texts across floors")
        return None

    print(f"Start text: {start_text}  Goal text: {goal_text}")

    # find positions
    start_pos = find_room(start_text, floors[0]['texts'])
    goal_pos = find_room(goal_text, floors[-1]['texts'])
    if start_pos is None or goal_pos is None:
        print("[!] Could not resolve start/goal positions")
        return None

    # scale positions to each floor grid coords
    def scale_pos(p, floor):
        x,y = p
        orig_w, orig_h = floor['orig_size']
        new_w, new_h = floor['new_size']
        sx = int(x * (new_w / orig_w)); sy = int(y * (new_h / orig_h))
        sx = max(0, min(new_w-1, sx)); sy = max(0, min(new_h-1, sy))
        return (sx, sy)

    start_scaled = scale_pos(start_pos, floors[0])
    goal_scaled = scale_pos(goal_pos, floors[-1])

    # ensure start/goal are on free cells (snap if needed)
    s_snapped = nearest_free_cell(floors[0]['grid'], start_scaled[0], start_scaled[1], max_radius=30)
    if s_snapped:
        start_scaled = s_snapped
    # For goal, prefer the nearest free cell that lies just outside the detected room mask
    room_mask_last = floors[-1].get('room_mask')
    goal_outside = None
    try:
        if room_mask_last is not None and room_mask_last.any():
            # label connected components and pick the component containing the goal center
            lm = (room_mask_last.astype('uint8') * 255)
            num, labels = cv2.connectedComponents(lm)
            gx, gy = int(goal_scaled[0]), int(goal_scaled[1])
            comp_label = 0
            if 0 <= gy < labels.shape[0] and 0 <= gx < labels.shape[1]:
                comp_label = int(labels[gy, gx])
            if comp_label > 0:
                comp_mask = (labels == comp_label)
                goal_outside = nearest_free_to_mask(floors[-1]['grid'], comp_mask, max_radius=60)
    except Exception:
        goal_outside = None

    if goal_outside:
        goal_scaled = goal_outside
    else:
        g_snapped = nearest_free_cell(floors[-1]['grid'], goal_scaled[0], goal_scaled[1], max_radius=30)
        if g_snapped:
            goal_scaled = g_snapped
    print(f"[debug] start_scaled={start_scaled}  goal_scaled={goal_scaled}  goal_outside_found={bool(goal_outside)}")
    # debug grid values at start/goal
    try:
        sv = floors[0]['grid'][start_scaled[1]][start_scaled[0]]
    except Exception:
        sv = None
    try:
        gv = floors[-1]['grid'][goal_scaled[1]][goal_scaled[0]]
    except Exception:
        gv = None
    print(f"[debug] start grid value={sv}  goal grid value={gv}")

    # 3D BFS across floors
    from collections import deque as _dq
    visited = set()
    q = _dq()
    q.append((0, start_scaled[0], start_scaled[1], [(0, start_scaled[0], start_scaled[1])]))
    visited.add((0, start_scaled[0], start_scaled[1]))

    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    found_path = None
    while q:
        f,x,y,path = q.popleft()
        if f == len(floors)-1 and (x,y) == goal_scaled:
            found_path = path
            break
        # neighbors in same floor (treat grid != 1 as traversable)
        H,W = floors[f]['grid'].shape
        for dx,dy in dirs:
            nx, ny = x+dx, y+dy
            if 0 <= nx < W and 0 <= ny < H:
                if floors[f]['grid'][ny][nx] != 1 and (f,nx,ny) not in visited:
                    visited.add((f,nx,ny))
                    q.append((f,nx,ny, path+[(f,nx,ny)]))
        # portals from nearby stair pixels: if current cell equals a stair centroid approximate
        # check for stairs on this floor and see if any portal connects
        for si, (sx, sy) in enumerate(floors[f]['stairs']):
            # allow larger proximity to trigger portal transfer
            if abs(sx - x) <= 6 and abs(sy - y) <= 6:
                key = (f, si)
                if key in portals:
                    for (nf, px, py) in portals[key]:
                        nx, ny = int(px), int(py)
                        if (nf, nx, ny) not in visited and floors[nf]['grid'][ny][nx] != 1:
                            visited.add((nf,nx,ny))
                            q.append((nf,nx,ny, path+[(nf,nx,ny)]))

    if found_path:
        # write per-floor path files and combined
        outdir = Path("outputs/multifloor_run")
        outdir.mkdir(parents=True, exist_ok=True)
        with open(outdir / "multifloor_path.txt", "w") as f:
            for (ff, xx, yy) in found_path:
                f.write(f"{ff},{xx},{yy}\n")

        # create overlays per floor
        for fi, floor in enumerate(floors):
            # extract path points for this floor
            pts = [(x,y) for (ff,x,y) in [(a,b,c) for (a,b,c) in found_path] if a==fi]
            # draw overlay using existing draw_overlay: need to craft a result dict
            # build a simple result
            res = {
                'path': [(x,y) for (x,y) in [(p[1], p[2]) for p in found_path if p[0]==fi]],
                'start_point': start_pos if fi==0 else None,
                'goal_point': goal_pos if fi==len(floors)-1 else None,
                'orig_size': floor['orig_size'],
                'new_size': floor['new_size']
            }
            try:
                draw_overlay(floor['path'], floor['texts'], res, out_path=str(outdir / f"overlay_floor_{fi+1}.png"))
            except Exception as e:
                print(f"[!] Failed drawing overlay for floor {fi+1}: {e}")

        # also write debug overlays showing stairs/portals/start/goal
        for fi, _ in enumerate(floors):
            try:
                draw_debug_overlay(floors, fi, start_scaled if fi==0 else None, goal_scaled if fi==len(floors)-1 else None, portals, str(outdir / f"debug_overlay_floor_{fi+1}.png"))
            except Exception as e:
                print(f"[!] Failed writing debug overlay for floor {fi+1}: {e}")

        print(f"[✔] Multi-floor path found, steps={len(found_path)}. Outputs → {outdir}")
        return {'path': found_path, 'outdir': str(outdir)}
    else:
        outdir = Path("outputs/multifloor_run_debug")
        outdir.mkdir(parents=True, exist_ok=True)
        print("[!] No multi-floor path found — writing debug overlays to", outdir)
        for fi, _ in enumerate(floors):
            try:
                draw_debug_overlay(floors, fi, start_scaled if fi==0 else None, goal_scaled if fi==len(floors)-1 else None, portals, str(outdir / f"debug_overlay_floor_{fi+1}.png"))
            except Exception as e:
                print(f"[!] Failed writing debug overlay for floor {fi+1}: {e}")
        return None


###############################################################
# MAIN
###############################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run navigation: segmentation + OCR + pathfinding")
    parser.add_argument("--image", "-i", help="Path to input image", required=False)
    parser.add_argument("--start", help="Start text (OCR-detected) to use", required=False)
    parser.add_argument("--goal", help="Goal text (OCR-detected) to use", required=False)
    parser.add_argument("--dilate", type=int, default=3, help="Wall dilation radius in mask pixels (default 3)")
    parser.add_argument("--clearance", type=float, default=None, help="Clearance in mask pixels (distance-transform)")
    args = parser.parse_args()

    image = args.image or r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-1.png"

    print("=== OCR RUN ===")
    text_positions_global = run_ocr(image)

    items = list_texts(text_positions_global)

    if args.start:
        start = args.start
    else:
        print("\n=== Select Start ===")
        start = ask("start: ", items)

    if args.goal:
        goal = args.goal
    else:
        print("\n=== Select Goal ===")
        goal = ask("goal: ", items)

    result = get_path(image, start, goal, wall_dilate=args.dilate, clearance_px=args.clearance)

    # Ensure all numpy types are converted to native Python types for JSON
    def _to_native(o):
        if o is None:
            return None
        if isinstance(o, (str, bool, type(None))):
            return o
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (list, tuple)):
            return [_to_native(v) for v in o]
        if isinstance(o, dict):
            return {k: _to_native(v) for k, v in o.items()}
        if isinstance(o, np.ndarray):
            return _to_native(o.tolist())
        try:
            return int(o)
        except Exception:
            try:
                return float(o)
            except Exception:
                return str(o)

    result_native = _to_native(result)
    print(json.dumps(result_native, indent=2, ensure_ascii=False))

    # Save overlay image with OCR texts and path
    try:
        draw_overlay(image, text_positions_global, result)
    except Exception as e:
        print(f"[!] Failed to draw overlay: {e}")
