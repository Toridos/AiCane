"""
경로 계획 시스템
AI 경로 통합 + 복도 기반 + 장애물 회피
"""

from typing import List, Tuple, Optional, Dict
import math


class PathPlanner:
    """
    통합 경로 계획 시스템
    
    - AI 경로 통합 (우선)
    - 복도 기반 경로 (대체)
    - 장애물 회피 (동적)
    - 웨이포인트 보간
    """
    
    def __init__(self, map_system, room_manager=None):
        """
        Args:
            map_system: FloorPlan, MultiFloorMap, 또는 UnifiedMapSystem
            room_manager: RoomManager (선택사항)
        """
        self.map_system = map_system
        self.room_manager = room_manager
    
    # ========================================
    # AI 경로 사용 (최우선)
    # ========================================
    
    def plan_with_ai(self, ai_path_json: Dict) -> List[Tuple[float, float, float]]:
        """
        AI 경로 사용 (최우선 방법)
        
        Args:
            ai_path_json: AI 모델의 경로 JSON
        
        Returns:
            list: [(x, y, theta), ...] waypoints
        """
        # MultiFloorMap이 있으면 사용
        if hasattr(self.map_system, 'parse_ai_path'):
            waypoints = self.map_system.parse_ai_path(ai_path_json)
            
            # (x, y) → (x, y, theta)
            return self._add_theta_to_waypoints(waypoints)
        
        # UnifiedMapSystem
        elif hasattr(self.map_system, 'map'):
            if hasattr(self.map_system.map, 'parse_ai_path'):
                waypoints = self.map_system.map.parse_ai_path(ai_path_json)
                return self._add_theta_to_waypoints(waypoints)
        
        raise ValueError("AI 경로 파싱 지원 안 함 (MultiFloorMap 필요)")
    
    def _add_theta_to_waypoints(self, waypoints: List[Dict]) -> List[Tuple[float, float, float]]:
        """Waypoint에 theta(방향) 추가"""
        result = []
        
        for i, wp in enumerate(waypoints):
            x = wp['x']
            y = wp['y']
            
            # 다음 waypoint 방향으로 theta 계산
            if i < len(waypoints) - 1:
                next_wp = waypoints[i + 1]
                dx = next_wp['x'] - x
                dy = next_wp['y'] - y
                theta = math.atan2(dy, dx)
            else:
                # 마지막은 이전 theta 유지
                theta = result[-1][2] if result else 0.0
            
            result.append((x, y, theta))
        
        return result
    
    # ========================================
    # 복도 기반 경로 (대체 방법)
    # ========================================
    
    def plan_room_to_room(self, from_room: str, to_room: str) -> List[Tuple[float, float, float]]:
        """
        방 간 경로 생성 (복도 기반)
        
        Args:
            from_room: 출발 방 (예: '101호')
            to_room: 도착 방 (예: '107호')
        
        Returns:
            list: [(x, y, theta), ...] waypoints
        """
        # FloorPlan이 있으면 사용
        if hasattr(self.map_system, 'generate_simple_path'):
            waypoints = self.map_system.generate_simple_path(from_room, to_room)
            return waypoints
        
        # UnifiedMapSystem
        elif hasattr(self.map_system, 'generate_simple_path'):
            waypoints = self.map_system.generate_simple_path(from_room, to_room)
            return waypoints
        
        # RoomManager 사용
        elif self.room_manager:
            start = self.room_manager.get_door_waypoint(from_room)
            goal = self.room_manager.get_door_waypoint(to_room)
            
            if start and goal:
                # 복도 경로 생성
                return self._plan_corridor_path(start, goal)
        
        raise ValueError("경로 생성 실패: FloorPlan 또는 RoomManager 필요")
    
    def _plan_corridor_path(self, 
                           start: Tuple[float, float, float], 
                           goal: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
        """
        복도 기반 경로 생성
        
        건물 구조를 고려한 L자 또는 ㄷ자 경로
        """
        sx, sy, s_theta = start
        gx, gy, g_theta = goal
        
        # 복도 중심선 Y 좌표 (예: 1312cm)
        corridor_y = 1312.5
        
        path = []
        
        # 1. 시작점
        path.append(start)
        
        # 2. 시작점에서 복도로
        if abs(sy - corridor_y) > 50:  # 복도 밖이면
            path.append((sx, corridor_y, 0.0))
        
        # 3. 복도 따라 이동
        if abs(gx - sx) > 50:  # 수평 이동 필요
            path.append((gx, corridor_y, 0.0))
        
        # 4. 복도에서 목적지로
        if abs(gy - corridor_y) > 50:  # 복도 밖이면
            path.append((gx, gy, g_theta))
        else:
            path.append(goal)
        
        return path
    
    # ========================================
    # 단순 직선 경로 (팀원 제안, 비상용)
    # ========================================
    
    def plan_straight(self, 
                     start: Tuple[float, float], 
                     goal: Tuple[float, float], 
                     steps: int = 20) -> List[Tuple[float, float, float]]:
        """
        단순 직선 경로 (팀원 제안)
        
        주의: 벽을 뚫고 갈 수 있음! 비상용만 사용
        
        Args:
            start: (x, y)
            goal: (x, y)
            steps: 중간 샘플 수
        
        Returns:
            list: [(x, y, theta), ...]
        """
        if steps <= 1:
            return [
                (start[0], start[1], 0.0),
                (goal[0], goal[1], 0.0)
            ]
        
        sx, sy = start
        gx, gy = goal
        
        path = []
        
        for i in range(steps + 1):
            t = i / steps
            x = sx + (gx - sx) * t
            y = sy + (gy - sy) * t
            
            # 방향 계산
            if i < steps:
                theta = math.atan2(gy - sy, gx - sx)
            else:
                theta = path[-1][2] if path else 0.0
            
            path.append((x, y, theta))
        
        return path
    
    # ========================================
    # 웨이포인트 보간
    # ========================================
    
    def interpolate_waypoints(self, 
                             waypoints: List[Tuple[float, float, float]], 
                             max_gap: float = 50.0) -> List[Tuple[float, float, float]]:
        """
        웨이포인트 사이 보간
        
        Args:
            waypoints: [(x, y, theta), ...]
            max_gap: 최대 간격 (cm)
        
        Returns:
            list: 보간된 waypoints
        """
        if len(waypoints) < 2:
            return waypoints
        
        result = [waypoints[0]]
        
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_wp = waypoints[i + 1]
            
            # 거리 계산
            dx = next_wp[0] - current[0]
            dy = next_wp[1] - current[1]
            dist = (dx*dx + dy*dy) ** 0.5
            
            # 보간 필요 여부
            if dist > max_gap:
                # 필요한 중간점 개수
                num_points = int(dist / max_gap)
                
                for j in range(1, num_points + 1):
                    t = j / (num_points + 1)
                    x = current[0] + dx * t
                    y = current[1] + dy * t
                    theta = math.atan2(dy, dx)
                    
                    result.append((x, y, theta))
            
            result.append(next_wp)
        
        return result
    
    # ========================================
    # 장애물 회피 경로
    # ========================================
    
    def replan_avoiding_obstacle(self,
                                 current_pos: Tuple[float, float, float],
                                 goal_pos: Tuple[float, float, float],
                                 obstacle_pos: Tuple[float, float],
                                 obstacle_radius: float = 100.0,
                                 floor: int = 1) -> List[Tuple[float, float, float]]:
        """
        장애물 회피 경로 재계획
        
        Args:
            current_pos: 현재 위치 (x, y, theta)
            goal_pos: 목표 위치 (x, y, theta)
            obstacle_pos: 장애물 위치 (x, y)
            obstacle_radius: 장애물 반경 (cm)
            floor: 층 번호
        
        Returns:
            list: 우회 경로 waypoints
        """
        # MultiFloorMap에 회피 기능 있으면 사용
        if hasattr(self.map_system, 'replan_path_avoiding_obstacle'):
            path = self.map_system.replan_path_avoiding_obstacle(
                current_floor=floor,
                current_pos=(current_pos[0], current_pos[1]),
                goal_pos=(goal_pos[0], goal_pos[1]),
                obstacle_pos=obstacle_pos,
                obstacle_radius=obstacle_radius,
            )
            
            # Dict → Tuple 변환
            return [(wp['x'], wp['y'], 0.0) for wp in path]
        
        # 간단한 회피 (좌우로 우회)
        else:
            return self._simple_avoid(current_pos, goal_pos, obstacle_pos, obstacle_radius)
    
    def _simple_avoid(self,
                     current: Tuple[float, float, float],
                     goal: Tuple[float, float, float],
                     obstacle: Tuple[float, float],
                     radius: float) -> List[Tuple[float, float, float]]:
        """간단한 좌우 우회"""
        cx, cy, c_theta = current
        gx, gy, g_theta = goal
        ox, oy = obstacle
        
        # 우회 거리
        avoid_dist = radius + 50  # 안전 마진
        
        # 좌측 우회점
        avoid_left = (ox - avoid_dist, oy, 0.0)
        
        # 우측 우회점
        avoid_right = (ox + avoid_dist, oy, 0.0)
        
        # 더 가까운 쪽 선택
        dist_left = ((avoid_left[0] - cx)**2 + (avoid_left[1] - cy)**2) ** 0.5
        dist_right = ((avoid_right[0] - cx)**2 + (avoid_right[1] - cy)**2) ** 0.5
        
        avoid_point = avoid_left if dist_left < dist_right else avoid_right
        
        # 경로 생성
        return [
            current,
            avoid_point,
            goal,
        ]
    
    # ========================================
    # 유틸리티
    # ========================================
    
    def smooth_path(self, 
                   waypoints: List[Tuple[float, float, float]], 
                   smoothing_factor: float = 0.3) -> List[Tuple[float, float, float]]:
        """
        경로 스무딩
        
        Args:
            waypoints: 원본 경로
            smoothing_factor: 스무딩 강도 (0~1)
        
        Returns:
            list: 스무딩된 경로
        """
        if len(waypoints) < 3:
            return waypoints
        
        smoothed = [waypoints[0]]
        
        for i in range(1, len(waypoints) - 1):
            prev = waypoints[i - 1]
            curr = waypoints[i]
            next_wp = waypoints[i + 1]
            
            # 이전, 현재, 다음의 평균
            x = curr[0] * (1 - smoothing_factor) + \
                (prev[0] + next_wp[0]) / 2 * smoothing_factor
            y = curr[1] * (1 - smoothing_factor) + \
                (prev[1] + next_wp[1]) / 2 * smoothing_factor
            
            # Theta는 다음 점 방향
            dx = next_wp[0] - x
            dy = next_wp[1] - y
            theta = math.atan2(dy, dx)
            
            smoothed.append((x, y, theta))
        
        smoothed.append(waypoints[-1])
        
        return smoothed
    
    def get_path_length(self, waypoints: List[Tuple[float, float, float]]) -> float:
        """경로 총 길이 (cm)"""
        if len(waypoints) < 2:
            return 0.0
        
        total = 0.0
        
        for i in range(len(waypoints) - 1):
            dx = waypoints[i+1][0] - waypoints[i][0]
            dy = waypoints[i+1][1] - waypoints[i][1]
            total += (dx*dx + dy*dy) ** 0.5
        
        return total


# 사용 예제
if __name__ == '__main__':
    print("=== PathPlanner 테스트 ===\n")
    
    # 1. 단순 직선 (팀원 제안)
    print("1️⃣ 단순 직선 경로:")
    planner = PathPlanner(None)
    
    path = planner.plan_straight((0, 0), (1000, 1000), steps=5)
    print(f"   경로 길이: {len(path)}개 waypoint")
    print(f"   총 거리: {planner.get_path_length(path):.1f}cm\n")
    
    # 2. 웨이포인트 보간
    print("2️⃣ 웨이포인트 보간:")
    waypoints = [
        (0, 0, 0),
        (500, 0, 0),
        (500, 500, 90),
    ]
    
    interpolated = planner.interpolate_waypoints(waypoints, max_gap=100)
    print(f"   원본: {len(waypoints)}개")
    print(f"   보간 후: {len(interpolated)}개\n")
    
    # 3. 경로 스무딩
    print("3️⃣ 경로 스무딩:")
    zigzag = [
        (0, 0, 0),
        (100, 50, 0),
        (200, 0, 0),
        (300, 50, 0),
        (400, 0, 0),
    ]
    
    smoothed = planner.smooth_path(zigzag, smoothing_factor=0.5)
    print(f"   원본 길이: {planner.get_path_length(zigzag):.1f}cm")
    print(f"   스무딩 후: {planner.get_path_length(smoothed):.1f}cm\n")
    
    print("✅ 테스트 완료")
