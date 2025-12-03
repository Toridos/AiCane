from ultralytics import YOLO
import cv2
import numpy as np
import os

# Paths (adjust if needed)
IMAGE = r"C:\SW_3_2\toridos\AiCane\debug_ocr_crops\box_7.png"
MODEL = r"c:\SW_3_2\toridos\AiCane\runs\segment\train7\weights\best.pt"
OUT_OVERLAY = r"mask_overlay.png"

print('Using model:', MODEL)
model = YOLO(MODEL)
res = model(IMAGE)[0]

masks = res.masks
boxes = res.boxes

# Get mask arrays and classes
mask_arrays = masks.data.cpu().numpy()  # shape (N, H_new, W_new)
classes = boxes.cls.cpu().numpy().astype(int)

# Determine original image size
orig_h_w = None
try:
    orig_h_w = masks.orig_shape  # (h,w)
    orig_h, orig_w = orig_h_w
except Exception:
    im = cv2.imread(IMAGE)
    orig_h, orig_w = im.shape[:2]

print('orig size:', orig_w, orig_h)
print('mask size (per mask):', mask_arrays.shape[1], mask_arrays.shape[2])

# Count pixels per class (threshold 0.5)
unique_classes = {}
for seg, cls in zip(mask_arrays, classes):
    cnt = int(np.sum(seg > 0.5))
    unique_classes.setdefault(int(cls), 0)
    unique_classes[int(cls)] += cnt

print('\nClass pixel counts (threshold>0.5):')
for cls, cnt in unique_classes.items():
    print(f'  class {cls}: {cnt} pixels')

# Prepare overlay on original image
img = cv2.imread(IMAGE)
overlay = img.copy()
alpha = 0.5

# color map for classes (BGR)
color_map = {
    0: (0,0,255),    # wall -> red
    1: (255,0,0),    # door -> blue
    2: (0,255,0),    # room -> green
    3: (0,255,255),  # elevator hall -> yellow
    4: (255,0,255),  # stair -> magenta
    5: (0,128,255)   # elevator -> orange-like
}

H_new, W_new = mask_arrays.shape[1], mask_arrays.shape[2]

for seg, cls in zip(mask_arrays, classes):
    cls = int(cls)
    mask = (seg > 0.5).astype(np.uint8) * 255  # new_h x new_w
    # resize mask to orig size
    mask_resized = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
    color = color_map.get(cls, (200,200,200))
    # create colored overlay
    colored = np.zeros_like(img, dtype=np.uint8)
    colored[:, :] = color
    # apply where mask
    mask_bin = mask_resized.astype(bool)
    overlay[mask_bin] = cv2.addWeighted(overlay, 1-alpha, colored, alpha, 0)[mask_bin]

# draw legend
y = 20
for cls, col in color_map.items():
    cv2.rectangle(overlay, (10, y-14), (30, y+6), col, -1)
    cv2.putText(overlay, f'class {cls}', (36, y+2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1, cv2.LINE_AA)
    y += 24

cv2.imwrite(OUT_OVERLAY, overlay)
print(f'Overlay saved to {OUT_OVERLAY}')

# Also save individual mask images per class for inspection
os.makedirs('mask_debug', exist_ok=True)
for i, (seg, cls) in enumerate(zip(mask_arrays, classes)):
    mask = (seg > 0.5).astype(np.uint8) * 255
    mask_resized = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
    path = os.path.join('mask_debug', f'mask_{i}_cls{int(cls)}.png')
    cv2.imwrite(path, mask_resized)
print('Saved individual masks in mask_debug/')
