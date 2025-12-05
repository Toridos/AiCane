"""
Mapping module
"""

from .floor_plan import FloorPlan
from .multi_floor_map import MultiFloorCorridorMap
from .unified_map import UnifiedMapSystem
from .room_manager import RoomManager

__all__ = [
    'FloorPlan',              # 기존 (1층 전용)
    'MultiFloorCorridorMap',  # 신규 (3층 + AI)
    'UnifiedMapSystem',       # 통합 (자동 선택)
    'RoomManager',            # 방 관리 (통합 API)
]
