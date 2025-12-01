"""
이동 평균 필터
센서 노이즈 제거용
"""


class MovingAverageFilter:
    """
    이동 평균 필터
    
    센서 측정값의 노이즈를 제거하기 위한 간단한 필터
    """
    
    def __init__(self, window=5):
        """
        Args:
            window (int): 윈도우 크기 (평균을 계산할 샘플 개수)
        """
        self.window = window
        self.data = []
    
    def update(self, value):
        """
        새로운 값 추가 및 필터링된 값 반환
        
        Args:
            value (float): 새로운 측정값 (None이면 무시)
        
        Returns:
            float or None: 필터링된 값 (데이터 부족 시 None)
        
        Example:
            >>> filter = MovingAverageFilter(window=3)
            >>> filter.update(10.0)
            10.0
            >>> filter.update(12.0)
            11.0
            >>> filter.update(11.0)
            11.0
        """
        # 유효하지 않은 값은 무시
        if value is None or value < 0:
            return None
        
        # 데이터 추가
        self.data.append(value)
        
        # 윈도우 크기 유지
        if len(self.data) > self.window:
            self.data.pop(0)
        
        # 평균 반환
        if len(self.data) == 0:
            return None
        
        return sum(self.data) / len(self.data)
    
    def reset(self):
        """
        필터 초기화
        """
        self.data = []
    
    def get_current_value(self):
        """
        현재 필터링된 값 반환 (업데이트 없이)
        
        Returns:
            float or None: 현재 값
        """
        if len(self.data) == 0:
            return None
        return sum(self.data) / len(self.data)
    
    def is_ready(self):
        """
        필터가 충분한 데이터를 가지고 있는지 확인
        
        Returns:
            bool: 윈도우가 가득 찼는지 여부
        """
        return len(self.data) >= self.window
    
    def __repr__(self):
        return f"MovingAverageFilter(window={self.window}, data={len(self.data)}/{self.window})"


if __name__ == '__main__':
    # 테스트
    print("=== 이동 평균 필터 테스트 ===\n")
    
    # 노이즈가 있는 데이터
    noisy_data = [100, 105, 98, 103, 101, 99, 102, 100, 104, 98]
    
    # 필터 적용
    filter_3 = MovingAverageFilter(window=3)
    filter_5 = MovingAverageFilter(window=5)
    
    print("윈도우 크기별 필터링 결과:")
    print(f"{'원본':>6} | {'윈도우=3':>8} | {'윈도우=5':>8}")
    print("-" * 32)
    
    for value in noisy_data:
        filtered_3 = filter_3.update(value)
        filtered_5 = filter_5.update(value)
        
        f3_str = f"{filtered_3:.1f}" if filtered_3 else "N/A"
        f5_str = f"{filtered_5:.1f}" if filtered_5 else "N/A"
        
        print(f"{value:6d} | {f3_str:>8} | {f5_str:>8}")
    
    print("\n✅ 노이즈 제거 효과:")
    print(f"   원본 표준편차: {(sum((x-100)**2 for x in noisy_data)/len(noisy_data))**0.5:.2f}")
