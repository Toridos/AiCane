# mecanum_kinematics.py

"""
Webots용 메카넘 휠 속도 변환 유틸
- vx: 전진(앞 +, 뒤 -) [m/s]
- vy: 좌/우(좌 +, 우 -) [m/s]
- omega: 반시계 방향 yaw 각속도 [rad/s]
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class MecanumConfig:
    wheel_radius: float = 0.033  # 바퀴 반지름 [m] (예시)
    lx: float = 0.09             # 로봇 중심~앞/뒤 바퀴까지 거리 [m]
    ly: float = 0.09             # 로봇 중심~좌/우 바퀴까지 거리 [m]

    @property
    def k(self) -> float:
        # 회전 항에 쓰이는 (lx + ly)
        return self.lx + self.ly


def body_to_wheel_speeds(
    vx: float,
    vy: float,
    omega: float,
    cfg: MecanumConfig,
) -> Tuple[float, float, float, float]:
    """
    메카넘 휠 역기구학 (body twist → wheel angular vel)
    반환: (w_fl, w_fr, w_rl, w_rr) [rad/s]
    """
    R = cfg.wheel_radius
    k = cfg.k

    # 표준 메카넘 행렬 (front-left, front-right, rear-left, rear-right)
    w_fl = (1 / R) * (vx - vy - k * omega)
    w_fr = (1 / R) * (vx + vy + k * omega)
    w_rl = (1 / R) * (vx + vy - k * omega)
    w_rr = (1 / R) * (vx - vy + k * omega)

    return w_fl, w_fr, w_rl, w_rr