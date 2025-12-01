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
            with open(args.path_file, 'r') as f:
                data = json.load(f)
            
            if 'waypoints' in data:
                pixel_path = [(p['x'], p['y']) for p in data['waypoints']]
            elif isinstance(data, list):
                pixel_path = data
            else:
                raise ValueError("경로 형식 오류: 'waypoints' 키 또는 리스트 필요")
            
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


if __name__ == '__main__':
    sys.exit(main())
