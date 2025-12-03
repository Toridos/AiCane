# 🔧 하드웨어 테스트 담당자 가이드

## 👋 환영합니다!

이 문서는 **하드웨어 테스트 담당** 팀원을 위한 완벽 가이드입니다.

---

## 📋 **당신이 읽어야 할 문서 (순서대로)**

### **1단계: 이 문서** (15분) ⭐⭐⭐
- ✅ 지금 읽는 중!

### **2단계: 하드웨어 연결** (10분) ⭐⭐⭐
- [블루투스 연결](#블루투스-연결)
- [LiDAR 연결](#lidar-연결-선택)

### **3단계: 테스트 실행** (20분) ⭐⭐⭐
- [기본 테스트](#기본-테스트)
- [LiDAR 테스트](#lidar-테스트)

### **추가 참고 (선택):**
- BLUETOOTH_GUIDE.md (상세 블루투스)
- LIDAR_GUIDE.md (상세 LiDAR)
- HARDWARE_CONFIG_INTEGRATION.md (설정 통합)

---

## 🚀 **빠른 시작 (5분)**

### **전체 흐름:**
```
1. 블루투스 연결 (5분)
2. 로봇 제어 테스트 (5분)
3. 초음파 센서 확인 (5분)
4. LiDAR 연결 (5분, 선택)
5. 통합 테스트 (10분)
```

---

## 🔌 **1. 블루투스 연결**

### **필요한 것:**
- 라즈베리파이 4
- RS CPU 보드 (HC-05 블루투스)
- 팀원이 테스트한 MAC: `98:D3:31:XX:XX:XX`

### **연결 순서:**

#### **1-1. MAC 주소 찾기**
```bash
sudo hcitool scan
```

**출력 예시:**
```
Scanning ...
    98:D3:31:XX:XX:XX    HC-05
```

#### **1-2. 페어링**
```bash
bluetoothctl

# bluetoothctl 쉘에서:
[bluetooth]# scan on
[bluetooth]# pair 98:D3:31:XX:XX:XX
[bluetooth]# trust 98:D3:31:XX:XX:XX
[bluetooth]# exit
```

#### **1-3. 수동 바인딩**
```bash
# rfcomm0으로 바인딩
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1

# 권한 설정
sudo chmod 666 /dev/rfcomm0

# 확인
ls -l /dev/rfcomm0
```

#### **1-4. 설정 파일 업데이트**
```bash
nano config/hardware.yaml
```

**수정:**
```yaml
robot:
  port: '/dev/rfcomm0'           # ✅ 팀원 검증!
  bluetooth_mac: '98:D3:31:XX:XX:XX'  # 실제 MAC으로 변경
```

**상세 가이드:** BLUETOOTH_GUIDE.md

---

## 🤖 **2. 로봇 제어 테스트**

### **2-1. 기본 테스트**
```bash
python scripts/test_hardware.py
```

**예상 출력:**
```
🔧 하드웨어 테스트

1️⃣ 연결:
  ✅ 포트 발견: /dev/rfcomm0
  ✅ 연결 성공

2️⃣ 모션 제어:
  전진 → ✅
  좌회전 → ✅
  우회전 → ✅
  정지 → ✅

3️⃣ 초음파:
  정면: 120.5cm
  좌: 98.3cm
  우: 105.7cm
```

### **2-2. 문제 해결**

**"포트 없음" 에러:**
```bash
# 블루투스 연결 확인
ls /dev/rfcomm0

# 없으면 다시 바인딩
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1
```

**"권한 거부" 에러:**
```bash
sudo chmod 666 /dev/rfcomm0
```

---

## 📡 **3. LiDAR 연결 (선택)**

### **팀원이 확인한 설정:**
```yaml
lidar:
  port: /dev/ttyUSB1           # ✅ USB1에 연결됨!
  baudrate: 115200             # ✅ A1/A2 모델
  model: rplidar_a2
```

### **3-1. USB 연결 확인**
```bash
# USB 포트 확인
ls /dev/ttyUSB*

# 예상 출력:
# /dev/ttyUSB0 or /dev/ttyUSB1
```

### **3-2. 권한 설정**
```bash
# LiDAR 포트 권한
sudo chmod 666 /dev/ttyUSB1

# 확인
ls -l /dev/ttyUSB1
```

### **3-3. 라이브러리 설치**
```bash
pip3 install rplidar-roboticia --break-system-packages
```

### **3-4. 설정 파일 확인**
```bash
nano config/hardware.yaml
```

**확인:**
```yaml
lidar:
  enabled: true                # ✅
  port: /dev/ttyUSB1           # ✅ 팀원 검증!
  baudrate: 115200             # ✅ 팀원 검증!
  model: rplidar_a2            # ✅
```

**상세 가이드:** LIDAR_GUIDE.md

---

## 🧪 **4. 테스트 실행**

### **4-1. 기본 테스트**
```bash
# 하드웨어 전체 테스트
python scripts/test_hardware.py
```

### **4-2. LiDAR 테스트**
```bash
# LiDAR만 테스트
python scripts/test_lidar.py
```

**예상 출력:**
```
📡 LiDAR 테스트

1️⃣ 연결:
  ✅ 포트: /dev/ttyUSB1
  ✅ 속도: 115200 baud
  ✅ 스캔 시작

2️⃣ 데이터:
  포인트: 360개
  거리: 45.0cm ~ 500.0cm

3️⃣ 360도 감지:
  정면: 45.0cm ⚠️
  좌측: 150.0cm ✅
  우측: 140.0cm ✅
```

### **4-3. 통합 테스트**
```bash
# 전체 시스템 테스트
python tests/test_all.py
```

---

## ✅ **체크리스트**

### **블루투스:**
- [ ] MAC 주소 확인
- [ ] 페어링 완료
- [ ] rfcomm0 바인딩
- [ ] 권한 설정 (666)
- [ ] config/hardware.yaml 업데이트

### **LiDAR (선택):**
- [ ] USB 연결 확인
- [ ] 포트 확인 (/dev/ttyUSB1)
- [ ] 권한 설정 (666)
- [ ] 라이브러리 설치
- [ ] config/hardware.yaml 확인

### **테스트:**
- [ ] test_hardware.py 통과
- [ ] test_lidar.py 통과 (LiDAR 있으면)
- [ ] test_all.py 통과

---

## 🆘 **문제 해결**

### **자주 있는 문제:**

#### **1. 블루투스 연결 안 됨**
```bash
# 해결책 1: rfcomm 재시작
sudo killall rfcomm
sudo rfcomm bind 0 98:D3:31:XX:XX:XX 1

# 해결책 2: 블루투스 재시작
sudo systemctl restart bluetooth

# 해결책 3: 수동 연결
bluetoothctl
connect 98:D3:31:XX:XX:XX
```

#### **2. LiDAR 데이터 없음**
```bash
# 해결책 1: 권한 확인
sudo chmod 666 /dev/ttyUSB1

# 해결책 2: 포트 확인
ls -l /dev/ttyUSB*

# 해결책 3: 속도 확인 (115200 vs 256000)
# config/hardware.yaml에서 baudrate 확인
```

#### **3. 초음파 값이 이상함**
```bash
# 해결책: 센서 연결 확인
# GPIO 핀 번호 확인:
# - 정면: 12
# - 좌측: 2
# - 우측: 3
```

---

## 📚 **추가 참고 문서**

### **필수 (이미 읽음):**
- ✅ 이 문서 (하드웨어 가이드)

### **상세 가이드 (선택):**
- BLUETOOTH_GUIDE.md (블루투스 상세)
- LIDAR_GUIDE.md (LiDAR 상세)
- LIDAR_VS_ULTRASONIC_GUIDE.md (센서 비교)
- HARDWARE_CONFIG_INTEGRATION.md (팀원 설정 통합)

### **개발 문서:**
- IMPLEMENTATION.md (전체 구현)
- QUICKSTART.md (빠른 시작)

---

## 🎉 **완료!**

**하드웨어 테스트 준비 완료했습니다!** ✅

**다음 단계:**
1. ✅ 블루투스 연결 완료
2. ✅ LiDAR 연결 완료 (선택)
3. ✅ 테스트 통과
4. → 이제 주행 테스트로! 🚀

**주행 테스트:**
```bash
# Mock 모드 (안전)
./launch/start_navigation.sh --from 101호 --to 107호 --mock

# 실제 주행 (준비되면)
./launch/start_navigation.sh --from 101호 --to 107호
```

**질문이 있으면 팀에게 문의하세요!** 💬
