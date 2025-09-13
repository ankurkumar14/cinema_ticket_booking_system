from datetime import datetime
import pytest
from src.services.cinema_service import CinemaService
from src.utils.errors import (
    CannotEndBeforeStartError,
    ShowAlreadyStartedError,
    ShowAlreadyEndedError,
    BookingUnavailableError,
    BookingAlreadyCancelledError,
    ShowNotFoundError,
    BookingNotFoundError,
)


def dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def test_end_before_start_raises():
    svc = CinemaService()
    s = svc.register_show("PVR", "Oppenheimer", dt("2025-08-25 10:00"), 300, 5)
    with pytest.raises(CannotEndBeforeStartError):
        svc.end_show(s)


def test_update_price_rules_and_show_not_found():
    svc = CinemaService()
    s = svc.register_show("INOX", "Interstellar", dt("2025-08-25 10:00"), 350, 10)
    # before start allowed
    svc.update_price(s, 400)
    # once started, disallow update
    svc.start_show(s)
    with pytest.raises(ShowAlreadyStartedError):
        svc.update_price(s, 450)
    # non-existent show
    with pytest.raises(ShowNotFoundError):
        svc.start_show("S99999")


def test_booking_unavailable_and_fallback_to_other_show():
    svc = CinemaService()
    s1 = svc.register_show("PVR", "Avatar", dt("2025-08-30 10:00"), 300, 2)
    s2 = svc.register_show("Grand", "Avatar", dt("2025-08-30 10:00"), 350, 10)

    # request qty=3, s1 insufficient (2) but s2 sufficient -> should pick s2 even though costlier
    bid, sid = svc.order_tickets("Avatar", dt("2025-08-30 10:00"), 3, dt("2025-08-29 09:00"))
    assert sid == s2

    # now request huge qty -> none sufficient => booking unavailable
    from src.utils.errors import ShowAlreadyStartedError
    with pytest.raises(BookingUnavailableError):
        svc.order_tickets("Avatar", dt("2025-08-30 10:00"), 100, dt("2025-08-29 10:00"))


def test_all_matching_started_gives_started_error():
    svc = CinemaService()
    s1 = svc.register_show("PVR", "Gravity", dt("2025-08-28 10:00"), 200, 5)
    svc.start_show(s1)
    with pytest.raises(ShowAlreadyStartedError):
        svc.order_tickets("Gravity", dt("2025-08-28 10:00"), 1, dt("2025-08-28 10:01"))


def test_cancel_twice_and_booking_not_found():
    svc = CinemaService()
    s = svc.register_show("INOX", "Joker", dt("2025-08-27 10:00"), 220, 5)
    bid, _ = svc.order_tickets("Joker", dt("2025-08-27 10:00"), 1, dt("2025-08-26 11:00"))
    svc.cancel_booking(bid, dt("2025-08-26 11:05"))
    with pytest.raises(BookingAlreadyCancelledError):
        svc.cancel_booking(bid, dt("2025-08-26 11:06"))

    with pytest.raises(BookingNotFoundError):
        _ = svc.store.get_booking("B99999")
