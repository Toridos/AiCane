"""
초음파 기반 위치 보정
복도에서 X 좌표를 초음파로 정확하게 보정
"""

from ..core.moving_average_filter import MovingAverageFilter


class UltrasonicLocalizer:
    """
    초음파 센서 기반 위치 보정
    
    복도에서:
    - 좌/우 초음파로 X 좌표 정확히 보정
    - 벽까지 거리 측정 → 절대 X 좌표 계산
    - 신뢰도 함께 반환
    """
    
    def __init__(self, robot, floor_map):
        """
        Args:
            robot: RobokitDriver 인스턴스
            floor_map: FloorPlan 인스턴스
        """
        self.robot = robot
        self.map = floor_map
        
        # 필터 (노이즈 제거)
        self.left_filter = MovingAverageFilter(window=5)
        self.right_filter = MovingAverageFilter(window=5)
    
    def get_corrected_pose(self, odom_x, odom_y, odom_theta):
        """
        초음파로 위치 보정
        
        Args:
            odom_x (float): 오도메트리 X (cm)
            odom_y (float): 오도메트리 Y (cm)
            odom_theta (float): 오도메트리 방향 (rad)
        
        Returns:
            tuple: (corrected_x, corrected_y, theta, confidence)
                  confidence: 0~1 (신뢰도)
        """
        # 현재 위치의 복도 정보
        corridor = self.map.get_corridor_at(odom_x, odom_y)
        
        if corridor is None:
            # 복도 아님
            return (odom_x, odom_y, odom_theta, 0.0)
        
        if corridor.get('type') == 'open_space':
            # 로비 (초음파 사용 불가)
            return (odom_x, odom_y, odom_theta, 0.3)
        
        # 초음파 읽기
        distances = self.robot.get_ultrasonic()
        d_left = self.left_filter.update(distances.get('left'))
        d_right = self.right_filter.update(distances.get('right'))
        
        if d_left is None or d_right is None:
            return (odom_x, odom_y, odom_theta, 0.0)
        
        # 범위 체크
        if d_left > 300 or d_right > 300:
            # 벽이 너무 멀음
            return (odom_x, odom_y, odom_theta, 0.2)
        
        # 복도 타입별 보정
        if corridor['type'] == 'horizontal':
            # 가로 복도
            return self._correct_horizontal_corridor(
                odom_x, odom_y, odom_theta,
                d_left, d_right, corridor
            )
        
        elif corridor['type'] == 'vertical':
            # 세로 복도
            return self._correct_vertical_corridor(
                odom_x, odom_y, odom_theta,
                d_left, d_right, corridor
            )
        
        return (odom_x, odom_y, odom_theta, 0.0)
    
    def _correct_horizontal_corridor(self, odom_x, odom_y, odom_theta,
                                     d_left, d_right, corridor):
        """
        가로 복도 보정
        
        가로 복도에서는 초음파가 좌우 벽(방 벽)을 보므로
        Y 좌표를 복도 중앙으로 부드럽게 보정
        """
        corridor_width = corridor['width']
        measured_width = d_left + d_right
        
        width_error = abs(measured_width - corridor_width)
        
        if width_error < 30:  # 30cm 이내 오차
            # 복도 중앙에 있음
            confidence = 1.0 - (width_error / 30)
            
            # Y 좌표를 복도 중앙으로 부드럽게 보정
            target_y = corridor['y_center']
            corrected_y = odom_y * 0.7 + target_y * 0.3
            
            return (odom_x, corrected_y, odom_theta, confidence)
        else:
            # 복도 벗어남?
            return (odom_x, odom_y, odom_theta, 0.2)
    
    def _correct_vertical_corridor(self, odom_x, odom_y, odom_theta,
                                   d_left, d_right, corridor):
        """
        세로 복도 보정
        
        세로 복도에서는 초음파가 좌우 벽을 정확히 보므로
        X 좌표를 정밀하게 보정 가능!
        """
        west_wall = corridor['west_wall_x']
        east_wall = corridor['east_wall_x']
        
        # X 좌표 계산 (양쪽 벽 기준)
        x_from_west = west_wall + d_left
        x_from_east = east_wall - d_right
        
        # 평균
        corrected_x = (x_from_west + x_from_east) / 2
        
        # 신뢰도 계산
        corridor_width = corridor['width']
        measured_width = d_left + d_right
        width_error = abs(measured_width - corridor_width)
        
        confidence = max(0, 1.0 - width_error / 50)
        
        return (corrected_x, odom_y, odom_theta, confidence)
    
    def is_in_corridor(self, x, y):
        """복도 안에 있는지 확인"""
        return self.map.is_in_corridor(x, y)


if __name__ == '__main__':
    print("=== UltrasonicLocalizer 테스트 ===\n")
    
    from ..hardware.robokit_driver import RobokitDriver
    from ..mapping.floor_plan import FloorPlan
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    localizer = UltrasonicLocalizer(robot, floor_map)
    
    # 세로 복도에서 테스트
    print("1️⃣ 세로 복도 (380, 500):")
    x, y, theta, conf = localizer.get_corrected_pose(380, 500, 0)
    print(f"   보정 위치: ({x:.1f}, {y:.1f}), 신뢰도: {conf:.2f}")
    
    # 가로 복도에서 테스트
    print("\n2️⃣ 가로 복도 (1000, 1312):")
    x, y, theta, conf = localizer.get_corrected_pose(1000, 1312, 0)
    print(f"   보정 위치: ({x:.1f}, {y:.1f}), 신뢰도: {conf:.2f}")
    
    print("\n✅ 테스트 완료")
