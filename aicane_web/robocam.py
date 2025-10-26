import cv2
import numpy as np
from RoboCam.robocam import *
from RobokitRS import *
import time

# === 카메라 & 로봇 초기화 ===
rCam = RoboCam()
rCam.CameraStreamInit(640, 480)
rCam.CameraStream()

rs = RobokitRS.RobokitRS()
rs.port_open("COM5")

SPEED = 10

def move_forward(sec=0.5): rs.set_mecanumwheels_drive_front(SPEED); time.sleep(sec); rs.set_mecanumwheels_drive_stop()
def move_back(sec=0.5): rs.set_mecanumwheels_drive_back(SPEED); time.sleep(sec); rs.set_mecanumwheels_drive_stop()
def move_left(sec=0.5): rs.set_mecanumwheels_drive_left(SPEED); time.sleep(sec); rs.set_mecanumwheels_drive_stop()
def move_right(sec=0.5): rs.set_mecanumwheels_drive_right(SPEED); time.sleep(sec); rs.set_mecanumwheels_drive_stop()

# === 카메라 연결 ===
cap = cv2.VideoCapture("http://192.168.4.1:81/stream")

print("🎥 카메라 스트리밍 시작...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ 프레임 읽기 실패")
        continue

    # 그레이스케일로 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 블러 처리 → 노이즈 제거
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    # 명암 대비(Threshold)로 윤곽 강조
    _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV)

    # 윤곽선 검출
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > 1500:  # 충분히 큰 물체로 간주
            x, y, w, h = cv2.boundingRect(c)
            cx = x + w//2
            cy = y + h//2
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)

            print(f"🎯 물체 감지! 중심=({cx},{cy}), 면적={area}")

            # 회피 판단
            if cx < 200:
                print("⬅️ 왼쪽에 물체 → 오른쪽 회피")
                move_right(1.0)
            elif cx > 440:
                print("➡️ 오른쪽에 물체 → 왼쪽 회피")
                move_left(1.0)
            else:
                print("⬆️ 정면 물체 → 후진")
                move_back(1.0)
        else:
            print("🟢 작은 물체(무시) → 전진")
            move_forward(0.5)
    else:
        print("🟢 전방 깨끗함 → 전진")
        move_forward(0.5)

    cv2.imshow("RoboCam - Object Detection", frame)
    if cv2.waitKey(1) == 27:  # ESC 종료
        break

cap.release()
cv2.destroyAllWindows()
rs.end()
