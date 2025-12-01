"""
AiCane Navigation 사용 예제
"""

from aicane_navigation import NavigationSystem
import time


def example1_simple_rooms():
    """예제 1: 간단한 방 간 이동"""
    print("=" * 60)
    print("예제 1: 방 간 이동 (101호 → 107호)")
    print("=" * 60 + "\n")
    
    # 시스템 초기화 (Mock 모드)
    nav = NavigationSystem(mock=True)
    
    # 이동
    nav.navigate_rooms('101호', '107호')
    
    # 종료
    nav.shutdown()


def example2_ai_path():
    """예제 2: AI 경로 추종"""
    print("\n" + "=" * 60)
    print("예제 2: AI 픽셀 경로 추종")
    print("=" * 60 + "\n")
    
    nav = NavigationSystem(mock=True)
    
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
    
    nav = NavigationSystem(mock=True)
    
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
    
    nav = NavigationSystem(mock=True)
    
    # JSON 파일 로드
    with open('./maps/example_path.json', 'r') as f:
        data = json.load(f)
    
    pixel_path = [(p['x'], p['y']) for p in data['waypoints']]
    
    nav.navigate_ai_path(pixel_path)
    
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


if __name__ == '__main__':
    try:
        example1_simple_rooms()
        example2_ai_path()
        example3_custom_path()
        example4_json_path()
        example5_realtime_monitoring()
        
        print("\n\n✅ 모든 예제 완료!")
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
