# 🤖 AI 경로 JSON 추가 - 빠른 답변

## 🎯 **핵심 질문**

### **Q: AI 모델이 생성한 JSON 경로를 어디에 추가해야 하나요?**

### **A: maps/ 폴더에 넣으면 됩니다!** ✅

---

## 📁 **저장 위치**

```bash
C:/25L/aicane_navigation/maps/

예시:
maps/
├── my_ai_path.json      ← 여기!
├── path_101_to_107.json ← 여기!
└── ai_generated.json    ← 여기!
```

---

## 📄 **JSON 형식**

### **간단 형식** (추천!):
```json
{
  "waypoints": [
    {"x": 100, "y": 314},
    {"x": 200, "y": 314},
    {"x": 300, "y": 314}
  ]
}
```

### **설명 포함**:
```json
{
  "description": "AI가 생성한 경로",
  "scale": "1픽셀 = 3.8cm",
  "waypoints": [
    {"x": 100, "y": 314, "description": "시작"},
    {"x": 200, "y": 314, "description": "중간"},
    {"x": 300, "y": 314, "description": "끝"}
  ]
}
```

---

## 🚀 **사용 방법**

### **1. JSON 파일 저장**
```bash
# maps/ 폴더에 저장
cp my_path.json maps/
```

### **2. 실행**
```bash
# 방법 1: navigate.py
python scripts/navigate.py \
  --mode ai_path \
  --path-file maps/my_path.json

# 방법 2: Mock 테스트
python scripts/navigate.py \
  --mode ai_path \
  --path-file maps/my_path.json \
  --mock
```

---

## ✅ **체크리스트**

- [ ] JSON 파일 생성 (waypoints 배열 포함)
- [ ] **maps/ 폴더에 저장**
- [ ] 파일명 .json 확장자
- [ ] Mock 모드로 테스트
- [ ] 실제 주행

---

## 📚 **상세 가이드**

👉 **[AI 팀 가이드 전체 보기](AI_TEAM_GUIDE.md)**

**내용:**
- ✅ JSON 형식 4가지
- ✅ 좌표 시스템 설명
- ✅ 테스트 방법
- ✅ 경로 시각화
- ✅ 문제 해결

**소요 시간:** 10분

---

## 🎉 **요약**

```
AI 모델 → JSON 생성 → maps/ 폴더 → navigate.py → 주행!
                         ↑
                    여기에 저장!
```

**핵심:** maps/ 폴더! ⭐⭐⭐
