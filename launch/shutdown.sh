#!/bin/bash
# 시스템 종료 및 정리 스크립트

echo "================================"
echo "🛑 AiCane Navigation 종료"
echo "================================"
echo ""

GREEN='\033[0;32m'
NC='\033[0m'

# 1. 실행 중인 프로세스 종료
echo "1️⃣  프로세스 종료..."
pkill -f "navigate.py" 2>/dev/null
pkill -f "navigation_system" 2>/dev/null
echo -e "   ${GREEN}✓${NC} 완료"
echo ""

# 2. 블루투스 연결 해제
echo "2️⃣  블루투스 연결 해제..."
if [ -e /dev/rfcomm0 ]; then
    sudo rfcomm release 0 2>/dev/null
    echo -e "   ${GREEN}✓${NC} rfcomm0 해제됨"
else
    echo "   (연결 없음)"
fi
echo ""

# 3. 로그 정리
echo "3️⃣  오래된 로그 정리 (30일 이상)..."
if [ -d "logs" ]; then
    old_logs=$(find logs -name "*.log" -mtime +30 2>/dev/null | wc -l)
    if [ "$old_logs" -gt 0 ]; then
        find logs -name "*.log" -mtime +30 -delete
        echo -e "   ${GREEN}✓${NC} ${old_logs}개 로그 삭제됨"
    else
        echo "   (없음)"
    fi
else
    echo "   (로그 디렉토리 없음)"
fi
echo ""

# 4. 임시 파일 정리
echo "4️⃣  임시 파일 정리..."
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo -e "   ${GREEN}✓${NC} 완료"
echo ""

echo "================================"
echo -e "${GREEN}✅ 종료 완료${NC}"
echo "================================"
echo ""
