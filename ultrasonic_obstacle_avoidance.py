"""
초음파 3개를 사용한 장애물 회피 시스템
- 전방 초음파 1개 (중앙)
- 좌측 초음파 1개 (옆구리)
- 우측 초음파 1개 (옆구리)

회피 전략:
1. 전방 장애물 감지 시 좌/우 중 한 방향으로 계속 이동
2. 전방이 clear할 때까지 같은 방향으로 12.5cm씩 반복
3. 본체 통과 후 원래 경로로 복귀
4. 후진 없음! 오직 전진, 좌, 우만 사용
"""

from RobokitRS import *
import time
from enum import Enum

# ========== 설정 클래스 ==========
class Config:
    """로봇 설정값 관리"""
    PORT = "COM3"
    SPEED = 14
    ROTATE_SPEED = 8
    THRESHOLD = 20
    SIDE_THRESHOLD = 2
    # 회피 방향 선택용 스캔
    SCAN_CLEAR_THRESHOLD = 40   # "뚫렸다"라고 인정하는 기준 거리
    SCAN_ROTATE_TIME = 1.465     # 로봇을 살짝 회전시켜서 다른 방향을 보는 시간(실험으로 튜닝)
    
    # 초음파 센서 포트
    FRONT_ULTRA_PORT = 2
    LEFT_ULTRA_PORT = 3
    RIGHT_ULTRA_PORT = 12
    
    # 본체 크기
    ROBOT_WIDTH_CM = 25
    ROBOT_LENGTH_CM = 25
    AVOID_UNIT_CM = 10
    MOVE_UNIT_TIME = 2.632 # 본체 길이만큼 움직이는 시간
    AVOID_UNIT_TIME = 1.053
    
    # 목표 거리
    TARGET_DISTANCE_M = 2.0
    TARGET_DISTANCE_CM = TARGET_DISTANCE_M * 100
    
    # 회피 설정
    MAX_AVOID_ATTEMPTS = 60
    BODY_WIDTH_EXTRA_MOVES = 2  # 본체 폭 확보를 위한 추가 이동 횟수
    FORWARD_INTERVAL_SEC = 0.528  # 직진 한 루프 주기 (초)
    FORWARD_STEP_CM = 5


class Direction(Enum):
    """이동 방향 열거형"""
    LEFT = "left"
    RIGHT = "right"
    
    def opposite(self):
        """반대 방향 반환"""
        return Direction.RIGHT if self == Direction.LEFT else Direction.LEFT


# ========== 센서 관리 클래스 ==========
class SensorManager:
    """초음파 센서 읽기 및 상태 관리"""
    
    def __init__(self, robot):
        self.robot = robot
        self._initialize_sensors()
    
    def _initialize_sensors(self):
        """센서 초기화"""
        self.robot.sonar_begin(Config.FRONT_ULTRA_PORT)
        #self.robot.sonar_begin(Config.LEFT_ULTRA_PORT)
        #self.robot.sonar_begin(Config.RIGHT_ULTRA_PORT)

    def _read_sensor(self, port, sensor_name):
        """개별 초음파 센서 읽기 (에러 처리 포함)"""
        try:
            distance = self.robot.sonar_read(port)
            if distance is None or distance <= 0:
                return float('inf')
            return distance
        except Exception as e:
            print(f"⚠️ {sensor_name} 센서 오류: {e}")
            return float('inf')
        
    def read_front(self):
        """전방 센서 읽기"""
        return self._read_sensor(Config.FRONT_ULTRA_PORT, "전방")
    
    def read_left_ir(self):
        """좌측 IR: True = 너무 가까움(위험), False = 안전"""
        # TODO: 실제 라이브러리 함수 이름으로 교체
        try:
            val = self.robot.digital_read(Config.LEFT_ULTRA_PORT)
            return bool(val)   # 센서 스펙에 따라 0/1 의미는 확인 필요
        except Exception as e:
            print(f"⚠️ 좌측 IR 센서 오류: {e}")
            return False

    def read_right_ir(self):
        """우측 IR: True = 위험"""
        try:
            val = self.robot.digital_read(Config.RIGHT_ULTRA_PORT)
            return bool(val)
        except Exception as e:
            print(f"⚠️ 우측 IR 센서 오류: {e}")
            return False
    
    def check_all(self):
        """모든 센서 상태 확인"""
        front = self.read_front()
        # left = self.read_left()
        # right = self.read_right()
        left_ir = self.read_left_ir()
        right_ir = self.read_right_ir()
        print(f"📡 센서 상태 - 전방: {front:.1f}cm | 좌측: {left_ir} | 우측: {right_ir}")
        
        return {
            'front': front,
            #'left': left,
            #'right': right,
            'front_blocked': front < Config.THRESHOLD,
            #'left_blocked': left < Config.SIDE_THRESHOLD,
            #'right_blocked': right < Config.SIDE_THRESHOLD
            'left_near': left_ir,
            'right_near': right_ir,
        }


