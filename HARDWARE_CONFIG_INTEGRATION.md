# Hardware Config 팀원 코드 통합 가이드 🔧

## 🤔 **팀원 코드 vs 현재 코드**

### **팀원 코드 (테스트 검증됨!):**
```yaml
robot:
  port: '/dev/rfcomm0'   # ✅ 실제 테스트 완료!
  baudrate: 9600

lidar:
  port: '/dev/ttyUSB1'   # ✅ 실제 연결 확인!
  baudrate: 115200       # ✅ A1/A2 모델 확인!
  enabled: True
```

### **현재 코드 (이론적):**
```yaml
robot:
  port: null             # 자동 탐색
  bluetooth_mac: '...'   # 자동 연결
  auto_connect: true

lidar:
  port: /dev/ttyUSB0     # 추정
  baudrate: 256000       # X4 모델 가정
  model: rplidar_x4
```

---

## 📊 **차이점 분석**

| 항목 | 팀원 | 현재 | 가져올까? |
|------|------|------|----------|
| **robot.port** | `/dev/rfcomm0` | `null` | ✅ YES |
| **robot.bluetooth_mac** | ❌ | ✅ | ✅ KEEP |
| **robot.auto_connect** | ❌ | ✅ | ✅ KEEP |
| **lidar.port** | `/dev/ttyUSB1` | `/dev/ttyUSB0` | ✅ YES |
| **lidar.baudrate** | `115200` | `256000` | ✅ YES |
| **lidar.model** | ❌ | `rplidar_x4` | ✅ FIX |
| **ultrasonic** | ✅ | ✅ | ✅ SAME |
| **speed** | ✅ | ✅ | ✅ SAME |

---

## 💡 **가져올 정보**

### **1. robot.port = '/dev/rfcomm0'** ⭐⭐⭐

**팀원 코드:**
```yaml
robot:
  port: '/dev/rfcomm0'   # 블루투스 시리얼
```

**판단:**
- ✅ **팀원이 실제 테스트 완료!**
- ✅ `/dev/rfcomm0`이 작동함!
- ✅ 가져오기!

**통합 전략:**
```yaml
robot:
  port: '/dev/rfcomm0'             # ✅ 팀원 검증!
  bluetooth_mac: '98:D3:31:XX:XX:XX'  # ✅ 자동 연결 백업
  auto_connect: true                # ✅ 유지
```

**이점:**
- 팀원 검증된 값 사용
- + 자동 연결 기능 유지 (백업)

---

### **2. lidar.port = '/dev/ttyUSB1'** ⭐⭐⭐

**팀원 코드:**
```yaml
lidar:
  port: '/dev/ttyUSB1'   # USB1
```

**현재 코드:**
```yaml
lidar:
  port: /dev/ttyUSB0     # USB0
```

**판단:**
- ✅ **팀원이 실제 연결 확인!**
- ✅ `/dev/ttyUSB1`이 LiDAR!
- ⚠️ USB0는 로봇이거나 다른 장치

**통합:**
```yaml
lidar:
  port: /dev/ttyUSB1     # ✅ 팀원 검증!
```

---

### **3. lidar.baudrate = 115200** ⭐⭐⭐

**팀원 코드:**
```yaml
lidar:
  baudrate: 115200       # A1/A2 속도
```

**현재 코드:**
```yaml
lidar:
  baudrate: 256000       # X4 속도
```

**판단:**
- ✅ **팀원이 실제 작동 확인!**
- ✅ `115200` = RPLidar A1 or A2 모델!
- ❌ `256000` = RPLidar X4 (잘못된 가정)

**통합:**
```yaml
lidar:
  baudrate: 115200       # ✅ 팀원 검증! (A1/A2)
  model: rplidar_a2      # ✅ 모델 수정!
```

---

### **4. ultrasonic & speed** ✅

**팀원 코드:**
```yaml
ultrasonic:
  pins: {front: 12, left: 2, right: 3}
  critical_distance: 25
  warning_distance: 50
  safe_distance: 100

speed:
  min_level: 6
  max_level: 15
  default_level: 10
```

**판단:**
- ✅ **현재 코드와 동일!**
- ✅ 이미 반영됨!

---

## 🔧 **통합 결과**

