#!/usr/bin/env python3
"""
사용 예제 1: 방 간 이동 (최신 버전)

최신 기능:
- config_dir 인자 추가
- LiDAR 자동 사용
- Logger 통합
"""

from aicane_navigation import NavigationSystem
from aicane_navigation.utils import NavigationLogger

# 로거 초기화
logger = NavigationLogger(
    name="room_navigation",
    log_to_file=True,
    log_dir='./logs'
)

logger.info("=" * 50)
logger.info("방 간 이동 예제")
logger.info("=" * 50)

# 시스템 초기화 (config_dir 추가!)
nav = NavigationSystem(config_dir='./config', mock=True)

# LiDAR 상태 확인
lidar_status = nav.get_lidar_status()
logger.info(f"LiDAR 활성화: {lidar_status['enabled']}")

if lidar_status['enabled']:
    logger.info(f"LiDAR 포트: {lidar_status.get('port', 'unknown')}")
    logger.info("→ 360도 장애물 감지 활성화!")

# 101호 → 107호 이동
logger.log_navigation_start("101호", "107호")

try:
    nav.navigate_rooms('101호', '107호')
    logger.log_navigation_end(success=True, reason="목적지 도착")
except Exception as e:
    logger.error(f"주행 실패: {e}")
    logger.log_navigation_end(success=False, reason=str(e))

# 통계
logger.print_stats()

# 종료
nav.shutdown()

print(f"\n📁 로그 파일: {logger.log_file}")
