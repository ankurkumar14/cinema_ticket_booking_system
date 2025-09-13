from dataclasses import dataclass
from datetime import datetime
from src.utils.enums import BookingStatus


@dataclass
class Booking:
    booking_id: str
    show_id: str
    quantity: int
    unit_price: int
    status: BookingStatus
    created_at: datetime
