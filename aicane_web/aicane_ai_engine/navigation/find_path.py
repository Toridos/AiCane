import numpy as np
from .astar import a_star
import json
import os


# Try to load room positions detected by preprocessing/OCR if available.
def _load_room_positions():
    candidates = ["uploads/room_positions.json", "room_positions.json"]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # ensure keys are strings and values are tuples
                    clean = {}
                    for k, v in data.items():
                        if isinstance(v, (list, tuple)) and len(v) >= 2:
                            clean[str(k)] = (int(v[0]), int(v[1]))
                    return clean
            except Exception:
                continue

    # fallback mapping (legacy / placeholder)
    return {
        "FrontDoor": (540, 80),
        "115": (300, 180),
        "103": (120, 80),
        "104": (160, 80),
    }


ROOM_POSITIONS = _load_room_positions()


# ─────────────────────────────────────────────
# 2) 방 번호로 최종 경로를 찾는 함수
# ─────────────────────────────────────────────
def find_path(room: str):

    if room not in ROOM_POSITIONS:
        return {"error": f"Unknown room '{room}'"}

    # Start = FrontDoor
    start = ROOM_POSITIONS["FrontDoor"]

    # Goal = room 좌표
    goal = ROOM_POSITIONS[room]

    # grid.npy 로드
    grid = np.load("uploads/grid.npy")

    # A* 탐색 좌표 swap → (y, x)
    start_yx = (start[1], start[0])
    goal_yx = (goal[1], goal[0])

    # A* path
    path = a_star(grid, start_yx, goal_yx)

    if path is None or len(path) == 0:
        return {"error": "Path not found"}

    # Waypoints (방향이 바뀔 때마다 기록)
    waypoints = simplify_path(path)

    return {
        "start": start,
        "goal": goal,
        "path": path,
        "waypoints": waypoints
    }


# ─────────────────────────────────────────────
# 3) 불필요한 점 제거 — 직선 구간만 남기기
# ─────────────────────────────────────────────
def simplify_path(path):
    if len(path) < 3:
        return path

    simplified = [path[0]]
    for i in range(1, len(path) - 1):
        x1, y1 = path[i - 1]
        x2, y2 = path[i]
        x3, y3 = path[i + 1]

        # 방향 변화 감지
        if (x2 - x1, y2 - y1) != (x3 - x2, y3 - y2):
            simplified.append((x2, y2))

    simplified.append(path[-1])
    return simplified
