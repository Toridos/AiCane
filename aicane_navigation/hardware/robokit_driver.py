"""
RobokitRS 하드웨어 드라이버
메카넘휠 제어 및 초음파 센서 인터페이스
"""

import time


class RobokitDriver:
    """
    RobokitRS 하드웨어 제어
    
    - 메카넘휠 제어 (속도 레벨 6~15)
    - 초음파 센서 읽기 (3개: 정면/좌/우)
    - 블루투스 통신
    """
    
    # 초음파 센서 핀
    ULTRASONIC_PINS = {
        'front': 12,
        'left': 2,
        'right': 3,
    }
    
    def __init__(self, port='COM3', baudrate=9600, timeout=1.0, mock=False):
        """
        Args:
            port (str): 시리얼 포트
            baudrate (int): 통신 속도
            timeout (float): 타임아웃 (초)
            mock (bool): 테스트용 Mock 모드
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.mock = mock
        
        # 현재 명령 상태 (오도메트리용)
        self.current_command = {
            'direction': 'STOP',
            'speed_level': 0,
            'start_time': time.time(),
        }
        
        # Mock 모드가 아니면 실제 연결
        if not self.mock:
            try:
                from RobokitRS import RobokitRS
                self.robot = RobokitRS(port=port)
                print(f"✅ RobokitRS 연결 성공: {port}")
            except Exception as e:
                print(f"⚠️ RobokitRS 연결 실패: {e}")
                print("   Mock 모드로 전환합니다.")
                self.mock = True
                self.robot = None
        else:
            self.robot = None
            print("🧪 Mock 모드로 시작")
    
    def set_motion(self, direction, speed_level):
        """
        로봇 모션 명령
        
        Args:
            direction (str): 'FORWARD', 'BACKWARD', 'LEFT', 'RIGHT',
                           'ROTATE_L', 'ROTATE_R', 'STOP'
            speed_level (int): 속도 레벨 (6~15, 0=정지)
        
        Example:
            >>> robot = RobokitDriver(mock=True)
            >>> robot.set_motion('FORWARD', 10)
            >>> robot.set_motion('ROTATE_L', 8)
            >>> robot.set_motion('STOP', 0)
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
        
        Example:
            >>> robot = RobokitDriver(mock=True)
            >>> distances = robot.get_ultrasonic()
            >>> print(distances['front'])
            120.5
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
        """
        로봇 정지
        """
        self.set_motion('STOP', 0)
    
    def close(self):
        """
        연결 종료
        """
        if not self.mock:
            try:
                self.stop()
                print("✅ RobokitRS 연결 종료")
            except:
                pass


if __name__ == '__main__':
    # 테스트
    print("=== RobokitDriver 테스트 ===\n")
    
    # Mock 모드로 테스트
    robot = RobokitDriver(mock=True)
    
    # 모션 테스트
    print("1️⃣ 모션 명령 테스트:")
    robot.set_motion('FORWARD', 10)
    time.sleep(0.5)
    robot.set_motion('ROTATE_L', 8)
    time.sleep(0.5)
    robot.set_motion('STOP', 0)
    
    # 초음파 테스트
    print("\n2️⃣ 초음파 센서 테스트:")
    for i in range(3):
        distances = robot.get_ultrasonic()
        print(f"   측정 {i+1}: 정면={distances['front']:.1f}cm, "
              f"좌={distances['left']:.1f}cm, 우={distances['right']:.1f}cm")
        time.sleep(0.2)
    
    # 명령 이력
    print("\n3️⃣ 현재 명령:")
    cmd = robot.get_current_command()
    print(f"   방향: {cmd['direction']}, 레벨: {cmd['speed_level']}")
    
    robot.close()
    print("\n✅ 테스트 완료")
