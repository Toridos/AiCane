from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolov8n-seg.pt")

    model.train(
        data=r"C:\SW_3_2\toridos\AiCane\floorplan_seg.yaml",
        epochs=5,
        imgsz=800,
        batch=1,
        workers=0,
        device=0   # GPU!
    )
