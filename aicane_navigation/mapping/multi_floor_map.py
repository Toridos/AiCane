"""
3층 건물 복도 맵 (개선 버전)
AI 경로 통합 + 층 이동 + 경로 재계획
"""

from typing import Dict, List, Tuple, Optional
import json


class MultiFloorCorridorMap:
    """
    다층 건물 복도 맵
    
    - 3개 층 (1~3층)
    - 계단 위치
    - AI 경로 통합
    - 픽셀 좌표 관리
    """
    
    def __init__(self):
        # 층별 복도 정보
        self.floors = {}
        
        # 계단 위치 (층 이동 지점)
        self.stairs = []
        
        # 픽셀 → cm 변환
        self.pixel_to_cm = 3.8
        
        self._load_floor_data()
    
    def _load_floor_data(self):
        """
        층별 데이터 로드
        (실제로는 JSON 파일에서 로드)
        """
        # 1층 데이터 (업로드된 이미지 기준)
        self.floors[1] = {
            'corridors': {
                'main_horizontal': {
                    'type': 'horizontal',
                    'corners': [
                        (219.745, 219.821),  # 좌측 상단/하단
                        (2390.746, 2390.813),  # 우측 상단/하단
                    ],
                    'y_center': 219.783,  # (219.745 + 219.821) / 2
                    'width': 240,  # cm
                },
                'central_lobby': {
                    'type': 'open_space',
                    'corners': [
                        (1225.746, 1241.884),  # 좌측
                        (1463.762, 1463.521),  # 우측
                        (1317.892, 1241.884),  # 중앙
                    ],
                },
                'vertical_corridor': {
                    'type': 'vertical',
                    'corners': [
                        (1225.746, 1241.884),
                        (1225.746, 219.821),
                    ],
                },
            },
            'rooms': {
                '101호': {'x': 120, 'y': 41, 'door_direction': 'south'},
                '102호': {'x': 200, 'y': 41, 'door_direction': 'south'},
                '103호': {'x': 280, 'y': 41, 'door_direction': 'south'},
                # ... (나머지 방)
            },
        }
        
        # 2층, 3층 (골격 동일, 방 번호만 변경)
        for floor in [2, 3]:
            self.floors[floor] = {
                'corridors': self.floors[1]['corridors'].copy(),
                'rooms': self._generate_room_numbers(floor),
            }
        
        # 계단 위치
        self.stairs = [
            {
                'id': 'stair_west',
                'floors': [1, 2, 3],
                'position': (1317.892, 1241.884),  # 픽셀 좌표
                'type': 'up_down',
            },
        ]
    
    def _generate_room_numbers(self, floor: int) -> Dict:
        """층별 방 번호 생성 (골격 동일)"""
        base_rooms = self.floors[1]['rooms'].copy()
        new_rooms = {}
        
        for room_id, info in base_rooms.items():
            # 101호 → 201호, 301호
            old_number = int(room_id[:3])
            new_number = floor * 100 + (old_number % 100)
            new_id = f"{new_number}호"
            new_rooms[new_id] = info.copy()
        
        return new_rooms
    
    def load_from_json(self, filepath: str):
        """
        JSON 파일에서 맵 데이터 로드
        
        파일 형식:
        {
          "floors": {
            "1": {
              "corridors": {...},
              "rooms": {...}
            }
          },
          "stairs": [...]
        }
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.floors = data.get('floors', {})
        self.stairs = data.get('stairs', [])
    
    def parse_ai_path(self, ai_json: Dict) -> List[Dict]:
        """
        AI 경로 JSON 파싱
        
        Args:
            ai_json: AI 모델의 경로 JSON
        
        Returns:
            list: 실행 가능한 waypoint 리스트
        """
        path = ai_json.get('path', [])
        
        waypoints = []
        current_floor = None
        
        for i, point in enumerate(path):
            floor = point['floor']
            x_pixel = point['x']
            y_pixel = point['y']
            
            # 픽셀 → cm 변환
            x_cm = x_pixel * self.pixel_to_cm
            y_cm = y_pixel * self.pixel_to_cm
            
            waypoint = {
                'floor': floor,
                'x': x_cm,
                'y': y_cm,
                'type': 'normal',
            }
            
            # 층 변경 감지 (계단)
            if current_floor is not None and floor != current_floor:
                # 이전 waypoint를 계단 진입으로 표시
                if waypoints:
                    waypoints[-1]['type'] = 'stair_approach'
                
                waypoint['type'] = 'stair_exit'
                waypoint['from_floor'] = current_floor
                waypoint['to_floor'] = floor
            
            waypoints.append(waypoint)
            current_floor = floor
        
        return waypoints
    
    def get_corridor_at(self, floor: int, x: float, y: float) -> Optional[Dict]:
        """
        특정 위치의 복도 정보 반환
        
        Args:
            floor: 층 번호
            x, y: 위치 (cm)
        
        Returns:
            dict or None: 복도 정보
        """
        if floor not in self.floors:
            return None
        
        corridors = self.floors[floor]['corridors']
        
        for corridor_id, corridor_info in corridors.items():
            if self._is_in_corridor(x, y, corridor_info):
                return {
                    'id': corridor_id,
                    'floor': floor,
                    **corridor_info
                }
        
        return None
    
    def _is_in_corridor(self, x: float, y: float, corridor: Dict) -> bool:
        """위치가 복도 안에 있는지 확인"""
        corridor_type = corridor.get('type')
        
        if corridor_type == 'horizontal':
            # 수평 복도
            corners = corridor['corners']
            x_min = min(c[0] for c in corners) * self.pixel_to_cm
            x_max = max(c[0] for c in corners) * self.pixel_to_cm
            y_center = corridor['y_center'] * self.pixel_to_cm
            width = corridor['width']
            
            return (x_min <= x <= x_max and 
                    y_center - width/2 <= y <= y_center + width/2)
        
        elif corridor_type == 'vertical':
            # 수직 복도
            corners = corridor['corners']
            x_center = corners[0][0] * self.pixel_to_cm
            y_min = min(c[1] for c in corners) * self.pixel_to_cm
            y_max = max(c[1] for c in corners) * self.pixel_to_cm
            width = 240  # cm
            
            return (x_center - width/2 <= x <= x_center + width/2 and
                    y_min <= y <= y_max)
        
        return False
    
    def find_nearest_stair(self, floor: int, x: float, y: float) -> Optional[Dict]:
        """가장 가까운 계단 찾기"""
        nearest = None
        min_dist = float('inf')
        
        for stair in self.stairs:
            if floor not in stair['floors']:
                continue
            
            sx = stair['position'][0] * self.pixel_to_cm
            sy = stair['position'][1] * self.pixel_to_cm
            
            dist = ((x - sx)**2 + (y - sy)**2) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                nearest = {
                    **stair,
                    'distance': dist,
                    'x': sx,
                    'y': sy,
                }
        
        return nearest
    
    def replan_path_avoiding_obstacle(self, 
                                     current_floor: int,
                                     current_pos: Tuple[float, float],
                                     goal_pos: Tuple[float, float],
                                     obstacle_pos: Tuple[float, float],
                                     obstacle_radius: float = 100.0) -> List[Dict]:
        """
        장애물 회피 경로 재계획
        
        Args:
            current_floor: 현재 층
            current_pos: 현재 위치 (x, y) cm
            goal_pos: 목표 위치 (x, y) cm
            obstacle_pos: 장애물 위치 (x, y) cm
            obstacle_radius: 장애물 반경 cm
        
        Returns:
            list: 새로운 waypoint 리스트
        """
        # 간단한 회피: 장애물을 우회하는 중간점 추가
        cx, cy = current_pos
        gx, gy = goal_pos
        ox, oy = obstacle_pos
        
        # 장애물 중심에서 수직 방향으로 우회점 생성
        dx = gx - cx
        dy = gy - cy
        
        # 좌우 우회 시도
        avoid_distance = obstacle_radius + 50  # 안전 마진
        
        # 좌측 우회
        avoid_left = (ox - avoid_distance, oy)
        
        # 우측 우회
        avoid_right = (ox + avoid_distance, oy)
        
        # 복도 안에 있는 우회점 선택
        corridor = self.get_corridor_at(current_floor, cx, cy)
        
        if corridor:
            if self._is_in_corridor(*avoid_left, corridor):
                avoid_point = avoid_left
            elif self._is_in_corridor(*avoid_right, corridor):
                avoid_point = avoid_right
            else:
                # 복도 밖이면 후진 후 우회
                avoid_point = (cx, cy - 100)
        else:
            avoid_point = avoid_left
        
        # 새 경로 생성
        new_path = [
            {'floor': current_floor, 'x': cx, 'y': cy, 'type': 'start'},
            {'floor': current_floor, 'x': avoid_point[0], 'y': avoid_point[1], 'type': 'avoid'},
            {'floor': current_floor, 'x': gx, 'y': gy, 'type': 'goal'},
        ]
        
        return new_path
    
    def export_to_json(self, filepath: str):
        """맵 데이터를 JSON 파일로 저장"""
        data = {
            'floors': self.floors,
            'stairs': self.stairs,
            'pixel_to_cm': self.pixel_to_cm,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# 사용 예제
if __name__ == '__main__':
    # 맵 생성
    corridor_map = MultiFloorCorridorMap()
    
    # AI 경로 파싱
    ai_path_json = {
        "success": True,
        "start": 101,
        "goal": 307,
        "path": [
            {"floor": 1, "x": 120, "y": 41},
            {"floor": 1, "x": 120, "y": 42},
            {"floor": 2, "x": 150, "y": 80},
            {"floor": 3, "x": 300, "y": 180},
        ]
    }
    
    waypoints = corridor_map.parse_ai_path(ai_path_json)
    
    print("AI 경로 파싱 결과:")
    for i, wp in enumerate(waypoints):
        print(f"  {i+1}. 층={wp['floor']}, 위치=({wp['x']:.1f}, {wp['y']:.1f}), 타입={wp['type']}")
    
    # 장애물 회피
    print("\n장애물 회피 경로:")
    new_path = corridor_map.replan_path_avoiding_obstacle(
        current_floor=1,
        current_pos=(456.0, 835.0),
        goal_pos=(912.0, 835.0),
        obstacle_pos=(684.0, 835.0),
    )
    
    for i, wp in enumerate(new_path):
        print(f"  {i+1}. ({wp['x']:.1f}, {wp['y']:.1f}) - {wp['type']}")
