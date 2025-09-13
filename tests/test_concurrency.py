import threading
from datetime import datetime
from src.services.cinema_service import CinemaService
from src.utils.errors import ShowAlreadyStartedError, BookingUnavailableError


def dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def test_race_for_last_seat_only_one_succeeds():
    svc = CinemaService()
    s = svc.register_show("PVR", "Rush", dt("2025-09-01 10:00"), price=300, capacity=1)

    successes = []
    errors = []

    def try_book(i: int):
        try:
            svc.order_tickets("Rush", dt("2025-09-01 10:00"), 1, dt("2025-08-31 09:00"))
            successes.append(i)
        except (ShowAlreadyStartedError, BookingUnavailableError):
            errors.append(i)

    threads = [threading.Thread(target=try_book, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one success, rest failed
    assert len(successes) == 1
    assert len(errors) == 9

    # Seats should be 0 and revenue should equal 300
    assert svc.store.get_show(s).seats_remaining == 0
    assert svc.revenue_for("PVR") == 300
