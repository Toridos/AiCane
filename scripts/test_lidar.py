#!/usr/bin/env python3
"""
LiDAR 테스트 스크립트
RPLidar X4 Pro 동작 확인
"""

import sys
import time
from aicane_navigation.hardware import LidarInterface


def test_connection(mock=False):
    """연결 테스트"""
    print("\n" + "="*50)
    print("1️⃣  연결 테스트")
    print("="*50 + "\n")
    
    lidar = LidarInterface(mock=mock)
    
    if lidar.open():
        print("✅ 연결 성공")
        stats = lidar.get_stats()
        print(f"   모드: {stats['mode']}")
        lidar.close()
        return True
    else:
        print("❌ 연결 실패")
        return False


def test_scan(mock=False, duration=5):
    """스캔 테스트"""
    print("\n" + "="*50)
    print(f"2️⃣  스캔 테스트 ({duration}초)")
    print("="*50 + "\n")
    
    with LidarInterface(mock=mock) as lidar:
        print(f"{duration}초간 스캔 중...\n")
        
        start_time = time.time()
        scan_count = 0
        
        while time.time() - start_time < duration:
            scan = lidar.get_latest_scan()
            scan_count += 1
            
            if scan:
                print(f"\r스캔 {scan_count}: {len(scan)}개 포인트", 
                      end='', flush=True)
            
            time.sleep(0.05)
        
        print(f"\n\n✅ 총 {scan_count}회 스캔 완료")
        
        # 최종 통계
        stats = lidar.get_stats()
        print(f"   총 스캔: {stats['scan_count']}회")
        print(f"   평균 Hz: {stats['scan_count'] / duration:.1f} Hz")


def test_sectors(mock=False):
    """섹터별 스캔 테스트"""
    print("\n" + "="*50)
    print("3️⃣  섹터별 스캔 테스트")
    print("="*50 + "\n")
    
    with LidarInterface(mock=mock) as lidar:
        time.sleep(1)  # 안정화
        
        sectors = [
            (0, "정면"),
            (90, "좌측"),
            (180, "후면"),
            (270, "우측"),
        ]
        
        for angle, name in sectors:
            scan = lidar.get_scan_in_sector(angle, 60)
            min_dist = lidar.get_min_distance_in_sector(angle, 60)
            
            print(f"  {name} ({angle}° ±30°):")
            print(f"    포인트: {len(scan)}개")
            if min_dist:
                print(f"    최소 거리: {min_dist:.1f}cm")
            print()
        
        print("✅ 섹터 테스트 완료")


def test_obstacles(mock=False):
    """장애물 감지 테스트"""
    print("\n" + "="*50)
    print("4️⃣  장애물 감지 테스트")
    print("="*50 + "\n")
    
    with LidarInterface(mock=mock) as lidar:
        time.sleep(1)
        
        print("10초간 정면 장애물 모니터링...\n")
        
        for i in range(50):  # 20Hz x 50 = ~2.5초
            front_min = lidar.get_min_distance_in_sector(0, 60)
            
            if front_min:
                if front_min < 25:
                    status = "🛑 긴급!"
                elif front_min < 50:
                    status = "⚠️  경고"
                else:
                    status = "✅ 안전"
                
                print(f"\r정면 최소 거리: {front_min:6.1f}cm  {status}", 
                      end='', flush=True)
            
            time.sleep(0.2)
        
        print("\n\n✅ 장애물 감지 테스트 완료")


def test_gap_finding(mock=False):
    """빈 공간 찾기 테스트"""
    print("\n" + "="*50)
    print("5️⃣  빈 공간 찾기 테스트")
    print("="*50 + "\n")
    
    with LidarInterface(mock=mock) as lidar:
        time.sleep(1)
        
        gaps = lidar.find_gaps(min_gap_width=60, min_distance=50)
        
        print(f"발견된 통과 가능 공간: {len(gaps)}개\n")
        
        for i, gap in enumerate(gaps[:5], 1):
            print(f"  {i}. 각도: {gap['angle']:6.1f}° "
                  f"({gap['angle_start']:.1f}° ~ {gap['angle_end']:.1f}°)")
            print(f"     거리: {gap['distance']:6.1f}cm")
            print(f"     폭:   {gap['width']:6.1f}cm")
            print()
        
        print("✅ 빈 공간 찾기 완료")


def test_visualization(mock=False):
    """간단한 시각화"""
    print("\n" + "="*50)
    print("6️⃣  ASCII 시각화")
    print("="*50 + "\n")
    
    with LidarInterface(mock=mock) as lidar:
        time.sleep(1)
        
        scan = lidar.get_latest_scan()
        
        if not scan:
            print("스캔 데이터 없음")
            return
        
        # 8방향 표시
        directions = {
            0: "→",    # 정면
            45: "↗",
            90: "↑",   # 좌측
            135: "↖",
            180: "←",  # 후면
            225: "↙",
            270: "↓",  # 우측
            315: "↘",
        }
        
        print("방향별 최소 거리:\n")
        
        for angle, arrow in directions.items():
            sector_scan = [d for a, d in scan 
                          if angle - 22.5 <= a <= angle + 22.5]
            
            if sector_scan:
                min_dist = min(sector_scan)
                
                # 거리에 따른 바 그래프
                bar_length = int(min_dist / 10)  # 10cm당 1칸
                bar = "█" * min(bar_length, 20)
                
                print(f"{arrow} {angle:3d}°: {min_dist:6.1f}cm  {bar}")
        
        print("\n✅ 시각화 완료")


def main():
    print("🔍 LiDAR 테스트 프로그램")
    print("="*50)
    
    # 모드 선택
    print("\n모드 선택:")
    print("  1. Mock 모드 (LiDAR 없이 테스트)")
    print("  2. 실제 LiDAR")
    
    choice = input("\n선택 (1/2): ").strip()
    
    mock = (choice == '1')
    
    if mock:
        print("\n🧪 Mock 모드로 시작")
    else:
        print("\n🔌 실제 LiDAR로 시작")
    
    # 테스트 실행
    try:
        # 1. 연결
        if not test_connection(mock):
            print("\n❌ 연결 실패, 종료합니다")
            return 1
        
        # 2. 스캔
        test_scan(mock, duration=3)
        
        # 3. 섹터
        test_sectors(mock)
        
        # 4. 장애물
        test_obstacles(mock)
        
        # 5. 빈 공간
        test_gap_finding(mock)
        
        # 6. 시각화
        test_visualization(mock)
        
        print("\n" + "="*50)
        print("🎉 모든 테스트 완료!")
        print("="*50)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏸️  사용자 중단")
        return 1
    
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
