"""
AiCane Navigation 통합 테스트
모든 모듈 기능 검증
"""

import sys
import time


def test_core_modules():
    """Core 모듈 테스트"""
    print("\n" + "="*60)
    print("1️⃣ Core 모듈 테스트")
    print("="*60)
    
    from aicane_navigation.core import (
        CoordinateConverter,
        SpeedProfile,
        MovingAverageFilter
    )
    
    # 좌표 변환
    print("\n  좌표 변환:")
    px, py = 100, 200
    cx, cy = CoordinateConverter.pixel_to_cm(px, py)
    print(f"    픽셀 ({px}, {py}) → cm ({cx}, {cy})")
    assert cx == 380 and cy == 760, "좌표 변환 실패!"
    
    # 속도 프로파일
    print("\n  속도 프로파일:")
    speed = SpeedProfile.get_speed(10, 'forward')
    print(f"    레벨 10 전진 속도: {speed:.4f} m/s")
    assert 0.05 < speed < 0.1, "속도 계산 실패!"
    
    # 필터
    print("\n  이동 평균 필터:")
    filter = MovingAverageFilter(3)
    values = [10, 12, 11, 13, 12]
    for v in values:
        filtered = filter.update(v)
    print(f"    필터 결과: {filtered:.1f}")
    
    print("  ✅ Core 모듈 정상")


def test_hardware():
    """Hardware 모듈 테스트"""
    print("\n" + "="*60)
    print("2️⃣ Hardware 모듈 테스트")
    print("="*60)
    
    from aicane_navigation.hardware import RobokitDriver
    
    robot = RobokitDriver(mock=True)
    
    # 초음파
    print("\n  초음파 센서:")
    distances = robot.get_ultrasonic()
    print(f"    정면: {distances['front']:.1f}cm")
    print(f"    좌: {distances['left']:.1f}cm")
    print(f"    우: {distances['right']:.1f}cm")
    
    # 모션
    print("\n  모션 제어:")
    robot.set_motion('FORWARD', 10)
    print("    FORWARD 명령 전송")
    time.sleep(0.1)
    robot.stop()
    
    robot.close()
    print("  ✅ Hardware 모듈 정상")


def test_mapping():
    """Mapping 모듈 테스트"""
    print("\n" + "="*60)
    print("3️⃣ Mapping 모듈 테스트")
    print("="*60)
    
    from aicane_navigation.mapping import FloorPlan
    import math
    
    floor_map = FloorPlan()
    
    # 복도 체크
    print("\n  복도 체크:")
    in_corridor = floor_map.is_in_corridor(380, 1312)
    print(f"    (380, 1312): {'복도' if in_corridor else '복도 아님'}")
    assert in_corridor, "복도 판정 실패!"
    
    # 방 위치
    print("\n  방 위치:")
    x, y, theta = floor_map.get_room_waypoint('101호')
    print(f"    101호: ({x:.0f}, {y:.0f}), {math.degrees(theta):.0f}°")
    
    # 경로 생성
    print("\n  경로 생성:")
    path = floor_map.generate_simple_path('101호', '107호')
    print(f"    101호 → 107호: {len(path)}개 웨이포인트")
    
    print("  ✅ Mapping 모듈 정상")


def test_localization():
    """Localization 모듈 테스트"""
    print("\n" + "="*60)
    print("4️⃣ Localization 모듈 테스트")
    print("="*60)
    
    from aicane_navigation.hardware import RobokitDriver
    from aicane_navigation.mapping import FloorPlan
    from aicane_navigation.localization import (
        SimpleOdometry,
        UltrasonicLocalizer,
        ThreeTierLocalization
    )
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    # 오도메트리
    print("\n  오도메트리:")
    odometry = SimpleOdometry()
    odometry.reset(0, 0, 0)
    odometry.update_from_command('FORWARD', 10, 1.0)
    x, y, theta = odometry.get_pose()
    print(f"    1초 전진 후: ({x:.1f}, {y:.1f})")
    
    # 초음파
    print("\n  초음파 위치 보정:")
    ultrasonic = UltrasonicLocalizer(robot, floor_map)
    x, y, theta, conf = ultrasonic.get_corrected_pose(380, 500, 0)
    print(f"    보정 위치: ({x:.1f}, {y:.1f}), 신뢰도: {conf:.2f}")
    
    # 3-Tier
    print("\n  3-Tier 시스템:")
    localization = ThreeTierLocalization(robot, ultrasonic, odometry)
    localization.reset_position(380, 500, 0)
    x, y, theta, tier, conf = localization.update()
    print(f"    Tier {tier}: ({x:.1f}, {y:.1f}), 신뢰도: {conf:.2f}")
    
    robot.close()
    print("  ✅ Localization 모듈 정상")


