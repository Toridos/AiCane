"""
통합 맵 시스템
기존 FloorPlan + 신규 MultiFloorCorridorMap
"""

from .floor_plan import FloorPlan
from .multi_floor_map import MultiFloorCorridorMap


class UnifiedMapSystem:
    """
    통합 맵 시스템
    
    - 단층 모드: FloorPlan 사용 (초음파 최적화)
    - 다층 모드: MultiFloorCorridorMap 사용 (AI 경로)
    """
    
    def __init__(self, mode='single_floor', ai_enabled=False):
        """
        Args:
            mode: 'single_floor' (1층만) 또는 'multi_floor' (3층)
            ai_enabled: AI 경로 사용 여부
        """
        self.mode = mode
        self.ai_enabled = ai_enabled
        
        if mode == 'single_floor' and not ai_enabled:
            # 1층 전용 (초음파 최적화)
            self.map = FloorPlan()
            print("📍 단층 모드 (초음파 최적화)")
        
        else:
            # 다층 또는 AI 경로
            self.map = MultiFloorCorridorMap()
            print("🏢 다층 모드 (AI 경로 지원)")
    
    def get_corridor_at(self, floor, x, y):
        """
        현재 위치의 복도 정보
        
        Args:
            floor: 층 (단층 모드에서는 무시)
            x, y: 위치 (cm)
        """
        if self.mode == 'single_floor':
            # FloorPlan API
            return self.map.get_corridor_at(x, y)
        else:
            # MultiFloorCorridorMap API
            return self.map.get_corridor_at(floor, x, y)
    
    def parse_ai_path(self, ai_json):
        """AI 경로 파싱 (다층 모드만)"""
        if isinstance(self.map, MultiFloorCorridorMap):
            return self.map.parse_ai_path(ai_json)
        else:
            raise ValueError("AI 경로는 다층 모드에서만 사용 가능")
    
    def generate_simple_path(self, from_room, to_room):
        """간단한 경로 생성 (단층 모드)"""
        if isinstance(self.map, FloorPlan):
            return self.map.generate_simple_path(from_room, to_room)
        else:
            # 다층에서는 AI 경로 사용 권장
            print("⚠️ 다층 모드에서는 AI 경로를 사용하세요")
            return []
    
    def get_room_waypoint(self, room_name):
        """방 위치 반환"""
        if isinstance(self.map, FloorPlan):
            return self.map.get_room_waypoint(room_name)
        else:
            # 다층: 층 번호 추출
            floor = int(room_name[0])  # 101호 → 1층
            rooms = self.map.floors.get(floor, {}).get('rooms', {})
            room_info = rooms.get(room_name)
            
            if room_info:
                return (
                    room_info['x'] * self.map.pixel_to_cm,
                    room_info['y'] * self.map.pixel_to_cm,
                    0.0  # theta
                )
            return None


# 사용 예제
if __name__ == '__main__':
    print("=== 통합 맵 시스템 테스트 ===\n")
    
    # 1. 단층 모드 (1층만)
    print("1️⃣ 단층 모드 테스트")
    single_map = UnifiedMapSystem(mode='single_floor')
    
    # 복도 확인
    corridor = single_map.get_corridor_at(floor=1, x=500, y=1312)
    print(f"   복도: {corridor['name']}")
    
    # 간단한 경로
    path = single_map.generate_simple_path('101호', '107호')
    print(f"   경로: {len(path)}개 waypoint\n")
    
    # 2. 다층 모드 (3층 + AI)
    print("2️⃣ 다층 모드 테스트")
    multi_map = UnifiedMapSystem(mode='multi_floor', ai_enabled=True)
    
    # AI 경로 파싱
    ai_json = {
        "path": [
            {"floor": 1, "x": 120, "y": 41},
            {"floor": 2, "x": 150, "y": 80},
            {"floor": 3, "x": 300, "y": 180},
        ]
    }
    
    waypoints = multi_map.parse_ai_path(ai_json)
    print(f"   AI 경로: {len(waypoints)}개 waypoint")
    
    for i, wp in enumerate(waypoints):
        print(f"   {i+1}. 층={wp['floor']}, 타입={wp['type']}")
    
    print("\n✅ 테스트 완료")
