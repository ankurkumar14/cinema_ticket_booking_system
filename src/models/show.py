from dataclasses import dataclass
from datetime import datetime
from src.utils.enums import ShowStatus


@dataclass
class Show:
    show_id: str
    cinema: str
    movie: str
    start_time: datetime
    price: int              # using int for rupees for deterministic math
    capacity: int
    seats_remaining: int
    status: ShowStatus = ShowStatus.REGISTERED
