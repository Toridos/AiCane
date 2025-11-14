from RobokitRS import *
import time

motion = RobokitRS.RobokitRS()
motion.port_open("COM3")

print("\n==========================================")
print("🛞 속도별 바퀴 회전 테스트 (1초 회전)")
print("0 ~ 15 사이 속도를 입력하세요")
print("==========================================\n")

def test_speed(speed):
    print(f"\n🛞 테스트: 속도 {speed} / 1초 회전")
    input("👉 바퀴에 흰색 표시(스티커)를 붙여 회전수를 볼 수 있게 준비하고 엔터를 누르세요. ")
    # 오른쪽 바퀴 기준 테스트 — 필요하면 네가 쓰는 회전 함수로 변경
    print("⏱ 1초 동안 회전 시작!")
    motion.set_mecanumwheels_drive_front(speed)
    start = time.time()
    time.sleep(0.528)
    motion.set_mecanumwheels_drive_front(speed)
    time.sleep(0.528)
    motion.set_mecanumwheels_drive_stop()
    end = time.time()

    print(f"⏱ 실제 구동 시간: {end - start:.3f}초")
    print("👀 바퀴 회전수를 직접 세서 기록하세요.")
    print("==========================================\n")


while True:
    try:
        s = input("속도 입력 (0~15), 종료하려면 q → ")

        if s.lower() == "q":
            print("\n👋 테스트 종료! 로봇을 안전하게 끄세요.")
            motion.set_mecanumwheels_drive_stop()
            break

        speed = int(s)

        if 0 <= speed <= 15:
            test_speed(speed)
        else:
            print("❌ 속도는 0~15 사이만 입력하세요.")

    except ValueError:
        print("❌ 숫자를 입력하세요.")
