import sys
from pathlib import Path

# ensure repo root is on sys.path so run_navigation can be imported
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import run_navigation as rn

imgs = [
  r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-1.png",
  r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-2.png",
  r"C:\SW_3_2\toridos\AiCane\s4-1\s4_1-3.png",
]

# Use the robust red extraction and prefer red-only walls to avoid holes
res = rn.multi_floor_path(imgs, use_red=True, use_blue=True, use_red_only=True, wall_dilate=1, clearance_px=None, stair_match_dist=140)
print(res)
