# RPLiadar X4 Pro 인터페이스

# hardware/lidar_interface.py
class RPLidarX4ProInterface:
    """RPLidar X4 Pro 인터페이스"""
    
    def __init__(self, port: str = '/dev/ttyUSB0')
    
    def start(self)
    def stop(self)
    
    def get_scan(self) -> dict
    # {
    #   'angles': [0, 1, 2, ..., 359],
    #   'distances': [120, 135, ...],  # cm
    #   'timestamp': float
    # }
    
    def close(self)