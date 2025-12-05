# ConfigLoader 완전 가이드 ⚙️

## 🤔 **팀원 제안 평가**

### **팀원 코드:**
```python
def load_yaml(path: str) -> Dict[str, Any]:
    # YAML 파일 읽기
    # FileNotFoundError 체크
    # 타입 체크
    return data
```

### **평가:**

| 항목 | 팀원 코드 | 개선 코드 |
|------|----------|----------|
| **간단함** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **작동** | ✅ | ✅ |
| **기본값** | ❌ | ✅ |
| **환경 변수** | ❌ | ✅ |
| **검증** | ❌ | ✅ |
| **머지** | ❌ | ✅ |
| **저장** | ❌ | ✅ |
| **중첩 키** | ❌ | ✅ |
| **총 기능** | 1개 | 8+개 |

---

## 💡 **팀원 코드 장단점**

### **장점:** ✅
1. **매우 간단** - 10줄 수준
2. **작동함** - 기본 로드 가능
3. **에러 처리** - FileNotFoundError, ValueError

### **단점:** ❌
1. **기본값 없음** - 파일 없으면 에러
2. **환경 변수 미지원** - ${VAR} 치환 불가
3. **검증 없음** - 필수 키 체크 X
4. **머지 불가** - 여러 파일 병합 X
5. **저장 불가** - YAML 쓰기 X
6. **중첩 키 불편** - config['robot']['port'] 깊이 필요

---

## 🎯 **개선 코드 핵심 기능**

### **1. 기본값 지원** ⭐⭐⭐
```python
# 파일 없어도 OK!
config = ConfigLoader.load_yaml(
    './config/hardware.yaml',
    default={'robot': {'port': '/dev/ttyUSB0'}}
)

# 파일 없으면 기본값 사용
# ⚠️ 설정 파일 없음: ./config/hardware.yaml
#    기본값 사용
```

**장점:**
- ✅ 파일 없어도 작동
- ✅ 개발/테스트 편리
- ✅ 안정적

---

### **2. 환경 변수 치환** ⭐⭐⭐
```yaml
# config/hardware.yaml
robot:
  port: ${ROBOT_PORT}           # 환경 변수
  bluetooth_mac: ${BT_MAC}
```

```python
# 환경 변수 설정
os.environ['ROBOT_PORT'] = '/dev/ttyUSB0'
os.environ['BT_MAC'] = '98:D3:31:XX:XX:XX'

# 로드
config = ConfigLoader.load_yaml('./config/hardware.yaml')

# 결과
# config['robot']['port'] = '/dev/ttyUSB0'
```

**장점:**
- ✅ 환경별 설정 다름 (개발/운영)
- ✅ 민감 정보 분리
- ✅ Docker 친화적

---

### **3. 설정 검증** ⭐⭐
```python
# 필수 키 체크
config = ConfigLoader.load_yaml(
    './config/hardware.yaml',
    required_keys=['robot', 'ultrasonic', 'robot.port']
)

# 필수 키 없으면 에러!
# ValueError: Missing required config keys: ['robot.port']
```

**장점:**
- ✅ 설정 누락 방지
- ✅ 에러 조기 발견

---

### **4. 여러 파일 머지** ⭐⭐
```python
# base.yaml
robot:
  port: /dev/ttyUSB0
  baudrate: 9600
  timeout: 1.0

# override.yaml
robot:
  baudrate: 19200  # 덮어쓰기

# 머지
base = ConfigLoader.load_yaml('./base.yaml')
override = ConfigLoader.load_yaml('./override.yaml')
merged = ConfigLoader._merge_dicts(base, override)

# 결과
# {
#   'robot': {
#     'port': '/dev/ttyUSB0',      # base
#     'baudrate': 19200,            # override
#     'timeout': 1.0                # base
#   }
# }
```

---

### **5. 설정 저장** ⭐⭐
```python
# 설정 수정
config['robot']['port'] = '/dev/ttyUSB1'

# 저장
ConfigLoader.save_yaml(config, './config/hardware_new.yaml')

# ✅ 설정 저장: ./config/hardware_new.yaml
```

---

### **6. 중첩 키 접근** ⭐⭐⭐
```python
config = {
    'robot': {
        'port': '/dev/ttyUSB0',
        'baudrate': 9600
    }
}

# 팀원 방식 (불편)
port = config['robot']['port']  # KeyError 위험!

# 개선 방식 (편리)
port = ConfigLoader.get_nested(config, 'robot.port', default='/dev/ttyUSB0')

# KeyError 없음! 기본값 반환!
```

---

### **7. 하드웨어/네비게이션 전용** ⭐⭐⭐
```python
# 하드웨어 설정
hw_config = ConfigLoader.load_hardware_config()

# 네비게이션 설정
nav_config = ConfigLoader.load_navigation_config()

# 전체 설정
all_config = ConfigLoader.load_all_configs()
# {
#   'hardware': {...},
#   'navigation': {...}
# }
```

**장점:**
- ✅ 타입 안전
- ✅ 기본값 내장
- ✅ 필수 키 자동 체크

---

### **8. 디버그 출력** ⭐
```python
config = ConfigLoader.load_hardware_config()

ConfigLoader.print_config(config, "Hardware Config")

# ==================================================
# Hardware Config
# ==================================================
# robot:
#   port: /dev/ttyUSB0
#   baudrate: 9600
#   timeout: 1.0
# lidar:
#   enabled: True
#   port: /dev/ttyUSB0
# ==================================================
```

---

## 🔄 **사용 패턴**

### **패턴 1: 기본 (팀원 방식)** ⭐⭐
```python
# 팀원 제안 그대로 작동!
from aicane_navigation.utils.config_loader import load_yaml

config = load_yaml('./config/hardware.yaml')

# + 기본값
config = load_yaml('./config/hardware.yaml', default={...})
```

