import cv2
import numpy as np

def run_segmentation(img_path):
    """
    테스트용 세그멘테이션: 
    - 벽: 흰색 라인
    - 공간: 검은색
    """

    img = cv2.imread(img_path, 0)
    if img is None:
        raise ValueError("❌ preprocess image not found")

    # 1) 벽(하얀 선)을 검출하기 위한 강한 threshold
    _, mask = cv2.threshold(img, 200, 1, cv2.THRESH_BINARY)

    # 2) 잡음 제거 & 선 두껍게 만들기
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.erode(mask, kernel, iterations=1)

    # 3) 저장
    np.save("uploads/mask.npy", mask.astype(np.uint8))

    return mask.astype(np.uint8)
