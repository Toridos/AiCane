import math, time
from planning.goal_biased import GoalBiasedPlanner
from planning.navigator import Navigator

class Mode:
    FOLLOW_GOAL = 'FOLLOW_GOAL'
    FOLLOW_MISSION = 'FOLLOW_MISSION'
    AVOID = 'AVOID'
    RECOVER = 'RECOVER'
    DONE = 'DONE'

class FSM:
    def __init__(self, mode, planner, controller, fusion, odom, goal_xy=None):
        self.mode = mode
        self.planner = planner
        self.controller = controller
        self.fusion = fusion
        self.odom = odom
        self.goal_xy = goal_xy
        self.last_cmd = (0.0, 0.0)

    def tick(self):
        pose = self.odom.pose()

        # Goal reached (mission case)
        if isinstance(self.planner, Navigator) and self.planner.is_goal(pose):
            self.mode = Mode.DONE
            self.controller.stop_all()
            return 0.0, 0.0, self.mode

        # Emergency / obstacle
        blocked = self.fusion.forward_blocked()

        if self.mode == Mode.FOLLOW_GOAL:
            if blocked:
                self.mode = Mode.AVOID
                return self.fusion.free_space_cmd(), self.mode  # unpacked below
            # planner pick
            v, steer = self.planner.pick(pose, self.fusion.lidar_clear_fn, self.goal_xy)
            if v is None:
                self.mode = Mode.AVOID
                v, steer = self.fusion.free_space_cmd()
            self.last_cmd = (v, steer)
            return v, steer, self.mode

        if self.mode == Mode.FOLLOW_MISSION:
            if blocked:
                self.mode = Mode.AVOID
                return self.fusion.free_space_cmd(), self.mode
            v, steer = self.planner.follow(pose)
            self.last_cmd = (v, steer)
            return v, steer, self.mode

        if self.mode == Mode.AVOID:
            if not blocked:
                self.mode = Mode.RECOVER
            v, steer = self.fusion.free_space_cmd(v_nom=0.25)
            self.last_cmd = (v, steer)
            return v, steer, self.mode

        if self.mode == Mode.RECOVER:
            # Same as normal follow; switch back when near path
            if isinstance(self.planner, Navigator):
                v, steer = self.planner.recover_to_path(pose)
                near, _ = self.planner.nearest_on_path((pose[0], pose[1]))
                if (near[0]-pose[0])**2 + (near[1]-pose[1])**2 < (0.20**2):
                    self.mode = Mode.FOLLOW_MISSION
            else:
                v, steer = self.last_cmd  # keep previous heading softly
                self.mode = Mode.FOLLOW_GOAL
            self.last_cmd = (v, steer)
            return v, steer, self.mode

        if self.mode == Mode.DONE:
            self.controller.stop_all()
            return 0.0, 0.0, self.mode
