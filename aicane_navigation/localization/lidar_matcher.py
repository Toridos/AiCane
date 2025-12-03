"""
LiDAR 기반 맵 매칭 (Tier 3 비상 위치 복구용)
"""

import math
from typing import List, Tuple, Optional


class LidarMapMatcher:
    """
    LiDAR 스캔으로 맵에서 위치 추정
    
    Tier 3 비상 모드에서만 사용 (CPU 부하 높음)
    """
    
    def __init__(self, lidar, floor_map):
        """
        Args:
            lidar: LidarInterface 인스턴스
            floor_map: FloorPlan 인스턴스
        """
        self.lidar = lidar
        self.map = floor_map
    
    def estimate_position_full_search(self, 
                                     lidar_scan: List[Tuple[float, float]],
                                     search_resolution: float = 50.0) -> Tuple[float, float, float, float]:
        """
        전체 맵 탐색으로 위치 추정 (느림, 정확함)
        
        Args:
            lidar_scan: [(angle, distance), ...] LiDAR 스캔 데이터
            search_resolution: 탐색 해상도 (cm)
        
        Returns:
            tuple: (x, y, theta, confidence)
        
        Note:
            이 함수는 CPU를 많이 사용합니다!
            Tier 3 비상 상황에서만 호출하세요.
        """
        if not lidar_scan:
            return (0, 0, 0, 0.0)
        
        # TODO: 실제 맵 매칭 알고리즘 구현
        # 현재는 간단한 복도 중심 추정
        
        # 좌우 벽 거리로 X 좌표 추정
        left_distances = [d for a, d in lidar_scan if 80 <= a <= 100]
        right_distances = [d for a, d in lidar_scan if 260 <= a <= 280]
        
        if left_distances and right_distances:
            d_left = sum(left_distances) / len(left_distances)
            d_right = sum(right_distances) / len(right_distances)
            
            # 복도 중앙으로 추정
            corridor = self.map.corridors[0]  # 메인 복도
            x = corridor['x_min'] + (corridor['x_max'] - corridor['x_min']) / 2
            y = corridor['y_center']
            theta = 0.0
            
            confidence = 0.5  # 중간 신뢰도
            
            return (x, y, theta, confidence)
        
        return (0, 0, 0, 0.0)
    
    def estimate_position_corridor(self,
                                   lidar_scan: List[Tuple[float, float]],
                                   current_pose: Tuple[float, float, float]) -> Tuple[float, float, float, float]:
        """
        복도 환경에서 빠른 위치 보정
        
        Args:
            lidar_scan: LiDAR 스캔 데이터
            current_pose: 현재 추정 위치 (x, y, theta)
        
        Returns:
            tuple: (corrected_x, corrected_y, theta, confidence)
        """
        if not lidar_scan:
            return (*current_pose, 0.0)
        
        x, y, theta = current_pose
        
        # 현재 위치의 복도 정보
        corridor = self.map.get_corridor_at(x, y)
        
        if not corridor or corridor['type'] == 'open_space':
            return (*current_pose, 0.0)
        
        # 좌우 벽 거리 측정
        left_scan = [d for a, d in lidar_scan if 80 <= a <= 100]
        right_scan = [d for a, d in lidar_scan if 260 <= a <= 280]
        
        if left_scan and right_scan:
            d_left = sum(left_scan) / len(left_scan)
            d_right = sum(right_scan) / len(right_scan)
            
            if corridor['type'] == 'vertical':
                # 세로 복도 - X 좌표 보정
                west_wall = corridor['west_wall_x']
                corrected_x = west_wall + d_left
                
                confidence = 0.8
                return (corrected_x, y, theta, confidence)
        
        return (*current_pose, 0.0)


if __name__ == '__main__':
    print("=== LidarMapMatcher 테스트 ===\n")
    
    from ..mapping import FloorPlan
    from .lidar_interface import LidarInterface
    
    # Mock 모드로 테스트
    lidar = LidarInterface(mock=True)
    lidar.open()
    lidar.start_scan()
    
    floor_map = FloorPlan()
    matcher = LidarMapMatcher(lidar, floor_map)
    
    import time
    time.sleep(1)  # 스캔 대기
    
    # 스캔 데이터
    scan = lidar.get_latest_scan()
    print(f"스캔 데이터: {len(scan)}개")
    
    # 위치 추정
    x, y, theta, conf = matcher.estimate_position_full_search(scan)
    print(f"\n추정 위치: ({x:.1f}, {y:.1f}), 각도: {theta:.2f}, 신뢰도: {conf:.2f}")
    
    lidar.close()
    print("\n✅ 테스트 완료")