def test_obstacle():
    """Obstacle 모듈 테스트"""
    print("\n" + "="*60)
    print("5️⃣ Obstacle 모듈 테스트")
    print("="*60)
    
    from aicane_navigation.hardware import RobokitDriver
    from aicane_navigation.mapping import FloorPlan
    from aicane_navigation.obstacle import (
        UltrasonicObstacleDetector,
        ObstacleVsSlipDetector,
        ObstacleAvoidanceSystem
    )
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    # 초음파 장애물 감지
    print("\n  초음파 장애물 감지:")
    detector = UltrasonicObstacleDetector(robot)
    result = detector.check_obstacles()
    print(f"    액션: {result['action']}")
    print(f"    정면 상태: {result['front']['status']}")
    
    # 미끄러짐 구분
    print("\n  미끄러짐 구분:")
    slip_detector = ObstacleVsSlipDetector(floor_map)
    current = {'left': 120, 'right': 80}
    expected = {'left': 120, 'right': 120}
    history = {'left': [120], 'right': [120]}
    result = slip_detector.analyze_ultrasonic_change(
        current, expected, history, (0, 0, 0)
    )
    print(f"    오른쪽: {result['right']['type']}")
    
    # 통합 회피
    print("\n  통합 회피 시스템:")
    avoidance = ObstacleAvoidanceSystem(robot, floor_map)
    result = avoidance.check_and_respond((380, 500, 0), (380, 1000))
    print(f"    결과: {result['action']}")
    
    robot.close()
    print("  ✅ Obstacle 모듈 정상")


def test_navigation():
    """Navigation 모듈 테스트"""
    print("\n" + "="*60)
    print("6️⃣ Navigation 모듈 테스트")
    print("="*60)
    
    from aicane_navigation.hardware import RobokitDriver
    from aicane_navigation.mapping import FloorPlan
    from aicane_navigation.localization import (
        SimpleOdometry,
        UltrasonicLocalizer,
        ThreeTierLocalization
    )
    from aicane_navigation.obstacle import ObstacleAvoidanceSystem
    from aicane_navigation.navigation import ObstacleAwareWaypointFollower
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    ultrasonic = UltrasonicLocalizer(robot, floor_map)
    odometry = SimpleOdometry()
    localization = ThreeTierLocalization(robot, ultrasonic, odometry)
    
    obstacles = ObstacleAvoidanceSystem(robot, floor_map)
    
    follower = ObstacleAwareWaypointFollower(robot, localization, obstacles)
    
    # 경로 설정
    print("\n  경로 추종:")
    path = [(0, 0), (100, 0), (200, 0)]
    follower.load_path(path)
    localization.reset_position(0, 0, 0)
    
    # 5 스텝 진행
    for i in range(5):
        follower.follow_step()
        time.sleep(0.1)
    
    follower.stop()
    
    robot.close()
    print("  ✅ Navigation 모듈 정상")


def test_integration():
    """통합 테스트"""
    print("\n" + "="*60)
    print("7️⃣ 통합 시스템 테스트")
    print("="*60)
    
    from aicane_navigation import NavigationSystem
    
    nav = NavigationSystem(mock=True)
    
    # AI 경로
    print("\n  AI 경로 추종:")
    ai_path = [(100, 314), (200, 314), (300, 314)]
    nav.navigate_ai_path(ai_path)
    
    nav.shutdown()
    print("  ✅ 통합 시스템 정상")


def main():
    print("\n" + "🧪 AiCane Navigation 통합 테스트")
    print("="*60)
    
    tests = [
        ("Core", test_core_modules),
        ("Hardware", test_hardware),
        ("Mapping", test_mapping),
        ("Localization", test_localization),
        ("Obstacle", test_obstacle),
        ("Navigation", test_navigation),
        ("Integration", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n  ❌ {name} 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 결과
    print("\n" + "="*60)
    print(f"테스트 결과: {passed}/{len(tests)} 성공")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {failed}개 테스트 실패")
        return 1


if __name__ == '__main__':
    sys.exit(main())
