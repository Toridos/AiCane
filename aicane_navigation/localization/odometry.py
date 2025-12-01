"""
명령 기반 오도메트리
속도 레벨과 시간으로부터 위치 추정
"""

import math
import time
from ..core.speed_profile import SpeedProfile


class SimpleOdometry:
    """
    명령 기반 오도메트리
    
    - 속도 레벨과 시간으로 이동 거리 계산
    - 미끄러짐 보정 없음 (초음파/LiDAR로 보정)
    - 짧은 거리에서는 비교적 정확
    """
    
    def __init__(self):
        # 현재 위치
        self.x = 0.0  # cm
        self.y = 0.0  # cm
        self.theta = 0.0  # rad
        
        # 마지막 업데이트 시간
        self.last_update = time.time()
    
    def reset(self, x, y, theta):
        """
        위치 초기화
        
        Args:
            x (float): X 좌표 (cm)
            y (float): Y 좌표 (cm)
            theta (float): 방향 (rad)
        """
        self.x = x
        self.y = y
        self.theta = theta
        self.last_update = time.time()
    
    def update_from_command(self, direction, speed_level, duration):
        """
        명령으로부터 위치 업데이트
        
        Args:
            direction (str): 'FORWARD', 'BACKWARD', 'LEFT', 'RIGHT',
                           'ROTATE_L', 'ROTATE_R'
            speed_level (int): 속도 레벨 (6~15)
            duration (float): 명령 지속 시간 (초)
        """
        if direction == 'STOP' or duration <= 0:
            return
        
        # 속도 가져오기
        if direction in ['FORWARD', 'BACKWARD']:
            speed = SpeedProfile.get_speed(speed_level, 'forward')  # m/s
            distance = speed * duration * 100  # cm
            
            if direction == 'FORWARD':
                self.x += distance * math.cos(self.theta)
                self.y += distance * math.sin(self.theta)
            else:  # BACKWARD
                self.x -= distance * math.cos(self.theta)
                self.y -= distance * math.sin(self.theta)
        
        elif direction in ['LEFT', 'RIGHT']:
            speed = SpeedProfile.get_speed(speed_level, 'lateral')  # m/s
            distance = speed * duration * 100  # cm
            
            if direction == 'LEFT':
                # 왼쪽 = theta + 90도 방향
                self.x += distance * math.cos(self.theta + math.pi/2)
                self.y += distance * math.sin(self.theta + math.pi/2)
            else:  # RIGHT
                # 오른쪽 = theta - 90도 방향
                self.x += distance * math.cos(self.theta - math.pi/2)
                self.y += distance * math.sin(self.theta - math.pi/2)
        
        elif direction in ['ROTATE_L', 'ROTATE_R']:
            angular_speed = SpeedProfile.get_speed(speed_level, 'rotate')  # rad/s
            angle_change = angular_speed * duration
            
            if direction == 'ROTATE_L':
                self.theta += angle_change
            else:  # ROTATE_R
                self.theta -= angle_change
            
            # 각도 정규화
            self._normalize_theta()
        
        self.last_update = time.time()
    
    def get_pose(self):
        """
        현재 위치 반환
        
        Returns:
            tuple: (x, y, theta) - cm, cm, rad
        """
        return (self.x, self.y, self.theta)
    
    def _normalize_theta(self):
        """각도를 -π ~ π 범위로 정규화"""
        while self.theta > math.pi:
            self.theta -= 2 * math.pi
        while self.theta < -math.pi:
            self.theta += 2 * math.pi


if __name__ == '__main__':
    print("=== SimpleOdometry 테스트 ===\n")
    
    odom = SimpleOdometry()
    odom.reset(0, 0, 0)
    
    print("초기 위치:", odom.get_pose())
    
    # 전진 1초
    print("\n1️⃣ FORWARD, 레벨 10, 1초")
    odom.update_from_command('FORWARD', 10, 1.0)
    x, y, theta = odom.get_pose()
    print(f"   위치: ({x:.1f}, {y:.1f}), 방향: {math.degrees(theta):.1f}°")
    
    # 좌회전 0.5초
    print("\n2️⃣ ROTATE_L, 레벨 8, 0.5초")
    odom.update_from_command('ROTATE_L', 8, 0.5)
    x, y, theta = odom.get_pose()
    print(f"   위치: ({x:.1f}, {y:.1f}), 방향: {math.degrees(theta):.1f}°")
    
    # 전진 1초
    print("\n3️⃣ FORWARD, 레벨 10, 1초")
    odom.update_from_command('FORWARD', 10, 1.0)
    x, y, theta = odom.get_pose()
    print(f"   위치: ({x:.1f}, {y:.1f}), 방향: {math.degrees(theta):.1f}°")
    
    print("\n✅ 테스트 완료")
