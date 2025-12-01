#!/usr/bin/env python3
"""
사용 예제 2: AI 픽셀 경로 추종
"""

from aicane_navigation import NavigationSystem

# 시스템 초기화
nav = NavigationSystem(mock=True)

# AI가 제공한 픽셀 경로
ai_path_pixels = [
    (100, 314),   # 시작
    (200, 314),   # 복도 진입
    (400, 314),   # 복도 주행
    (600, 314),   # 로비 방향
    (700, 314),   # 로비 통과
    (900, 314),   # 복도 재진입
    (1100, 314),  # 목표 근처
    (1150, 377),  # 목표 도착
]

# 시작 위치 설정 (101호)
nav.set_start_position_from_room('101호')

# AI 경로 추종
nav.navigate_ai_path(ai_path_pixels)

# 종료
nav.shutdown()
