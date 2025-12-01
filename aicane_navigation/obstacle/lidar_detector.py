# LIDAR 장애물 감지

# obstacle/lidar_detector.py
class LidarObstacleDetector:
    """LiDAR 장애물 감지"""
    
    def __init__(self, lidar)
    
    def detect_obstacles_in_sector(self, 
                                   scan: dict, 
                                   center_angle: float, 
                                   sector_width: float = 60) -> dict
    
    def find_clear_path(self, 
                       scan: dict, 
                       preferred_angle: float = 0,
                       search_range: float = 180) -> dict
    # 빈 공간 찾기 (회피 경로)
