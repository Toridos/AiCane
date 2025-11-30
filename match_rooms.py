# ---------------------------------------------------------------
#  Smart Room Number Matching (OCR → Clean Room Numbers)
#  - Supports OCR noise like 2213, 2023, 2221, 303초, 218소 등
#  - Infers missing rooms (205호, 217호 등)
#  - Handles special structure (118, 223, 332 in the middle)
#  - Handles clockwise room number increase
# ---------------------------------------------------------------

import re
import numpy as np
from difflib import SequenceMatcher


# ===============================================================
# 0. Utility Functions
# ===============================================================

def levenshtein(a, b):
    """Compute Levenshtein edit distance."""
    a = str(a)
    b = str(b)
    dp = [[i+j if i*j==0 else 0 for j in range(len(b)+1)]
          for i in range(len(a)+1)]
    for i in range(1, len(a)+1):
        dp[i][0] = i
    for j in range(1, len(b)+1):
        dp[0][j] = j

    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + (a[i-1] != b[j-1])
            )
    return dp[len(a)][len(b)]


# ===============================================================
# 1. OCR → Candidate Room Numbers
# ===============================================================

def extract_numeric_candidates(raw):
    """
    raw: OCR detected string (like '2213', '218소', '203호', '303초', 'L', '거호')
    returns list of possible numeric room candidates
    """
    raw = raw.replace(" ", "")
    nums = re.findall(r"\d+", raw)
    if not nums:
        return []

    n = nums[0]

    # Case 1: 정상 3자리 숫자
    if len(n) == 3:
        return [int(n)]

    # Case 2: 4자리 → floor + room parsing (2213 → 221/213)
    if len(n) == 4:
        f = n[0]  # floor digit
        last3 = n[1:]     # 2xx?
        last2 = n[2:]     # xx?
        cand = []
        if len(last3) == 3:
            cand.append(int(f + last3))  # ex: 2213 → 221
        if len(last2) == 2:
            cand.append(int(f + last2))  # ex: 2213 → 213
        return list(set(cand))

    # Case 3: 2자리 or others (rare)
    if len(n) == 2:
        # If floor known externally, handle later
        return [int(n)]

    return []


# ===============================================================
# 2. Filter by expected floor range
# ===============================================================

def filter_floor_range(candidates, start, end):
    return [c for c in candidates if start <= c <= end]


# ===============================================================
# 3. Sort OCR results by x coordinate (clockwise increasing)
# ===============================================================

def sort_by_x(text_positions):
    """
    text_positions: dict { 'raw_text': (x,y) }
    returns list of (raw, x, y) sorted left→right
    """
    arr = []
    for t, (x, y) in text_positions.items():
        arr.append((t, int(x), int(y)))
    arr.sort(key=lambda x: x[1])
    return arr


# ===============================================================
# 4. Infer missing room numbers by position
# ===============================================================

def infer_missing_positions(sorted_rooms, cleaned_map, start, end):
    """
    sorted_rooms: list [(room_number, x, y)] sorted by x
    cleaned_map: dict room_number → (x,y)
    start ~ end: expected room range
    """

    final_map = dict(cleaned_map)

    # Special mid-room exceptions:
    special_rooms = {
        # (lower, upper, special)
        1: (112, 113, 118),
        2: (204, 205, 223),
        3: (306, 307, 332),
    }

    # Determine floor
    floor = start // 100

    # If special room missing → generate its position
    if floor in special_rooms:
        lo, hi, special = special_rooms[floor]
        if special not in final_map and lo in final_map and hi in final_map:
            x_lo, y_lo = final_map[lo]
            x_hi, y_hi = final_map[hi]
            sx = (x_lo + x_hi) // 2
            sy = (y_lo + y_hi) // 2
            final_map[special] = (sx, sy)

    # Fill sequential rooms by equal spacing
    seq = [r for r in range(start, end+1)]

    # Create list of existing rooms in order
    existing = [r for r in seq if r in final_map]

    if not existing:
        return final_map

    for i in range(len(existing)-1):
        a = existing[i]
        b = existing[i+1]

        dx = final_map[b][0] - final_map[a][0]
        dy = final_map[b][1] - final_map[a][1]
        gap = b - a  # number difference

        if gap <= 1:
            continue

        # fill missing rooms between
        for k, rn in enumerate(range(a+1, b)):
            ratio = (k+1) / gap
            x = int(final_map[a][0] + dx * ratio)
            y = int(final_map[a][1] + dy * ratio)
            if rn not in final_map:
                final_map[rn] = (x, y)

    return final_map


# ===============================================================
# 5. Main Room Matching (OCR → cleaned rooms)
# ===============================================================

def match_floor_rooms(text_positions, start, end, max_dist=2):
    """
    Complete OCR-based room detection + correction + inference
    """
    # 1) Extract numeric candidates
    candidates = []  # (room_number_candidate, raw_text, (x,y))
    for raw, (x, y) in text_positions.items():
        num_cands = extract_numeric_candidates(raw)
        if not num_cands:
            continue

        # Filter by floor range
        num_cands = filter_floor_range(num_cands, start, end)
        for n in num_cands:
            candidates.append((n, raw, (x, y)))

    # 2) If exact match exists → use it with priority
    cleaned = {}
    for rn, raw, (x, y) in candidates:
        if rn not in cleaned:
            cleaned[rn] = (x, y)

    # 3) Match OCR noise to valid room numbers by Levenshtein
    valid_range = list(range(start, end+1))

    for exp in valid_range:
        if exp in cleaned:
            continue
        # Find closest candidate
        best = None
        best_d = 999
        for rn, raw, (x, y) in candidates:
            d = levenshtein(str(exp), str(rn))
            if d < best_d:
                best = (rn, raw, (x, y))
                best_d = d
        if best and best_d <= max_dist:
            cleaned[exp] = best[2]

    # 4) Sort by x for consistent ordering
    sorted_raw = sort_by_x({str(k): v for k, v in cleaned.items()})
    sorted_rooms = [(int(raw), x, y) for raw, x, y in sorted_raw]

    # 5) Infer missing rooms (205, 217, etc)
    final_map = infer_missing_positions(sorted_rooms, cleaned, start, end)

    return final_map
