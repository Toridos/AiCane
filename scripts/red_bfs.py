import sys
import cv2
import json
import numpy as np
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import run_navigation as rn
from match_rooms import match_floor_rooms


# ==========================================================
#  COLOR MASKS
# ==========================================================

def extract_red_mask(img, kernel_size=9, min_area=400):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 60, 40])
    upper1 = np.array([25, 255, 255])
    lower2 = np.array([150, 60, 40])
    upper2 = np.array([180, 255, 255])
    m1 = cv2.inRange(hsv, lower1, upper1)
    m2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(m1, m2)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    mask = cv2.dilate(mask, k)

    # remove small components
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(out, [c], -1, 255, -1)
    return out


def extract_blue_mask(img, kernel_size=9, min_area=400):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([80, 80, 40])
    upper = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    mask = cv2.dilate(mask, k)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(out, [c], -1, 255, -1)
    return out


def mask_to_grid(mask):
    g = np.zeros(mask.shape, dtype=np.uint8)
    g[mask > 0] = 1
    return g


# ==========================================================
#  MULTI-FLOOR GRAPH + BFS
# ==========================================================

def find_stair_centroids(blue_mask):
    cnts, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pts = []
    for c in cnts:
        M = cv2.moments(c)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        pts.append((cx, cy))
    return pts


def connect_stairs(stairs_f1, stairs_f2):
    """Return list of matched stair coordinate pairs ((x1,y1),(x2,y2)).

    Matches each stair in stairs_f1 to the nearest in stairs_f2. If no stairs
    found on one floor, returns empty list.
    """
    pairs = []
    if not stairs_f1 or not stairs_f2:
        return pairs

    used = set()
    for a in stairs_f1:
        best = None
        best_d = None
        best_j = None
        for j, b in enumerate(stairs_f2):
            if j in used:
                continue
            d = (a[0]-b[0])**2 + (a[1]-b[1])**2
            if best_d is None or d < best_d:
                best_d = d
                best = b
                best_j = j
        if best is not None:
            pairs.append((a, best))
            used.add(best_j)
    return pairs


# Multi-floor BFS
def bfs_multifloor(grids, stairs_connect, start, goal):
    """
    grids = { floor_number: binary_grid }
    stairs_connect = dict: floor → list of ((x1,y1),(x2,y2)) to next floor
    start=(f,x,y), goal=(f,x,y)
    """
    from collections import deque

    Q = deque([start])
    visited = set([start])
    parent = {}

    H = grids[start[0]].shape[0]
    W = grids[start[0]].shape[1]

    while Q:
        f, x, y = Q.popleft()
        if (f,x,y)==goal:
            # reconstruct
            path=[]
            cur=(f,x,y)
            while cur in parent:
                path.append(cur)
                cur=parent[cur]
            path.append(start)
            return path[::-1]

        # neighbors same floor
        grid = grids[f]
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny = x+dx, y+dy
            if 0<=nx<W and 0<=ny<H:
                if grid[ny,nx]==0:  # free
                    nxt=(f,nx,ny)
                    if nxt not in visited:
                        visited.add(nxt)
                        parent[nxt]=(f,x,y)
                        Q.append(nxt)

        # stair edges
        if f in stairs_connect:
            for (sx,sy),(tx,ty) in stairs_connect[f]:
                # if at (sx,sy), go to next floor (f+1)
                if abs(x-sx)<=2 and abs(y-sy)<=2:
                    nxt=(f+1, tx, ty)
                    if nxt not in visited:
                        visited.add(nxt)
                        parent[nxt]=(f,x,y)
                        Q.append(nxt)

    return None


# ==========================================================
#  MAIN PIPELINE
# ==========================================================

def run_all_floors(image_info, outdir):
    """
    image_info = [
       (path, start_room, end_room, floor_number)
    ]
    returns:
        floors = {floor: { 'cleaned': dict, 'grid': grid, 'stairs': [(cx,cy)...], 'img':img }}
    """
    floors = {}

    for imgpath, rstart, rend, f in image_info:
        print(f"\n=== Floor {f}: {imgpath} ===")
        img = cv2.imread(imgpath)
        if img is None:
            print("[!] Cannot load", imgpath)
            continue

        # OCR
        texts = rn.run_ocr(imgpath)
        cleaned = match_floor_rooms(texts, rstart, rend, max_dist=2)

        # Walls
        red_mask = extract_red_mask(img)
        grid = mask_to_grid(red_mask)

        # Stairs
        blue_mask = extract_blue_mask(img)
        stairs = find_stair_centroids(blue_mask)

        floors[f] = dict(
            cleaned=cleaned,
            grid=grid,
            stairs=stairs,
            img=img,
            texts=texts,
            red_mask=red_mask,
            blue_mask=blue_mask,
            imgpath=imgpath
        )
    return floors


