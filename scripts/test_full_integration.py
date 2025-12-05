#!/usr/bin/env python3
"""
전체 시스템 통합 테스트
모든 모듈이 올바르게 연동되는지 확인
"""

import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*70)
print("🔍 AiCane Navigation 전체 시스템 통합 테스트")
print("="*70)

# 테스트 결과 저장
results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_section(name):
    """테스트 섹션 출력"""
    print(f"\n{'='*70}")
    print(f"📋 {name}")
    print("="*70)

def test_pass(message):
    """테스트 통과"""
    print(f"  ✅ {message}")
    results['passed'].append(message)

def test_fail(message, error=None):
    """테스트 실패"""
    print(f"  ❌ {message}")
    if error:
        print(f"     오류: {error}")
    results['failed'].append(message)

def test_warn(message):
    """경고"""
    print(f"  ⚠️  {message}")
    results['warnings'].append(message)


# ============================================================================
# 1. 모듈 Import 테스트
# ============================================================================
test_section("1️⃣ 모듈 Import 테스트")

# Core 모듈
try:
    from aicane_navigation.core import CoordinateConverter, SpeedProfile, MovingAverageFilter
    test_pass("core 모듈 (CoordinateConverter, SpeedProfile, MovingAverageFilter)")
except Exception as e:
    test_fail("core 모듈", e)

# Hardware 모듈
try:
    from aicane_navigation.hardware import RobokitDriver, LidarInterface
    test_pass("hardware 모듈 (RobokitDriver, LidarInterface)")
except Exception as e:
    test_fail("hardware 모듈", e)

# Mapping 모듈
try:
    from aicane_navigation.mapping import FloorPlan
    test_pass("mapping 모듈 (FloorPlan)")
except Exception as e:
    test_fail("mapping 모듈", e)

try:
    from aicane_navigation.mapping import RoomManager, PathPlanner
    test_pass("mapping 모듈 (RoomManager, PathPlanner)")
except Exception as e:
    test_warn("mapping 고급 모듈 (RoomManager, PathPlanner) - 선택 사항")

# Localization 모듈
try:
    from aicane_navigation.localization import SimpleOdometry, UltrasonicLocalizer, ThreeTierLocalization
    test_pass("localization 모듈 (Odometry, UltrasonicLocalizer, ThreeTierLocalization)")
except Exception as e:
    test_fail("localization 모듈", e)

# Obstacle 모듈
try:
    from aicane_navigation.obstacle import UltrasonicObstacleDetector, ObstacleAvoidanceSystem
    test_pass("obstacle 모듈 (UltrasonicObstacleDetector, ObstacleAvoidanceSystem)")
except Exception as e:
    test_fail("obstacle 모듈", e)

try:
    from aicane_navigation.obstacle import LidarObstacleDetector
    test_pass("obstacle 모듈 (LidarObstacleDetector)")
except Exception as e:
    test_warn("LiDAR 장애물 감지 - 선택 사항")

# Navigation 모듈
try:
    from aicane_navigation.navigation import ObstacleAwareWaypointFollower
    test_pass("navigation 모듈 (ObstacleAwareWaypointFollower)")
except Exception as e:
    test_fail("navigation 모듈", e)

try:
    from aicane_navigation.navigation import SimpleSlipCorrector, AdaptiveSlipCompensator
    test_pass("navigation 모듈 (SimpleSlipCorrector, AdaptiveSlipCompensator)")
except Exception as e:
    test_warn("미끄러짐 보정 - 신규 기능")

# Utils 모듈
try:
    from aicane_navigation.utils import NavigationLogger, ConfigLoader
    test_pass("utils 모듈 (NavigationLogger, ConfigLoader)")
except Exception as e:
    test_fail("utils 모듈", e)

# NavigationSystem
try:
    from aicane_navigation import NavigationSystem
    test_pass("NavigationSystem (메인 클래스)")
except Exception as e:
    test_fail("NavigationSystem", e)


# ============================================================================
# 2. NavigationSystem 초기화 테스트
# ============================================================================
test_section("2️⃣ NavigationSystem 초기화 테스트")

