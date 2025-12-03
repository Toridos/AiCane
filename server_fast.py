from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, time
from pathlib import Path
import cv2
import numpy as np
import uuid

# -------------------------------------------------------------
# CORS
# -------------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Request model
# -------------------------------------------------------------
class PathRequest(BaseModel):
    start_room: int
    goal_room: int

# -------------------------------------------------------------
# JSON 저장
# -------------------------------------------------------------
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

OVERLAY_DIR = Path("static/overlays")
OVERLAY_DIR.mkdir(exist_ok=True)

def save_route_json(start_room, goal_room, data):
    ts = int(time.time())
    filename = f"route_{start_room}_{goal_room}_{ts}.json"
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return str(filepath)

# -------------------------------------------------------------
# Floor 기반 파일 경로
# -------------------------------------------------------------
floor_image = {
    1: "static/s4_1-1.png",
    2: "static/s4_1-2.png",
    3: "static/s4_1-3.png",
}

# -------------------------------------------------------------
# 단층 BFS path-overlay 생성
# -------------------------------------------------------------
def draw_path_overlay(floor, path):
    img = cv2.imread(floor_image[floor])
    if img is None:
        raise ValueError(f"이미지 로드 실패: {floor_image[floor]}")

    # 경로 그리기
    for i, p in enumerate(path):
        x, y = p["x"], p["y"]
        cv2.circle(img, (x, y), 3, (0, 0, 255), -1)
        if i > 0:
            px, py = path[i - 1]["x"], path[i - 1]["y"]
            cv2.line(img, (px, py), (x, y), (0, 0, 255), 2)

    # 저장
    outname = f"overlay_{floor}_{uuid.uuid4().hex}.png"
    outpath = OVERLAY_DIR / outname
    cv2.imwrite(str(outpath), img)

    return f"/static/overlays/{outname}"

# -------------------------------------------------------------
# Dummy coordinate mapping (임시)
# -------------------------------------------------------------
def room_to_coord(room):
    f = int(str(room)[0])
    return f, 300, 150

# -------------------------------------------------------------
# BFS (단층)
# -------------------------------------------------------------
def bfs_path(floor, start_xy, goal_xy):
    img = cv2.imread(floor_image[floor])
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    red1 = cv2.inRange(hsv, np.array([0,60,40]), np.array([25,255,255]))
    red2 = cv2.inRange(hsv, np.array([150,60,40]), np.array([180,255,255]))
    grid = ((red1 | red2) > 0).astype(np.uint8)

    from collections import deque
    Q = deque([start_xy])
    visited = {start_xy}
    parent = {}
    sx, sy = start_xy
    gx, gy = goal_xy
    H, W = grid.shape

    while Q:
        x, y = Q.popleft()
        if (x,y)==(gx,gy):
            path=[]
            cur=(gx,gy)
            while cur in parent:
                path.append(cur)
                cur=parent[cur]
            path.append((sx,sy))
            path.reverse()
            return path

        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny=x+dx,y+dy
            if 0<=nx<W and 0<=ny<H and grid[ny,nx]==0:
                if (nx,ny) not in visited:
                    visited.add((nx,ny))
                    parent[(nx,ny)] = (x,y)
                    Q.append((nx,ny))

    return None

# -------------------------------------------------------------
# API 엔드포인트
# -------------------------------------------------------------
@app.post("/api/generate-path")
def generate(req: PathRequest):

    f1, sx, sy = room_to_coord(req.start_room)
    f2, gx, gy = room_to_coord(req.goal_room)

    # --------------------------
    # ① 단층
    # --------------------------
    if f1 == f2:
        path_raw = bfs_path(f1, (sx,sy), (gx,gy))
        if not path_raw:
            return {"success": False}

        # Convert to JSON-style
        path_json = [{"floor": f1, "x": x, "y": y} for x,y in path_raw]

        # Overlay image 생성
        overlay_url = draw_path_overlay(f1, path_json)

        # JSON 파일 저장
        jsonfile = save_route_json(req.start_room, req.goal_room,
                                   {"success": True,
                                    "path": path_json,
                                    "overlay": [overlay_url]})

        return {
            "success": True,
            "path": path_json,
            "overlay": [overlay_url],
            "json_file": jsonfile
        }

    # --------------------------
    # ② 복층  
    # (계단좌표는 더미 좌표 300,50 사용)
    # --------------------------
    stair = (300,50)

    p1 = bfs_path(f1,(sx,sy),stair)
    p2 = bfs_path(f2,stair,(gx,gy))

    if not p1 or not p2:
        return {"success": False}

    path_json = []
    path_json += [{"floor": f1, "x": x, "y": y} for x,y in p1]
    path_json += [{"floor": f2, "x": x, "y": y} for x,y in p2]

    # 두 이미지 오버레이
    overlay_urls = []
    overlay_urls.append(draw_path_overlay(f1, [{"floor": f1, "x": x, "y": y} for x,y in p1]))
    overlay_urls.append(draw_path_overlay(f2, [{"floor": f2, "x": x, "y": y} for x,y in p2]))

    # JSON 저장
    jsonfile = save_route_json(req.start_room, req.goal_room,
                               {"success": True,
                                "path": path_json,
                                "overlay": overlay_urls})

    return {
        "success": True,
        "path": path_json,
        "overlay": overlay_urls,
        "json_file": jsonfile
    }
