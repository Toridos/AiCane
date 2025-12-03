# Launch Scripts 📜

이 디렉토리는 **AiCane Navigation을 쉽게 실행하기 위한 자동화 스크립트 모음**입니다.

## 📂 포함된 스크립트

### 1. `setup_check.sh` - 초기 설정 체크
시스템 상태를 전체적으로 확인합니다.
```bash
bash launch/setup_check.sh
```

**체크 항목:**
- ✅ Python 버전
- ✅ 필수 패키지 설치
- ✅ 블루투스 도구
- ✅ 시리얼 포트
- ✅ MAC 주소 설정
- ✅ 디렉토리 구조

---

### 2. `connect_bluetooth.sh` - 블루투스 자동 연결
설정 파일의 MAC 주소로 자동 연결합니다.
```bash
bash launch/connect_bluetooth.sh
```

**수행 작업:**
1. config/hardware.yaml에서 MAC 주소 읽기
2. 블루투스 서비스 시작
3. 자동 페어링 (필요시)
4. rfcomm 바인딩
5. 권한 설정

---

### 3. `start_navigation.sh` - 자동 주행 시작
블루투스 연결부터 주행까지 한 번에!
```bash
bash launch/start_navigation.sh --from 101호 --to 107호
```

**옵션:**
- `--from <방이름>`: 출발 방
- `--to <방이름>`: 도착 방
- `--mock`: Mock 모드 (하드웨어 없이 테스트)

**자동 처리:**
- 블루투스 연결 확인
- 로그 파일 생성
- 주행 실행
- 결과 저장

---

### 4. `demo_full.sh` - 완전 자동 데모
전체 시나리오를 자동으로 실행합니다.
```bash
bash launch/demo_full.sh          # 실제 모드
bash launch/demo_full.sh --mock   # Mock 모드
```

**데모 시나리오:**
1. 시스템 체크 및 블루투스 연결
2. 시나리오 1: 방 간 이동 (101호 → 107호)
3. 시나리오 2: AI 경로 추종
4. 통계 및 요약 출력

---

### 5. `shutdown.sh` - 시스템 종료 및 정리
안전하게 종료하고 정리합니다.
```bash
bash launch/shutdown.sh
```

**수행 작업:**
- 실행 중인 프로세스 종료
- 블루투스 연결 해제
- 오래된 로그 정리 (30일 이상)
- 임시 파일 삭제

---

## 🚀 사용 시나리오

### 시나리오 1: 최초 설정
```bash
# 1. 시스템 체크
bash launch/setup_check.sh

# 2. config/hardware.yaml에 MAC 주소 입력
nano config/hardware.yaml

# 3. 블루투스 연결
bash launch/connect_bluetooth.sh

# 4. 테스트
bash launch/start_navigation.sh --from 101호 --to 107호 --mock
```

### 시나리오 2: 매일 사용
```bash
# RS CPU 보드 전원 켜고

# 바로 실행!
bash launch/start_navigation.sh --from 101호 --to 107호
```

### 시나리오 3: 데모 시연
```bash
# 전체 데모 자동 실행
bash launch/demo_full.sh
```

### 시나리오 4: 종료
```bash
# 안전하게 종료
bash launch/shutdown.sh
```

---

## 🔧 실행 권한 부여

처음 사용 시 실행 권한을 부여해야 합니다:
```bash
chmod +x launch/*.sh
```

---

## 📝 로그 파일

모든 스크립트는 `logs/` 디렉토리에 로그를 저장합니다:
```
logs/
├── navigation_101호_to_107호_20250102_143022.log
├── navigation_101호_to_107호_20250102_153045.log
└── ...
```

로그 확인:
```bash
ls -lt logs/
tail -f logs/navigation_*.log
```

---

## 💡 팁

### 자동 시작 설정 (systemd)
부팅 시 자동으로 연결하려면:
```bash
sudo nano /etc/systemd/system/aicane-bluetooth.service
```

내용:
```ini
[Unit]
Description=AiCane Bluetooth Connection
After=bluetooth.service

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/aicane_navigation
ExecStart=/bin/bash /home/pi/aicane_navigation/launch/connect_bluetooth.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

활성화:
```bash
sudo systemctl enable aicane-bluetooth.service
```

---

## 🆘 문제 해결

### 스크립트가 실행 안 됨
```bash
# 권한 확인
ls -l launch/*.sh

# 권한 부여
chmod +x launch/*.sh
```

### 블루투스 연결 실패
```bash
# 상태 확인
systemctl status bluetooth

# 재시작
sudo systemctl restart bluetooth

# 수동 연결
bash launch/connect_bluetooth.sh
```

### Mock 모드로 테스트
하드웨어 없이 테스트하려면 `--mock` 옵션 추가:
```bash
bash launch/start_navigation.sh --from 101호 --to 107호 --mock
bash launch/demo_full.sh --mock
```

---

## 📚 추가 문서

- [블루투스 가이드](../BLUETOOTH_GUIDE.md)
- [빠른 시작](../QUICKSTART.md)
- [메인 README](../README.md)
