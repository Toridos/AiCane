#!/usr/bin/env python3
"""
예제: LiDAR 360도 장애물 감지

LiDAR를 사용한 고급 장애물 감지 기능:
- 360도 전방위 감지
- 섹터별 분석 (8방향)
- 경로 상 장애물 감지
- 통과 가능 경로 자동 발견
- 초음파 통합 (하이브리드)
"""

from aicane_navigation import NavigationSystem
from aicane_navigation.utils import ConfigLoader, NavigationLogger


def check_lidar_status():
    """LiDAR 상태 확인"""
    print("=" * 60)
    print("LiDAR 상태 확인")
    print("=" * 60 + "\n")
    
    # 설정 로드
    hw_config = ConfigLoader.load_hardware_config()
    
    print("📡 LiDAR 설정:")
    print(f"  활성화: {hw_config['lidar']['enabled']}")
    print(f"  포트: {hw_config['lidar']['port']}")
    print(f"  모델: {hw_config['lidar']['model']}")
    print(f"  속도: {hw_config['lidar']['baudrate']} baud")
    print(f"  스캔 속도: {hw_config['lidar']['scan_rate']} Hz")
    
    # 시스템 초기화
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # 실제 LiDAR 상태
    lidar_status = nav.get_lidar_status()
    
    print(f"\n🔌 실제 연결 상태:")
    print(f"  연결: {lidar_status['connected']}")
    print(f"  스캔 중: {lidar_status['scanning']}")
    
    if lidar_status['scanning']:
        print(f"  포인트 수: {lidar_status['num_points']}")
    
    nav.shutdown()


def test_360_detection():
    """360도 장애물 감지 테스트"""
    print("\n" + "=" * 60)
    print("360도 장애물 감지 테스트")
    print("=" * 60 + "\n")
    
    from aicane_navigation.hardware import LidarInterface
    from aicane_navigation.obstacle import LidarObstacleDetector
    
    # LiDAR 초기화
    lidar = LidarInterface(mock=True)
    lidar.open()
    lidar.start_scan()
    
    # 감지기
    detector = LidarObstacleDetector(lidar, min_distance=50.0)
    
    # 스캔
    scan = lidar.get_latest_scan()
    
    print(f"📊 스캔 데이터: {len(scan)}개 포인트\n")
    
    # 1. 기본 감지
    result = detector.detect(scan)
    
    print("1️⃣ 가장 가까운 장애물:")
    print(f"  방향: {result['direction']}")
    print(f"  거리: {result['distance']:.1f}cm")
    print(f"  각도: {result['angle']:.1f}°")
    
    # 2. 섹터별 분석
    sectors = detector.detect_by_sectors(scan)
    
    print("\n2️⃣ 섹터별 장애물 (8방향):")
    for direction, info in sectors['sectors'].items():
        obstacle = "⚠️" if info['obstacle'] else "✅"
        print(f"  {direction:12s}: {obstacle} {info['min_distance']:5.1f}cm")
    
    # 3. 경로 상 장애물
    path_result = detector.detect_in_path(scan, path_angle=0, path_width=60)
    
    print("\n3️⃣ 진행 방향 장애물 (정면 ±30°):")
    print(f"  장애물: {path_result['obstacle']}")
    print(f"  최소 거리: {path_result['min_distance']:.1f}cm")
    print(f"  권장: {path_result['recommended_action']}")
    
    # 4. 통과 가능 경로
    gaps = detector.find_clear_paths(scan, min_gap_width=80)
    
    print("\n4️⃣ 통과 가능 경로:")
    if gaps:
        for i, gap in enumerate(gaps[:3], 1):
            print(f"  경로 {i}: {gap['center_angle']:5.1f}° "
                  f"(폭: {gap['gap_width']:.1f}°, "
                  f"거리: {gap['min_distance']:.1f}cm)")
    else:
        print("  통과 가능 경로 없음")
    
    # 종료
    lidar.stop_scan()
    lidar.close()


def test_hybrid_detection():
    """하이브리드 장애물 감지 (초음파 + LiDAR)"""
    print("\n" + "=" * 60)
    print("하이브리드 장애물 감지")
    print("=" * 60 + "\n")
    
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
    combined = detector.combine_with_ultrasonic(lidar_result, us_result)
    
    print("🔍 감지 결과:")
    print(f"\n1️⃣ 초음파:")
    print(f"  장애물: {us_result['obstacle']}")
    print(f"  정면: {us_result['front']:.1f}cm")
    print(f"  좌측: {us_result['left']:.1f}cm")
    print(f"  우측: {us_result['right']:.1f}cm")
    
    print(f"\n2️⃣ LiDAR:")
    print(f"  장애물: {lidar_result['obstacle']}")
    print(f"  최소 거리: {lidar_result['min_distance']:.1f}cm")
    
    print(f"\n3️⃣ 통합 (하이브리드):")
    print(f"  장애물: {combined['obstacle']}")
    print(f"  신뢰도: {combined['confidence']}")
    print(f"  권장: {combined['recommended_action']}")
    
    # 우회 경로
    if combined['obstacle']:
        gaps = detector.find_clear_paths(scan)
        if gaps:
            print(f"\n4️⃣ 우회 경로:")
            best_gap = gaps[0]
            print(f"  최적 각도: {best_gap['center_angle']:.1f}°")
            print(f"  폭: {best_gap['gap_width']:.1f}°")
            print(f"  거리: {best_gap['min_distance']:.1f}cm")
    
    # 종료
    lidar.stop_scan()
    lidar.close()
    robot.close()


def navigate_with_lidar():
    """LiDAR를 사용한 실제 주행"""
    print("\n" + "=" * 60)
    print("LiDAR 주행 테스트")
    print("=" * 60 + "\n")
    
    # 로거
    logger = NavigationLogger(
        name="lidar_nav",
        log_to_file=True,
        log_dir='./logs'
    )
    
    # 시스템 초기화
    nav = NavigationSystem(config_dir='./config', mock=True)
    
    # 설정 확인
    nav_config = ConfigLoader.load_navigation_config()
    mode = nav_config['obstacle_detection']['mode']
    
    logger.info(f"장애물 감지 모드: {mode}")
    
    # LiDAR 상태
    lidar_status = nav.get_lidar_status()
    logger.info(f"LiDAR 활성화: {lidar_status['enabled']}")
    
    if mode == 'hybrid':
        logger.info("✅ 하이브리드 모드!")
        logger.info("  - 초음파: 근거리 감지")
        logger.info("  - LiDAR: 360도 감지 + 우회 경로")
    
    # 주행
    logger.log_navigation_start("101호", "107호")
    
    try:
        nav.navigate_rooms('101호', '107호')
        logger.log_navigation_end(success=True)
    except Exception as e:
        logger.error(f"주행 실패: {e}")
        logger.log_navigation_end(success=False, reason=str(e))
    
    # 종료
    nav.shutdown()
    
    print(f"\n📁 로그 파일: {logger.log_file}")


if __name__ == '__main__':
    try:
        print("🚀 LiDAR 360도 장애물 감지 예제\n")
        
        # 1. 상태 확인
        check_lidar_status()
        
        # 2. 360도 감지
        test_360_detection()
        
        # 3. 하이브리드
        test_hybrid_detection()
        
        # 4. 실제 주행
        navigate_with_lidar()
        
        print("\n\n✅ 모든 테스트 완료!")
        print("\n📚 추가 문서:")
        print("  - LIDAR_GUIDE.md")
        print("  - LIDAR_VS_ULTRASONIC_GUIDE.md")
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
