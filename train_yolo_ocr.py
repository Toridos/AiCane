from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolov8n.pt")

    model.train(
        data=r"C:\SW_3_2\toridos\AiCane\floorplan_ocr.yaml",
        epochs=5,
        imgsz=640,
        batch=4,
        workers=0,
        device=0  # GPU
    )
