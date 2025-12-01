# 복도 정보

# mapping/corridor_map.py
class CorridorMap:
    """복도 정보 관리"""
    
    corridors: list = [
        {
            'id': 'main_horizontal',
            'type': 'horizontal',
            'x_range': (0, 11840),
            'y_center': 1312.5,
            'width': 240,
            ...
        },
        ...
    ]
    
    def get_expected_ultrasonic_distances(self, x: float, y: float, theta: float) -> dict
    # 특정 위치에서 예상되는 초음파 거리
