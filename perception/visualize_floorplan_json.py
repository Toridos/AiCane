import json
import cv2
import numpy as np

def draw_map(json_path: str, out_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    w = data["image_size"]["width"]
    h = data["image_size"]["height"]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)

    # 벽: 파란색
    for wall in data["walls"]:
        pts = np.array(wall["polygon"], dtype=np.int32)
        cv2.polylines(canvas, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

    # 문: 초록색
    for door in data["doors"]:
        pts = np.array(door["polygon"], dtype=np.int32)
        cv2.polylines(canvas, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

    # 방: 빨간색 윤곽
    for room in data["rooms"]:
        pts = np.array(room["polygon"], dtype=np.int32)
        cv2.polylines(canvas, [pts], isClosed=True, color=(0, 0, 255), thickness=2)

    cv2.imwrite(out_path, canvas)
    print(f"[OK] 시각화 결과 저장: {out_path}")