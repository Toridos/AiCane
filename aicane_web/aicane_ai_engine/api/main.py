import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

import cv2, numpy as np, os

from preprocess.preprocess import preprocess_floorplan
from segmentation.infer_unet import run_segmentation
from navigation.occupancy_grid import build_grid
from navigation.astar import a_star
from navigation.find_path import find_path
# optional: backend process_map for OCR-based room detection
try:
    from backend.process_map import process_floorplan as backend_process_floorplan
except Exception:
    backend_process_floorplan = None

app = FastAPI()

# -----------------------------
# 🔥 CORS 설정 (중요!)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 또는 ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# =============================
# Upload → Process
# =============================
@app.post("/process")
async def process(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    with open(path, "wb") as f:
        f.write(await file.read())

    pre = preprocess_floorplan(path)
    cv2.imwrite("uploads/preprocessed.png", pre)

    mask = run_segmentation("uploads/preprocessed.png")
    np.save("uploads/mask.npy", mask)

    grid = build_grid(mask)
    # If available, run backend/process_map to produce room_positions via OCR
    room_positions = None
    ocr_texts = None
    if backend_process_floorplan is not None:
        try:
            res = backend_process_floorplan(path)
            if isinstance(res, (list, tuple)) and len(res) >= 3:
                _, room_positions, ocr_texts = res
            else:
                _, room_positions = res
        except Exception:
            room_positions = None
            ocr_texts = None

    return {"status": "ok", "rooms": room_positions, "ocr": ocr_texts}


# =============================
# A* Navigate
# =============================
@app.get("/navigate")
def navigate(sx: int, sy: int, gx: int, gy: int):
    grid = np.load("uploads/grid.npy")
    path = a_star(grid, (sy, sx), (gy, gx))
    return {"path": path}


# =============================
# Grid Image for Viewer
# =============================
@app.get("/grid/image")
def get_grid_image():
    grid = np.load("uploads/grid.npy")
    img = (grid * 255).astype("uint8")
    # encode image to PNG in-memory and return bytes to avoid touching disk
    ret, buf = cv2.imencode('.png', img)
    if not ret:
        return JSONResponse({"error": "failed to encode image"}, status_code=500)
    return Response(content=buf.tobytes(), media_type="image/png")


# =============================
# Room → Path
# =============================
@app.get("/path")
def get_path(room: str):
    result = find_path(room)
    return result
