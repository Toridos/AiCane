# 빠른 시작 가이드 🚀

5분 안에 AiCane Navigation 시작하기!

## ⚡ 초간단 체크리스트

### ✅ 1단계: 하드웨어 준비 (30초)
```bash
# RS CPU 보드 전원 켜기
# 블루투스 LED 깜빡임 확인
```

### ✅ 2단계: MAC 주소 확인 (1분)
```bash
sudo hcitool scan

# 출력 예:
# 98:D3:31:XX:XX:XX    HC-05
# ↑ 이 MAC 주소 복사!
```

### ✅ 3단계: 설정 파일 수정 (30초)
```bash
nano config/hardware.yaml
```

수정:
```yaml
bluetooth_mac: '98:D3:31:XX:XX:XX'  # 위에서 복사한 MAC 주소
```

### ✅ 4단계: 테스트 (1분)
```bash
# 센서 테스트
python scripts/test_sensors.py

# 선택: 1 (초음파)
```

### ✅ 5단계: 주행! (2분)
```bash
# 방 간 이동
python scripts/navigate.py --from 101호 --to 107호
```

---

## 🎯 상세 가이드

### 최초 페어링 (한 번만)
```bash
bluetoothctl

# 안에서:
power on
agent on
default-agent
pair 98:D3:31:XX:XX:XX    # PIN: 1234 또는 0000
trust 98:D3:31:XX:XX:XX
exit
```

### 연결 확인
```bash
# 포트 확인
ls -l /dev/rfcomm* /dev/ttyUSB*

# 또는 Python으로
python3 -c "from aicane_navigation.hardware import RobokitDriver; RobokitDriver.list_available_ports()"
```

---

## 🧪 기본 사용 예제

### 1. 간단한 주행
```python
from aicane_navigation import NavigationSystem

# 시스템 초기화 (자동으로 블루투스 연결)
nav = NavigationSystem()

# 주행
nav.navigate_rooms('101호', '107호')

# 종료
nav.shutdown()
```

### 2. AI 경로 추종
```python
from aicane_navigation import NavigationSystem

nav = NavigationSystem()

# AI가 생성한 픽셀 경로
ai_path = [
    (100, 314),
    (200, 314),
    (300, 314),
]

nav.navigate_ai_path(ai_path)
nav.shutdown()
```

### 3. 센서만 테스트
```python
from aicane_navigation.hardware import RobokitDriver
import time

robot = RobokitDriver()  # 자동 연결

# 초음파 읽기
for i in range(10):
    distances = robot.get_ultrasonic()
    print(f"정면: {distances['front']:.1f}cm")
    time.sleep(0.5)

robot.close()
```

---

## ⚠️ 빠른 문제 해결

### Q: "Permission denied" 오류
```bash
sudo chmod 666 /dev/rfcomm0
```

### Q: 연결이 안 됨
```bash
# 블루투스 재시작
sudo systemctl restart bluetooth

# 재바인딩
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1
```

### Q: Mock 모드로 테스트하고 싶음
```python
nav = NavigationSystem(mock=True)
```

---

## 📁 파일 구조

```
C:/25L/aicane_navigation/
├── scripts/
│   ├── navigate.py         ← 메인 주행 스크립트
│   └── test_sensors.py     ← 센서 테스트
├── config/
│   └── hardware.yaml       ← MAC 주소 여기 입력!
├── maps/
│   ├── floor_plan.json     ← 1층 평면도
│   └── example_path.json   ← 예제 경로
└── examples/
    └── basic_usage.py      ← 사용 예제
```

---

## 🎓 다음 단계

1. ✅ 기본 주행 테스트
2. 📏 속도 캘리브레이션: `python scripts/calibrate.py` (추후)
3. 🗺️ 맵 수정: `maps/floor_plan.json` 편집
4. 🎯 AI 경로 통합: `navigate_ai_path()` 사용

---

## 📞 도움이 필요하면?

- 🔍 자세한 가이드: [BLUETOOTH_GUIDE.md](BLUETOOTH_GUIDE.md)
- 📖 전체 문서: [README.md](README.md)
- 🧪 테스트: `python tests/test_all.py`
- 💻 예제: `examples/basic_usage.py`

---

## 🎉 준비 완료!

이제 로봇을 움직일 준비가 되었습니다! 🚀

```bash
python scripts/navigate.py --from 101호 --to 107호
```

화이팅! 💪
