# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    1: "static/s4_1-1.png",
    2: "static/s4_1-2.png",
    3: "static/s4_1-3.png"
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
    # 계단은 좌표가 여러개 있을 수 있으니 가장 가까운 것 선택
    stairs_start = min(PRE[start_f]["stairs"], key=lambda s: abs(s[0]-sx)+abs(s[1]-sy))
    stairs_goal  = min(PRE[goal_f]["stairs"], key=lambda s: abs(s[0]-gx)+abs(s[1]-gy))

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
