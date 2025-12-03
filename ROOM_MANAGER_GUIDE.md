# RoomManager 완전 가이드 🚪

## 🤔 **필요한가?**

### **현재 상황:**
```
✅ FloorPlan - 이미 방 정보 있음
✅ MultiFloorMap - 이미 방 정보 있음
❓ RoomManager - 중복 아닌가?
```

---

## 📊 **중복 분석**

### **FloorPlan에 이미 있음:**
```python
class FloorPlan:
    def _init_rooms(self):
        return {
            '101호': {
                'door_x': 380,
                'door_y': 1072.5,
                'door_direction': 'south',
            }
        }
    
    def get_room_waypoint(self, room_name):
        return (x, y, theta)
```

### **MultiFloorMap에도 있음:**
```python
class MultiFloorCorridorMap:
    self.floors[1] = {
        'rooms': {
            '101호': {'x': 120, 'y': 41}
        }
    }
```

---

## 💡 **그럼 왜 RoomManager?**

### **장점: 통합 인터페이스!** ⭐

```python
# 문제: 각 맵마다 API가 다름
floor_plan.get_room_waypoint('101호')     # FloorPlan
multi_map.floors[1]['rooms']['101호']      # MultiFloorMap

# 해결: 통일된 API
room_mgr.get_door_position('101호')        # 어떤 맵이든 동일!
```

---

## 🎯 **RoomManager의 역할**

### **1. 통합 접근**
```python
from aicane_navigation.mapping import RoomManager, FloorPlan

# FloorPlan 연결
floor_plan = FloorPlan()
room_mgr = RoomManager(floor_plan)

# 통일된 API
pos = room_mgr.get_door_position('101호')
waypoint = room_mgr.get_door_waypoint('101호')
```

### **2. 추가 기능**
```python
# 가장 가까운 방
nearest = room_mgr.get_nearest_room(x=500, y=200, floor=1)

# 층별 필터링
floor1_rooms = room_mgr.list_rooms_by_floor(1)

# 검색
offices = room_mgr.search_rooms(floor=1, room_type='office')
```

### **3. 방 관리**
```python
# 방 추가
room_mgr.add_room('119호', {
    'floor': 1,
    'door_x': 600,
    'door_y': 200,
})

# 방 업데이트
room_mgr.update_room('101호', {'type': 'conference'})

# 방 제거
room_mgr.remove_room('119호')
```

---

## 📊 **비교표**

| 기능 | FloorPlan | MultiFloorMap | RoomManager |
|------|----------|--------------|------------|
| **방 정보** | ✅ | ✅ | ✅ |
| **통일된 API** | ❌ | ❌ | ✅ |
| **가까운 방** | ❌ | ❌ | ✅ |
| **검색** | ❌ | ❌ | ✅ |
| **동적 추가** | ❌ | ❌ | ✅ |
| **층별 필터** | ❌ | ⚠️ | ✅ |

---

## 🔄 **사용 패턴**

### **패턴 1: RoomManager 없이 (현재도 OK)**
```python
from aicane_navigation.mapping import FloorPlan

floor_plan = FloorPlan()
waypoint = floor_plan.get_room_waypoint('101호')
# 작동함! ✅
```

**장점:**
- 간단함
- 기존 코드 그대로

**단점:**
- API 통일 안 됨
- 추가 기능 없음

---

### **패턴 2: RoomManager 사용 (추천!)**
```python
from aicane_navigation.mapping import FloorPlan, RoomManager

floor_plan = FloorPlan()
room_mgr = RoomManager(floor_plan)

# 통일된 API
pos = room_mgr.get_door_position('101호')
waypoint = room_mgr.get_door_waypoint('101호')

# 추가 기능
nearest = room_mgr.get_nearest_room(500, 200, 1)
```

**장점:**
- ✅ API 통일
- ✅ 추가 기능
- ✅ 유연함

**단점:**
- 약간 복잡

---

### **패턴 3: UnifiedMapSystem + RoomManager (최고!)**
```python
from aicane_navigation.mapping import UnifiedMapSystem, RoomManager

map_sys = UnifiedMapSystem(mode='multi_floor')
room_mgr = RoomManager(map_sys)

# 모든 기능 사용
pos = room_mgr.get_door_position('101호')     # 1층
pos = room_mgr.get_door_position('307호')     # 3층
nearest = room_mgr.get_nearest_room(500, 200, 2)
```

