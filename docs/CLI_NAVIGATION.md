# CLI: Navigation pipeline

Run the navigation pipeline non-interactively from the command line.

Example:

```powershell
.\.venv\Scripts\python.exe run_navigation.py --image "<path_to_image>" --start "START_TEXT" --goal "GOAL_TEXT" --dilate 3 --clearance 9
```

- `--dilate`: morphological dilation radius (mask pixels) applied to wall masks.
- `--clearance`: distance-transform clearance in mask pixels; blocks cells within this many pixels of a wall.

If `--start` or `--goal` are omitted, the script falls back to interactive selection from detected OCR texts.
