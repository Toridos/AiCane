import os, json, zipfile, shutil, glob
from tqdm import tqdm

###############################################################
# 경로 설정
###############################################################

BASE = r"C:\SW_3_2\ai\AI_lab\data\floorplans\raw\01-1.정식개방데이터"
OUT_DIR = r"C:\SW_3_2\ai\AI_lab\data\floorplans\ocr_filtered"
YOLO_BASE = r"C:\SW_3_2\ai\AI_lab\yolo_ocr"

OCR_ZIPS = [
    rf"{BASE}\Training\01.원천데이터\TS_OCR_1.zip",
    rf"{BASE}\Training\02.라벨링데이터\TL_OCR.zip",
    rf"{BASE}\Validation\01.원천데이터\VS_OCR.zip",
    rf"{BASE}\Validation\02.라벨링데이터\VL_OCR.zip",
]

###############################################################
# 준비
###############################################################

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(f"{YOLO_BASE}/images", exist_ok=True)
os.makedirs(f"{YOLO_BASE}/labels", exist_ok=True)

MAX_BYTES = 4 * 1024 * 1024 * 1024

def is_needed(name):
    name = name.lower()
    return name.endswith(".json") or name.endswith(".png") or name.endswith(".jpg") or name.endswith(".jpeg")

###############################################################
# 1) ZIP selective extract
###############################################################

print("===== [1/3] Extract OCR ZIP =====")

for z in OCR_ZIPS:
    if not os.path.exists(z):
        print("❌ Not found:", z)
        continue
    used = 0
    with zipfile.ZipFile(z, "r") as zipf:
        for m in zipf.infolist():
            if not is_needed(m.filename):
                continue
            if used + m.file_size > MAX_BYTES:
                break
            zipf.extract(m, OUT_DIR)
            used += m.file_size

###############################################################
# 2) JSON → YOLO Detection (OCR only)
###############################################################

print("===== [2/3] JSON → YOLO OCR conversion =====")

json_list = glob.glob(f"{OUT_DIR}/**/*.json", recursive=True)

for jp in tqdm(json_list):
    with open(jp, "r", encoding="utf-8") as f:
        data = json.load(f)

    img_info = data["images"][0]
    img_name = img_info["file_name"]
    W, H = img_info["width"], img_info["height"]

    # 이미지 찾기
    src_img = None
    for cand in [img_name, img_name.replace(".PNG",".png"), img_name.replace(".png",".PNG")]:
        p = os.path.join(os.path.dirname(jp), cand)
        if os.path.exists(p):
            src_img = p
            break
    if src_img is None:
        continue

    shutil.copy(src_img, f"{YOLO_BASE}/images/{os.path.basename(src_img)}")

    out_txt = f"{YOLO_BASE}/labels/{img_name.rsplit('.',1)[0]}.txt"
    with open(out_txt, "w") as F:
        for ann in data["annotations"]:
            if ann["category_id"] != 21:
                continue

            x, y, w, h = ann["bbox"]
            xc = (x + w/2) / W
            yc = (y + h/2) / H
            wn = w / W
            hn = h / H

            F.write(f"0 {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n")

###############################################################
# 3) Train/Val split
###############################################################

print("===== [3/3] Train/Val split =====")

import random

IMG = f"{YOLO_BASE}/images"
LBL = f"{YOLO_BASE}/labels"

TRAIN_IMG = f"{IMG}/train"
VAL_IMG = f"{IMG}/val"
TRAIN_LBL = f"{LBL}/train"
VAL_LBL = f"{LBL}/val"

for p in [TRAIN_IMG, VAL_IMG, TRAIN_LBL, VAL_LBL]:
    os.makedirs(p, exist_ok=True)

images = glob.glob(f"{IMG}/*.*")
random.shuffle(images)
cut = int(len(images)*0.85)

def mv(lst, iout, lout):
    for p in lst:
        name = os.path.basename(p)
        lbl = name.rsplit('.',1)[0]+".txt"
        if os.path.exists(f"{LBL}/{lbl}"):
            shutil.copy(p, f"{iout}/{name}")
            shutil.copy(f"{LBL}/{lbl}", f"{lout}/{lbl}")

mv(images[:cut], TRAIN_IMG, TRAIN_LBL)
mv(images[cut:], VAL_IMG, VAL_LBL)

print("OCR dataset build complete!")
