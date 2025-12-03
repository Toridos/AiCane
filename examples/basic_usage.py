"""
AiCane Navigation 사용 예제 (최신 버전)

최신 기능:
- LiDAR 360도 장애물 감지
- 하이브리드 모드 (초음파 + LiDAR)
- NavigationLogger 통합
- ConfigLoader 사용
"""

from aicane_navigation import NavigationSystem
from aicane_navigation.utils import ConfigLoader, NavigationLogger
import time


def example1_simple_rooms():
    """예제 1: 간단한 방 간 이동"""
    print("=" * 60)
    print("예제 1: 방 간 이동 (101호 → 107호)")
    print("=" * 60 + "\n")
    
    # 시스템 초기화 (Mock 모드)
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # 이동
    nav.navigate_rooms('101호', '107호')
    
    # 종료
    nav.shutdown()


def example2_ai_path():
    """예제 2: AI 경로 추종"""
    print("\n" + "=" * 60)
    print("예제 2: AI 픽셀 경로 추종")
    print("=" * 60 + "\n")
    
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # AI가 제공한 픽셀 경로
    ai_path = [
        (100, 314),
        (200, 314),
        (300, 314),
        (400, 314),
        (500, 314),
    ]
    
    nav.navigate_ai_path(ai_path)
    
    nav.shutdown()


def example3_custom_path():
    """예제 3: 직접 cm 경로 지정"""
    print("\n" + "=" * 60)
    print("예제 3: 직접 경로 지정 (cm 단위)")
    print("=" * 60 + "\n")
    
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # 직접 cm 단위로 경로 지정
    waypoints = [
        (380, 500),    # 시작
        (380, 1000),   # 중간
        (380, 1242),   # 도착
    ]
    
    nav.navigate_path(waypoints)
    
    nav.shutdown()


def example4_json_path():
    """예제 4: JSON 파일에서 경로 로드"""
    print("\n" + "=" * 60)
    print("예제 4: JSON 파일 경로")
    print("=" * 60 + "\n")
    
    import json
    
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # JSON 파일 로드
    try:
        with open('./maps/example_path.json', 'r') as f:
            data = json.load(f)
        
        pixel_path = [(p['x'], p['y']) for p in data['waypoints']]
        
        nav.navigate_ai_path(pixel_path)
    except FileNotFoundError:
        print("⚠️ example_path.json 파일이 없습니다. 건너뜁니다.")
    
    nav.shutdown()


def example5_realtime_monitoring():
    """예제 5: 실시간 위치 모니터링"""
    print("\n" + "=" * 60)
    print("예제 5: 실시간 모니터링")
    print("=" * 60 + "\n")
    
    from aicane_navigation.hardware import RobokitDriver
    from aicane_navigation.mapping import FloorPlan
    from aicane_navigation.localization import (
        SimpleOdometry,
        UltrasonicLocalizer,
        ThreeTierLocalization
    )
    
    # 초기화
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    ultrasonic = UltrasonicLocalizer(robot, floor_map)
    odometry = SimpleOdometry()
    
    localization = ThreeTierLocalization(robot, ultrasonic, odometry)
    localization.reset_position(380, 500, 0)
    
    # 10초간 위치 모니터링
    print("10초간 위치 모니터링...\n")
    
    robot.set_motion('FORWARD', 10)
    
    for i in range(50):  # 5Hz x 10초
        x, y, theta, tier, conf = localization.update()
        
        tier_icon = {1: "📡", 2: "📍", 3: "🚨"}
        
        print(f"\r{tier_icon[tier]} ({x:6.1f}, {y:6.1f}), "
              f"Tier {tier}, 신뢰도 {conf:.2f}",
              end='', flush=True)
        
        time.sleep(0.2)
    
    robot.stop()
    
    print("\n\n")
    localization.print_stats()


# ============================================
# 🆕 신규 예제: LiDAR 통합
# ============================================

def example6_lidar_detection():
    """예제 6: LiDAR 360도 장애물 감지"""
    print("\n" + "=" * 60)
    print("예제 6: LiDAR 360도 장애물 감지")
    print("=" * 60 + "\n")
    
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # LiDAR 상태 확인
    lidar_status = nav.get_lidar_status()
    
    print(f"LiDAR 활성화: {lidar_status['enabled']}")
    print(f"LiDAR 연결: {lidar_status['connected']}")
    print(f"스캔 중: {lidar_status['scanning']}")
    
    if lidar_status['scanning']:
        print(f"포인트 수: {lidar_status['num_points']}")
    
    # 주행 (LiDAR 자동 사용)
    nav.navigate_rooms('101호', '107호')
    
    nav.shutdown()