**장점:**
- ✅✅ 최고의 유연성
- ✅✅ 모든 기능

---

## 💡 **실전 시나리오**

### **시나리오 1: 현재 위치에서 가장 가까운 방**
```python
room_mgr = RoomManager(floor_plan)

# 로봇 위치
current_x = 500
current_y = 800
current_floor = 1

# 가장 가까운 방
nearest = room_mgr.get_nearest_room(current_x, current_y, current_floor)
print(f"가장 가까운 방: {nearest}")

# 그 방으로 이동
waypoint = room_mgr.get_door_waypoint(nearest)
nav.move_to(*waypoint)
```

---

### **시나리오 2: 층별 방 순회**
```python
room_mgr = RoomManager(multi_map)

# 1층 모든 방 방문
for room_name in room_mgr.list_rooms_by_floor(1):
    waypoint = room_mgr.get_door_waypoint(room_name)
    print(f"{room_name} 방문: {waypoint}")
    nav.move_to(*waypoint)
```

---

### **시나리오 3: 동적 방 추가 (임시 목적지)**
```python
room_mgr = RoomManager(floor_plan)

# 임시 목적지 추가
room_mgr.add_room('임시A', {
    'floor': 1,
    'door_x': 1000,
    'door_y': 1312,
    'door_direction': 'north',
})

# 그곳으로 이동
waypoint = room_mgr.get_door_waypoint('임시A')
nav.move_to(*waypoint)

# 완료 후 제거
room_mgr.remove_room('임시A')
```

---

## 📝 **최종 권장사항**

### **Option 1: 안 써도 됨** ✅
```python
# 기존 코드 그대로
from aicane_navigation.mapping import FloorPlan

floor_plan = FloorPlan()
waypoint = floor_plan.get_room_waypoint('101호')
```

**조건:**
- 1층만 사용
- 추가 기능 불필요
- 간단한 프로젝트

---

### **Option 2: 써도 좋음** ⭐
```python
# 통일된 API
from aicane_navigation.mapping import RoomManager, FloorPlan

room_mgr = RoomManager(FloorPlan())
pos = room_mgr.get_door_position('101호')
```

**조건:**
- API 통일 원함
- 추가 기능 필요 (가까운 방, 검색 등)
- 확장성 중요

---

### **Option 3: 강력 추천!** ⭐⭐⭐
```python
# UnifiedMapSystem + RoomManager
from aicane_navigation.mapping import UnifiedMapSystem, RoomManager

map_sys = UnifiedMapSystem(mode='multi_floor')
room_mgr = RoomManager(map_sys)

# 모든 기능 + 유연성
```

**조건:**
- 다층 건물
- AI 경로 통합
- 최대 유연성

---

## 🎉 **결론**

### **Q: RoomManager 안 써도 돼?**

### **A: 상황에 따라!**

| 상황 | 권장 |
|------|------|
| **1층만 + 간단** | ❌ 불필요 (FloorPlan 충분) |
| **다층 + API 통일** | ✅ 권장 |
| **추가 기능 필요** | ✅ 권장 |
| **동적 관리 필요** | ✅ 필수 |

---

### **팀원 제안 코드 vs 개선 코드:**

| | 팀원 제안 | 개선 코드 |
|---|---|---|
| **기본 기능** | ✅ | ✅ |
| **맵 통합** | ❌ | ✅ |
| **가까운 방** | ❌ | ✅ |
| **검색** | ❌ | ✅ |
| **동적 관리** | ❌ | ✅ |

---

### **최종 답변:**

**넣어두는 게 좋습니다!** ✅

**이유:**
1. ✅ 팀원 제안 반영
2. ✅ API 통일
3. ✅ 추가 기능 (가까운 방, 검색)
4. ✅ 확장성
5. ✅ 사용 안 해도 문제없음

**→ 있으면 유용, 없어도 문제없음. 넣어두는 게 나중을 위해 좋음!** 🚀
