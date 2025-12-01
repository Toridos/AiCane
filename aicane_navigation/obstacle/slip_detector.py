"""
장애물 vs 미끄러짐 구분 로직
초음파 변화 패턴 분석
"""


class ObstacleVsSlipDetector:
    """
    장애물 출현 vs 미끄러짐 구분
    
    판단 기준:
    1. 급격한 변화 (>40cm) → 장애물 출현
    2. 점진적 변화 (트렌드) → 미끄러짐
    3. 양쪽 반대 변화 → 미끄러짐
    """
    
    def __init__(self, floor_map):
        """
        Args:
            floor_map: FloorPlan 인스턴스
        """
        self.map = floor_map
        
        # 임계값
        self.SUDDEN_CHANGE_THRESHOLD = 40  # cm
        self.GRADUAL_CHANGE_THRESHOLD = 10  # cm
    
    def analyze_ultrasonic_change(self, 
                                   current_distances,
                                   expected_distances,
                                   history,
                                   current_pose):
        """
        초음파 변화 분석
        
        Args:
            current_distances (dict): {'left': cm, 'right': cm}
            expected_distances (dict): {'left': cm, 'right': cm}
            history (dict): {'left': [cm, ...], 'right': [cm, ...]}
            current_pose (tuple): (x, y, theta)
        
        Returns:
            dict: {
                'left': {'type': 'normal'|'obstacle'|'slip', ...},
                'right': {...},
                'action': 'continue'|'avoid_left'|'avoid_right'|'stop'
            }
        """
        result = {
            'left': self._analyze_side('left',
                                       current_distances.get('left'),
                                       expected_distances.get('left'),
                                       history.get('left', [])),
            'right': self._analyze_side('right',
                                        current_distances.get('right'),
                                        expected_distances.get('right'),
                                        history.get('right', [])),
        }
        
        # 액션 결정
        left_type = result['left']['type']
        right_type = result['right']['type']
        
        if left_type == 'obstacle' and right_type == 'obstacle':
            result['action'] = 'stop'  # 양쪽 막힘
        elif left_type == 'obstacle':
            result['action'] = 'avoid_left'  # 오른쪽으로
        elif right_type == 'obstacle':
            result['action'] = 'avoid_right'  # 왼쪽으로
        elif left_type == 'slip' or right_type == 'slip':
            result['action'] = 'correct_position'  # 위치 보정
        else:
            result['action'] = 'continue'
        
        return result
    
    def _analyze_side(self, side, current_dist, expected_dist, history):
        """
        한쪽 센서 분석
        
        Returns:
            dict: {
                'type': 'normal' | 'obstacle' | 'slip' | 'uncertain',
                'confidence': 0~1,
                'reason': str,
                'diff': cm
            }
        """
        if current_dist is None or expected_dist is None:
            return {
                'type': 'normal',
                'confidence': 0,
                'reason': 'no_data',
                'diff': 0
            }
        
        # 차이 계산
        diff = expected_dist - current_dist
        
        # 이력 트렌드
        if len(history) >= 5:
            trend = self._calculate_trend(history[-5:])
        else:
            trend = 0
        
        # ═══════════════════════════════════════
        # 판단 로직
        # ═══════════════════════════════════════
        
        # Case 1: 급격한 변화 (>40cm)
        if abs(diff) > self.SUDDEN_CHANGE_THRESHOLD:
            if diff > 0:  # 예상보다 가까움
                # 장애물 출현!
                return {
                    'type': 'obstacle',
                    'confidence': 0.9,
                    'reason': f'sudden_closer_{diff:.1f}cm',
                    'diff': diff
                }
            else:  # 예상보다 멀음
                # 반대편으로 많이 미끄러짐
                return {
                    'type': 'slip',
                    'confidence': 0.7,
                    'reason': f'sudden_farther_{abs(diff):.1f}cm',
                    'diff': diff
                }
        
        # Case 2: 점진적 변화 (트렌드)
        if abs(trend) > 2.0:  # cm/step
            # 지속적으로 한쪽으로 치우침 → 미끄러짐
            return {
                'type': 'slip',
                'confidence': 0.6,
                'reason': f'gradual_drift_{trend:.1f}cm/step',
                'diff': diff
            }
        
        # Case 3: 정상
        if abs(diff) < self.GRADUAL_CHANGE_THRESHOLD:
            return {
                'type': 'normal',
                'confidence': 1.0,
                'reason': 'within_tolerance',
                'diff': diff
            }
        
        # Case 4: 애매한 경우 (10~40cm)
        return {
            'type': 'uncertain',
            'confidence': 0.3,
            'reason': f'moderate_diff_{diff:.1f}cm',
            'diff': diff
        }
    
    def _calculate_trend(self, history):
        """
        이력 트렌드 계산 (선형 회귀)
        
        Args:
            history (list): 거리 측정 이력
        
        Returns:
            float: slope (cm/step) - 양수면 멀어짐, 음수면 가까워짐
        """
        if len(history) < 2:
            return 0
        
        n = len(history)
        x = list(range(n))
        y = history
        
        # 간단한 선형 회귀
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope


if __name__ == '__main__':
    print("=== ObstacleVsSlipDetector 테스트 ===\n")
    
    from ..mapping.floor_plan import FloorPlan
    
    floor_map = FloorPlan()
    detector = ObstacleVsSlipDetector(floor_map)
    
    # 시나리오 1: 장애물 출현 (급격한 변화)
    print("1️⃣ 장애물 출현 시나리오:")
    current = {'left': 120, 'right': 120}
    expected = {'left': 120, 'right': 80}  # 오른쪽에 갑자기 장애물!
    history = {'left': [120, 120, 120], 'right': [120, 120, 120]}
    
    result = detector.analyze_ultrasonic_change(
        current, expected, history, (0, 0, 0)
    )
    
    print(f"   오른쪽: {result['right']['type']} ({result['right']['reason']})")
    print(f"   액션: {result['action']}")
    
    # 시나리오 2: 미끄러짐 (점진적 변화)
    print("\n2️⃣ 미끄러짐 시나리오:")
    current = {'left': 105, 'right': 135}
    expected = {'left': 120, 'right': 120}
    history = {'left': [120, 115, 110, 108, 105], 
               'right': [120, 125, 130, 132, 135]}
    
    result = detector.analyze_ultrasonic_change(
        current, expected, history, (0, 0, 0)
    )
    
    print(f"   왼쪽: {result['left']['type']} ({result['left']['reason']})")
    print(f"   오른쪽: {result['right']['type']} ({result['right']['reason']})")
    print(f"   액션: {result['action']}")
    
    print("\n✅ 테스트 완료")
