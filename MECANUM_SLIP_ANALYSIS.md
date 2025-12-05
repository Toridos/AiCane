# 🔧 메카넘휠 제어 및 미끄러짐 보정 분석

## 🎯 **핵심 질문**

### **Q1: RS CPU 보드에서 라즈베리파이 명령을 받고 실제 작동하는거 잘 구현되어 있어?**
### **Q2: 미끄러지면 각도를 얼마나 틀고 직진해야 원하는 포인트에 도달하는지 계산해서 전달해주고 있니?**

---

## 📊 **현재 구현 상태**

### **1. RS CPU 보드 제어** ⭐⭐ (기본 구현됨)

#### **robokit_driver.py:**
```python
✅ 구현된 기능:
- 블루투스 연결 (rfcomm)
- 메카넘휠 명령 전송
  - FORWARD, BACKWARD
  - LEFT, RIGHT (메카넘휠 횡이동)
  - ROTATE_L, ROTATE_R
  - STOP
- 속도 레벨 (6~15)
- 초음파 센서 읽기

✅ 명령 흐름:
라즈베리파이 → 블루투스 → RS CPU → 메카넘휠 모터
```

**코드:**
```python
def set_motion(self, direction, speed_level):
    if direction == 'FORWARD':
        self.robot.set_mecanumwheels_drive_front(speed_level)
    elif direction == 'LEFT':
        self.robot.set_mecanumwheels_drive_left(speed_level)
    # ... 등등
```

**→ 기본 제어는 잘 작동합니다!** ✅

---

### **2. 미끄러짐 보정** ❌❌ (구현 안 됨!)

#### **현재 상황:**
```python
❌ 미끄러짐 감지만 있음 (판별만)
❌ 보정 계산 없음
❌ 각도 조정 없음
❌ 피드백 제어 없음
```

#### **odometry.py:**
```python
# 단순 추측 항법만 (Dead Reckoning)
def update_from_command(self, direction, speed_level, duration):
    # 명령 → 예상 이동 거리 계산
    # ❌ 실제 이동 거리 확인 없음!
    # ❌ 미끄러짐 감지 없음!
    # ❌ 보정 없음!
```

#### **waypoint_follower.py:**
```python
# 실시간 재계획 방식
def follow_step(self):
    # 1. 현재 위치 읽기
    x, y, theta = self.loc.update()
    
    # 2. 목표와 비교
    dx = target_x - x
    dy = target_y - y
    
    # 3. 새로 계산해서 명령
    # ✅ 매 루프마다 재계산 (간접 보정)
    # ❌ 명시적 미끄러짐 보정 없음
```

**→ 명시적 미끄러짐 보정 없습니다!** ❌

---

## 🔍 **문제점 상세 분석**

### **문제 1: 미끄러짐 계산 없음** ❌

**시나리오:**
```
목표: (100, 0)으로 이동
명령: FORWARD 10 레벨

예상 이동: 7cm
실제 이동: 5cm (미끄러짐!)

현재 시스템:
- ❌ 미끄러짐 크기 계산 안 함
- ❌ 보정량 계산 안 함
- ❌ 다음 명령에 반영 안 함
```

---

### **문제 2: 각도 보정 없음** ❌

**시나리오:**
```
목표: 직진
명령: FORWARD 10 레벨

예상: 0도 방향 직진
실제: 5도 틀어짐 (바닥 마찰, 모터 불균형)

현재 시스템:
- ❌ 방향 오차 계산 안 함
- ❌ 각도 틀기 보정 안 함
```

---

### **문제 3: 횡방향 미끄러짐 보정 없음** ❌

**메카넘휠 특성:**
```
메카넘휠은 횡방향 미끄러짐이 크다!

예: LEFT 명령
→ 완전 횡이동이 아니라
→ 횡이동 + 약간 전진/후진 (롤러 각도 45도)

현재 시스템:
- ❌ 횡방향 미끄러짐 계산 안 함
- ❌ 횡방향 보정 안 함
```

---

## 💡 **현재 보정 방식 (간접적)**

### **실시간 재계획 방식:**
```python
# waypoint_follower.py

매 루프 (0.2초마다):
  1. 현재 위치 읽기 (초음파 보정)
  2. 목표와 비교
  3. 오차 → 새 명령 생성
  4. 명령 전송
  5. 반복
```

**특징:**
```
✅ 장점:
- 간단함
- 초음파로 실제 위치 확인
- 오차가 누적되면 자동으로 보정됨

❌ 단점:
- 미끄러짐 계산 안 함
- 보정량 예측 안 함
- 다음 경로에 학습 안 함
- 반응이 느림 (0.2초 주기)
```

