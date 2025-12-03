"""
실시간 주행 모니터링 (ROS 없이)
"""

import time
from typing import Optional
from threading import Thread


class LiveMonitor:
    """
    실시간 주행 상태 모니터링
    
    ROS 없이 간단한 모니터링
    - 위치
    - 센서 값
    - 상태
    """
    
    def __init__(self, navigation_system):
        """
        Args:
            navigation_system: NavigationSystem 인스턴스
        """
        self.nav = navigation_system
        self.running = False
        self.monitor_thread = None
    
    def start(self):
        """모니터링 시작"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("📊 모니터링 시작")
    
    def stop(self):
        """모니터링 중지"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        print("📊 모니터링 중지")
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while self.running:
            self._print_status()
            time.sleep(1.0)  # 1초마다
    
    def _print_status(self):
        """상태 출력"""
        try:
            # 위치
            pose = self.nav.localization.get_current_pose()
            
            # 센서
            distances = self.nav.obstacle_detector.get_ultrasonic_distances()
            
            # 출력
            print(f"\r위치: ({pose[0]:.1f}, {pose[1]:.1f}, {pose[2]:.1f}°) | "
                  f"센서: F={distances.get('front', 0):.1f}cm "
                  f"L={distances.get('left', 0):.1f}cm "
                  f"R={distances.get('right', 0):.1f}cm",
                  end='', flush=True)
        
        except Exception as e:
            pass


# 사용 예제
if __name__ == '__main__':
    from aicane_navigation import NavigationSystem
    
    # 시스템
    nav = NavigationSystem()
    
    # 모니터링
    monitor = LiveMonitor(nav)
    monitor.start()
    
    # 주행 (모니터링 하면서)
    try:
        nav.navigate_rooms('101호', '107호')
    finally:
        monitor.stop()
