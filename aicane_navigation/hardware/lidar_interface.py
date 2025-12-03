"""
RPLidar X4 Pro LiDAR 센서 인터페이스
실제 스캔 데이터 읽기 및 처리
"""

import time
import math
from typing import List, Tuple, Optional, Dict
import threading
import queue


class LidarInterface:
    """
    RPLidar X4 Pro (또는 호환 센서) 인터페이스
    
    특징:
    - 360도 스캔
    - 실시간 데이터 읽기
    - Mock 모드 지원
    - 스레드 안전
    """
    
    def __init__(self, 
                 port: str = "/dev/ttyUSB0", 
                 baudrate: int = 115200,
                 timeout: float = 1.0,
                 mock: bool = False) -> None:
        """
        Args:
            port (str): 시리얼 포트
            baudrate (int): 통신 속도
            timeout (float): 타임아웃 (초)
            mock (bool): Mock 모드 (테스트용)
        """
        self._port_name = port
        self._baudrate = baudrate
        self._timeout = timeout
        self.mock = mock
        
        # 상태
        self._serial: Optional = None
        self._lidar = None
        self._running = False
        self._scan_thread = None
        
        # 데이터 버퍼
        self._latest_scan: List[Tuple[float, float]] = []
        self._scan_queue = queue.Queue(maxsize=10)
        self._lock = threading.Lock()
        
        # 통계
        self.scan_count = 0
        self.last_scan_time = 0
        
        print(f"🔍 LiDAR 초기화: {port} ({'Mock' if mock else 'Real'})")
    
    def open(self) -> bool:
        """
        LiDAR 연결 및 시작
        
        Returns:
            bool: 연결 성공 여부
        """
        if self.mock:
            print("✅ LiDAR Mock 모드")
            return True
        
        try:
            # pyserial 확인
            import serial
            
            # RPLidar 라이브러리 사용 시도
            try:
                from rplidar import RPLidar
                
                print(f"🔌 LiDAR 연결 중: {self._port_name}")
                self._lidar = RPLidar(self._port_name, baudrate=self._baudrate, timeout=self._timeout)
                
                # 장치 정보 가져오기
                info = self._lidar.get_info()
                health = self._lidar.get_health()
                
                print(f"✅ LiDAR 연결 성공")
                print(f"   모델: {info.get('model', 'Unknown')}")
                print(f"   펌웨어: {info.get('firmware', 'Unknown')}")
                print(f"   하드웨어: {info.get('hardware', 'Unknown')}")
                print(f"   상태: {health[0]}")
                
                return True
                
            except ImportError:
                print("⚠️ rplidar 라이브러리 없음")
                print("   설치: pip install rplidar-roboticia")
                print("   Mock 모드로 전환합니다")
                self.mock = True
                return True
                
        except Exception as e:
            print(f"❌ LiDAR 연결 실패: {e}")
            print("   Mock 모드로 전환합니다")
            self.mock = True
            return True
    
    def start_scan(self) -> None:
        """스캔 시작 (백그라운드 스레드)"""
        if self._running:
            return
        
        self._running = True
        
        if not self.mock:
            # 실제 LiDAR 스캔 시작
            try:
                self._lidar.start_motor()
                time.sleep(0.5)  # 모터 안정화
            except:
                pass
        
        # 스캔 스레드 시작
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()
        
        print("🔄 LiDAR 스캔 시작")
    
    def stop_scan(self) -> None:
        """스캔 중지"""
        self._running = False
        
        if self._scan_thread:
            self._scan_thread.join(timeout=2.0)
        
        if not self.mock and self._lidar:
            try:
                self._lidar.stop()
                self._lidar.stop_motor()
            except:
                pass
        
        print("⏸️ LiDAR 스캔 중지")
    
    def _scan_loop(self) -> None:
        """백그라운드 스캔 루프"""
        while self._running:
            try:
                if self.mock:
                    # Mock 데이터 생성
                    scan = self._generate_mock_scan()
                else:
                    # 실제 스캔
                    scan = self._read_real_scan()
                
                if scan:
                    with self._lock:
                        self._latest_scan = scan
                        self.scan_count += 1
                        self.last_scan_time = time.time()
                    
                    # 큐에 추가
                    try:
                        self._scan_queue.put_nowait(scan)
                    except queue.Full:
                        # 오래된 데이터 제거
                        try:
                            self._scan_queue.get_nowait()
                            self._scan_queue.put_nowait(scan)
                        except:
                            pass
                
            except Exception as e:
                print(f"⚠️ 스캔 오류: {e}")
                time.sleep(0.1)
    
    def _read_real_scan(self) -> List[Tuple[float, float]]:
        """
        실제 LiDAR에서 스캔 읽기
        
        Returns:
            list: [(angle_deg, distance_cm), ...]
        """
        if not self._lidar:
            return []
        
        try:
            scan_data = []
            
            # 한 프레임 스캔
            for scan in self._lidar.iter_scans(max_buf_meas=500):
                for (quality, angle, distance) in scan:
                    # quality: 신호 품질 (0~255)
                    # angle: 각도 (0~360)
                    # distance: 거리 (mm)
                    
                    if quality > 10 and distance > 0:  # 품질 필터
                        distance_cm = distance / 10.0  # mm → cm
                        scan_data.append((angle, distance_cm))
                
                # 한 프레임만 읽고 반환
                break
            
            return scan_data
            
        except Exception as e:
            print(f"⚠️ 스캔 읽기 오류: {e}")
            return []
    
    def _generate_mock_scan(self) -> List[Tuple[float, float]]:
        """
        Mock 스캔 데이터 생성 (테스트용)
        
        Returns:
            list: [(angle_deg, distance_cm), ...]
        """
        import random
        
        scan = []
        
        # 360도 스캔 (1도 간격)
        for angle in range(0, 360, 1):
            # 기본 거리 (복도: 120cm)
            base_distance = 120.0
            
            # 노이즈 추가
            noise = random.uniform(-5, 5)
            distance = base_distance + noise
            
            # 특정 각도에 장애물 시뮬레이션
            if 30 <= angle <= 50:
                # 정면 30~50도에 장애물 (50cm)
                distance = 50.0 + random.uniform(-2, 2)
            elif 150 <= angle <= 210:
                # 뒤쪽은 멀리 (200cm)
                distance = 200.0 + random.uniform(-10, 10)
            
            scan.append((float(angle), distance))
        
        time.sleep(0.05)  # 20Hz (실제 LiDAR와 유사)
        return scan
    
    def get_latest_scan(self) -> List[Tuple[float, float]]:
        """
        최신 스캔 데이터 반환
        
        Returns:
            list: [(angle_deg, distance_cm), ...]
        """
        with self._lock:
            return self._latest_scan.copy()
    
    def get_scan_blocking(self, timeout: float = 1.0) -> Optional[List[Tuple[float, float]]]:
        """
        새로운 스캔 대기 (블로킹)
        
        Args:
            timeout (float): 타임아웃 (초)
        
        Returns:
            list or None: 스캔 데이터
        """
        try:
            scan = self._scan_queue.get(timeout=timeout)
            return scan
        except queue.Empty:
            return None
    
    def get_scan_in_sector(self, 
                           center_angle: float, 
                           sector_width: float) -> List[Tuple[float, float]]:
        """
        특정 섹터의 스캔 데이터만 반환
        
        Args:
            center_angle (float): 중심 각도 (degree)
            sector_width (float): 섹터 폭 (degree)
        
        Returns:
            list: [(angle, distance), ...]
        
        Example:
            >>> scan = lidar.get_scan_in_sector(0, 30)  # 정면 ±15도
        """
        scan = self.get_latest_scan()
        
        half_width = sector_width / 2.0
        min_angle = (center_angle - half_width) % 360
        max_angle = (center_angle + half_width) % 360
        
        filtered = []
        for angle, distance in scan:
            if min_angle <= max_angle:
                if min_angle <= angle <= max_angle:
                    filtered.append((angle, distance))
            else:
                # 0도를 넘어가는 경우
                if angle >= min_angle or angle <= max_angle:
                    filtered.append((angle, distance))
        
        return filtered
    
    def get_min_distance_in_sector(self,
                                   center_angle: float,
                                   sector_width: float) -> Optional[float]:
        """
        특정 섹터에서 최소 거리 반환
        
        Args:
            center_angle (float): 중심 각도
            sector_width (float): 섹터 폭
        
        Returns:
            float or None: 최소 거리 (cm)
        """
        scan = self.get_scan_in_sector(center_angle, sector_width)
        
        if not scan:
            return None
        
        distances = [d for _, d in scan]
        return min(distances)
    
    def find_gaps(self, 
                  min_gap_width: float = 60.0,
                  min_distance: float = 50.0) -> List[Dict]:
        """
        통과 가능한 빈 공간 찾기
        
        Args:
            min_gap_width (float): 최소 간격 폭 (cm)
            min_distance (float): 최소 거리 (cm)
        
        Returns:
            list: [{'angle': float, 'distance': float, 'width': float}, ...]
        """
        scan = self.get_latest_scan()
        if not scan:
            return []
        
        gaps = []
        gap_start = None
        gap_angles = []
        
        for angle, distance in sorted(scan, key=lambda x: x[0]):
            if distance >= min_distance:
                # 빈 공간 발견
                if gap_start is None:
                    gap_start = angle
                gap_angles.append((angle, distance))
            else:
                # 장애물
                if gap_start is not None and gap_angles:
                    # 간격 계산
                    gap_end = gap_angles[-1][0]
                    gap_width_deg = gap_end - gap_start
                    
                    # 평균 거리에서의 물리적 폭 계산
                    avg_distance = sum(d for _, d in gap_angles) / len(gap_angles)
                    gap_width_cm = 2 * avg_distance * math.tan(math.radians(gap_width_deg / 2))
                    
                    if gap_width_cm >= min_gap_width:
                        center_angle = (gap_start + gap_end) / 2
                        gaps.append({
                            'angle': center_angle,
                            'distance': avg_distance,
                            'width': gap_width_cm,
                            'angle_start': gap_start,
                            'angle_end': gap_end,
                        })
                    
                    gap_start = None
                    gap_angles = []
        
        return gaps
    
    def close(self) -> None:
        """LiDAR 연결 종료"""
        self.stop_scan()
        
        if not self.mock and self._lidar:
            try:
                self._lidar.stop()
                self._lidar.stop_motor()
                self._lidar.disconnect()
            except:
                pass
        
        print("✅ LiDAR 종료")
    
    def get_stats(self) -> Dict:
        """통계 정보 반환"""
        return {
            'scan_count': self.scan_count,
            'last_scan_time': self.last_scan_time,
            'running': self._running,
            'mode': 'Mock' if self.mock else 'Real',
        }
    
    def __enter__(self):
        self.open()
        self.start_scan()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    # 테스트
    print("=== LiDAR Interface 테스트 ===\n")
    
    # Mock 모드로 테스트
    with LidarInterface(mock=True) as lidar:
        print("\n1️⃣ 5초간 스캔...")
        time.sleep(5)
        
        # 통계
        stats = lidar.get_stats()
        print(f"\n📊 통계:")
        print(f"   스캔 횟수: {stats['scan_count']}")
        print(f"   실행 중: {stats['running']}")
        
        # 최신 스캔
        print("\n2️⃣ 최신 스캔:")
        scan = lidar.get_latest_scan()
        print(f"   데이터 개수: {len(scan)}")
        if scan:
            print(f"   샘플: {scan[:5]}")
        
        # 섹터 스캔
        print("\n3️⃣ 정면 ±30도 스캔:")
        front_scan = lidar.get_scan_in_sector(0, 60)
        print(f"   데이터 개수: {len(front_scan)}")
        
        # 최소 거리
        min_dist = lidar.get_min_distance_in_sector(0, 60)
        print(f"   최소 거리: {min_dist:.1f}cm")
        
        # 빈 공간 찾기
        print("\n4️⃣ 통과 가능한 공간:")
        gaps = lidar.find_gaps(min_gap_width=60, min_distance=100)
        print(f"   발견: {len(gaps)}개")
        for i, gap in enumerate(gaps[:3]):
            print(f"   {i+1}. 각도={gap['angle']:.1f}°, "
                  f"거리={gap['distance']:.1f}cm, "
                  f"폭={gap['width']:.1f}cm")
    
    print("\n✅ 테스트 완료")
