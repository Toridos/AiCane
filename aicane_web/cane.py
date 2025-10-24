from RobokitRS import *
import json, time, math

PORT = "COM5"
SPEED = 10
THRESHOLD = 30
ULTRA_PORT = 2

rs = RobokitRS.RobokitRS()
rs.port_open(PORT)
rs.sonar_begin(ULTRA_PORT)

def stop(): rs.set_mecanumwheels_drive_stop()

def move_forward(sec=1.0): rs.set_mecanumwheels_drive_front(SPEED); time.sleep(sec); stop()
def move_back(sec=1.0): rs.set_mecanumwheels_drive_back(SPEED); time.sleep(sec); stop()
def move_left(sec=1.0): rs.set_mecanumwheels_drive_left(SPEED); time.sleep(sec); stop()
def move_right(sec=1.0): rs.set_mecanumwheels_drive_right(SPEED); time.sleep(sec); stop()
def move_forward_left(sec=1.0): rs.set_mecanumwheels_drive_frontleft(SPEED); time.sleep(sec); stop()
def move_forward_right(sec=1.0): rs.set_mecanumwheels_drive_frontright(SPEED); time.sleep(sec); stop()
def move_back_left(sec=1.0): rs.set_mecanumwheels_drive_backleft(SPEED); time.sleep(sec); stop()
def move_back_right(sec=1.0): rs.set_mecanumwheels_drive_backright(SPEED); time.sleep(sec); stop()

def detect_obstacle():
    try:
        distance = rs.sonar_read(ULTRA_PORT)
        if distance is None or distance <= 0:
            return False
        print(f"📡 감지 거리: {distance:.1f} cm")
        return distance < THRESHOLD
    except Exception as e:
        print("⚠️ 센서 오류:", e)
        return False

def get_direction(start, end):
    dx = end["lng"] - start["lng"]
    dy = end["lat"] - start["lat"]

    # 방향 구분
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
    if direction == "N": move_forward(2.0)
    elif direction == "S": move_back(2.0)
    elif direction == "E": move_right(2.0)
    elif direction == "W": move_left(2.0)
    elif direction == "NE": move_forward_right(2.0)
    elif direction == "NW": move_forward_left(2.0)
    elif direction == "SE": move_back_right(2.0)
    elif direction == "SW": move_back_left(2.0)
    else:
        print("❓ 방향 알 수 없음 → 정지")
        stop()

# === 경로 불러오기 ===
with open("route_data.json", "r", encoding="utf-8") as f:
    route = json.load(f)
path = route["path"]

print(f"\n📍 {route['route_id']} 경로 로드 완료 — 총 {len(path)}개 지점\n")

# === 주행 루프 ===
for i in range(len(path) - 1):
    start = path[i]
    end = path[i + 1]
    direction = get_direction(start, end)

    print(f"🚗 {i+1}/{len(path)-1} 이동 중 → {start} → {end} | 방향: {direction}")

    if detect_obstacle():
        print("⚠️ 장애물 감지 → 회피 중...")
        stop()
        move_back(0.8)
        move_right(1.0)
        move_forward(1.0)
        print("✅ 회피 완료, 경로 복귀")
    else:
        move_in_direction(direction)
        print(f"🧭 방향 {direction}으로 주행 완료")

stop()
print("\n🎯 목적지 도착 — 주행 완료!\n")
rs.end()
