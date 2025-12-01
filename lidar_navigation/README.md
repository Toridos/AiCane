"""
# LiDAR Navigation System

## 설치
```bash
# 1. RobokitRS.py 복사
cp ../path/to/RobokitRS.py utils/

# 2. ROS2 패키지 생성 (선택)
# 또는 Python 단독 실행 가능

# 3. 권한 설정
sudo chmod 666 /dev/ttyUSB*
```

## 실행

### Python 단독 실행
```bash
# 터미널 1
python3 nodes/robokit_driver_node.py

# 터미널 2
python3 nodes/localization_node.py

# 터미널 3
python3 nodes/controller_node.py

# 터미널 4
python3 nodes/path_manager.py
```

### ROS2 실행 (권장)
```bash
ros2 launch lidar_navigation navigation.launch.py
```

## 설정 수정
`config.py` 파일에서 모든 설정 변경 가능

## 테스트
```bash
# 센서 확인
python3 -c "
import sys
sys.path.insert(0, 'utils')
from RobokitRS import RobokitRS
r = RobokitRS()
r.port_open('/dev/ttyUSB0')
r.sonar_begin(2)
print(r.sonar_read(2))
"
```
"""