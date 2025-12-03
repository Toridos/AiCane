"""
방 정보 통합 관리
FloorPlan과 MultiFloorMap의 방 정보를 통합 접근
"""

from typing import Dict, Optional, Tuple, List


class RoomManager:
    """
    호실(방) 정보 통합 관리
    
    - FloorPlan과 MultiFloorMap에서 방 정보 추출
    - 통일된 인터페이스 제공
    - 층별, 타입별 필터링
    """
    
    def __init__(self, map_system=None):
        """
        Args:
            map_system: FloorPlan, MultiFloorMap, 또는 UnifiedMapSystem
        """
        self.map_system = map_system
        self.rooms = {}
        
        if map_system:
            self._load_from_map(map_system)
        else:
            # 기본 데이터
            self._load_default_rooms()
    
    def _load_from_map(self, map_system):
        """맵 시스템에서 방 정보 로드"""
        # FloorPlan
        if hasattr(map_system, 'rooms') and isinstance(map_system.rooms, dict):
            self.rooms = self._convert_floorplan_rooms(map_system.rooms)
        
        # MultiFloorMap
        elif hasattr(map_system, 'floors'):
            self.rooms = self._convert_multifloor_rooms(map_system.floors)
        
        # UnifiedMapSystem
        elif hasattr(map_system, 'map'):
            self._load_from_map(map_system.map)
    
    def _convert_floorplan_rooms(self, rooms_dict: Dict) -> Dict:
        """FloorPlan 형식 → 표준 형식"""
        converted = {}
        
        for room_name, info in rooms_dict.items():
            converted[room_name] = {
                'floor': 1,  # FloorPlan은 1층만
                'door_x': info.get('door_x', 0),
                'door_y': info.get('door_y', 0),
                'door_direction': info.get('door_direction', 'unknown'),
                'type': info.get('type', 'office'),
            }
        
        return converted
    
    def _convert_multifloor_rooms(self, floors_dict: Dict) -> Dict:
        """MultiFloorMap 형식 → 표준 형식"""
        converted = {}
        
        for floor, floor_data in floors_dict.items():
            rooms = floor_data.get('rooms', {})
            
            for room_name, info in rooms.items():
                # 픽셀 → cm 변환 (3.8 곱하기)
                converted[room_name] = {
                    'floor': int(floor),
                    'door_x': info.get('x', 0) * 3.8,
                    'door_y': info.get('y', 0) * 3.8,
                    'door_direction': info.get('door_direction', 'unknown'),
                    'type': 'office',
                }
        
        return converted
    
    def _load_default_rooms(self):
        """기본 방 정보 (테스트용)"""
        self.rooms = {
            "101호": {
                "floor": 1,
                "door_x": 456.0,
                "door_y": 155.8,
                "door_direction": "south",
                "type": "office"
            },
            "102호": {
                "floor": 1,
                "door_x": 760.0,
                "door_y": 155.8,
                "door_direction": "south",
                "type": "office"
            },
            "107호": {
                "floor": 1,
                "door_x": 456.0,
                "door_y": 835.0,
                "door_direction": "north",
                "type": "office"
            },
        }
    
    def get_room(self, room_name: str) -> Optional[Dict]:
        """
        방 정보 반환
        
        Args:
            room_name: 방 이름 (예: '101호')
        
        Returns:
            dict or None: 방 정보
        """
        return self.rooms.get(room_name)
    
    def get_door_position(self, room_name: str) -> Optional[Tuple[float, float]]:
        """
        방 출입문 위치 반환
        
        Args:
            room_name: 방 이름
        
        Returns:
            tuple or None: (x, y) 위치 (cm)
        """
        room = self.get_room(room_name)
        
        if room is None:
            return None
        
        x = room.get("door_x")
        y = room.get("door_y")
        
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return (float(x), float(y))
        
        return None
    
    def get_door_waypoint(self, room_name: str) -> Optional[Tuple[float, float, float]]:
        """
        방 출입문 waypoint 반환 (x, y, theta)
        
        Args:
            room_name: 방 이름
        
        Returns:
            tuple or None: (x, y, theta)
        """
        room = self.get_room(room_name)
        
        if room is None:
            return None
        
        x = room.get("door_x", 0)
        y = room.get("door_y", 0)
        direction = room.get("door_direction", "south")
        
        # 문 방향에 따른 각도
        direction_angles = {
            'north': 0.0,      # 북쪽 (0도)
            'south': 180.0,    # 남쪽 (180도)
            'east': 270.0,     # 동쪽 (270도)
            'west': 90.0,      # 서쪽 (90도)
        }
        
        theta = direction_angles.get(direction, 0.0)
        
        return (x, y, theta)
    
    def get_rooms_on_floor(self, floor: int) -> Dict[str, Dict]:
        """
        특정 층의 방 목록 반환
        
        Args:
            floor: 층 번호
        
        Returns:
            dict: 방 이름 → 방 정보
        """
        return {
            name: info
            for name, info in self.rooms.items()
            if info.get("floor") == floor
        }
    
    def list_all_rooms(self) -> List[str]:
        """
        모든 방 이름 리스트
        
        Returns:
            list: 방 이름들
        """
        return list(self.rooms.keys())
    
    def list_rooms_by_floor(self, floor: int) -> List[str]:
        """
        특정 층의 방 이름 리스트
        
        Args:
            floor: 층 번호
        
        Returns:
            list: 방 이름들
        """
        return [
            name for name, info in self.rooms.items()
            if info.get("floor") == floor
        ]
    
    def search_rooms(self, 
                    floor: Optional[int] = None,
                    room_type: Optional[str] = None) -> List[str]:
        """
        조건으로 방 검색
        
        Args:
            floor: 층 (None이면 전체)
            room_type: 방 타입 (None이면 전체)
        
        Returns:
            list: 조건에 맞는 방 이름들
        """
        results = []
        
        for name, info in self.rooms.items():
            # 층 필터
            if floor is not None and info.get("floor") != floor:
                continue
            
            # 타입 필터
            if room_type is not None and info.get("type") != room_type:
                continue
            
            results.append(name)
        
        return results
    
    def get_nearest_room(self, x: float, y: float, floor: int) -> Optional[str]:
        """
        가장 가까운 방 찾기
        
        Args:
            x, y: 현재 위치 (cm)
            floor: 현재 층
        
        Returns:
            str or None: 가장 가까운 방 이름
        """
        floor_rooms = self.get_rooms_on_floor(floor)
        
        if not floor_rooms:
            return None
        
        nearest = None
        min_dist = float('inf')
        
        for name, info in floor_rooms.items():
            dx = info['door_x'] - x
            dy = info['door_y'] - y
            dist = (dx*dx + dy*dy) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                nearest = name
        
        return nearest
    
    def add_room(self, room_name: str, room_info: Dict):
        """방 추가"""
        self.rooms[room_name] = room_info
    
    def update_room(self, room_name: str, updates: Dict):
        """방 정보 업데이트"""
        if room_name in self.rooms:
            self.rooms[room_name].update(updates)
    
    def remove_room(self, room_name: str):
        """방 제거"""
        if room_name in self.rooms:
            del self.rooms[room_name]


