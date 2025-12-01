"""
Navigation System Configuration
"""

class HardwareConfig:
    """하드웨어 설정"""
    # 시리얼 포트
    ROBOKIT_PORT = '/dev/ttyUSB0'  # 라즈베리파이
    LIDAR_PORT = '/dev/ttyUSB1'
    
    # 초음파 센서 핀
    ULTRASONIC_FRONT = 2
    ULTRASONIC_LEFT = 3
    ULTRASONIC_RIGHT = 12
    
    # 모터 속도
    BASE_SPEED = 10
    ROTATE_SPEED = 8
    
    # ⚠️ test_mecanumwheels.py로 측정 후 수정!
    ACTUAL_SPEED_FORWARD = 0.095   # m/s
    ACTUAL_SPEED_LATERAL = 0.095
    ACTUAL_SPEED_ROTATE = 0.43     # rad/s


class NavigationConfig:
    """경로 계획 및 제어 설정"""
    GOAL_THRESHOLD = 0.15          # m
    ANGLE_TOLERANCE = 0.3          # rad
    KP_ANGULAR = 1.5
    KP_LATERAL = 0.8
    
    OBSTACLE_THRESHOLD = 0.25      # m
    WALL_FOLLOW_DISTANCE = 0.20
    WALL_TOLERANCE = 0.05
    
    CONTROL_HZ = 10
    SENSOR_HZ = 10


class PathConfig:
    """경로 파일 설정"""
    import os
    PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
    PATH_FILE = os.path.join(PACKAGE_DIR, 'path.json')
    
    DEFAULT_PATH = [
        {"x": 1.0, "y": 0.0},
        {"x": 2.0, "y": 0.0},
        {"x": 0.0, "y": 0.0}
    ]