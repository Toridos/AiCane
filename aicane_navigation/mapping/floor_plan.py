"""
1층 평면도 맵 정보
복도, 방 위치, 장애물 정보 관리
"""

import json
import math
import os


class FloorPlan:
    """
    1층 평면도 전체 정보
    
    - 건물 크기: 118.4m × 26.25m
    - 축척: 1픽셀 = 3.8cm
    - 복도 폭: 240cm
    """
    
    def __init__(self):
        # 건물 크기 (cm)
        self.building_width = 11840  # 118.4m
        self.building_height = 2625  # 26.25m
        
        # 복도 정보
        self.corridors = self._init_corridors()
        
        # 방 정보
        self.rooms = self._init_rooms()
    
    def _init_corridors(self):
        """복도 정의"""
        return [
            {
                'id': 'main_horizontal',
                'name': '중앙 메인 복도',
                'type': 'horizontal',
                
                # X 범위 (가로 전체)
                'x_min': 0,
                'x_max': 11840,
                
                # Y 범위 (복도 폭 240cm)
                'y_center': 1312.5,
                'y_min': 1192.5,   # 북쪽 벽
                'y_max': 1432.5,   # 남쪽 벽
                'width': 240,
                
                # 초음파용 벽 정보
                'north_wall_y': 1192.5,
                'south_wall_y': 1432.5,
            },
            {
                'id': 'vertical_west',
                'name': '서쪽 세로 복도',
                'type': 'vertical',
                
                # Y 범위
                'y_min': 0,
                'y_max': 1312.5,
                
                # X 범위 (복도 폭)
                'x_center': 380,
                'x_min': 260,
                'x_max': 500,
                'width': 240,
                
                # 초음파용 벽 정보
                'west_wall_x': 260,
                'east_wall_x': 500,
            },
            {
                'id': 'central_lobby',
                'name': '중앙 로비',
                'type': 'open_space',
                
                # 넓은 공간
                'x_min': 5700,
                'x_max': 7200,
                'y_min': 1000,
                'y_max': 1625,
                
                'use_ultrasonic': False,  # 초음파 사용 불가
            },
        ]
    
    def _init_rooms(self):
        """방 위치 정의 (문 좌표)"""
        rooms = {}
        
        # 북쪽 방들 (101~106호)
        north_rooms = [
            ('101호', 380),
            ('102호', 1140),
            ('103호', 1900),
            ('104호', 7600),
            ('105호', 9120),
            ('106호', 10640),
        ]
        
        for name, x in north_rooms:
            rooms[name] = {
                'door_x': x,
                'door_y': 1192.5,
                'direction': 'south',  # 문이 남쪽(복도)을 향함
            }
        
        # 남쪽 방들 (107~118호)
        south_rooms = [
            ('117호', 380),
            ('116호', 760),
            ('115호', 1520),
            ('114호', 2280),
            ('113호', 3040),
            ('118호', 3800),
            ('112호', 7600),
            ('111호', 8360),
            ('110호', 9120),
            ('109호', 9880),
            ('108호', 10640),
            ('107호', 11460),
        ]
        
        for name, x in south_rooms:
            rooms[name] = {
                'door_x': x,
                'door_y': 1432.5,
                'direction': 'north',  # 문이 북쪽(복도)을 향함
            }
        
        return rooms
    
    def get_corridor_at(self, x, y):
        """
        좌표에서 복도 정보 반환
        
        Args:
            x (float): X 좌표 (cm)
            y (float): Y 좌표 (cm)
        
        Returns:
            dict or None: 복도 정보
        """
        for corridor in self.corridors:
            if corridor['type'] == 'horizontal':
                if (corridor['x_min'] <= x <= corridor['x_max'] and
                    corridor['y_min'] <= y <= corridor['y_max']):
                    return corridor
            
            elif corridor['type'] == 'vertical':
                if (corridor['y_min'] <= y <= corridor['y_max'] and
                    corridor['x_min'] <= x <= corridor['x_max']):
                    return corridor
            
            elif corridor['type'] == 'open_space':
                if (corridor['x_min'] <= x <= corridor['x_max'] and
                    corridor['y_min'] <= y <= corridor['y_max']):
                    return corridor
        
        return None
    
    def is_in_corridor(self, x, y):
        """
        복도 안에 있는지 확인
        
        Args:
            x (float): X 좌표 (cm)
            y (float): Y 좌표 (cm)
        
        Returns:
            bool: 복도 안이면 True
        """
        corridor = self.get_corridor_at(x, y)
        if corridor is None:
            return False
        
        # 로비는 복도로 치지 않음 (초음파 작동 안 함)
        if corridor['type'] == 'open_space':
            return False
        
        return True
    
    def is_open_space(self, x, y):
        """
        넓은 공간(로비)인지 확인
        
        Args:
            x (float): X 좌표 (cm)
            y (float): Y 좌표 (cm)
        
        Returns:
            bool: 로비면 True
        """
        corridor = self.get_corridor_at(x, y)
        return corridor is not None and corridor['type'] == 'open_space'
    
    def get_room_door_position(self, room_name):
        """
        방 문 위치
        
        Args:
            room_name (str): 방 이름 (예: '101호')
        
        Returns:
            tuple: (x, y) 문 좌표 (cm)
        
        Raises:
            ValueError: 방을 찾을 수 없음
        """
        if room_name not in self.rooms:
            raise ValueError(f"방 '{room_name}'을 찾을 수 없습니다")
        
        room = self.rooms[room_name]
        return (room['door_x'], room['door_y'])
    
    def get_room_waypoint(self, room_name):
        """
        방 문 앞 대기 위치 (로봇이 갈 좌표)
        
        Args:
            room_name (str): 방 이름
        
        Returns:
            tuple: (x, y, theta) 대기 위치 및 방향
        
        Example:
            >>> floor_plan = FloorPlan()
            >>> x, y, theta = floor_plan.get_room_waypoint('101호')
            >>> print(f"101호 문 앞: ({x}, {y}), 방향: {math.degrees(theta)}도")
        """
        if room_name not in self.rooms:
            raise ValueError(f"방 '{room_name}'을 찾을 수 없습니다")
        
        room = self.rooms[room_name]
        door_x = room['door_x']
        door_y = room['door_y']
        
        # 문에서 50cm 떨어진 대기 위치
        if room['direction'] == 'south':
            # 북쪽 방 → 문 앞(남쪽, 복도 쪽)에서 대기
            wait_x = door_x
            wait_y = door_y + 50  # 복도 안쪽
            theta = math.radians(0)  # 북쪽 향함
        else:
            # 남쪽 방 → 문 앞(북쪽, 복도 쪽)에서 대기
            wait_x = door_x
            wait_y = door_y - 50
            theta = math.radians(180)  # 남쪽 향함
        
        return (wait_x, wait_y, theta)
    
    def generate_simple_path(self, from_room, to_room, waypoint_gap=50):
        """
        방 간 간단한 경로 생성 (복도 따라가기)
        
        Args:
            from_room (str): 출발 방
            to_room (str): 도착 방
            waypoint_gap (float): 웨이포인트 간격 (cm)
        
        Returns:
            list: [(x, y), ...] 경로 (cm 단위)
        """
        # 시작/끝 위치
        start_x, start_y, _ = self.get_room_waypoint(from_room)
        end_x, end_y, _ = self.get_room_waypoint(to_room)
        
        waypoints = [(start_x, start_y)]
        
        # 메인 복도를 따라가는 간단한 경로
        corridor = self.corridors[0]  # 중앙 메인 복도
        corridor_y = corridor['y_center']
        
        # 1. 복도로 진입
        waypoints.append((start_x, corridor_y))
        
        # 2. 복도를 따라 이동 (중간 포인트 추가)
        current_x = start_x
        target_x = end_x
        
        step = waypoint_gap if target_x > current_x else -waypoint_gap
        
        while abs(current_x - target_x) > waypoint_gap:
            current_x += step
            waypoints.append((current_x, corridor_y))
        
        # 3. 목표 방으로
        waypoints.append((end_x, corridor_y))
        waypoints.append((end_x, end_y))
        
        return waypoints
    
    def load_from_json(self, filename):
        """JSON 파일에서 맵 로드"""
        if not os.path.exists(filename):
            print(f"⚠️ 맵 파일 없음: {filename}")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'corridors' in data:
                self.corridors = data['corridors']
            if 'rooms' in data:
                self.rooms = data['rooms']
            
            print(f"✅ 맵 로드 완료: {filename}")
        except Exception as e:
            print(f"❌ 맵 로드 실패: {e}")
    
    def save_to_json(self, filename):
        """맵을 JSON 파일로 저장"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            data = {
                'building_size': {
                    'width_cm': self.building_width,
                    'height_cm': self.building_height,
                },
                'corridors': self.corridors,
                'rooms': self.rooms,
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 맵 저장 완료: {filename}")
        except Exception as e:
            print(f"❌ 맵 저장 실패: {e}")


if __name__ == '__main__':
    # 테스트
    print("=== FloorPlan 테스트 ===\n")
    
    floor_plan = FloorPlan()
    
    # 1. 복도 체크
    print("1️⃣ 복도 체크:")
    test_points = [
        (380, 1312, "복도 중앙"),
        (5700, 1312, "복도 (로비 근처)"),
        (6500, 1312, "로비"),
        (100, 100, "복도 밖"),
    ]
    
    for x, y, name in test_points:
        in_corridor = floor_plan.is_in_corridor(x, y)
        is_open = floor_plan.is_open_space(x, y)
        print(f"   {name} ({x}, {y}): 복도={in_corridor}, 로비={is_open}")
    
    # 2. 방 위치
    print("\n2️⃣ 방 위치:")
    for room_name in ['101호', '107호', '118호']:
        x, y, theta = floor_plan.get_room_waypoint(room_name)
        print(f"   {room_name}: ({x:.0f}, {y:.0f}), 방향={math.degrees(theta):.0f}°")
    
    # 3. 경로 생성
    print("\n3️⃣ 경로 생성 (101호 → 107호):")
    path = floor_plan.generate_simple_path('101호', '107호', waypoint_gap=100)
    print(f"   총 {len(path)}개 웨이포인트")
    for i, (x, y) in enumerate(path):
        print(f"     {i}: ({x:.0f}, {y:.0f})")
    
    print("\n✅ 테스트 완료")
