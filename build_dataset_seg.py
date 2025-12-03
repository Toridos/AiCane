import os, json, zipfile, shutil, glob
from tqdm import tqdm

BASE = r"C:\SW_3_2\ai\AI_lab\data\floorplans\raw\01-1.정식개방데이터"
OUT_DIR = r"C:\SW_3_2\ai\AI_lab\data\floorplans\seg_filtered"
YOLO_BASE = r"C:\SW_3_2\ai\AI_lab\yolo_seg"

# Floorplan ZIPs (SPA/STR)
ZIP_LIST = [
    rf"{BASE}\Training\01.원천데이터\TS_STR_1.zip",
    rf"{BASE}\Training\02.라벨링데이터\TL_STR.zip",
    rf"{BASE}\Training\01.원천데이터\TS_SPA_1.zip",
    rf"{BASE}\Training\02.라벨링데이터\TL_SPA.zip",

    rf"{BASE}\Validation\01.원천데이터\VS_STR.zip",
    rf"{BASE}\Validation\02.라벨링데이터\VL_STR.zip",
    rf"{BASE}\Validation\01.원천데이터\VS_SPA.zip",
    rf"{BASE}\Validation\02.라벨링데이터\VL_SPA.zip",
]

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(YOLO_BASE, exist_ok=True)
os.makedirs(f"{YOLO_BASE}/images", exist_ok=True)
os.makedirs(f"{YOLO_BASE}/labels", exist_ok=True)

MAX_BYTES = 5 * 1024 * 1024 * 1024

def is_needed(name):
    name = name.lower()
    return name.endswith(".png") or name.endswith(".jpg") or name.endswith(".jpeg") or name.endswith(".json")

print("===== [1/3] Selective extraction =====")

for z in ZIP_LIST:
    used = 0
    if not os.path.exists(z):
        print("Missing:", z)
        continue
    with zipfile.ZipFile(z, "r") as zipf:
        for m in zipf.infolist():
            if not is_needed(m.filename):
                continue
            if used + m.file_size > MAX_BYTES:
                break
            zipf.extract(m, OUT_DIR)
            used += m.file_size

print("===== [2/3] JSON → YOLO conversion (seg only) =====")

MERGE_MAP = {
    11:0,   # wall
    9:1,    # door
    1:2, 13:2,14:2,15:2,16:2,17:2,18:2,19:2,20:2,22:2,  # rooms
    2:3,    # elevator hall
    3:4,    # stair
    23:5,   # elevator
}

EXCLUDE = [21,10,4,5,6,7,8]   # OCR 제거 + 비필요 객체들

json_list = glob.glob(f"{OUT_DIR}/**/*.json", recursive=True)

def norm(seg, w, h):
    xs=seg[0::2]; ys=seg[1::2]
    out=[]
    for x,y in zip(xs,ys):
        out.append(x/w); out.append(y/h)
    return out

for jp in tqdm(json_list):
    with open(jp,"r",encoding="utf-8") as f: data=json.load(f)

    img_info=data["images"][0]
    img_name=img_info["file_name"]
    w,h=img_info["width"],img_info["height"]

    # Locate image
    for cand in [
        img_name,
        img_name.replace(".PNG",".png"),
        img_name.replace(".png",".PNG"),
    ]:
        path=os.path.join(os.path.dirname(jp), cand)
        if os.path.exists(path):
            shutil.copy(path, f"{YOLO_BASE}/images/{os.path.basename(path)}")
            break

    out_txt = f"{YOLO_BASE}/labels/{img_name.rsplit('.', 1)[0]}.txt"
    with open(out_txt, "w") as F:
        for ann in data["annotations"]:
            cid = ann["category_id"]

            if cid in EXCLUDE:
                continue
            if cid not in MERGE_MAP:
                continue

            # segmentation 검사: 없거나 비어있으면 skip
            if "segmentation" not in ann:
                continue
            if not ann["segmentation"]:
                continue
            if not ann["segmentation"][0] or len(ann["segmentation"][0]) < 6:
                continue

            seg = ann["segmentation"][0]
            norm_seg = norm(seg, w, h)
            s = " ".join(f"{v:.6f}" for v in norm_seg)

            F.write(f"{MERGE_MAP[cid]} {s}\n")

print("===== [3/3] Train/Val split =====")

import random
IMG=f"{YOLO_BASE}/images"
LBL=f"{YOLO_BASE}/labels"

TRAIN_IMG=f"{YOLO_BASE}/images/train"
VAL_IMG=f"{YOLO_BASE}/images/val"
TRAIN_LBL=f"{YOLO_BASE}/labels/train"
VAL_LBL=f"{YOLO_BASE}/labels/val"

for p in [TRAIN_IMG,VAL_IMG,TRAIN_LBL,VAL_LBL]: os.makedirs(p, exist_ok=True)

images=glob.glob(f"{IMG}/*.*")
random.shuffle(images)
cut=int(len(images)*0.85)

def mv(lst, iout, lout):
    for p in lst:
        name=os.path.basename(p)
        lbl=name.rsplit('.',1)[0]+".txt"
        if os.path.exists(f"{LBL}/{lbl}"):
            shutil.copy(p, f"{iout}/{name}")
            shutil.copy(f"{LBL}/{lbl}", f"{lout}/{lbl}")

mv(images[:cut], TRAIN_IMG, TRAIN_LBL)
mv(images[cut:], VAL_IMG, VAL_LBL)

print("Dataset (SEG) build done!")
