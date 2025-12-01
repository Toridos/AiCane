"""
장애물 회피 기능이 있는 Waypoint 추종
실시간 재계획 방식
"""

import math
import time
from ..core.speed_profile import SpeedProfile


class ObstacleAwareWaypointFollower:
    """
    장애물 회피 기능이 있는 경로 추종
    
    특징:
    - 매 루프마다 현재 위치에서 목표까지 재계산
    - 미끄러짐/오차 자동 보정
    - 장애물 발견 시 회피
    - Waypoint 단위 진행
    """
    
    def __init__(self, robot, localization, obstacle_system):
        """
        Args:
            robot: RobokitDriver
            localization: ThreeTierLocalization
            obstacle_system: ObstacleAvoidanceSystem
        """
        self.robot = robot
        self.loc = localization
        self.obstacles = obstacle_system
        
        # 경로
        self.waypoints = []
        self.current_idx = 0
        
        # 파라미터
        self.GOAL_THRESHOLD = 5.0  # cm - 도달 판정 거리
        self.ANGLE_THRESHOLD = 15  # degree - 회전 우선 각도
        
        # 회피 상태
        self.avoiding = False
        self.avoid_waypoint = None
    
    def load_path(self, waypoints):
        """
        경로 로드
        
        Args:
            waypoints (list): [(x, y), ...] cm 단위
        """
        self.waypoints = waypoints
        self.current_idx = 0
        self.avoiding = False
        
        print(f"📍 경로 로드: {len(waypoints)}개 웨이포인트")
    
    def follow_step(self):
        """
        한 스텝 진행 (장애물 고려)
        
        Returns:
            bool: True=계속, False=완료
        """
        # 경로 완료?
        if self.current_idx >= len(self.waypoints):
            self.robot.set_motion('STOP', 0)
            return False
        
        # 1️⃣ 위치 업데이트
        x, y, theta, tier, confidence = self.loc.update()
        current_pose = (x, y, theta)
        
        # 티어 표시
        tier_icon = {1: "📡", 2: "📍", 3: "🚨"}
        
        # 2️⃣ 목표 결정
        if self.avoiding and self.avoid_waypoint:
            # 회피 모드 → 임시 목표
            target_x, target_y = self.avoid_waypoint
        else:
            # 정상 모드 → 다음 웨이포인트
            target_x, target_y = self.waypoints[self.current_idx]
        
        target_pose = (target_x, target_y)
        
        # 3️⃣ 장애물 체크
        obstacle_check = self.obstacles.check_and_respond(
            current_pose,
            target_pose
        )
        
        # 4️⃣ 행동 결정
        if obstacle_check['action'] == 'stop':
            # 정지
            self.robot.set_motion('STOP', 0)
            print("🛑 장애물로 인한 정지")
            time.sleep(0.5)
            return True
        
        elif obstacle_check['action'] == 'avoid':
            # 회피
            self._execute_avoidance(current_pose, obstacle_check)
            return True
        
        elif obstacle_check['action'] == 'slow_down':
            # 감속
            speed_modifier = 0.6
        else:
            # 정상
            speed_modifier = 1.0
        
        # 5️⃣ 거리/각도 계산
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        
        # 6️⃣ 도달 체크
        if distance < self.GOAL_THRESHOLD:
            if self.avoiding:
                # 회피 웨이포인트 도달 → 정상 모드 복귀
                print("✅ 회피 완료, 정상 경로 복귀")
                self.avoiding = False
                self.avoid_waypoint = None
            else:
                # 실제 웨이포인트 도달
                print(f"{tier_icon[tier]} Waypoint {self.current_idx} 도달 "
                      f"({x:.0f}, {y:.0f})")
                self.current_idx += 1
            
            return True
        
        # 7️⃣ 이동 명령
        target_angle = math.atan2(dy, dx)
        angle_error = self._normalize_angle(target_angle - theta)
        
        if abs(angle_error) > math.radians(self.ANGLE_THRESHOLD):
            # 회전 우선
            direction = 'ROTATE_L' if angle_error > 0 else 'ROTATE_R'
            speed = self._select_speed(abs(angle_error), 'rotate', speed_modifier)
            
            self.robot.set_motion(direction, speed)
        else:
            # 전진
            speed = self._select_speed(distance, 'forward', speed_modifier)
            
            self.robot.set_motion('FORWARD', speed)
        
        return True
    
    def _execute_avoidance(self, current_pose, obstacle_check):
        """
        회피 실행
        
        Args:
            current_pose (tuple): (x, y, theta)
            obstacle_check (dict): 장애물 체크 결과
        """
        avoid_angle = obstacle_check['avoid_direction']
        
        if isinstance(avoid_angle, str):
            # 'left' or 'right'
            avoid_angle = 30 if avoid_angle == 'left' else -30
        
        # 회피 웨이포인트 생성 (1m 떨어진 곳)
        avoid_distance = 100  # cm
        
        x, y, theta = current_pose
        avoid_rad = theta + math.radians(avoid_angle)
        
        avoid_x = x + avoid_distance * math.cos(avoid_rad)
        avoid_y = y + avoid_distance * math.sin(avoid_rad)
        
        self.avoiding = True
        self.avoid_waypoint = (avoid_x, avoid_y)
        
        print(f"🔄 회피: ({avoid_x:.0f}, {avoid_y:.0f}) 방향 {avoid_angle}도")
        
        # 회전 시작
        direction = 'ROTATE_L' if avoid_angle > 0 else 'ROTATE_R'
        self.robot.set_motion(direction, 8)
    
    def _select_speed(self, value, motion_type, modifier=1.0):
        """
        거리/각도에 따라 속도 선택
        
        Args:
            value (float): 거리 (cm) 또는 각도 (rad)
            motion_type (str): 'forward' or 'rotate'
            modifier (float): 속도 수정자 (0~1)
        
        Returns:
            int: 속도 레벨 (6~15)
        """
        if motion_type == 'forward':
            if value > 50:
                base_level = 12
            elif value > 20:
                base_level = 10
            else:
                base_level = 8
        else:  # rotate
            if value > math.radians(45):
                base_level = 10
            else:
                base_level = 8
        
        # 수정자 적용
        level = int(base_level * modifier)
        
        # 최소 레벨 보장
        level = max(6, level)
        
        return level
    
    def stop(self):
        """경로 추종 중단"""
        self.robot.set_motion('STOP', 0)
        print("⏸️ 경로 추종 중단")
    
    @staticmethod
    def _normalize_angle(angle):
        """각도 정규화 (-π ~ π)"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


if __name__ == '__main__':
    print("=== ObstacleAwareWaypointFollower 테스트 ===\n")
    
    from ..hardware.robokit_driver import RobokitDriver
    from ..mapping.floor_plan import FloorPlan
    from ..localization import SimpleOdometry, UltrasonicLocalizer, ThreeTierLocalization
    from ..obstacle import ObstacleAvoidanceSystem
    import time
    
    # 초기화
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    ultrasonic = UltrasonicLocalizer(robot, floor_map)
    odometry = SimpleOdometry()
    localization = ThreeTierLocalization(robot, ultrasonic, odometry)
    
    obstacles = ObstacleAvoidanceSystem(robot, floor_map)
    
    follower = ObstacleAwareWaypointFollower(robot, localization, obstacles)
    
    # 경로 설정
    path = [(0, 0), (100, 0), (200, 0), (300, 0)]
    follower.load_path(path)
    
    # 초기 위치
    localization.reset_position(0, 0, 0)
    
    # 시뮬레이션
    print("🚀 경로 추종 시뮬레이션:\n")
    
    for i in range(10):
        continue_flag = follower.follow_step()
        
        if not continue_flag:
            print("\n✅ 목적지 도착!")
            break
        
        time.sleep(0.2)
    
    follower.stop()
    localization.print_stats()
    
    print("\n✅ 테스트 완료")
