"""
통합 장애물 회피 시스템
초음파 + 미끄러짐 구분 + 회피 전략
"""


class ObstacleAvoidanceSystem:
    """
    통합 장애물 감지 및 회피
    
    - 초음파로 근접 장애물 감지
    - 장애물 vs 미끄러짐 구분
    - 회피 방향 결정
    """
    
    def __init__(self, robot, floor_map, lidar=None):
        """
        Args:
            robot: RobokitDriver
            floor_map: FloorPlan
            lidar: LiDAR 인터페이스 (선택사항)
        """
        self.robot = robot
        self.map = floor_map
        self.lidar = lidar
        
        # 센서
        from .ultrasonic_detector import UltrasonicObstacleDetector
        from .slip_detector import ObstacleVsSlipDetector
        
        self.ultrasonic = UltrasonicObstacleDetector(robot)
        self.slip_detector = ObstacleVsSlipDetector(floor_map)
        
        # 상태
        self.avoidance_mode = False
        self.blocked_count = 0
    
    def check_and_respond(self, current_pose, target_pose):
        """
        장애물 체크 및 대응
        
        Args:
            current_pose (tuple): (x, y, theta) 현재 위치
            target_pose (tuple): (x, y) 목표 위치
        
        Returns:
            dict: {
                'safe_to_proceed': bool,
                'action': 'continue' | 'slow_down' | 'stop' | 'avoid',
                'avoid_direction': None | angle,
                'reason': str
            }
        """
        # ═══════════════════════════════════════
        # 1️⃣ 초음파 체크 (근접 장애물)
        # ═══════════════════════════════════════
        ultrasonic_result = self.ultrasonic.check_obstacles()
        
        # 긴급 상황?
        if ultrasonic_result['action'] == 'stop':
            self.blocked_count += 1
            
            # 장애물 vs 미끄러짐 판단
            corridor = self.map.get_corridor_at(*current_pose[:2])
            
            if corridor and corridor['type'] != 'open_space':
                # 복도 안 → 예상 거리 계산 가능
                expected_distances = self._get_expected_distances(
                    current_pose, corridor
                )
                
                current_distances = {
                    'left': ultrasonic_result['left']['distance'],
                    'right': ultrasonic_result['right']['distance']
                }
                
                # 분석
                analysis = self.slip_detector.analyze_ultrasonic_change(
                    current_distances,
                    expected_distances,
                    self.ultrasonic.last_distances,
                    current_pose
                )
                
                # 장애물이면 회피
                if analysis['action'] in ['avoid_left', 'avoid_right']:
                    return self._plan_avoidance(
                        current_pose,
                        target_pose,
                        analysis['action']
                    )
                
                elif analysis['action'] == 'stop':
                    # 양쪽 막힘
                    return {
                        'safe_to_proceed': False,
                        'action': 'stop',
                        'avoid_direction': None,
                        'reason': 'blocked_both_sides'
                    }
            
            # 일반 정지
            return {
                'safe_to_proceed': False,
                'action': 'stop',
                'avoid_direction': None,
                'reason': 'obstacle_too_close'
            }
        
        # ═══════════════════════════════════════
        # 2️⃣ 정상 진행
        # ═══════════════════════════════════════
        self.blocked_count = max(0, self.blocked_count - 1)
        
        action = ultrasonic_result['action']  # 'continue' or 'slow_down'
        
        return {
            'safe_to_proceed': True,
            'action': action,
            'avoid_direction': None,
            'reason': 'clear'
        }
    
    def _get_expected_distances(self, current_pose, corridor):
        """
        복도에서 예상되는 초음파 거리
        
        Args:
            current_pose (tuple): (x, y, theta)
            corridor (dict): 복도 정보
        
        Returns:
            dict: {'left': cm, 'right': cm}
        """
        x, y, theta = current_pose
        
        if corridor['type'] == 'horizontal':
            # 가로 복도
            north_wall = corridor['north_wall_y']
            south_wall = corridor['south_wall_y']
            
            expected_left = abs(y - north_wall)
            expected_right = abs(south_wall - y)
        
        elif corridor['type'] == 'vertical':
            # 세로 복도
            west_wall = corridor['west_wall_x']
            east_wall = corridor['east_wall_x']
            
            expected_left = abs(x - west_wall)
            expected_right = abs(east_wall - x)
        
        else:
            # 기타
            expected_left = 120
            expected_right = 120
        
        return {
            'left': expected_left,
            'right': expected_right
        }
    
    def _plan_avoidance(self, current_pose, target_pose, avoid_action):
        """
        초음파 기반 간단 회피
        
        Args:
            current_pose (tuple): (x, y, theta)
            target_pose (tuple): (x, y)
            avoid_action (str): 'avoid_left' or 'avoid_right'
        
        Returns:
            dict: 회피 명령
        """
        # 반대 방향으로 살짝 이동
        if avoid_action == 'avoid_left':
            avoid_angle = -30  # 오른쪽으로 30도
        else:
            avoid_angle = 30   # 왼쪽으로 30도
        
        print(f"⚠️ 장애물 회피: {avoid_action} → {avoid_angle}도")
        
        return {
            'safe_to_proceed': True,
            'action': 'avoid',
            'avoid_direction': avoid_angle,
            'reason': f'obstacle_{avoid_action}'
        }


if __name__ == '__main__':
    print("=== ObstacleAvoidanceSystem 테스트 ===\n")
    
    from ..hardware.robokit_driver import RobokitDriver
    from ..mapping.floor_plan import FloorPlan
    import time
    
    robot = RobokitDriver(mock=True)
    floor_map = FloorPlan()
    
    avoidance = ObstacleAvoidanceSystem(robot, floor_map)
    
    # 테스트
    current_pose = (380, 500, 0)
    target_pose = (380, 1000)
    
    print("🚦 장애물 회피 시뮬레이션:\n")
    
    for i in range(3):
        result = avoidance.check_and_respond(current_pose, target_pose)
        
        print(f"스텝 {i+1}: {result['action']} - {result['reason']}")
        
        if result['avoid_direction'] is not None:
            print(f"  → 회피 방향: {result['avoid_direction']}도")
        
        time.sleep(0.3)
    
    print("\n✅ 테스트 완료")
