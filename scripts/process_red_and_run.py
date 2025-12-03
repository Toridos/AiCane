import os
import cv2
import numpy as np
from pathlib import Path

import sys
from pathlib import Path as _Path

# ensure repo root is on sys.path so run_navigation can be imported the same way
repo_root = _Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
import run_navigation as rn


def extract_red_mask(img, kernel_size=7, min_area=500):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower1 = np.array([0, 100, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([160, 100, 50])
    upper2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # remove small components
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(out, [c], -1, 255, -1)

    return out


def mask_to_grid_from_binary(mask):
    # mask: uint8 0/255
    grid = np.zeros(mask.shape, dtype=np.uint8)
    grid[mask > 0] = 1
    return grid


def pick_start_goal_from_ocr(text_positions):
    # prefer numeric room labels; choose leftmost as start, rightmost as goal
    items = []
    for t, pos in text_positions.items():
        x, y = int(pos[0]), int(pos[1])
        items.append((t, (x, y)))

    if not items:
        return None, None

    # filter tokens containing digits
    numeric = [(t, p) for t, p in items if any(ch.isdigit() for ch in t)]
    use = numeric if numeric else items

    # sort by x coordinate
    use_sorted = sorted(use, key=lambda it: it[1][0])
    start = use_sorted[0][1]
    goal = use_sorted[-1][1]
    return start, goal


def draw_overlay_custom(image, red_mask, text_positions, path, start, goal, out_path):
    img = image.copy()
    h, w = img.shape[:2]

    # overlay red mask (as translucent red)
    red_col = np.zeros_like(img)
    red_col[:, :, 2] = 255
    alpha = (red_mask > 0).astype(np.float32) * 0.6
    alpha3 = np.stack([alpha, alpha, alpha], axis=2)
    img = (img.astype(np.float32) * (1 - alpha3) + red_col.astype(np.float32) * alpha3).astype(np.uint8)

    # draw OCR texts
    for t, pos in text_positions.items():
        try:
            x, y = int(pos[0]), int(pos[1])
            cv2.circle(img, (x, y), 6, (0, 255, 0), -1)
            cv2.putText(img, str(t), (x + 8, y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        except Exception:
            continue

    # draw path
    if path:
        pts = [(int(x), int(y)) for (x, y) in path]
        if len(pts) > 0:
            for p in pts:
                cv2.circle(img, p, 2, (255, 0, 0), -1)
            cv2.polylines(img, [np.array(pts, dtype=np.int32)], False, (255, 0, 0), 2)

    # start/goal
    if start:
        try:
            cv2.circle(img, (int(start[0]), int(start[1])), 12, (0, 255, 255), -1)
        except Exception:
            pass
    if goal:
        try:
            cv2.circle(img, (int(goal[0]), int(goal[1])), 12, (0, 0, 255), -1)
        except Exception:
            pass

    cv2.imwrite(out_path, img)
    print(f"[✔] Saved overlay → {out_path}")


def run_on_image(image_path):
    p = Path(image_path)
    if not p.exists():
        print(f"[!] Image not found: {image_path}")
        return

    outdir = Path("outputs/red_wall_run")
    outdir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(p))
    red_mask = extract_red_mask(img, kernel_size=9, min_area=200)
    cv2.imwrite(str(outdir / "red_wall_mask.png"), red_mask)
    print("[✔] Red mask written:", str(outdir / "red_wall_mask.png"))

    grid = mask_to_grid_from_binary(red_mask)
    np.savetxt(str(outdir / "grid_map.txt"), grid, fmt="%d")
    print("[✔] Grid map saved:", str(outdir / "grid_map.txt"))

    # run OCR using run_navigation's function (this may take a bit)
    print("=== Running OCR (this may take a bit) ===")
    text_positions = rn.run_ocr(str(p))
    print("Detected OCR count:", len(text_positions))

    # show detected tokens to user
    items = list(text_positions.items())

    # extract numeric room id (e.g., 101 from '101호' or '101')
    import re
    numeric_items = []  # list of (tok, pos, num)
    other_items = []
    for tok, pos in items:
        m = re.search(r"(\d{2,4})", str(tok))
        if m:
            try:
                num = int(m.group(1))
                numeric_items.append((tok, pos, num))
            except Exception:
                other_items.append((tok, pos))
        else:
            other_items.append((tok, pos))

    # sort numeric items by numeric value
    numeric_items.sort(key=lambda t: t[2])

    print('\nDetected OCR tokens (numeric first):')
    # print numeric list (with indices starting at 0)
    for i, (tok, pos, num) in enumerate(numeric_items):
        try:
            print(f"[{i}] {num} -> '{tok}' @ ({int(pos[0])},{int(pos[1])})")
        except Exception:
            print(f"[{i}] {num} -> '{tok}' @ {pos}")

    # print non-numeric items after
    if other_items:
        print('\nOther detected tokens:')
        for j, (tok, pos) in enumerate(other_items, start=len(numeric_items)):
            try:
                print(f"[{j}] '{tok}' @ ({int(pos[0])},{int(pos[1])})")
            except Exception:
                print(f"[{j}] '{tok}' @ {pos}")

    # allow CLI args: python process_red_and_run.py <image> <start_token_or_index> <goal_token_or_index>
    import sys
    start_pos = None
    goal_pos = None
    if len(sys.argv) >= 3:
        # arguments provided: interpret as token strings first, then indices
        a = sys.argv[1]
        b = sys.argv[2]
        def resolve_arg(val):
            # allow selecting from numeric_items first (indices 0..len(numeric_items)-1)
            if val.isdigit():
                idx = int(val)
                total = len(numeric_items) + len(other_items)
                if 0 <= idx < total:
                    if idx < len(numeric_items):
                        return numeric_items[idx][1]
                    else:
                        return other_items[idx - len(numeric_items)][1]
                return None
            # exact match
            if val in text_positions:
                return text_positions[val]
            # partial match
            for k in text_positions:
                if val in k:
                    return text_positions[k]
            return None
        start_pos = resolve_arg(a)
        goal_pos = resolve_arg(b)
    else:
        print('\nEnter start token (exact text shown) or index number. Leave blank to auto-pick.')
        s_in = input('start> ').strip()
        print('Enter goal token (exact text shown) or index number. Leave blank to auto-pick.')
        g_in = input('goal> ').strip()
        if s_in == '' and g_in == '':
            start_pos, goal_pos = pick_start_goal_from_ocr(text_positions)
        else:
            def resolve_input(val):
                if val == '':
                    return None
                if val.isdigit():
                    idx = int(val)
                    total = len(numeric_items) + len(other_items)
                    if 0 <= idx < total:
                        if idx < len(numeric_items):
                            return numeric_items[idx][1]
                        else:
                            return other_items[idx - len(numeric_items)][1]
                    return None
                if val in text_positions:
                    return text_positions[val]
                for k in text_positions:
                    if val in k:
                        return text_positions[k]
                return None
            start_pos = resolve_input(s_in)
            goal_pos = resolve_input(g_in)

    if start_pos is None or goal_pos is None:
        print('[!] Could not resolve start/goal from input. Aborting path search.')
        return

    # clamp to grid and convert to ints
    H, W = grid.shape
    sx = max(0, min(W - 1, int(start_pos[0])))
    sy = max(0, min(H - 1, int(start_pos[1])))
    gx = max(0, min(W - 1, int(goal_pos[0])))
    gy = max(0, min(H - 1, int(goal_pos[1])))

    print(f"Requested Start {sx,sy}  Goal {gx,gy}")

    # snap to nearest free cell if the requested point is on a wall
    try:
        ns = rn.nearest_free_cell(grid, sx, sy, max_radius=30)
        ng = rn.nearest_free_cell(grid, gx, gy, max_radius=30)
        if ns != (sx, sy):
            print(f"Snapped start {sx,sy} -> {ns}")
            sx, sy = ns
        if ng != (gx, gy):
            print(f"Snapped goal {gx,gy} -> {ng}")
            gx, gy = ng
    except Exception:
        # if nearest_free_cell isn't available, proceed without snapping
        pass

    path = rn.bfs(grid, (sx, sy), (gx, gy))
    if path:
        print(f"[✔] Path found, length={len(path)}")
        with open(outdir / "path.txt", "w") as f:
            for x,y in path:
                f.write(f"{x},{y}\n")
    else:
        print("[!] No path found")

    # create overlay
    draw_overlay_custom(img, red_mask, text_positions, path, (sx, sy), (gx, gy), str(outdir / "overlay_red_wall.png"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/process_red_and_run.py <image_path>")
        sys.exit(1)
    image_path = sys.argv[1]
    run_on_image(image_path)
