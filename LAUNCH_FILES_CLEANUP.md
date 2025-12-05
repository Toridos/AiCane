# Launch 파일 정리 가이드 🚀

## 🤔 **문제 상황**

### **현재 launch 폴더:**
```
launch/
├── navigation.launch.py      ← ⚠️ 골격만 (비어있음)
├── test.launch.py            ← ⚠️ 골격만 (비어있음)
├── start_navigation.sh       ✅ 작동함!
├── demo_full.sh              ✅ 작동함!
├── setup_check.sh            ✅ 작동함!
└── ...
```

---

## 💡 **판단: .launch.py 안 씀!**

### **이유 1: ROS 불필요** ⭐⭐⭐

**.launch.py = ROS2 전용 파일 형식**

```python
# ROS2 시스템에서만 사용
# from launch import LaunchDescription
# from launch_ros.actions import Node
# ...
```

**우리 시스템:**
- ❌ ROS 안 씀
- ✅ 단일 프로세스
- ✅ Python 직접 실행

---

### **이유 2: bash 스크립트로 충분** ⭐⭐⭐

**start_navigation.sh가 모든 기능 제공:**
```bash
# 작동하는 bash 스크립트!
./launch/start_navigation.sh --from 101호 --to 107호

기능:
✅ 블루투스 연결 확인
✅ LiDAR 포트 확인
✅ 로그 디렉토리 생성
✅ 주행 시작
✅ 에러 처리
✅ Mock 모드 지원
```

---

### **이유 3: 혼란 방지** ⭐⭐

**골격만 있으면 혼란:**
```
사용자: navigation.launch.py를 써야 하나?
      → 열어봄 → 비어있음 → 혼란!
```

---

## 📊 **비교표**

| 항목 | .launch.py (ROS2) | .sh (bash) |
|------|------------------|------------|
| **필요성** | ROS 필요 | ROS 불필요 |
| **복잡도** | 높음 | 낮음 |
| **작동** | ❌ (ROS 없음) | ✅ |
| **현재 상태** | 골격만 | 완성됨 |
| **사용 여부** | ❌ | ✅ |

---

## 🔧 **처리 방안**

### **Option 1: 삭제 (추천!)** ⭐⭐⭐

```bash
# 불필요한 파일 삭제
rm launch/navigation.launch.py
rm launch/test.launch.py

# 이유:
✅ ROS 안 씀
✅ bash 스크립트로 충분
✅ 혼란 방지
✅ 코드 정리
```

**추천 이유:**
- 가장 명확
- 혼란 없음
- 불필요한 파일 제거

---

### **Option 2: 이름 변경** ⭐⭐

```bash
# 참고용으로 보관
mv launch/navigation.launch.py launch/navigation.launch.py.unused
mv launch/test.launch.py launch/test.launch.py.unused

# 또는
mv launch/navigation.launch.py launch/.navigation.launch.py.backup
mv launch/test.launch.py launch/.test.launch.py.backup

# 이유:
✅ 나중에 ROS로 전환할 수도?
✅ 참고용 보관
⚠️ 하지만 혼란 가능
```

---

### **Option 3: 주석 추가** ⭐

```python
# launch/navigation.launch.py

"""
⚠️ DEPRECATED: 이 파일은 사용되지 않습니다.

이유:
- ROS2를 사용하지 않음
- bash 스크립트로 대체됨

대신 사용:
  ./launch/start_navigation.sh --from 101호 --to 107호

또는:
  python scripts/navigate.py --mode rooms --from 101호 --to 107호
"""

# 전체 시스템 런치 (ROS2 전용, 현재 미사용)
```

---

### **Option 4: 구현 (불필요!)** ❌

```python
# 완전히 구현
# → ROS2 설치 필요
# → 복잡도 증가
# → 불필요!
```

---

## ✅ **최종 권장사항**

### **Option 1 (삭제) 추천!** ⭐⭐⭐

**명령어:**
```bash
cd C:/25L/aicane_navigation/launch

# 삭제
rm navigation.launch.py
rm test.launch.py

# 또는 이름 변경 (보관하고 싶다면)
mv navigation.launch.py navigation.launch.py.unused
mv test.launch.py test.launch.py.unused
```

---

## 📝 **대체 사용법**

### **1. bash 스크립트 사용 (추천!)**
```bash
# 방 간 이동
./launch/start_navigation.sh --from 101호 --to 107호

# Mock 모드
./launch/start_navigation.sh --from 101호 --to 107호 --mock

# 데모
./launch/demo_full.sh

# 설정 확인
./launch/setup_check.sh
```

---

### **2. Python 직접 실행**
```bash
# 방 간 이동
python scripts/navigate.py --mode rooms --from 101호 --to 107호

# AI 경로
python scripts/navigate.py --mode ai_path --path maps/path.json

# Mock 모드
python scripts/navigate.py --mode rooms --from 101호 --to 107호 --mock
```

---

### **3. Python 코드에서 사용**
```python
from aicane_navigation import NavigationSystem

nav = NavigationSystem(config_dir='./config', mock=False)
nav.navigate_rooms('101호', '107호')
nav.shutdown()
```

---

## 🎯 **정리**

### **Q: .launch.py 파일 안 써?**
### **A: 안 씁니다! 삭제 권장!** ✅

**이유:**
1. ✅ **ROS 불필요** - 단일 프로세스 시스템
2. ✅ **bash로 충분** - start_navigation.sh 완성됨
3. ✅ **혼란 방지** - 골격만 있으면 혼란
4. ✅ **코드 정리** - 불필요한 파일 제거

**대체:**
```bash
# .launch.py 대신
./launch/start_navigation.sh --from 101호 --to 107호
```

**결과:**
```
launch/
├── start_navigation.sh       ✅ 주 실행 파일
├── demo_full.sh              ✅ 데모
├── setup_check.sh            ✅ 설정 확인
├── connect_bluetooth.sh      ✅ 블루투스
├── shutdown.sh               ✅ 종료
└── README.md                 ✅ 문서
```

**→ .launch.py 삭제, bash 스크립트 사용!** 🚀✨
