# obstacle.yaml 업데이트 가이드 🚧

## 🔍 **문제 발견**

### **현재 상태:**
```
📁 config/
├── obstacle.yaml        ← 구버전 (장애물 감지)
└── navigation.yaml      ← 신버전 (장애물 감지 + LiDAR)
```

**문제:**
- ⚠️ **중복!** 두 파일 모두 장애물 설정
- ⚠️ **충돌 가능!** 어느 걸 따를지 불명확
- ⚠️ **LiDAR 없음!** obstacle.yaml에는 LiDAR 설정 없음

---

## 📊 **비교 분석**

### **obstacle.yaml (기존):**
```yaml
ultrasonic:
  sudden_change_threshold_cm: 40     # ✅ 미끄러짐 감지!
  gradual_change_threshold_cm: 10

avoidance:
  enable: true
  avoidance_distance_cm: 100
  retry_count: 3
```

**특징:**
- ✅ **미끄러짐 감지** (고유 기능!)
- ⚠️ 초음파만
- ⚠️ LiDAR 없음

---

### **navigation.yaml (신규):**
```yaml
obstacle_detection:
  mode: hybrid                       # ✅ 초음파 + LiDAR!
  
  ultrasonic:
    min_distance: 50
    emergency_stop: 30
  
  lidar:                             # ✅ 360도 감지!
    min_distance: 50
    path_width: 60
    min_gap_width: 80
  
  hybrid:
    confidence_threshold: medium
    priority: ultrasonic

path_replanning:                     # ✅ 자동 재계획!
  enabled: true
  strategy:
    use_lidar_gaps: true
```

**특징:**
- ✅ **LiDAR 통합!**
- ✅ 하이브리드 감지
- ✅ 자동 재계획
- ⚠️ 미끄러짐 감지 없음

---

## 💡 **해결책**

### **전략: 역할 분리!** ⭐⭐⭐

```
obstacle.yaml:
  ✅ 미끄러짐 vs 장애물 구분 (고유 기능)
  ✅ 단순 회피 전략
  
navigation.yaml:
  ✅ 장애물 감지 (초음파 + LiDAR)
  ✅ 하이브리드 모드
  ✅ 경로 재계획
```

**이점:**
- ✅ 중복 제거
- ✅ 역할 명확
- ✅ 고유 기능 유지 (미끄러짐 감지)

---

## 🔧 **변경 사항**

### **Before (기존):**
```yaml
# obstacle.yaml
ultrasonic:
  sudden_change_threshold_cm: 40
  gradual_change_threshold_cm: 10

avoidance:
  enable: true
  avoidance_distance_cm: 100
  retry_count: 3
```

---

### **After (개선!):**
```yaml
# obstacle.yaml

# ⚠️ DEPRECATION NOTICE:
# 장애물 감지는 navigation.yaml로 이동
# 이 파일은 미끄러짐 감지 전용

slip_detection:                      # ✅ 명확한 이름!
  sudden_change_threshold_cm: 40     # ✅ 미끄러짐 판단
  gradual_change_threshold_cm: 10
  time_window_sec: 1.0               # ✅ 신규!
  confidence_threshold: 0.7          # ✅ 신규!

avoidance:
  enable: true
  avoidance_distance_cm: 100
  retry_count: 3
  strategy: simple                   # ✅ 신규!
  direction_priority: left_first     # ✅ 신규!
```

---

## 📋 **역할 정리**

| 설정 | 파일 | 역할 |
|------|------|------|
| **미끄러짐 감지** | obstacle.yaml | ✅ 전용 |
| **장애물 감지 (초음파)** | navigation.yaml | ✅ 주요 |
| **장애물 감지 (LiDAR)** | navigation.yaml | ✅ 주요 |
| **하이브리드 모드** | navigation.yaml | ✅ 주요 |
| **경로 재계획** | navigation.yaml | ✅ 주요 |
| **단순 회피** | obstacle.yaml | ✅ 보조 |

---

## 🎯 **사용 방법**

