# === 팀별로 여기만 바꾸세요 ===
COM_PORT       = "COM3"      # 각자 PC 포트 (예: "COM3","COM5"...)
MOTOR_TYPE     = 1           # DC motor=1 (교안 규격)
CAM_INDEX      = 0           # 노트북 웹캠=0, USB카메라면 1일 수도 있음
FRAME_W, FRAME_H = 640, 480  # OpenCV 캐처 해상도

# 주행 파라미터 (개선됨)
SPEED_FWD       = 8          # 전진 속도 (기존 9 → 8로 안정성 향상)
SPEED_TURN      = 6          # 회전 속도
SPEED_AVOID     = 7          # 회피 시 속도
CENTER_DEADBAND = 50         # 중앙 허용 폭 (기존 60 → 50으로 더 정확하게)
ROI_Y_RATIO    = 0.66        # 화면 하단 1/3만 사용(바닥 인식 안정)

# 센서 임계값
ULTRA_THRESH_CM = 35         # 초음파 감지 거리 (cm)
IR_ACTIVE = 1                # IR 센서 활성 값 (1=장애물 감지)

# 안전 옵션
PERSON_STOP    = False       # True면 RoboCam 얼굴 감지시 즉시 정지(옵션)

# Wi-Fi 카메라 설정
CAM_IP   = "192.168.4.1"  # 카메라 기본 IP
CAM_PORT = 80             # 보통 80 (안 되면 554 등 테스트)

# ROI_Y_RATIO    = 0.66
ROI_Y_RATIO    = 0.74   # 하단 좁게 인식 → 바닥과 유사색 객체의 하단 경계가 더 또렷
