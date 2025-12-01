# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json, time, uuid, cv2
import numpy as np
from pathlib import Path
from route_core import bfs_single_floor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the `static/` folder at the `/static` URL path
# Use an absolute path based on this file's directory to avoid CWD issues.
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

# ---------------------------------------------------
# Load precomputed data
# ---------------------------------------------------
PRE = {}

for f in [1,2,3]:
    with open(f"static/cleaned_f{f}.json") as fp:
        cleaned = {int(k): list(map(int,v)) for k,v in json.load(fp).items()}
    grid = np.load(f"static/grid_f{f}.npy")
    with open(f"static/stairs_f{f}.json") as fp:
        stairs = [tuple(x) for x in json.load(fp)]
    PRE[f] = {"cleaned": cleaned, "grid": grid, "stairs": stairs}


FLOOR_IMG = {
    1: "static/s4_1_nor-1.png",
    2: "static/s4_1_nor-2.png",
    3: "static/s4_1_nor-3.png"
}

OVERLAY_DIR = Path("static/overlays")
OVERLAY_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

class Req(BaseModel):
    start_room: int
    goal_room: int


# ---------------------------------------------------
# Overlay generator
# ---------------------------------------------------
def draw_overlay(floor, path):
    img = cv2.imread(FLOOR_IMG[floor])
    for i,(x,y) in enumerate(path):
        cv2.circle(img,(x,y),3,(0,0,255),-1)
        if i>0:
            px,py = path[i-1]
            cv2.line(img,(px,py),(x,y),(0,0,255),2)
    name = f"overlay_{floor}_{uuid.uuid4().hex}.png"
    cv2.imwrite(str(OVERLAY_DIR/name),img)
    return f"/static/overlays/{name}"


# ---------------------------------------------------
# API
# ---------------------------------------------------
@app.post("/api/generate-path")
def generate_path(req: Req):
    start_f = int(str(req.start_room)[0])
    goal_f  = int(str(req.goal_room)[0])

    sx, sy = PRE[start_f]["cleaned"][req.start_room]
    gx, gy = PRE[goal_f]["cleaned"][req.goal_room]

    # --------------------------------------------------
    # 단층
    # --------------------------------------------------
    if start_f == goal_f:
        raw = bfs_single_floor(PRE[start_f]["grid"], (sx,sy), (gx,gy))
        if not raw:
            return {"success": False}
        path = [{"floor":start_f,"x":x,"y":y} for x,y in raw]
        img_url = draw_overlay(start_f, raw)

        # save JSON
        outfile = OUTPUT_DIR / f"route_{req.start_room}_{req.goal_room}_{time.time()}.json"
        with open(outfile,"w") as f: json.dump(path,f,indent=2)

        return {"success":True,"path":path,"overlay":[img_url],"json_file":str(outfile)}

    # --------------------------------------------------
    # 복층
    # --------------------------------------------------
    # 계단을 반드시 같은 계단(같은 스택/샤프트)으로 사용하도록 시도합니다.
    # 방법: 시작층의 각 계단 후보에 대해 목표층에서 가장 가까운 대응 계단을 찾고,
    # 양쪽에서 실제 경로(raw1, raw2)가 생성되는 조합 중 비용(경로 길이 합)이 가장 작은 것을 선택합니다.
    start_stairs = PRE[start_f]["stairs"]
    goal_stairs = PRE[goal_f]["stairs"]

    best = None
    best_score = None
    # iterate start stairs and match to nearest on goal floor
    for s in start_stairs:
        # find nearest candidate on goal floor (by squared distance)
        t = min(goal_stairs, key=lambda g: (g[0]-s[0])**2 + (g[1]-s[1])**2)
        raw1_cand = bfs_single_floor(PRE[start_f]["grid"], (sx,sy), s)
        raw2_cand = bfs_single_floor(PRE[goal_f]["grid"], t, (gx,gy))
        if raw1_cand and raw2_cand:
            score = len(raw1_cand) + len(raw2_cand)
            if best is None or score < best_score:
                best = (s, t, raw1_cand, raw2_cand)
                best_score = score

    if best is not None:
        stairs_start, stairs_goal, raw1, raw2 = best
    else:
        # fallback: independent nearest (기존 동작)
        stairs_start = min(start_stairs, key=lambda s: abs(s[0]-sx)+abs(s[1]-sy))
        stairs_goal  = min(goal_stairs, key=lambda s: abs(s[0]-gx)+abs(s[1]-gy))
        raw1 = bfs_single_floor(PRE[start_f]["grid"], (sx,sy), stairs_start)
        raw2 = bfs_single_floor(PRE[goal_f]["grid"], stairs_goal, (gx,gy))

    if not raw1 or not raw2:
        return {"success":False}

    path=[]
    path+= [{"floor":start_f,"x":x,"y":y} for x,y in raw1]
    path+= [{"floor":goal_f,"x":x,"y":y} for x,y in raw2]

    img1 = draw_overlay(start_f, raw1)
    img2 = draw_overlay(goal_f, raw2)

    outfile = OUTPUT_DIR / f"route_{req.start_room}_{req.goal_room}_{time.time()}.json"
    with open(outfile,"w") as f: json.dump(path,f,indent=2)

    return {"success":True,"path":path,"overlay":[img1,img2],"json_file":str(outfile)}


