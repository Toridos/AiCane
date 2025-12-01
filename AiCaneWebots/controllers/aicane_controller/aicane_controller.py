from controller import Robot
import math

# === 기본 설정 ===
robot = Robot()
TIME_STEP = int(robot.getBasicTimeStep()) or 32

MOTORS = [
    "front_left_wheel",
    "front_right_wheel",
    "rear_left_wheel",
    "rear_right_wheel",
]

SENSORS = ["us_front", "us_left", "us_right"]

GPS_NAME = "gps"
IMU_NAME = "inertial unit"  # Webots InertialUnit 노드 이름 (다르면 여기만 수정)

# 속도 파라미터 (안정성 위해 다소 보수적으로 설정)
MAX_SPEED = 6.0     # 모터 절대 최대 속도 클램프
BASE_SPEED = 2.0     # 직진 기본 속도
ANG_KP = 1.0         # 회전 제어 비례 이득

# 장애물 회피용 센서 비율 (maxValue의 몇 %를 임계값으로 쓸지)
FRONT_RATIO = 0.25
SIDE_RATIO = 0.25

print("[SIM] === Controller Init ===")

# --- 모터 로드 ---
motors = {}
for n in MOTORS:
    m = robot.getDevice(n)
    if m:
        m.setPosition(float("inf"))  # velocity 제어 모드
        m.setVelocity(0.0)
        motors[n] = m
        print(f"[MOTOR] loaded '{n}'")
    else:
        print(f"[WARN] motor '{n}' missing!")

if len(motors) < 4:
    print("[ERROR] Some wheels not found!")

# --- 센서 로드 ---
sensors = {}
for n in SENSORS:
    s = robot.getDevice(n)
    if s:
        s.enable(TIME_STEP)
        sensors[n] = s
        print(f"[SENSOR] loaded '{n}'")
    else:
        print(f"[WARN] sensor '{n}' missing!")

# 센서 임계값 계산 (world에서 정의한 maxValue 기준)
max_front = sensors["us_front"].getMaxValue()
max_left = sensors["us_left"].getMaxValue()
max_right = sensors["us_right"].getMaxValue()

front_th = max_front * FRONT_RATIO
side_th = max_left * SIDE_RATIO

print(f"[SENS] front max={max_front}, left max={max_left}, right max={max_right}")
print(f"[SENS] thresholds → front={front_th:.2f}, side={side_th:.2f}")

# --- GPS / IMU 로드 ---
gps = None
imu = None
try:
    gps_dev = robot.getDevice(GPS_NAME)
    gps_dev.enable(TIME_STEP)
    gps = gps_dev
    print(f"[NAV] GPS '{GPS_NAME}' enabled")
except Exception:
    print(f"[WARN] GPS '{GPS_NAME}' not found")

try:
    imu_dev = robot.getDevice(IMU_NAME)
    imu_dev.enable(TIME_STEP)
    imu = imu_dev
    print(f"[NAV] InertialUnit '{IMU_NAME}' enabled")
except Exception:
    print(f"[WARN] InertialUnit '{IMU_NAME}' not found")

has_localization = gps is not None and imu is not None
print(f"[NAV] Localization: {'ON' if has_localization else 'OFF'}")

# === Waypoint 리스트 ===
# world 좌표계 기준 (x, z)로 작성.
# 이 world에서는 y가 높이이므로, 바닥 평면 좌표(x-z)를 waypoint에 사용한다.
WAYPOINTS = [
    (-1.0, 0.05),   # 출발점(-2, 0.11)에서 장애물 방향으로 직진 시작
    (0.5, 0.05),    # 장애물 앞쪽까지 직진
    (0.5, 0.8),     # 장애물 윗쪽으로 회피
    (2.0, 0.8),     # 우회한 후 직진
    (3.0, 0.05),    # 원래 라인(z≈0.05)으로 복귀
]

print(f"[NAV] Waypoints: {WAYPOINTS}")

# === 유틸 함수 ===
def clamp(v, vmin, vmax):
    return max(vmin, min(vmax, v))


