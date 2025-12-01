"""
속도 프로파일 관리
속도 레벨 ↔ 실제 속도 (m/s, rad/s) 변환
"""

import json
import os


class SpeedProfile:
    """
    로봇 속도 레벨과 실제 속도 간 매핑
    
    실측 데이터 기반:
    - 레벨 14: 전진 0.0947 m/s, 회전 0.94 rad/s
    - 레벨 8: 전진 0.054 m/s, 회전 0.536 rad/s
    - 레벨 6~: 선형 보간
    - 레벨 5 이하: Dead Zone (작동 안 함)
    """
    
    # 실측 데이터 (캘리브레이션 결과)
    MEASURED_DATA = {
        8: {
            'forward': 0.054,   # m/s
            'rotate': 0.536,    # rad/s
            'lateral': 0.049,   # m/s (측면)
        },
        14: {
            'forward': 0.0947,  # m/s
            'rotate': 0.94,     # rad/s
            'lateral': 0.085,   # m/s
        },
    }
    
    # 최소 작동 레벨
    MIN_WORKING_LEVEL = 6  # 6 미만은 파워 부족
    MAX_LEVEL = 15
    
    @classmethod
    def get_speed(cls, level, motion_type='forward'):
        """
        속도 레벨 → 실제 속도
        
        Args:
            level (int): 속도 레벨 (6~15)
            motion_type (str): 'forward', 'rotate', 'lateral'
        
        Returns:
            float: 실제 속도 (m/s 또는 rad/s)
        
        Example:
            >>> SpeedProfile.get_speed(10, 'forward')
            0.0687  # m/s
        """
        # Dead Zone
        if level < cls.MIN_WORKING_LEVEL:
            return 0.0
        
        # 범위 제한
        level = max(cls.MIN_WORKING_LEVEL, min(cls.MAX_LEVEL, level))
        
        # 실측 데이터에 정확히 일치
        if level in cls.MEASURED_DATA:
            return cls.MEASURED_DATA[level].get(motion_type, 0.0)
        
        # 선형 보간
        if level < 8:
            # 레벨 6~8 구간
            lower_level = cls.MIN_WORKING_LEVEL
            upper_level = 8
            
            # 레벨 6 속도 추정 (레벨 8의 70% 정도로 가정)
            lower_speed = cls.MEASURED_DATA[8][motion_type] * 0.7
            upper_speed = cls.MEASURED_DATA[8][motion_type]
            
        else:
            # 레벨 8~14 구간
            lower_level = 8
            upper_level = 14
            
            lower_speed = cls.MEASURED_DATA[8][motion_type]
            upper_speed = cls.MEASURED_DATA[14][motion_type]
        
        # 선형 보간
        ratio = (level - lower_level) / (upper_level - lower_level)
        speed = lower_speed + ratio * (upper_speed - lower_speed)
        
        return speed
    
    @classmethod
    def get_level_for_speed(cls, target_speed, motion_type='forward'):
        """
        목표 속도 → 속도 레벨
        
        Args:
            target_speed (float): 목표 속도 (m/s 또는 rad/s)
            motion_type (str): 'forward', 'rotate', 'lateral'
        
        Returns:
            int: 속도 레벨 (6~15)
        
        Example:
            >>> SpeedProfile.get_level_for_speed(0.07, 'forward')
            10
        """
        # 최소 레벨
        if target_speed <= 0:
            return 0
        
        min_speed = cls.get_speed(cls.MIN_WORKING_LEVEL, motion_type)
        if target_speed < min_speed:
            return cls.MIN_WORKING_LEVEL
        
        # 최대 레벨
        max_speed = cls.get_speed(cls.MAX_LEVEL, motion_type)
        if target_speed >= max_speed:
            return cls.MAX_LEVEL
        
        # 레벨 8~14 구간인지 확인
        speed_8 = cls.MEASURED_DATA[8][motion_type]
        speed_14 = cls.MEASURED_DATA[14][motion_type]
        
        if target_speed >= speed_8:
            # 레벨 8~14
            ratio = (target_speed - speed_8) / (speed_14 - speed_8)
            level = 8 + ratio * (14 - 8)
        else:
            # 레벨 6~8
            speed_6 = cls.get_speed(cls.MIN_WORKING_LEVEL, motion_type)
            ratio = (target_speed - speed_6) / (speed_8 - speed_6)
            level = cls.MIN_WORKING_LEVEL + ratio * (8 - cls.MIN_WORKING_LEVEL)
        
        return int(round(level))
    
    @classmethod
    def load_calibration(cls, filename):
        """
        캘리브레이션 데이터 로드
        
        Args:
            filename (str): JSON 파일 경로
        
        Example:
            >>> SpeedProfile.load_calibration('./config/calibration.json')
        """
        if not os.path.exists(filename):
            print(f"⚠️ 캘리브레이션 파일 없음: {filename}")
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # 데이터 업데이트
            for level_str, speeds in data.items():
                level = int(level_str)
                cls.MEASURED_DATA[level] = speeds
            
            print(f"✅ 캘리브레이션 로드 완료: {filename}")
            print(f"   레벨: {sorted(cls.MEASURED_DATA.keys())}")
            
        except Exception as e:
            print(f"❌ 캘리브레이션 로드 실패: {e}")
    
    @classmethod
    def save_calibration(cls, filename):
        """
        캘리브레이션 데이터 저장
        
        Args:
            filename (str): JSON 파일 경로
        """
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump(cls.MEASURED_DATA, f, indent=2)
            
            print(f"✅ 캘리브레이션 저장 완료: {filename}")
            
        except Exception as e:
            print(f"❌ 캘리브레이션 저장 실패: {e}")


if __name__ == '__main__':
    # 테스트
    print("=== 속도 프로파일 테스트 ===\n")
    
    # 레벨 → 속도
    print("📊 레벨별 속도:")
    for level in [6, 8, 10, 12, 14, 15]:
        forward = SpeedProfile.get_speed(level, 'forward')
        rotate = SpeedProfile.get_speed(level, 'rotate')
        print(f"  레벨 {level:2d}: 전진 {forward:.4f} m/s, 회전 {rotate:.4f} rad/s")
    
    print("\n🎯 속도 → 레벨:")
    test_speeds = [0.05, 0.07, 0.09]
    for speed in test_speeds:
        level = SpeedProfile.get_level_for_speed(speed, 'forward')
        actual = SpeedProfile.get_speed(level, 'forward')
        print(f"  목표 {speed:.3f} m/s → 레벨 {level} (실제 {actual:.4f} m/s)")
