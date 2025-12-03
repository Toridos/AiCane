import os
import sys
from pathlib import Path
import numpy as np
import cv2

# ensure project root on path
proj_root = str(Path(__file__).resolve().parents[1])
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from run_navigation import run_seg

IMAGE = r"C:\SW_3_2\toridos\AiCane\s4-1\s4-1_floor1.png"
OUT = os.path.join(str(Path(__file__).resolve().parents[1]), 'outputs', 'seg_inspect')
os.makedirs(OUT, exist_ok=True)

def main():
    print('[+] Running segmentation on', IMAGE)
    masks, boxes, (orig_w, orig_h), (new_w, new_h) = run_seg(IMAGE)
    mask_arr = masks.data.cpu().numpy()
    classes = boxes.cls.cpu().numpy().astype(int)

    print('orig_size=', (orig_w, orig_h), 'mask_size=', (new_w, new_h))

    unique = sorted(set(int(c) for c in classes))
    print('Detected class indices:', unique)

    # Count pixels per class
    counts = {}
    for seg_np, cls in zip(mask_arr, classes):
        cls_i = int(cls)
        cnt = int(np.sum(seg_np > 0.5))
        counts.setdefault(cls_i, 0)
        counts[cls_i] += cnt

    for k in sorted(counts.keys()):
        print(f'  class {k}: {counts[k]} pixels')

    # save per-class masks and a color overlay
    color_map = {
        0: (0,0,255),    # class 0 -> red (wall?)
        1: (0,255,0),    # class 1 -> green
        2: (255,0,0),    # class 2 -> blue (rooms?)
        3: (0,255,255),  # class 3 -> yellow
    }

    # base empty overlay (mask resolution)
    overlay_mask = np.zeros((new_h, new_w, 3), dtype=np.uint8)

    for idx, (seg_np, cls) in enumerate(zip(mask_arr, classes)):
        cls_i = int(cls)
        mask_bool = seg_np > 0.5
        if not mask_bool.any():
            continue
        color = color_map.get(cls_i, (128,128,128))
        # paint color where mask is true
        for c in range(3):
            overlay_mask[:, :, c][mask_bool] = color[c]

        # save per-instance mask upsampled to original size
        mask_up = (mask_bool.astype('uint8') * 255)
        mask_up = cv2.resize(mask_up, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        out_mask_file = os.path.join(OUT, f'class_{cls_i}_inst{idx}_mask.png')
        cv2.imwrite(out_mask_file, mask_up)
        print('  wrote', out_mask_file)

    # composite overlay onto original image
    overlay_up = cv2.resize(overlay_mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
    img = cv2.imread(IMAGE)
    if img is None:
        print('[!] Could not read image', IMAGE)
        return
    over = img.copy()
    alpha = 0.5
    colored = over.copy()
    mask_nonzero = overlay_up.sum(axis=2) > 0
    colored[mask_nonzero] = (overlay_up[mask_nonzero] * 0.7 + over[mask_nonzero] * 0.3).astype('uint8')
    out_overlay = os.path.join(OUT, 'seg_classes_overlay.png')
    cv2.imwrite(out_overlay, colored)
    print('[+] Wrote overlay:', out_overlay)

    # Save raw combined wall mask (class 0 if present)
    wall_mask = None
    for seg_np, cls in zip(mask_arr, classes):
        if int(cls) == 0:
            if wall_mask is None:
                wall_mask = seg_np > 0.5
            else:
                wall_mask = np.logical_or(wall_mask, seg_np > 0.5)

    if wall_mask is None:
        print('[!] No class 0 (wall) masks found')
    else:
        wall_up = (wall_mask.astype('uint8') * 255)
        wall_up = cv2.resize(wall_up, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        out_wall = os.path.join(OUT, 'wall_combined_mask.png')
        cv2.imwrite(out_wall, wall_up)
        print('[+] Wrote wall combined mask:', out_wall)

if __name__ == '__main__':
    main()
