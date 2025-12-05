#!/bin/bash
# 시스템 초기화 및 체크 스크립트
# 첫 실행 시 필요한 모든 체크를 한 번에!

echo "================================"
echo "🚀 AiCane Navigation 초기 설정"
echo "================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Python 버전 체크
echo "1️⃣  Python 버전 확인..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "   ${GREEN}✓${NC} Python $python_version"
echo ""

# 2. 필수 패키지 설치 확인
echo "2️⃣  필수 패키지 확인..."
packages=("numpy" "pyyaml" "pyserial")
missing_packages=()

for package in "${packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} $package 설치됨"
    else
        echo -e "   ${RED}✗${NC} $package 누락"
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}누락된 패키지 설치 중...${NC}"
    pip3 install "${missing_packages[@]}"
fi
echo ""

# 3. 블루투스 도구 확인
echo "3️⃣  블루투스 도구 확인..."
if command -v bluetoothctl &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} bluetoothctl 설치됨"
else
    echo -e "   ${RED}✗${NC} bluetoothctl 누락"
    echo -e "   ${YELLOW}설치: sudo apt-get install bluetooth bluez${NC}"
fi

if command -v rfcomm &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} rfcomm 설치됨"
else
    echo -e "   ${RED}✗${NC} rfcomm 누락"
    echo -e "   ${YELLOW}설치: sudo apt-get install bluez-tools${NC}"
fi
echo ""

# 4. 시리얼 포트 확인
echo "4️⃣  시리얼 포트 확인..."
found_port=false

for port in /dev/rfcomm* /dev/ttyUSB* /dev/ttyACM*; do
    if [ -e "$port" ]; then
        echo -e "   ${GREEN}✓${NC} $port 발견"
        found_port=true
        
        # 권한 확인
        if [ -r "$port" ] && [ -w "$port" ]; then
            echo -e "      ${GREEN}권한 OK${NC}"
        else
            echo -e "      ${YELLOW}권한 필요: sudo chmod 666 $port${NC}"
        fi
    fi
done

if [ "$found_port" = false ]; then
    echo -e "   ${YELLOW}⚠${NC} 포트가 발견되지 않음"
    echo "      블루투스 연결 또는 USB 케이블 확인 필요"
fi
echo ""

# 5. MAC 주소 스캔
echo "5️⃣  블루투스 장치 스캔..."
echo "   (3초간 스캔...)"
timeout 3s sudo hcitool scan 2>/dev/null || echo -e "   ${YELLOW}⚠${NC} 스캔 실패 (권한 또는 블루투스 비활성화)"
echo ""

# 6. 설정 파일 확인
echo "6️⃣  설정 파일 확인..."
config_file="config/hardware.yaml"

if [ -f "$config_file" ]; then
    echo -e "   ${GREEN}✓${NC} $config_file 존재"
    
    # MAC 주소 설정 확인
    if grep -q "XX:XX:XX" "$config_file"; then
        echo -e "   ${YELLOW}⚠${NC} MAC 주소 미설정"
        echo "      편집: nano $config_file"
    else
        mac_address=$(grep "bluetooth_mac:" "$config_file" | awk '{print $2}' | tr -d "'\"")
        echo -e "   ${GREEN}✓${NC} MAC 주소 설정됨: $mac_address"
    fi
else
    echo -e "   ${RED}✗${NC} $config_file 없음"
fi
echo ""

# 7. 디렉토리 구조 확인
echo "7️⃣  디렉토리 구조 확인..."
dirs=("aicane_navigation" "scripts" "config" "maps")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✓${NC} $dir/"
    else
        echo -e "   ${RED}✗${NC} $dir/ 누락"
    fi
done
echo ""

# 8. 테스트 실행 제안
echo "================================"
echo "🎯 다음 단계"
echo "================================"
echo ""
echo "1. MAC 주소 설정 (필요시):"
echo "   nano config/hardware.yaml"
echo ""
echo "2. 센서 테스트:"
echo "   python scripts/test_sensors.py"
echo ""
echo "3. 주행 테스트:"
echo "   python scripts/navigate.py --from 101호 --to 107호 --mock"
echo ""
echo "4. 블루투스 페어링 (필요시):"
echo "   bluetoothctl"
echo "   > pair <MAC_ADDRESS>"
echo "   > trust <MAC_ADDRESS>"
echo ""
echo "================================"

# 9. 요약
echo ""
echo "📊 요약"
echo "================================"
if [ ${#missing_packages[@]} -eq 0 ] && [ -f "$config_file" ]; then
    echo -e "${GREEN}✅ 기본 설정 완료!${NC}"
else
    echo -e "${YELLOW}⚠️  일부 설정 필요${NC}"
fi
echo ""
