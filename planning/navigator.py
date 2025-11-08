import math
from planning.path_utils import mission_to_polyline, nearest_point_on_polyline
from planning.pure_pursuit import target_point, control_cmd

class Navigator:
    def __init__(self, mission, lookahead=0.6, done_tol=0.15):
        self.mission = mission
        self.poly = mission_to_polyline(mission)
        self.idx_near = 0
        self.lookahead = lookahead
        self.done_tol = done_tol

    def is_goal(self, pose):
        gx,gy = self.poly[-1]
        x,y,_ = pose
        return math.hypot(gx-x, gy-y) < self.done_tol

    def follow(self, pose):
        _, idx = nearest_point_on_polyline((pose[0],pose[1]), self.poly)
        self.idx_near = idx
        tgt,_ = target_point(self.poly, self.idx_near, self.lookahead)
        return control_cmd(pose, tgt)

    def recover_to_path(self, pose):
        return self.follow(pose)

    def nearest_on_path(self, pt_xy):
        return nearest_point_on_polyline(pt_xy, self.poly)
