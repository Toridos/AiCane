# controller.py
# - RobokitRS import 구조를 안전하게 처리
# - macOS에서 포트 자동 감지
# - 보드가 없으면 "비활성" 상태로만 동작

from time import sleep
import platform
import glob

try:
    import config as C
except ImportError:
    # 최소 기본값만 가진 더미 config
    class _Cfg:
        COM_PORT = None
        MOTOR_TYPE = 1
        SPEED_FWD = 10
        SPEED_TURN = 6
    C = _Cfg()

rs = None          # 실제 RobokitRS 인스턴스
RobokitRSClass = None  # RobokitRS 클래스(정상 import 되면 채워짐)


def _load_robokit_class():
    """
    RobokitRS 패키지 구조가 어떻게 되어 있든지 간에
    실제 '클래스' 객체만 찾아서 반환.
    """
    # 1) import RobokitRS as pkg  → pkg.RobokitRS 가 클래스일 수도 있음
    try:
        import RobokitRS as pkg
        # pkg.RobokitRS 가 존재하고, 호출 가능한 경우에만 사용
        if hasattr(pkg, "RobokitRS") and callable(getattr(pkg, "RobokitRS")):
            print("[CTRL] RobokitRS import: import RobokitRS; 사용: RobokitRS.RobokitRS")
            return pkg.RobokitRS
    except Exception as e:
        print(f"[CTRL] 1단계 import 실패(import RobokitRS): {e}")

    # 2) from RobokitRS import RobokitRS as cls  → cls 가 클래스일 때
    try:
        from RobokitRS import RobokitRS as cls
        if callable(cls):
            print("[CTRL] RobokitRS import: from RobokitRS import RobokitRS")
            return cls
        # callable 이 아니면(=모듈) 무시
    except Exception as e:
        print(f"[CTRL] 2단계 import 실패(from RobokitRS import RobokitRS): {e}")

    # 3) from RobokitRS.RobokitRS import RobokitRS as cls
    try:
        from RobokitRS.RobokitRS import RobokitRS as cls
        if callable(cls):
            print("[CTRL] RobokitRS import: from RobokitRS.RobokitRS import RobokitRS")
            return cls
    except Exception as e:
        print(f"[CTRL] 3단계 import 실패(from RobokitRS.RobokitRS import RobokitRS): {e}")

    print("[CTRL] RobokitRS 클래스를 찾지 못했습니다. 보드 제어는 비활성화됩니다.")
    return None


# 모듈 import 시점에 한 번만 클래스 탐색
RobokitRSClass = _load_robokit_class()


def init() -> bool:
    """
    보드 초기화.
    - 성공: True, rs 가 유효한 인스턴스로 설정
    - 실패: False, rs = None
    """
    global rs

    # 이미 초기화돼 있으면 재사용
    if rs is not None:
        return True

    if RobokitRSClass is None:
        print("[CTRL] RobokitRSClass 가 없습니다. 보드 제어는 비활성 상태입니다.")
        return False

    port = getattr(C, "COM_PORT", None)

    # macOS면 자동 포트 탐지 시도
    if not port:
        if platform.system() == "Darwin":
            candidates = glob.glob("/dev/cu.usbserial-*") + glob.glob("/dev/tty.usbserial-*")
            if candidates:
                port = candidates[0]
                print(f"[CTRL] macOS 자동 감지된 포트: {port}")
            else:
                print("[CTRL] macOS에서 사용 가능한 직렬 포트를 찾지 못했습니다.")
                return False
        else:
            print("[CTRL] COM_PORT 가 설정되지 않았습니다. config.COM_PORT 를 확인하세요.")
            return False

    try:
        print(f"[CTRL] 포트 {port} 열기 시도…")
        board = RobokitRSClass()     # 여기서 '클래스'인지만 보장하면 됨
        board.port_open(port)
        rs = board
        print("[CTRL] 포트 열기 성공")
        return True
    except Exception as e:
        print(f"[CTRL] 포트 열기 실패: {e}")
        rs = None
        return False


