# 상단 import 유지
import cv2, time, signal
import perceive as P
import sensors
from fsm import tick
sensors._LOG = True

controller_available = False
try:
    import controller as ctrl
    controller_available = True
    print("[OK] 컨트롤러 연결 성공")
except Exception as e:
    print(f"[WARNING] 컨트롤러 연결 실패: {e}")
    print("[INFO] 카메라 전용 모드로 실행합니다")

_shutdown = False
def _on_signal(*_):
    global _shutdown
    _shutdown = True
    print("\n[SYSTEM] 종료 신호 감지")
signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)

def main():
    print("="*70)
    print("종료: 'q'/ESC 또는 Ctrl+C")
    print("="*70)

    # 카메라 워밍업 (프레임 도착 전 None 가능)
    print("\n[INFO] 카메라 준비 중... 5초 대기")
    time.sleep(5)

    consecutive_none = 0
    NONE_THRESHOLD = 60   # 약 3초(50ms*60) 이상 연속 None이면 재시도
    last_ok_frame_ts = time.time()

    try:
        while not _shutdown:
            frame = P.get_frame()

            # 프레임 None 방어
            if frame is None:
                consecutive_none += 1
                if consecutive_none == 1:
                    print("[WARN] frame=None (워밍업/유실 가능) ... 대기")
                # 오래 None이면 카메라 재시작 시도
                if consecutive_none >= NONE_THRESHOLD:
                    print("[WARN] 프레임 유실 지속 → 카메라 재시작")
                    try:
                        P.shutdown()
                    except Exception as e:
                        print(f"[WARN] 카메라 종료 중 예외: {e}")
                    time.sleep(0.5)
                    consecutive_none = 0
                time.sleep(0.05)
                # 다음 루프로
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q'), 27):
                    break
                continue

            # 정상 프레임
            consecutive_none = 0
            last_ok_frame_ts = time.time()

            # 센서 읽기 (0/1 정규화 반영)
            prox = sensors.read_proximity()

            # 상태 머신
            state = tick(frame, prox=prox)

            # 디스플레이/키 처리
            cv2.imshow("RoboCam", frame)
            key = cv2.waitKey(50) & 0xFF
            if key in (ord('q'), ord('Q'), 27):
                print("\n[SYSTEM] 종료 키 입력")
                break

    except KeyboardInterrupt:
        print("\n[SYSTEM] Ctrl+C 수신")
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 예외 발생: {e}")
        traceback.print_exc()
    finally:
        print("\n[SYSTEM] 정리 중...")
        # 1) 모터 정지
        try:
            if controller_available:
                ctrl.stop()
        except Exception as e:
            print(f"[CLEANUP] stop 예외: {e}")

        # 2) 카메라 종료
        try:
            P.shutdown()
        except Exception as e:
            print(f"[CLEANUP] camera shutdown 예외: {e}")

        # 3) OpenCV 윈도우 정리
        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except Exception as e:
            print(f"[CLEANUP] destroyAllWindows 예외: {e}")

        # 4) 포트 닫기 (호환 이름 탐색)
        try:
            if controller_available and hasattr(ctrl, "close"):
                ctrl.close()
        except Exception as e:
            print(f"[CLEANUP] ctrl.close 예외: {e}")

        print("[SYSTEM] 종료 완료")

if __name__ == "__main__":
    main()
