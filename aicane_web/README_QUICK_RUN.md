Quick run: segmentation + path overlay

1) Install (recommended virtualenv)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install opencv-python numpy
   # optional pytesseract if you want OCR
   pip install pytesseract

2) Run the quick processor
   python scripts\quick_process.py --image path\to\floorplan.png --start 200,800 --target 105

Outputs (uploads/):
 - preprocessed.png  # binary walls preview
 - grid.npy          # occupancy grid (wall=1)
 - ocr_debug.png     # candidate boxes and OCR text (if available)
 - path_overlay.png  # original image with path drawn

Notes:
- If pytesseract is not installed, OCR step is skipped; you can pass target as coordinates: --target 200,80
- This is a quick prototype: for production you should train a detector (YOLO) or a UNet segmentation model.
