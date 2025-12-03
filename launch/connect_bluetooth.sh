#!/bin/bash
# 블루투스 자동 연결 스크립트
# MAC 주소만 있으면 자동으로 모든 과정 처리

echo "================================"
echo "🔗 블루투스 자동 연결"
echo "================================"
echo ""

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# MAC 주소 읽기
CONFIG_FILE="config/hardware.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 설정 파일 없음: $CONFIG_FILE${NC}"
    exit 1
fi

MAC_ADDRESS=$(grep "bluetooth_mac:" "$CONFIG_FILE" | awk '{print $2}' | tr -d "'\"")

if [ -z "$MAC_ADDRESS" ] || [ "$MAC_ADDRESS" == "XX:XX:XX" ]; then
    echo -e "${RED}❌ MAC 주소가 설정되지 않음${NC}"
    echo ""
    echo "1. MAC 주소 찾기:"
    echo "   sudo hcitool scan"
    echo ""
    echo "2. 설정 파일에 입력:"
    echo "   nano $CONFIG_FILE"
    exit 1
fi

echo "MAC 주소: $MAC_ADDRESS"
echo ""

# 1. 블루투스 서비스 확인
echo "1️⃣  블루투스 서비스 확인..."
if systemctl is-active --quiet bluetooth; then
    echo -e "   ${GREEN}✓${NC} 블루투스 활성화됨"
else
    echo -e "   ${YELLOW}⚠${NC} 블루투스 시작 중..."
    sudo systemctl start bluetooth
    sleep 2
fi
echo ""

# 2. 기존 연결 해제
echo "2️⃣  기존 연결 확인..."
if [ -e /dev/rfcomm0 ]; then
    echo -e "   ${YELLOW}⚠${NC} 기존 연결 해제 중..."
    sudo rfcomm release 0 2>/dev/null
    sleep 1
fi
echo ""

# 3. 페어링 확인
echo "3️⃣  페어링 확인..."
if bluetoothctl info "$MAC_ADDRESS" 2>/dev/null | grep -q "Paired: yes"; then
    echo -e "   ${GREEN}✓${NC} 이미 페어링됨"
else
    echo -e "   ${YELLOW}⚠${NC} 페어링 시도..."
    echo "   PIN 입력이 필요할 수 있습니다 (보통 1234 또는 0000)"
    
    # 자동 페어링 시도
    (
        sleep 1
        echo "pair $MAC_ADDRESS"
        sleep 3
        echo "1234"
        sleep 2
        echo "trust $MAC_ADDRESS"
        sleep 1
        echo "exit"
    ) | bluetoothctl
    
    sleep 2
fi
echo ""

# 4. rfcomm 바인딩
echo "4️⃣  시리얼 포트 바인딩..."
if sudo rfcomm bind 0 "$MAC_ADDRESS" 1; then
    echo -e "   ${GREEN}✓${NC} rfcomm0 바인딩 성공"
    sleep 2
    
    # 권한 설정
    if sudo chmod 666 /dev/rfcomm0; then
        echo -e "   ${GREEN}✓${NC} 권한 설정 완료"
    fi
else
    echo -e "   ${RED}❌ 바인딩 실패${NC}"
    exit 1
fi
echo ""

# 5. 연결 확인
echo "5️⃣  연결 확인..."
if [ -e /dev/rfcomm0 ]; then
    echo -e "   ${GREEN}✅ 연결 성공!${NC}"
    echo "   포트: /dev/rfcomm0"
    ls -l /dev/rfcomm0
else
    echo -e "   ${RED}❌ 연결 실패${NC}"
    exit 1
fi
echo ""

# 6. 테스트 제안
echo "================================"
echo "🎉 블루투스 연결 완료!"
echo "================================"
echo ""
echo "다음 단계:"
echo "1. 센서 테스트:"
echo "   python scripts/test_sensors.py"
echo ""
echo "2. 주행 테스트:"
echo "   python scripts/navigate.py --from 101호 --to 107호"
echo ""