### **Before (현재 코드):**
```yaml
robot:
  port: null                    # ❌ 자동 탐색 (불확실)
  
lidar:
  port: /dev/ttyUSB0            # ❌ 추정
  baudrate: 256000              # ❌ X4 가정
  model: rplidar_x4
```

### **After (팀원 검증 통합!):**
```yaml
robot:
  port: '/dev/rfcomm0'          # ✅ 팀원 검증!
  bluetooth_mac: '...'          # ✅ 백업 유지
  auto_connect: true

lidar:
  port: /dev/ttyUSB1            # ✅ 팀원 검증!
  baudrate: 115200              # ✅ 팀원 검증! (A1/A2)
  model: rplidar_a2             # ✅ 모델 수정!
```

---

## 🎯 **핵심 변경사항**

### **1. robot.port** 변경
```diff
- port: null                    # 자동 탐색
+ port: '/dev/rfcomm0'          # 팀원 검증!
```

### **2. lidar.port** 변경
```diff
- port: /dev/ttyUSB0            # 추정
+ port: /dev/ttyUSB1            # 팀원 검증!
```

### **3. lidar.baudrate** 변경
```diff
- baudrate: 256000              # X4 모델
+ baudrate: 115200              # A1/A2 모델 (팀원 검증!)
```

### **4. lidar.model** 변경
```diff
- model: rplidar_x4
+ model: rplidar_a2             # 115200 → A2
```

---

## 📝 **검증 체크리스트**

### **로봇 연결:**
- [x] port: `/dev/rfcomm0` (팀원 검증)
- [x] baudrate: `9600` (팀원 검증)
- [x] timeout: `1.0` (동일)

### **LiDAR 연결:**
- [x] port: `/dev/ttyUSB1` (팀원 검증)
- [x] baudrate: `115200` (팀원 검증)
- [x] model: `rplidar_a2` (115200 기준)
- [x] enabled: `true` (팀원 검증)

### **센서:**
- [x] ultrasonic pins (동일)
- [x] ultrasonic thresholds (동일)
- [x] speed levels (동일)

---

## 🚀 **테스트 방법**

### **1. 하드웨어 확인**
```bash
# 로봇 포트
ls -l /dev/rfcomm0
# ✅ 있어야 함 (팀원 검증)

# LiDAR 포트
ls -l /dev/ttyUSB1
# ✅ 있어야 함 (팀원 검증)
```

### **2. 테스트 실행**
```bash
# 로봇 테스트
python scripts/test_hardware.py

# LiDAR 테스트
python scripts/test_lidar.py
```

### **3. 통합 테스트**
```python
from aicane_navigation.utils import ConfigLoader

# 설정 로드
hw_config = ConfigLoader.load_hardware_config()

# 확인
print(f"Robot port: {hw_config['robot']['port']}")
# ✅ /dev/rfcomm0

print(f"LiDAR port: {hw_config['lidar']['port']}")
# ✅ /dev/ttyUSB1

print(f"LiDAR baudrate: {hw_config['lidar']['baudrate']}")
# ✅ 115200
```

---

## 🎉 **최종 정리**

### **가져온 정보:**

1. ✅ **robot.port** = `/dev/rfcomm0` (검증됨!)
2. ✅ **lidar.port** = `/dev/ttyUSB1` (검증됨!)
3. ✅ **lidar.baudrate** = `115200` (검증됨! A2 모델)
4. ✅ **lidar.model** = `rplidar_a2` (115200 기준 수정)

### **유지한 정보:**

1. ✅ **robot.bluetooth_mac** (자동 연결)
2. ✅ **robot.auto_connect** (백업)
3. ✅ **lidar.scan_rate** (CPU 절약)
4. ✅ **lidar.mock** (테스트 모드)

### **결과:**

**팀원 검증 + 현재 기능 = 완벽한 통합!** 🎊

```yaml
# ✅ 팀원 검증된 실제 값
robot.port: /dev/rfcomm0
lidar.port: /dev/ttyUSB1
lidar.baudrate: 115200 (A2 모델)

# ✅ 현재 고급 기능
bluetooth_mac, auto_connect
scan_rate, mock mode
```

**→ 실전 검증 + 이론적 완성도!** 🚀✨
