# Logger 완전 가이드 📝

## 🤔 **팀원 제안 평가**

### **팀원 코드:**
```python
class NavigationLogger:
    def log_position(pose, tier, confidence)
    def log_event(message, tier, extra)
```

### **평가:**

| 항목 | 팀원 코드 | 개선 코드 |
|------|----------|----------|
| **간단함** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **작동** | ✅ | ✅ |
| **파일 저장** | ❌ | ✅ |
| **Python logging** | ❌ | ✅ |
| **장애물 로그** | ❌ | ✅ |
| **명령어 로그** | ❌ | ✅ |
| **통계** | ❌ | ✅ |
| **총 기능** | 2개 | 10+ |

---

## 💡 **팀원 코드 장단점**

### **장점:** ✅
1. **매우 간단** - 10줄 수준
2. **의존성 없음** - print만
3. **작동함** - 기본 로깅 가능

### **단점:** ❌
1. **파일 저장 없음** - 터미널 꺼지면 사라짐
2. **로그 레벨 제한** - tier 0~3만
3. **표준 라이브러리 미사용** - Python logging X
4. **장애물 로그 없음** - 골격엔 있는데 팀원 코드엔 없음
5. **명령어 로그 없음** - 로봇 명령 기록 X
6. **필터링 어려움** - 로그 검색 불편
7. **로그 관리 없음** - 파일 분리, 백업 등

---

## 📊 **기능 비교**

### **팀원 코드:**
```python
logger = NavigationLogger("aicane")

# 위치 로그
logger.log_position((100, 200, 90), tier=1, confidence=0.9)
# [2025-12-03 15:30:00] [aicane] [INFO] pose=(100.00, 200.00, 90.00), confidence=0.90

# 이벤트 로그
logger.log_event("장애물 감지", tier=2, extra={'distance': 45})
# [2025-12-03 15:30:01] [aicane] [WARN] 장애물 감지 | extra={'distance': 45}
```

**총 기능: 2개**

---

### **개선 코드:**
```python
logger = NavigationLogger(
    name="aicane",
    log_to_file=True,       # ✅ 파일 저장
    log_dir="./logs",
    level="INFO"
)

# 1. 위치 로그 (팀원 제안 포함)
logger.log_position((100, 200, 90), tier=1, confidence=0.9)

# 2. 장애물 로그 (신규!)
logger.log_obstacle({
    'front': 45,
    'left': 120,
    'right': 98,
    'action': 'slow_down',
    'source': 'ultrasonic'
}, severity="WARNING")

# 3. 명령어 로그 (신규!)
logger.log_command('forward', 10, extra={'reason': 'waypoint'})

# 4. 이벤트 로그 (팀원 제안)
logger.log_event("경로 재계획", tier=2, extra={'attempts': 3})

# 5. 단축 메서드 (신규!)
logger.info("웨이포인트 도착")
logger.warning("GPS 신호 약함")
logger.error("센서 오류")

# 6. 주행 시작/종료 (신규!)
logger.log_navigation_start("101호", "107호")
logger.log_navigation_end(success=True)

# 7. 통계 (신규!)
logger.print_stats()

# 8. 파일 저장 (신규!)
logger.save_to_file("./logs/backup.log")
```

**총 기능: 10+개**

---

## 🎯 **개선 코드 핵심 기능**

### **1. 파일 저장** ⭐⭐⭐
```python
# 자동 파일 저장
logger = NavigationLogger(log_to_file=True)

# 로그 파일: ./logs/nav_20251203_153000.log
# 터미널 + 파일 동시 저장!
```

**장점:**
- ✅ 터미널 꺼져도 로그 보존
- ✅ 날짜별 자동 분리
- ✅ 나중에 분석 가능

---

### **2. Python logging 사용** ⭐⭐⭐
```python
# 표준 라이브러리 활용
import logging

logger.setLevel(logging.DEBUG)  # 레벨 동적 변경
logger.addHandler(...)           # 핸들러 추가
```

**장점:**
- ✅ 표준 기능 활용
- ✅ 로그 레벨 정확
- ✅ 필터링 쉬움

---

### **3. 장애물 로그** ⭐⭐⭐
```python
logger.log_obstacle({
    'front': 45.0,
    'left': 120.0,
    'right': 98.0,
    'action': 'slow_down',
    'source': 'ultrasonic'
}, severity="WARNING")

# [2025-12-03 15:30:00] [aicane] [WARNING] Obstacle: [front=45.0cm, left=120.0cm, right=98.0cm] | Action: slow_down | Source: ultrasonic
```

**현재 골격에 있는데** 팀원 코드엔 없음!

---

### **4. 명령어 로그** ⭐⭐
```python
logger.log_command('forward', 10, extra={'reason': 'waypoint'})

# [2025-12-03 15:30:00] [aicane] [DEBUG] Command: FORWARD | Speed: 10 | reason=waypoint
```

---

### **5. 통계** ⭐⭐
```python
logger.print_stats()

# === 로그 통계 ===
#   positions_logged: 245
#   obstacles_logged: 12
#   commands_logged: 523
#   events_logged: 38
```

---

