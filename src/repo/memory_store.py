from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime
import threading

from src.models.show import Show
from src.models.booking import Booking
from src.utils.enums import ShowStatus, BookingStatus
from src.utils.errors import (
    ShowNotFoundError,
    BookingNotFoundError,
    InvalidInputError,
)
from src.utils.ids import next_show_id, next_booking_id
from src.utils.locks import ShowLockManager

Key = Tuple[str, datetime]  # (movie, start_time)


class MemoryStore:
    """
    In-memory storage with simple secondary index:
    - shows_by_id
    - shows_by_key[(movie, start_time)] -> [show_id,...]
    - bookings_by_id
    - revenue_by_cinema[cinema] -> int (rupees)
    """

    def __init__(self) -> None:
        self.shows_by_id: Dict[str, Show] = {}
        self.shows_by_key: Dict[Key, List[str]] = defaultdict(list)
        self.bookings_by_id: Dict[str, Booking] = {}
        self.revenue_by_cinema: Dict[str, int] = defaultdict(int)
        self.locks = ShowLockManager()

        # Global registration lock to protect show creation & indexing
        self._register_lock = threading.Lock()

    # ----- Show ops -----
    def create_show(
        self, cinema: str, movie: str, start_time: datetime, price: int, capacity: int
    ) -> str:
        if price <= 0 or capacity <= 0:
            raise InvalidInputError("Price/Capacity must be positive")

        # <sync block start>
        # // Cinemas registering shows and capacities
        with self._register_lock:
            sid = next_show_id()
            show = Show(
                show_id=sid,
                cinema=cinema,
                movie=movie,
                start_time=start_time,
                price=price,
                capacity=capacity,
                seats_remaining=capacity,
            )
            self.shows_by_id[sid] = show
            self.shows_by_key[(movie, start_time)].append(sid)
        # <sync block end>

        return sid

    def get_show(self, show_id: str) -> Show:
        try:
            return self.shows_by_id[show_id]
        except KeyError:
            raise ShowNotFoundError(f"Show not found: {show_id}")

    def save_show(self, show: Show) -> None:
        self.shows_by_id[show.show_id] = show

    def list_shows_by_key(self, movie: str, start_time: datetime) -> List[Show]:
        return [self.shows_by_id[sid] for sid in self.shows_by_key.get((movie, start_time), [])]

    # ----- Booking ops -----
    def create_booking(self, show_id: str, qty: int, unit_price: int, now: datetime) -> str:
        bid = next_booking_id()
        booking = Booking(
            booking_id=bid,
            show_id=show_id,
            quantity=qty,
            unit_price=unit_price,
            status=BookingStatus.CONFIRMED,
            created_at=now,
        )
        self.bookings_by_id[bid] = booking
        return bid

    def get_booking(self, booking_id: str) -> Booking:
        try:
            return self.bookings_by_id[booking_id]
        except KeyError:
            raise BookingNotFoundError(f"Booking not found: {booking_id}")

    def save_booking(self, booking: Booking) -> None:
        self.bookings_by_id[booking.booking_id] = booking

    # ----- Revenue -----
    def add_revenue(self, cinema: str, amount_rupees: int) -> None:
        self.revenue_by_cinema[cinema] += amount_rupees

    def get_revenue(self, cinema: str) -> int:
        return self.revenue_by_cinema.get(cinema, 0)

    def all_revenue(self) -> Dict[str, int]:
        return dict(self.revenue_by_cinema)