# 내부에서 항상 rs 가 있는지 확인
def _ensure_rs():
    if rs is None:
        print("[CTRL] rs 가 초기화되어 있지 않습니다.")
        return False
    return True


# === 기본 구동 API ===

def stop():
    if not _ensure_rs():
        return
    try:
        rs.set_mecanumwheels_drive_stop(getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] stop 예외: {e}")


def forward(s=None):
    if not _ensure_rs():
        return
    if s is None:
        s = getattr(C, "SPEED_FWD", 10)
    try:
        rs.set_mecanumwheels_drive_front(s, getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] forward 예외: {e}")


def back(s=None):
    if not _ensure_rs():
        return
    if s is None:
        s = getattr(C, "SPEED_FWD", 10)
    try:
        rs.set_mecanumwheels_drive_back(s, getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] back 예외: {e}")


def left(s=None):
    if not _ensure_rs():
        return
    if s is None:
        s = getattr(C, "SPEED_FWD", 10)
    try:
        rs.set_mecanumwheels_drive_left(s, getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] left 예외: {e}")


def right(s=None):
    if not _ensure_rs():
        return
    if s is None:
        s = getattr(C, "SPEED_FWD", 10)
    try:
        rs.set_mecanumwheels_drive_right(s, getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] right 예외: {e}")


def rleft(s=None):
    if not _ensure_rs():
        return
    if s is None:
        s = getattr(C, "SPEED_TURN", 6)
    try:
        rs.set_mecanumwheels_rotate_left(s, getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] rleft 예외: {e}")


def rright(s=None):
    if not _ensure_rs():
        return
    if s is None:
        s = getattr(C, "SPEED_TURN", 6)
    try:
        rs.set_mecanumwheels_rotate_right(s, getattr(C, "MOTOR_TYPE", 1))
    except Exception as e:
        print(f"[CTRL] rright 예외: {e}")


# === 고급 회피 로직(기존 그대로 유지) ===

def avoid_smart(front, left, right):
    """
    front, left, right: 0/1
    """
    if not _ensure_rs():
        print("[SMART_AVOID] rs 없음 → 동작 생략")
        return

    if front and left and right:
        print("[SMART_AVOID] 막다른 골목 -> 180도 회전")
        back(8); sleep(0.7)
        stop(); sleep(0.1)
        rleft(7); sleep(1.0)
        stop()
    elif front:
        if not left and not right:
            print("[SMART_AVOID] 정면 -> 왼쪽")
            back(6); sleep(0.4)
            rleft(6); sleep(0.5)
        elif not left:
            print("[SMART_AVOID] 정면+우측 -> 왼쪽")
            back(6); sleep(0.4)
            rleft(7); sleep(0.6)
        else:
            print("[SMART_AVOID] 정면+좌측 -> 우측")
            back(6); sleep(0.4)
            rright(7); sleep(0.6)
        stop()
    elif left:
        print("[SMART_AVOID] 좌측 -> 우측 회피")
        right(8); sleep(0.3)
        stop()
    elif right:
        print("[SMART_AVOID] 우측 -> 좌측 회피")
        left(8); sleep(0.3)
        stop()


def avoid_simple():
    """기본 회피 시퀀스."""
    back(6);  sleep(0.5)
    left(6);  sleep(0.4)
    stop();   sleep(0.1)


def emergency_stop():
    """긴급 정지 + 후진"""
    if not _ensure_rs():
        return
    stop()
    sleep(0.2)
    back(5)
    sleep(0.3)
    stop()


def close():
    """정상 종료: 모터 정지 후 포트 닫기(여러 메소드 이름 시도)"""
    global rs
    if rs is None:
        return
    try:
        stop()
    except Exception as e:
        print(f"[CTRL] stop 예외: {e}")

    for name in ("port_close", "portClose", "close", "serial_close", "serialClose"):
        try:
            if hasattr(rs, name):
                getattr(rs, name)()
                print(f"[CTRL] {name} 호출 완료")
                rs = None
                return
        except Exception as e:
            print(f"[CTRL] {name} 예외: {e}")
    print("[CTRL] 닫기 메소드 없음(라이브러리에 맡김)")
    rs = None