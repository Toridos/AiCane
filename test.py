import os
import glob
import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import easyocr
import json
import re
from ultralytics import YOLO
import cv2

model = YOLO(r"C:\SW_3_2\toridos\AiCane\runs\segment\train7\weights\best.pt")
res = model(r"C:\SW_3_2\ai\AI_lab\yolo_dataset\images\APT_FP_OCR_230087881.PNG")[0]

res.save(filename="seg_debug.png")