try:
    from aicane_navigation import NavigationSystem
    
    print("\n  Mock 모드로 초기화 중...")
    nav = NavigationSystem(mock=True)
    
    # 컴포넌트 확인
    assert nav.robot is not None, "robot 컴포넌트 없음"
    test_pass("robot 컴포넌트 초기화")
    
    assert nav.floor_map is not None, "floor_map 컴포넌트 없음"
    test_pass("floor_map 컴포넌트 초기화")
    
    assert nav.localization is not None, "localization 컴포넌트 없음"
    test_pass("localization 컴포넌트 초기화")
    
    assert nav.obstacle_system is not None, "obstacle_system 컴포넌트 없음"
    test_pass("obstacle_system 컴포넌트 초기화")
    
    assert nav.follower is not None, "follower 컴포넌트 없음"
    test_pass("follower 컴포넌트 초기화")
    
    test_pass("NavigationSystem 전체 초기화 성공")
    
except Exception as e:
    test_fail("NavigationSystem 초기화", e)
    import traceback
    traceback.print_exc()


# ============================================================================
# 3. 좌표 변환 테스트
# ============================================================================
test_section("3️⃣ 좌표 변환 테스트")

try:
    from aicane_navigation.core import CoordinateConverter
    
    # 픽셀 → cm
    px, py = 100, 200
    cx, cy = CoordinateConverter.pixel_to_cm(px, py)
    
    assert cx == 380 and cy == 760, f"변환 오류: ({cx}, {cy}) != (380, 760)"
    test_pass(f"픽셀 → cm 변환: ({px}, {py}) → ({cx}, {cy})")
    
    # cm → 픽셀 (역변환)
    px2, py2 = CoordinateConverter.cm_to_pixel(cx, cy)
    
    error = abs(px - px2) + abs(py - py2)
    assert error < 0.1, f"역변환 오차: {error}"
    test_pass(f"cm → 픽셀 역변환: 오차 {error:.4f}")
    
except Exception as e:
    test_fail("좌표 변환", e)


# ============================================================================
# 4. 속도 프로파일 테스트
# ============================================================================
test_section("4️⃣ 속도 프로파일 테스트")

try:
    from aicane_navigation.core import SpeedProfile
    
    # 레벨 → 속도
    level = 10
    speed = SpeedProfile.get_speed(level, 'forward')
    
    assert 0.05 < speed < 0.15, f"속도 범위 오류: {speed}"
    test_pass(f"레벨 {level} → 속도 {speed:.4f} m/s")
    
    # 속도 → 레벨
    target_speed = 0.07
    level2 = SpeedProfile.get_level_for_speed(target_speed, 'forward')
    
    test_pass(f"목표 {target_speed} m/s → 레벨 {level2}")
    
except Exception as e:
    test_fail("속도 프로파일", e)


# ============================================================================
# 5. 맵 데이터 테스트
# ============================================================================
test_section("5️⃣ 맵 데이터 테스트")

try:
    from aicane_navigation.mapping import FloorPlan
    
    floor_map = FloorPlan()
    
    # 복도 체크
    in_corridor = floor_map.is_in_corridor(380, 1312)
    assert in_corridor, "복도 판정 실패"
    test_pass(f"복도 체크: (380, 1312) = 복도")
    
    # 방 위치
    x, y, theta = floor_map.get_room_waypoint('101호')
    test_pass(f"방 위치: 101호 = ({x:.0f}, {y:.0f}, {theta:.2f}rad)")
    
    # 경로 생성
    path = floor_map.generate_simple_path('101호', '107호', spacing_cm=100)
    assert len(path) > 0, "경로 생성 실패"
    test_pass(f"경로 생성: 101호 → 107호 = {len(path)}개 포인트")
    
except Exception as e:
    test_fail("맵 데이터", e)


# ============================================================================
# 6. 위치 추정 테스트
# ============================================================================
test_section("6️⃣ 위치 추정 테스트")

try:
    from aicane_navigation.hardware import RobokitDriver
    from aicane_navigation.mapping import FloorPlan
    from aicane_navigation.localization import SimpleOdometry, UltrasonicLocalizer, ThreeTierLocalization
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    # 오도메트리
    odometry = SimpleOdometry()
    odometry.reset(0, 0, 0)
    test_pass("오도메트리 초기화")
    
    # 초음파 위치 추정
    ultrasonic = UltrasonicLocalizer(robot, floor_map)
    test_pass("초음파 위치 추정 초기화")
    
    # 3-Tier 시스템
    localization = ThreeTierLocalization(robot, ultrasonic, odometry)
    localization.reset_position(380, 500, 0)
    x, y, theta, tier, conf = localization.update()
    test_pass(f"3-Tier 위치 추정: Tier {tier}, 신뢰도 {conf:.2f}")
    
    robot.close()
    
