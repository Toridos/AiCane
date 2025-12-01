# 로깅

# utils/logger.py
class NavigationLogger:
    """주행 로그 기록"""
    
    def log_position(self, pose: tuple, tier: int, confidence: float)
    def log_obstacle(self, obstacle_info: dict)
    def log_command(self, direction: str, speed_level: int)
    def save_to_file(self, filename: str)
