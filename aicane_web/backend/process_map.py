import cv2
import numpy as np
import json
import os

# optional OCR
try:
    import pytesseract
    _HAS_TESSERACT = True
except Exception:
    pytesseract = None
    _HAS_TESSERACT = False

def process_floorplan(path):

    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold
    _, bin_img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # remove text noise
    kernel = np.ones((3,3), np.uint8)
    clean = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=2)

    # walls
    edges = cv2.Canny(clean, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    wall_map = np.zeros_like(clean)
    cv2.drawContours(wall_map, contours, -1, 255, thickness=5)

    # occupancy grid
    grid = (wall_map == 255).astype(int)
    grid = 1 - grid

    grid_path = path.replace(".png", "_grid.npy")
    np.save(grid_path, grid)

    room_positions = {}
    ocr_texts = []

    # If pytesseract is available, attempt to detect numeric room labels
    if _HAS_TESSERACT:
        try:
            # prepare grayscale & slightly blurred image for OCR
            gray_for_ocr = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray_for_ocr = cv2.medianBlur(gray_for_ocr, 3)

            # Use a relatively low threshold to keep text
            _, th = cv2.threshold(gray_for_ocr, 200, 255, cv2.THRESH_BINARY)

            # find contours that might be text blobs (small to medium sized)
            cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            candidates = []
            h_img, w_img = th.shape[:2]
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                # ignore extremely large contours (walls) and extremely small noise
                if w < 8 or h < 8:
                    continue
                if w > w_img * 0.5 or h > h_img * 0.5:
                    continue
                # accept candidate
                candidates.append((x, y, w, h))

            # sort small-to-large so digits are more isolated first
            candidates = sorted(candidates, key=lambda r: (r[1], r[0], r[2] * r[3]))

            # iterate candidates and run tesseract with digit whitelist
            debug_img = img.copy()
            for (x, y, w, h) in candidates:
                pad = 4
                x0 = max(0, x - pad)
                y0 = max(0, y - pad)
                x1 = min(w_img, x + w + pad)
                y1 = min(h_img, y + h + pad)
                crop = gray_for_ocr[y0:y1, x0:x1]

                # scale up small crops to improve OCR
                scale = 2 if max(w, h) < 40 else 1
                if scale > 1:
                    crop = cv2.resize(crop, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

                config = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789"
                text = pytesseract.image_to_string(crop, config=config)
                text = text.strip()
                # keep only digits
                import re

                digits = re.sub(r"[^0-9]", "", text)

                # compute centroid in original image coordinates
                cx = int((x0 + x1) / 2)
                cy = int((y0 + y1) / 2)

                # record raw OCR result (even if empty digits)
                orec = {"raw": text, "digits": digits, "bbox": [x0, y0, x1, y1], "centroid": [cx, cy]}
                ocr_texts.append(orec)
                print("OCR candidate:", orec)

                if digits == "":
                    # draw faint box for non-digit detections
                    cv2.rectangle(debug_img, (x0, y0), (x1, y1), (0, 0, 255), 1)
                    continue
                try:
                    room_num = str(int(digits))
                except Exception:
                    cv2.rectangle(debug_img, (x0, y0), (x1, y1), (0, 0, 255), 1)
                    continue

                # map to (x, y) integer tuple
                room_positions[room_num] = (cx, cy)
                # draw box and label on debug image
                cv2.rectangle(debug_img, (x0, y0), (x1, y1), (0, 255, 0), 2)
                cv2.putText(debug_img, room_num, (x0, y0 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # save debug image and json
            try:
                os.makedirs("uploads", exist_ok=True)
                cv2.imwrite("uploads/ocr_debug.png", debug_img)
                json.dump(ocr_texts, open("uploads/ocr_debug.json", "w"), indent=2, ensure_ascii=False)
            except Exception:
                pass

        except Exception as e:
            # OCR failed — fall back to placeholders later
            print("OCR detection failed:", e)

    # ensure FrontDoor exists: if 103 and 104 both present use midpoint
    if "FrontDoor" not in room_positions:
        if "103" in room_positions and "104" in room_positions:
            x1, y1 = room_positions["103"]
            x2, y2 = room_positions["104"]
            room_positions["FrontDoor"] = (int((x1 + x2) / 2), int((y1 + y2) / 2))
        else:
            room_positions.setdefault("FrontDoor", (140, 80))

    # save for navigation (both project root & uploads)
    try:
        json.dump(room_positions, open("room_positions.json", "w"), indent=4)
    except Exception:
        pass
    try:
        os.makedirs("uploads", exist_ok=True)
        json.dump(room_positions, open("uploads/room_positions.json", "w"), indent=4)
    except Exception:
        pass

    return grid_path, room_positions, ocr_texts
