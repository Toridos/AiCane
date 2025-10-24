from time import sleep
from RobokitRS import RobokitRS
import config as C

rs = RobokitRS.RobokitRS()
rs.port_open(C.COM_PORT)

def close():
    """정상 종료: 모터 정지 후 포트 닫기 (예외 안전)"""
    try:
        stop()
    except Exception as e:
        print(f"[CTRL] stop 예외: {e}")
    try:
        rs.port_close()
    except Exception as e:
        print(f"[CTRL] port_close 예외: {e}")

def stop():                    rs.set_mecanumwheels_drive_stop(C.MOTOR_TYPE)
def forward(s=C.SPEED_FWD):    rs.set_mecanumwheels_drive_front(s, C.MOTOR_TYPE)
def back(s=C.SPEED_FWD):       rs.set_mecanumwheels_drive_back(s, C.MOTOR_TYPE)
def left(s=C.SPEED_FWD):       rs.set_mecanumwheels_drive_left(s, C.MOTOR_TYPE)
def right(s=C.SPEED_FWD):      rs.set_mecanumwheels_drive_right(s, C.MOTOR_TYPE)
def rleft(s=C.SPEED_TURN):     rs.set_mecanumwheels_rotate_left(s, C.MOTOR_TYPE)
def rright(s=C.SPEED_TURN):    rs.set_mecanumwheels_rotate_right(s, C.MOTOR_TYPE)


# ===== 고급 회피 기능 =====

def avoid_smart(front, left, right):
    """
    센서 상태에 따른 스마트 회피
    front, left, right: 0(없음) or 1(장애물)
    """
    if front and left and right:
        # 모든 방향 막힘 - 180도 회전
        print("[SMART_AVOID] 막다른 골목 -> 180도 회전")
        back(8); sleep(0.7)
        stop(); sleep(0.1)
        rleft(7); sleep(1.0)
        stop()
    elif front:
        if not left and not right:
            # 정면만 - 왼쪽 우선
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
    """기본 회피 시퀀스(후진→왼쪽 평행이동)."""
    back(6);  sleep(0.5)
    left(6);  sleep(0.4)
    stop();   sleep(0.1)

def emergency_stop():
    """긴급 정지 + 후진"""
    stop()
    sleep(0.2)
    back(5)
    sleep(0.3)
    stop()

def close():
    """정상 종료: 모터 정지 후 포트 닫기(가능한 메소드 이름을 순차 시도)"""
    try:
        stop()
    except Exception as e:
        print(f"[CTRL] stop 예외: {e}")
    # 포트 닫기 이름 후보들
    for name in ("port_close", "portClose", "close", "serial_close", "serialClose"):
        try:
            if hasattr(rs, name):
                getattr(rs, name)()
                print(f"[CTRL] {name} 호출 완료")
                return
        except Exception as e:
            print(f"[CTRL] {name} 예외: {e}")
    print("[CTRL] 닫기 메소드 없음(라이브러리 종료에 맡김)")