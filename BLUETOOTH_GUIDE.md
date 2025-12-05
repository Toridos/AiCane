# 블루투스 연결 가이드 🔗

## 📱 라즈베리파이 ↔ RS CPU 보드 블루투스 연결

### 준비물
- 라즈베리파이 4B
- RS CPU 보드 (블루투스 모듈 포함)
- 전원

---

## 🔧 초기 설정 (최초 1회만)

### 1. 블루투스 도구 설치
```bash
sudo apt-get update
sudo apt-get install -y bluetooth bluez bluez-tools rfcomm
```

### 2. 블루투스 서비스 시작
```bash
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

### 3. RS CPU 보드 전원 켜기
- RS CPU 보드의 블루투스 LED가 깜빡이는지 확인

---

## 🔍 MAC 주소 찾기

### 방법 1: bluetoothctl 사용
```bash
bluetoothctl

# 블루투스 컨트롤러 안에서:
power on
agent on
default-agent
scan on

# RS CPU 보드 MAC 주소 찾기 (예: 98:D3:31:XX:XX:XX)
# 보통 "HC-05", "HC-06", "RobokitRS" 같은 이름으로 나옴

# MAC 주소 확인 후 스캔 종료
scan off
exit
```

### 방법 2: hcitool 사용
```bash
sudo hcitool scan

# 출력 예:
# Scanning ...
#     98:D3:31:XX:XX:XX    HC-05
```

---

## 🔗 페어링 (최초 1회만)

```bash
bluetoothctl

# 블루투스 컨트롤러 안에서:
pair 98:D3:31:XX:XX:XX    # 실제 MAC 주소로 변경
# PIN 입력 요청 시: 보통 "1234" 또는 "0000"

trust 98:D3:31:XX:XX:XX   # 자동 연결 허용

exit
```

---

## 📡 시리얼 포트 바인딩

### 자동 바인딩 (추천)
우리 코드에서 자동으로 처리하지만, 수동으로도 가능합니다:

```bash
# rfcomm0에 바인딩
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1

# 확인
ls -l /dev/rfcomm0
```

### 권한 설정
```bash
sudo chmod 666 /dev/rfcomm0
```

### 바인딩 해제 (필요시)
```bash
sudo rfcomm release 0
```

---

## 🚀 AiCane Navigation 사용

### 방법 1: 자동 연결 (추천)
코드에서 자동으로 연결을 시도합니다:

```python
from aicane_navigation import NavigationSystem

# MAC 주소만 설정 파일에 넣으면 자동 연결
nav = NavigationSystem()
```

### 방법 2: 수동 포트 지정
```python
from aicane_navigation.hardware import RobokitDriver

# 포트 직접 지정
robot = RobokitDriver(port='/dev/rfcomm0')

# 또는 MAC 주소로 자동 연결
robot = RobokitDriver(bluetooth_mac='98:D3:31:XX:XX:XX', auto_connect=True)
```

---

## 🔧 설정 파일에 MAC 주소 저장

`config/hardware.yaml` 파일 수정:

```yaml
robot:
  # 시리얼 포트 (자동 탐색하려면 null)
  port: null
  
  # 블루투스 MAC 주소
  bluetooth_mac: '98:D3:31:XX:XX:XX'  # 실제 MAC 주소로 변경
  
  # 자동 연결 시도
  auto_connect: true
  
  baudrate: 9600
  timeout: 1.0
```

---

## 🧪 연결 테스트

### 1. 포트 확인
```bash
python3 -c "from aicane_navigation.hardware import RobokitDriver; RobokitDriver.list_available_ports()"
```

### 2. 센서 테스트
```bash
cd /home/pi/aicane_navigation
python scripts/test_sensors.py
```

### 3. 간단한 모션 테스트
```python
from aicane_navigation.hardware import RobokitDriver
import time

robot = RobokitDriver()  # 자동 연결
robot.set_motion('FORWARD', 10)
time.sleep(2)
robot.stop()
robot.close()
```

---

## ⚠️ 문제 해결

### 문제 1: "Permission denied" 오류
```bash
# 권한 부여
sudo chmod 666 /dev/rfcomm0

# 또는 사용자를 dialout 그룹에 추가
sudo usermod -a -G dialout $USER
# 재부팅 필요
```

### 문제 2: 연결이 안 됨
```bash
# 블루투스 재시작
sudo systemctl restart bluetooth

# rfcomm 리셋
sudo rfcomm release 0
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1

# RS CPU 보드 재부팅
```

### 문제 3: 포트를 찾을 수 없음
```bash
# 포트 확인
ls -l /dev/rfcomm*
ls -l /dev/ttyUSB*

# 블루투스 상태 확인
hciconfig
# hci0이 UP RUNNING 상태여야 함
```

### 문제 4: "Device not found" 오류
```bash
# 스캔해서 MAC 주소 다시 확인
sudo hcitool scan

# 페어링 다시
bluetoothctl
remove 98:D3:31:XX:XX:XX
pair 98:D3:31:XX:XX:XX
trust 98:D3:31:XX:XX:XX
```

---

## 🔄 부팅 시 자동 연결 (선택사항)

### systemd 서비스 생성
```bash
sudo nano /etc/systemd/system/rfcomm-bind.service
```

내용:
```ini
[Unit]
Description=RFCOMM Bind for RS CPU Board
After=bluetooth.service

[Service]
Type=oneshot
ExecStart=/usr/bin/rfcomm bind 0 98:D3:31:XX:XX:XX 1
RemainAfterExit=yes
ExecStop=/usr/bin/rfcomm release 0

[Install]
WantedBy=multi-user.target
```

활성화:
```bash
sudo systemctl enable rfcomm-bind.service
sudo systemctl start rfcomm-bind.service
```

---

## 📝 요약

### 최초 설정 순서:
1. ✅ 블루투스 도구 설치
2. ✅ MAC 주소 찾기
3. ✅ 페어링
4. ✅ `config/hardware.yaml`에 MAC 주소 저장
5. ✅ 테스트

### 매번 사용 시:
1. RS CPU 보드 전원 켜기
2. `python scripts/navigate.py ...` 실행
3. 자동으로 연결됨! 🎉

---

## 💡 팁

- **연결이 끊기면**: 코드에서 자동으로 재연결 시도
- **여러 로봇 사용**: MAC 주소만 바꾸면 됨
- **USB 케이블로도 가능**: `/dev/ttyUSB0` 또는 `/dev/ttyACM0`

---

## 🆘 도움말

문제가 있으면:
1. `dmesg | grep -i bluetooth` 확인
2. `sudo systemctl status bluetooth` 확인
3. RS CPU 보드 LED 상태 확인
4. Mock 모드로 테스트: `mock=True`