# ========== 모션 컨트롤 클래스 ==========
class MotionController:
    """로봇 이동 제어"""
    
    def __init__(self, robot):
        self.robot = robot
    
    def stop(self):
        """로봇 정지"""
        self.robot.set_mecanumwheels_drive_stop()
        time.sleep(0.1)
    
    def move_forward(self, distance_cm):
        """전진 (cm 단위)"""
        move_time = (distance_cm / Config.FORWARD_STEP_CM) * Config.FORWARD_INTERVAL_SEC
        self.robot.set_mecanumwheels_drive_front(Config.SPEED)
        time.sleep(move_time)
    
    def move_left(self, distance_cm):
        """좌측 이동 (cm 단위)"""
        move_time = (distance_cm / Config.AVOID_UNIT_CM) * Config.AVOID_UNIT_TIME
        self.robot.set_mecanumwheels_drive_left(Config.SPEED)
        time.sleep(move_time)
    
    def move_right(self, distance_cm):
        """우측 이동 (cm 단위)"""
        move_time = (distance_cm / Config.AVOID_UNIT_CM) * Config.AVOID_UNIT_TIME
        self.robot.set_mecanumwheels_drive_right(Config.SPEED)
        time.sleep(move_time)
    
    def move_direction(self, direction: Direction, distance_cm):
        """지정된 방향으로 이동"""
        if direction == Direction.LEFT:
            self.move_left(distance_cm)
        else:
            self.move_right(distance_cm)
    
    def rotate_left(self, duration):
        """제자리에서 왼쪽으로 회전 (duration초)"""
        self.robot.set_mecanumwheels_rotate_left(Config.ROTATE_SPEED)
        time.sleep(duration)
        self.stop()

    def rotate_right(self, duration):
        """제자리에서 오른쪽 회전"""
        self.robot.set_mecanumwheels_rotate_right(Config.ROTATE_SPEED)
        time.sleep(duration)
        self.stop()


