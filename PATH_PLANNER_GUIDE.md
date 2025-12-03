# PathPlanner 완전 가이드 🗺️

## 🤔 **팀원 제안 평가**

### **팀원 코드:**
```python
class PathPlanner:
    def plan(self, start, goal, steps=20):
        # 단순 직선 (선형 보간)
        return [(x, y), ...]
```

### **평가:**

| 항목 | 평가 | 설명 |
|------|------|------|
| **간단함** | ⭐⭐⭐⭐⭐ | 매우 이해하기 쉬움 |
| **작동** | ✅ | 직선 경로 생성함 |
| **속도** | ⭐⭐⭐⭐⭐ | 매우 빠름 |
| **현실성** | ❌ | 벽을 뚫고 감 |
| **복도 고려** | ❌ | 건물 구조 무시 |
| **장애물 회피** | ❌ | 장애물 못 피함 |
| **AI 통합** | ❌ | AI 경로 사용 불가 |

---

## 💡 **우리 프로젝트 요구사항**

### **필수 기능:**
1. ✅ **AI 경로 통합** - AI 모델이 준 경로 우선
2. ✅ **복도 기반** - 건물 구조 고려
3. ✅ **장애물 회피** - 동적 재계획
4. ✅ **층 이동** - 계단 처리
5. ✅ **웨이포인트 보간** - 부드러운 경로
6. ✅ **경로 스무딩** - 자연스러운 주행

### **팀원 코드가 제공:**
- ✅ 선형 보간만 (1개)

---

## 📊 **코드 비교**

### **팀원 제안 vs 개선 코드:**

| 기능 | 팀원 코드 | 개선 코드 |
|------|----------|----------|
| **직선 경로** | ✅ | ✅ |
| **AI 경로** | ❌ | ✅ |
| **복도 기반** | ❌ | ✅ |
| **장애물 회피** | ❌ | ✅ |
| **웨이포인트 보간** | ❌ | ✅ |
| **경로 스무딩** | ❌ | ✅ |
| **다층 지원** | ❌ | ✅ |
| **총 기능** | 1개 | 7개 |

---

## 🎯 **개선 코드 핵심 기능**

### **1. AI 경로 통합 (최우선)** ⭐⭐⭐
```python
planner = PathPlanner(multi_map)

# AI 경로 JSON
ai_json = {
    "path": [
        {"floor": 1, "x": 120, "y": 41},
        {"floor": 2, "x": 150, "y": 80},
    ]
}

# 파싱 및 사용
waypoints = planner.plan_with_ai(ai_json)
```

**장점:**
- AI 모델의 최적 경로 사용
- 계단 자동 처리
- 다층 건물 지원

---

### **2. 복도 기반 경로 (대체)** ⭐⭐
```python
planner = PathPlanner(floor_plan, room_mgr)

# 방 간 경로
waypoints = planner.plan_room_to_room('101호', '107호')
```

**장점:**
- 건물 구조 고려
- 벽을 뚫지 않음
- 복도 따라감

---

### **3. 단순 직선 (팀원 제안, 비상용)** ⭐
```python
# 비상 상황만
waypoints = planner.plan_straight((0, 0), (1000, 1000), steps=20)
```

**주의:**
- ⚠️ 벽을 뚫을 수 있음
- ⚠️ 비상용만 사용
- ⚠️ 테스트용

---

### **4. 웨이포인트 보간**
```python
# 성긴 경로
sparse = [
    (0, 0, 0),
    (500, 0, 0),
    (500, 500, 90),
]

# 부드러운 경로
dense = planner.interpolate_waypoints(sparse, max_gap=50)

print(f"원본: {len(sparse)}개 → 보간: {len(dense)}개")
```

---

### **5. 장애물 회피**
```python
# 장애물 발견!
new_path = planner.replan_avoiding_obstacle(
    current_pos=(400, 800, 0),
    goal_pos=(900, 800, 0),
    obstacle_pos=(650, 800),
    obstacle_radius=100,
)

# 우회 경로로 주행
```

---

### **6. 경로 스무딩**
```python
# 지그재그 경로
zigzag = [(0,0,0), (100,50,0), (200,0,0), (300,50,0)]

# 부드럽게
smooth = planner.smooth_path(zigzag, smoothing_factor=0.5)
```

---

## 🔄 **사용 패턴**

### **패턴 1: AI 경로 사용 (최우선!)** ⭐⭐⭐
```python
from aicane_navigation.mapping import MultiFloorCorridorMap
from aicane_navigation.navigation import PathPlanner

# 맵 + 플래너
multi_map = MultiFloorCorridorMap()
planner = PathPlanner(multi_map)

# AI 경로
ai_json = get_ai_path()  # AI 모델에서
waypoints = planner.plan_with_ai(ai_json)

# 보간 (부드럽게)
waypoints = planner.interpolate_waypoints(waypoints, max_gap=50)

# 주행
for x, y, theta in waypoints:
    nav.move_to(x, y, theta)
```

---

