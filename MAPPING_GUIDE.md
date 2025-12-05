# Mapping 모듈 완전 가이드 🗺️

## 📂 **파일 구조**

```
aicane_navigation/mapping/
├── __init__.py
├── floor_plan.py           ← 기존 (1층 단층용)
├── multi_floor_map.py      ← 신규 (3층 다층용)
└── unified_map.py          ← 통합 (자동 선택)
```

---

## 🔍 **각 파일 상세 설명**

### **1. `floor_plan.py` - 1층 전용** 📍

```python
class FloorPlan:
    """
    1층 평면도만 다룸
    초음파 위치 보정에 최적화
    """
```

**기능:**
- ✅ 1층 복도 정보 (horizontal, vertical, lobby)
- ✅ 1층 방 위치 (101~118호)
- ✅ 초음파 보정용 벽 정보
- ✅ 간단한 A* 경로 생성
- ✅ 복도 타입 판별

**사용 시기:**
- 1층만 주행
- 초음파 위치 보정
- AI 경로 없음

**예제:**
```python
from aicane_navigation.mapping import FloorPlan

floor_plan = FloorPlan()

# 복도 확인
corridor = floor_plan.get_corridor_at(x=500, y=1312)
print(corridor['name'])  # '중앙 메인 복도'

# 간단한 경로
path = floor_plan.generate_simple_path('101호', '107호')
```

**장점:**
- ⚡ 빠름 (1층만)
- 🎯 초음파 최적화
- 📦 간단함

**단점:**
- ❌ 1층만 지원
- ❌ AI 경로 통합 없음
- ❌ 계단 없음

---

### **2. `multi_floor_map.py` - 3층 전용** 🏢

```python
class MultiFloorCorridorMap:
    """
    3층 건물 전체 관리
    AI 경로 + 계단 + 장애물 회피
    """
```

**기능:**
- ✅ 3층 모두 지원 (1~3층)
- ✅ AI 경로 JSON 파싱
- ✅ 계단 위치 관리
- ✅ 층별 데이터 필터링
- ✅ 장애물 회피 경로
- ✅ JSON 저장/로드

**사용 시기:**
- 다층 건물 주행
- AI 경로 사용
- 계단 이동

**예제:**
```python
from aicane_navigation.mapping import MultiFloorCorridorMap

multi_map = MultiFloorCorridorMap()

# AI 경로 파싱
ai_json = {
    "path": [
        {"floor": 1, "x": 120, "y": 41},
        {"floor": 2, "x": 150, "y": 80},
        {"floor": 3, "x": 300, "y": 180},
    ]
}

waypoints = multi_map.parse_ai_path(ai_json)

for wp in waypoints:
    print(f"층={wp['floor']}, 타입={wp['type']}")
```

**장점:**
- 🏢 다층 지원
- 🤖 AI 통합
- 🪜 계단 관리
- 🚧 회피 경로

**단점:**
- 🐢 1층만 쓸 땐 오버헤드
- 📊 복잡함

---

### **3. `unified_map.py` - 통합 시스템** 🎯

```python
class UnifiedMapSystem:
    """
    자동으로 최적의 맵 선택
    단층 ↔ 다층 자동 전환
    """
```

**기능:**
- ✅ 모드 자동 선택
- ✅ 단일 API
- ✅ 기존 코드 호환
- ✅ AI 경로 자동 감지

**사용 시기:**
- **추천: 항상!**
- 모드 모를 때
- 유연성 필요

**예제:**
```python
from aicane_navigation.mapping import UnifiedMapSystem

# 자동 선택
map_system = UnifiedMapSystem(
    mode='single_floor',  # 또는 'multi_floor'
    ai_enabled=False
)

# 통합 API
corridor = map_system.get_corridor_at(floor=1, x=500, y=1312)
path = map_system.generate_simple_path('101호', '107호')
```

**장점:**
- 🎯 자동 최적화
- 📝 단일 API
- 🔄 유연함

**단점:**
- 없음!

---

## 📊 **비교표**

| 기능 | FloorPlan | MultiFloorMap | UnifiedMap |
|------|----------|--------------|-----------|
| **1층 지원** | ✅ | ✅ | ✅ |
| **다층 지원** | ❌ | ✅ | ✅ |
| **AI 경로** | ❌ | ✅ | ✅ |
| **계단** | ❌ | ✅ | ✅ |
| **초음파 최적화** | ✅ | ⚠️ | ✅ |
| **속도 (1층만)** | ⚡⚡⚡ | ⚡⚡ | ⚡⚡⚡ |
| **복잡도** | 낮음 | 높음 | 중간 |
| **추천도** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 **사용 가이드**

