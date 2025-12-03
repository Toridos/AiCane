"""
RobokitRS 하드웨어 드라이버 (개선 통합 버전)
블루투스 자동 연결 + 센서 초기화 + 에러 처리
"""

import time
import subprocess
import os


class RobokitDriver:
    """
    RobokitRS 하드웨어 제어 (개선 버전)
    
    팀원 제안 + 블루투스 기능 통합
    """
    
    # 초음파 센서 핀 (실제 배선에 맞게 수정 필요!)
    ULTRASONIC_PINS = {
        'front': 12,  # ← 실제 배선 확인 필요!
        'left': 2,
        'right': 3,
    }
    
    def __init__(self, 
                 port=None,
                 baudrate=115200,
                 timeout=1.0, 
                 mock=False,
                 bluetooth_mac=None,
                 auto_connect=True):
        """
        Args:
            port (str): 시리얼 포트 (None이면 자동 탐색)
            baudrate (int): 통신 속도
            timeout (float): 타임아웃
            mock (bool): Mock 모드
            bluetooth_mac (str): 블루투스 MAC 주소
            auto_connect (bool): 자동 연결
        """
        self.baudrate = baudrate
        self.timeout = timeout
        self.mock = mock
        self.bluetooth_mac = bluetooth_mac
        
        # 현재 명령 상태
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
        """시리얼 포트 자동 탐색"""
        print("🔍 시리얼 포트 탐색 중...")
        
        # 1. /dev/rfcomm* (블루투스)
        for i in range(5):
            port = f'/dev/rfcomm{i}'
            if os.path.exists(port):
                print(f"✅ 블루투스 포트 발견: {port}")
                return port
        
        # 2. /dev/ttyUSB*
        for i in range(5):
            port = f'/dev/ttyUSB{i}'
            if os.path.exists(port):
                print(f"✅ USB 포트 발견: {port}")
                return port
        
        # 3. /dev/ttyACM*
        for i in range(5):
            port = f'/dev/ttyACM{i}'
            if os.path.exists(port):
                print(f"✅ ACM 포트 발견: {port}")
                return port
        
        # 4. 블루투스 자동 연결
        if auto_connect and bluetooth_mac:
            print(f"🔗 블루투스 연결 시도: {bluetooth_mac}")
            port = self._connect_bluetooth(bluetooth_mac)
            if port:
                return port
        
        return None
    
    def _connect_bluetooth(self, mac_address):
        """블루투스 자동 연결"""
        try:
            cmd = ['sudo', 'rfcomm', 'bind', '0', mac_address, '1']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ 블루투스 연결 성공")
                time.sleep(2)
                
                if os.path.exists('/dev/rfcomm0'):
                    return '/dev/rfcomm0'
            else:
                print(f"❌ 블루투스 연결 실패: {result.stderr}")
        
        except Exception as e:
            print(f"❌ 블루투스 연결 오류: {e}")
        
        return None
    
    def _connect_robot(self):
        """
        RobokitRS 라이브러리 연결
        
        두 가지 방식 모두 시도:
        1. from RobokitRS import RobokitRS
        2. from RobokitRS.RobokitRS import RobokitRS
        """
        try:
            # 방법 1 시도
            try:
                from RobokitRS import RobokitRS
                print("📦 RobokitRS 라이브러리 로드 (방법 1)")
                
                # 생성자에 포트 전달 방식
                try:
                    self.robot = RobokitRS(port=self.port)
                    print(f"✅ RobokitRS 연결 성공 (생성자): {self.port}")
                except:
                    # 분리된 초기화 방식
                    self.robot = RobokitRS()
                    self.robot.port_open(self.port)
                    print(f"✅ RobokitRS 연결 성공 (port_open): {self.port}")
            
            except ImportError:
                # 방법 2 시도
                from RobokitRS.RobokitRS import RobokitRS
                print("📦 RobokitRS 라이브러리 로드 (방법 2)")
                
                self.robot = RobokitRS()
                self.robot.port_open(self.port)
                print(f"✅ RobokitRS 연결 성공: {self.port}")
            
            # 초음파 센서 초기화
            self._init_sensors()
            
            # 초기 정지 상태
            self._initial_stop()
            
        except ImportError:
            print("❌ RobokitRS 라이브러리가 설치되지 않았습니다.")
            print("   설치: pip install RobokitRS")
            self.mock = True
            self.robot = None
        
        except Exception as e:
            print(f"❌ RobokitRS 연결 실패: {e}")
            print(f"   포트: {self.port}")
            self.mock = True
            self.robot = None
    
    def _init_sensors(self):
        """초음파 센서 초기화 (필요 시)"""
        try:
            # sonar_begin이 있는지 확인
            if hasattr(self.robot, 'sonar_begin'):
                print("🔧 초음파 센서 초기화 중...")
                for name, pin in self.ULTRASONIC_PINS.items():
                    self.robot.sonar_begin(pin)
                    print(f"   ✓ {name} (핀 {pin})")
            else:
                print("ℹ️  초음파 센서 자동 초기화 (sonar_begin 불필요)")
        
        except Exception as e:
            print(f"⚠️ 센서 초기화 경고: {e}")
    
    def _initial_stop(self):
        """초기 정지 상태로 설정"""
        try:
            # 여러 정지 메서드 시도
            if hasattr(self.robot, 'set_mecanumwheels_stop'):
                self.robot.set_mecanumwheels_stop()
            elif hasattr(self.robot, 'set_mecanumwheels_drive_stop'):
                self.robot.set_mecanumwheels_drive_stop()
            
            time.sleep(0.1)
            print("✅ 초기 정지 상태")
        
        except Exception as e:
            print(f"⚠️ 정지 명령 경고: {e}")
    
    def set_motion(self, direction, speed_level):
        """
        로봇 모션 명령
        
        여러 API 버전 대응
        """
        # 명령 기록
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
                self._send_stop()
            elif direction == 'FORWARD':
                self._send_forward(speed_level)
            elif direction == 'BACKWARD':
                self._send_backward(speed_level)
            elif direction == 'LEFT':
                self._send_left(speed_level)
            elif direction == 'RIGHT':
                self._send_right(speed_level)
            elif direction == 'ROTATE_L':
                self._send_rotate_left(speed_level)
            elif direction == 'ROTATE_R':
                self._send_rotate_right(speed_level)
            else:
                print(f"⚠️ 알 수 없는 방향: {direction}")
        
        except Exception as e:
            print(f"❌ 모션 명령 실패: {e}")
    
    # API 호환성을 위한 헬퍼 메서드
    def _send_stop(self):
        """정지 (여러 API 대응)"""
        if hasattr(self.robot, 'set_mecanumwheels_stop'):
            self.robot.set_mecanumwheels_stop()
        elif hasattr(self.robot, 'set_mecanumwheels_drive_stop'):
            self.robot.set_mecanumwheels_drive_stop()
    
    def _send_forward(self, speed):
        if hasattr(self.robot, 'set_mecanumwheels_drive_front'):
            self.robot.set_mecanumwheels_drive_front(speed)
        elif hasattr(self.robot, 'set_mecanumwheels_front'):
            self.robot.set_mecanumwheels_front(speed)
    
    def _send_backward(self, speed):
        if hasattr(self.robot, 'set_mecanumwheels_drive_back'):
            self.robot.set_mecanumwheels_drive_back(speed)
        elif hasattr(self.robot, 'set_mecanumwheels_back'):
            self.robot.set_mecanumwheels_back(speed)
    
    def _send_left(self, speed):
        if hasattr(self.robot, 'set_mecanumwheels_drive_left'):
            self.robot.set_mecanumwheels_drive_left(speed)
        elif hasattr(self.robot, 'set_mecanumwheels_left'):
            self.robot.set_mecanumwheels_left(speed)
    
    def _send_right(self, speed):
        if hasattr(self.robot, 'set_mecanumwheels_drive_right'):
            self.robot.set_mecanumwheels_drive_right(speed)
        elif hasattr(self.robot, 'set_mecanumwheels_right'):
            self.robot.set_mecanumwheels_right(speed)
    
    def _send_rotate_left(self, speed):
        if hasattr(self.robot, 'set_mecanumwheels_turn_left'):
            self.robot.set_mecanumwheels_turn_left(speed)
        elif hasattr(self.robot, 'set_mecanumwheels_rotate_left'):
            self.robot.set_mecanumwheels_rotate_left(speed)
    
    def _send_rotate_right(self, speed):
        if hasattr(self.robot, 'set_mecanumwheels_turn_right'):
            self.robot.set_mecanumwheels_turn_right(speed)
        elif hasattr(self.robot, 'set_mecanumwheels_rotate_right'):
            self.robot.set_mecanumwheels_rotate_right(speed)
    
    def get_ultrasonic(self):
        """초음파 센서 읽기"""
        # Mock 모드
        if self.mock:
            import random
            return {
                'front': random.uniform(100, 200),
                'left': random.uniform(100, 140),
                'right': random.uniform(100, 140),
            }
        
        # 실제 센서
        try:
            distances = {}
            
            for name, pin in self.ULTRASONIC_PINS.items():
                distance = self.robot.sonar_read(pin)
                
                # None 처리
                if distance is None:
                    distance = 0.0
                
                # 유효 범위 체크
                if 2 <= distance <= 400:
                    distances[name] = distance
                else:
                    distances[name] = None
            
            return distances
        
        except Exception as e:
            print(f"❌ 초음파 읽기 실패: {e}")
            return {'front': None, 'left': None, 'right': None}
    
    def get_current_command(self):
        """현재 명령 정보"""
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
        """사용 가능한 포트 목록"""
        print("\n📡 사용 가능한 포트:")
        
        found = False
        
        for i in range(5):
            port = f'/dev/rfcomm{i}'
            if os.path.exists(port):
                print(f"  - {port} (블루투스)")
                found = True
        
        for i in range(5):
            port = f'/dev/ttyUSB{i}'
            if os.path.exists(port):
                print(f"  - {port} (USB)")
                found = True
        
        for i in range(5):
            port = f'/dev/ttyACM{i}'
            if os.path.exists(port):
                print(f"  - {port} (ACM)")
                found = True
        
        if not found:
            print("  (없음)")


if __name__ == '__main__':
    # 테스트
    print("=== RobokitDriver 통합 테스트 ===\n")
    
    # 포트 목록
    RobokitDriver.list_available_ports()
    
    # Mock 모드 테스트
    print("\n" + "="*50)
    print("Mock 모드 테스트")
    print("="*50)
    
    robot = RobokitDriver(mock=True)
    
    # 모션
    print("\n모션 명령:")
    robot.set_motion('FORWARD', 10)
    time.sleep(0.5)
    robot.set_motion('STOP', 0)
    
    # 초음파
    print("\n초음파 센서:")
    for i in range(3):
        distances = robot.get_ultrasonic()
        print(f"  측정 {i+1}: 정면={distances['front']:.1f}cm, "
              f"좌={distances['left']:.1f}cm, 우={distances['right']:.1f}cm")
        time.sleep(0.2)
    
    robot.close()
    print("\n✅ 테스트 완료")
