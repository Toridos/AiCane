"""
간단한 미끄러짐 보정기
실시간 재계획 방식에 비례 보정 추가
"""

import math


class SimpleSlipCorrector:
    """
    간단한 미끄러짐 보정
    
    특징:
    - 거리 오차에 비례해서 속도 조정
    - 각도 오차에 비례해서 회전 속도 조정
    - 구현 간단, 즉시 적용 가능
    """
    
    def __init__(self, position_gain=0.2, angle_gain=0.3):
        """
        Args:
            position_gain (float): 위치 보정 이득 (0~1)
            angle_gain (float): 각도 보정 이득 (0~1)
        """
        self.position_gain = position_gain
        self.angle_gain = angle_gain
        
        # 이전 오차 (변화율 계산용)
        self.last_position_error = None
        self.last_angle_error = None
    
    def correct_forward(self, target_distance, measured_distance, base_speed):
        """
        전진 명령 보정
        
        Args:
            target_distance (float): 목표 거리 (cm)
            measured_distance (float): 측정 거리 (cm)
            base_speed (int): 기본 속도 레벨 (6~15)
        
        Returns:
            int: 보정된 속도 레벨
        """
        # 오차 계산
        error = target_distance - measured_distance
        
        # 보정량 계산
        correction = 1.0 + (self.position_gain * error / 100.0)
        
        # 속도 조정
        corrected_speed = int(base_speed * correction)
        
        # 범위 제한
        corrected_speed = max(6, min(15, corrected_speed))
        
        # 이전 오차 저장
        self.last_position_error = error
        
        return corrected_speed
    
    def correct_rotation(self, target_angle, measured_angle, base_speed):
        """
        회전 명령 보정
        
        Args:
            target_angle (float): 목표 각도 (rad)
            measured_angle (float): 측정 각도 (rad)
            base_speed (int): 기본 속도 레벨 (6~15)
        
        Returns:
            int: 보정된 속도 레벨
        """
        # 각도 오차 (정규화)
        error = self._normalize_angle(target_angle - measured_angle)
        
        # 보정량 계산
        correction = 1.0 + (self.angle_gain * abs(error))
        
        # 속도 조정
        corrected_speed = int(base_speed * correction)
        
        # 범위 제한
        corrected_speed = max(6, min(15, corrected_speed))
        
        # 이전 오차 저장
        self.last_angle_error = error
        
        return corrected_speed
    
    def correct_command(self, current_pose, target_pose, direction, base_speed):
        """
        통합 명령 보정
        
        Args:
            current_pose (tuple): (x, y, theta) 현재 위치
            target_pose (tuple): (x, y, theta) 목표 위치
            direction (str): 명령 방향
            base_speed (int): 기본 속도 레벨
        
        Returns:
            int: 보정된 속도 레벨
        """
        cx, cy, ctheta = current_pose
        tx, ty, ttheta = target_pose
        
        if direction in ['FORWARD', 'BACKWARD']:
            # 거리 기반 보정
            target_dist = math.sqrt((tx - cx)**2 + (ty - cy)**2)
            
            # 현재 거리 = 0 (아직 이동 안 함)
            # 오차 = 남은 거리
            corrected = self.correct_forward(target_dist, 0, base_speed)
            
            return corrected
        
        elif direction in ['ROTATE_L', 'ROTATE_R']:
            # 각도 기반 보정
            corrected = self.correct_rotation(ttheta, ctheta, base_speed)
            
            return corrected
        
        else:
            # 횡이동은 그대로
            return base_speed
    
    @staticmethod
    def _normalize_angle(angle):
        """각도 정규화 (-π ~ π)"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


class AdaptiveSlipCompensator:
    """
    학습 기반 미끄러짐 보정
    
    특징:
    - 이동 이력 기록
    - 평균 미끄러짐 계산
    - 점진적 개선
    """
    
    def __init__(self, history_size=20):
        """
        Args:
            history_size (int): 보관할 이력 개수
        """
        self.history_size = history_size
        
        # 방향별 미끄러짐 이력
        self.slip_history = {
            'forward': [],
            'backward': [],
            'left': [],
            'right': [],
            'rotate_l': [],
            'rotate_r': []
        }
    
    def record_motion(self, direction, speed_level, expected_delta, actual_delta):
        """
        이동 기록
        
        Args:
            direction (str): 명령 방향
            speed_level (int): 속도 레벨
            expected_delta (tuple): 예상 이동 (dx, dy, dtheta)
            actual_delta (tuple): 실제 이동 (dx, dy, dtheta)
        """
        # 오차 계산
        slip = {
            'speed_level': speed_level,
            'error_x': actual_delta[0] - expected_delta[0],
            'error_y': actual_delta[1] - expected_delta[1],
            'error_theta': actual_delta[2] - expected_delta[2],
            'slip_ratio': self._calculate_slip_ratio(expected_delta, actual_delta)
        }
        
        # 방향 정규화
        dir_key = direction.lower()
        
        # 이력 추가
        self.slip_history[dir_key].append(slip)
        
        # 오래된 이력 제거
        if len(self.slip_history[dir_key]) > self.history_size:
            self.slip_history[dir_key].pop(0)
    
    def get_compensation_factor(self, direction, speed_level):
        """
        보정 인자 계산
        
        Args:
            direction (str): 명령 방향
            speed_level (int): 속도 레벨
        
        Returns:
            float: 보정 인자 (1.0 = 보정 없음)
        """
        dir_key = direction.lower()
        history = self.slip_history[dir_key]
        
        if len(history) < 3:
            # 데이터 부족 → 보정 없음
            return 1.0
        
        # 평균 미끄러짐 비율
        avg_slip = sum(h['slip_ratio'] for h in history) / len(history)
        
        # 보정 인자 (미끄러짐 보상)
        # 예: 10% 미끄러짐 → 1.11배 속도
        compensation = 1.0 / (1.0 - avg_slip) if avg_slip < 0.5 else 1.0
        
        # 안전 범위
        compensation = max(0.8, min(1.3, compensation))
        
        return compensation
    
    def get_angle_offset(self, direction):
        """
        각도 오프셋 계산 (방향 틀어짐 보정)
        
        Args:
            direction (str): 명령 방향
        
        Returns:
            float: 각도 오프셋 (rad)
        """
        dir_key = direction.lower()
        history = self.slip_history[dir_key]
        
        if len(history) < 3:
            return 0.0
        
        # 평균 각도 오차
        avg_error = sum(h['error_theta'] for h in history) / len(history)
        
        return avg_error
    
    def print_stats(self):
        """학습 통계 출력"""
        print("\n📊 미끄러짐 학습 통계:")
        
        for direction, history in self.slip_history.items():
            if len(history) == 0:
                continue
            
            avg_slip = sum(h['slip_ratio'] for h in history) / len(history)
            compensation = self.get_compensation_factor(direction, 10)
            
            print(f"  {direction:10s}: 미끄러짐 {avg_slip*100:.1f}%, "
                  f"보정 인자 {compensation:.3f}x ({len(history)}개 이력)")
    
    @staticmethod
    def _calculate_slip_ratio(expected, actual):
        """
        미끄러짐 비율 계산
        
        Args:
            expected (tuple): 예상 (dx, dy, dtheta)
            actual (tuple): 실제 (dx, dy, dtheta)
        
        Returns:
            float: 미끄러짐 비율 (0~1)
        """
        expected_dist = math.sqrt(expected[0]**2 + expected[1]**2)
        actual_dist = math.sqrt(actual[0]**2 + actual[1]**2)
        
        if expected_dist < 0.1:
            return 0.0
        
        # 미끄러짐 = (예상 - 실제) / 예상
        slip = (expected_dist - actual_dist) / expected_dist
        
        # 음수 방지 (실제가 예상보다 크면 0)
        slip = max(0.0, slip)
        
        return slip


if __name__ == '__main__':
    print("=== SimpleSlipCorrector 테스트 ===\n")
    
    corrector = SimpleSlipCorrector(position_gain=0.2, angle_gain=0.3)
    
    # 전진 보정 테스트
    print("1️⃣ 전진 보정:")
    print(f"   목표: 100cm, 측정: 0cm, 기본 속도: 10")
    corrected = corrector.correct_forward(100, 0, 10)
    print(f"   → 보정 속도: {corrected}")
    
    # 회전 보정 테스트
    print("\n2️⃣ 회전 보정:")
    print(f"   목표: 90도, 측정: 0도, 기본 속도: 8")
    corrected = corrector.correct_rotation(math.radians(90), 0, 8)
    print(f"   → 보정 속도: {corrected}")
    
    print("\n" + "="*50)
    print("=== AdaptiveSlipCompensator 테스트 ===\n")
    
    compensator = AdaptiveSlipCompensator(history_size=10)
    
    # 미끄러짐 이력 시뮬레이션
    print("3️⃣ 미끄러짐 학습:")
    
    for i in range(5):
        # 예상: 10cm 전진
        expected = (10, 0, 0)
        
        # 실제: 8cm 전진 (20% 미끄러짐)
        actual = (8, 0, 0)
        
        compensator.record_motion('forward', 10, expected, actual)
        print(f"   이동 {i+1}: 예상 10cm, 실제 8cm")
    
    # 보정 인자
    factor = compensator.get_compensation_factor('forward', 10)
    print(f"\n   → 보정 인자: {factor:.3f}x")
    print(f"   → 다음 명령: 속도 레벨 {int(10 * factor)}")
    
    # 통계
    compensator.print_stats()
    
    print("\n✅ 테스트 완료")
