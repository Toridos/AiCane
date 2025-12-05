"""
LiDAR 모듈 테스트
360도 장애물 감지 기능 검증
"""

import sys


def test_lidar_interface():
    """LiDAR 인터페이스 테스트"""
    print("\n" + "="*60)
    print("1️⃣ LiDAR 인터페이스")
    print("="*60)
    
    from aicane_navigation.hardware import LidarInterface
    
    # Mock 모드로 테스트
    lidar = LidarInterface(mock=True)
    
    # 연결
    print("\n  연결:")
    lidar.open()
    print("    ✅ 포트 열기 성공")
    
    # 스캔 시작
    lidar.start_scan()
    print("    ✅ 스캔 시작")
    
    # 데이터 읽기
    scan = lidar.get_latest_scan()
    print(f"    ✅ 스캔 데이터: {len(scan)}개 포인트")
    
    # 종료
    lidar.stop_scan()
    lidar.close()
    print("    ✅ 종료 완료")
    
    assert len(scan) > 0, "스캔 데이터 없음!"
    print("\n  ✅ LiDAR 인터페이스 정상")


def test_lidar_obstacle_detector():
    """LiDAR 장애물 감지기 테스트"""
    print("\n" + "="*60)
    print("2️⃣ LiDAR 장애물 감지")
    print("="*60)
    
    from aicane_navigation.hardware import LidarInterface
    from aicane_navigation.obstacle import LidarObstacleDetector
    
    # LiDAR 초기화
    lidar = LidarInterface(mock=True)
    lidar.open()
    lidar.start_scan()
    
    # 감지기
    detector = LidarObstacleDetector(lidar, min_distance=50.0)
    
    # 1. 기본 감지
    print("\n  1. 기본 장애물 감지:")
    scan = lidar.get_latest_scan()
    result = detector.detect(scan)
    
    print(f"    방향: {result['direction']}")
    print(f"    거리: {result['distance']:.1f}cm")
    print(f"    각도: {result['angle']:.1f}°")
    
    assert 'direction' in result, "방향 정보 없음!"
    assert 'distance' in result, "거리 정보 없음!"
    
    # 2. 섹터별 분석
    print("\n  2. 섹터별 분석 (8방향):")
    sectors = detector.detect_by_sectors(scan)
    
    for direction in ['front', 'left', 'right', 'back']:
        info = sectors['sectors'][direction]
        print(f"    {direction}: {info['min_distance']:.1f}cm")
    
    assert 'sectors' in sectors, "섹터 정보 없음!"
    
    # 3. 경로 상 장애물
    print("\n  3. 진행 방향 장애물:")
    path_result = detector.detect_in_path(scan, path_angle=0, path_width=60)
    
    print(f"    장애물: {path_result['obstacle']}")
    print(f"    최소 거리: {path_result['min_distance']:.1f}cm")
    print(f"    권장: {path_result['recommended_action']}")
    
    assert 'recommended_action' in path_result, "권장 액션 없음!"
    
    # 4. 통과 가능 경로
    print("\n  4. 통과 가능 경로 찾기:")
    gaps = detector.find_clear_paths(scan, min_gap_width=80)
    
    print(f"    발견된 경로: {len(gaps)}개")
    if gaps:
        print(f"    최적 각도: {gaps[0]['center_angle']:.1f}°")
    
    # 종료
    lidar.stop_scan()
    lidar.close()
    
    print("\n  ✅ LiDAR 장애물 감지 정상")


def test_hybrid_detection():
    """하이브리드 감지 테스트 (초음파 + LiDAR)"""
    print("\n" + "="*60)
    print("3️⃣ 하이브리드 감지")
    print("="*60)
    
    from aicane_navigation.hardware import LidarInterface, RobokitDriver
    from aicane_navigation.obstacle import LidarObstacleDetector
    
    # 초기화
    robot = RobokitDriver(mock=True)
    lidar = LidarInterface(mock=True)
    lidar.open()
    lidar.start_scan()
    
    detector = LidarObstacleDetector(lidar, min_distance=50.0)
    
    # 초음파 결과 (가상)
    us_result = {
        'obstacle': True,
        'front': 45.0,
        'left': 120.0,
        'right': 98.0,
        'action': 'slow_down',
        'source': 'ultrasonic'
    }
    
    # LiDAR 결과
    scan = lidar.get_latest_scan()
    lidar_result = detector.detect_in_path(scan, path_angle=0)
    
    # 통합
    print("\n  통합 감지:")
    combined = detector.combine_with_ultrasonic(lidar_result, us_result)
    
    print(f"    초음파 장애물: {us_result['obstacle']}")
    print(f"    LiDAR 장애물: {lidar_result['obstacle']}")
    print(f"    통합 장애물: {combined['obstacle']}")
    print(f"    신뢰도: {combined['confidence']}")
    
    assert 'confidence' in combined, "신뢰도 정보 없음!"
    
    # 종료
    lidar.stop_scan()
    lidar.close()
    robot.close()
    
    print("  ✅ 하이브리드 감지 정상")


def test_lidar_config():
    """LiDAR 설정 테스트"""
    print("\n" + "="*60)
    print("4️⃣ LiDAR 설정")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    # 하드웨어 설정
    hw_config = ConfigLoader.load_hardware_config()
    
    print("\n  설정 확인:")
    print(f"    활성화: {hw_config['lidar']['enabled']}")
    print(f"    포트: {hw_config['lidar']['port']}")
    print(f"    모델: {hw_config['lidar']['model']}")
    print(f"    속도: {hw_config['lidar']['baudrate']} baud")
    
    assert 'lidar' in hw_config, "LiDAR 설정 없음!"
    assert 'enabled' in hw_config['lidar'], "enabled 설정 없음!"
    
    # 네비게이션 설정
    nav_config = ConfigLoader.load_navigation_config()
    
    print(f"\n  장애물 감지:")
    print(f"    모드: {nav_config['obstacle_detection']['mode']}")
    print(f"    LiDAR 최소거리: {nav_config['obstacle_detection']['lidar']['min_distance']}cm")
    
    assert 'obstacle_detection' in nav_config, "obstacle_detection 설정 없음!"
    
    print("  ✅ LiDAR 설정 정상")


def main():
    print("\n" + "🧪 LiDAR 모듈 테스트")
    print("="*60)
    
    tests = [
        ("LiDAR 인터페이스", test_lidar_interface),
        ("장애물 감지", test_lidar_obstacle_detector),
        ("하이브리드 감지", test_hybrid_detection),
        ("LiDAR 설정", test_lidar_config),
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
        print("\n🎉 모든 LiDAR 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {failed}개 테스트 실패")
        return 1


if __name__ == '__main__':
    sys.exit(main())
