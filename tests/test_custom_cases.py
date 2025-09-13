from datetime import datetime
import pytest

from src.services.cinema_service import CinemaService
from src.utils.errors import (
    BookingUnavailableError,
    InvalidInputError,
)
from src.utils.enums import ShowStatus


def dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def test_tie_breaker_same_price_choose_earliest_registration():
    svc = CinemaService()
    s1 = svc.register_show("PVR", "Tie", dt("2025-08-25 10:00"), price=300, capacity=5)
    s2 = svc.register_show("Grand", "Tie", dt("2025-08-25 10:00"), price=300, capacity=5)

    # Both have same price; should pick earliest registered (lexicographically smaller show_id => s1)
    bid, sid = svc.order_tickets("Tie", dt("2025-08-25 10:00"), 1, now=dt("2025-08-24 09:00"))
    assert sid == s1


def test_exact_string_match_only():
    svc = CinemaService()
    svc.register_show("PVR", "Avengers", dt("2025-08-26 10:00"), 250, 5)

    # Correct name works
    bid, sid = svc.order_tickets("Avengers", dt("2025-08-26 10:00"), 1, now=dt("2025-08-25 09:00"))
    assert isinstance(bid, str)

    # Slightly different string = considered different show → booking unavailable
    with pytest.raises(BookingUnavailableError):
        svc.order_tickets("Avenger", dt("2025-08-26 10:00"), 1, now=dt("2025-08-25 09:01"))
    with pytest.raises(BookingUnavailableError):
        svc.order_tickets("AVENGERS", dt("2025-08-26 10:00"), 1, now=dt("2025-08-25 09:02"))


def test_booking_unavailable_then_cancellation_frees_then_booking_succeeds():
    svc = CinemaService()
    s = svc.register_show("PVR", "FreeUp", dt("2025-08-27 10:00"), 200, capacity=2)

    # Fill up completely
    bid1, sid = svc.order_tickets("FreeUp", dt("2025-08-27 10:00"), 2, now=dt("2025-08-26 10:00"))

    # Another attempt now fails
    with pytest.raises(BookingUnavailableError):
        svc.order_tickets("FreeUp", dt("2025-08-27 10:00"), 1, now=dt("2025-08-26 10:01"))

    # Cancel BEFORE start → seats restored by 2 and refund 50%
    refund = svc.cancel_booking(bid1, now=dt("2025-08-26 10:02"))
    assert refund == (200 * 2) // 2
    assert svc.store.get_show(s).seats_remaining == 2

    # Now booking works again
    bid2, sid2 = svc.order_tickets("FreeUp", dt("2025-08-27 10:00"), 1, now=dt("2025-08-26 10:03"))
    assert sid2 == s
    assert svc.store.get_show(s).seats_remaining == 1


def test_update_price_validation_and_only_before_start():
    svc = CinemaService()
    s = svc.register_show("PVR", "Pricey", dt("2025-08-28 10:00"), 300, 5)

    # Invalid price values
    with pytest.raises(InvalidInputError):
        svc.update_price(s, 0)
    with pytest.raises(InvalidInputError):
        svc.update_price(s, -10)

    # Valid update works while REGISTERED
    svc.update_price(s, 350)
    assert svc.store.get_show(s).price == 350

    # After start → further update is disallowed
    svc.start_show(s)
    assert svc.store.get_show(s).status == ShowStatus.STARTED
    with pytest.raises(Exception):  # specific ShowAlreadyStartedError acceptable
        svc.update_price(s, 360)
