# 간단한 경로 생성


# navigation/path_planner.py
class SimplePathPlanner:
    """간단한 경로 생성"""
    
    def __init__(self, floor_map)
    
    def plan_room_to_room(self, from_room: str, to_room: str) -> list
    # 방 간 경로 생성 (복도 따라가기)
    
    def interpolate_waypoints(self, waypoints: list, max_gap: float = 50) -> list
    # 웨이포인트 사이 보간