---

### **패턴 2: 클래스 사용 (추천!)** ⭐⭐⭐
```python
from aicane_navigation.utils import ConfigLoader

# 하드웨어 설정
hw_config = ConfigLoader.load_hardware_config()

# 네비게이션 설정
nav_config = ConfigLoader.load_navigation_config()

# 중첩 키 접근
port = ConfigLoader.get_nested(hw_config, 'robot.port')
lidar_enabled = ConfigLoader.get_nested(hw_config, 'lidar.enabled', False)
```

---

### **패턴 3: 환경 변수 (운영)** ⭐⭐⭐
```yaml
# config/hardware.yaml
robot:
  port: ${ROBOT_PORT}
  bluetooth_mac: ${BT_MAC}

lidar:
  enabled: ${LIDAR_ENABLED}
  port: ${LIDAR_PORT}
```

```bash
# 환경 변수 설정
export ROBOT_PORT=/dev/ttyUSB0
export BT_MAC=98:D3:31:XX:XX:XX
export LIDAR_ENABLED=true
export LIDAR_PORT=/dev/ttyUSB1

# 실행
python main.py
```

---

## 💡 **실전 예제**

### **예제 1: NavigationSystem 통합**
```python
from aicane_navigation.utils import ConfigLoader

class NavigationSystem:
    def __init__(self, config_dir='./config'):
        # 설정 로드
        self.hw_config = ConfigLoader.load_hardware_config(
            config_dir=config_dir
        )
        self.nav_config = ConfigLoader.load_navigation_config(
            config_dir=config_dir
        )
        
        # 디버그 출력
        if self.debug:
            ConfigLoader.print_config(self.hw_config, "Hardware")
            ConfigLoader.print_config(self.nav_config, "Navigation")
        
        # 중첩 키 접근
        self.robot_port = ConfigLoader.get_nested(
            self.hw_config, 
            'robot.port',
            default=None
        )
        
        self.lidar_enabled = ConfigLoader.get_nested(
            self.hw_config,
            'lidar.enabled',
            default=False
        )
        
        # 하드웨어 초기화
        self._init_hardware()
```

---

### **예제 2: 설정 생성/저장**
```python
from aicane_navigation.utils import ConfigLoader

# 새 설정 생성
new_config = {
    'robot': {
        'port': '/dev/ttyUSB0',
        'baudrate': 9600,
        'bluetooth_mac': '98:D3:31:XX:XX:XX',
    },
    'lidar': {
        'enabled': True,
        'port': '/dev/ttyUSB1',
    }
}

# 저장
ConfigLoader.save_yaml(new_config, './config/hardware_new.yaml')

# 로드
config = ConfigLoader.load_yaml('./config/hardware_new.yaml')
```

---

### **예제 3: 개발/운영 분리**
```yaml
# config/base.yaml (공통)
robot:
  baudrate: 9600
  timeout: 1.0

lidar:
  baudrate: 256000

# config/dev.yaml (개발)
robot:
  port: /dev/ttyUSB0
  mock: true

lidar:
  enabled: false
  mock: true

# config/prod.yaml (운영)
robot:
  port: ${ROBOT_PORT}
  mock: false

lidar:
  enabled: true
  port: ${LIDAR_PORT}
  mock: false
```

```python
# 머지
base = ConfigLoader.load_yaml('./config/base.yaml')

if ENV == 'dev':
    override = ConfigLoader.load_yaml('./config/dev.yaml')
else:
    override = ConfigLoader.load_yaml('./config/prod.yaml')

config = ConfigLoader._merge_dicts(base, override)
```

---

## 📝 **최종 권장사항**

### **Q: 팀원 코드 어때?**

### **A: 좋은데, 개선 버전 사용!** ⭐⭐⭐

**이유:**
1. ✅ **팀원 제안 포함** - load_yaml() 함수 유지
2. ✅ **기본값 지원** - 파일 없어도 OK
3. ✅ **환경 변수** - 운영 환경 대응
4. ✅ **검증** - 설정 누락 방지
5. ✅ **편의 기능** - 중첩 키, 저장, 출력

---

### **비교:**

| | 팀원 제안 | 개선 코드 |
|---|---|---|
| **간단함** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **기능** | 1개 | 8+개 |
| **기본값** | ❌ | ✅ |
| **환경 변수** | ❌ | ✅ |
| **검증** | ❌ | ✅ |
| **실용성** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **추천도** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎉 **결론**

### **팀원 제안 → 반영하되 대폭 개선!** ✅

**최종 구조:**
```python
# ✅ 팀원 제안 (함수, 그대로)
def load_yaml(path: str) -> Dict:
    return ConfigLoader.load_yaml(path)

# ✅ 개선 (클래스)
class ConfigLoader:
    # 기본 로드
    @staticmethod
    def load_yaml(path, default, required_keys, env_vars)
    
    # 전용 로더
    @staticmethod
    def load_hardware_config(...)
    def load_navigation_config(...)
    def load_all_configs(...)
    
    # 저장
    @staticmethod
    def save_yaml(data, path)
    
    # 유틸
    @staticmethod
    def get_nested(data, key_path, default)
    def print_config(config, title)
    
    # 내부
    @staticmethod
    def _replace_env_vars(...)
    def _merge_dicts(...)
    def _validate_keys(...)
```

**사용:**
```python
# 팀원 방식 (여전히 작동!)
config = load_yaml('./config/hardware.yaml')

# 개선 방식 (추천!)
config = ConfigLoader.load_hardware_config()
port = ConfigLoader.get_nested(config, 'robot.port')
```

**→ 팀원 제안을 존중하면서 실용성 대폭 향상!** 🚀🎊✨
