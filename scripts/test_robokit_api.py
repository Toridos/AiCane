#!/usr/bin/env python3
"""
RobokitRS API 확인 스크립트
실제 하드웨어에서 어떤 방식이 맞는지 테스트
"""

import sys
import time


def test_import_methods():
    """Import 방식 테스트"""
    print("="*60)
    print("1️⃣  Import 방식 테스트")
    print("="*60 + "\n")
    
    # 방법 1
    print("방법 1: from RobokitRS import RobokitRS")
    try:
        from RobokitRS import RobokitRS
        print("✅ 성공!")
        method1_class = RobokitRS
    except Exception as e:
        print(f"❌ 실패: {e}")
        method1_class = None
    
    print()
    
    # 방법 2
    print("방법 2: from RobokitRS.RobokitRS import RobokitRS")
    try:
        from RobokitRS.RobokitRS import RobokitRS as RobokitRS2
        print("✅ 성공!")
        method2_class = RobokitRS2
    except Exception as e:
        print(f"❌ 실패: {e}")
        method2_class = None
    
    print()
    
    # 결론
    if method1_class and method2_class:
        print("💡 결론: 둘 다 가능!")
    elif method1_class:
        print("💡 결론: 방법 1 사용!")
    elif method2_class:
        print("💡 결론: 방법 2 사용!")
    else:
        print("❌ 둘 다 실패!")
        return None
    
    return method1_class or method2_class


def test_initialization_methods(RobokitClass, port='/dev/ttyUSB0'):
    """초기화 방식 테스트"""
    print("\n" + "="*60)
    print("2️⃣  초기화 방식 테스트")
    print("="*60 + "\n")
    
    # 방법 1: 생성자에 포트
    print(f"방법 1: RobokitRS(port='{port}')")
    try:
        robot1 = RobokitClass(port=port)
        print("✅ 성공!")
        robot1_ok = True
    except Exception as e:
        print(f"❌ 실패: {e}")
        robot1_ok = False
    
    print()
    
    # 방법 2: port_open()
    print(f"방법 2: RobokitRS() + port_open('{port}')")
    try:
        robot2 = RobokitClass()
        robot2.port_open(port)
        print("✅ 성공!")
        robot2_ok = True
    except Exception as e:
        print(f"❌ 실패: {e}")
        robot2_ok = False
    
    print()
    
    # 결론
    if robot1_ok and robot2_ok:
        print("💡 결론: 둘 다 가능!")
        return robot2  # port_open 방식 선호
    elif robot1_ok:
        print("💡 결론: 생성자 방식 사용!")
        return robot1
    elif robot2_ok:
        print("💡 결론: port_open 방식 사용!")
        return robot2
    else:
        print("❌ 둘 다 실패!")
        return None


def test_sensor_initialization(robot):
    """센서 초기화 필요 여부 테스트"""
    print("\n" + "="*60)
    print("3️⃣  센서 초기화 테스트")
    print("="*60 + "\n")
    
    test_pin = 12
    
    # sonar_begin 메서드 있는지 확인
    if not hasattr(robot, 'sonar_begin'):
        print("ℹ️  sonar_begin 메서드 없음 → 초기화 불필요")
        return False
    
    print(f"✅ sonar_begin 메서드 있음\n")
    
    # 초기화 전 읽기
    print(f"초기화 전: 핀 {test_pin} 읽기")
    try:
        val_before = robot.sonar_read(test_pin)
        print(f"   값: {val_before}")
    except Exception as e:
        print(f"   오류: {e}")
        val_before = None
    
    print()
    
    # 초기화
    print(f"센서 초기화: sonar_begin({test_pin})")
    try:
        robot.sonar_begin(test_pin)
        print("   ✅ 성공")
        time.sleep(0.5)
    except Exception as e:
        print(f"   ❌ 실패: {e}")
    
    print()
    
    # 초기화 후 읽기
    print(f"초기화 후: 핀 {test_pin} 읽기")
    try:
        val_after = robot.sonar_read(test_pin)
        print(f"   값: {val_after}")
    except Exception as e:
        print(f"   오류: {e}")
        val_after = None
    
    print()
    
    # 결론
    if val_before is None and val_after is not None:
        print("💡 결론: 센서 초기화 필수!")
        return True
    else:
        print("💡 결론: 센서 초기화 선택사항")
        return False


