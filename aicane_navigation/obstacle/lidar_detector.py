"""
LiDAR 기반 장애물 감지 (개선 버전)
초음파와 병행 사용 + CPU 효율적
"""

from typing import List, Tuple, Dict, Optional
import time


class LidarObstacleDetector:
    """
    LiDAR 기반 장애물 감지
    
    - 360도 스캔
    - 섹터별 분석
    - CPU 효율적
    - 초음파와 보완
    """
    
    def __init__(self, 
                 min_distance: float = 50.0,  # cm
                 sectors: int = 8,
                 scan_rate: float = 10.0):     # Hz
        """
        Args:
            min_distance: 장애물 판단 거리 (cm)
            sectors: 방향 섹터 수 (8방향)
            scan_rate: 스캔 속도 (Hz)
        """
        self.min_distance = min_distance
        self.sectors = sectors
        self.scan_interval = 1.0 / scan_rate
        
        self.last_scan_time = 0
        self.last_result = None
    
    # ========================================
    # 기본 장애물 감지 (팀원 제안 개선)
    # ========================================
    
    def detect(self, scan: List[Tuple[float, float]]) -> Dict[str, bool]:
        """
        장애물 감지 (팀원 제안 개선)
        
        Args:
            scan: [(angle_deg, distance_cm), ...]
        
        Returns:
            dict: {'obstacle': bool, 'direction': str}
        """
        if not scan:
            return {'obstacle': False, 'direction': None}
        
        # 가장 가까운 장애물 찾기
        closest = min(scan, key=lambda x: x[1] if x[1] > 0 else float('inf'))
        angle, distance = closest
        
        # 장애물 여부
        obstacle = distance > 0 and distance < self.min_distance
        
        # 방향
        direction = self._angle_to_direction(angle) if obstacle else None
        
        return {
            'obstacle': obstacle,
            'direction': direction,
            'distance': distance,
            'angle': angle,
        }
    
    # ========================================
    # 섹터별 분석 (CPU 효율적)
    # ========================================
    
    def detect_by_sectors(self, scan: List[Tuple[float, float]]) -> Dict:
        """
        섹터별 장애물 감지 (8방향)
        
        Args:
            scan: [(angle_deg, distance_cm), ...]
        
        Returns:
            dict: {
                'obstacle': bool,
                'sectors': {
                    'front': {'obstacle': bool, 'min_dist': float},
                    'front_left': ...,
                    ...
                }
            }
        """
        # 섹터 초기화
        sector_names = [
            'front',       # 0도 (337.5~22.5)
            'front_right', # 45도
            'right',       # 90도
            'back_right',  # 135도
            'back',        # 180도
            'back_left',   # 225도
            'left',        # 270도
            'front_left',  # 315도
        ]
        
        sectors = {name: {'obstacle': False, 'min_dist': float('inf')} 
                   for name in sector_names}
        
        # 섹터별 분류
        sector_size = 360 / self.sectors
        
        for angle, distance in scan:
            if distance <= 0:
                continue
            
            # 섹터 인덱스
            sector_idx = int((angle + sector_size/2) % 360 / sector_size)
            sector_name = sector_names[sector_idx]
            
            # 최소 거리 업데이트
            if distance < sectors[sector_name]['min_dist']:
                sectors[sector_name]['min_dist'] = distance
            
            # 장애물 여부
            if distance < self.min_distance:
                sectors[sector_name]['obstacle'] = True
        
        # 전체 장애물 여부
        any_obstacle = any(s['obstacle'] for s in sectors.values())
        
        return {
            'obstacle': any_obstacle,
            'sectors': sectors,
            'scan_time': time.time(),
        }
    
    # ========================================
    # 경로 상 장애물 (가장 중요!)
    # ========================================
    
    def detect_in_path(self, 
                      scan: List[Tuple[float, float]],
                      path_angle: float,
                      path_width: float = 60.0) -> Dict:
        """
        경로 상의 장애물 감지 (가장 실용적!)
        
        Args:
            scan: [(angle_deg, distance_cm), ...]
            path_angle: 진행 방향 각도 (0~360)
            path_width: 경로 폭 (degrees)
        
        Returns:
            dict: {
                'obstacle_in_path': bool,
                'min_distance': float,
                'recommended_action': str
            }
        """
        # 경로 범위
        angle_min = (path_angle - path_width/2) % 360
        angle_max = (path_angle + path_width/2) % 360
        
        # 경로 상의 포인트 필터링
        path_points = []
        
        for angle, distance in scan:
            if distance <= 0:
                continue
            
            # 각도 범위 체크
            in_range = False
            if angle_min < angle_max:
                in_range = angle_min <= angle <= angle_max
            else:  # 360도 넘어가는 경우
                in_range = angle >= angle_min or angle <= angle_max
            
            if in_range:
                path_points.append((angle, distance))
        
        # 장애물 여부
        if not path_points:
            return {
                'obstacle_in_path': False,
                'min_distance': float('inf'),
                'recommended_action': 'proceed',
            }
        
        # 최소 거리
        min_dist = min(d for _, d in path_points)
        
        # 권장 액션
        if min_dist < self.min_distance:
            action = 'stop'
        elif min_dist < self.min_distance * 2:
            action = 'slow_down'
        else:
            action = 'proceed'
        
        return {
            'obstacle_in_path': min_dist < self.min_distance,
            'min_distance': min_dist,
            'recommended_action': action,
            'num_points': len(path_points),
        }
    
    # ========================================
    # 통과 가능 경로 찾기
    # ========================================
    
    def find_clear_paths(self, 
                        scan: List[Tuple[float, float]],
                        min_gap_width: float = 80.0) -> List[Dict]:
        """
        통과 가능한 경로 찾기
        
        Args:
            scan: [(angle_deg, distance_cm), ...]
            min_gap_width: 최소 통과 폭 (degrees)
        
        Returns:
            list: [{
                'center_angle': float,
                'width': float,
                'min_distance': float
            }, ...]
        """
        if not scan:
            return []
        
        # 각도 정렬
        sorted_scan = sorted(scan, key=lambda x: x[0])
        
        gaps = []
        gap_start = None
        
        for i, (angle, distance) in enumerate(sorted_scan):
            # 충분히 먼 경우 (통과 가능)
            if distance >= self.min_distance:
                if gap_start is None:
                    gap_start = i
            else:
                # 장애물 → 갭 종료
                if gap_start is not None:
                    gap_end = i - 1
                    
                    # 갭 분석
                    gap_angles = [sorted_scan[j][0] for j in range(gap_start, gap_end+1)]
                    gap_dists = [sorted_scan[j][1] for j in range(gap_start, gap_end+1)]
                    
                    width = gap_angles[-1] - gap_angles[0]
                    
                    # 최소 폭 이상이면 추가
                    if width >= min_gap_width:
                        gaps.append({
                            'center_angle': (gap_angles[0] + gap_angles[-1]) / 2,
                            'width': width,
                            'min_distance': min(gap_dists),
                        })
                    
                    gap_start = None
        
        # 마지막 갭 처리
        if gap_start is not None:
            gap_angles = [sorted_scan[j][0] for j in range(gap_start, len(sorted_scan))]
            gap_dists = [sorted_scan[j][1] for j in range(gap_start, len(sorted_scan))]
            
            width = gap_angles[-1] - gap_angles[0]
            
            if width >= min_gap_width:
                gaps.append({
                    'center_angle': (gap_angles[0] + gap_angles[-1]) / 2,
                    'width': width,
                    'min_distance': min(gap_dists),
                })
        
        return gaps
    
    # ========================================
    # 초음파 보완 (하이브리드)
    # ========================================
    
    def combine_with_ultrasonic(self,
                                lidar_result: Dict,
                                ultrasonic: Dict[str, float]) -> Dict:
        """
        LiDAR + 초음파 통합
        
        Args:
            lidar_result: LiDAR 결과
            ultrasonic: {'front': 120, 'left': 95, 'right': 98}
        
        Returns:
            dict: 통합 결과
        """
        # LiDAR 장애물
        lidar_obstacle = lidar_result.get('obstacle', False)
        
        # 초음파 장애물 (50cm 이내)
        us_front = ultrasonic.get('front', 999) < 50
        us_left = ultrasonic.get('left', 999) < 50
        us_right = ultrasonic.get('right', 999) < 50
        us_obstacle = us_front or us_left or us_right
        
        # 통합 판단 (둘 중 하나라도 감지하면)
        combined_obstacle = lidar_obstacle or us_obstacle
        
        # 신뢰도 계산
        confidence = 'high' if lidar_obstacle and us_obstacle else 'medium'
        
        return {
            'obstacle': combined_obstacle,
            'lidar_detected': lidar_obstacle,
            'ultrasonic_detected': us_obstacle,
            'confidence': confidence,
            'details': {
                'lidar': lidar_result,
                'ultrasonic': ultrasonic,
            }
        }
    
    # ========================================
    # 유틸리티
    # ========================================
    
    def _angle_to_direction(self, angle: float) -> str:
        """각도 → 방향"""
        if 337.5 <= angle or angle < 22.5:
            return 'front'
        elif 22.5 <= angle < 67.5:
            return 'front_right'
        elif 67.5 <= angle < 112.5:
            return 'right'
        elif 112.5 <= angle < 157.5:
            return 'back_right'
        elif 157.5 <= angle < 202.5:
            return 'back'
        elif 202.5 <= angle < 247.5:
            return 'back_left'
        elif 247.5 <= angle < 292.5:
            return 'left'
        else:
            return 'front_left'
    
    def should_scan(self) -> bool:
        """스캔 필요 여부 (CPU 절약)"""
        now = time.time()
        
        if now - self.last_scan_time >= self.scan_interval:
            self.last_scan_time = now
            return True
        
        return False


