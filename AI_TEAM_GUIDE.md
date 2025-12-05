# 🤖 AI 모델 담당자 가이드 - JSON 경로 추가

## 👋 환영합니다!

이 문서는 **AI 경로 생성 담당** 팀원을 위한 가이드입니다.

---

## 🎯 **핵심 질문: JSON 파일을 어디에 추가?**

### **답변:** ⭐⭐⭐
```bash
maps/ 폴더에 JSON 파일을 넣으면 됩니다!

예시:
C:/25L/aicane_navigation/maps/my_ai_path.json
```

---

## 📋 **전체 흐름**

```
1. AI 모델이 경로 생성
   ↓
2. JSON 파일로 저장
   ↓
3. maps/ 폴더에 복사  ← 여기!
   ↓
4. navigate.py로 실행
   ↓
5. 로봇 주행!
```

---

## 📄 **JSON 파일 형식**

### **형식 1: 기본 형식** (추천!) ⭐⭐⭐

```json
{
  "description": "AI가 생성한 경로",
  "waypoints": [
    {"x": 100, "y": 314},
    {"x": 200, "y": 314},
    {"x": 300, "y": 314}
  ]
}
```

**특징:**
- ✅ 가장 간단!
- ✅ 필수 정보만
- ✅ 추천!

---

### **형식 2: 설명 포함** (상세 버전) ⭐⭐

```json
{
  "description": "101호 → 107호 경로",
  "scale": "1픽셀 = 3.8cm",
  "waypoints": [
    {"x": 100, "y": 314, "description": "101호 출발"},
    {"x": 200, "y": 314, "description": "복도 진입"},
    {"x": 400, "y": 314, "description": "복도 주행"},
    {"x": 600, "y": 314, "description": "로비 방향"},
    {"x": 800, "y": 314, "description": "로비 통과"},
    {"x": 1000, "y": 314, "description": "복도 재진입"},
    {"x": 1200, "y": 314, "description": "107호 근처"},
    {"x": 1300, "y": 377, "description": "107호 문 앞"}
  ]
}
```

**특징:**
- ✅ 설명 포함
- ✅ 디버깅 편리
- ✅ 문서화에 좋음

---

### **형식 3: 리스트만** (간단 버전) ⭐

```json
[
  {"x": 100, "y": 314},
  {"x": 200, "y": 314},
  {"x": 300, "y": 314}
]
```

**특징:**
- ✅ 최소 형식
- ✅ AI 출력 그대로
- ⚠️ 설명 없음

---

### **형식 4: Python 리스트** (선택)

```python
# path.py
ai_path = [
    (100, 314),
    (200, 314),
    (300, 314)
]
```

**특징:**
- ✅ Python 직접 실행
- ⚠️ JSON 아님

---

## 📁 **파일 저장 위치**

### **1. maps/ 폴더** (추천!) ⭐⭐⭐

```bash
C:/25L/aicane_navigation/maps/

예시 파일명:
├── ai_path_101_to_107.json
├── path_20251203.json
├── emergency_path.json
└── test_path.json
```

**장점:**
- ✅ 기본 경로 폴더
- ✅ 예제 파일 있음
- ✅ 관리 편리

---

### **2. 임의 위치** (가능)

```bash
# 어디든 가능!
/home/ai_model/outputs/path.json
/tmp/ai_path.json
~/Downloads/path.json
```

**실행:**
```bash
python scripts/navigate.py \
  --mode ai_path \
  --path-file /home/ai_model/outputs/path.json
```

---

## 🚀 **사용 방법**

### **Step 1: JSON 파일 생성**

```python
# AI 모델 출력 (예시)
import json

waypoints = [
    {"x": 100, "y": 314},
    {"x": 200, "y": 314},
    {"x": 300, "y": 314},
    # ... AI가 생성한 경로
]

data = {
    "description": "AI generated path",
    "waypoints": waypoints
}

# JSON 파일로 저장
with open('maps/ai_path.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ JSON 파일 저장 완료!")
```

---

### **Step 2: 파일 확인**

```bash
# 파일 존재 확인
ls maps/ai_path.json

# 내용 확인
cat maps/ai_path.json
```

---

### **Step 3: 주행 실행**

```bash
# 방법 1: Python 직접 실행
python scripts/navigate.py \
  --mode ai_path \
  --path-file maps/ai_path.json

# 방법 2: Python 코드
python examples/example_ai_path.py
```

---

## 🧪 **테스트 방법**

### **1. Mock 모드 테스트** (안전!) ⭐⭐⭐

```bash
# Mock 모드로 먼저 테스트
python scripts/navigate.py \
  --mode ai_path \
  --path-file maps/ai_path.json \
  --mock

# 예상 출력:
# ✅ JSON 로드 성공!
# ✅ 웨이포인트: 8개
# ✅ 픽셀 → cm 변환 완료
# ✅ 주행 시작 (Mock 모드)
```

---

### **2. Python 코드 테스트**

```python
# test_my_path.py
from aicane_navigation import NavigationSystem
import json

# JSON 로드
with open('maps/ai_path.json', 'r') as f:
    data = json.load(f)

pixel_path = [(p['x'], p['y']) for p in data['waypoints']]

print(f"경로 포인트: {len(pixel_path)}개")
print(f"시작: {pixel_path[0]}")
print(f"끝: {pixel_path[-1]}")

# Mock 모드로 테스트
nav = NavigationSystem(config_dir='./config', mock=True)
nav.navigate_ai_path(pixel_path)
nav.shutdown()

print("✅ 테스트 완료!")
```

**실행:**
```bash
python test_my_path.py
```

---

