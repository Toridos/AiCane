"""
NavigationLogger 모듈 테스트
로깅 시스템 기능 검증
"""

import sys
import os


def test_logger_creation():
    """로거 생성 테스트"""
    print("\n" + "="*60)
    print("1️⃣ 로거 생성")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    # 콘솔만
    print("\n  콘솔 전용 로거:")
    logger1 = NavigationLogger(name="test1", log_to_file=False)
    logger1.info("콘솔 전용 메시지")
    print("    ✅ 콘솔 로거 생성 성공")
    
    # 파일 + 콘솔
    print("\n  파일 + 콘솔 로거:")
    logger2 = NavigationLogger(
        name="test2",
        log_to_file=True,
        log_dir='./logs',
        level='DEBUG'
    )
    logger2.info("파일 + 콘솔 메시지")
    print(f"    ✅ 파일 로거 생성: {logger2.log_file}")
    
    assert logger2.log_file is not None, "로그 파일 생성 실패!"
    assert os.path.exists(logger2.log_file), "로그 파일 없음!"
    
    print("  ✅ 로거 생성 정상")


def test_log_position():
    """위치 로그 테스트"""
    print("\n" + "="*60)
    print("2️⃣ 위치 로그")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    logger = NavigationLogger(name="test_pos", log_to_file=False)
    
    print("\n  위치 로그:")
    
    # 기본 로그
    logger.log_position(
        pose=(456.0, 835.0, 90.0),
        tier=1,
        confidence=0.95
    )
    print("    ✅ 기본 위치 로그")
    
    # 추가 정보
    logger.log_position(
        pose=(760.0, 1242.0, 0.0),
        tier=2,
        confidence=0.75,
        extra={'tier': 2, 'source': 'odometry'}
    )
    print("    ✅ 추가 정보 포함")
    
    # 통계 확인
    stats = logger.get_stats()
    assert stats['positions_logged'] == 2, "위치 로그 카운트 오류!"
    
    print("  ✅ 위치 로그 정상")


def test_log_obstacle():
    """장애물 로그 테스트"""
    print("\n" + "="*60)
    print("3️⃣ 장애물 로그")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    logger = NavigationLogger(name="test_obs", log_to_file=False)
    
    print("\n  장애물 로그:")
    
    # 초음파
    logger.log_obstacle({
        'front': 45.0,
        'left': 120.0,
        'right': 98.0,
        'action': 'slow_down',
        'source': 'ultrasonic'
    }, severity="WARNING")
    print("    ✅ 초음파 장애물")
    
    # LiDAR
    logger.log_obstacle({
        'front': 50.0,
        'action': 'stop',
        'source': 'lidar'
    }, severity="ERROR")
    print("    ✅ LiDAR 장애물")
    
    # 통계 확인
    stats = logger.get_stats()
    assert stats['obstacles_logged'] == 2, "장애물 로그 카운트 오류!"
    
    print("  ✅ 장애물 로그 정상")


def test_log_command():
    """명령어 로그 테스트"""
    print("\n" + "="*60)
    print("4️⃣ 명령어 로그")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    logger = NavigationLogger(name="test_cmd", log_to_file=False)
    
    print("\n  명령어 로그:")
    
    logger.log_command('forward', 10)
    logger.log_command('left', 8, extra={'reason': 'turn'})
    logger.log_command('stop', 0)
    
    print("    ✅ 3개 명령어 로그")
    
    # 통계 확인
    stats = logger.get_stats()
    assert stats['commands_logged'] == 3, "명령어 로그 카운트 오류!"
    
    print("  ✅ 명령어 로그 정상")