### **시나리오 1: 1층만 주행**

```python
# Option A: FloorPlan (최적화)
from aicane_navigation.mapping import FloorPlan

floor_plan = FloorPlan()
path = floor_plan.generate_simple_path('101호', '107호')
```

```python
# Option B: UnifiedMap (권장!)
from aicane_navigation.mapping import UnifiedMapSystem

map_sys = UnifiedMapSystem(mode='single_floor')
path = map_sys.generate_simple_path('101호', '107호')
```

---

### **시나리오 2: 3층 + AI 경로**

```python
# Option A: MultiFloorMap (직접)
from aicane_navigation.mapping import MultiFloorCorridorMap

multi_map = MultiFloorCorridorMap()
waypoints = multi_map.parse_ai_path(ai_json)
```

```python
# Option B: UnifiedMap (권장!)
from aicane_navigation.mapping import UnifiedMapSystem

map_sys = UnifiedMapSystem(mode='multi_floor', ai_enabled=True)
waypoints = map_sys.parse_ai_path(ai_json)
```

---

### **시나리오 3: 모를 때 (권장!)** ⭐

```python
from aicane_navigation.mapping import UnifiedMapSystem

# 1층만? 다층?  → 자동 선택!
map_sys = UnifiedMapSystem(
    mode='multi_floor' if AI_PATH else 'single_floor',
    ai_enabled=True if AI_PATH else False
)

# 통합 API로 뭐든 가능
if AI_PATH:
    waypoints = map_sys.parse_ai_path(ai_json)
else:
    waypoints = map_sys.generate_simple_path('101호', '107호')
```

---

## 🔄 **기존 코드 마이그레이션**

### **기존 코드:**
```python
from aicane_navigation.mapping import FloorPlan

floor_plan = FloorPlan()
corridor = floor_plan.get_corridor_at(x, y)
```

### **새 코드 (호환됨!):**
```python
from aicane_navigation.mapping import UnifiedMapSystem

map_sys = UnifiedMapSystem(mode='single_floor')
corridor = map_sys.get_corridor_at(floor=1, x=x, y=y)
```

**변경 최소화!** ✅

---

## 💡 **최종 권장사항**

### **프로젝트 초기:** 🚀
```python
from aicane_navigation.mapping import UnifiedMapSystem

# 유연하게 시작
map_sys = UnifiedMapSystem(mode='multi_floor', ai_enabled=True)
```

**이유:**
- ✅ 나중에 AI 추가해도 OK
- ✅ 나중에 다층 확장해도 OK
- ✅ 지금 1층만 써도 OK

---

### **성능 중요 시:** ⚡
```python
from aicane_navigation.mapping import FloorPlan

# 1층만 확실하면
floor_plan = FloorPlan()
```

**이유:**
- ⚡ 가장 빠름
- 🎯 초음파 최적화
- 📦 단순함

---

### **확장성 중요 시:** 🏢
```python
from aicane_navigation.mapping import MultiFloorCorridorMap

# 처음부터 3층 고려
multi_map = MultiFloorCorridorMap()
```

**이유:**
- 🏢 다층 기본
- 🤖 AI 기본
- 🪜 계단 기본

---

## 📝 **정리**

### **Q: 기존 floor_plan.py는 안 쓰는 거야?**

### **A: 아니요! 계속 씁니다!** ✅

**사용 전략:**

1. **1층만 주행** → `FloorPlan` 또는 `UnifiedMapSystem(single_floor)`
2. **3층 + AI** → `MultiFloorCorridorMap` 또는 `UnifiedMapSystem(multi_floor)`
3. **모를 때** → `UnifiedMapSystem` (자동 선택)

**파일 역할:**
- `floor_plan.py` - 1층 최적화 ✅
- `multi_floor_map.py` - 3층 + AI ✅
- `unified_map.py` - 자동 선택 ✅

**모두 유지! 상황에 따라 선택!** 🎯

---

## 🎉 **결론**

### **기존 코드:**
- ✅ `floor_plan.py` 유지
- ✅ 1층 최적화 계속 사용

### **신규 코드:**
- ✅ `multi_floor_map.py` 추가 (3층 + AI)
- ✅ `unified_map.py` 추가 (통합)

### **권장:**
```python
# 가장 유연한 방법
from aicane_navigation.mapping import UnifiedMapSystem

map_sys = UnifiedMapSystem(mode='multi_floor', ai_enabled=True)
```

**→ 필요에 따라 자동으로 최적화!** 🚀
