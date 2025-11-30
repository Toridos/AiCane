import cv2
import json
import numpy as np
from pathlib import Path

import run_navigation as rn
from match_rooms import match_floor_rooms


# ==========================================================
# COLOR MASK FUNCTIONS
# ==========================================================

def extract_red_mask(img, kernel_size=9, min_area=400):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 60, 40])
    upper1 = np.array([25, 255, 255])
    lower2 = np.array([150, 60, 40])
    upper2 = np.array([180, 255, 255])

    m1 = cv2.inRange(hsv, lower1, upper1)
    m2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(m1, m2)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    mask = cv2.dilate(mask, k)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(out, [c], -1, 255, -1)
    return out


def extract_blue_mask(img, kernel_size=9, min_area=400):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([80, 80, 40])
    upper = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    mask = cv2.dilate(mask, k)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(out, [c], -1, 255, -1)
    return out


def mask_to_grid(mask):
    g = np.zeros(mask.shape, dtype=np.uint8)
    g[mask > 0] = 1
    return g


# ==========================================================
# STAIR PROCESSING
# ==========================================================

def find_stair_centroids(blue_mask):
    cnts, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pts = []
    for c in cnts:
        M = cv2.moments(c)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        pts.append((cx, cy))
    return pts


def connect_stairs(stairs_f1, stairs_f2):
    pairs = []
    if not stairs_f1 or not stairs_f2:
        return pairs

    used = set()
    for a in stairs_f1:
        best = None
        best_d = None
        best_j = None
        for j, b in enumerate(stairs_f2):
            if j in used:
                continue
            d = (a[0] - b[0])**2 + (a[1] - b[1])**2
            if best_d is None or d < best_d:
                best_d = d
                best = b
                best_j = j
        if best is not None:
            pairs.append((a, best))
            used.add(best_j)
    return pairs


# ==========================================================
# MULTI-FLOOR BFS
# ==========================================================

def bfs_multifloor(grids, stairs_connect, start, goal):
    from collections import deque

    Q = deque([start])
    visited = set([start])
    parent = {}

    while Q:
        f, x, y = Q.popleft()

        if (f, x, y) == goal:
            # reconstruct path
            path = []
            cur = (f, x, y)
            while cur in parent:
                path.append(cur)
                cur = parent[cur]
            path.append(start)
            return path[::-1]

        grid = grids[f]
        H, W = grid.shape

        # same-floor neighbors
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < W and 0 <= ny < H and grid[ny, nx] == 0:
                nxt = (f, nx, ny)
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = (f, x, y)
                    Q.append(nxt)

        # floor changes via stairs
        if f in stairs_connect:
            for (sx, sy), (tx, ty) in stairs_connect[f]:
                if abs(x - sx) <= 2 and abs(y - sy) <= 2:
                    nxt = (f + 1, tx, ty)
                    if nxt not in visited:
                        visited.add(nxt)
                        parent[nxt] = (f, x, y)
                        Q.append(nxt)

    return None


# ==========================================================
# MAIN ROUTE GENERATION FUNCTION
# ==========================================================

def generate_multifloor_path(images, start_room, goal_room):
    """
    images = [
        (imgpath, range_start, range_end, floor_number)
    ]
    """

    floors = {}
    floor_nums = []

    # ------------------------------------------------------
    # 1) 모든 층 이미지 로드 + OCR + 방 좌표 찾기
    # ------------------------------------------------------
    for imgpath, rstart, rend, f in images:
        floor_nums.append(f)

        img = cv2.imread(imgpath)
        if img is None:
            raise FileNotFoundError(f"Cannot load image: {imgpath}")

        # OCR
        texts = rn.run_ocr(imgpath)
        cleaned = match_floor_rooms(texts, rstart, rend, max_dist=5)

        # red mask
        red_mask = extract_red_mask(img)
        grid = mask_to_grid(red_mask)

        # blue mask
        blue_mask = extract_blue_mask(img)
        stairs = find_stair_centroids(blue_mask)

        floors[f] = dict(
            img=img,
            grid=grid,
            stairs=stairs,
            cleaned=cleaned,
            texts=texts,
            red_mask=red_mask,
            blue_mask=blue_mask
        )

    floor_nums.sort()

    # ------------------------------------------------------
    # 2) 감지된 방 번호 목록
    # ------------------------------------------------------
    detected_rooms = {
        f: sorted(list(floors[f]["cleaned"].keys()))
        for f in floor_nums
    }

    # ------------------------------------------------------
    # 3) start_room / goal_room 감지 여부 확인
    # ------------------------------------------------------
    start_detected = any(start_room in floors[f]["cleaned"] for f in floor_nums)
    goal_detected = any(goal_room in floors[f]["cleaned"] for f in floor_nums)

    if not start_detected or not goal_detected:
        return {
            "success": False,
            "reason": "Start or Goal room NOT detected via OCR",
            "start_room": start_room,
            "goal_room": goal_room,
            "detected_rooms": detected_rooms
        }

    # ------------------------------------------------------
    # 4) 계단 연결 정보 생성
    # ------------------------------------------------------
    stairs_connect = {}

    for f in floor_nums:
        if f + 1 not in floors:
            continue

        s1 = floors[f]["stairs"]
        s2 = floors[f + 1]["stairs"]
        pairs = connect_stairs(s1, s2)
        stairs_connect[f] = pairs

        # stairs 주변 grid 열린 공간 carve
        grid_f = floors[f]["grid"]
        grid_nf = floors[f + 1]["grid"]

        for (sx, sy), (tx, ty) in pairs:
            r = 3
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    ax = int(sx + dx)
                    ay = int(sy + dy)
                    bx = int(tx + dx)
                    by = int(ty + dy)

                    H, W = grid_f.shape
                    if 0 <= ax < W and 0 <= ay < H:
                        grid_f[ay, ax] = 0

                    H2, W2 = grid_nf.shape
                    if 0 <= bx < W2 and 0 <= by < H2:
                        grid_nf[by, bx] = 0

    # ------------------------------------------------------
    # 5) BFS로 최종 경로 생성
    # ------------------------------------------------------
    # start, goal 좌표
    start_floor = max([f for f in floor_nums if start_room in floors[f]["cleaned"]])
    goal_floor = max([f for f in floor_nums if goal_room in floors[f]["cleaned"]])

    sx, sy = floors[start_floor]["cleaned"][start_room]
    gx, gy = floors[goal_floor]["cleaned"][goal_room]

    path = bfs_multifloor(
        grids={f: floors[f]["grid"] for f in floor_nums},
        stairs_connect=stairs_connect,
        start=(start_floor, int(sx), int(sy)),
        goal=(goal_floor, int(gx), int(gy)),
    )

    if not path:
        return {
            "success": False,
            "reason": "No BFS path possible",
            "start_room": start_room,
            "goal_room": goal_room,
            "detected_rooms": detected_rooms
        }

    # ------------------------------------------------------
    # 6) 최종 path JSON 형태로 변환
    # ------------------------------------------------------
    converted = [
        {"floor": f, "x": int(x), "y": int(y)}
        for (f, x, y) in path
    ]

    return {
        "success": True,
        "start_room": start_room,
        "goal_room": goal_room,
        "detected_rooms": detected_rooms,
        "path": converted
    }