### **코드 예시:**
```python
from aicane_navigation.utils import ConfigLoader

# 1. 미끄러짐 감지 설정
obstacle_config = ConfigLoader.load_yaml('./config/obstacle.yaml')

slip_threshold = obstacle_config['slip_detection']['sudden_change_threshold_cm']
# 40cm

# 2. 장애물 감지 설정 (주요!)
nav_config = ConfigLoader.load_navigation_config()

obs_mode = nav_config['obstacle_detection']['mode']
# 'hybrid'

us_min_dist = nav_config['obstacle_detection']['ultrasonic']['min_distance']
# 50cm

lidar_enabled = nav_config['obstacle_detection']['lidar']['min_distance']
# 50cm
```

---

### **통합 사용:**
```python
from aicane_navigation import NavigationSystem

class NavigationSystem:
    def __init__(self):
        # 장애물 감지 (navigation.yaml)
        self.nav_config = ConfigLoader.load_navigation_config()
        self.obs_mode = self.nav_config['obstacle_detection']['mode']
        
        # 미끄러짐 감지 (obstacle.yaml)
        self.obstacle_config = ConfigLoader.load_yaml('./config/obstacle.yaml')
        self.slip_threshold = self.obstacle_config['slip_detection']['sudden_change_threshold_cm']
    
    def check_obstacle_or_slip(self, ultrasonic_distances):
        # 1. 장애물 감지 (navigation.yaml 설정)
        if self.obs_mode == 'hybrid':
            # 초음파 + LiDAR
            obstacle = self._check_hybrid()
        
        # 2. 미끄러짐 감지 (obstacle.yaml 설정)
        if obstacle:
            is_slip = self._check_slip(ultrasonic_distances, self.slip_threshold)
            
            if is_slip:
                # 미끄러짐 → 오도메트리 보정
                return 'slip'
            else:
                # 진짜 장애물 → 회피
                return 'obstacle'
```

---

## 📝 **핵심 변경사항**

### **1. 명확한 구분** ✅
```yaml
# obstacle.yaml
slip_detection:           # ✅ 미끄러짐 전용!
  sudden_change_threshold_cm: 40

# navigation.yaml
obstacle_detection:       # ✅ 장애물 전용!
  mode: hybrid
```

---

### **2. Deprecation 노트** ✅
```yaml
# obstacle.yaml 상단
# ⚠️ DEPRECATION NOTICE:
# 기본 장애물 감지는 navigation.yaml로 이동
# 이 파일은 미끄러짐 감지 전용
```

---

### **3. 참조 가이드** ✅
```yaml
# obstacle.yaml 하단
# 📋 장애물 감지 설정은 navigation.yaml 참조:
# 
# obstacle_detection:
#   mode: hybrid
#   ultrasonic: {...}
#   lidar: {...}
```

---

## ✅ **체크리스트**

### **obstacle.yaml:**
- [x] 미끄러짐 감지 설정 유지
- [x] slip_detection 섹션 추가
- [x] time_window_sec 추가
- [x] confidence_threshold 추가
- [x] avoidance 전략 추가
- [x] Deprecation 노트 추가
- [x] 참조 가이드 추가

### **navigation.yaml:**
- [x] obstacle_detection (이미 있음)
- [x] ultrasonic 상세 설정
- [x] lidar 설정
- [x] hybrid 설정
- [x] path_replanning

---

## 🎉 **최종 정리**

### **Q: obstacle.yaml 수정 필요한가?**

### **A: 필요함! (역할 명확화)** ✅

**이유:**
1. ✅ **중복 제거** - navigation.yaml과 충돌 방지
2. ✅ **역할 분리** - 미끄러짐 감지 전용
3. ✅ **고유 기능 유지** - sudden_change_threshold
4. ✅ **명확한 문서화** - Deprecation 노트

**결과:**
```
obstacle.yaml (개선):
  ✅ 미끄러짐 vs 장애물 구분
  ✅ 단순 회피 전략
  ✅ 참조 가이드 (navigation.yaml)

navigation.yaml (주요):
  ✅ 장애물 감지 (초음파 + LiDAR)
  ✅ 하이브리드 모드
  ✅ 경로 재계획
```

**→ 역할이 명확해지고 중복 제거!** 🚀✨