# 사용 예제
if __name__ == '__main__':
    print("=== LidarObstacleDetector 테스트 ===\n")
    
    # 샘플 스캔 데이터
    sample_scan = [
        (0, 120),    # 정면 120cm
        (45, 150),   # 우전방 150cm
        (90, 200),   # 우측 200cm
        (135, 180),  # 우후방
        (180, 250),  # 후방
        (225, 190),  # 좌후방
        (270, 95),   # 좌측 95cm (가까움!)
        (315, 140),  # 좌전방
    ]
    
    detector = LidarObstacleDetector(min_distance=100)
    
    # 1. 기본 감지
    print("1️⃣ 기본 장애물 감지:")
    result = detector.detect(sample_scan)
    print(f"   장애물: {result['obstacle']}")
    print(f"   방향: {result['direction']}")
    print(f"   거리: {result['distance']:.1f}cm\n")
    
    # 2. 섹터별
    print("2️⃣ 섹터별 분석:")
    sectors = detector.detect_by_sectors(sample_scan)
    for name, info in sectors['sectors'].items():
        if info['obstacle']:
            print(f"   {name}: 장애물! ({info['min_dist']:.1f}cm)")
    print()
    
    # 3. 경로 상 장애물
    print("3️⃣ 경로 상 장애물 (정면):")
    path_check = detector.detect_in_path(sample_scan, path_angle=0, path_width=60)
    print(f"   경로 상 장애물: {path_check['obstacle_in_path']}")
    print(f"   권장 액션: {path_check['recommended_action']}\n")
    
    # 4. 통과 가능 경로
    print("4️⃣ 통과 가능 경로:")
    gaps = detector.find_clear_paths(sample_scan, min_gap_width=45)
    for i, gap in enumerate(gaps):
        print(f"   경로 {i+1}: {gap['center_angle']:.1f}° (폭 {gap['width']:.1f}°)")
    
    print("\n✅ 테스트 완료")
