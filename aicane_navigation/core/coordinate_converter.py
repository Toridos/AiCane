"""
좌표 변환 유틸리티
픽셀 ↔ cm 변환
"""


class CoordinateConverter:
    """
    픽셀과 cm 단위 간 좌표 변환
    
    축척: 1픽셀 = 3.8cm (도면 실측 기반)
    """
    
    # 확정된 축척
    PIXEL_TO_CM = 3.8  # 1픽셀 = 3.8cm
    CM_TO_PIXEL = 1.0 / 3.8  # 1cm ≈ 0.263 픽셀
    
    @classmethod
    def pixel_to_cm(cls, x_pixel, y_pixel):
        """
        픽셀 좌표 → cm 좌표
        
        Args:
            x_pixel (float): X 좌표 (픽셀)
            y_pixel (float): Y 좌표 (픽셀)
        
        Returns:
            tuple: (x_cm, y_cm)
        
        Example:
            >>> CoordinateConverter.pixel_to_cm(100, 200)
            (380.0, 760.0)
        """
        x_cm = x_pixel * cls.PIXEL_TO_CM
        y_cm = y_pixel * cls.PIXEL_TO_CM
        return (x_cm, y_cm)
    
    @classmethod
    def cm_to_pixel(cls, x_cm, y_cm):
        """
        cm 좌표 → 픽셀 좌표
        
        Args:
            x_cm (float): X 좌표 (cm)
            y_cm (float): Y 좌표 (cm)
        
        Returns:
            tuple: (x_pixel, y_pixel)
        
        Example:
            >>> CoordinateConverter.cm_to_pixel(380, 760)
            (100.0, 200.0)
        """
        x_pixel = x_cm * cls.CM_TO_PIXEL
        y_pixel = y_cm * cls.CM_TO_PIXEL
        return (x_pixel, y_pixel)
    
    @classmethod
    def path_pixel_to_cm(cls, pixel_path):
        """
        경로 일괄 변환 (픽셀 → cm)
        
        Args:
            pixel_path (list): [(x1, y1), (x2, y2), ...] 픽셀 좌표 리스트
        
        Returns:
            list: [(x1_cm, y1_cm), ...] cm 좌표 리스트
        
        Example:
            >>> path = [(50, 100), (100, 100), (150, 100)]
            >>> CoordinateConverter.path_pixel_to_cm(path)
            [(190.0, 380.0), (380.0, 380.0), (570.0, 380.0)]
        """
        return [cls.pixel_to_cm(x, y) for x, y in pixel_path]
    
    @classmethod
    def path_cm_to_pixel(cls, cm_path):
        """
        경로 일괄 변환 (cm → 픽셀)
        
        Args:
            cm_path (list): [(x1, y1), (x2, y2), ...] cm 좌표 리스트
        
        Returns:
            list: [(x1_px, y1_px), ...] 픽셀 좌표 리스트
        """
        return [cls.cm_to_pixel(x, y) for x, y in cm_path]
    
    @classmethod
    def distance_pixel_to_cm(cls, distance_pixel):
        """
        거리 변환 (픽셀 → cm)
        
        Args:
            distance_pixel (float): 거리 (픽셀)
        
        Returns:
            float: 거리 (cm)
        """
        return distance_pixel * cls.PIXEL_TO_CM
    
    @classmethod
    def distance_cm_to_pixel(cls, distance_cm):
        """
        거리 변환 (cm → 픽셀)
        
        Args:
            distance_cm (float): 거리 (cm)
        
        Returns:
            float: 거리 (픽셀)
        """
        return distance_cm * cls.CM_TO_PIXEL


if __name__ == '__main__':
    # 테스트
    print("=== 좌표 변환 테스트 ===")
    
    # 픽셀 → cm
    px, py = 100, 200
    cx, cy = CoordinateConverter.pixel_to_cm(px, py)
    print(f"픽셀 ({px}, {py}) → cm ({cx}, {cy})")
    
    # cm → 픽셀
    px2, py2 = CoordinateConverter.cm_to_pixel(cx, cy)
    print(f"cm ({cx}, {cy}) → 픽셀 ({px2}, {py2})")
    
    # 경로 변환
    path = [(50, 100), (100, 100), (150, 100)]
    cm_path = CoordinateConverter.path_pixel_to_cm(path)
    print(f"\n경로 변환:")
    for i, (px_coord, cm_coord) in enumerate(zip(path, cm_path)):
        print(f"  {i}: 픽셀 {px_coord} → cm {cm_coord}")
