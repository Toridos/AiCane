"""
AiCane Configuration Loader
YAML 설정 파일 로드 + 검증 + 환경 변수 + 기본값
"""

from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import os
import yaml
import copy


class ConfigLoader:
    """
    YAML 설정 파일 로더
    
    - 기본값 지원
    - 환경 변수 치환
    - 설정 검증
    - 여러 파일 머지
    - 타입 변환
    """
    
    # 기본 설정 디렉토리
    DEFAULT_CONFIG_DIR = './config'
    
    # 기본 설정 (fallback)
    DEFAULT_HARDWARE = {
        'robot': {
            'port': None,
            'baudrate': 9600,
            'timeout': 1.0,
            'auto_connect': True,
        },
        'lidar': {
            'enabled': False,
            'port': '/dev/ttyUSB0',
            'baudrate': 256000,
            'mock': False,
        },
        'ultrasonic': {
            'pins': {
                'front': 12,
                'left': 2,
                'right': 3,
            },
            'critical_distance': 25,
            'warning_distance': 50,
            'safe_distance': 100,
        },
    }
    
    DEFAULT_NAVIGATION = {
        'control': {
            'rate_hz': 5,
            'goal_threshold_cm': 5.0,
            'angle_threshold_deg': 15.0,
        },
        'obstacle_detection': {
            'mode': 'hybrid',
            'ultrasonic': {
                'min_distance': 50,
                'emergency_stop': 30,
            },
            'lidar': {
                'min_distance': 50,
                'path_width': 60,
            },
        },
    }
    
    # ========================================
    # 기본 로드 (팀원 제안 개선)
    # ========================================
    
    @staticmethod
    def load_yaml(path: str, 
                  default: Optional[Dict] = None,
                  required_keys: Optional[List[str]] = None,
                  env_vars: bool = True) -> Dict[str, Any]:
        """
        YAML 파일 로드 (팀원 제안 개선)
        
        Args:
            path: YAML 파일 경로
            default: 기본값 딕셔너리
            required_keys: 필수 키 리스트
            env_vars: 환경 변수 치환 여부
        
        Returns:
            dict: 설정 딕셔너리
        
        Raises:
            FileNotFoundError: 파일 없음
            ValueError: 잘못된 형식
        """
        p = Path(path)
        
        # 파일 확인
        if not p.is_file():
            if default is not None:
                print(f"⚠️ 설정 파일 없음: {p}")
                print(f"   기본값 사용")
                return default
            raise FileNotFoundError(f"Config file not found: {p}")
        
        # YAML 로드
        try:
            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        
        # 타입 체크
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping(dict), got: {type(data)}")
        
        # 환경 변수 치환
        if env_vars:
            data = ConfigLoader._replace_env_vars(data)
        
        # 기본값 머지
        if default is not None:
            data = ConfigLoader._merge_dicts(default, data)
        
        # 필수 키 체크
        if required_keys:
            ConfigLoader._validate_keys(data, required_keys)
        
        return data
    
    # ========================================
    # 하드웨어 설정
    # ========================================
    
    @staticmethod
    def load_hardware_config(filename: Optional[str] = None,
                            config_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        하드웨어 설정 로드
        
        Args:
            filename: 설정 파일명 (기본: hardware.yaml)
            config_dir: 설정 디렉토리 (기본: ./config)
        
        Returns:
            dict: 하드웨어 설정
        """
        if filename is None:
            filename = 'hardware.yaml'
        
        if config_dir is None:
            config_dir = ConfigLoader.DEFAULT_CONFIG_DIR
        
        path = Path(config_dir) / filename
        
        return ConfigLoader.load_yaml(
            str(path),
            default=ConfigLoader.DEFAULT_HARDWARE,
            required_keys=['robot', 'ultrasonic'],
            env_vars=True
        )
    
    # ========================================
    # 네비게이션 설정
    # ========================================
    
    @staticmethod
    def load_navigation_config(filename: Optional[str] = None,
                              config_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        네비게이션 설정 로드
        
        Args:
            filename: 설정 파일명 (기본: navigation.yaml)
            config_dir: 설정 디렉토리 (기본: ./config)
        
        Returns:
            dict: 네비게이션 설정
        """
        if filename is None:
            filename = 'navigation.yaml'
        
        if config_dir is None:
            config_dir = ConfigLoader.DEFAULT_CONFIG_DIR
        
        path = Path(config_dir) / filename
        
        return ConfigLoader.load_yaml(
            str(path),
            default=ConfigLoader.DEFAULT_NAVIGATION,
            required_keys=['control', 'obstacle_detection'],
            env_vars=True
        )
    
    # ========================================
    # 전체 설정 로드
    # ========================================
    
    @staticmethod
    def load_all_configs(config_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        모든 설정 파일 로드
        
        Args:
            config_dir: 설정 디렉토리
        
        Returns:
            dict: {
                'hardware': {...},
                'navigation': {...}
            }
        """
        if config_dir is None:
            config_dir = ConfigLoader.DEFAULT_CONFIG_DIR
        
        return {
            'hardware': ConfigLoader.load_hardware_config(config_dir=config_dir),
            'navigation': ConfigLoader.load_navigation_config(config_dir=config_dir),
        }
    
    # ========================================
    # 설정 저장
    # ========================================
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], path: str) -> None:
        """
        딕셔너리를 YAML 파일로 저장
        
        Args:
            data: 저장할 데이터
            path: 파일 경로
        """
        p = Path(path)
        
        # 디렉토리 생성
        p.parent.mkdir(parents=True, exist_ok=True)
        
        # YAML 저장
        with p.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 설정 저장: {p}")
    
    # ========================================
    # 환경 변수 치환
    # ========================================
    
    @staticmethod
    def _replace_env_vars(data: Any) -> Any:
        """
        환경 변수 치환: ${VAR_NAME} → 환경 변수 값
        
        Args:
            data: 데이터 (dict, list, str 등)
        
        Returns:
            치환된 데이터
        """
        if isinstance(data, dict):
            return {k: ConfigLoader._replace_env_vars(v) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [ConfigLoader._replace_env_vars(item) for item in data]
        
        elif isinstance(data, str):
            # ${VAR_NAME} 패턴 찾기
            if data.startswith('${') and data.endswith('}'):
                var_name = data[2:-1]
                return os.getenv(var_name, data)
            return data
        
        else:
            return data
    
    # ========================================
    # 딕셔너리 머지
    # ========================================
    
    @staticmethod
    def _merge_dicts(base: Dict, override: Dict) -> Dict:
        """
        두 딕셔너리를 깊게 머지
        
        Args:
            base: 기본값
            override: 덮어쓸 값
        
        Returns:
            dict: 머지된 딕셔너리
        """
        result = copy.deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 재귀적으로 머지
                result[key] = ConfigLoader._merge_dicts(result[key], value)
            else:
                # 덮어쓰기
                result[key] = value
        
        return result
    
    # ========================================
    # 설정 검증
    # ========================================
    
    @staticmethod
    def _validate_keys(data: Dict, required_keys: List[str]) -> None:
        """
        필수 키 존재 확인
        
        Args:
            data: 검증할 딕셔너리
            required_keys: 필수 키 리스트
        
        Raises:
            ValueError: 필수 키 없음
        """
        missing = []
        
        for key in required_keys:
            # 중첩 키 지원: 'robot.port'
            if '.' in key:
                parts = key.split('.')
                current = data
                
                for part in parts:
                    if not isinstance(current, dict) or part not in current:
                        missing.append(key)
                        break
                    current = current[part]
            else:
                if key not in data:
                    missing.append(key)
        
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")
    
    # ========================================
    # 값 가져오기
    # ========================================
    
    @staticmethod
    def get_nested(data: Dict, key_path: str, default: Any = None) -> Any:
        """
        중첩된 키로 값 가져오기
        
        Args:
            data: 딕셔너리
            key_path: 키 경로 (예: 'robot.port')
            default: 기본값
        
        Returns:
            값 또는 기본값
        
        Example:
            >>> config = {'robot': {'port': '/dev/ttyUSB0'}}
            >>> ConfigLoader.get_nested(config, 'robot.port')
            '/dev/ttyUSB0'
        """
        parts = key_path.split('.')
        current = data
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        
        return current
    
    # ========================================
    # 디버그 출력
    # ========================================
    
    @staticmethod
    def print_config(config: Dict, title: str = "Configuration") -> None:
        """
        설정을 보기 좋게 출력
        
        Args:
            config: 설정 딕셔너리
            title: 제목
        """
        print(f"\n{'=' * 50}")
        print(f"{title}")
        print('=' * 50)
        
        ConfigLoader._print_nested(config, indent=0)
        
        print('=' * 50)
    
    @staticmethod
    def _print_nested(data: Any, indent: int = 0) -> None:
        """중첩된 데이터 출력"""
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefix}{key}:")
                    ConfigLoader._print_nested(value, indent + 1)
                else:
                    print(f"{prefix}{key}: {value}")
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    ConfigLoader._print_nested(item, indent)
                else:
                    print(f"{prefix}- {item}")
        
        else:
            print(f"{prefix}{data}")


# 편의 함수 (팀원 제안 유지)
def load_yaml(path: str) -> Dict[str, Any]:
    """
    주어진 경로의 YAML 설정 파일을 읽어 딕셔너리로 반환합니다. (팀원 제안)
    
    Args:
        path: YAML 파일 경로
    
    Returns:
        dict: 설정 딕셔너리
    """
    return ConfigLoader.load_yaml(path)


# 사용 예제
if __name__ == '__main__':
    print("=== ConfigLoader 테스트 ===\n")
    
    # 1. 팀원 방식 (그대로 작동!)
    print("1️⃣ 팀원 방식:")
    try:
        config = load_yaml('./config/hardware.yaml')
        print(f"   ✅ 로드 성공: {len(config)} keys")
    except Exception as e:
        print(f"   ⚠️ {e}")
    
    # 2. 기본값 사용
    print("\n2️⃣ 기본값 사용:")
    config = ConfigLoader.load_yaml(
        './config/nonexistent.yaml',
        default={'test': 'value'},
    )
    print(f"   config: {config}")
    
    # 3. 환경 변수 치환
    print("\n3️⃣ 환경 변수 치환:")
    os.environ['ROBOT_PORT'] = '/dev/ttyUSB1'
    config = {'port': '${ROBOT_PORT}'}
    result = ConfigLoader._replace_env_vars(config)
    print(f"   원본: {config}")
    print(f"   결과: {result}")
    
    # 4. 하드웨어 설정 로드
    print("\n4️⃣ 하드웨어 설정:")
    try:
        hw_config = ConfigLoader.load_hardware_config()
        ConfigLoader.print_config(hw_config, "Hardware Config")
    except Exception as e:
        print(f"   ⚠️ {e}")
    
    # 5. 네비게이션 설정 로드
    print("\n5️⃣ 네비게이션 설정:")
    try:
        nav_config = ConfigLoader.load_navigation_config()
        ConfigLoader.print_config(nav_config, "Navigation Config")
    except Exception as e:
        print(f"   ⚠️ {e}")
    
    # 6. 중첩 키 가져오기
    print("\n6️⃣ 중첩 키 가져오기:")
    config = {'robot': {'port': '/dev/ttyUSB0', 'baudrate': 9600}}
    port = ConfigLoader.get_nested(config, 'robot.port')
    baudrate = ConfigLoader.get_nested(config, 'robot.baudrate')
    print(f"   port: {port}")
    print(f"   baudrate: {baudrate}")
    
    # 7. 설정 저장
    print("\n7️⃣ 설정 저장:")
    test_config = {
        'robot': {
            'port': '/dev/ttyUSB0',
            'baudrate': 9600,
        },
        'sensors': ['ultrasonic', 'lidar']
    }
    ConfigLoader.save_yaml(test_config, './logs/test_config.yaml')
    
    print("\n✅ 테스트 완료")
