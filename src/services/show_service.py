from datetime import datetime
from src.repo.memory_store import MemoryStore
from src.utils.enums import ShowStatus
from src.utils.errors import (
    ShowNotFoundError,
    ShowAlreadyStartedError,
    CannotEndBeforeStartError,
    ShowAlreadyEndedError,
    InvalidInputError,
)


class ShowService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def register_show(self, cinema: str, movie: str, start_time: datetime, price: int, capacity: int) -> str:
        return self.store.create_show(cinema, movie, start_time, price, capacity)

    def start_show(self, show_id: str) -> None:
        show = self.store.get_show(show_id)
        if show.status == ShowStatus.STARTED:
            raise ShowAlreadyStartedError("Show already started")
        if show.status == ShowStatus.ENDED:
            raise ShowAlreadyEndedError("Show already ended")
        show.status = ShowStatus.STARTED
        self.store.save_show(show)

    def end_show(self, show_id: str) -> None:
        show = self.store.get_show(show_id)
        if show.status == ShowStatus.REGISTERED:
            raise CannotEndBeforeStartError("Cannot end before start")
        if show.status == ShowStatus.ENDED:
            raise ShowAlreadyEndedError("Show already ended")
        show.status = ShowStatus.ENDED
        self.store.save_show(show)

    def update_price(self, show_id: str, new_price: int) -> None:
        if new_price <= 0:
            raise InvalidInputError("Price must be positive")
        show = self.store.get_show(show_id)
        if show.status != ShowStatus.REGISTERED:
            # Only allow price update before start
            raise ShowAlreadyStartedError("Cannot update price after start")
        show.price = new_price
        self.store.save_show(show)
