"""
통합 장애물 회피 시스템
초음파 + LiDAR + 미끄러짐 구분 + 회피 전략
"""

import math


class ObstacleAvoidanceSystem:
    """
    통합 장애물 감지 및 회피
    
    - 초음파로 근접 장애물 감지
    - LiDAR로 전방 및 측면 장애물 감지 (후방 90도 제외)
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
        
        # LiDAR 감지기 (있으면)
        self.lidar_detector = None
        if self.lidar:
            try:
                from .lidar_detector import LidarObstacleDetector
                self.lidar_detector = LidarObstacleDetector(
                    min_distance=80.0,  # cm
                    sectors=8,
                    scan_rate=5.0  # 5Hz (CPU 부담 감소)
                )
                print("✅ LiDAR 장애물 감지 활성화")
            except Exception as e:
                print(f"⚠️ LiDAR 감지기 초기화 실패: {e}")
                self.lidar_detector = None
        
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
        # 1️⃣ LiDAR 체크 (전방 장애물) - 우선순위 높음!
        # ═══════════════════════════════════════
        if self.lidar and self.lidar_detector:
            lidar_result = self._check_lidar_obstacle(current_pose, target_pose)
            
            if lidar_result is not None:
                # LiDAR가 장애물 감지
                if lidar_result['action'] in ['stop', 'avoid']:
                    return lidar_result
                elif lidar_result['action'] == 'slow_down':
                    # slow_down은 계속 진행하되 초음파도 체크
                    pass
        
        # ═══════════════════════════════════════
        # 2️⃣ 초음파 체크 (근접 장애물)
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
        # 3️⃣ 정상 진행
        # ═══════════════════════════════════════
        self.blocked_count = max(0, self.blocked_count - 1)
        
        action = ultrasonic_result['action']  # 'continue' or 'slow_down'
        
        return {
            'safe_to_proceed': True,
            'action': action,
            'avoid_direction': None,
            'reason': 'clear'
        }
    
    def _check_lidar_obstacle(self, current_pose, target_pose):
        """
        LiDAR 장애물 체크 (후방 90도 제외)
        
        Args:
            current_pose (tuple): (x, y, theta) 현재 위치
            target_pose (tuple): (x, y) 목표 위치
        
        Returns:
            dict or None: 장애물 정보 또는 None
        """
        try:
            # 스캔
            scan = self.lidar.get_scan()
            
            if not scan:
                return None
            
            # ⭐ 후방 90도 제외 (135도~225도)
            # 로봇이 정면을 0도라고 가정
            filtered_scan = [
                (angle, distance) 
                for angle, distance in scan
                if not (135 <= angle <= 225)  # 후방 90도 제외
            ]
            
            if not filtered_scan:
                return None
            
            # 진행 방향 각도 계산
            x, y, theta = current_pose
            target_x, target_y = target_pose
            
            dx = target_x - x
            dy = target_y - y
            target_angle = math.atan2(dy, dx)
            
            # 로봇 좌표계로 변환 (현재 방향 기준)
            relative_angle = math.degrees(target_angle - theta)
            relative_angle = (relative_angle + 360) % 360
            
            # 경로 상 장애물 감지
            path_result = self.lidar_detector.detect_in_path(
                filtered_scan,
                path_angle=relative_angle,
                path_width=60.0  # 60도 폭
            )
            
            # 장애물 있으면 대응
            if path_result['obstacle_in_path']:
                min_dist = path_result['min_distance']
                
                if min_dist < 50:
                    # 매우 가까움 → 정지
                    print(f"🚨 LiDAR: 전방 장애물 {min_dist:.1f}cm (정지)")
                    return {
                        'safe_to_proceed': False,
                        'action': 'stop',
                        'avoid_direction': None,
                        'reason': 'lidar_obstacle_close'
                    }
                
                elif min_dist < 80:
                    # 가까움 → 회피
                    print(f"⚠️ LiDAR: 전방 장애물 {min_dist:.1f}cm (회피)")
                    
                    # 통과 가능한 경로 찾기
                    clear_paths = self.lidar_detector.find_clear_paths(
                        filtered_scan,
                        min_gap_width=60.0
                    )
                    
                    if clear_paths:
                        # 가장 가까운 경로 선택
                        best_path = min(
                            clear_paths,
                            key=lambda p: abs(p['center_angle'] - relative_angle)
                        )
                        
                        # 회피 각도
                        avoid_angle = best_path['center_angle'] - relative_angle
                        
                        print(f"   → 회피 경로: {best_path['center_angle']:.1f}도")
                        
                        return {
                            'safe_to_proceed': True,
                            'action': 'avoid',
                            'avoid_direction': avoid_angle,
                            'reason': 'lidar_obstacle_avoid'
                        }
                    else:
                        # 회피 불가 → 정지
                        print(f"   → 회피 불가, 정지")
                        return {
                            'safe_to_proceed': False,
                            'action': 'stop',
                            'avoid_direction': None,
                            'reason': 'lidar_no_clear_path'
                        }
                
                else:
                    # 중간 거리 → 감속
                    return {
                        'safe_to_proceed': True,
                        'action': 'slow_down',
                        'avoid_direction': None,
                        'reason': 'lidar_obstacle_far'
                    }
            
            # 장애물 없음
            return None
        
        except Exception as e:
            print(f"❌ LiDAR 체크 오류: {e}")
            return None
    
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
        
        print(f"⚠️ 초음파: 장애물 회피 {avoid_action} → {avoid_angle}도")
        
        return {
            'safe_to_proceed': True,
            'action': 'avoid',
            'avoid_direction': avoid_angle,
            'reason': f'ultrasonic_{avoid_action}'
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
