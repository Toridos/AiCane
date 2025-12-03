from ultralytics import YOLO
import cv2
import numpy as np
import os

IMAGE = r"C:\SW_3_2\ai\AI_lab\yolo_dataset\images\APT_FP_OCR_230087881.PNG"
MODEL = r"c:\SW_3_2\toridos\AiCane\runs\segment\train7\weights\best.pt"
OUT_MASK_OVERLAY = r"mask_overlay_nav.png"
OUT_COMPOSITE = r"mask_and_path_overlay.png"

print('Using model:', MODEL)
model = YOLO(MODEL)
res = model(IMAGE)[0]

masks = res.masks
boxes = res.boxes

mask_arrays = masks.data.cpu().numpy()  # (N, H_new, W_new)
classes = boxes.cls.cpu().numpy().astype(int)

try:
    orig_h, orig_w = masks.orig_shape
except Exception:
    im = cv2.imread(IMAGE)
    orig_h, orig_w = im.shape[:2]

H_new, W_new = mask_arrays.shape[1], mask_arrays.shape[2]
print('orig (w,h)=', orig_w, orig_h, 'mask (w,h)=', W_new, H_new)

# create overlay on original image
img = cv2.imread(IMAGE)
overlay = img.copy()
alpha = 0.6
color_map = {0: (0,0,255), 1: (255,0,0), 2: (0,255,0), 3: (0,255,255), 4: (255,0,255), 5: (0,128,255)}

for seg, cls in zip(mask_arrays, classes):
    cls = int(cls)
    mask = (seg > 0.5).astype(np.uint8) * 255
    mask_resized = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
    color = color_map.get(cls, (200,200,200))
    colored = np.zeros_like(img, dtype=np.uint8)
    colored[:, :] = color
    mask_bin = mask_resized.astype(bool)
    overlay[mask_bin] = cv2.addWeighted(overlay, 1-alpha, colored, alpha, 0)[mask_bin]

cv2.imwrite(OUT_MASK_OVERLAY, overlay)
print('Saved', OUT_MASK_OVERLAY)

# Now overlay path (if exists)
if os.path.exists('path.txt'):
    pts = []
    with open('path.txt') as f:
        for l in f:
            if l.strip():
                x,y = map(int, l.strip().split(','))
                # scale to orig
                x_orig = int(x * (orig_w / float(W_new)))
                y_orig = int(y * (orig_h / float(H_new)))
                pts.append((x_orig, y_orig))
    comp = overlay.copy()
    if len(pts)>0:
        for p in pts:
            cv2.circle(comp, p, 3, (255,0,0), -1)
        cv2.polylines(comp, [np.array(pts, dtype=np.int32)], False, (255,0,0), 2)
    cv2.imwrite(OUT_COMPOSITE, comp)
    print('Saved', OUT_COMPOSITE)
else:
    print('path.txt not found; skipping composite')
