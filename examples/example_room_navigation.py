#!/usr/bin/env python3
"""
사용 예제 1: 방 간 이동
"""

from aicane_navigation import NavigationSystem

# 시스템 초기화 (Mock 모드)
nav = NavigationSystem(mock=True)

# 101호 → 107호 이동
nav.navigate_rooms('101호', '107호')

# 종료
nav.shutdown()
