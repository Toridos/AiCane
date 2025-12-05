#!/usr/bin/env python3
"""
메인 주행 스크립트
방 간 이동 또는 AI 경로 추종
"""

import argparse
import json
import sys

from aicane_navigation import NavigationSystem


def main():
    parser = argparse.ArgumentParser(
        description='AiCane 자율주행 로봇 주행'
    )
    
    # 모드 선택
    parser.add_argument(
        '--mode',
        choices=['rooms', 'ai_path'],
        default='rooms',
        help='주행 모드: rooms (방 간 이동) 또는 ai_path (AI 경로)'
    )
    
    # 방 간 이동 옵션
    parser.add_argument(
        '--from',
        dest='from_room',
        help='출발 방 (예: 101호)'
    )
    parser.add_argument(
        '--to',
        dest='to_room',
        help='도착 방 (예: 107호)'
    )
    
    # AI 경로 옵션
    parser.add_argument(
        '--path-file',
        help='AI 경로 JSON 파일 경로'
    )
    
    # 공통 옵션
    parser.add_argument(
        '--config',
        default='./config',
        help='설정 파일 디렉토리'
    )
    parser.add_argument(
        '--hz',
        type=float,
        default=5.0,
        help='제어 주기 (Hz)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Mock 모드 (테스트용)'
    )
    
    args = parser.parse_args()
    
    # 모드별 필수 인자 확인
    if args.mode == 'rooms':
        if not args.from_room or not args.to_room:
            parser.error("rooms 모드는 --from과 --to가 필요합니다")
    elif args.mode == 'ai_path':
        if not args.path_file:
            parser.error("ai_path 모드는 --path-file이 필요합니다")
    
    # 시스템 초기화
    print("🚀 AiCane Navigation System\n")
    
    try:
        nav = NavigationSystem(
            config_dir=args.config,
            mock=args.mock
        )
        
        # 주행 실행
        if args.mode == 'rooms':
            # 방 간 이동
            nav.navigate_rooms(
                args.from_room,
                args.to_room,
                control_hz=args.hz
            )
        
        elif args.mode == 'ai_path':
            # AI 경로 로드
            with open(args.path_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 다양한 JSON 형식 지원
            pixel_path = parse_ai_path(data)
            
            print(f"📍 경로 포인트: {len(pixel_path)}개")
            print(f"   시작: ({pixel_path[0][0]}, {pixel_path[0][1]})")
            print(f"   끝: ({pixel_path[-1][0]}, {pixel_path[-1][1]})\n")
            
            # AI 경로 추종
            nav.navigate_ai_path(
                pixel_path,
                control_hz=args.hz
            )
        
        # 종료
        nav.shutdown()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n⏸️ 사용자 중단")
        return 1
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


def parse_ai_path(data):
    """
    다양한 JSON 형식을 픽셀 경로로 변환
    
    지원 형식:
    1. {"waypoints": [{"x": 100, "y": 200}, ...]}
    2. [{"x": 100, "y": 200}, ...]
    3. [{"x": 100, "y": 200, "floor": 1}, ...]  ← 신규!
    4. [[100, 200], ...]
    5. [(100, 200), ...]
    
    Args:
        data: JSON 데이터
    
    Returns:
        list: [(x, y), ...] 픽셀 좌표 리스트
    """
    # 형식 1: {"waypoints": [...]}
    if isinstance(data, dict) and 'waypoints' in data:
        waypoints = data['waypoints']
    elif isinstance(data, list):
        waypoints = data
    else:
        raise ValueError(
            "지원하지 않는 경로 형식입니다.\n"
            "지원 형식:\n"
            "  1. {\"waypoints\": [{\"x\": 100, \"y\": 200}, ...]}\n"
            "  2. [{\"x\": 100, \"y\": 200}, ...]\n"
            "  3. [{\"x\": 100, \"y\": 200, \"floor\": 1}, ...]\n"
            "  4. [[100, 200], ...]\n"
        )
    
    # 빈 경로 체크
    if not waypoints:
        raise ValueError("경로가 비어있습니다")
    
    # 첫 번째 포인트로 형식 판단
    first = waypoints[0]
    
    # 형식 2, 3: {"x": ..., "y": ..., "floor": ...}
    if isinstance(first, dict):
        if 'x' in first and 'y' in first:
            # floor 키는 무시하고 x, y만 추출
            pixel_path = [(p['x'], p['y']) for p in waypoints]
        else:
            raise ValueError(
                f"딕셔너리 형식이지만 'x', 'y' 키가 없습니다: {first}"
            )
    
    # 형식 4: [[100, 200], ...]
    elif isinstance(first, list):
        if len(first) >= 2:
            pixel_path = [(p[0], p[1]) for p in waypoints]
        else:
            raise ValueError(
                f"리스트 항목이 최소 2개 필요합니다 (x, y): {first}"
            )
    
    # 형식 5: [(100, 200), ...]
    elif isinstance(first, tuple):
        if len(first) >= 2:
            pixel_path = [(p[0], p[1]) for p in waypoints]
        else:
            raise ValueError(
                f"튜플 항목이 최소 2개 필요합니다 (x, y): {first}"
            )
    
    else:
        raise ValueError(
            f"지원하지 않는 포인트 형식입니다: {type(first)}"
        )
    
    return pixel_path


if __name__ == '__main__':
    sys.exit(main())
