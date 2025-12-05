# Examples 폴더 업데이트 가이드 📚

## 🔍 **변경 필요 여부**

### **Q: examples 폴더 바뀌어야 하나?**
### **A: 네! 업데이트 필요합니다!** ✅

---

## 📊 **변경 사항 요약**

| 파일 | 상태 | 변경 | 이유 |
|------|------|------|------|
| **basic_usage.py** | ✅ 업데이트 | 10개 예제로 확장 | LiDAR, Logger, Config 추가 |
| **example_ai_path.py** | ✅ 업데이트 | config_dir 추가 | 설정 파일 사용 |
| **example_room_navigation.py** | ✅ 업데이트 | Logger 통합 | 로그 파일 생성 |
| **example_lidar_360.py** | ✅ 신규 | LiDAR 전용 예제 | 360도 감지 시연 |

---

## 💡 **주요 변경사항**

### **1. NavigationSystem 초기화** ⭐⭐⭐

**Before:**
```python
nav = NavigationSystem(mock=True)
```

**After:**
```python
nav = NavigationSystem(config_dir='./config', mock=True)
```

**이유:**
- ✅ 설정 파일 사용
- ✅ LiDAR 설정 로드
- ✅ ConfigLoader 통합

---

### **2. LiDAR 예제 추가** ⭐⭐⭐

**신규 파일:** `example_lidar_360.py`

**기능:**
- ✅ LiDAR 상태 확인
- ✅ 360도 장애물 감지
- ✅ 섹터별 분석 (8방향)
- ✅ 경로 상 장애물
- ✅ 통과 가능 경로 찾기
- ✅ 하이브리드 감지 (초음파 + LiDAR)

**예제 구성:**
```python
1️⃣ check_lidar_status()     # LiDAR 상태 확인
2️⃣ test_360_detection()     # 360도 감지
3️⃣ test_hybrid_detection()  # 하이브리드
4️⃣ navigate_with_lidar()    # 실제 주행
```

---

### **3. Logger 통합** ⭐⭐

**Before:**
```python
# 로깅 없음
nav.navigate_rooms('101호', '107호')
```

**After:**
```python
logger = NavigationLogger(log_to_file=True)

logger.log_navigation_start("101호", "107호")
nav.navigate_rooms('101호', '107호')
logger.log_navigation_end(success=True)

print(f"로그 파일: {logger.log_file}")
```

**이유:**
- ✅ 로그 파일 생성
- ✅ 주행 기록 보존
- ✅ 디버깅 편리

---

### **4. ConfigLoader 예제** ⭐⭐

**신규 예제:** `example7_config_loader()`

```python
# 설정 로드
hw_config = ConfigLoader.load_hardware_config()
nav_config = ConfigLoader.load_navigation_config()

# 중첩 키 접근
robot_port = ConfigLoader.get_nested(hw_config, 'robot.port')
lidar_enabled = ConfigLoader.get_nested(hw_config, 'lidar.enabled')
```

**이유:**
- ✅ ConfigLoader 사용법 시연
- ✅ 설정 파일 활용

---

### **5. 환경 변수 예제** ⭐

**신규 예제:** `example10_environment_variables()`

```python
import os

os.environ['ROBOT_PORT'] = '/dev/rfcomm0'
os.environ['LIDAR_PORT'] = '/dev/ttyUSB1'

# hardware.yaml에서 ${ROBOT_PORT} 치환
```

---

## 📋 **파일별 상세 변경**

### **basic_usage.py**

**Before:** 5개 예제
```python
example1_simple_rooms()
example2_ai_path()
example3_custom_path()
example4_json_path()
example5_realtime_monitoring()
```

**After:** 10개 예제 (5개 추가!)
```python
# 기존
example1_simple_rooms()
example2_ai_path()
example3_custom_path()
example4_json_path()
example5_realtime_monitoring()

# ✅ 신규!
example6_lidar_detection()          # LiDAR 감지
example7_config_loader()            # 설정 로드
example8_navigation_logger()        # 로그 시스템
example9_hybrid_obstacle_detection() # 하이브리드
example10_environment_variables()   # 환경 변수
```

---