def test_pin_numbers(robot):
    """초음파 핀 번호 확인"""
    print("\n" + "="*60)
    print("4️⃣  초음파 핀 번호 확인")
    print("="*60 + "\n")
    
    print("각 핀에서 초음파 센서 읽기:")
    print("(손으로 센서를 막으면서 어느 값이 변하는지 확인하세요!)\n")
    
    pins = [2, 3, 12]
    
    for i in range(10):
        print(f"측정 {i+1}/10:")
        for pin in pins:
            try:
                val = robot.sonar_read(pin)
                if val is None:
                    val = 0.0
                print(f"  핀 {pin:2d}: {val:6.1f}cm", end='')
            except:
                print(f"  핀 {pin:2d}: 오류", end='')
        print()
        time.sleep(1)
    
    print()
    print("💡 결론: 손으로 막았을 때 변한 핀 번호를 config에 입력하세요!")


def test_method_names(robot):
    """메서드 이름 확인"""
    print("\n" + "="*60)
    print("5️⃣  메서드 이름 확인")
    print("="*60 + "\n")
    
    # 모든 메서드 출력
    methods = [m for m in dir(robot) if not m.startswith('_')]
    
    print("사용 가능한 메서드:\n")
    
    # 카테고리별 분류
    categories = {
        'stop': [],
        'front': [],
        'back': [],
        'left': [],
        'right': [],
        'rotate': [],
        'sonar': [],
        'other': [],
    }
    
    for method in methods:
        added = False
        for keyword, cat_list in categories.items():
            if keyword in method.lower():
                cat_list.append(method)
                added = True
                break
        if not added:
            categories['other'].append(method)
    
    # 출력
    for category, method_list in categories.items():
        if method_list:
            print(f"[{category.upper()}]")
            for m in method_list:
                print(f"  - {m}")
            print()
    
    print("💡 결론: 위 메서드 이름을 코드에서 사용하세요!")


def main():
    print("🔍 RobokitRS API 확인 스크립트\n")
    
    # 포트 입력
    port = input("시리얼 포트 입력 (기본: /dev/ttyUSB0): ").strip()
    if not port:
        port = '/dev/ttyUSB0'
    
    print(f"\n사용할 포트: {port}\n")
    
    try:
        # 1. Import
        RobokitClass = test_import_methods()
        if not RobokitClass:
            return 1
        
        # 2. 초기화
        robot = test_initialization_methods(RobokitClass, port)
        if not robot:
            return 1
        
        # 3. 센서 초기화
        sensor_init_required = test_sensor_initialization(robot)
        
        # 4. 핀 번호
        test_pin_numbers(robot)
        
        # 5. 메서드 이름
        test_method_names(robot)
        
        # 최종 요약
        print("\n" + "="*60)
        print("📋 최종 요약")
        print("="*60 + "\n")
        
        print("코드에 반영해야 할 사항:\n")
        
        print("1. Import 방식:")
        print("   → 위 테스트 결과 참고\n")
        
        print("2. 초기화 방식:")
        print("   → 위 테스트 결과 참고\n")
        
        if sensor_init_required:
            print("3. 센서 초기화:")
            print("   ✅ 필수! sonar_begin() 호출 필요\n")
        else:
            print("3. 센서 초기화:")
            print("   ℹ️  선택사항\n")
        
        print("4. 초음파 핀 번호:")
        print("   → 위 테스트에서 확인한 핀 번호 사용\n")
        
        print("5. 메서드 이름:")
        print("   → 위 목록의 메서드 사용\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏸️  사용자 중단")
        return 1
    
    except Exception as e:
        print(f"\n\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
