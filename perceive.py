# perceive.py — Wi-Fi RoboCAM 전용 (노트북 내장캠 대신 사용)
# 요구: pip install RoboCam, OpenCV(cv2), numpy
# 설정: config.py에 FRAME_W/FRAME_H, ROI_Y_RATIO, CENTER_DEADBAND, CAM_IP/CAM_PORT(선택)

import cv2, numpy as np, time
import config as C
import atexit

# --------- 설정값 ---------
SHOW_DEBUG = True  # ROI/Mask 디버그 창 보기

# config에 CAM_IP/CAM_PORT가 없으면 기본값 사용
CAM_IP   = getattr(C, "CAM_IP",   "192.168.4.1")
CAM_PORT = getattr(C, "CAM_PORT", 80)

# 프레임 크기
FW, FH = C.FRAME_W, C.FRAME_H
rcam = None
_shutdown = False

# --------- RoboCAM 초기화 ---------
# RoboCam은 와이파이 카메라 전용 스트리머
try:
    from RoboCam.robocam import *
    print("[OK] RoboCam 로드 성공")
except ImportError:
    try:
        from RoboCam.robocam import *
        print("[OK] RoboCam 로드 성공")
    except ImportError as e:
        print(f"[ERROR] RoboCam을 로드할 수 없습니다: {e}")
        raise

    from RoboCam.robocam import *

def _ensure_started():
    global rcam
    if rcam is None:
        
        rcam = RoboCam()
        print("[INFO] CameraStreamInit 호출...")
        rcam.CameraStreamInit(width=FW, height=FH)
        print("[INFO] 초기화 대기 중...")
        time.sleep(1.0)
        print("[INFO] CameraStream 시작...")
        rcam.CameraStream()
        print("[INFO] 스트림 대기 중...")
        time.sleep(2.0)
        print("[OK] RoboCam 스트림 시작")
    return rcam

# --------- 퍼블릭 API ---------
def get_frame():
    if _shutdown:
        return None
    """
    Wi-Fi 카메라에서 한 프레임을 받아 (FW, FH)로 리사이즈하여 반환.
    실패하면 None.
    """
    cam = _ensure_started()
    
    # RoboCam의 내부 변수에서 프레임 가져오기
    # Python name mangling: __raw_img → _RoboCam__raw_img
    frame = getattr(cam, "_RoboCam__raw_img", None)
    
    if frame is None:
        return None
    h, w = frame.shape[:2]
    if (w, h) != (FW, FH):
        frame = cv2.resize(frame, (FW, FH))
    return frame


def shutdown():
    """카메라 스트림 정상 종료"""
    global rcam, _shutdown
    if _shutdown:
        return
    _shutdown = True
    try:
        if rcam is not None:
            print("[CAM] CameraStreamOff 호출...")
            try:
                rcam.CameraStreamOff()
            except Exception as e:
                print(f"[CAM] CameraStreamOff 예외: {e}")
            time.sleep(0.2)
    finally:
        rcam = None
        print("[CAM] 카메라 종료 완료")

# 파이썬 종료 시에도 안전하게 닫기
atexit.register(shutdown)

def freespace_center_offset(frame) -> tuple[int | None, dict]:
    """
    하단 ROI에서 '바닥/자유공간' 후보를 HSV 임계로 분리.
    가장 큰 영역의 무게중심 x를 화면 중앙과 비교해 offset(px)을 반환.
      - 반환값: (offset, debug_dict)
        offset: 중앙보다 왼쪽은 음수, 오른쪽은 양수. 실패 시 None.
        debug_dict: {"roi": ROI이미지, "mask": 마스크}
    """
    h, w = frame.shape[:2]
    y0 = int(h * getattr(C, "ROI_Y_RATIO", 0.66))
    roi = frame[y0:, :]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 바닥(밝고 채도가 낮음) 후보 — 현장에 맞게 튜닝하세요
    # 범위 예시: H(0~179), S(0~60), V(80~255)
    lower = np.array([0, 0, 80], dtype=np.uint8)
    upper = np.array([179, 60, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)

    # 노이즈 정리
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        if SHOW_DEBUG:
            _show_debug(roi, mask, w//2, None, None)
        return None, {"roi": roi, "mask": mask}

    c = max(cnts, key=cv2.contourArea)
    M = cv2.moments(c)
    if M["m00"] == 0:
        if SHOW_DEBUG:
            _show_debug(roi, mask, w//2, None, None)
        return None, {"roi": roi, "mask": mask}

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    if SHOW_DEBUG:
        _show_debug(roi, mask, w//2, cx, cy)

    # 화면 전체 기준 중앙과의 오프셋(px)
    return cx - (w // 2), {"roi": roi, "mask": mask}

# --------- (옵션) 사람 감지 → 즉시 정지 훅 ---------
# 발표 안정성을 위해 기본 False만 반환 (원하면 Haar/YOLO/Robocam FaceDetector로 확장 가능)
def face_start_if_needed():
    """옵션: 사람 감지 기능 시작 (현재는 미사용)."""
    return

def person_detected() -> bool:
    """옵션: 사람 감지 결과 (현재는 항상 False)."""
    return False

# --------- 디버그 표시 ---------
def _show_debug(roi, mask, cx_mid, cx=None, cy=None):
    dbg = roi.copy()
    h, w = dbg.shape[:2]
    # 중앙선
    cv2.line(dbg, (w // 2, 0), (w // 2, h), (255, 0, 0), 1)
    # 추정 중심
    if cx is not None and cy is not None:
        cv2.circle(dbg, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(dbg, f"offset={cx - (w//2)}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.imshow("ROI/FreeSpace", dbg)
    cv2.imshow("Mask", mask)
