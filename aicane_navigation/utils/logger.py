"""
AiCane Navigation Logger
위치, 장애물, 명령어 등 모든 주행 정보 기록
"""

import time
import logging
import os
from typing import Tuple, Optional, Dict, Any
from datetime import datetime


class NavigationLogger:
    """
    AiCane 내비게이션 통합 로거
    
    - 위치 로그
    - 장애물 로그
    - 명령어 로그
    - 이벤트 로그
    - 파일 저장
    - 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    """
    
    def __init__(self, 
                 name: str = "aicane_navigation",
                 log_to_file: bool = True,
                 log_dir: str = "./logs",
                 level: str = "INFO"):
        """
        Args:
            name: 로거 이름
            log_to_file: 파일 저장 여부
            log_dir: 로그 디렉토리
            level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        """
        self.name = name
        self.log_dir = log_dir
        
        # Python logging 설정
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 핸들러 제거 (중복 방지)
        self.logger.handlers.clear()
        
        # 포맷 설정
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 파일 핸들러
        if log_to_file:
            os.makedirs(log_dir, exist_ok=True)
            
            # 날짜별 파일
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"nav_{timestamp}.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            self.log_file = log_file
            self.logger.info(f"로그 파일: {log_file}")
        else:
            self.log_file = None
        
        # 통계
        self.stats = {
            'positions_logged': 0,
            'obstacles_logged': 0,
            'commands_logged': 0,
            'events_logged': 0,
        }
    
    # ========================================
    # 위치 로그
    # ========================================
    
    def log_position(self, 
                    pose: Tuple[float, float, float], 
                    tier: int, 
                    confidence: float,
                    extra: Optional[Dict] = None) -> None:
        """
        위치 로그
        
        Args:
            pose: (x, y, theta) 위치
            tier: 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR
            confidence: 0.0~1.0 신뢰도
            extra: 추가 정보
        """
        x, y, theta = pose
        
        # 로그 레벨
        level = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR][tier]
        
        # 메시지
        msg = f"Position: ({x:.2f}, {y:.2f}, θ={theta:.1f}°) | Confidence: {confidence:.2f}"
        
        # 추가 정보
        if extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            msg += f" | {extra_str}"
        
        self.logger.log(level, msg)
        self.stats['positions_logged'] += 1
    
    # ========================================
    # 장애물 로그
    # ========================================
    
    def log_obstacle(self, 
                    obstacle_info: Dict[str, Any],
                    severity: str = "INFO") -> None:
        """
        장애물 로그
        
        Args:
            obstacle_info: {
                'front': float,
                'left': float,
                'right': float,
                'action': str,
                'source': 'ultrasonic' | 'lidar' | 'hybrid'
            }
            severity: DEBUG, INFO, WARNING, ERROR
        """
        level = getattr(logging, severity.upper())
        
        # 메시지 생성
        distances = []
        for direction in ['front', 'left', 'right']:
            if direction in obstacle_info:
                distances.append(f"{direction}={obstacle_info[direction]:.1f}cm")
        
        dist_str = ", ".join(distances)
        action = obstacle_info.get('action', 'unknown')
        source = obstacle_info.get('source', 'unknown')
        
        msg = f"Obstacle: [{dist_str}] | Action: {action} | Source: {source}"
        
        self.logger.log(level, msg)
        self.stats['obstacles_logged'] += 1
    
    # ========================================
    # 명령어 로그
    # ========================================
    
    def log_command(self, 
                   direction: str, 
                   speed_level: int,
                   extra: Optional[Dict] = None) -> None:
        """
        로봇 명령어 로그
        
        Args:
            direction: 'forward', 'backward', 'left', 'right', 'stop'
            speed_level: 속도 레벨
            extra: 추가 정보
        """
        msg = f"Command: {direction.upper()} | Speed: {speed_level}"
        
        if extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            msg += f" | {extra_str}"
        
        self.logger.debug(msg)
        self.stats['commands_logged'] += 1
    
    # ========================================
    # 이벤트 로그 (팀원 제안 포함)
    # ========================================
    
    def log_event(self, 
                 message: str, 
                 tier: int = 1, 
                 extra: Optional[Dict] = None) -> None:
        """
        일반 이벤트 로그 (팀원 제안)
        
        Args:
            message: 로그 메시지
            tier: 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR
            extra: 추가 정보
        """
        level = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR][tier]
        
        msg = message
        
        if extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            msg += f" | {extra_str}"
        
        self.logger.log(level, msg)
        self.stats['events_logged'] += 1
    
    # ========================================
    # 단축 메서드
    # ========================================
    
    def debug(self, message: str, **kwargs):
        """DEBUG 레벨 로그"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """INFO 레벨 로그"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """WARNING 레벨 로그"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """ERROR 레벨 로그"""
        self.logger.error(message, extra=kwargs)
    
    # ========================================
    # 파일 관리
    # ========================================
    
    def save_to_file(self, filename: str) -> None:
        """
        현재 로그를 특정 파일로 복사
        
        Args:
            filename: 저장할 파일명
        """
        if not self.log_file:
            self.warning("파일 로깅이 비활성화되어 있습니다")
            return
        
        import shutil
        try:
            shutil.copy(self.log_file, filename)
            self.info(f"로그 저장 완료: {filename}")
        except Exception as e:
            self.error(f"로그 저장 실패: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """로그 통계 반환"""
        return self.stats.copy()
    
    def print_stats(self):
        """로그 통계 출력"""
        self.info("=== 로그 통계 ===")
        for key, value in self.stats.items():
            self.info(f"  {key}: {value}")
    
    # ========================================
    # 주행 시작/종료
    # ========================================
    
    def log_navigation_start(self, from_room: str, to_room: str):
        """주행 시작 로그"""
        self.info("=" * 50)
        self.info(f"주행 시작: {from_room} → {to_room}")
        self.info("=" * 50)
    
    def log_navigation_end(self, success: bool, reason: str = ""):
        """주행 종료 로그"""
        status = "성공" if success else "실패"
        self.info("=" * 50)
        self.info(f"주행 종료: {status}")
        if reason:
            self.info(f"사유: {reason}")
        self.print_stats()
        self.info("=" * 50)


# 전역 로거 (싱글톤)
_global_logger = None


def get_logger(name: str = "aicane_navigation", **kwargs) -> NavigationLogger:
    """
    전역 로거 가져오기
    
    Args:
        name: 로거 이름
        **kwargs: NavigationLogger 인자
    
    Returns:
        NavigationLogger
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = NavigationLogger(name, **kwargs)
    
    return _global_logger


