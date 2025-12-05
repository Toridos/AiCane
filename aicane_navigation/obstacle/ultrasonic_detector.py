"""
초음파 기반 장애물 감지
정면/좌/우 초음파로 근접 장애물 감지
"""

from ..core.moving_average_filter import MovingAverageFilter


class UltrasonicObstacleDetector:
    """
    초음파 기반 장애물 감지
    
    - 정면/좌/우 3개 센서
    - 거리별 위험도: Critical(<25cm), Warning(<50cm), Safe(>50cm)
    - 급격한 거리 변화 감지 (장애물 출현)
    """
    
    def __init__(self, robot):
        """
        Args:
            robot: RobokitDriver 인스턴스
        """
        self.robot = robot
        
        # 안전 거리 임계값
        self.CRITICAL_DISTANCE = 25   # cm - 긴급 정지
        self.WARNING_DISTANCE = 50    # cm - 감속
        self.SAFE_DISTANCE = 100      # cm - 정상
        
        # 필터 (빠른 반응 위해 윈도우 작게)
        self.front_filter = MovingAverageFilter(window=3)
        self.left_filter = MovingAverageFilter(window=5)
        self.right_filter = MovingAverageFilter(window=5)
        
        # 이력 (급격한 변화 감지용)
        self.last_distances = {
            'front': [],
            'left': [],
            'right': [],
        }
        self.max_history = 10
    
    def check_obstacles(self):
        """
        장애물 체크
        
        Returns:
            dict: {
                'front': {'distance': cm, 'status': str, 'obstacle_detected': bool},
                'left': {...},
                'right': {...},
                'action': 'continue' | 'slow_down' | 'stop'
            }
        """
        # 센서 읽기
        raw = self.robot.get_ultrasonic()
        
        # 필터링
        d_front = self.front_filter.update(raw.get('front'))
        d_left = self.left_filter.update(raw.get('left'))
        d_right = self.right_filter.update(raw.get('right'))
        
        # 이력 저장
        self._update_history('front', d_front)
        self._update_history('left', d_left)
        self._update_history('right', d_right)
        
        # 각 방향 상태 판단
        result = {
            'front': self._check_direction(d_front, 'front'),
            'left': self._check_direction(d_left, 'left'),
            'right': self._check_direction(d_right, 'right'),
        }
        
        # 종합 판단
        if result['front']['status'] == 'critical':
            result['action'] = 'stop'
        elif result['front']['status'] == 'warning':
            result['action'] = 'slow_down'
        else:
            result['action'] = 'continue'
        
        return result
    
    def _check_direction(self, distance, direction):
        """
        방향별 상태 체크
        
        Returns:
            dict: {'distance', 'status', 'obstacle_detected'}
        """
        if distance is None or distance > 200:
            return {
                'distance': None,
                'status': 'safe',
                'obstacle_detected': False
            }
        
        # 상태 판단
        if distance < self.CRITICAL_DISTANCE:
            status = 'critical'
        elif distance < self.WARNING_DISTANCE:
            status = 'warning'
        else:
            status = 'safe'
        
        # 장애물 감지 여부
        obstacle = distance < self.WARNING_DISTANCE
        
        return {
            'distance': distance,
            'status': status,
            'obstacle_detected': obstacle
        }
    
    def _update_history(self, direction, distance):
        """이력 업데이트"""
        if distance is not None and distance > 0:
            self.last_distances[direction].append(distance)
            if len(self.last_distances[direction]) > self.max_history:
                self.last_distances[direction].pop(0)
    
    def detect_sudden_change(self, direction='front'):
        """
        급격한 거리 변화 감지 (장애물 출현 vs 미끄러짐 구분)
        
        Args:
            direction (str): 'front', 'left', 'right'
        
        Returns:
            dict: {
                'sudden_change': bool,
                'change_amount': cm,
                'likely_obstacle': bool,
                'getting_closer': bool
            }
        """
        history = self.last_distances[direction]
        
        if len(history) < 6:
            return {
                'sudden_change': False,
                'change_amount': 0,
                'likely_obstacle': False,
                'getting_closer': False
            }
        
        # 최근 3개 평균
        recent_avg = sum(history[-3:]) / 3
        
        # 이전 3개 평균
        prev_avg = sum(history[-6:-3]) / 3
        
        # 변화량
        change = abs(recent_avg - prev_avg)
        
        # 급격한 변화? (50cm 이상)
        sudden = change > 50
        
        # 장애물 가능성 (갑자기 가까워짐)
        getting_closer = recent_avg < prev_avg
        likely_obstacle = sudden and getting_closer
        
        return {
            'sudden_change': sudden,
            'change_amount': change,
            'likely_obstacle': likely_obstacle,
            'getting_closer': getting_closer
        }


if __name__ == '__main__':
    print("=== UltrasonicObstacleDetector 테스트 ===\n")
    
    from ..hardware.robokit_driver import RobokitDriver
    import time
    
    robot = RobokitDriver(mock=True)
    detector = UltrasonicObstacleDetector(robot)
    
    print("🚦 장애물 감지 시뮬레이션:\n")
    
    for i in range(5):
        result = detector.check_obstacles()
        
        action_icon = {
            'continue': '✅',
            'slow_down': '⚠️',
            'stop': '🛑'
        }
        
        front = result['front']
        print(f"{action_icon[result['action']]} 스텝 {i+1}: "
              f"정면 {front['distance']:.1f}cm ({front['status']}), "
              f"액션: {result['action']}")
        
        time.sleep(0.2)
    
    print("\n✅ 테스트 완료")
