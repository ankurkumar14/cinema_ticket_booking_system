from __future__ import annotations
from datetime import datetime
from typing import Tuple, List
from src.repo.memory_store import MemoryStore
from src.utils.enums import ShowStatus, BookingStatus
from src.utils.errors import (
    BookingUnavailableError,
    ShowAlreadyStartedError,
    BookingAlreadyCancelledError,
)
from src.models.show import Show


class BookingService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    # ---------- ORDER ----------
    def order_tickets(self, movie: str, start_time: datetime, qty: int, now: datetime) -> Tuple[str, str]:
        """
        Returns: (booking_id, show_id)
        Selection: among matching (movie, start_time) shows, choose cheapest with seats and not started/ended.
        """
        shows = self.store.list_shows_by_key(movie, start_time)
        if not shows:
            # No such show registered at all -> treat as unavailable
            raise BookingUnavailableError("Booking unavailable")

        candidates: List[Show] = []
        any_started = False
        for s in shows:
            if s.status in (ShowStatus.STARTED, ShowStatus.ENDED):
                if s.status == ShowStatus.STARTED:
                    any_started = True
                continue
            if s.seats_remaining >= qty:
                candidates.append(s)

        if not candidates:
            if any_started:
                raise ShowAlreadyStartedError("Show already started")
            raise BookingUnavailableError("Booking unavailable")

        # choose cheapest; tie-breaker: smallest show_id (earliest registration)
        candidates.sort(key=lambda s: (s.price, s.show_id))
        chosen = candidates[0]

        lock = self.store.locks.get(chosen.show_id)
        with lock:
            # <async block start>
            # // Concurrent booking and cancellation requests
            s = self.store.get_show(chosen.show_id)
            if s.status != ShowStatus.REGISTERED:
                raise ShowAlreadyStartedError("Show already started")
            if s.seats_remaining < qty:
                raise BookingUnavailableError("Booking unavailable")

            # Mutations guarded by per-show lock
            s.seats_remaining -= qty
            self.store.save_show(s)

            bid = self.store.create_booking(s.show_id, qty, s.price, now)
            self.store.add_revenue(s.cinema, s.price * qty)
            # <async block end>
            return bid, s.show_id

    # ---------- CANCEL ----------
    def cancel_booking(self, booking_id: str, now: datetime) -> int:
        """
        Cancels entire booking (batch). Returns refund amount (int rupees).
        Before start => 50% refund and seats restored.
        After start/ended => 0% refund and seats NOT restored.
        """
        booking = self.store.get_booking(booking_id)
        if booking.status == BookingStatus.CANCELLED:
            raise BookingAlreadyCancelledError("Booking already cancelled")

        show = self.store.get_show(booking.show_id)
        lock = self.store.locks.get(show.show_id)

        with lock:
            # <async block start>
            # // Concurrent booking and cancellation requests
            show = self.store.get_show(booking.show_id)
            booking = self.store.get_booking(booking_id)

            if booking.status == BookingStatus.CANCELLED:
                raise BookingAlreadyCancelledError("Booking already cancelled")

            if show.status == ShowStatus.REGISTERED:
                # Before start → refund 50% and restore seats
                refund = (booking.unit_price * booking.quantity) // 2
                show.seats_remaining += booking.quantity
                self.store.save_show(show)
                self.store.add_revenue(show.cinema, -refund)
            else:
                # STARTED or ENDED → no refund, no seat return
                refund = 0

            booking.status = BookingStatus.CANCELLED
            self.store.save_booking(booking)
            # <async block end>
            return refund
