import math, time

class Odom:
    def __init__(self, kv=1.0, kw=1.0):
        self.x = 0.0; self.y = 0.0; self.yaw = 0.0  # rad
        self._t = time.time()
        self.kv = kv; self.kw = kw

    def reset(self):
        self.x = 0.0; self.y = 0.0; self.yaw = 0.0
        self._t = time.time()

    def step(self, v_cmd_mps: float, w_cmd_dps: float):
        t = time.time()
        dt = t - self._t
        self._t = t
        v = v_cmd_mps * self.kv
        w = math.radians(w_cmd_dps) * self.kw
        self.yaw += w * dt
        self.x   += v * math.cos(self.yaw) * dt
        self.y   += v * math.sin(self.yaw) * dt
        return dt

    def pose(self):
        return (self.x, self.y, self.yaw)
