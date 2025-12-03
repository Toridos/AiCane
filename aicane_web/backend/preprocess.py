import cv2
import numpy as np

def preprocess_floorplan(path):
    img = cv2.imread(path)

    # 1) 그레이 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2) 가우시안 블러 → 노이즈 제거
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3) Adaptive Threshold → 컬러든 흑백이든 robust
    bin_img = cv2.adaptiveThreshold(
        blur, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        25, 2
    )

    # 4) 벽 강화 (두껍게)
    kernel = np.ones((5,5), np.uint8)
    walls = cv2.dilate(bin_img, kernel, iterations=2)

    # 5) 글자 제거 → 작은 요소 지우기
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(walls)
    min_area = 200  # 작은 아이콘, 글자 제거
    cleaned = np.zeros_like(walls)

    for i in range(1, n_labels):
        if stats[i][cv2.CC_STAT_AREA] > min_area:
            cleaned[labels == i] = 255

    # 6) 벽 윤곽 보존 + 빈 공간은 0
    cv2.imwrite("preprocessed.png", cleaned)
    return cleaned
