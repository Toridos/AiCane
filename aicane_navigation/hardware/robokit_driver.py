"""
RobokitRS 하드웨어 드라이버 (블루투스 지원)
메카넘휠 제어 및 초음파 센서 인터페이스
"""

import time
import subprocess
import os


class RobokitDriver:
    """
    RobokitRS 하드웨어 제어
    
    - 메카넘휠 제어 (속도 레벨 6~15)
    - 초음파 센서 읽기 (3개: 정면/좌/우)
    - 블루투스 자동 연결 지원
    """
    
    # 초음파 센서 핀
    ULTRASONIC_PINS = {
        'front': 12,
        'left': 2,
        'right': 3,
    }
    
    def __init__(self, port=None, baudrate=9600, timeout=1.0, mock=False,
                 bluetooth_mac=None, auto_connect=True):
        """
        Args:
            port (str): 시리얼 포트 (None이면 자동 탐색)
            baudrate (int): 통신 속도
            timeout (float): 타임아웃 (초)
            mock (bool): 테스트용 Mock 모드
            bluetooth_mac (str): 블루투스 MAC 주소 (예: '98:D3:31:XX:XX:XX')
            auto_connect (bool): 블루투스 자동 연결 시도
        """
        self.baudrate = baudrate
        self.timeout = timeout
        self.mock = mock
        self.bluetooth_mac = bluetooth_mac
        
        # 현재 명령 상태 (오도메트리용)
        self.current_command = {
            'direction': 'STOP',
            'speed_level': 0,
            'start_time': time.time(),
        }
        
        # Mock 모드
        if self.mock:
            self.robot = None
            self.port = None
            print("🧪 Mock 모드로 시작")
            return
        
        # 포트 결정
        if port is None:
            # 자동 탐색
            port = self._find_serial_port(bluetooth_mac, auto_connect)
        
        self.port = port
        
        if self.port is None:
            print("⚠️ 시리얼 포트를 찾을 수 없습니다. Mock 모드로 전환합니다.")
            self.mock = True
            self.robot = None
            return
        
        # RobokitRS 연결
        self._connect_robot()
    
    def _find_serial_port(self, bluetooth_mac, auto_connect):
        """
        시리얼 포트 자동 탐색
        
        Args:
            bluetooth_mac (str): 블루투스 MAC 주소
            auto_connect (bool): 자동 연결 시도
        
        Returns:
            str: 포트 경로 또는 None
        """
        print("🔍 시리얼 포트 탐색 중...")
        
        # 1. /dev/rfcomm* 확인 (블루투스)
        for i in range(5):
            port = f'/dev/rfcomm{i}'
            if os.path.exists(port):
                print(f"✅ 블루투스 포트 발견: {port}")
                return port
        
        # 2. /dev/ttyUSB* 확인 (USB)
        for i in range(5):
            port = f'/dev/ttyUSB{i}'
            if os.path.exists(port):
                print(f"✅ USB 포트 발견: {port}")
                return port
        
        # 3. /dev/ttyACM* 확인
        for i in range(5):
            port = f'/dev/ttyACM{i}'
            if os.path.exists(port):
                print(f"✅ ACM 포트 발견: {port}")
                return port
        
        # 4. 블루투스 자동 연결 시도
        if auto_connect and bluetooth_mac:
            print(f"🔗 블루투스 연결 시도: {bluetooth_mac}")
            port = self._connect_bluetooth(bluetooth_mac)
            if port:
                return port
        
        print("❌ 사용 가능한 포트가 없습니다.")
        print("\n💡 블루투스 수동 연결 방법:")
        print("   sudo rfcomm bind 0 <MAC_ADDRESS> 1")
        print("   예: sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1")
        
        return None
    
    def _connect_bluetooth(self, mac_address):
        """
        블루투스 자동 연결
        
        Args:
            mac_address (str): MAC 주소
        
        Returns:
            str: 포트 경로 또는 None
        """
        try:
            # rfcomm 바인딩
            cmd = ['sudo', 'rfcomm', 'bind', '0', mac_address, '1']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ 블루투스 연결 성공")
                time.sleep(2)  # 연결 안정화 대기
                
                if os.path.exists('/dev/rfcomm0'):
                    return '/dev/rfcomm0'
            else:
                print(f"❌ 블루투스 연결 실패: {result.stderr}")
        
        except Exception as e:
            print(f"❌ 블루투스 연결 오류: {e}")
        
        return None
    
    def _connect_robot(self):
        """RobokitRS 라이브러리 연결"""
        try:
            from RobokitRS import RobokitRS
            
            print(f"🔌 RobokitRS 연결 시도: {self.port}")
            self.robot = RobokitRS(port=self.port)
            
            print(f"✅ RobokitRS 연결 성공: {self.port}")
            
            # 초기화 - 정지 상태로
            self.robot.set_mecanumwheels_stop()
            time.sleep(0.1)
        
        except ImportError:
            print("❌ RobokitRS 라이브러리가 설치되지 않았습니다.")
            print("   설치: pip install RobokitRS")
            self.mock = True
            self.robot = None
        
        except Exception as e:
            print(f"❌ RobokitRS 연결 실패: {e}")
            print(f"   포트: {self.port}")
            print(f"   권한 확인: sudo chmod 666 {self.port}")
            self.mock = True
            self.robot = None
    
    def set_motion(self, direction, speed_level):
        """
        로봇 모션 명령
        
        Args:
            direction (str): 'FORWARD', 'BACKWARD', 'LEFT', 'RIGHT',
                           'ROTATE_L', 'ROTATE_R', 'STOP'
            speed_level (int): 속도 레벨 (6~15, 0=정지)
        """
        # 명령 기록 (오도메트리용)
        self.current_command = {
            'direction': direction,
            'speed_level': speed_level,
            'start_time': time.time(),
        }
        
        # Mock 모드
        if self.mock:
            print(f"🤖 [Mock] 모션: {direction}, 레벨: {speed_level}")
            return
        
        # 실제 명령 전송
        try:
            if direction == 'STOP':
                self.robot.set_mecanumwheels_stop()
            
            elif direction == 'FORWARD':
                self.robot.set_mecanumwheels_drive_front(speed_level)
            
            elif direction == 'BACKWARD':
                self.robot.set_mecanumwheels_drive_back(speed_level)
            
            elif direction == 'LEFT':
                self.robot.set_mecanumwheels_drive_left(speed_level)
            
            elif direction == 'RIGHT':
                self.robot.set_mecanumwheels_drive_right(speed_level)
            
            elif direction == 'ROTATE_L':
                self.robot.set_mecanumwheels_turn_left(speed_level)
            
            elif direction == 'ROTATE_R':
                self.robot.set_mecanumwheels_turn_right(speed_level)
            
            else:
                print(f"⚠️ 알 수 없는 방향: {direction}")
        
        except Exception as e:
            print(f"❌ 모션 명령 실패: {e}")
    
    def get_ultrasonic(self):
        """
        초음파 센서 읽기
        
        Returns:
            dict: {'front': cm, 'left': cm, 'right': cm}
                  측정 실패 시 None
        """
        # Mock 모드 - 랜덤 값
        if self.mock:
            import random
            return {
                'front': random.uniform(100, 200),
                'left': random.uniform(100, 140),
                'right': random.uniform(100, 140),
            }
        
        # 실제 센서 읽기
        try:
            distances = {}
            
            for name, pin in self.ULTRASONIC_PINS.items():
                distance = self.robot.sonar_read(pin)
                
                # 유효 범위 체크 (2~200cm)
                if distance is not None and 2 <= distance <= 400:
                    distances[name] = distance
                else:
                    distances[name] = None
            
            return distances
        
        except Exception as e:
            print(f"❌ 초음파 읽기 실패: {e}")
            return {'front': None, 'left': None, 'right': None}
    
    def get_current_command(self):
        """
        현재 명령 정보 반환 (오도메트리용)
        
        Returns:
            dict: {'direction': str, 'speed_level': int, 'start_time': float}
        """
        return self.current_command.copy()
    
    def stop(self):
        """로봇 정지"""
        self.set_motion('STOP', 0)
    
    def close(self):
        """연결 종료"""
        if not self.mock and self.robot is not None:
            try:
                self.stop()
                print("✅ RobokitRS 연결 종료")
            except:
                pass
    
    @staticmethod
    def list_available_ports():
        """사용 가능한 포트 목록 출력"""
        print("\n📡 사용 가능한 포트:")
        
        found = False
        
        # 블루투스
        for i in range(5):
            port = f'/dev/rfcomm{i}'
            if os.path.exists(port):
                print(f"  - {port} (블루투스)")
                found = True
        
        # USB
        for i in range(5):
            port = f'/dev/ttyUSB{i}'
            if os.path.exists(port):
                print(f"  - {port} (USB)")
                found = True
        
        # ACM
        for i in range(5):
            port = f'/dev/ttyACM{i}'
            if os.path.exists(port):
                print(f"  - {port} (ACM)")
                found = True
        
        if not found:
            print("  (없음)")
            print("\n💡 블루투스 연결 확인:")
            print("   1. 페어링: bluetoothctl")
            print("   2. 바인딩: sudo rfcomm bind 0 <MAC> 1")
            print("   3. 권한: sudo chmod 666 /dev/rfcomm0")


if __name__ == '__main__':
    # 테스트
    print("=== RobokitDriver 블루투스 테스트 ===\n")
    
    # 포트 목록
    RobokitDriver.list_available_ports()
    
    # Mock 모드로 테스트
    print("\n" + "="*50)
    print("Mock 모드 테스트")
    print("="*50)
    
    robot = RobokitDriver(mock=True)
    
    # 모션 테스트
    print("\n모션 명령:")
    robot.set_motion('FORWARD', 10)
    time.sleep(0.5)
    robot.set_motion('ROTATE_L', 8)
    time.sleep(0.5)
    robot.set_motion('STOP', 0)
    
    # 초음파 테스트
    print("\n초음파 센서:")
    for i in range(3):
        distances = robot.get_ultrasonic()
        print(f"  측정 {i+1}: 정면={distances['front']:.1f}cm, "
              f"좌={distances['left']:.1f}cm, 우={distances['right']:.1f}cm")
        time.sleep(0.2)
    
    robot.close()
    print("\n✅ 테스트 완료")