### **3. 실제 주행** (준비되면)

```bash
# 실제 로봇으로 주행
python scripts/navigate.py \
  --mode ai_path \
  --path-file maps/ai_path.json
```

---

## 📐 **좌표 시스템**

### **픽셀 좌표:** (AI 모델 출력)
```
원점 (0, 0) = 맵 이미지 왼쪽 위
X축: 오른쪽으로 증가
Y축: 아래로 증가

축척: 1픽셀 = 3.8cm
```

### **cm 좌표:** (로봇 내부)
```
자동 변환됨!
픽셀 * 3.8 = cm
```

### **예시:**
```
픽셀 (100, 200)
  ↓ (자동 변환)
cm (380, 760)
```

---

## ✅ **체크리스트**

### **JSON 파일 준비:**
- [ ] AI 모델로 경로 생성
- [ ] JSON 형식 확인 (waypoints 배열)
- [ ] 파일 저장 (maps/ 폴더)
- [ ] 파일명 확인 (.json 확장자)

### **테스트:**
- [ ] Mock 모드 테스트
- [ ] 경로 시각화 (선택)
- [ ] 웨이포인트 개수 확인
- [ ] 좌표 범위 확인

### **실행:**
- [ ] navigate.py 실행
- [ ] 에러 없이 로드
- [ ] 주행 성공!

---

## 🎨 **경로 시각화** (선택)

### **방법 1: Python으로 그리기**

```python
import json
import matplotlib.pyplot as plt
from PIL import Image

# 맵 이미지
map_img = Image.open('maps/floor_plan.png')

# JSON 로드
with open('maps/ai_path.json', 'r') as f:
    data = json.load(f)

# 경로 추출
xs = [p['x'] for p in data['waypoints']]
ys = [p['y'] for p in data['waypoints']]

# 그리기
plt.figure(figsize=(12, 8))
plt.imshow(map_img)
plt.plot(xs, ys, 'r-o', linewidth=2, markersize=8)
plt.plot(xs[0], ys[0], 'go', markersize=12, label='Start')
plt.plot(xs[-1], ys[-1], 'ro', markersize=12, label='End')
plt.legend()
plt.title('AI Generated Path')
plt.show()

print(f"✅ 경로 시각화 완료! ({len(xs)}개 포인트)")
```

---

### **방법 2: 웹 도구 사용**

```bash
# 간단한 시각화 서버 실행 (선택)
# TODO: 나중에 추가 가능
```

---

## 🆘 **문제 해결**

### **문제 1: JSON 파일을 못 찾음**

```bash
# 에러:
FileNotFoundError: maps/ai_path.json

# 해결:
# 1. 파일 위치 확인
ls maps/ai_path.json

# 2. 절대 경로 사용
python scripts/navigate.py \
  --mode ai_path \
  --path-file /home/pi/aicane_navigation/maps/ai_path.json
```

---

### **문제 2: JSON 형식 오류**

```bash
# 에러:
JSONDecodeError: Expecting value

# 해결:
# JSON 검증 사이트: https://jsonlint.com/
# 또는:
python -m json.tool maps/ai_path.json
```

---

### **문제 3: waypoints 키가 없음**

```bash
# 에러:
KeyError: 'waypoints'

# 해결:
# 형식 확인:
{
  "waypoints": [    ← 이 키 필수!
    {"x": 100, "y": 200}
  ]
}

# 또는 리스트 형식:
[
  {"x": 100, "y": 200}
]
```

---

### **문제 4: 좌표 범위 이상**

```bash
# 에러:
경로가 맵 밖으로 나감

# 해결:
# 맵 크기 확인:
# - 가로: 0 ~ 1520 픽셀
# - 세로: 0 ~ 800 픽셀 (대략)

# 좌표 검증:
python -c "
import json
with open('maps/ai_path.json') as f:
    data = json.load(f)
    for p in data['waypoints']:
        assert 0 <= p['x'] <= 1520, f'X out: {p}'
        assert 0 <= p['y'] <= 800, f'Y out: {p}'
print('✅ 좌표 검증 통과!')
"
```

---

## 📚 **예제 파일**

### **maps/example_path.json** (참고!)

이미 있는 예제 파일:
```bash
cat maps/example_path.json
```

이걸 복사해서 수정하세요!

```bash
# 복사
cp maps/example_path.json maps/my_path.json

# 수정
nano maps/my_path.json
```

---

## 🔗 **추가 참고**

### **관련 문서:**
- [README.md](README.md) - 전체 시스템
- [MAPPING_GUIDE.md](MAPPING_GUIDE.md) - 좌표 시스템
- [examples/example_ai_path.py](examples/example_ai_path.py) - 코드 예제

### **관련 파일:**
- `scripts/navigate.py` - 주 실행 파일
- `maps/` - JSON 저장 위치
- `examples/example_ai_path.py` - 예제 코드

---

## 🎉 **완료!**

**AI 경로 JSON 추가 준비 완료!** ✅

**요약:**
1. ✅ AI 모델로 경로 생성
2. ✅ JSON 파일로 저장
3. ✅ **maps/ 폴더에 복사** ← 핵심!
4. ✅ navigate.py로 실행
5. ✅ 로봇 주행!

**빠른 테스트:**
```bash
# 1. JSON 저장
echo '{
  "waypoints": [
    {"x": 100, "y": 314},
    {"x": 200, "y": 314}
  ]
}' > maps/test_path.json

# 2. Mock 테스트
python scripts/navigate.py \
  --mode ai_path \
  --path-file maps/test_path.json \
  --mock

# 3. 성공! 🎉
```

**질문이 있으면 팀에게 문의하세요!** 💬
