"""
NavigationSystem LiDAR 통합 패치
기존 코드에 추가할 내용
"""

# ============================================
# navigation_system.py 수정 사항
# ============================================

# 1. Import 추가 (파일 상단)
from .hardware import RobokitDriver, LidarInterface
from .obstacle import ObstacleAvoidanceSystem, LidarObstacleDetector

# 2. __init__에 LiDAR 초기화 추가

def __init__(self, config_dir='./config', mock=False):
    """
    Args:
        config_dir (str): 설정 파일 디렉토리
        mock (bool): Mock 모드 (테스트용)
    """
    print("🚀 AiCane Navigation System 초기화...\n")
    
    self.mock = mock
    self.config_dir = config_dir
    
    # 설정 로드
    self.config = self._load_config(config_dir)
    
    # 1️⃣ 하드웨어 초기화
    print("1️⃣ 하드웨어 연결...")
    self.robot = RobokitDriver(mock=mock)
    
    # ✅ LiDAR 초기화 (신규!)
    self.lidar = None
    self.lidar_detector = None
    self._init_lidar()
    
    # ... (기존 코드 계속)
    
    # 4️⃣ 장애물 회피 시스템 (수정!)
    print("4️⃣ 장애물 회피 시스템 구성...")
    self.obstacle_system = ObstacleAvoidanceSystem(
        self.robot,
        self.floor_map,
        self.lidar,              # ✅ LiDAR 전달
        self.lidar_detector      # ✅ LiDAR 감지기 전달
    )


# ============================================
# 3. 새로운 메서드 추가
# ============================================

def _load_config(self, config_dir):
    """설정 파일 로드"""
    import yaml
    import os
    
    config = {}
    
    # hardware.yaml
    hardware_path = os.path.join(config_dir, 'hardware.yaml')
    if os.path.exists(hardware_path):
        with open(hardware_path, 'r') as f:
            config['hardware'] = yaml.safe_load(f)
    
    # navigation.yaml
    nav_path = os.path.join(config_dir, 'navigation.yaml')
    if os.path.exists(nav_path):
        with open(nav_path, 'r') as f:
            config['navigation'] = yaml.safe_load(f)
    
    return config


def _init_lidar(self):
    """
    LiDAR 초기화
    
    hardware.yaml 설정 읽어서 LiDAR 활성화
    """
    # 설정 확인
    lidar_config = self.config.get('hardware', {}).get('lidar', {})
    enabled = lidar_config.get('enabled', False)
    
    if not enabled:
        print("   ℹ️  LiDAR 비활성화 (초음파만 사용)")
        return
    
    # Mock 모드
    if self.mock:
        print("   🧪 LiDAR Mock 모드")
        try:
            self.lidar = LidarInterface(mock=True)
            self.lidar.open()
            self.lidar.start_scan()
            
            # 감지기
            self.lidar_detector = LidarObstacleDetector(
                self.lidar,
                min_distance=50.0
            )
            
            print("   ✅ LiDAR Mock 초기화 완료")
        except Exception as e:
            print(f"   ⚠️ LiDAR Mock 초기화 실패: {e}")
            self.lidar = None
            self.lidar_detector = None
        return
    
    # 실제 LiDAR
    print("   📡 LiDAR 연결 중...")
    
    try:
        from .hardware import LidarInterface
        from .obstacle import LidarObstacleDetector
        
        # 설정 읽기
        port = lidar_config.get('port', '/dev/ttyUSB0')
        scan_rate = lidar_config.get('scan_rate', 10)
        min_distance = self.config.get('navigation', {}).get(
            'obstacle_detection', {}
        ).get('lidar', {}).get('min_distance', 50.0)
        
        # LiDAR 인터페이스
        self.lidar = LidarInterface(port=port, mock=False)
        self.lidar.open()
        self.lidar.start_scan()
        
        # 감지기
        self.lidar_detector = LidarObstacleDetector(
            self.lidar,
            min_distance=min_distance,
            scan_rate=scan_rate
        )
        
        print(f"   ✅ LiDAR 연결 완료: {port}")
        print(f"      - 최소 거리: {min_distance}cm")
        print(f"      - 스캔 속도: {scan_rate}Hz")
    
    except ImportError:
        print("   ⚠️ rplidar 라이브러리 없음")
        print("      설치: pip install rplidar-roboticia")
        self.lidar = None
        self.lidar_detector = None
    
    except Exception as e:
        print(f"   ⚠️ LiDAR 연결 실패: {e}")
        print("      초음파만 사용합니다")
        self.lidar = None
        self.lidar_detector = None


def get_lidar_status(self):
    """
    LiDAR 상태 확인
    
    Returns:
        dict: {
            'enabled': bool,
            'connected': bool,
            'scanning': bool,
            'latest_scan': list or None
        }
    """
    if not self.lidar:
        return {
            'enabled': False,
            'connected': False,
            'scanning': False,
            'latest_scan': None
        }
    
    try:
        scan = self.lidar.get_latest_scan()
        
        return {
            'enabled': True,
            'connected': True,
            'scanning': len(scan) > 0,
            'latest_scan': scan,
            'num_points': len(scan)
        }
    except:
        return {
            'enabled': True,
            'connected': False,
            'scanning': False,
            'latest_scan': None
        }


def close(self):
    """
    시스템 종료
    
    모든 하드웨어 안전하게 종료
    """
    print("\n🛑 시스템 종료 중...")
    
    # 로봇 정지
    try:
        self.robot.stop()
        self.robot.close()
        print("   ✅ 로봇 정지")
    except:
        pass
    
    # LiDAR 종료
    if self.lidar:
        try:
            self.lidar.stop_scan()
            self.lidar.close()
            print("   ✅ LiDAR 종료")
        except:
            pass
    
    print("✅ 시스템 종료 완료")


# ============================================
# 사용 예제
# ============================================

if __name__ == '__main__':
    # 기본 사용
    nav = NavigationSystem(config_dir='./config')
    
    # LiDAR 상태 확인
    lidar_status = nav.get_lidar_status()
    print(f"\nLiDAR 상태: {lidar_status}")
    
    # 주행
    try:
        nav.navigate_rooms('101호', '107호')
    finally:
        nav.close()
