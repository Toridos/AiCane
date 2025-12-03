import cv2
import numpy as np


def preprocess_floorplan(path):
    """
    Improved preprocessing for floorplans.

    - Read color image, convert to grayscale
    - Contrast limited adaptive histogram equalization (CLAHE)
    - Median blur to reduce salt-and-pepper noise
    - Adaptive threshold (binary inverted) to highlight walls/text
    - Morphological open to remove small noise, close to fill characters
    - Return cleaned binary image (walls + text) as uint8 (0/255)
    """
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"preprocess: file not found: {path}")

    # grayscale + contrast enhancement
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # denoise a bit while keeping edges
    denoised = cv2.medianBlur(gray, 3)

    # adaptive threshold - invert so walls/text become white
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 8
    )

    # morphological operations to clean tiny noise and join text strokes
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_large, iterations=1)

    # optionally thicken lines to make segmentation more robust
    walls = cv2.dilate(closed, np.ones((3, 3), np.uint8), iterations=1)

    # save a preview to uploads for debugging (if uploads exists)
    try:
        import os

        os.makedirs("uploads", exist_ok=True)
        cv2.imwrite("uploads/preprocessed.png", walls)
    except Exception:
        # ignore filesystem problems in library function
        pass

    return walls
