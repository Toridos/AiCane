# LiDAR 사용 가이드 🔍

RPLidar X4 Pro를 AiCane Navigation에서 사용하는 방법

---

## 📦 **설치**

### 1. rplidar 라이브러리 설치
```bash
pip3 install rplidar-roboticia
```

### 2. 권한 설정
```bash
# LiDAR USB 포트 권한
sudo chmod 666 /dev/ttyUSB0

# 영구 설정 (추천)
sudo usermod -a -G dialout $USER
# 재부팅 필요
```

---

## 🔌 **하드웨어 연결**

### USB 연결
```
RPLidar X4 Pro → USB → 라즈베리파이

포트: /dev/ttyUSB0 (보통)
또는: /dev/ttyUSB1, /dev/ttyACM0 등
```

### 포트 확인
```bash
ls -l /dev/ttyUSB* /dev/ttyACM*

# 또는
dmesg | grep tty
```

---

## 🚀 **기본 사용법**

### 1. Mock 모드 테스트 (LiDAR 없이)
```python
from aicane_navigation.hardware import LidarInterface
import time

# Mock 모드로 생성
lidar = LidarInterface(mock=True)
lidar.open()
lidar.start_scan()

# 5초 대기
time.sleep(5)

# 스캔 데이터 가져오기
scan = lidar.get_latest_scan()
print(f"스캔 데이터: {len(scan)}개")
print(f"샘플: {scan[:5]}")

lidar.close()
```

### 2. 실제 LiDAR 사용
```python
from aicane_navigation.hardware import LidarInterface

# 실제 모드로 생성
lidar = LidarInterface(port='/dev/ttyUSB0', mock=False)
lidar.open()
lidar.start_scan()

# 최신 스캔
scan = lidar.get_latest_scan()

# 정면 ±30도만
front_scan = lidar.get_scan_in_sector(center_angle=0, sector_width=60)

# 최소 거리
min_dist = lidar.get_min_distance_in_sector(0, 60)
print(f"정면 최소 거리: {min_dist:.1f}cm")

lidar.close()
```

### 3. Context Manager 사용 (추천)
```python
from aicane_navigation.hardware import LidarInterface

with LidarInterface(port='/dev/ttyUSB0') as lidar:
    # 자동으로 open()과 start_scan() 호출됨
    
    scan = lidar.get_latest_scan()
    print(f"스캔: {len(scan)}개")
    
    # 자동으로 close() 호출됨
```

---

## 🎯 **주요 기능**

### 1. 전체 360도 스캔
```python
scan = lidar.get_latest_scan()
# 반환: [(angle_deg, distance_cm), ...]

for angle, distance in scan:
    print(f"{angle:.1f}도: {distance:.1f}cm")
```

### 2. 특정 섹터 스캔
```python
# 정면 ±30도
front = lidar.get_scan_in_sector(center_angle=0, sector_width=60)

# 좌측 ±15도
left = lidar.get_scan_in_sector(center_angle=90, sector_width=30)

# 우측 ±15도
right = lidar.get_scan_in_sector(center_angle=270, sector_width=30)
```

### 3. 최소 거리 찾기
```python
# 정면 최소 거리 (장애물 감지)
min_dist = lidar.get_min_distance_in_sector(
    center_angle=0,
    sector_width=60
)

if min_dist and min_dist < 50:
    print("⚠️ 정면 장애물!")
```

### 4. 빈 공간 찾기 (회피 경로)
```python
# 통과 가능한 공간 찾기
gaps = lidar.find_gaps(
    min_gap_width=60.0,   # 최소 60cm 폭
    min_distance=50.0      # 최소 50cm 거리
)

for gap in gaps:
    print(f"각도: {gap['angle']:.1f}°")
    print(f"거리: {gap['distance']:.1f}cm")
    print(f"폭: {gap['width']:.1f}cm")
```

### 5. 통계 정보
```python
stats = lidar.get_stats()
print(f"스캔 횟수: {stats['scan_count']}")
print(f"최근 스캔: {stats['last_scan_time']}")
print(f"모드: {stats['mode']}")
```

---

## 🔧 **고급 사용**

### 장애물 회피에 활용
```python
from aicane_navigation.hardware import LidarInterface

with LidarInterface() as lidar:
    # 정면 체크
    front_min = lidar.get_min_distance_in_sector(0, 60)
    
    if front_min and front_min < 50:
        # 장애물 발견! 회피 경로 찾기
        gaps = lidar.find_gaps(min_gap_width=60)
        
        if gaps:
            # 가장 가까운 빈 공간으로 회피
            best_gap = min(gaps, key=lambda g: abs(g['angle']))
            print(f"회피 각도: {best_gap['angle']:.1f}°")
```