def example7_config_loader():
    """예제 7: ConfigLoader 사용"""
    print("\n" + "=" * 60)
    print("예제 7: 설정 파일 로드")
    print("=" * 60 + "\n")
    
    # 하드웨어 설정
    hw_config = ConfigLoader.load_hardware_config()
    
    print("🔧 하드웨어 설정:")
    print(f"  로봇 포트: {hw_config['robot']['port']}")
    print(f"  LiDAR 활성화: {hw_config['lidar']['enabled']}")
    print(f"  LiDAR 포트: {hw_config['lidar']['port']}")
    print(f"  LiDAR 속도: {hw_config['lidar']['baudrate']}")
    
    # 네비게이션 설정
    nav_config = ConfigLoader.load_navigation_config()
    
    print("\n🚀 네비게이션 설정:")
    print(f"  장애물 감지 모드: {nav_config['obstacle_detection']['mode']}")
    print(f"  초음파 최소 거리: {nav_config['obstacle_detection']['ultrasonic']['min_distance']}cm")
    print(f"  LiDAR 최소 거리: {nav_config['obstacle_detection']['lidar']['min_distance']}cm")
    
    # 중첩 키 접근
    robot_port = ConfigLoader.get_nested(hw_config, 'robot.port')
    lidar_enabled = ConfigLoader.get_nested(hw_config, 'lidar.enabled', False)
    
    print(f"\n📋 중첩 키 접근:")
    print(f"  robot.port: {robot_port}")
    print(f"  lidar.enabled: {lidar_enabled}")


def example8_navigation_logger():
    """예제 8: NavigationLogger 사용"""
    print("\n" + "=" * 60)
    print("예제 8: 로그 시스템")
    print("=" * 60 + "\n")
    
    # 로거 생성
    logger = NavigationLogger(
        name="example_nav",
        log_to_file=True,
        log_dir='./logs',
        level='INFO'
    )
    
    # 주행 시작
    logger.log_navigation_start("101호", "107호")
    
    # 위치 로그
    logger.log_position(
        pose=(456.0, 835.0, 90.0),
        tier=1,
        confidence=0.95,
        extra={'source': 'ultrasonic'}
    )
    
    # 장애물 로그
    logger.log_obstacle({
        'front': 45.0,
        'left': 120.0,
        'right': 98.0,
        'action': 'slow_down',
        'source': 'hybrid'
    }, severity="WARNING")
    
    # 명령어 로그
    logger.log_command('forward', 10, extra={'reason': 'waypoint'})
    
    # 이벤트 로그
    logger.info("웨이포인트 도착")
    logger.warning("GPS 신호 약함")
    
    # 주행 종료
    logger.log_navigation_end(success=True, reason="목적지 도착")
    
    # 통계
    logger.print_stats()
    
    print(f"\n📁 로그 파일: {logger.log_file}")


def example9_hybrid_obstacle_detection():
    """예제 9: 하이브리드 장애물 감지 (초음파 + LiDAR)"""
    print("\n" + "=" * 60)
    print("예제 9: 하이브리드 장애물 감지")
    print("=" * 60 + "\n")
    
    # 설정 확인
    nav_config = ConfigLoader.load_navigation_config()
    
    mode = nav_config['obstacle_detection']['mode']
    print(f"장애물 감지 모드: {mode}")
    
    if mode == 'hybrid':
        print("\n✅ 하이브리드 모드 활성화!")
        print("  - 초음파: 근거리 감지")
        print("  - LiDAR: 360도 감지 + 우회 경로")
    
    # 주행
    nav = NavigationSystem(config_dir='./config', mock=True)
    nav.navigate_rooms('101호', '107호')
    nav.shutdown()


def example10_environment_variables():
    """예제 10: 환경 변수 사용"""
    print("\n" + "=" * 60)
    print("예제 10: 환경 변수")
    print("=" * 60 + "\n")
    
    import os
    
    # 환경 변수 설정
    os.environ['ROBOT_PORT'] = '/dev/rfcomm0'
    os.environ['LIDAR_PORT'] = '/dev/ttyUSB1'
    
    print("🌍 환경 변수 설정:")
    print(f"  ROBOT_PORT={os.environ['ROBOT_PORT']}")
    print(f"  LIDAR_PORT={os.environ['LIDAR_PORT']}")
    
    # 설정 파일에서 ${ROBOT_PORT} 치환
    # (hardware.yaml에 ${ROBOT_PORT} 설정 필요)
    
    print("\n💡 hardware.yaml에 다음과 같이 설정하면:")
    print("  robot:")
    print("    port: ${ROBOT_PORT}")
    print("  lidar:")
    print("    port: ${LIDAR_PORT}")
    print("\n→ 자동으로 환경 변수로 치환됩니다!")


if __name__ == '__main__':
    try:
        print("🚀 AiCane Navigation 예제 모음\n")
        
        # 기본 예제
        example1_simple_rooms()
        example2_ai_path()
        example3_custom_path()
        example4_json_path()
        example5_realtime_monitoring()
        
        # 🆕 신규 예제
        example6_lidar_detection()
        example7_config_loader()
        example8_navigation_logger()
        example9_hybrid_obstacle_detection()
        example10_environment_variables()
        
        print("\n\n✅ 모든 예제 완료!")
        print("\n📚 추가 문서:")
        print("  - LIDAR_GUIDE.md")
        print("  - CONFIG_LOADER_GUIDE.md")
        print("  - LOGGER_GUIDE.md")
        print("  - HARDWARE_CONFIG_INTEGRATION.md")
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