@app.post("/api/generate-path-coords")
def generate_path_coords(body: dict):
    """Accepts JSON:
    {"start": {"floor":1,"x":100,"y":150}, "goal": {"floor":3,"x":200,"y":300}}
    Returns same structure as /api/generate-path
    """
    try:
        start = body.get("start")
        goal = body.get("goal")
        sf = int(start.get("floor"))
        gf = int(goal.get("floor"))
        sx, sy = int(start.get("x")), int(start.get("y"))
        gx, gy = int(goal.get("x")), int(goal.get("y"))
    except Exception as e:
        return {"success": False, "error": "invalid payload"}

    # single floor
    if sf == gf:
        raw = bfs_single_floor(PRE[sf]["grid"], (sx, sy), (gx, gy))
        if not raw:
            return {"success": False}
        path = [{"floor": sf, "x": x, "y": y} for x, y in raw]
        img_url = draw_overlay(sf, raw)
        outfile = OUTPUT_DIR / f"route_coords_{sf}_{time.time()}.json"
        with open(outfile, "w") as f:
            json.dump(path, f, indent=2)
        return {"success": True, "path": path, "overlay": [img_url], "json_file": str(outfile)}

    # multi-floor: pick same-stair matching similar to existing logic
    start_stairs = PRE[sf]["stairs"]
    goal_stairs = PRE[gf]["stairs"]

    best = None
    best_score = None
    for s in start_stairs:
        t = min(goal_stairs, key=lambda g: (g[0]-s[0])**2 + (g[1]-s[1])**2)
        raw1_cand = bfs_single_floor(PRE[sf]["grid"], (sx, sy), s)
        raw2_cand = bfs_single_floor(PRE[gf]["grid"], t, (gx, gy))
        if raw1_cand and raw2_cand:
            score = len(raw1_cand) + len(raw2_cand)
            if best is None or score < best_score:
                best = (s, t, raw1_cand, raw2_cand)
                best_score = score

    if best is not None:
        stairs_start, stairs_goal, raw1, raw2 = best
    else:
        stairs_start = min(start_stairs, key=lambda s: abs(s[0]-sx)+abs(s[1]-sy))
        stairs_goal  = min(goal_stairs, key=lambda s: abs(s[0]-gx)+abs(s[1]-gy))
        raw1 = bfs_single_floor(PRE[sf]["grid"], (sx, sy), stairs_start)
        raw2 = bfs_single_floor(PRE[gf]["grid"], stairs_goal, (gx, gy))

    if not raw1 or not raw2:
        return {"success": False}

    path = []
    path += [{"floor": sf, "x": x, "y": y} for x, y in raw1]
    path += [{"floor": gf, "x": x, "y": y} for x, y in raw2]

    img1 = draw_overlay(sf, raw1)
    img2 = draw_overlay(gf, raw2)
    outfile = OUTPUT_DIR / f"route_coords_{sf}_{gf}_{time.time()}.json"
    with open(outfile, "w") as f:
        json.dump(path, f, indent=2)

    return {"success": True, "path": path, "overlay": [img1, img2], "json_file": str(outfile)}