except Exception as e:
    test_fail("위치 추정", e)


# ============================================================================
# 7. 장애물 감지 테스트
# ============================================================================
test_section("7️⃣ 장애물 감지 테스트")

try:
    from aicane_navigation.hardware import RobokitDriver
    from aicane_navigation.mapping import FloorPlan
    from aicane_navigation.obstacle import UltrasonicObstacleDetector, ObstacleAvoidanceSystem
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    # 초음파 장애물 감지
    detector = UltrasonicObstacleDetector(robot)
    result = detector.check_obstacles()
    test_pass(f"초음파 장애물 감지: {result['action']}")
    
    # 통합 회피 시스템
    avoidance = ObstacleAvoidanceSystem(robot, floor_map)
    result = avoidance.check_and_respond((380, 500, 0), (380, 1000))
    test_pass(f"장애물 회피 시스템: {result['action']}")
    
    robot.close()
    
except Exception as e:
    test_fail("장애물 감지", e)


# ============================================================================
# 8. 경로 추종 시뮬레이션
# ============================================================================
test_section("8️⃣ 경로 추종 시뮬레이션")

try:
    from aicane_navigation import NavigationSystem
    
    nav = NavigationSystem(mock=True)
    
    # AI 경로 테스트
    print("\n  AI 경로 추종 테스트:")
    ai_path = [(100, 314), (200, 314), (300, 314)]
    
    # 픽셀 → cm 변환 확인
    from aicane_navigation.core import CoordinateConverter
    waypoints = CoordinateConverter.path_pixel_to_cm(ai_path)
    test_pass(f"AI 경로 변환: {len(ai_path)}개 픽셀 → {len(waypoints)}개 cm")
    
    # 방 간 이동 경로 생성
    print("\n  방 간 이동 경로 테스트:")
    path = nav.floor_map.generate_simple_path('101호', '107호')
    test_pass(f"방 간 경로: 101호 → 107호 = {len(path)}개 포인트")
    
    nav.shutdown()
    
except Exception as e:
    test_fail("경로 추종 시뮬레이션", e)


# ============================================================================
# 9. 설정 파일 테스트
# ============================================================================
test_section("9️⃣ 설정 파일 테스트")

try:
    import os
    
    config_files = [
        './config/hardware.yaml',
        './config/navigation.yaml',
        './config/obstacle.yaml'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            test_pass(f"설정 파일 존재: {config_file}")
        else:
            test_warn(f"설정 파일 없음: {config_file}")
    
except Exception as e:
    test_fail("설정 파일", e)


# ============================================================================
# 10. 결과 요약
# ============================================================================
test_section("📊 테스트 결과 요약")

print(f"\n  ✅ 통과: {len(results['passed'])}개")
print(f"  ❌ 실패: {len(results['failed'])}개")
print(f"  ⚠️  경고: {len(results['warnings'])}개")

if results['failed']:
    print(f"\n  ❌ 실패한 테스트:")
    for i, test in enumerate(results['failed'], 1):
        print(f"     {i}. {test}")

if results['warnings']:
    print(f"\n  ⚠️  경고 사항:")
    for i, test in enumerate(results['warnings'], 1):
        print(f"     {i}. {test}")

print("\n" + "="*70)

if len(results['failed']) == 0:
    print("🎉 모든 필수 테스트 통과!")
    print("="*70)
    print("\n✅ 시스템이 정상적으로 작동할 준비가 되었습니다!")
    print("\n다음 단계:")
    print("  1. Mock 모드로 주행 테스트: python examples/basic_usage.py")
    print("  2. 하드웨어 연결 테스트: python scripts/test_hardware.py")
    print("  3. 실제 주행: ./launch/start_navigation.sh --from 101호 --to 107호")
    sys.exit(0)
else:
    print("⚠️ 일부 테스트가 실패했습니다.")
    print("="*70)
    print("\n수정이 필요한 부분이 있습니다.")
    sys.exit(1)