# 사용 예제
if __name__ == '__main__':
    print("=== NavigationLogger 테스트 ===\n")
    
    # 1. 로거 생성
    logger = NavigationLogger(
        name="test_nav",
        log_to_file=True,
        log_dir="./logs",
        level="DEBUG"
    )
    
    # 2. 주행 시작
    logger.log_navigation_start("101호", "107호")
    
    # 3. 위치 로그
    logger.log_position(
        pose=(456.0, 835.0, 90.0),
        tier=1,  # INFO
        confidence=0.95,
        extra={'tier': 1, 'source': 'ultrasonic'}
    )
    
    # 4. 장애물 로그
    logger.log_obstacle({
        'front': 45.0,
        'left': 120.0,
        'right': 98.0,
        'action': 'slow_down',
        'source': 'ultrasonic'
    }, severity="WARNING")
    
    # 5. 명령어 로그
    logger.log_command('forward', 10, extra={'reason': 'waypoint'})
    
    # 6. 이벤트 로그 (팀원 제안)
    logger.log_event("경로 재계획", tier=2, extra={'attempts': 3})
    
    # 7. 단축 메서드
    logger.info("웨이포인트 도착")
    logger.warning("GPS 신호 약함")
    logger.error("센서 오류")
    
    # 8. 주행 종료
    logger.log_navigation_end(success=True, reason="목적지 도착")
    
    # 9. 통계
    logger.print_stats()
    
    # 10. 파일 저장
    logger.save_to_file("./logs/backup.log")
    
    print("\n✅ 테스트 완료")
    print(f"로그 파일: {logger.log_file}")
