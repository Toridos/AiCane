# floorplan_to_json.py

from ultralytics import YOLO
import cv2
import json
import numpy as np

MODEL_PATH = "runs/segment/train/weights/best.pt"  # 학습된 모델 경로
model = YOLO(MODEL_PATH)

def infer_floorplan(image_path: str) -> dict:
    """평면도 이미지 1장을 YOLO 세그멘테이션 → JSON map dict로 변환."""
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    results = model(img)[0]  # 첫 번째 결과
    masks = results.masks
    classes = results.boxes.cls.cpu().numpy().astype(int)

    walls = []
    doors = []
    rooms = []

    if masks is not None:
        for i, m in enumerate(masks.data):
            cls_id = classes[i]
            # m: (H,W) mask tensor -> numpy로 변환
            mask = m.cpu().numpy()
            # 등고선(외곽선) 추출 → polygon
            contours, _ = cv2.findContours(
                (mask * 255).astype(np.uint8),
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                continue
            # 가장 큰 컨투어 하나만 사용
            c = max(contours, key=cv2.contourArea)
            poly = c.squeeze().tolist()  # [[x,y], [x,y], ...]

            if cls_id == 0:
                walls.append({"id": len(walls)+1, "polygon": poly})
            elif cls_id == 1:
                doors.append({"id": len(doors)+1, "polygon": poly})
            elif cls_id == 2:
                rooms.append({"id": f"R{len(rooms)+1:03d}", "polygon": poly})

    map_dict = {
        "map_id": "SAMPLE_FLOOR_01",
        "source": image_path,
        "image_size": {"width": w, "height": h},
        "resolution": 0.05,
        "origin": {"x": 0.0, "y": 0.0},
        "walls": walls,
        "doors": doors,
        "rooms": rooms
    }
    return map_dict


def save_map_json(image_path: str, out_json: str):
    data = infer_floorplan(image_path)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True, help="입력 평면도 이미지")
    p.add_argument("--out", required=True, help="출력 JSON 경로")
    args = p.parse_args()

    save_map_json(args.image, args.out)
    print(f"[OK] JSON map saved to {args.out}")