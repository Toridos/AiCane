import time
import atexit
import signal
import sys
from typing import Optional, Tuple

import cv2
import numpy as np
import config as C

# --------- 설정값 ---------
SHOW_DEBUG = True # 성능을 위해 디버그 끄기
FW, FH = C.FRAME_W, C.FRAME_H

rcam = None
_FRAME_NONE_COUNT = 0
_FRAME_NONE_LIMIT = getattr(C, "FRAME_NONE_LIMIT", 50)
_last_valid_frame = None
_initialization_done = False

# --------- Signal Handler ---------
def _signal_handler(signum, frame):
    print(f"\n[SIGNAL] 시그널 {signum} 수신, 안전 종료 중...")
    shutdown()
    sys.exit(0)

try:
    signal.signal(signal.SIGTRAP, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
except Exception as e:
    print(f"[WARN] 시그널 핸들러 등록 실패: {e}")

# --------- RoboCAM 로드 ---------
try:
    from RoboCam.robocam import RoboCam
    print("[OK] RoboCam 로드 성공")
except ImportError as e:
    print(f"[ERROR] RoboCam 로드 실패: {e}")
    raise


# --------- 초기화 ---------
def _ensure_started():
    global rcam, _initialization_done
    
    if rcam is not None and _initialization_done:
        return rcam

    try:
        print("[CAM] === 초기화 시작 ===")
        
        print("[CAM] Step 1: RoboCam() 생성...")
        rcam = RoboCam()
        time.sleep(0.3)
        
        print("[CAM] Step 2: CameraStreamInit(320x240)...")
        try:
            rcam.CameraStreamInit(width=320, height=240)
        except Exception as e:
            print(f"[CAM] 기본 해상도 실패, 재시도: {e}")
            rcam.CameraStreamInit()
        time.sleep(0.3)
        
        print("[CAM] Step 3: CameraStream()...")
        rcam.CameraStream()
        time.sleep(0.5)
        
        print("[CAM] Step 4: 첫 프레임 대기 중...")
        for i in range(10):
            try:
                test_frame = getattr(rcam, "_RoboCam__raw_img", None)
                if test_frame is not None and hasattr(test_frame, 'shape') and test_frame.size > 0:
                    print(f"[CAM] ✓ 첫 프레임 수신 완료 ({i}번째 시도)")
                    _initialization_done = True
                    return rcam
            except:
                pass
            time.sleep(0.3)
            print(f"[CAM] ... 대기 중 ({i+1}/10)")
        
        print("[CAM] [경고] 첫 프레임 타임아웃 (계속 진행)")
        _initialization_done = True
        return rcam
        
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        rcam = None
        _initialization_done = False
        return None


def _restart_camera():
    global rcam, _FRAME_NONE_COUNT, _initialization_done, _last_valid_frame
    print("\n[CAM] === 재시작 시도 ===")
    
    try:
        if rcam is not None:
            print("[CAM] 기존 스트림 종료...")
            try:
                rcam.CameraStreamOff()
            except:
                pass
            time.sleep(0.5)
    finally:
        rcam = None
        _initialization_done = False
        _FRAME_NONE_COUNT = 0
        _last_valid_frame = None
        
    time.sleep(0.5)
    _ensure_started()


# --------- 프레임 가져오기 (강제 반복 읽기) ---------
def get_frame():
    """RoboCam에서 프레임 한 장을 가져온다. 실패 시 마지막 유효 프레임을 반환."""
    global _FRAME_NONE_COUNT, _last_valid_frame

    try:
        cam = _ensure_started()
    except Exception as e:
        print(f"[ERROR] 초기화 예외: {e}")
        return _last_valid_frame

    if cam is None:
        return _last_valid_frame

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            raw_frame = None
            for attr in ('_RoboCam__raw_img', '__raw_img', 'raw_img', 'frame'):
                try:
                    raw_frame = getattr(cam, attr, None)
                    if raw_frame is not None and hasattr(raw_frame, 'shape') and raw_frame.size > 0:
                        break
                except Exception:
                    continue

            if raw_frame is None or not hasattr(raw_frame, 'shape') or raw_frame.size == 0:
                if attempt == 0:
                    _FRAME_NONE_COUNT += 1
                    if _FRAME_NONE_COUNT == 1:
                        print("[CAM] 프레임 None (재시도 중...)")
                    elif _FRAME_NONE_COUNT % 10 == 0:
                        print(f"[CAM] 프레임 None {_FRAME_NONE_COUNT}회")
                time.sleep(0.02)
                continue

            # 정상 프레임
            _FRAME_NONE_COUNT = 0
            h, w = raw_frame.shape[:2]
            if (w, h) != (FW, FH):
                frame = cv2.resize(raw_frame, (FW, FH))
            else:
                frame = raw_frame.copy()
            _last_valid_frame = frame
            return frame

        except Exception as e:
            if attempt == 0:
                print(f"[ERROR] 프레임 처리 오류 (시도 {attempt+1}): {e}")

    # 모든 재시도 실패
    print(f"[WARN] {MAX_RETRIES}회 재시도 실패 → 마지막 유효 프레임 반환")
    if _FRAME_NONE_COUNT >= _FRAME_NONE_LIMIT:
        print(f"[CAM] {_FRAME_NONE_COUNT}회 초과 → 재시작")
        _restart_camera()
    return _last_valid_frame


def shutdown():
    global rcam, _last_valid_frame, _initialization_done
    
    print("\n[CAM] === 종료 시작 ===")
    try:
        if rcam is not None:
            print("[CAM] CameraStreamOff()...")
            try:
                rcam.CameraStreamOff()
            except Exception as e:
                print(f"[CAM] StreamOff 예외: {e}")
            time.sleep(0.3)
    except Exception as e:
        print(f"[CAM] 종료 예외: {e}")
    finally:
        rcam = None
        _last_valid_frame = None
        _initialization_done = False
        print("[CAM] 종료 완료")


atexit.register(shutdown)


def freespace_center_offset(frame) -> Tuple[Optional[int], dict]:
    """바닥 감지"""
    if frame is None:
        return None, {"roi": None, "mask": None}
    
    try:
        h, w = frame.shape[:2]
        y0 = int(h * getattr(C, "ROI_Y_RATIO", 0.66))
        roi = frame[y0:, :]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        lower = np.array([0, 0, 80], dtype=np.uint8)
        upper = np.array([179, 60, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            if SHOW_DEBUG:
                _show_debug(roi, mask, w // 2, None, None)
            return None, {"roi": roi, "mask": mask}

        c = max(cnts, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] < 100:
            if SHOW_DEBUG:
                _show_debug(roi, mask, w // 2, None, None)
            return None, {"roi": roi, "mask": mask}

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        if SHOW_DEBUG:
            _show_debug(roi, mask, w // 2, cx, cy)

        return cx - (w // 2), {"roi": roi, "mask": mask}
        
    except Exception as e:
        print(f"[ERROR] freespace 처리 오류: {e}")
        return None, {"roi": None, "mask": None}


def face_start_if_needed():
    return


def person_detected() -> bool:
    return False


def _show_debug(roi, mask, cx_mid, cx=None, cy=None):
    """디버그 표시"""
    if not SHOW_DEBUG or roi is None or mask is None:
        return
    try:
        dbg = roi.copy()
        h, w = dbg.shape[:2]
        cv2.line(dbg, (w // 2, 0), (w // 2, h), (255, 0, 0), 1)
        if cx is not None and cy is not None:
            cv2.circle(dbg, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(dbg, f"offset={cx - (w//2)}", (10, 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("ROI/FreeSpace", dbg)
        cv2.imshow("Mask", mask)
        cv2.waitKey(1)
    except:
        pass