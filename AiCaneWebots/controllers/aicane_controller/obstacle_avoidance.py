# obstacle_avoidance.py

"""
Webots 시뮬용 초음파 장애물 회피 로직

입력: 초음파 거리 (m)
출력: (vx, vy, omega) [m/s, m/s, rad/s]
 - vx > 0 : 전진
 - vy > 0 : 왼쪽으로 평행 이동
 - omega > 0 : 반시계 회전
"""

from dataclasses import dataclass
from enum import Enum, auto


class AvoidState(Enum):
    GO_STRAIGHT = auto()
    BACK_OFF = auto()
    SIDESTEP = auto()
    RECOVER = auto()


@dataclass
class AvoidConfig:
    front_threshold: float = 0.35   # 정면 최소 거리 [m]
    side_threshold: float = 0.25    # 좌/우 최소 거리 [m]
    back_duration: float = 0.5      # 후진 시간 [s]
    side_duration: float = 0.7      # 측면 이동 시간 [s]
    recover_duration: float = 0.7   # 경로 복귀 시간 [s]
    vx_forward: float = 0.12        # 기본 전진 속도
    vx_back: float = -0.10          # 후진 속도
    vy_side: float = 0.10           # 측면 이동 속도
    omega_turn: float = 0.6         # 회전 속도 (rad/s)


@dataclass
class AvoidContext:
    state: AvoidState = AvoidState.GO_STRAIGHT
    state_start: float = 0.0
    sidestep_dir: int = 0  # +1: left, -1: right


class ObstacleAvoider:
    def __init__(self, cfg: AvoidConfig | None = None):
        self.cfg = cfg or AvoidConfig()
        self.ctx = AvoidContext()

    def _time_in_state(self, now: float) -> float:
        return now - self.ctx.state_start

    def _set_state(self, state: AvoidState, now: float):
        self.ctx.state = state
        self.ctx.state_start = now

    def step(
        self,
        dist_front: float,
        dist_left: float,
        dist_right: float,
        now: float,
    ):
        """
        한 타임스텝마다 호출.
        반환: (vx, vy, omega)
        """
        c = self.cfg
        s = self.ctx.state

        # 1) 기본 전진 상태
        if s == AvoidState.GO_STRAIGHT:
            # 정면 장애물?
            if dist_front < c.front_threshold:
                # 어느 쪽이 더 여유 있는지 보고 sidestep 방향 결정
                if dist_left > dist_right:
                    self.ctx.sidestep_dir = +1  # 왼쪽으로 피해가기
                else:
                    self.ctx.sidestep_dir = -1  # 오른쪽으로 피해가기
                self._set_state(AvoidState.BACK_OFF, now)
                return c.vx_back, 0.0, 0.0

            # 좌우가 너무 가까운 경우는 살짝 중앙으로 보정
            vy = 0.0
            if dist_left < c.side_threshold < dist_right:
                vy = -c.vy_side * 0.3   # 오른쪽으로 살짝
            elif dist_right < c.side_threshold < dist_left:
                vy = +c.vy_side * 0.3   # 왼쪽으로 살짝

            return c.vx_forward, vy, 0.0

        # 2) BACK_OFF (잠깐 후진)
        if s == AvoidState.BACK_OFF:
            if self._time_in_state(now) >= c.back_duration:
                self._set_state(AvoidState.SIDESTEP, now)
                dir_sign = self.ctx.sidestep_dir
                return 0.0, dir_sign * c.vy_side, 0.0
            return c.vx_back, 0.0, 0.0

        # 3) SIDESTEP (옆으로 이동)
        if s == AvoidState.SIDESTEP:
            if self._time_in_state(now) >= c.side_duration:
                self._set_state(AvoidState.RECOVER, now)
                # 회전하면서 원래 경로 쪽으로 복귀
                dir_sign = self.ctx.sidestep_dir
                return c.vx_forward * 0.5, 0.0, -dir_sign * c.omega_turn
            dir_sign = self.ctx.sidestep_dir
            return 0.0, dir_sign * c.vy_side, 0.0

        # 4) RECOVER (원래 경로로 복귀)
        if s == AvoidState.RECOVER:
            if self._time_in_state(now) >= c.recover_duration:
                self._set_state(AvoidState.GO_STRAIGHT, now)
                return c.vx_forward, 0.0, 0.0
            dir_sign = self.ctx.sidestep_dir
            return c.vx_forward * 0.5, 0.0, -dir_sign * c.omega_turn * 0.7

        # 방어적 default
        self._set_state(AvoidState.GO_STRAIGHT, now)
        return c.vx_forward, 0.0, 0.0