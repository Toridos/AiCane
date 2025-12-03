import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from match_rooms import match_floor_rooms
import run_navigation as rn
import json

images = [
    (r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-1.png", 101, 118),
    (r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-2.png", 201, 223),
    (r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-3.png", 301, 332),
]

outdir = Path('outputs/match_demo')
outdir.mkdir(parents=True, exist_ok=True)

for imgpath, start, end in images:
    print(f"\n--- Processing {Path(imgpath).name} expected {start}-{end} ---")
    texts = rn.run_ocr(imgpath)
    print(f"Detected OCR tokens: {len(texts)}")
    cleaned = match_floor_rooms(texts, start, end, max_dist=2)
    print(f"Corrected rooms: {len(cleaned)} entries")
    # print some sample
    keys = sorted(cleaned.keys())
    for k in keys:
        x,y = cleaned[k]
        print(f" {k} -> ({x},{y})")
    # write json
    outf = outdir / f"cleaned_{Path(imgpath).stem}.json"
    with open(outf, 'w', encoding='utf-8') as f:
        json.dump({str(k): cleaned[k] for k in keys}, f, ensure_ascii=False, indent=2)
    print('Wrote', outf)
    # create visual overlay
    try:
        import cv2
        img = cv2.imread(imgpath)
        if img is not None:
            # draw cleaned room numbers
            for k in keys:
                x,y = cleaned[k]
                # clamp
                h,w = img.shape[:2]
                xx = max(0, min(w-1, int(x)))
                yy = max(0, min(h-1, int(y)))
                # circle
                cv2.circle(img, (xx, yy), 10, (0, 255, 0), -1)
                # label
                cv2.putText(img, str(k), (xx+12, yy+6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
            # also draw original OCR tokens in blue
            for tok, (tx,ty) in texts.items():
                try:
                    txi = int(tx); tyi = int(ty)
                    cv2.circle(img, (txi, tyi), 4, (255,0,0), -1)
                except Exception:
                    pass
            ovf = outdir / f"overlay_{Path(imgpath).stem}.png"
            cv2.imwrite(str(ovf), img)
            print('Wrote overlay', ovf)
    except Exception as e:
        print('[!] Failed to write overlay:', e)

print('\nDone.')
