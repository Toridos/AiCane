#!/bin/bash
# 자동 주행 시작 스크립트
# 모든 준비 과정을 자동화

echo "================================"
echo "🚀 AiCane 자동 주행 시작"
echo "================================"
echo ""

# 색상
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 파라미터 파싱
FROM_ROOM=""
TO_ROOM=""
MOCK_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --from)
            FROM_ROOM="$2"
            shift 2
            ;;
        --to)
            TO_ROOM="$2"
            shift 2
            ;;
        --mock)
            MOCK_MODE="--mock"
            shift
            ;;
        *)
            echo "알 수 없는 옵션: $1"
            echo "사용법: $0 --from 101호 --to 107호 [--mock]"
            exit 1
            ;;
    esac
done

# 필수 파라미터 체크
if [ -z "$FROM_ROOM" ] || [ -z "$TO_ROOM" ]; then
    echo -e "${RED}❌ 출발/도착 방 지정 필요${NC}"
    echo "사용법: $0 --from 101호 --to 107호 [--mock]"
    exit 1
fi

# 1. 블루투스 연결 확인
echo "1️⃣  블루투스 연결 확인..."
if [ -z "$MOCK_MODE" ]; then
    # 실제 모드
    if ls /dev/rfcomm* 1> /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} 블루투스 포트 발견"
    elif ls /dev/ttyUSB* 1> /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} USB 포트 발견"
    else
        echo -e "   ⚠️  포트 없음, Mock 모드 권장"
        read -p "   Mock 모드로 실행할까요? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            MOCK_MODE="--mock"
        fi
    fi
else
    echo -e "   ${GREEN}✓${NC} Mock 모드"
fi
echo ""

# 2. 로그 디렉토리 생성
echo "2️⃣  로그 디렉토리 준비..."
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/navigation_${FROM_ROOM}_to_${TO_ROOM}_${TIMESTAMP}.log"
echo -e "   ${GREEN}✓${NC} $LOG_FILE"
echo ""

# 3. 주행 시작
echo "3️⃣  주행 시작..."
echo "   출발: $FROM_ROOM"
echo "   도착: $TO_ROOM"
[ -n "$MOCK_MODE" ] && echo "   모드: Mock"
echo ""
echo "================================"
echo ""

# 실행
python scripts/navigate.py \
    --mode rooms \
    --from "$FROM_ROOM" \
    --to "$TO_ROOM" \
    $MOCK_MODE \
    2>&1 | tee "$LOG_FILE"

# 결과
exit_code=$?
echo ""
echo "================================"
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ 주행 완료!${NC}"
else
    echo -e "${RED}❌ 주행 실패 (코드: $exit_code)${NC}"
fi
echo "로그: $LOG_FILE"
echo "================================"

exit $exit_code
