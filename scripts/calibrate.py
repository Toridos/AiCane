# 실행 스크립트-캘리브레이션
#!/usr/bin/env python3
"""
속도 캘리브레이션
"""
from aicane_navigation.hardware import RobokitDriver
from aicane_navigation.hardware import RPLidarX4ProInterface
from aicane_navigation.core import SpeedProfile

def calibrate_all_levels():
    robot = RobokitDriver()
    lidar = RPLidarX4ProInterface()
    
    results = {}
    
    for level in [6, 8, 10, 12, 14, 15]:
        print(f"\n=== 레벨 {level} 캘리브레이션 ===")
        
        # 전진
        forward_speed = calibrate_forward(robot, lidar, level)
        
        # 회전
        rotate_speed = calibrate_rotate(robot, lidar, level)
        
        results[level] = {
            'forward': forward_speed,
            'rotate': rotate_speed
        }
    
    # 저장
    SpeedProfile.save_calibration('./config/calibration.yaml', results)
    print("\n✅ 캘리브레이션 완료!")

if __name__ == '__main__':
    calibrate_all_levels()