### **example_ai_path.py**

**Before:**
```python
nav = NavigationSystem(mock=True)
nav.navigate_ai_path(ai_path_pixels)
```

**After:**
```python
nav = NavigationSystem(config_dir='./config', mock=True)

print(f"LiDAR: {nav.get_lidar_status()['enabled']}")

nav.navigate_ai_path(ai_path_pixels)
```

**변경:**
- ✅ config_dir 추가
- ✅ LiDAR 상태 출력

---

### **example_room_navigation.py**

**Before:**
```python
nav = NavigationSystem(mock=True)
nav.navigate_rooms('101호', '107호')
nav.shutdown()
```

**After:**
```python
logger = NavigationLogger(log_to_file=True)

nav = NavigationSystem(config_dir='./config', mock=True)

logger.log_navigation_start("101호", "107호")
nav.navigate_rooms('101호', '107호')
logger.log_navigation_end(success=True)

print(f"로그 파일: {logger.log_file}")
```

**변경:**
- ✅ config_dir 추가
- ✅ Logger 통합
- ✅ 로그 파일 생성

---

### **example_lidar_360.py** (신규!)

**기능:**
1. LiDAR 상태 확인
2. 360도 장애물 감지
3. 하이브리드 감지
4. 실제 주행

**예시 출력:**
```
📡 LiDAR 설정:
  활성화: True
  포트: /dev/ttyUSB1
  모델: rplidar_a2
  속도: 115200 baud

📊 스캔 데이터: 360개 포인트

1️⃣ 가장 가까운 장애물:
  방향: front
  거리: 45.0cm
  각도: 0.0°

2️⃣ 섹터별 장애물 (8방향):
  front       : ⚠️  45.0cm
  front_right : ✅ 150.0cm
  right       : ✅ 200.0cm
  ...

3️⃣ 진행 방향 장애물:
  장애물: True
  최소 거리: 45.0cm
  권장: stop

4️⃣ 통과 가능 경로:
  경로 1:  45.0° (폭: 90.0°, 거리: 150.0cm)
  경로 2: -45.0° (폭: 85.0°, 거리: 140.0cm)
```

---

## 🎯 **사용 방법**

### **1. 기본 예제 실행**
```bash
# 전체 예제 (10개)
python examples/basic_usage.py

# 개별 예제
python examples/example_room_navigation.py
python examples/example_ai_path.py
```

---

### **2. LiDAR 예제 실행**
```bash
# LiDAR 전용
python examples/example_lidar_360.py
```

---

### **3. 출력 확인**
```bash
# 로그 파일
ls ./logs/

# 로그 내용
cat ./logs/nav_20251203_*.log
```

---

## ✅ **체크리스트**

### **파일 업데이트:**
- [x] basic_usage.py (5개 → 10개 예제)
- [x] example_ai_path.py (config_dir 추가)
- [x] example_room_navigation.py (Logger 통합)
- [x] example_lidar_360.py (신규 생성)

### **신규 예제:**
- [x] LiDAR 상태 확인
- [x] 360도 장애물 감지
- [x] 하이브리드 감지
- [x] ConfigLoader 사용
- [x] NavigationLogger 사용
- [x] 환경 변수 사용

---

## 🎉 **최종 정리**

### **Q: examples 폴더 바뀌어야 하나?**
### **A: 네! 대폭 업데이트 완료!** ✅

**변경 사항:**
1. ✅ **기존 3개 파일** 업데이트
   - config_dir 추가
   - Logger 통합
   - LiDAR 상태 확인

2. ✅ **신규 1개 파일** 추가
   - example_lidar_360.py (LiDAR 전용)

3. ✅ **예제 개수** 확장
   - 5개 → 10개 (basic_usage.py)
   - LiDAR, Logger, Config 예제 추가

**결과:**
```
examples/
├── basic_usage.py             ✅ 10개 예제 (5개 추가!)
├── example_ai_path.py         ✅ config_dir 추가
├── example_room_navigation.py ✅ Logger 통합
└── example_lidar_360.py       ✅ 신규! (LiDAR 전용)
```

**→ 최신 기능 모두 반영 완료!** 🚀✨🎊