# 사용 예제
if __name__ == '__main__':
    print("=== RoomManager 테스트 ===\n")
    
    # 1. 기본 생성
    room_mgr = RoomManager()
    
    print("1️⃣ 전체 방 목록:")
    print(f"   {room_mgr.list_all_rooms()}\n")
    
    # 2. 방 정보 조회
    print("2️⃣ 101호 정보:")
    room = room_mgr.get_room('101호')
    print(f"   {room}\n")
    
    # 3. 출입문 위치
    print("3️⃣ 출입문 위치:")
    pos = room_mgr.get_door_position('101호')
    print(f"   101호: {pos}\n")
    
    # 4. Waypoint
    print("4️⃣ Waypoint (x, y, theta):")
    waypoint = room_mgr.get_door_waypoint('101호')
    print(f"   101호: {waypoint}\n")
    
    # 5. 층별 방
    print("5️⃣ 1층 방 목록:")
    floor1_rooms = room_mgr.list_rooms_by_floor(1)
    print(f"   {floor1_rooms}\n")
    
    # 6. 가장 가까운 방
    print("6️⃣ 가장 가까운 방:")
    nearest = room_mgr.get_nearest_room(x=500, y=200, floor=1)
    print(f"   위치 (500, 200)에서: {nearest}\n")
    
    # 7. FloorPlan과 통합
    print("7️⃣ FloorPlan 통합:")
    try:
        from ..floor_plan import FloorPlan
        floor_plan = FloorPlan()
        room_mgr2 = RoomManager(floor_plan)
        print(f"   방 개수: {len(room_mgr2.list_all_rooms())}")
    except:
        print("   FloorPlan import 실패 (정상)")
    
    print("\n✅ 테스트 완료")
