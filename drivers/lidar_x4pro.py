# YDLIDAR X4-Pro driver (stub). Replace with actual SDK integration.
import math, time, random

class LidarX4Pro:
    def __init__(self, port='/dev/ttyUSB1'):
        self.port = port
        print(f"[LidarX4Pro] Initialized (stub) on {port}")

    def get_scan(self):
        # Return list of (angle_rad, distance_m). Stub: sparse fake free space.
        data = []
        for deg in range(-90, 91, 5):
            ang = math.radians(deg)
            # fake wall at 0.5~2.0m, with random openings
            base = 1.2 + 0.6*math.sin(ang*2)
            noise = random.uniform(-0.1, 0.1)
            data.append((ang, max(0.2, base + noise)))
        return data