### **패턴 2: 복도 기반 (AI 없을 때)** ⭐⭐
```python
from aicane_navigation.mapping import FloorPlan, RoomManager
from aicane_navigation.navigation import PathPlanner

# 맵 + 플래너
floor_plan = FloorPlan()
room_mgr = RoomManager(floor_plan)
planner = PathPlanner(floor_plan, room_mgr)

# 방 간 경로
waypoints = planner.plan_room_to_room('101호', '107호')

# 보간
waypoints = planner.interpolate_waypoints(waypoints)

# 주행
for x, y, theta in waypoints:
    nav.move_to(x, y, theta)
```

---

### **패턴 3: 장애물 회피 (동적)** ⭐⭐⭐
```python
# 주행 중
current = nav.get_current_position()
goal = waypoints[next_index]

# 장애물 감지!
if obstacle_detected:
    obstacle = nav.get_obstacle_position()
    
    # 경로 재계획
    new_path = planner.replan_avoiding_obstacle(
        current_pos=current,
        goal_pos=goal,
        obstacle_pos=obstacle,
    )
    
    # 우회 경로로 변경
    waypoints = new_path + waypoints[next_index+1:]
```

---

### **패턴 4: 단순 직선 (테스트만!)** ⚠️
```python
# 테스트용
planner = PathPlanner(None)

# 직선 경로
waypoints = planner.plan_straight((0, 0), (1000, 1000), steps=20)

# ⚠️ 실제 주행에는 사용하지 마세요!
```

---

## 💡 **실전 예제**

### **예제 1: 완전 자동 주행**
```python
from aicane_navigation import NavigationSystem
from aicane_navigation.mapping import MultiFloorCorridorMap
from aicane_navigation.navigation import PathPlanner

# 시스템 구축
nav = NavigationSystem()
multi_map = MultiFloorCorridorMap()
planner = PathPlanner(multi_map)

# AI 경로 받기
ai_json = request_ai_path('101호', '307호')

# 경로 계획
waypoints = planner.plan_with_ai(ai_json)
waypoints = planner.interpolate_waypoints(waypoints, max_gap=50)
waypoints = planner.smooth_path(waypoints, smoothing_factor=0.3)

print(f"총 {len(waypoints)}개 waypoint")
print(f"총 거리: {planner.get_path_length(waypoints):.1f}cm")

# 주행
for i, (x, y, theta) in enumerate(waypoints):
    print(f"Waypoint {i+1}/{len(waypoints)}")
    nav.move_to(x, y, theta)
    
    # 장애물 체크
    if nav.check_obstacle():
        print("장애물 감지! 재계획...")
        obstacle = nav.get_obstacle_position()
        
        # 남은 경로 재계획
        remaining = planner.replan_avoiding_obstacle(
            current_pos=nav.get_current_position(),
            goal_pos=waypoints[-1],
            obstacle_pos=obstacle,
        )
        
        waypoints = waypoints[:i+1] + remaining

print("✅ 도착!")
```

---

### **예제 2: 복도 주행 (1층)**
```python
from aicane_navigation.mapping import FloorPlan, RoomManager
from aicane_navigation.navigation import PathPlanner

# 시스템
floor_plan = FloorPlan()
room_mgr = RoomManager(floor_plan)
planner = PathPlanner(floor_plan, room_mgr)

# 경로 계획
waypoints = planner.plan_room_to_room('101호', '107호')

# 최적화
waypoints = planner.interpolate_waypoints(waypoints, max_gap=50)
waypoints = planner.smooth_path(waypoints)

# 주행
nav = NavigationSystem()
for x, y, theta in waypoints:
    nav.move_to(x, y, theta)
```

---

## 📝 **최종 권장사항**

### **팀원 코드는?**

### **Option 1: 일부만 사용** ⭐
```python
# plan_straight() 메서드로 포함
class PathPlanner:
    def plan_straight(self, start, goal, steps):
        # 팀원 제안 코드
        # 비상용/테스트용만
```

**이유:**
- ✅ 팀원 아이디어 반영
- ✅ 비상 상황 대비
- ⚠️ 주의사항 명시

---

### **Option 2: 개선 코드 사용 (추천!)** ⭐⭐⭐
```python
from aicane_navigation.navigation import PathPlanner

# 모든 기능
planner = PathPlanner(map_system, room_mgr)

# 1순위: AI 경로
if ai_path:
    waypoints = planner.plan_with_ai(ai_path)

# 2순위: 복도 기반
else:
    waypoints = planner.plan_room_to_room('101호', '107호')

# 3순위: 직선 (비상)
# waypoints = planner.plan_straight(...)  # 사용 금지!
```

---

## 🎉 **결론**

### **Q: 팀원 코드 수용할까?**

### **A: 일부만 수용! (비상용)** ✅

**이유:**
1. ✅ 팀원 아이디어 존중 (`plan_straight()` 메서드)
2. ✅ 하지만 실제로는 AI 경로 + 복도 기반 사용
3. ✅ 직선 경로는 비상용/테스트용만

### **최종 구조:**
```python
class PathPlanner:
    # ⭐⭐⭐ 최우선
    def plan_with_ai(ai_json)
    
    # ⭐⭐ 대체
    def plan_room_to_room(from_room, to_room)
    
    # ⭐ 비상 (팀원 제안)
    def plan_straight(start, goal, steps)
    
    # 추가 기능
    def interpolate_waypoints(...)
    def smooth_path(...)
    def replan_avoiding_obstacle(...)
```

**→ 팀원 코드를 포함하되, 실제로는 AI/복도 경로 사용!** 🚀
