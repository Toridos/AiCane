import run_navigation as rn
from pathlib import Path

imgs = [r'C:\SW_3_2\toridos\AiCane\s4-1\s4_1-1.png']
img = imgs[0]
print('Running inspection on', img)
# segmentation and sizes
masks, boxes, orig_size, new_size = rn.run_seg(img)
orig_w, orig_h = orig_size
new_w, new_h = new_size
red = rn.extract_red_mask_from_image(img)
# build grids
grid_m, room_m = rn.grid_from_masks_and_optional_red(masks, boxes, red_mask=red, wall_dilate=3, clearance_px=None, use_red_only=False)
grid_r, room_r = rn.grid_from_masks_and_optional_red(masks, boxes, red_mask=red, wall_dilate=1, clearance_px=None, use_red_only=True)
# OCR
texts = rn.run_ocr(img)
print('Detected texts:', list(texts.keys())[:30])
start='101호'
goal='110호'
if start not in texts or goal not in texts:
    print('Start or goal not detected by OCR')
    raise SystemExit
# get center points
sp = rn.find_room(start, texts)
gp = rn.find_room(goal, texts)
print('Found centers (orig coords):', sp, gp)
# scale to grid
ss = (int(sp[0]*(new_w/orig_w)), int(sp[1]*(new_h/orig_h)))
gs = (int(gp[0]*(new_w/orig_w)), int(gp[1]*(new_h/orig_h)))
print('Scaled to grid coords:', ss, gs)
# BFS
path_m = rn.bfs(grid_m, ss, gs)
path_r = rn.bfs(grid_r, ss, gs)

def check_path(grid, path):
    if path is None:
        return None
    bad = [(x,y) for (x,y) in path if grid[y][x]==1]
    return bad

bad_m = check_path(grid_m, path_m)
bad_r = check_path(grid_r, path_r)
print('Merged grid: path_len=', None if path_m is None else len(path_m), 'bad_cells=', None if bad_m is None else len(bad_m))
print('Red-only grid: path_len=', None if path_r is None else len(path_r), 'bad_cells=', None if bad_r is None else len(bad_r))
if path_m:
    print('Merged path sample:', path_m[:10])
if bad_m:
    print('Examples of bad merged path points (on walls):', bad_m[:10])
if path_r:
    print('Red-only path sample:', path_r[:10])
if bad_r:
    print('Examples of bad red-only path points (on walls):', bad_r[:10])

# save a debug overlay showing path over wall overlay
from pathlib import Path
out = Path('C:/SW_3_2/toridos/AiCane/outputs/inspect_path_debug.png')
print('grid_m at start,goal =', grid_m[ss[1]][ss[0]], grid_m[gs[1]][gs[0]])
print('grid_r at start,goal =', grid_r[ss[1]][ss[0]], grid_r[gs[1]][gs[0]])
# write a wall-overlay from merged grid for visual check
out_wall = Path('C:/SW_3_2/toridos/AiCane/outputs/inspect_wall_overlay.png')
rn.draw_wall_overlay(img, grid_m, str(out_wall))
print('Wrote wall overlay to', out_wall)
# For debug overlay of path, use draw_debug_overlay signature: floors is list of dicts
floors = [{'path': img, 'grid': grid_m, 'texts': texts}]
# draw_debug_overlay expects floors list, index, start_scaled, goal_scaled, portals, out_path
try:
    rn.draw_debug_overlay(floors, 0, ss, gs, portals=[], out_path=str(out))
    print('Wrote debug overlay to', out)
except Exception as e:
    print('draw_debug_overlay failed:', e)
print('Wrote debug overlay to', out)