def normalize_angle(angle):
    """[-pi, pi] 범위로 정규화."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def get_pose():
    """현재 (x, z, yaw) 반환. GPS + IMU 필요.

    Webots GPS: [x, y, z]에서 y는 높이(중력 방향), x-z 평면이 바닥.
    """
    pos = gps.getValues()  # [x, y, z]
    x = pos[0]
    z = pos[2]
    rpy = imu.getRollPitchYaw()  # [roll, pitch, yaw]
    yaw = rpy[2]  # yaw: z축 기준 회전
    return x, z, yaw


def set_wheels(left, right):
    """좌우 속도 지정."""
    left = clamp(left, -MAX_SPEED, MAX_SPEED)
    right = clamp(right, -MAX_SPEED, MAX_SPEED)

    motors["front_left_wheel"].setVelocity(left)
    motors["rear_left_wheel"].setVelocity(left)
    motors["front_right_wheel"].setVelocity(right)
    motors["rear_right_wheel"].setVelocity(right)


def drive_forward():
    set_wheels(BASE_SPEED, BASE_SPEED)


# === 상태 정의 ===
STATE_FOLLOW = "follow_waypoints"
STATE_AVOID = "avoid_obstacle"
STATE_FINISHED = "finished"

state = STATE_FOLLOW if has_localization else STATE_AVOID
current_wp_idx = 0
avoid_until = 0.0  # 회피 유지 시간 (초 단위, robot.getTime 기준)


def compute_waypoint_control():
    """현재 waypoint를 향해 가기 위한 (left, right) 속도 계산."""
    global current_wp_idx, state

    if current_wp_idx >= len(WAYPOINTS):
        state = STATE_FINISHED
        return 0.0, 0.0

    x, z, yaw = get_pose()
    tx, tz = WAYPOINTS[current_wp_idx]

    dx = tx - x
    dz = tz - z
    dist = math.sqrt(dx * dx + dz * dz)

    # waypoint 도달 판정
    if dist < 0.15:  # 15cm 이내 접근 시 다음 waypoint
        print(f"[NAV] reached waypoint {current_wp_idx}: ({tx:.2f}, {tz:.2f})")
        current_wp_idx += 1
        if current_wp_idx >= len(WAYPOINTS):
            state = STATE_FINISHED
            return 0.0, 0.0
        # 다음 waypoint 기준으로 다시 계산
        tx, tz = WAYPOINTS[current_wp_idx]
        dx = tx - x
        dz = tz - z
        dist = math.sqrt(dx * dx + dz * dz)

    # x-z 평면에서 목표 각도 계산
    target_heading = math.atan2(dz, dx)
    error = normalize_angle(target_heading - yaw)

    turn = ANG_KP * error
    forward = BASE_SPEED

    left = forward - turn
    right = forward + turn

    return left, right


def compute_avoidance_control():
    """초음파 기반 장애물 회피 제어 (left, right) 속도 계산."""
    f = sensors["us_front"].getValue()
    l = sensors["us_left"].getValue()
    r = sensors["us_right"].getValue()

    # 앞이 바짝 막혀있을 때는 제자리 회전
    if f < front_th:
        if l < r:
            # 왼쪽이 더 가까우면 오른쪽으로 회전
            left = BASE_SPEED
            right = -BASE_SPEED
        else:
            # 오른쪽이 더 가까우면 왼쪽으로 회전
            left = -BASE_SPEED
            right = BASE_SPEED
    else:
        # 전방은 여유 있을 때, 옆 벽을 따라가듯이 살짝 편향해서 전진
        bias = 0.0
        if l < side_th:
            bias += 1.0   # 오른쪽으로 살짝 꺾기
        if r < side_th:
            bias -= 1.0   # 왼쪽으로 살짝 꺾기

        left = BASE_SPEED - bias
        right = BASE_SPEED + bias

    return left, right


print(f"[FSM] initial state = {state}")

last_log_time = -1.0

# === 메인 루프 ===
while robot.step(TIME_STEP) != -1:
    t = robot.getTime()

    # 1초마다 pose 로그
    if has_localization and (last_log_time < 0 or t - last_log_time > 1.0):
        x, z, yaw = get_pose()
        print(f"[POSE] t={t:.2f}  x={x:.2f}  z={z:.2f}  yaw={yaw:.2f}")
        last_log_time = t

    # 센서값 읽기
    f = sensors["us_front"].getValue()
    l = sensors["us_left"].getValue()
    r = sensors["us_right"].getValue()

    # 장애물 감지 시 회피 상태로 전환 (finished 상태가 아닐 때만)
    if state != STATE_FINISHED and f < front_th:
        if state != STATE_AVOID:
            print("[FSM] obstacle detected → AVOID")
        state = STATE_AVOID
        avoid_until = t + 1.0  # 최소 1초는 회피 유지

    # 상태별 동작
    if state == STATE_FINISHED:
        # 모든 waypoint 완료 → 정지
        set_wheels(0.0, 0.0)
        continue

    elif state == STATE_AVOID:
        left, right = compute_avoidance_control()
        set_wheels(left, right)

        # 로컬라이제이션이 가능하고, 일정 시간 지난 뒤 전방이 충분히 뚫리면
        # waypoint 추종 상태로 복귀
        if has_localization and t > avoid_until and f > front_th * 1.5:
            print("[FSM] obstacle cleared → FOLLOW_WAYPOINTS")
            state = STATE_FOLLOW

    elif state == STATE_FOLLOW:
        if has_localization:
            left, right = compute_waypoint_control()
        else:
            # 이 경우는 거의 발생하지 않지만, 안전하게 직진 + 간단 회피
            if f < front_th:
                left, right = compute_avoidance_control()
            else:
                left, right = BASE_SPEED, BASE_SPEED
        set_wheels(left, right)