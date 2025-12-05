"""
장애물 회피 기능이 있는 Waypoint 추종
실시간 재계획 방식 + 고정 속도 + 상세 로그
"""

import math
import time
from ..core import CoordinateConverter


class ObstacleAwareWaypointFollower:
    """
    장애물 회피 기능이 있는 경로 추종
    
    특징:
    - 매 루프마다 현재 위치에서 목표까지 재계산
    - 미끄러짐/오차 자동 보정
    - 장애물 발견 시 회피
    - Waypoint 단위 진행
    - ⭐ 고정 속도: 직진 14, 회전 8
    - ⭐ 상세 로그: 픽셀 좌표 표시
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
        self.waypoints = []  # cm 단위
        self.waypoints_pixel = []  # 픽셀 단위 (로그용)
        self.current_idx = 0
        
        # 파라미터
        self.GOAL_THRESHOLD = 5.0  # cm - 도달 판정 거리
        self.ANGLE_THRESHOLD = 15  # degree - 회전 우선 각도
        
        # ⭐ 고정 속도 레벨 (가변 속도 없음!)
        self.FORWARD_LEVEL = 14  # 직진: 무조건 14
        self.ROTATE_LEVEL = 8    # 회전: 무조건 8
        
        # 회피 상태
        self.avoiding = False
        self.avoid_waypoint = None
        
        # 통계
        self.total_distance = 0.0  # 총 주행 거리
        self.start_time = None
    
    def load_path(self, waypoints):
        """
        경로 로드
        
        Args:
            waypoints (list): [(x, y), ...] cm 단위
        """
        self.waypoints = waypoints
        self.current_idx = 0
        self.avoiding = False
        
        # 픽셀 좌표로 변환 (로그용)
        self.waypoints_pixel = [
            CoordinateConverter.cm_to_pixel(x, y)
            for x, y in waypoints
        ]
        
        # 총 거리 계산
        total_dist = 0
        for i in range(len(waypoints) - 1):
            dx = waypoints[i+1][0] - waypoints[i][0]
            dy = waypoints[i+1][1] - waypoints[i][1]
            total_dist += math.sqrt(dx**2 + dy**2)
        
        self.start_time = time.time()
        
        print(f"📍 경로 로드: {len(waypoints)}개 웨이포인트")
        print(f"   총 거리: {total_dist:.1f}cm")
        print(f"   시작 픽셀: ({self.waypoints_pixel[0][0]:.0f}, {self.waypoints_pixel[0][1]:.0f})")
        print(f"   끝 픽셀: ({self.waypoints_pixel[-1][0]:.0f}, {self.waypoints_pixel[-1][1]:.0f})\n")
    
    def follow_step(self):
        """
        한 스텝 진행 (장애물 고려)
        
        Returns:
            bool: True=계속, False=완료
        """
        # 경로 완료?
        if self.current_idx >= len(self.waypoints):
            self.robot.set_motion('STOP', 0)
            self._print_final_stats()
            return False
        
        # 1️⃣ 위치 업데이트
        x, y, theta, tier, confidence = self.loc.update()
        current_pose = (x, y, theta)
        
        # 현재 위치를 픽셀로 변환
        current_pixel = CoordinateConverter.cm_to_pixel(x, y)
        
        # 티어 표시
        tier_icon = {1: "📡", 2: "📍", 3: "🚨"}
        
        # 2️⃣ 목표 결정
        if self.avoiding and self.avoid_waypoint:
            # 회피 모드 → 임시 목표
            target_x, target_y = self.avoid_waypoint
            target_pixel = CoordinateConverter.cm_to_pixel(target_x, target_y)
        else:
            # 정상 모드 → 다음 웨이포인트
            target_x, target_y = self.waypoints[self.current_idx]
            target_pixel = self.waypoints_pixel[self.current_idx]
        
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
        
        # 5️⃣ 거리/각도 계산
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        
        # ⭐ 로그 먼저 출력 (도달 체크 전에!)
        self._print_status(
            self.current_idx,
            current_pixel,
            target_pixel,
            (x, y),
            (target_x, target_y),
            distance,
            tier
        )
        
        # 6️⃣ 도달 체크
        if distance < self.GOAL_THRESHOLD:
            if self.avoiding:
                # 회피 웨이포인트 도달 → 정상 모드 복귀
                print("   ✅ 회피 완료, 정상 경로 복귀\n")
                self.avoiding = False
                self.avoid_waypoint = None
            else:
                # 실제 웨이포인트 도달
                print(f"   ✅ 웨이포인트 {self.current_idx + 1} 도달!\n")
                self.current_idx += 1
            
            return True
        
        # 7️⃣ 이동 명령 (⭐ 고정 속도!)
        target_angle = math.atan2(dy, dx)
        angle_error = self._normalize_angle(target_angle - theta)
        
        if abs(angle_error) > math.radians(self.ANGLE_THRESHOLD):
            # 회전 우선 (⭐ 무조건 레벨 8)
            direction = 'ROTATE_L' if angle_error > 0 else 'ROTATE_R'
            speed_level = self.ROTATE_LEVEL
            
            print(f"   → 명령: {direction}, 레벨:{speed_level}")
            self.robot.set_motion(direction, speed_level)
        else:
            # 전진 (⭐ 무조건 레벨 14)
            speed_level = self.FORWARD_LEVEL
            
            print(f"   → 명령: FORWARD, 레벨:{speed_level}")
            self.robot.set_motion('FORWARD', speed_level)
        
        print()  # 빈 줄
        return True
    
    def _print_status(self, idx, current_pixel, target_pixel, current_cm, target_cm, distance, tier):
        """
        상태 로그 출력
        
        Args:
            idx: 현재 웨이포인트 인덱스
            current_pixel: 현재 위치 (픽셀)
            target_pixel: 목표 위치 (픽셀)
            current_cm: 현재 위치 (cm)
            target_cm: 목표 위치 (cm)
            distance: 남은 거리 (cm)
            tier: 위치 추정 티어
        """
        tier_icon = {1: "📡", 2: "📍", 3: "🚨"}
        
        print(f"{tier_icon[tier]} 웨이포인트 {idx + 1}/{len(self.waypoints)}")
        print(f"   현재 위치: 픽셀({current_pixel[0]:.0f}, {current_pixel[1]:.0f}) / cm({current_cm[0]:.1f}, {current_cm[1]:.1f})")
        print(f"   목표 위치: 픽셀({target_pixel[0]:.0f}, {target_pixel[1]:.0f}) / cm({target_cm[0]:.1f}, {target_cm[1]:.1f})")
        print(f"   남은 거리: {distance:.1f}cm")
    
    def _print_final_stats(self):
        """최종 통계 출력"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n📊 주행 완료!")
            print(f"   소요 시간: {elapsed:.1f}초")
            print(f"   웨이포인트: {len(self.waypoints)}개")
    
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
        
        avoid_pixel = CoordinateConverter.cm_to_pixel(avoid_x, avoid_y)
        
        print(f"🔄 회피 시작")
        print(f"   회피 위치: 픽셀({avoid_pixel[0]:.0f}, {avoid_pixel[1]:.0f}) / cm({avoid_x:.0f}, {avoid_y:.0f})")
        print(f"   회피 각도: {avoid_angle}도\n")
        
        # 회전 시작 (⭐ 회전도 레벨 8)
        direction = 'ROTATE_L' if avoid_angle > 0 else 'ROTATE_R'
        self.robot.set_motion(direction, self.ROTATE_LEVEL)
    
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
