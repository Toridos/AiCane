"""
AiCane 자율주행 통합 시스템
모든 서브시스템 통합 관리
"""

import math
import time

from .core import CoordinateConverter, SpeedProfile
from .hardware import RobokitDriver
from .mapping import FloorPlan
from .localization import SimpleOdometry, UltrasonicLocalizer, ThreeTierLocalization
from .obstacle import ObstacleAvoidanceSystem
from .navigation import ObstacleAwareWaypointFollower


class NavigationSystem:
    """
    AiCane 자율주행 통합 시스템
    
    특징:
    - 3-Tier 위치 추정 (초음파 90% + 오도메트리 9% + LiDAR 1%)
    - 장애물 자동 회피
    - 미끄러짐 vs 장애물 구분
    - 실시간 경로 재계획
    """
    
    def __init__(self, config_dir='./config', mock=False):
        """
        Args:
            config_dir (str): 설정 파일 디렉토리
            mock (bool): Mock 모드 (테스트용)
        """
        print("🚀 AiCane Navigation System 초기화...\n")
        
        self.mock = mock
        
        # 1️⃣ 하드웨어 초기화
        print("1️⃣ 하드웨어 연결...")
        self.robot = RobokitDriver(mock=mock)
        self.lidar = None  # LiDAR는 선택사항
        
        # 2️⃣ 맵 로드
        print("2️⃣ 맵 로드...")
        self.floor_map = FloorPlan()
        # self.floor_map.load_from_json(f'{config_dir}/floor_map.json')
        
        # 3️⃣ 위치 추정 시스템
        print("3️⃣ 위치 추정 시스템 구성...")
        self.ultrasonic_loc = UltrasonicLocalizer(self.robot, self.floor_map)
        self.odometry = SimpleOdometry()
        self.lidar_matcher = None  # LiDAR 매칭은 나중에
        
        self.localization = ThreeTierLocalization(
            self.robot,
            self.ultrasonic_loc,
            self.odometry,
            self.lidar_matcher
        )
        
        # 4️⃣ 장애물 회피 시스템
        print("4️⃣ 장애물 회피 시스템 구성...")
        self.obstacle_system = ObstacleAvoidanceSystem(
            self.robot,
            self.floor_map,
            self.lidar
        )
        
        # 5️⃣ 경로 추종
        print("5️⃣ 경로 추종 시스템 구성...")
        self.follower = ObstacleAwareWaypointFollower(
            self.robot,
            self.localization,
            self.obstacle_system
        )
        
        # 속도 프로파일 로드
        # SpeedProfile.load_calibration(f'{config_dir}/calibration.json')
        
        print("\n✅ 초기화 완료!\n")
    
    def navigate_rooms(self, from_room, to_room, control_hz=5):
        """
        방 간 이동 (자동 경로 생성)
        
        Args:
            from_room (str): 출발 방 (예: '101호')
            to_room (str): 도착 방 (예: '107호')
            control_hz (float): 제어 주기 (Hz)
        
        Example:
            >>> nav = NavigationSystem()
            >>> nav.navigate_rooms('101호', '107호')
        """
        print(f"\n🎯 {from_room} → {to_room} 이동 시작\n")
        
        try:
            # 1. 시작 위치 설정
            start_x, start_y, start_theta = self.floor_map.get_room_waypoint(from_room)
            self.localization.reset_position(start_x, start_y, start_theta)
            
            # 2. 경로 생성
            waypoints = self.floor_map.generate_simple_path(from_room, to_room)
            print(f"📍 경로 생성: {len(waypoints)}개 웨이포인트\n")
            
            # 3. 주행
            self._execute_navigation(waypoints, control_hz)
            
            print(f"\n✅ {to_room} 도착!")
            
        except Exception as e:
            print(f"\n❌ 주행 실패: {e}")
            self.emergency_stop()
    
    def navigate_path(self, waypoints, control_hz=5):
        """
        특정 경로 추종 (cm 단위)
        
        Args:
            waypoints (list): [(x, y), ...] cm 단위 경로
            control_hz (float): 제어 주기 (Hz)
        """
        print(f"\n🎯 경로 추종 시작 ({len(waypoints)}개 포인트)\n")
        
        try:
            self._execute_navigation(waypoints, control_hz)
            print("\n✅ 목적지 도착!")
            
        except Exception as e:
            print(f"\n❌ 주행 실패: {e}")
            self.emergency_stop()
    
    def navigate_ai_path(self, pixel_path, control_hz=5):
        """
        AI 픽셀 경로 추종
        
        Args:
            pixel_path (list): [(x_px, y_px), ...] 픽셀 단위 경로
            control_hz (float): 제어 주기 (Hz)
        
        Example:
            >>> nav = NavigationSystem()
            >>> ai_path = [(100, 314), (200, 314), (300, 314)]
            >>> nav.navigate_ai_path(ai_path)
        """
        print(f"\n🎯 AI 경로 추종 시작 ({len(pixel_path)}개 포인트)\n")
        
        # 픽셀 → cm 변환
        waypoints = CoordinateConverter.path_pixel_to_cm(pixel_path)
        
        print("📐 좌표 변환 (픽셀 → cm):")
        for i, (px, cm) in enumerate(zip(pixel_path[:3], waypoints[:3])):
            print(f"   {i}: 픽셀 {px} → cm {cm}")
        if len(pixel_path) > 3:
            print(f"   ... (총 {len(pixel_path)}개)")
        print()
        
        try:
            self._execute_navigation(waypoints, control_hz)
            print("\n✅ 목적지 도착!")
            
        except Exception as e:
            print(f"\n❌ 주행 실패: {e}")
            self.emergency_stop()
    
    def _execute_navigation(self, waypoints, control_hz):
        """
        내부: 경로 추종 실행
        
        Args:
            waypoints (list): [(x, y), ...] cm 단위
            control_hz (float): 제어 주기
        """
        self.follower.load_path(waypoints)
        
        dt = 1.0 / control_hz
        
        try:
            while True:
                loop_start = time.time()
                
                # 한 스텝 진행
                continue_flag = self.follower.follow_step()
                
                if not continue_flag:
                    break
                
                # 주기 맞추기
                elapsed = time.time() - loop_start
                if elapsed < dt:
                    time.sleep(dt - elapsed)
        
        except KeyboardInterrupt:
            print("\n\n⏸️ 사용자 중단")
            self.emergency_stop()
            raise
        
        finally:
            # 통계 출력
            self.localization.print_stats()
    
    def emergency_stop(self):
        """긴급 정지"""
        print("\n🛑 긴급 정지!")
        self.robot.stop()
    
    def shutdown(self):
        """시스템 종료"""
        print("\n👋 시스템 종료 중...")
        self.robot.stop()
        self.robot.close()
        print("✅ 종료 완료")


if __name__ == '__main__':
    # 테스트
    print("=== NavigationSystem 통합 테스트 ===\n")
    
    # Mock 모드로 시스템 생성
    nav = NavigationSystem(mock=True)
    
    # 테스트 1: 방 간 이동
    print("\n" + "="*50)
    print("테스트 1: 방 간 이동")
    print("="*50)
    
    try:
        nav.navigate_rooms('101호', '107호')
    except Exception as e:
        print(f"오류: {e}")
    
    # 테스트 2: AI 경로 추종
    print("\n" + "="*50)
    print("테스트 2: AI 픽셀 경로")
    print("="*50)
    
    ai_path = [
        (100, 314),
        (200, 314),
        (300, 314),
    ]
    
    try:
        nav.navigate_ai_path(ai_path)
    except Exception as e:
        print(f"오류: {e}")
    
    # 종료
    nav.shutdown()
    
    print("\n✅ 통합 테스트 완료")
