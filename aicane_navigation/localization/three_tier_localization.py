"""
3단계 위치 추정 시스템
Tier 1: 초음파 (90%) → Tier 2: 오도메트리 (9%) → Tier 3: LiDAR (1%)
"""

import time


class ThreeTierLocalization:
    """
    3단계 위치 추정 시스템
    
    Tier 1 (최우선): 초음파 + 오도메트리
        - 복도 안에서 초음파로 X 좌표 보정
        - 가장 빠르고 정확
        - 90% 시간 사용
    
    Tier 2 (보조): 오도메트리만
        - 복도 밖이나 로비
        - 짧은 시간이면 괜찮음
        - 9% 시간 사용
    
    Tier 3 (비상): LiDAR 풀스캔
        - 길을 완전히 잃었을 때
        - CPU 부하 높음
        - 1% 시간만 사용
    """
    
    def __init__(self, robot, ultrasonic_localizer, odometry, lidar_matcher=None):
        """
        Args:
            robot: RobokitDriver
            ultrasonic_localizer: UltrasonicLocalizer
            odometry: SimpleOdometry
            lidar_matcher: LidarMapMatcher (선택사항)
        """
        self.robot = robot
        self.ultrasonic = ultrasonic_localizer
        self.odometry = odometry
        self.lidar = lidar_matcher
        
        # 현재 위치
        self.current_pose = (0, 0, 0)
        self.current_tier = 1
        
        # 길 잃음 카운터
        self.lost_counter = 0
        self.LOST_THRESHOLD = 20  # 4초 (5Hz 기준)
        
        # 통계
        self.stats = {
            'tier1_count': 0,  # 초음파
            'tier2_count': 0,  # 오도메트리
            'tier3_count': 0,  # LiDAR
        }
        
        # 마지막 명령 추적
        self.last_command = None
        self.command_start_time = None
    
    def update(self, lidar_scan=None):
        """
        위치 업데이트 (3단계 시도)
        
        Args:
            lidar_scan (dict): LiDAR 스캔 데이터 (비상시만)
        
        Returns:
            tuple: (x, y, theta, tier, confidence)
                  tier: 1=초음파, 2=오도메트리, 3=LiDAR
        """
        # 오도메트리 업데이트 (항상)
        self._update_odometry()
        odom_x, odom_y, odom_theta = self.odometry.get_pose()
        
        # ═══════════════════════════════════════
        # Tier 1: 초음파 보정 시도 ⭐
        # ═══════════════════════════════════════
        if self.ultrasonic.is_in_corridor(odom_x, odom_y):
            x, y, theta, confidence = self.ultrasonic.get_corrected_pose(
                odom_x, odom_y, odom_theta
            )
            
            if confidence > 0.5:
                # ✅ 초음파 보정 성공!
                self.current_pose = (x, y, theta)
                self.current_tier = 1
                self.lost_counter = 0
                
                self.stats['tier1_count'] += 1
                
                return (x, y, theta, 1, confidence)
        
        # ═══════════════════════════════════════
        # Tier 2: 오도메트리만 사용
        # ═══════════════════════════════════════
        self.current_pose = (odom_x, odom_y, odom_theta)
        self.current_tier = 2
        self.lost_counter += 1
        
        self.stats['tier2_count'] += 1
        
        # 길 잃음 체크
        if self.lost_counter < self.LOST_THRESHOLD:
            return (odom_x, odom_y, odom_theta, 2, 0.5)
        
        # ═══════════════════════════════════════
        # Tier 3: LiDAR 비상 모드 🚨
        # ═══════════════════════════════════════
        if self.lidar is not None and lidar_scan is not None:
            print("🚨 LiDAR 비상 위치 복구 시작...")
            
            try:
                lidar_x, lidar_y, lidar_theta, lidar_conf = \
                    self.lidar.estimate_position_full_search(lidar_scan)
                
                if lidar_conf > 0.4:
                    # ✅ LiDAR로 위치 복구!
                    self.current_pose = (lidar_x, lidar_y, lidar_theta)
                    self.current_tier = 3
                    self.lost_counter = 0
                    
                    # 오도메트리도 리셋
                    self.odometry.reset(lidar_x, lidar_y, lidar_theta)
                    
                    self.stats['tier3_count'] += 1
                    
                    print(f"✅ 위치 복구: ({lidar_x:.1f}, {lidar_y:.1f})")
                    
                    return (lidar_x, lidar_y, lidar_theta, 3, lidar_conf)
                else:
                    print("❌ LiDAR 복구 실패 (신뢰도 낮음)")
            
            except Exception as e:
                print(f"❌ LiDAR 오류: {e}")
        
        # 최악: 오도메트리 그대로 사용
        return (odom_x, odom_y, odom_theta, 2, 0.2)
    
    def _update_odometry(self):
        """오도메트리 업데이트 (명령 기반)"""
        # 현재 명령 가져오기
        current_cmd = self.robot.get_current_command()
        
        if current_cmd is None:
            return
        
        direction = current_cmd['direction']
        speed_level = current_cmd['speed_level']
        start_time = current_cmd['start_time']
        
        # 새 명령인지 확인
        if self.last_command != (direction, speed_level, start_time):
            # 이전 명령 완료 처리
            if self.last_command is not None and self.command_start_time is not None:
                prev_dir, prev_level, prev_start = self.last_command
                duration = start_time - self.command_start_time
                
                if duration > 0:
                    self.odometry.update_from_command(prev_dir, prev_level, duration)
            
            # 새 명령 시작
            self.last_command = (direction, speed_level, start_time)
            self.command_start_time = start_time
    
    def get_pose(self):
        """
        현재 위치 반환
        
        Returns:
            tuple: (x, y, theta)
        """
        return self.current_pose
    
    def reset_position(self, x, y, theta):
        """
        위치 수동 리셋
        
        Args:
            x (float): X 좌표 (cm)
            y (float): Y 좌표 (cm)
            theta (float): 방향 (rad)
        """
        self.current_pose = (x, y, theta)
        self.odometry.reset(x, y, theta)
        self.lost_counter = 0
        
        print(f"📍 위치 리셋: ({x:.1f}, {y:.1f}), {theta:.2f} rad")
    
    def print_stats(self):
        """통계 출력"""
        total = sum(self.stats.values())
        if total == 0:
            print("📊 통계 없음")
            return
        
        print("\n📊 위치 추정 통계:")
        print(f"  Tier 1 (초음파):     {self.stats['tier1_count']:4d} "
              f"({self.stats['tier1_count']/total*100:5.1f}%)")
        print(f"  Tier 2 (오도메트리): {self.stats['tier2_count']:4d} "
              f"({self.stats['tier2_count']/total*100:5.1f}%)")
        print(f"  Tier 3 (LiDAR 비상): {self.stats['tier3_count']:4d} "
              f"({self.stats['tier3_count']/total*100:5.1f}%)")
        print(f"  총 업데이트:        {total:4d}")


if __name__ == '__main__':
    print("=== ThreeTierLocalization 테스트 ===\n")
    
    from ..hardware.robokit_driver import RobokitDriver
    from ..mapping.floor_plan import FloorPlan
    from .ultrasonic_localizer import UltrasonicLocalizer
    from .odometry import SimpleOdometry
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    ultrasonic = UltrasonicLocalizer(robot, floor_map)
    odometry = SimpleOdometry()
    
    localization = ThreeTierLocalization(robot, ultrasonic, odometry)
    
    # 초기 위치 설정
    localization.reset_position(380, 500, 0)
    
    # 시뮬레이션
    print("🚀 위치 추정 시뮬레이션:\n")
    
    for i in range(10):
        robot.set_motion('FORWARD', 10)
        time.sleep(0.1)
        
        x, y, theta, tier, conf = localization.update()
        
        tier_icon = {1: "📡", 2: "📍", 3: "🚨"}
        print(f"{tier_icon[tier]} 스텝 {i+1}: ({x:.1f}, {y:.1f}), "
              f"Tier {tier}, 신뢰도 {conf:.2f}")
    
    robot.stop()
    
    # 통계
    localization.print_stats()
    
    print("\n✅ 테스트 완료")