---

## 🔧 **개선안**

### **Option 1: 명시적 미끄러짐 보정** ⭐⭐⭐

#### **1-1. 미끄러짐 계산:**
```python
class SlipCompensator:
    """미끄러짐 보정기"""
    
    def __init__(self):
        # 미끄러짐 히스토리
        self.slip_history = {
            'forward': [],
            'backward': [],
            'left': [],
            'right': [],
            'rotate_l': [],
            'rotate_r': []
        }
    
    def record_motion(self, direction, speed_level, 
                      expected_pose, actual_pose):
        """
        이동 기록
        
        Args:
            direction: 명령 방향
            speed_level: 속도 레벨
            expected_pose: 예상 위치 (오도메트리)
            actual_pose: 실제 위치 (초음파)
        """
        # 오차 계산
        dx = actual_pose[0] - expected_pose[0]
        dy = actual_pose[1] - expected_pose[1]
        dtheta = actual_pose[2] - expected_pose[2]
        
        slip = {
            'dx': dx,
            'dy': dy,
            'dtheta': dtheta,
            'speed_level': speed_level
        }
        
        self.slip_history[direction.lower()].append(slip)
        
        # 최근 10개만 유지
        if len(self.slip_history[direction.lower()]) > 10:
            self.slip_history[direction.lower()].pop(0)
    
    def get_compensation(self, direction, speed_level):
        """
        보정량 계산
        
        Args:
            direction: 명령 방향
            speed_level: 속도 레벨
        
        Returns:
            dict: {'position_factor': float, 'angle_offset': float}
        """
        history = self.slip_history[direction.lower()]
        
        if len(history) < 3:
            # 데이터 부족 → 보정 없음
            return {'position_factor': 1.0, 'angle_offset': 0.0}
        
        # 평균 미끄러짐 계산
        avg_dx = sum(s['dx'] for s in history) / len(history)
        avg_dy = sum(s['dy'] for s in history) / len(history)
        avg_dtheta = sum(s['dtheta'] for s in history) / len(history)
        
        # 보정 인자
        slip_distance = math.sqrt(avg_dx**2 + avg_dy**2)
        
        if direction in ['FORWARD', 'BACKWARD']:
            position_factor = 1.0 + (slip_distance / 100.0)  # 예: 5cm 미끄러짐 → 1.05
            angle_offset = avg_dtheta
        else:
            position_factor = 1.0
            angle_offset = avg_dtheta
        
        return {
            'position_factor': position_factor,
            'angle_offset': angle_offset
        }
```

---

#### **1-2. 보정 적용:**
```python
class CompensatedOdometry(SimpleOdometry):
    """보정된 오도메트리"""
    
    def __init__(self, compensator):
        super().__init__()
        self.compensator = compensator
    
    def update_from_command(self, direction, speed_level, duration):
        # 보정량 가져오기
        comp = self.compensator.get_compensation(direction, speed_level)
        
        # 속도에 보정 인자 적용
        adjusted_speed_level = int(speed_level * comp['position_factor'])
        
        # 기본 업데이트
        super().update_from_command(direction, adjusted_speed_level, duration)
        
        # 각도 보정
        self.theta += comp['angle_offset']
        self._normalize_theta()
```

---

#### **1-3. 실시간 학습:**
```python
class AdaptiveWaypointFollower(ObstacleAwareWaypointFollower):
    """학습 기반 경로 추종"""
    
    def __init__(self, robot, localization, obstacle_system):
        super().__init__(robot, localization, obstacle_system)
        
        # 미끄러짐 보정기
        self.compensator = SlipCompensator()
        
        # 마지막 명령
        self.last_command = None
        self.last_expected_pose = None
    
    def follow_step(self):
        # 1. 이전 명령 평가
        if self.last_command is not None:
            # 실제 위치
            actual_pose = self.loc.get_pose()
            
            # 미끄러짐 기록
            self.compensator.record_motion(
                self.last_command['direction'],
                self.last_command['speed_level'],
                self.last_expected_pose,
                actual_pose
            )
        
        # 2. 새 명령 생성 (부모 클래스)
        result = super().follow_step()
        
        # 3. 예상 위치 저장
        self.last_command = self.robot.get_current_command()
        self.last_expected_pose = self.loc.get_pose()
        
        return result
```

---

### **Option 2: PID 제어** ⭐⭐ (고급)

