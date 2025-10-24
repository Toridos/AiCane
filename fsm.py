from time import sleep
import config as C
import controller as ctrl
import perceive as P

class State:
    EXPLORE = "EXPLORE"           # 정상 주행
    AVOID = "AVOID"               # 장애물 회피 중
    EMERGENCY_BACK = "EMERGENCY"  # 긴급 후진
    TURN_AROUND = "TURN_AROUND"   # 완전 회전

state = State.EXPLORE
avoid_counter = 0  # 연속 회피 카운터 (막다른 골목 감지용)

def tick(frame, prox=None):
    """
    복합 센서 기반 지능형 회피 FSM
    prox: (ultra_front, ir_left, ir_right) 각각 0/1 또는 None
    """
    global state, avoid_counter

    # (옵션) 사람 감지 → 즉시 정지
    if P.person_detected():
        ctrl.stop()
        return state

    # ===== 센서 데이터 읽기 =====
    uf = il = ir = 0
    if prox is not None:
        uf, il, ir = prox
        uf = 1 if uf else 0
        il = 1 if il else 0
        ir = 1 if ir else 0
    
    # 장애물 감지 플래그
    front_blocked = (uf == 1)
    left_blocked = (il == 1)
    right_blocked = (ir == 1)
    any_blocked = (front_blocked or left_blocked or right_blocked)
    
    # ===== 비전 기반 경로 분석 =====
    off, _dbg = P.freespace_center_offset(frame)
    vision_available = (off is not None)
    
    # ===== 상태 기계 =====
    
    # --- 긴급 상황: 정면 + 양옆 모두 막힘 (막다른 골목) ---
    if front_blocked and left_blocked and right_blocked:
        print("[EMERGENCY] 막다른 골목! 180도 회전")
        ctrl.stop(); sleep(0.1)
        # 긴급 후진
        ctrl.back(8); sleep(0.6)
        ctrl.stop(); sleep(0.1)
        # 180도 회전
        ctrl.rleft(7); sleep(1.0)
        ctrl.stop(); sleep(0.1)
        avoid_counter = 0
        state = State.TURN_AROUND
        return state
    
    # --- 장애물 있을 때 ---
    if any_blocked:
        avoid_counter += 1
        
        # 연속 회피가 5회 이상이면 막다른 골목 가능성
        if avoid_counter >= 5:
            print("[WARNING] 연속 회피 5회! 방향 전환")
            ctrl.stop(); sleep(0.1)
            ctrl.back(7); sleep(0.5)
            ctrl.rleft(7); sleep(0.8)
            ctrl.stop(); sleep(0.1)
            avoid_counter = 0
            state = State.TURN_AROUND
            return state
        
        # 스마트 회피: 센서 조합에 따라 최적 경로 선택
        ctrl.stop(); sleep(0.05)
        
        if front_blocked:
            # 정면 막힘 - 좌우 센서 확인
            if not left_blocked and not right_blocked:
                # 양쪽 다 뚫림 - 비전 기반으로 선택
                if vision_available and off > 30:
                    # 오른쪽으로 공간이 보임
                    print("[AVOID] 정면 막힘 → 오른쪽으로")
                    ctrl.back(6); sleep(0.4)
                    ctrl.rright(6); sleep(0.5)
                    ctrl.right(8); sleep(0.3)
                else:
                    # 왼쪽으로
                    print("[AVOID] 정면 막힘 → 왼쪽으로")
                    ctrl.back(6); sleep(0.4)
                    ctrl.rleft(6); sleep(0.5)
                    ctrl.left(8); sleep(0.3)
            elif not left_blocked:
                # 왼쪽만 뚫림
                print("[AVOID] 정면+우측 막힘 → 왼쪽으로")
                ctrl.back(6); sleep(0.4)
                ctrl.rleft(7); sleep(0.6)
                ctrl.left(8); sleep(0.4)
            elif not right_blocked:
                # 오른쪽만 뚫림
                print("[AVOID] 정면+좌측 막힘 → 오른쪽으로")
                ctrl.back(6); sleep(0.4)
                ctrl.rright(7); sleep(0.6)
                ctrl.right(8); sleep(0.4)
            else:
                # 모두 막힘 (위에서 처리되어야 하지만 안전장치)
                print("[AVOID] 전방 완전 차단 → 후진")
                ctrl.back(8); sleep(0.6)
        
        elif left_blocked and not right_blocked:
            # 왼쪽만 막힘 - 오른쪽으로 회피
            print("[AVOID] 좌측 장애물 → 우측 회피")
            ctrl.right(8); sleep(0.3)
            ctrl.forward(7); sleep(0.2)
        
        elif right_blocked and not left_blocked:
            # 오른쪽만 막힘 - 왼쪽으로 회피
            print("[AVOID] 우측 장애물 → 좌측 회피")
            ctrl.left(8); sleep(0.3)
            ctrl.forward(7); sleep(0.2)
        
        elif left_blocked and right_blocked and not front_blocked:
            # 양옆 막힘, 정면 뚫림 - 조심스럽게 전진
            print("[AVOID] 양옆 막힘 → 직진")
            ctrl.forward(6); sleep(0.3)
        
        ctrl.stop(); sleep(0.1)
        state = State.AVOID
        return state
    
    # --- 장애물 없을 때: 비전 기반 주행 ---
    else:
        # 회피 카운터 감소 (안전 지대 진입)
        if avoid_counter > 0:
            avoid_counter -= 1
        
        if not vision_available:
            # 비전 실패 시 조심스럽게 직진
            print("[EXPLORE] 비전 없음 → 저속 직진")
            ctrl.forward(C.SPEED_FWD - 2)
            state = State.EXPLORE
            return state
        
        # 오프셋 기반 방향 제어
        if abs(off) <= C.CENTER_DEADBAND:
            # 중앙 정렬 - 직진
            ctrl.forward(C.SPEED_FWD)
            state = State.EXPLORE
        else:
            # 경로 보정 필요
            if abs(off) > 100:
                # 큰 오프셋 - 제자리 회전
                if off > 0:
                    print(f"[EXPLORE] 큰 우측 오프셋({off}) → 우회전")
                    ctrl.rright(6); sleep(0.15)
                else:
                    print(f"[EXPLORE] 큰 좌측 오프셋({off}) → 좌회전")
                    ctrl.rleft(6); sleep(0.15)
                ctrl.forward(C.SPEED_FWD - 1)
            else:
                # 작은 오프셋 - 부드러운 보정
                if off > 0:
                    ctrl.rright(5); sleep(0.1)
                else:
                    ctrl.rleft(5); sleep(0.1)
                ctrl.forward(C.SPEED_FWD)
            
            state = State.EXPLORE
    
    return state
