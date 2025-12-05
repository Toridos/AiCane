"""
ConfigLoader 모듈 테스트
설정 파일 로드 및 관리 기능 검증
"""

import sys
import os


def test_yaml_load():
    """YAML 로드 테스트"""
    print("\n" + "="*60)
    print("1️⃣ YAML 파일 로드")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    # 하드웨어 설정
    print("\n  하드웨어 설정:")
    hw_config = ConfigLoader.load_hardware_config()
    
    print(f"    로봇 포트: {hw_config['robot']['port']}")
    print(f"    LiDAR 포트: {hw_config['lidar']['port']}")
    print(f"    초음파 핀: {hw_config['ultrasonic']['pins']}")
    
    assert 'robot' in hw_config, "robot 설정 없음!"
    assert 'lidar' in hw_config, "lidar 설정 없음!"
    
    # 네비게이션 설정
    print("\n  네비게이션 설정:")
    nav_config = ConfigLoader.load_navigation_config()
    
    print(f"    제어 주기: {nav_config['control']['rate_hz']} Hz")
    print(f"    장애물 모드: {nav_config['obstacle_detection']['mode']}")
    
    assert 'control' in nav_config, "control 설정 없음!"
    assert 'obstacle_detection' in nav_config, "obstacle_detection 설정 없음!"
    
    print("  ✅ YAML 로드 정상")


def test_default_values():
    """기본값 테스트"""
    print("\n" + "="*60)
    print("2️⃣ 기본값 처리")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    # 존재하지 않는 파일
    print("\n  존재하지 않는 파일:")
    config = ConfigLoader.load_yaml(
        './config/nonexistent.yaml',
        default={'test': 'value', 'number': 42}
    )
    
    print(f"    test: {config['test']}")
    print(f"    number: {config['number']}")
    
    assert config['test'] == 'value', "기본값 적용 실패!"
    assert config['number'] == 42, "기본값 적용 실패!"
    
    print("  ✅ 기본값 처리 정상")


def test_environment_variables():
    """환경 변수 치환 테스트"""
    print("\n" + "="*60)
    print("3️⃣ 환경 변수 치환")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    # 환경 변수 설정
    os.environ['TEST_PORT'] = '/dev/ttyUSB0'
    os.environ['TEST_BAUD'] = '115200'
    
    # 치환 테스트
    print("\n  환경 변수 치환:")
    test_config = {
        'port': '${TEST_PORT}',
        'baudrate': '${TEST_BAUD}',
        'normal': 'no_change'
    }
    
    result = ConfigLoader._replace_env_vars(test_config)
    
    print(f"    port: {result['port']}")
    print(f"    baudrate: {result['baudrate']}")
    print(f"    normal: {result['normal']}")
    
    assert result['port'] == '/dev/ttyUSB0', "환경 변수 치환 실패!"
    assert result['baudrate'] == '115200', "환경 변수 치환 실패!"
    assert result['normal'] == 'no_change', "일반 값 변경됨!"
    
    print("  ✅ 환경 변수 치환 정상")


def test_nested_keys():
    """중첩 키 접근 테스트"""
    print("\n" + "="*60)
    print("4️⃣ 중첩 키 접근")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    config = {
        'robot': {
            'port': '/dev/ttyUSB0',
            'settings': {
                'baudrate': 9600,
                'timeout': 1.0
            }
        }
    }
    
    # 중첩 키 테스트
    print("\n  중첩 키 접근:")
    
    port = ConfigLoader.get_nested(config, 'robot.port')
    print(f"    robot.port: {port}")
    assert port == '/dev/ttyUSB0', "1단계 중첩 실패!"
    
    baudrate = ConfigLoader.get_nested(config, 'robot.settings.baudrate')
    print(f"    robot.settings.baudrate: {baudrate}")
    assert baudrate == 9600, "2단계 중첩 실패!"
    
    # 기본값 테스트
    missing = ConfigLoader.get_nested(config, 'robot.missing', default='default')
    print(f"    robot.missing (기본값): {missing}")
    assert missing == 'default', "기본값 처리 실패!"
    
    print("  ✅ 중첩 키 접근 정상")


