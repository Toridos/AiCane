#!/usr/bin/env python3
"""
전체 시스템 통합 테스트
모든 모듈이 제대로 작동하는지 확인
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """모듈 Import 테스트"""
    print("\n" + "="*60)
    print("1️⃣ Import 테스트")
    print("="*60)
    
    try:
        from aicane_navigation import NavigationSystem
        from aicane_navigation.core import CoordinateConverter, SpeedProfile, MovingAverageFilter
        from aicane_navigation.hardware import RobokitDriver
        from aicane_navigation.mapping import FloorPlan
        from aicane_navigation.localization import SimpleOdometry, UltrasonicLocalizer, ThreeTierLocalization
        from aicane_navigation.obstacle import UltrasonicObstacleDetector, ObstacleVsSlipDetector, ObstacleAvoidanceSystem
        from aicane_navigation.navigation import ObstacleAwareWaypointFollower
        
        print("✅ 모든 모듈 Import 성공!")
        return True
    except Exception as e:
        print(f"❌ Import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coordinate_conversion():
    """좌표 변환 테스트"""
    print("\n" + "="*60)
    print("2️⃣ 좌표 변환 테스트")
    print("="*60)
    
    from aicane_navigation.core import CoordinateConverter
    
    # 픽셀 → cm
    px, py = 100, 200
    cx, cy = CoordinateConverter.pixel_to_cm(px, py)
    print(f"픽셀 ({px}, {py}) → cm ({cx}, {cy})")
    
    # cm → 픽셀 (역변환)
    px2, py2 = CoordinateConverter.cm_to_pixel(cx, cy)
    print(f"cm ({cx}, {cy}) → 픽셀 ({px2:.1f}, {py2:.1f})")
    
    # 오차 확인
    error = abs(px - px2) + abs(py - py2)
    if error < 0.1:
        print("✅ 좌표 변환 정상!")
        return True
    else:
        print(f"❌ 오차 발생: {error}")
        return False


def test_speed_profile():
    """속도 프로파일 테스트"""
    print("\n" + "="*60)
    print("3️⃣ 속도 프로파일 테스트")
    print("="*60)
    
    from aicane_navigation.core import SpeedProfile
    
    # 레벨 → 속도
    level = 10
    speed = SpeedProfile.get_speed(level, 'forward')
    print(f"레벨 {level} → 속도 {speed:.4f} m/s")
    
    # 속도 → 레벨
    target_speed = 0.07
    level2 = SpeedProfile.get_level_for_speed(target_speed, 'forward')
    print(f"목표 {target_speed} m/s → 레벨 {level2}")
    
    print("✅ 속도 프로파일 정상!")
    return True


def test_floor_plan():
    """맵 테스트"""
    print("\n" + "="*60)
    print("4️⃣ 맵 데이터 테스트")
    print("="*60)
    
    from aicane_navigation.mapping import FloorPlan
    
    floor_map = FloorPlan()
    
    # 복도 체크
    in_corridor = floor_map.is_in_corridor(380, 1312)
    print(f"(380, 1312) 복도 여부: {in_corridor}")
    
    # 방 위치
    x, y, theta = floor_map.get_room_waypoint('101호')
    print(f"101호 문 앞: ({x:.0f}, {y:.0f})")
    
    # 경로 생성
    path = floor_map.generate_simple_path('101호', '107호', 100)
    print(f"101호→107호 경로: {len(path)}개 포인트")
    
    print("✅ 맵 데이터 정상!")
    return True


def test_navigation_system():
    """통합 시스템 테스트"""
    print("\n" + "="*60)
    print("5️⃣ 통합 시스템 테스트 (Mock 모드)")
    print("="*60)
    
    from aicane_navigation import NavigationSystem
    
    try:
        # 시스템 초기화
        nav = NavigationSystem(mock=True)
        print("✅ 시스템 초기화 성공!")
        
        # 시작 위치 설정
        nav.set_start_position_from_room('101호')
        print("✅ 시작 위치 설정 성공!")
        
        # 종료
        nav.shutdown()
        print("✅ 시스템 종료 성공!")
        
        return True
    
    except Exception as e:
        print(f"❌ 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print(" 🧪 AiCane Navigation 통합 테스트")
    print("="*60)
    
    tests = [
        ("Import", test_imports),
        ("좌표 변환", test_coordinate_conversion),
        ("속도 프로파일", test_speed_profile),
        ("맵 데이터", test_floor_plan),
        ("통합 시스템", test_navigation_system),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 테스트 중 오류: {e}")
            results.append((name, False))
    
    # 결과 요약
    print("\n" + "="*60)
    print(" 📊 테스트 결과")
    print("="*60)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {total-passed}개 테스트 실패")
        return 1


if __name__ == '__main__':
    sys.exit(main())
