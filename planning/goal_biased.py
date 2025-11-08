import math

class GoalBiasedPlanner:
    def __init__(self, w_goal=1.2, w_clear=0.6, w_turn=0.25,
                 fov_deg=180, step_deg=5, min_clear=0.6,
                 steer_limit_deg=30, base_speed=0.35):
        self.w_goal = w_goal
        self.w_clear = w_clear
        self.w_turn = w_turn
        self.fov = math.radians(fov_deg)
        self.step = math.radians(step_deg)
        self.min_clear = min_clear
        self.steer_limit = steer_limit_deg
        self.prev_theta = 0.0
        self.base_v = base_speed

    def goal_heading(self, pose, goal_xy):
        x,y,yaw = pose; gx,gy = goal_xy
        return math.atan2(gy - y, gx - x)

    def pick(self, pose, lidar_clear_fn, goal_xy):
        goal_hd = self.goal_heading(pose, goal_xy)
        best = None; best_score = -1e9
        # candidates within FOV
        a0 = -self.fov/2; a1 = self.fov/2; step = self.step
        d = a0
        while d <= a1 + 1e-6:
            hd = wrap(pose[2] + d)
            clr = lidar_clear_fn(hd)
            if clr >= self.min_clear:
                dtheta = ang_diff(hd, goal_hd)
                score = (self.w_goal*math.cos(dtheta)
                         + self.w_clear*min(clr, 2.0)
                         - self.w_turn*abs(d))
                score -= 0.1 * abs(d - self.prev_theta)
                if score > best_score:
                    best_score = score; best = d
            d += step
        if best is None:
            return None, None
        self.prev_theta = best
        steer_deg = max(-self.steer_limit, min(self.steer_limit, math.degrees(best)))
        v = self.base_v * max(0.4, 1.0 - abs(steer_deg)/self.steer_limit)
        return v, steer_deg

def ang_diff(a,b):
    d = (a-b+math.pi)%(2*math.pi)-math.pi
    return d

def wrap(a):
    return (a+math.pi)%(2*math.pi)-math.pi