def test_dict_merge():
    """딕셔너리 병합 테스트"""
    print("\n" + "="*60)
    print("5️⃣ 딕셔너리 병합")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    base = {
        'robot': {
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
            'timeout': 1.0
        },
        'lidar': {
            'enabled': False
        }
    }
    
    override = {
        'robot': {
            'baudrate': 19200  # 덮어쓰기
        },
        'lidar': {
            'enabled': True,   # 덮어쓰기
            'port': '/dev/ttyUSB1'  # 추가
        }
    }
    
    print("\n  병합:")
    merged = ConfigLoader._merge_dicts(base, override)
    
    print(f"    robot.port: {merged['robot']['port']} (base)")
    print(f"    robot.baudrate: {merged['robot']['baudrate']} (override)")
    print(f"    robot.timeout: {merged['robot']['timeout']} (base)")
    print(f"    lidar.enabled: {merged['lidar']['enabled']} (override)")
    print(f"    lidar.port: {merged['lidar']['port']} (override)")
    
    assert merged['robot']['port'] == '/dev/ttyUSB0', "base 값 손실!"
    assert merged['robot']['baudrate'] == 19200, "override 실패!"
    assert merged['robot']['timeout'] == 1.0, "base 값 손실!"
    assert merged['lidar']['enabled'] == True, "override 실패!"
    assert merged['lidar']['port'] == '/dev/ttyUSB1', "추가 실패!"
    
    print("  ✅ 딕셔너리 병합 정상")


def test_required_keys():
    """필수 키 검증 테스트"""
    print("\n" + "="*60)
    print("6️⃣ 필수 키 검증")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    
    config = {
        'robot': {
            'port': '/dev/ttyUSB0'
        },
        'lidar': {
            'enabled': True
        }
    }
    
    print("\n  필수 키 체크:")
    
    # 성공 케이스
    try:
        ConfigLoader._validate_keys(config, ['robot', 'lidar'])
        print("    ✅ 'robot', 'lidar' 존재")
    except ValueError as e:
        print(f"    ❌ 실패: {e}")
        assert False, "필수 키 검증 실패!"
    
    # 중첩 키
    try:
        ConfigLoader._validate_keys(config, ['robot.port', 'lidar.enabled'])
        print("    ✅ 'robot.port', 'lidar.enabled' 존재")
    except ValueError as e:
        print(f"    ❌ 실패: {e}")
        assert False, "중첩 키 검증 실패!"
    
    # 실패 케이스
    try:
        ConfigLoader._validate_keys(config, ['robot.missing'])
        print("    ❌ 없는 키가 통과됨!")
        assert False, "없는 키 검증 실패!"
    except ValueError:
        print("    ✅ 없는 키 정상 감지")
    
    print("  ✅ 필수 키 검증 정상")


def test_save_yaml():
    """YAML 저장 테스트"""
    print("\n" + "="*60)
    print("7️⃣ YAML 저장")
    print("="*60)
    
    from aicane_navigation.utils import ConfigLoader
    import os
    
    test_config = {
        'robot': {
            'port': '/dev/ttyUSB0',
            'baudrate': 9600
        },
        'test': True
    }
    
    # 저장
    print("\n  YAML 저장:")
    test_path = './logs/test_config.yaml'
    ConfigLoader.save_yaml(test_config, test_path)
    
    assert os.path.exists(test_path), "파일 생성 실패!"
    print(f"    ✅ 파일 생성: {test_path}")
    
    # 다시 로드
    loaded = ConfigLoader.load_yaml(test_path)
    
    assert loaded['robot']['port'] == '/dev/ttyUSB0', "로드 실패!"
    assert loaded['robot']['baudrate'] == 9600, "로드 실패!"
    print("    ✅ 로드 확인 성공")
    
    # 정리
    os.remove(test_path)
    print("    ✅ 테스트 파일 정리")
    
    print("  ✅ YAML 저장 정상")


def main():
    print("\n" + "🧪 ConfigLoader 모듈 테스트")
    print("="*60)
    
    tests = [
        ("YAML 로드", test_yaml_load),
        ("기본값 처리", test_default_values),
        ("환경 변수 치환", test_environment_variables),
        ("중첩 키 접근", test_nested_keys),
        ("딕셔너리 병합", test_dict_merge),
        ("필수 키 검증", test_required_keys),
        ("YAML 저장", test_save_yaml),
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
        print("\n🎉 모든 ConfigLoader 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {failed}개 테스트 실패")
        return 1


if __name__ == '__main__':
    sys.exit(main())
