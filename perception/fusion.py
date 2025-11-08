import math

class Fusion:
    def __init__(self, lidar, perceiver, estop_front=0.35):
        self.lidar = lidar
        self.perceiver = perceiver
        self.estop_front = estop_front
        self._scan = []  # cache
        self._last_offset = 0

    def update_cache(self, frame):
        self._scan = self.lidar.get_scan()
        off,_ = self.perceiver.freespace_center_offset(frame)
        if off is not None:
            self._last_offset = off

    def forward_blocked(self, threshold=0.7):
        # Use LiDAR scan in [-30°,30°] to check min distance
        min_d = 999.0
        for ang, dist in self._scan:
            deg = math.degrees(ang)
            if -30 <= deg <= 30:
                if dist < min_d:
                    min_d = dist
        return min_d < threshold

    def emergency_stop(self):
        # Hard E-Stop closer than estop_front
        min_d = 999.0
        for ang, dist in self._scan:
            deg = math.degrees(ang)
            if -15 <= deg <= 15:
                if dist < min_d:
                    min_d = dist
        return min_d < self.estop_front

    def free_space_cmd(self, v_nom=0.25):
        # Simple avoidance using camera offset sign
        steer = 0.0
        if self._last_offset is not None:
            if abs(self._last_offset) < 5:
                steer = 0.0
            elif self._last_offset > 0:
                steer = 20.0  # turn right
            else:
                steer = -20.0 # turn left
        v = v_nom * max(0.5, 1.0 - abs(steer)/30.0)
        return v, steer

    def lidar_clear_fn(self, hd_abs):
        # Return min distance along absolute heading (stub from cached scan)
        # hd_abs in radians; find nearest bin in scan
        best = 0.0
        best_err = 1e9
        for ang, dist in self._scan:
            err = abs((ang - hd_abs + math.pi)%(2*math.pi)-math.pi)
            if err < best_err:
                best_err = err
                best = dist
        return best
