from RobokitRS import *
import json, time, math, sys, os

# ========== 설정 ==========
PORT = "COM5"
SPEED = 15
THRESHOLD = 30
SIDE_THRESHOLD = 25

# 초음파 센서 포트
FRONT_ULTRA_PORT = 2
LEFT_ULTRA_PORT = 3
RIGHT_ULTRA_PORT = 4

# 이동 단위 및 로봇 크기
ROBOT_WIDTH_CM = 25
ROBOT_LENGTH_CM = 25
MOVE_UNIT_CM = 10
MOVE_UNIT_TIME = 2  # 10cm 이동 시간
METERS_PER_MOVE = 0.5
DEGREE_TO_METER = 111320.0

# ========== 초기화 ==========
rs = RobokitRS.RobokitRS()
rs.port_open(PORT)
rs.sonar_begin(FRONT_ULTRA_PORT)
rs.sonar_begin(LEFT_ULTRA_PORT)
rs.sonar_begin(RIGHT_ULTRA_PORT)

print("=" * 50)
print("🤖 route.json 기반 + 3초음파 회피 주행 시스템 시작")
print("=" * 50)

# ========== 기본 함수 ==========
def stop():
    rs.set_mecanumwheels_drive_stop()
    time.sleep(0.1)

def move_forward(distance_cm):
    move_time = (distance_cm / MOVE_UNIT_CM) * MOVE_UNIT_TIME
    rs.set_mecanumwheels_drive_front(SPEED)
    time.sleep(move_time)
    stop()

def move_left(distance_cm):
    move_time = (distance_cm / MOVE_UNIT_CM) * MOVE_UNIT_TIME
    rs.set_mecanumwheels_drive_left(SPEED)
    time.sleep(move_time)
    stop()

def move_right(distance_cm):
    move_time = (distance_cm / MOVE_UNIT_CM) * MOVE_UNIT_TIME
    rs.set_mecanumwheels_drive_right(SPEED)
    time.sleep(move_time)
    stop()

# ========== 센서 읽기 ==========
def read_sensor(port):
    try:
        val = rs.sonar_read(port)
        if val is None or val <= 0: return float('inf')
        return val
    except: return float('inf')

def check_sensors():
    front = read_sensor(FRONT_ULTRA_PORT)
    left = read_sensor(LEFT_ULTRA_PORT)
    right = read_sensor(RIGHT_ULTRA_PORT)
    print(f"📡 센서 - 전방: {front:.1f}cm | 좌: {left:.1f} | 우: {right:.1f}")
    return {
        'front': front, 'left': left, 'right': right,
        'front_blocked': front < THRESHOLD,
        'left_blocked': left < SIDE_THRESHOLD,
        'right_blocked': right < SIDE_THRESHOLD
    }

# ========== 장애물 회피 알고리즘 ==========
def try_avoid_obstacle():
    print("\n⚠️ 장애물 감지 - 회피 시도")
    sensors = check_sensors()
    if not sensors['front_blocked']:
        print("✅ 전방 clear - 회피 불필요")
        return True

    # 좌우 중 열린 방향 선택 (좌측 우선)
    if not sensors['left_blocked']:
        direction, opposite = "left", "right"
        print("👈 좌측 회피 선택")
    elif not sensors['right_blocked']:
        direction, opposite = "right", "left"
        print("👉 우측 회피 선택")
    else:
        print("🚨 좌우 모두 막힘 - 회피 불가")
        return False

    move_count = 0
    for i in range(10):  # 최대 10회 이동
        if direction == "left": move_left(MOVE_UNIT_CM)
        else: move_right(MOVE_UNIT_CM)
        move_count += 1
        sensors = check_sensors()
        if not sensors['front_blocked']:
            print("✅ 전방 clear, 통로 확보")
            for _ in range(2):  # 추가 2회 = 폭 확보
                if direction == "left": move_left(MOVE_UNIT_CM)
                else: move_right(MOVE_UNIT_CM)
                move_count += 1
            print(f"➡️ 전진하여 장애물 통과")
            move_forward(ROBOT_LENGTH_CM)
            print(f"🔁 반대 방향으로 복귀 ({move_count * MOVE_UNIT_CM}cm)")
            for _ in range(move_count):
                if opposite == "left": move_left(MOVE_UNIT_CM)
                else: move_right(MOVE_UNIT_CM)
            print("✅ 복귀 완료")
            return True
    print("❌ 회피 실패")
    return False

# ========== 경로 기반 주행 ==========
def get_direction(a, b):
    dx, dy = b['lng'] - a['lng'], b['lat'] - a['lat']
    if abs(dx) < 1e-6 and dy > 0: return "N"
    if abs(dx) < 1e-6 and dy < 0: return "S"
    if dx > 0 and abs(dy) < 1e-6: return "E"
    if dx < 0 and abs(dy) < 1e-6: return "W"
    if dx > 0 and dy > 0: return "NE"
    if dx < 0 and dy > 0: return "NW"
    if dx > 0 and dy < 0: return "SE"
    if dx < 0 and dy < 0: return "SW"
    return "?"

def move_in_direction(direction):
    if direction == "N": move_forward(20)
    elif direction == "S": move_forward(20)  # 후진 대신 전진 회피
    elif direction == "E": move_right(20)
    elif direction == "W": move_left(20)
    elif direction == "NE": move_forward(20); move_right(20)
    elif direction == "NW": move_forward(20); move_left(20)
    elif direction == "SE": move_right(20); move_forward(20)
    elif direction == "SW": move_left(20); move_forward(20)
    stop()

def navigate_route():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    route_path = os.path.join(base_dir, 'route_data.json')
    with open(route_path, 'r', encoding='utf-8') as f:
        route = json.load(f)
    path = route["path"]

    print(f"\n📍 {route['route_id']} 경로 로드 완료 — 총 {len(path)}개 지점\n")

    for i in range(len(path) - 1):
        start, end = path[i], path[i + 1]
        direction = get_direction(start, end)
        print(f"\n🚗 구간 {i+1}/{len(path)-1}: 방향 {direction}")

        sensors = check_sensors()
        if sensors['front_blocked']:
            print("⚠️ 전방 장애물 → 회피 시도")
            if not try_avoid_obstacle():
                print("❌ 회피 실패 - 경로 스킵")
                continue

        move_in_direction(direction)
        print("🧭 경로상 다음 지점으로 이동 완료")
        time.sleep(0.3)

    print("\n🎉 경로 종료! 모든 지점 도달 완료")
    stop()

# ========== 메인 실행 ==========
try:
    navigate_route()
except KeyboardInterrupt:
    print("\n⚠️ 사용자 중단")
    stop()
finally:
    stop()
    print("\n🔚 시스템 종료")
    rs.end()
