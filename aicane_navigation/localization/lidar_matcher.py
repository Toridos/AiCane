# LIDAR 맵 매칭 (비상용)

# localization/lidar_matcher.py
class LidarMapMatcher:
    """LiDAR 맵 매칭 (비상용)"""
    
    def __init__(self, floor_map)
    
    def estimate_position(self, 
                         lidar_scan: dict, 
                         rough_pose: tuple) -> tuple
    # Returns: (x, y, theta, confidence)
    
    def estimate_position_full_search(self, lidar_scan: dict) -> tuple
    # 전체 맵 탐색 (초기 위치 모를 때)

