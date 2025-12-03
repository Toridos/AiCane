import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from process_map import process_floorplan
from navigator import load_grid, get_position, a_star, simplify_waypoints

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload_png(file: UploadFile = File(...)):
    path = f"{UPLOAD_DIR}/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"message": "uploaded", "path": path}


@app.post("/process-map")
async def process_map(filename: str):
    png_path = f"{UPLOAD_DIR}/{filename}"
    grid_path, room_positions = process_floorplan(png_path)
    return {"grid_path": grid_path, "rooms": room_positions}


@app.get("/navigate")
async def navigate(room: str):
    grid = load_grid()

    start = get_position("FrontDoor")
    goal = get_position(room)

    path = a_star(grid, start, goal)
    waypoints = simplify_waypoints(path)

    return {"start": start, "goal": goal, "path": path, "waypoints": waypoints}


@app.get("/logs")
async def stream_logs():

    def log_stream():
        if os.path.exists("runtime.log"):
            for line in open("runtime.log", "r"):
                yield line
        else:
            yield "No logs yet."

    return StreamingResponse(log_stream(), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