# ==========================================================
#  FULL MULTIFLOOR PATH → from 101 → 307
# ==========================================================

def visualize_multifloor_path(floors, path, outdir):
    """Draw overlay for each floor."""
    for f, data in floors.items():
        img = data["img"].copy()
        grid = data["grid"]
        red_mask = data["red_mask"]
        texts = data["texts"]
        cleaned = data["cleaned"]

        h,w = img.shape[:2]

        # red mask overlay
        red = np.zeros_like(img); red[:,:,2]=255
        a=(red_mask>0).astype(np.float32)*0.4
        a3=np.stack([a,a,a],2)
        img=(img*(1-a3)+red*a3).astype(np.uint8)

        # cleaned rooms
        for rn,(x,y) in cleaned.items():
            cv2.circle(img,(int(x),int(y)),8,(0,255,0),-1)
            cv2.putText(img,str(rn),(int(x)+10,int(y)),
                cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),2)

        # path: draw only nodes on this floor
        pts=[]
        for (ff,xx,yy) in path:
            if ff==f:
                pts.append((int(xx),int(yy)))
        for p in pts:
            cv2.circle(img,p,3,(255,0,0),-1)
        if len(pts)>=2:
            cv2.polylines(img,[np.array(pts)],False,(255,0,0),2)

        # write
        outpath=outdir/f"overlay_floor_{f}.png"
        cv2.imwrite(str(outpath),img)
        print("[✔] wrote",outpath)


# ==========================================================
# ENTRY EXAMPLE (101 → 307)
# ==========================================================

if __name__=="__main__":

    outdir=Path("outputs/multifloor_route")
    outdir.mkdir(parents=True,exist_ok=True)

    images = [
        (r"C:\SW_3_2\toridos\AiCane\static\s4_1-1.png", 101,118, 1),
        (r"C:\SW_3_2\toridos\AiCane\static\s4_1-2.png", 201,223, 2),
        (r"C:\SW_3_2\toridos\AiCane\static\s4_1-3.png", 301,332, 3),
    ]

    floors = run_all_floors(images, outdir)

    # ------------------------------
    # build stair connections
    # ------------------------------
    stairs_connect = {}
    for f in [1,2]:
        s1 = floors[f]["stairs"]
        s2 = floors[f+1]["stairs"]
        print(f"Floor {f} stairs detected: {s1}")
        print(f"Floor {f+1} stairs detected: {s2}")
        pairs = connect_stairs(s1, s2)
        print(f"Matched stair pairs between floor {f} -> {f+1}: {pairs}")

        # carve small openings around matched stair centroids so BFS can traverse
        # convert red-mask grid (1=wall) to ensure cells near stairs are free (0)
        grid_f = floors[f]["grid"]
        grid_nf = floors[f+1]["grid"]
        for (sx,sy),(tx,ty) in pairs:
            r = 3
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    ax = int(sx+dx)
                    ay = int(sy+dy)
                    bx = int(tx+dx)
                    by = int(ty+dy)
                    H,W = grid_f.shape
                    if 0<=ax<W and 0<=ay<H:
                        grid_f[ay,ax] = 0
                    H2,W2 = grid_nf.shape
                    if 0<=bx<W2 and 0<=by<H2:
                        grid_nf[by,bx] = 0

        stairs_connect[f] = pairs

    # ------------------------------
    # START = 101호 on floor 1
    # GOAL  = 307호 on floor 3
    # ------------------------------

    sx,sy = floors[1]["cleaned"][101]
    gx,gy = floors[3]["cleaned"][307]

    # Multi-floor BFS
    path = bfs_multifloor(
        grids = {f: floors[f]["grid"] for f in floors},
        stairs_connect = stairs_connect,
        start = (1,int(sx),int(sy)),
        goal  = (3,int(gx),int(gy))
    )

    if not path:
        print("[!] No path found")
        sys.exit()

    print("[✔] PATH FOUND (multi-floor):", len(path))

    # Save global path
    with open(outdir/"path_multifloor.txt","w") as f:
        for (ff,x,y) in path:
            f.write(f"{ff},{x},{y}\n")

    # visualize
    visualize_multifloor_path(floors, path, outdir)

    print("\nDone.")
