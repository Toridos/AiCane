# AiCane Navigation System

실내 자율주행 로봇 시스템 (1층 평면도 기반)

## 특징

- **3-Tier 위치 추정**: 초음파(90%) + 오도메트리(9%) + LiDAR(1%)
- **장애물 회피**: 초음파 + LiDAR 통합 감지
- **미끄러짐 구분**: 장애물 출현 vs 미끄러짐 자동 판별
- **실시간 경로 재계획**: Waypoint 기반 추종

## 하드웨어

- Raspberry Pi 4B
- RobokitRS (메카넘휠)
- RPLidar X4 Pro
- 초음파 센서 3개 (정면/좌/우)

## 설치

```bash
cd C:/25L/aicane_navigation
pip install -e .
```

## 사용법

### 방 간 이동
```bash
python scripts/navigate.py --from 101호 --to 107호
```

### 캘리브레이션
```bash
python scripts/calibrate.py
```

### AI 경로 추종
```python
from aicane_navigation import NavigationSystem

nav = NavigationSystem()

# AI가 제공한 픽셀 경로
ai_path = [(100, 314), (200, 314), ...]

nav.navigate_ai_path(ai_path)
```

## 좌표 시스템

- **축척**: 1픽셀 = 3.8cm
- **원점**: 평면도 좌측 하단
- **방향**: X(동쪽), Y(북쪽), Theta(반시계방향)

## 구조

```
aicane_navigation/
├── core/           # 핵심 유틸리티
├── hardware/       # 하드웨어 인터페이스
├── localization/   # 위치 추정
├── mapping/        # 맵 관리
├── obstacle/       # 장애물 감지/회피
└── navigation/     # 경로 추종
```

## 라이선스

MIT