```python
class PIDController:
    """PID 제어기"""
    
    def __init__(self, kp, ki, kd):
        self.kp = kp  # 비례 이득
        self.ki = ki  # 적분 이득
        self.kd = kd  # 미분 이득
        
        self.error_sum = 0.0
        self.last_error = 0.0
    
    def update(self, setpoint, measured_value, dt):
        """
        PID 업데이트
        
        Args:
            setpoint: 목표값
            measured_value: 측정값
            dt: 시간 간격
        
        Returns:
            float: 제어 출력
        """
        # 오차
        error = setpoint - measured_value
        
        # P: 비례
        p_term = self.kp * error
        
        # I: 적분
        self.error_sum += error * dt
        i_term = self.ki * self.error_sum
        
        # D: 미분
        d_term = self.kd * (error - self.last_error) / dt if dt > 0 else 0
        
        # 출력
        output = p_term + i_term + d_term
        
        # 업데이트
        self.last_error = error
        
        return output
```

---

### **Option 3: 간단한 비례 보정** ⭐ (현실적)

```python
class SimpleCorrection:
    """간단한 보정"""
    
    def __init__(self, correction_gain=0.3):
        self.gain = correction_gain
    
    def correct_command(self, target_pose, current_pose, base_speed):
        """
        간단한 비례 보정
        
        Args:
            target_pose: 목표 (x, y, theta)
            current_pose: 현재 (x, y, theta)
            base_speed: 기본 속도
        
        Returns:
            dict: {'direction': str, 'speed_level': int}
        """
        dx = target_pose[0] - current_pose[0]
        dy = target_pose[1] - current_pose[1]
        
        distance = math.sqrt(dx**2 + dy**2)
        
        # 오차가 크면 속도 증가
        speed_correction = 1.0 + (self.gain * distance / 100.0)
        
        adjusted_speed = int(base_speed * speed_correction)
        adjusted_speed = min(15, max(6, adjusted_speed))
        
        return {
            'direction': 'FORWARD',  # 예시
            'speed_level': adjusted_speed
        }
```

---

## 📊 **비교표**

| 방식 | 구현 난이도 | 효과 | 현재 상태 |
|------|-----------|------|----------|
| **실시간 재계획** | ⭐ 쉬움 | ⭐⭐ 중간 | ✅ 구현됨 |
| **명시적 보정** | ⭐⭐ 중간 | ⭐⭐⭐ 높음 | ❌ 없음 |
| **PID 제어** | ⭐⭐⭐ 어려움 | ⭐⭐⭐ 높음 | ❌ 없음 |
| **간단한 보정** | ⭐ 쉬움 | ⭐⭐ 중간 | ❌ 없음 |

---

## ✅ **답변**

### **Q1: RS CPU 보드 제어 잘 구현되어 있어?**
**A: ✅ 예, 기본 제어는 잘 작동합니다!**

```python
✅ 구현됨:
- 블루투스 연결
- 메카넘휠 명령 (6방향)
- 속도 제어 (레벨 6~15)
- 초음파 센서 읽기

✅ 명령 흐름:
라즈베리파이 → 블루투스 → RS CPU → 메카넘휠
```

---

### **Q2: 미끄러짐 보정 계산해서 전달해주고 있니?**
**A: ❌ 아니요, 명시적 보정은 없습니다!**

```python
❌ 없는 것:
- 미끄러짐 크기 계산
- 보정량 계산
- 각도 틀기 계산
- 횡방향 보정

✅ 대신 있는 것:
- 실시간 재계획 (간접 보정)
- 초음파로 위치 확인
- 매 루프마다 오차 수정
```

---

## 🚀 **개선 추천**

### **즉시 적용 가능:** ⭐
```python
Option 3: 간단한 비례 보정
- 구현 쉬움 (1시간)
- 효과 있음
- 기존 코드에 추가만
```

### **중기 목표:** ⭐⭐
```python
Option 1: 명시적 미끄러짐 보정
- 학습 기반
- 점점 개선됨
- 구현 시간: 3~4시간
```

### **장기 목표:** ⭐⭐⭐
```python
Option 2: PID 제어
- 최고 성능
- 튜닝 필요
- 구현 시간: 8시간+
```

---

## 📝 **결론**

### **현재 상태:**
```
✅ 기본 제어: 잘 작동
❌ 미끄러짐 보정: 없음
⚠️ 간접 보정: 실시간 재계획 (느림)
```

### **권장 사항:**
```
1. 우선 Option 3 (간단한 보정) 추가
2. 나중에 Option 1 (학습 기반) 고려
3. 필요하면 Option 2 (PID)
```

**→ 개선 필요!** ⚠️
