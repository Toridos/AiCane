# perception/floorplan_infer.py

"""
평면도 YOLO 세그멘테이션 결과를 기반으로
벽/문/방 폴리곤을 추출하여 내부용 JSON 지도 포맷으로 저장하는 스크립트입니다.

사용 예시:
    python -m perception.floorplan_infer data/raw_floorplans/floor1.png CBNU_ENG2_F1
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    print("[WARN] ultralytics가 설치되어 있지 않습니다. (Colab/가상환경에 설치 필요)")

# 프로젝트 루트 기준 경로 계산
ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "models" / "floorplan_yolov8n_seg_best.pt"
MAP_OUT_DIR = ROOT_DIR / "data" / "maps"

MAP_OUT_DIR.mkdir(parents=True, exist_ok=True)

_model = None


def _load_model():
    """YOLO 세그멘테이션 모델을 Lazy-Load."""
    global _model
    if _model is not None:
        return _model

    if YOLO is None:
        raise RuntimeError("ultralytics가 설치되어 있지 않습니다. (pip install ultralytics)")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

    print(f"[FLOORPLAN] 모델 로드: {MODEL_PATH}")
    _model = YOLO(MODEL_PATH.as_posix())
    return _model


def infer_floorplan(image_path: str, map_id: str) -> Dict[str, Any]:
    """
    평면도 이미지 1장을 입력으로 받아
    내부 지도 JSON(dict)을 생성하여 반환합니다.
    (실제 파일 저장은 save_floorplan_map에서 수행)
    """
    model = _load_model()

    img_path = Path(image_path)
    if not img_path.exists():
        raise FileNotFoundError(f"입력 이미지가 존재하지 않습니다: {img_path}")

    print(f"[FLOORPLAN] 추론 시작: {img_path}")
    results = model(img_path.as_posix())[0]

    h, w = results.orig_shape
    print(f"[FLOORPLAN] 원본 해상도: {w} x {h}")

    # 클래스 ID → semantic 이름 매핑
    # 학습 시 MERGE_MAP 기준:
    #   0: wall, 1: door, 2: room
    CLASS_NAME = {0: "wall", 1: "door", 2: "room"}

    walls: List[Dict[str, Any]] = []
    doors: List[Dict[str, Any]] = []
    rooms: List[Dict[str, Any]] = []

    # 세그멘테이션 결과에서 폴리곤 추출
    if results.masks is None:
        print("[FLOORPLAN] masks 결과가 없습니다. (seg 모델인지 확인 요망)")
    else:
        # results.masks.xy: 각 인스턴스별 polygon ndarray(N, 2)
        polys_xy = results.masks.xy
        cls_list = results.boxes.cls.cpu().numpy().astype(int).tolist()

        for cls_id, poly in zip(cls_list, polys_xy):
            if cls_id not in CLASS_NAME:
                continue

            poly_arr = np.asarray(poly, dtype=float)
            polygon = poly_arr.tolist()  # [[x, y], [x, y], ...]

            item = {"cls_id": int(cls_id),
                    "cls_name": CLASS_NAME[cls_id],
                    "polygon": polygon}

            if cls_id == 0:
                walls.append(item)
            elif cls_id == 1:
                doors.append(item)
            elif cls_id == 2:
                rooms.append(item)

    # 간단한 구조의 내부 지도 JSON 생성
    map_data: Dict[str, Any] = {
        "map_id": map_id,
        "image_file": str(img_path.name),
        "image_size": [int(w), int(h)],
        "walls": walls,
        "doors": doors,
        "rooms": rooms,
        # 나중에 수동으로 편집할 수 있는 확장 포인트
        "corridors": [],
        "waypoints": [],
    }

    return map_data


def save_floorplan_map(map_data: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)
    print(f"[FLOORPLAN] 지도 JSON 저장 완료: {out_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="평면도 YOLO 세그 → 내부 지도 JSON 변환")
    parser.add_argument("image", help="입력 평면도 이미지 경로 (png/jpg)")
    parser.add_argument("map_id", help="지도 ID (예: CBNU_ENG2_F1)")
    args = parser.parse_args()

    img_path = args.image
    map_id = args.map_id

    map_data = infer_floorplan(img_path, map_id)

    out_name = f"{map_id}.json"
    out_path = MAP_OUT_DIR / out_name
    save_floorplan_map(map_data, out_path)


if __name__ == "__main__":
    main()