### Tier 3 비상 위치 복구
```python
from aicane_navigation.hardware import LidarInterface
from aicane_navigation.localization import LidarMapMatcher
from aicane_navigation.mapping import FloorPlan

lidar = LidarInterface()
lidar.open()
lidar.start_scan()

floor_map = FloorPlan()
matcher = LidarMapMatcher(lidar, floor_map)

# 스캔 대기
import time
time.sleep(1)

# 위치 추정
scan = lidar.get_latest_scan()
x, y, theta, confidence = matcher.estimate_position_full_search(scan)

print(f"추정 위치: ({x:.1f}, {y:.1f})")
print(f"신뢰도: {confidence:.2f}")

lidar.close()
```

---

## 📊 **성능**

### 스캔 속도
- **실제 LiDAR**: ~20Hz (초당 20회)
- **Mock 모드**: ~20Hz (동일)

### 데이터 크기
- **360개 포인트** (1도 간격)
- **메모리**: ~5KB per scan

### CPU 사용률
- **백그라운드 스캔**: ~5%
- **전체 맵 매칭**: ~20-30% (Tier 3 비상)

---

## ⚠️ **주의사항**

### 1. 스레드 안전
```python
# ✅ 올바른 사용
with LidarInterface() as lidar:
    scan = lidar.get_latest_scan()  # 스레드 안전

# ❌ 잘못된 사용
lidar = LidarInterface()
# start_scan() 없이 get_latest_scan() 호출 → 빈 리스트
```

### 2. Mock 모드 vs 실제 모드
```python
# Mock 모드 (테스트용)
lidar = LidarInterface(mock=True)
# → 랜덤 데이터 생성, rplidar 라이브러리 불필요

# 실제 모드
lidar = LidarInterface(port='/dev/ttyUSB0', mock=False)
# → 실제 센서 필요, rplidar 라이브러리 필요
```

### 3. 포트 충돌
```python
# 이미 사용 중인 포트
# → 다른 프로그램 종료 필요

# 포트 사용 확인
lsof /dev/ttyUSB0
```

---

## 🐛 **문제 해결**

### 문제 1: "Permission denied"
```bash
sudo chmod 666 /dev/ttyUSB0
```

### 문제 2: "rplidar 모듈 없음"
```bash
pip3 install rplidar-roboticia
```

### 문제 3: 데이터가 안 들어옴
```python
# start_scan() 호출 확인
lidar.start_scan()

# 1초 대기
import time
time.sleep(1)

# 통계 확인
stats = lidar.get_stats()
print(stats)
```

### 문제 4: Mock 모드로 자동 전환됨
```python
# rplidar 라이브러리 설치 확인
pip3 list | grep rplidar

# 포트 확인
ls -l /dev/ttyUSB*

# 권한 확인
groups  # dialout이 있어야 함
```

---

## 📚 **예제 코드**

### 완전한 예제
```python
#!/usr/bin/env python3
from aicane_navigation.hardware import LidarInterface
import time

def main():
    # LiDAR 초기화
    with LidarInterface(port='/dev/ttyUSB0') as lidar:
        print("LiDAR 시작...")
        
        # 3초간 스캔
        for i in range(15):  # 20Hz x 15 = 3초
            # 최신 스캔
            scan = lidar.get_latest_scan()
            
            # 정면 최소 거리
            front_min = lidar.get_min_distance_in_sector(0, 60)
            
            # 빈 공간
            gaps = lidar.find_gaps(min_gap_width=60)
            
            print(f"[{i+1}] 스캔: {len(scan)}개, "
                  f"정면: {front_min:.1f}cm, "
                  f"빈공간: {len(gaps)}개")
            
            time.sleep(0.05)  # 20Hz
        
        # 통계
        stats = lidar.get_stats()
        print(f"\n총 스캔: {stats['scan_count']}회")

if __name__ == '__main__':
    main()
```

---

## 🎯 **통합 사용 (NavigationSystem)**

```python
from aicane_navigation import NavigationSystem

# LiDAR 포함 시스템
nav = NavigationSystem()

# 자동으로:
# 1. LiDAR 자동 감지
# 2. Tier 3 비상 모드 활성화
# 3. 길 잃으면 LiDAR로 위치 복구

nav.navigate_rooms('101호', '107호')
```

---

## 📝 **요약**

- ✅ **Mock 모드**: 테스트용, rplidar 불필요
- ✅ **실제 모드**: rplidar 라이브러리 필요
- ✅ **Context Manager**: 자동 open/close
- ✅ **백그라운드 스캔**: 스레드 안전
- ✅ **다양한 기능**: 섹터, 최소거리, 빈공간

**LiDAR는 선택사항이지만, 있으면 Tier 3 비상 복구가 가능합니다!** 🚀
