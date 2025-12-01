# 방위치 관리

# mapping/room_manager.py
class RoomManager:
    """방 위치 및 정보 관리"""
    
    rooms: dict = {
        '101호': {'door_x': ..., 'door_y': ..., ...},
        ...
    }
    
    def get_room_info(self, room_name: str) -> dict
    def list_all_rooms(self) -> list