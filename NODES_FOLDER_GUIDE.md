# nodes 폴더 가이드 📝

## 🤔 **nodes 폴더는 뭐야?**

### **현재 상태:**
```
aicane_navigation/nodes/
├── __init__.py          (빈 파일)
├── navigation_node.py   (빈 파일, 0 bytes)
└── monitor_node.py      (빈 파일, 0 bytes)
```

**모두 비어있음!** ❌

---

## 🔍 **원래 목적**

### **ROS용으로 준비된 것으로 추정:**

**ROS (Robot Operating System)에서:**
```bash
# ROS 방식 (여러 프로세스)
roscore                           # ROS 마스터
rosrun aicane_nav navigation_node  # 주행 노드
rosrun aicane_nav monitor_node     # 모니터링 노드
rosrun aicane_nav sensor_node      # 센서 노드
```

**노드 구조:**
```
[navigation_node] ─┬─> /cmd_vel (속도 명령)
                   ├─> /odom (오도메트리)
                   └─> /pose (위치)

[monitor_node] ────> /status (상태)

[sensor_node] ─────> /ultrasonic (초음파)
```

---

## 💡 **우리 프로젝트는?**

### **ROS 안 씀! (이미 결정함)**

```python
# 우리 방식 (단일 프로세스)
from aicane_navigation import NavigationSystem

nav = NavigationSystem()
nav.navigate_rooms('101호', '107호')
```

**차이점:**
| | ROS | 우리 |
|---|---|---|
| 프로세스 | 여러 개 | 1개 |
| 통신 | Topic/Service | 직접 호출 |
| 복잡도 | 높음 | 낮음 |
| 노드 폴더 | 필요 | 불필요 |

---

## 🗑️ **어떻게 할까?**

### **Option 1: 완전 제거 (추천!)** ⭐⭐⭐

```bash
# nodes 폴더 삭제
rm -rf aicane_navigation/nodes/
```

**이유:**
- ✅ ROS 안 쓰니까 불필요
- ✅ 코드 정리
- ✅ 혼란 방지

---

### **Option 2: 유틸리티로 변환** ⭐⭐

```
nodes/monitor_node.py (빈 파일)
    ↓
utils/live_monitor.py (실제 기능)
```

**만약 모니터링이 필요하다면:**
```python
from aicane_navigation.utils import LiveMonitor

monitor = LiveMonitor(nav)
monitor.start()  # 백그라운드 모니터링
```

**제공 기능:**
- 실시간 위치 출력
- 센서 값 출력
- 상태 모니터링

---

### **Option 3: 그냥 두기** ⭐

```
# 빈 폴더로 둠
# 나중에 ROS로 전환하면 사용
```

**단점:**
- ⚠️ 혼란 유발
- ⚠️ 불필요한 파일

---

## 📊 **기능 비교**

### **ROS nodes vs 우리 시스템:**

| 기능 | ROS nodes | 우리 시스템 |
|------|----------|-----------|
| **주행** | navigation_node | NavigationSystem |
| **센서** | sensor_node | ObstacleDetector |
| **위치** | localization_node | LocalizationTier |
| **모니터** | monitor_node | LiveMonitor (선택) |
| **통신** | Topic/Service | 직접 호출 |

---

## 💡 **최종 권장사항**

### **제거하세요!** ⭐⭐⭐

```bash
# nodes 폴더 삭제
cd C:/25L/aicane_navigation/aicane_navigation
rm -rf nodes/
```

**이유:**
1. ✅ ROS 안 씀
2. ✅ 기능 중복 (NavigationSystem이 이미 함)
3. ✅ 코드 정리
4. ✅ 혼란 방지

---

### **만약 모니터링 필요하면:**

```python
# utils/live_monitor.py 사용 (방금 생성함!)
from aicane_navigation.utils import LiveMonitor
from aicane_navigation import NavigationSystem

nav = NavigationSystem()
monitor = LiveMonitor(nav)

monitor.start()  # 백그라운드 모니터링

# 주행 (모니터링 하면서)
nav.navigate_rooms('101호', '107호')

monitor.stop()
```

---

## 🎯 **실전 가이드**

### **1. nodes 폴더 제거**
```bash
rm -rf aicane_navigation/nodes/
```

### **2. 모니터링 필요시**
```python
# utils/live_monitor.py 사용
from aicane_navigation.utils import LiveMonitor

monitor = LiveMonitor(nav)
monitor.start()
```

### **3. 디버깅은 로그로**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("위치: (%.1f, %.1f)", x, y)
logger.debug("센서: F=%.1f L=%.1f R=%.1f", f, l, r)
```

---

## 🎉 **결론**

### **Q: nodes 폴더는 뭐야?**

### **A: ROS용으로 만들었던 것! 지금은 불필요!** ✅

**이유:**
1. ✅ ROS 안 씀 (단일 프로세스)
2. ✅ 기능 중복 (NavigationSystem)
3. ✅ 빈 파일들 (0 bytes)

**권장:**
- ✅ 폴더 제거
- ✅ 모니터링 필요시 `utils/live_monitor.py` 사용
- ✅ 디버깅은 로깅으로

**→ nodes 폴더 삭제하고, 필요하면 LiveMonitor 사용!** 🚀
