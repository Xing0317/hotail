from enum import Enum

class RoomType(Enum):
    HOURLY = "hourly"
    DAILY = "daily"

class RoomStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class Room:
    def __init__(self, room_number, room_type, price, status=RoomStatus.AVAILABLE):
        self.room_number = room_number
        self.room_type = RoomType(room_type)
        self.price = price
        self.status = status
    
    def to_dict(self):
        return {
            "room_number": self.room_number,
            "room_type": self.room_type.value,
            "price": self.price,
            "status": self.status.value
        } 