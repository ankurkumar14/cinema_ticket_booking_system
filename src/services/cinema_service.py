from datetime import datetime
from typing import Tuple, Dict
from src.repo.memory_store import MemoryStore
from src.services.show_service import ShowService
from src.services.booking_service import BookingService
from src.services.revenue_service import RevenueService
from src.services.scheduler import Scheduler


class CinemaService:
    """
    Facade to orchestrate all operations (store + services + scheduler).
    """

    def __init__(self) -> None:
        self.store = MemoryStore()
        self.shows = ShowService(self.store)
        self.booking = BookingService(self.store)
        self.revenue = RevenueService(self.store)
        # Wire scheduler to call ShowService.start_show
        self.scheduler = Scheduler(self.shows.start_show)

    # ----- Show operations -----
    def register_show(self, cinema: str, movie: str, start_time: datetime, price: int, capacity: int) -> str:
        show_id = self.shows.register_show(cinema, movie, start_time, price, capacity)
        # Schedule auto-start at start_time (best-effort)
        self.scheduler.schedule_start(show_id, start_time)
        return show_id

    def start_show(self, show_id: str) -> None:
        # If a timer exists, cancel it (manual start takes precedence)
        self.scheduler.cancel(show_id)
        return self.shows.start_show(show_id)

    def end_show(self, show_id: str) -> None:
        return self.shows.end_show(show_id)

    def update_price(self, show_id: str, new_price: int) -> None:
        return self.shows.update_price(show_id, new_price)

    # ----- Booking operations -----
    def order_tickets(self, movie: str, start_time: datetime, qty: int, now: datetime) -> Tuple[str, str]:
        return self.booking.order_tickets(movie, start_time, qty, now)

    def cancel_booking(self, booking_id: str, now: datetime) -> int:
        return self.booking.cancel_booking(booking_id, now)

    # ----- Revenue reporting -----
    def revenue_for(self, cinema: str) -> int:
        return self.revenue.revenue_for(cinema)

    def all_revenue(self) -> Dict[str, int]:
        return self.revenue.all_revenue()
