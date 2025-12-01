#!/usr/bin/env python3
"""
센서 테스트 스크립트
하드웨어 동작 확인
"""

import time
import sys

from aicane_navigation.hardware import RobokitDriver


def test_ultrasonic(robot, duration=10):
    """초음파 센서 테스트"""
    print("\n" + "="*50)
    print("초음파 센서 테스트")
    print("="*50 + "\n")
    
    print(f"{duration}초 동안 측정...\n")
    
    start = time.time()
    count = 0
    
    while time.time() - start < duration:
        distances = robot.get_ultrasonic()
        
        print(f"\r측정 {count+1}: "
              f"정면={distances['front']:6.1f}cm, "
              f"좌={distances['left']:6.1f}cm, "
              f"우={distances['right']:6.1f}cm",
              end='', flush=True)
        
        count += 1
        time.sleep(0.2)
    
    print(f"\n\n✅ 총 {count}회 측정 완료")


def test_motion(robot):
    """모션 제어 테스트"""
    print("\n" + "="*50)
    print("모션 제어 테스트")
    print("="*50 + "\n")
    
    tests = [
        ('FORWARD', 10, 1.0, "전진"),
        ('BACKWARD', 10, 1.0, "후진"),
        ('LEFT', 10, 1.0, "왼쪽"),
        ('RIGHT', 10, 1.0, "오른쪽"),
        ('ROTATE_L', 8, 1.0, "좌회전"),
        ('ROTATE_R', 8, 1.0, "우회전"),
    ]
    
    for direction, speed, duration, name in tests:
        print(f"  {name} (레벨 {speed}, {duration}초)...")
        robot.set_motion(direction, speed)
        time.sleep(duration)
        robot.stop()
        time.sleep(0.5)
    
    print("\n✅ 모션 테스트 완료")


def main():
    print("🧪 AiCane 센서 테스트\n")
    
    # 하드웨어 연결
    try:
        robot = RobokitDriver(mock=False)
    except:
        print("⚠️ 실제 하드웨어 연결 실패, Mock 모드로 전환")
        robot = RobokitDriver(mock=True)
    
    print("\n테스트 선택:")
    print("  1. 초음파 센서")
    print("  2. 모션 제어")
    print("  3. 전체")
    print("  q. 종료")
    
    choice = input("\n선택 (1/2/3/q): ").strip()
    
    try:
        if choice == '1':
            test_ultrasonic(robot)
        elif choice == '2':
            test_motion(robot)
        elif choice == '3':
            test_ultrasonic(robot)
            test_motion(robot)
        elif choice == 'q':
            print("종료")
            return 0
        else:
            print("잘못된 선택")
            return 1
        
        robot.close()
        print("\n✅ 테스트 완료")
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⏸️ 사용자 중단")
        robot.stop()
        robot.close()
        return 1
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        robot.stop()
        robot.close()
        return 1


if __name__ == '__main__':
    sys.exit(main())
