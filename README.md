# AiCane Navigation System 🤖

실내 자율주행 로봇 시스템 (1층 평면도 기반)

---

## 🎯 **역할별 빠른 시작** ⭐ (새로 추가!)

### 🔧 **하드웨어 테스트 담당이신가요?**
👉 **[하드웨어 팀 가이드 바로가기](HARDWARE_TEAM_GUIDE.md)** (15분)

**빠른 체크:**
1. 블루투스 연결 → [가이드](HARDWARE_TEAM_GUIDE.md#블루투스-연결)
2. LiDAR 연결 (선택) → [가이드](HARDWARE_TEAM_GUIDE.md#lidar-연결-선택)
3. 테스트 실행 → [가이드](HARDWARE_TEAM_GUIDE.md#테스트-실행)

---

### 🤖 **AI 경로 담당이신가요?**
👉 **[AI 경로 예제](examples/example_ai_path.py)** (5분)

**빠른 체크:**
1. AI 경로 형식 확인 → [예제](examples/example_ai_path.py)
2. 픽셀 → cm 변환 이해 → [MAPPING_GUIDE.md](MAPPING_GUIDE.md)
3. 경로 테스트 → `python examples/example_ai_path.py`

---

### 🗺️ **내비게이션/알고리즘 담당이신가요?**
👉 **[빠른 시작](QUICKSTART.md)** (5분) → **[구현 상세](IMPLEMENTATION.md)** (1시간)

**빠른 체크:**
1. 전체 시스템 이해 → [IMPLEMENTATION.md](IMPLEMENTATION.md)
2. 위치 추정 → [3-Tier 시스템](IMPLEMENTATION.md#3-tier-위치-추정)
3. 경로 계획 → [PATH_PLANNER_GUIDE.md](PATH_PLANNER_GUIDE.md)

---

### 👨‍💻 **팀장/전체 시스템 담당이신가요?**
👉 **[빠른 시작](QUICKSTART.md)** (5분)

**빠른 체크:**
1. 프로젝트 개요 → 아래 계속 읽기
2. 빠른 시작 → [QUICKSTART.md](QUICKSTART.md)
3. 전체 문서 → [문서 정리 가이드](DOCS_REORGANIZATION_PLAN.md)

---

## ✨ **특징**

- **3-Tier 위치 추정**: 초음파(90%) + 오도메트리(9%) + LiDAR(1%)
- **360도 장애물 감지**: 초음파 + LiDAR 하이브리드
- **미끄러짐 구분**: 장애물 출현 vs 미끄러짐 자동 판별
- **실시간 경로 재계획**: Waypoint 기반 추종
- **블루투스 자동 연결**: RS CPU 보드 자동 인식

---

## 🔧 **하드웨어**

### **필수:**
- Raspberry Pi 4B
- RobokitRS (메카넘휠) + RS CPU 보드 (블루투스)
- 초음파 센서 3개 (정면/좌/우)

### **선택 (강력 추천!):**
- RPLidar A2 or X4 (360도 장애물 감지)
  - **팀원 검증:** A2 모델, USB1 포트, 115200 baud ✅

---

## 📦 **설치**

### **1. 기본 설치**
```bash
cd /home/pi/aicane_navigation
pip install -e .
```

### **2. 하드웨어 설정** ⭐
👉 **[하드웨어 팀 가이드](HARDWARE_TEAM_GUIDE.md)** 참고!

**요약:**
```bash
# 블루투스 (5분)
sudo hcitool scan
bluetoothctl
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1

# LiDAR (선택, 5분)
ls /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB1
pip3 install rplidar-roboticia --break-system-packages

# 설정 파일
nano config/hardware.yaml
```

**상세 가이드:**
- [HARDWARE_TEAM_GUIDE.md](HARDWARE_TEAM_GUIDE.md) ⭐ 하드웨어 담당 필독!
- [BLUETOOTH_GUIDE.md](BLUETOOTH_GUIDE.md) (블루투스 상세)
- [LIDAR_GUIDE.md](LIDAR_GUIDE.md) (LiDAR 상세)

---

## 🚀 **사용법**

### **방 간 이동**
```bash
# 스크립트 (추천!)
./launch/start_navigation.sh --from 101호 --to 107호

# Python 직접 실행
python scripts/navigate.py --mode rooms --from 101호 --to 107호

# Mock 모드 (테스트)
./launch/start_navigation.sh --from 101호 --to 107호 --mock
```

### **AI 경로 추종**
```python
from aicane_navigation import NavigationSystem

nav = NavigationSystem(config_dir='./config')

# AI가 제공한 픽셀 경로
ai_path = [(100, 314), (200, 314), (300, 314)]

nav.navigate_ai_path(ai_path)
nav.shutdown()
```

**예제:** [examples/example_ai_path.py](examples/example_ai_path.py)

---

## 🧪 **테스트**

### **하드웨어 테스트** (하드웨어 담당)
```bash
# 기본 테스트
python scripts/test_hardware.py

# LiDAR 테스트
python scripts/test_lidar.py

# 전체 테스트
python tests/test_all.py
```

### **통합 테스트**
```bash
# 모든 모듈 테스트
python tests/test_all.py

# 신규 기능 테스트
python tests/test_lidar.py
python tests/test_config_loader.py
python tests/test_logger.py
```

---

## 📁 **프로젝트 구조**

```
aicane_navigation/
├── aicane_navigation/          # 메인 패키지
│   ├── core/                   # 좌표 변환, 속도 프로파일
│   ├── hardware/               # 로봇, LiDAR 인터페이스
│   ├── mapping/                # 맵 데이터, 경로 생성
│   ├── localization/           # 3-Tier 위치 추정
│   ├── obstacle/               # 장애물 감지 및 회피
│   ├── navigation/             # 경로 추종
│   └── utils/                  # Logger, ConfigLoader
├── config/                     # 설정 파일
│   ├── hardware.yaml           # 하드웨어 설정 ⭐
│   ├── navigation.yaml         # 주행 설정
│   └── obstacle.yaml           # 장애물 감지
├── examples/                   # 사용 예제
│   ├── basic_usage.py          # 10개 예제
│   ├── example_ai_path.py      # AI 경로
│   └── example_lidar_360.py    # LiDAR 360도
├── scripts/                    # 실행 스크립트
│   ├── navigate.py             # 메인 실행
│   ├── test_hardware.py        # 하드웨어 테스트
│   └── test_lidar.py           # LiDAR 테스트
├── tests/                      # 테스트 코드
│   ├── test_all.py             # 전체 테스트
│   ├── test_lidar.py           # LiDAR 테스트
│   └── test_config_loader.py   # 설정 테스트
└── launch/                     # 시작 스크립트
    ├── start_navigation.sh     # 주 실행 파일 ⭐
    ├── demo_full.sh            # 데모
    └── setup_check.sh          # 설정 확인
```

---

## 📚 **문서 가이드**

### **역할별 필독 문서:** ⭐

| 역할 | 필독 문서 | 소요 시간 |
|------|----------|----------|
| **하드웨어 테스트** | [HARDWARE_TEAM_GUIDE.md](HARDWARE_TEAM_GUIDE.md) | 15분 |
| **AI 경로** | [examples/example_ai_path.py](examples/example_ai_path.py) | 5분 |
| **내비게이션** | [QUICKSTART.md](QUICKSTART.md) → [IMPLEMENTATION.md](IMPLEMENTATION.md) | 1시간 |
| **팀장/전체** | [QUICKSTART.md](QUICKSTART.md) | 5분 |

### **상세 문서:** (선택)

#### **하드웨어:**
- BLUETOOTH_GUIDE.md (블루투스 상세)
- LIDAR_GUIDE.md (LiDAR 상세)
- LIDAR_VS_ULTRASONIC_GUIDE.md (센서 비교)
- HARDWARE_CONFIG_INTEGRATION.md (설정 통합)

#### **기능:**
- MAPPING_GUIDE.md (맵 시스템)
- PATH_PLANNER_GUIDE.md (경로 계획)
- ROOM_MANAGER_GUIDE.md (방 관리)
- LOGGER_GUIDE.md (로깅 시스템)
- CONFIG_LOADER_GUIDE.md (설정 관리)

#### **개발:**
- IMPLEMENTATION.md (구현 상세)
- EXAMPLES_UPDATE_GUIDE.md (예제 업데이트)
- TESTS_UPDATE_GUIDE.md (테스트 업데이트)

#### **참고:**
- DOCS_REORGANIZATION_PLAN.md (문서 정리 계획)

---

## 🔑 **핵심 설정 파일** ⭐

### **config/hardware.yaml** (하드웨어 담당 필수!)
```yaml
robot:
  port: '/dev/rfcomm0'           # ✅ 팀원 검증!
  bluetooth_mac: '98:D3:31:XX:XX:XX'

lidar:
  enabled: true                  # ✅
  port: /dev/ttyUSB1             # ✅ 팀원 검증!
  baudrate: 115200               # ✅ A2 모델
  model: rplidar_a2
```

### **config/navigation.yaml**
```yaml
obstacle_detection:
  mode: hybrid                   # 초음파 + LiDAR

  ultrasonic:
    min_distance: 50
    emergency_stop: 30

  lidar:
    min_distance: 50
    path_width: 60               # 진행 방향 감지 폭
```

---

## 🆘 **문제 해결**

### **빠른 해결:**
👉 **[하드웨어 팀 가이드 - 문제 해결](HARDWARE_TEAM_GUIDE.md#문제-해결)**

### **자주 있는 문제:**

#### **블루투스 연결 안 됨**
```bash
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1
sudo chmod 666 /dev/rfcomm0
```

#### **LiDAR 데이터 없음**
```bash
sudo chmod 666 /dev/ttyUSB1
ls -l /dev/ttyUSB*
```

**상세 해결:** [HARDWARE_TEAM_GUIDE.md](HARDWARE_TEAM_GUIDE.md#문제-해결)

---

## 🤝 **기여**

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 📄 **라이선스**

MIT License

---

## 👥 **팀**

AiCane Navigation Team

**문의:** 팀 채널로 연락주세요!

---

## 🎉 **빠른 시작 요약**

### **하드웨어 담당:**
```bash
1. HARDWARE_TEAM_GUIDE.md 읽기 (15분)
2. 블루투스 연결 (5분)
3. python scripts/test_hardware.py
```

### **AI 경로 담당:**
```bash
1. examples/example_ai_path.py 확인 (5분)
2. python examples/example_ai_path.py
```

### **전체 시스템:**
```bash
1. QUICKSTART.md 읽기 (5분)
2. ./launch/start_navigation.sh --from 101호 --to 107호 --mock
```

**행운을 빕니다!** 🚀✨
