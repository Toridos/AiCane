# route_core.py
import cv2
import numpy as np
import json
from pathlib import Path
import run_navigation as rn
from match_rooms import match_floor_rooms


# ------------------------------------------------------
# OCR + 방 좌표 계산
# ------------------------------------------------------
def compute_room_coords(imgpath, rstart, rend):
    texts = rn.run_ocr(imgpath)
    cleaned = match_floor_rooms(texts, rstart, rend, max_dist=5)
    return cleaned   # dict: {room_number: (x, y)}


# ------------------------------------------------------
# 벽 mask → grid
# ------------------------------------------------------
def extract_red_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 60, 40])
    upper1 = np.array([25, 255, 255])
    lower2 = np.array([150, 60, 40])
    upper2 = np.array([180, 255, 255])
    m1 = cv2.inRange(hsv, lower1, upper1)
    m2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(m1, m2)
    return (mask > 0).astype(np.uint8)   # 1=wall


# ------------------------------------------------------
# 계단
# ------------------------------------------------------
def extract_blue_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([80, 80, 40])
    upper = np.array([130, 255, 255])
    return cv2.inRange(hsv, lower, upper)


def find_stairs(mask):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pts=[]
    for c in cnts:
        M=cv2.moments(c)
        if M["m00"]>0:
            cx=int(M["m10"]/M["m00"])
            cy=int(M["m01"]/M["m00"])
            pts.append((cx,cy))
    return pts


# ------------------------------------------------------
# BFS (단층)
# ------------------------------------------------------
from collections import deque

def bfs_single_floor(grid, start, goal):
    H, W = grid.shape
    sx, sy = start
    gx, gy = goal
    
    Q = deque([(sx,sy)])
    visited = {(sx,sy)}
    parent = {}

    while Q:
        x,y = Q.popleft()

        if (x,y) == (gx,gy):
            path=[]
            cur=(gx,gy)
            while cur in parent:
                path.append(cur)
                cur=parent[cur]
            path.append((sx,sy))
            path.reverse()
            return path

        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny = x+dx, y+dy
            if 0<=nx<W and 0<=ny<H and grid[ny,nx]==0:
                if (nx,ny) not in visited:
                    visited.add((nx,ny))
                    parent[(nx,ny)] = (x,y)
                    Q.append((nx,ny))

    return None
