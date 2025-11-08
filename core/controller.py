import math, time

class Controller:
    def __init__(self, uno):
        self.uno = uno
        # Parameters for speed/steer conversion – tune if needed
        self.max_speed_mps = 0.5
        self.max_steer_deg = 30.0

    def send_speed_steer(self, v_mps: float, steer_deg: float):
        v = max(-self.max_speed_mps, min(self.max_speed_mps, v_mps))
        s = max(-self.max_steer_deg, min(self.max_steer_deg, steer_deg))
        self.uno.send_speed_steer(v, s)

    def stop_all(self):
        self.uno.send_speed_steer(0.0, 0.0)

    def deg_per_sec_from_steer(self, steer_deg: float) -> float:
        # Simple proportional mapping (approx)
        return 90.0 * (steer_deg / self.max_steer_deg)