def test_log_event():
    """이벤트 로그 테스트"""
    print("\n" + "="*60)
    print("5️⃣ 이벤트 로그")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    logger = NavigationLogger(name="test_event", log_to_file=False)
    
    print("\n  이벤트 로그:")
    
    # tier 방식 (팀원 제안)
    logger.log_event("시스템 시작", tier=1)
    logger.log_event("경로 재계획", tier=2, extra={'attempts': 3})
    print("    ✅ tier 방식")
    
    # 단축 메서드
    logger.debug("디버그 메시지")
    logger.info("정보 메시지")
    logger.warning("경고 메시지")
    logger.error("에러 메시지")
    print("    ✅ 단축 메서드")
    
    # 통계 확인
    stats = logger.get_stats()
    assert stats['events_logged'] >= 2, "이벤트 로그 카운트 오류!"
    
    print("  ✅ 이벤트 로그 정상")


def test_navigation_lifecycle():
    """주행 생명주기 로그 테스트"""
    print("\n" + "="*60)
    print("6️⃣ 주행 생명주기")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    logger = NavigationLogger(name="test_nav", log_to_file=False)
    
    print("\n  주행 시작:")
    logger.log_navigation_start("101호", "107호")
    
    print("\n  주행 중:")
    logger.log_position((456.0, 835.0, 90.0), tier=1, confidence=0.95)
    logger.log_command('forward', 10)
    logger.info("웨이포인트 도착")
    
    print("\n  주행 종료:")
    logger.log_navigation_end(success=True, reason="목적지 도착")
    
    print("\n  통계:")
    logger.print_stats()
    
    print("  ✅ 주행 생명주기 정상")


def test_log_file_save():
    """로그 파일 저장 테스트"""
    print("\n" + "="*60)
    print("7️⃣ 로그 파일 저장")
    print("="*60)
    
    from aicane_navigation.utils import NavigationLogger
    
    logger = NavigationLogger(
        name="test_save",
        log_to_file=True,
        log_dir='./logs'
    )
    
    # 로그 생성
    print("\n  로그 생성:")
    logger.info("테스트 메시지 1")
    logger.info("테스트 메시지 2")
    print("    ✅ 2개 메시지")
    
    # 파일 확인
    assert os.path.exists(logger.log_file), "로그 파일 없음!"
    print(f"    ✅ 파일 존재: {logger.log_file}")
    
    # 복사 저장
    backup_path = './logs/test_backup.log'
    logger.save_to_file(backup_path)
    
    assert os.path.exists(backup_path), "백업 파일 생성 실패!"
    print(f"    ✅ 백업 생성: {backup_path}")
    
    # 정리
    os.remove(backup_path)
    print("    ✅ 백업 파일 정리")
    
    print("  ✅ 로그 파일 저장 정상")


def test_global_logger():
    """전역 로거 테스트"""
    print("\n" + "="*60)
    print("8️⃣ 전역 로거")
    print("="*60)
    
    from aicane_navigation.utils import get_logger
    
    print("\n  전역 로거:")
    
    # 첫 번째 호출
    logger1 = get_logger("global_test")
    logger1.info("첫 번째 로거")
    
    # 두 번째 호출 (같은 인스턴스)
    logger2 = get_logger("global_test")
    logger2.info("두 번째 로거")
    
    # 같은 인스턴스인지 확인
    assert logger1 is logger2, "전역 로거 싱글톤 실패!"
    print("    ✅ 싱글톤 패턴 정상")
    
    print("  ✅ 전역 로거 정상")


def main():
    print("\n" + "🧪 NavigationLogger 모듈 테스트")
    print("="*60)
    
    tests = [
        ("로거 생성", test_logger_creation),
        ("위치 로그", test_log_position),
        ("장애물 로그", test_log_obstacle),
        ("명령어 로그", test_log_command),
        ("이벤트 로그", test_log_event),
        ("주행 생명주기", test_navigation_lifecycle),
        ("로그 파일 저장", test_log_file_save),
        ("전역 로거", test_global_logger),
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
        print("\n🎉 모든 Logger 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {failed}개 테스트 실패")
        return 1


if __name__ == '__main__':
    sys.exit(main())