# ========== 장애물 회피 클래스 ==========
class ObstacleAvoider:
    """장애물 회피 로직"""
    def _scan_directions(self):
        """
        네 방향(왼앞, 왼쪽, 오른앞, 오른쪽)의 여유 거리(cm)를 측정
        반환: (left_front, left, right_front, right)
        """
        lf = l = rf = r = 0

        # (0) 시작: 현재 정면 

        # (1) 왼쪽앞
        self.motion.rotate_left(Config.SCAN_ROTATE_TIME)
        lf = self.sensors.read_front()

        # (2) 왼쪽
        self.motion.rotate_left(Config.SCAN_ROTATE_TIME)
        l = self.sensors.read_front()

        #(중간정면)
        self.motion.rotate_right(Config.SCAN_ROTATE_TIME * 2)

        # (3) 오른앞
        # 지금 왼쪽으로 2칸 돌아왔으므로 오른쪽으로 3칸 돌리면 "오른쪽 앞"
        self.motion.rotate_right(Config.SCAN_ROTATE_TIME)
        rf = self.sensors.read_front()

        # (4) 오른쪽
        self.motion.rotate_right(Config.SCAN_ROTATE_TIME)
        r = self.sensors.read_front()

        # (5) 복귀 → 다시 왼쪽으로 3칸
        self.motion.rotate_left(Config.SCAN_ROTATE_TIME * 2)

        print(f"🔍 스캔 결과 - LF:{lf:.1f}, L:{l:.1f}, RF:{rf:.1f}, R:{r:.1f}")
        return lf, l, rf, r

    
    def __init__(self, motion: MotionController, sensors: SensorManager):
        self.motion = motion
        self.sensors = sensors
    
    def _determine_avoidance_plan(self):
        lf, l, rf, r = self._scan_directions()
        direction, max_dist, opposite, opposite_max_dist = decide_direction_and_limit(lf, l, rf, r)

        if direction is None:
            print("🚨 회피 가능한 방향 없음")
            return None, 0

        max_steps = max(1, int((max_dist-20) // Config.AVOID_UNIT_CM))
        print(f"👉 방향 선택: {direction.value}, 최대 이동 가능 횟수: {max_steps}")

        return direction, max_steps, opposite, opposite_max_dist
    
    def _check_side_collision(self, direction: Direction):
        """측면 충돌 체크"""
        if direction == Direction.LEFT:
            dist = self.sensors.read_left_ir()
            if self.sensors.read_left_ir():
                print("   ⚠️ 좌측 IR 충돌 위험")
                return True
        else:
            if self.sensors.read_right_ir():
                print("   ⚠️ 우측 IR 충돌 위험")
                return True
        return False
    
    def _try_direction_avoidance(self, direction: Direction, max_steps: int):
        print(f"\n{'='*50}")
        print(f"🔄 {direction.value} 방향으로 통로 탐색 (최대 {max_steps}회)")
        print(f"{'='*50}")
        
        move_count = 0

        print(f"🔄 {direction.value} 방향으로 통로 탐색")
        
        for attempt in range(min(Config.MAX_AVOID_ATTEMPTS, max_steps)):
            print(f"\n📍 {direction.value} 이동 #{attempt + 1}/{min(Config.MAX_AVOID_ATTEMPTS, max_steps)}")
            
            print(f"🔄 {direction.value} 방향으로 통로 탐색")
            # 1) 좌/우 이동
            self.motion.move_direction(direction, Config.AVOID_UNIT_CM)
            move_count += 1

            # 전방 확인
            front_dist = self.sensors.read_front()
            print(f"   → 전방: {front_dist:.1f}cm")
            
            # 전방 clear?
            if front_dist >= Config.THRESHOLD:
                print(f"   ✅ 전방 통로 발견!")
                
                # 본체 폭 확보를 위한 추가 이동
                print(f"   → 본체 폭({Config.ROBOT_WIDTH_CM}cm) 확보용 추가 이동")
                for _ in range(Config.BODY_WIDTH_EXTRA_MOVES):
                    self.motion.move_direction(direction, Config.AVOID_UNIT_CM)
                    move_count += 1
                
                final_front = self.sensors.read_front()
                print(f"   → 최종 전방: {final_front:.1f}cm")
                
                if final_front >= Config.THRESHOLD:
                    return True, move_count
            
            # 측면 충돌 체크
            if self._check_side_collision(direction):
                break
        
        print(f"\n❌ {direction.value} 방향 실패")
        return False, move_count
    
    def _return_to_path(self, direction: Direction, move_count: int) -> float:
        """원래 경로로 복귀"""
        total_offset = move_count * Config.AVOID_UNIT_CM
        
        print(f"\n{'='*50}")
        print(f"🎉 회피 성공! ({direction.value} {total_offset}cm 이동)")
        print(f"{'='*50}")
        print(f"\n🔄 원래 경로로 복귀 시작")
        
        # 1. 본체 길이+25cm만큼 전진 (장애물 완전히 통과)
        forward_distance = Config.ROBOT_LENGTH_CM + Config.THRESHOLD + 5
        print(f"   → 본체 길이+25m({forward_distance}cm) 전진 (장애물 통과)")
        self.motion.move_forward(forward_distance)

        # 👉 회피로 인해 전진한 만큼 전체 남은 거리에서 차감
        if hasattr(self, "distance_remaining"):
            self.distance_remaining -= forward_distance
            print(f"📉 남은 거리 갱신: {self.distance_remaining:.1f}cm")
        
        # 2. 반대 방향으로 복귀
        opposite = direction.opposite()
        print(f"   → {opposite.value} 방향으로 {total_offset}cm 복귀 이동")
        for _ in range(move_count):
            self.motion.move_direction(opposite, Config.AVOID_UNIT_CM)
        
        print(f"   ✅ 원래 경로 복귀 완료!")
        print(f"{'='*50}")

        return forward_distance
    
    def try_avoid_obstacle(self):
        """장애물 회피 시도 + 경로 복귀"""
        print("\n" + "="*50)
        print("⚠️ 장애물 감지! 회피 알고리즘 시작")
        print("="*50)
        
        sensor_data = self.sensors.check_all()
        
        # 회피 방향 결정
        direction, max_steps, opposite, opposite_max_steps = self._determine_avoidance_plan()
        # 첫 번째 방향 시도
        if direction is None:
            return False, 0.0
        
        success, move_count = self._try_direction_avoidance(direction, max_steps)
        if success:
            extra_forward = self._return_to_path(direction, move_count)
            return True, extra_forward
        
        # 반대 방향 시도
        if opposite is None:
            print("❌ 반대 방향도 막힘 - 회피 불가능")
            return False, 0.0
        
        return_count = move_count

        success, move_count = self._try_direction_avoidance(opposite, opposite_max_steps+return_count)
        print(f"\n🔄 반대 방향({opposite.value}) 시도")
        print(f"{'='*50}")

        move_count= move_count - return_count
        
        if success:
            self._return_to_path(opposite, move_count)
            return True
        
        print("\n❌ 양방향 모두 실패 - 회피 불가능")
        return False, 0.0
    

def decide_direction_and_limit(lf, l, rf, r, clear_th=Config.SCAN_CLEAR_THRESHOLD):
    lf_open = lf >= clear_th
    l_open  = l  >= clear_th
    rf_open = rf >= clear_th
    r_open  = r  >= clear_th

    print(f"열림 여부 - LF:{lf_open}, L:{l_open}, RF:{rf_open}, R:{r_open}")

    # a) 네 방향 모두 뚫림
    if lf_open and l_open and rf_open and r_open:
        if l > r:
            primary = Direction.LEFT
            secondary = primary.opposite()
            return primary, l, secondary, r
        elif r > l:
            primary = Direction.RIGHT
            secondary = primary.opposite()
            return primary, r, secondary, l
        else:
            if(lf>=rf):
                primary = Direction.LEFT
                primary_steps = l
                secondary = primary.opposite()
                secondary_steps = r
            else:
                primary = Direction.RIGHT
                primary_steps = r
                secondary = primary.opposite()
                secondary_steps = l
            return primary, primary_steps, secondary, secondary_steps

    # b) 왼앞·왼·오른 뚫리고, 오른앞 막힘 → 왼
    if lf_open and l_open and r_open and not rf_open:
        primary = Direction.LEFT
        secondary = primary.opposite()
        return primary, l, secondary, r

    # c) 오른앞·오른·왼 뚫리고, 왼앞 막힘 → 오른
    if rf_open and r_open and l_open and not lf_open:
        primary = Direction.RIGHT
        secondary = primary.opposite()
        return primary, r, secondary, l

    # d) 왼앞·오른앞 막히고, 왼/오 모두 뚫림 → 더 큰 쪽
    if not lf_open and not rf_open and l_open and r_open:
        if(l>=r):
            primary = Direction.LEFT
            primary_steps = l
            secondary = primary.opposite()
            secondary_steps = r
        else:
            primary = Direction.RIGHT
            primary_steps = r
            secondary = primary.opposite()
            secondary_steps = l
        return primary, primary_steps, secondary, secondary_steps

    # e) 왼오 중 한쪽만 뚫림
    if l_open and not r_open:
        return Direction.LEFT, l, None, 0
    if r_open and not l_open:
        return Direction.RIGHT, r, None, 0

    return None, 0, None, 0   # 완전 막힘

# ========== 내비게이션 클래스 ==========
class Navigator:
    """목표 지점까지 주행 관리"""
    
    def __init__(self, motion: MotionController, sensors: SensorManager, avoider: ObstacleAvoider):
        self.motion = motion
        self.sensors = sensors
        self.avoider = avoider
    
    def _handle_side_correction(self, sensor_data):
        """측면 보정"""
        if sensor_data['left_near']:
            print("⚠️ 좌측 근접! 우측 보정")
            self.motion.move_right(5)
        
        if sensor_data['right_near']:
            print("⚠️ 우측 근접! 좌측 보정")
            self.motion.move_left(5)
    
    def navigate_to_goal(self):
        """목표 지점까지 장애물 회피하며 주행"""
        traveled_distance = 0
        
        print("\n🚀 목표 지점으로 주행 시작!\n")
        
        while traveled_distance < Config.TARGET_DISTANCE_CM:
            remaining = Config.TARGET_DISTANCE_CM - traveled_distance
            
            print(f"\n{'='*50}")
            print(f"📍 현재: {traveled_distance:.0f}cm / {Config.TARGET_DISTANCE_CM:.0f}cm")
            print(f"📏 남은 거리: {remaining:.0f}cm")
            print(f"{'='*50}")
            
            # 센서 체크
            sensor_data = self.sensors.check_all()
            
            # 전방 장애물 처리
            if sensor_data['front_blocked']:
                print("⚠️ 전방 장애물 감지!")

                success, extra_forward = self.avoider.try_avoid_obstacle()
                if success:
                    # 🔥 회피 때문에 추가로 직진한 거리 반영
                    traveled_distance += extra_forward
                    remaining = Config.TARGET_DISTANCE_CM - traveled_distance
                    print("✅ 회피 완료, 주행 재개\n")
                    continue
                else:
                    print("❌ 회피 불가능 - 주행 중단")
                    return False
            
            # 측면 보정
            self._handle_side_correction(sensor_data)
            
            # 전진
            step = min(Config.FORWARD_STEP_CM, remaining)
            print(f"➡️ {step:.0f}cm 전진")
            self.motion.move_forward(step)
            traveled_distance += step
        
        print("\n" + "="*50)
        print("🎉 목표 도착!")
        print("="*50)
        return True


# ========== 메인 시스템 클래스 ==========
class RobotSystem:
    """전체 로봇 시스템 통합"""
    
    def __init__(self):
        self.robot = RobokitRS.RobokitRS()
        self.robot.port_open(Config.PORT)
        
        self.sensors = SensorManager(self.robot)
        self.motion = MotionController(self.robot)
        self.avoider = ObstacleAvoider(self.motion, self.sensors)
        self.navigator = Navigator(self.motion, self.sensors, self.avoider)
        
        self._print_startup_info()
    
    def _print_startup_info(self):
        """시작 정보 출력"""
        print("=" * 50)
        print("🤖 초음파 3개로 장애물 회피 시스템 시작")
        print("=" * 50)
        print(f"📏 목표 거리: {Config.TARGET_DISTANCE_M}m ({Config.TARGET_DISTANCE_CM}cm)")
        print(f"🔧 본체 크기: {Config.ROBOT_WIDTH_CM}cm (폭) x {Config.ROBOT_LENGTH_CM}cm (길이)")
        print(f"⚡ 속도: {Config.SPEED}")
        print(f"📡 감지 임계값: 전방 {Config.THRESHOLD}cm, 측면 {Config.SIDE_THRESHOLD}cm")
        print("=" * 50)
        time.sleep(2)
    
    def run(self):
        """시스템 실행"""
        try:
            success = self.navigator.navigate_to_goal()
            
            if success:
                print("\n✅ 미션 성공!")
                # ⭐ 2) 180도 회전
                print("\n🔄 복귀를 위해 180도 회전합니다.")
                self.motion.rotate_left( Config.SCAN_ROTATE_TIME * 4 )

                time.sleep(0.5)

                # ⭐ 3) 출발점으로 다시 navigate
                print("\n🚗💨 출발점으로 복귀 시작!")
                success_return = self.navigator.navigate_to_goal()

                if success_return:
                    print("\n🏁 출발점 복귀 완료!")
                else:
                    print("\n❌ 복귀 중 실패")
            else:
                print("\n❌ 미션 실패")
            
            return success
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 사용자 중단")
            self.motion.stop()
        
        except Exception as e:
            print(f"\n\n❌ 오류: {e}")
            self.motion.stop()
        
        finally:
            self.motion.stop()
            print("\n🔚 시스템 종료")
            self.robot.end()


# ========== 메인 실행 ==========
if __name__ == "__main__":
    system = RobotSystem()
    system.run()