### **6. 주행 시작/종료** ⭐⭐
```python
logger.log_navigation_start("101호", "107호")
# ==================================================
# 주행 시작: 101호 → 107호
# ==================================================

logger.log_navigation_end(success=True, reason="목적지 도착")
# ==================================================
# 주행 종료: 성공
# 사유: 목적지 도착
# === 로그 통계 ===
# ...
# ==================================================
```

---

## 🔄 **사용 패턴**

### **패턴 1: 기본 (팀원 제안 수용)** ⭐⭐
```python
logger = NavigationLogger()

# 팀원 제안 그대로 사용 가능!
logger.log_position((100, 200, 90), tier=1, confidence=0.9)
logger.log_event("장애물 감지", tier=2)
```

**장점:**
- ✅ 팀원 아이디어 반영
- ✅ + 파일 저장 자동

---

### **패턴 2: 완전 활용 (추천!)** ⭐⭐⭐
```python
logger = NavigationLogger(
    log_to_file=True,
    log_dir="./logs",
    level="INFO"
)

# 주행 시작
logger.log_navigation_start("101호", "107호")

# 위치
logger.log_position((100, 200, 90), tier=1, confidence=0.95,
                   extra={'tier': 1, 'source': 'ultrasonic'})

# 장애물
logger.log_obstacle({
    'front': 45, 'left': 120, 'right': 98,
    'action': 'slow_down', 'source': 'ultrasonic'
}, severity="WARNING")

# 명령어
logger.log_command('forward', 10)

# 이벤트
logger.info("웨이포인트 도착")
logger.warning("GPS 신호 약함")

# 주행 종료
logger.log_navigation_end(success=True)
```

---

### **패턴 3: 전역 로거** ⭐⭐
```python
from aicane_navigation.utils import get_logger

# 어디서든 동일한 로거
logger = get_logger()

# 다른 파일에서도
logger = get_logger()  # 같은 인스턴스!
```

---

## 💡 **실전 예제**

### **예제 1: NavigationSystem 통합**
```python
from aicane_navigation.utils import NavigationLogger

class NavigationSystem:
    def __init__(self):
        self.logger = NavigationLogger(log_to_file=True)
        self.logger.info("NavigationSystem 초기화 완료")
    
    def navigate_rooms(self, from_room, to_room):
        # 시작
        self.logger.log_navigation_start(from_room, to_room)
        
        try:
            # 주행 중...
            for waypoint in waypoints:
                # 위치
                self.logger.log_position(
                    pose=current_pose,
                    tier=1,
                    confidence=self.localization.get_confidence()
                )
                
                # 장애물 체크
                if obstacle_detected:
                    self.logger.log_obstacle(obstacle_info, "WARNING")
                
                # 명령
                self.logger.log_command('forward', 10)
            
            # 성공
            self.logger.log_navigation_end(success=True)
        
        except Exception as e:
            # 실패
            self.logger.error(f"주행 실패: {e}")
            self.logger.log_navigation_end(success=False, reason=str(e))
```

---

### **예제 2: 로그 분석**
```bash
# 로그 파일 보기
cat ./logs/nav_20251203_153000.log

# 에러만 보기
grep ERROR ./logs/nav_20251203_153000.log

# 장애물만 보기
grep Obstacle ./logs/nav_20251203_153000.log

# 위치만 보기
grep Position ./logs/nav_20251203_153000.log
```

---

## 📝 **최종 권장사항**

### **Q: 팀원 코드 어때?**

### **A: 좋은데, 개선 버전 사용!** ⭐⭐⭐

**이유:**
1. ✅ **팀원 아이디어 반영** - log_position, log_event 그대로
2. ✅ **파일 저장** - 로그 보존
3. ✅ **Python logging** - 표준 기능
4. ✅ **현재 골격 반영** - obstacle, command 추가
5. ✅ **추가 기능** - 통계, 주행 시작/종료

---

### **비교:**

| | 팀원 제안 | 개선 코드 |
|---|---|---|
| **간단함** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **기능** | 2개 | 10+개 |
| **파일 저장** | ❌ | ✅ |
| **로그 관리** | ❌ | ✅ |
| **실용성** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **추천도** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎉 **결론**

### **팀원 제안 → 반영하되 개선!** ✅

**최종 코드:**
```python
class NavigationLogger:
    # ✅ 팀원 제안 (그대로)
    def log_position(pose, tier, confidence, extra)
    def log_event(message, tier, extra)
    
    # ✅ 개선 추가
    def log_obstacle(...)        # 현재 골격에 있음
    def log_command(...)         # 현재 골격에 있음
    def info/warning/error(...)  # 단축 메서드
    def log_navigation_start/end(...)  # 주행 관리
    def print_stats(...)         # 통계
    def save_to_file(...)        # 파일 관리
```

**사용:**
```python
# 팀원 방식 (그대로 작동!)
logger.log_position((100, 200, 90), tier=1, confidence=0.9)
logger.log_event("장애물", tier=2)

# + 추가 기능
logger.log_obstacle(...)
logger.log_command(...)
logger.info("메시지")
```

**→ 팀원 아이디어 존중 + 실용성 대폭 향상!** 🚀🎊
