from datetime import datetime
from src.services.cinema_service import CinemaService


def dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def test_cheapest_selection_and_revenue_and_seats():
    svc = CinemaService()
    s1 = svc.register_show("PVR", "Avengers", dt("2025-08-21 10:00"), price=300, capacity=50)
    s2 = svc.register_show("Grand", "Avengers", dt("2025-08-21 10:00"), price=250, capacity=50)

    bid, sid = svc.order_tickets("Avengers", dt("2025-08-21 10:00"), qty=5, now=dt("2025-08-20 09:00"))
    assert sid == s2  # cheapest chosen
    assert svc.revenue_for("Grand") == 250 * 5

    # seat decrement
    # Internal peek through store to verify seats (not typical black-box, but OK here)
    show = svc.store.get_show(s2)
    assert show.seats_remaining == 45


def test_start_then_end_and_block_bookings():
    svc = CinemaService()
    s1 = svc.register_show("PVR", "Dune2", dt("2025-08-21 10:00"), price=400, capacity=10)
    svc.start_show(s1)

    # Booking should fail once started
    from src.utils.errors import ShowAlreadyStartedError, BookingUnavailableError
    try:
        svc.order_tickets("Dune2", dt("2025-08-21 10:00"), 1, dt("2025-08-21 10:01"))
        assert False, "Expected exception"
    except ShowAlreadyStartedError:
        pass

    # Ending should be allowed only after started
    svc.end_show(s1)
    # Ending again -> error
    from src.utils.errors import ShowAlreadyEndedError
    try:
        svc.end_show(s1)
        assert False, "Expected error when ending again"
    except ShowAlreadyEndedError:
        pass


def test_cancel_before_and_after_start():
    svc = CinemaService()
    s1 = svc.register_show("PVR", "Matrix", dt("2025-08-22 10:00"), price=300, capacity=10)

    # book, then cancel BEFORE start -> 50% refund and seats restored
    bid, _ = svc.order_tickets("Matrix", dt("2025-08-22 10:00"), 4, dt("2025-08-21 09:00"))
    assert svc.revenue_for("PVR") == 300 * 4
    refund = svc.cancel_booking(bid, dt("2025-08-21 09:05"))
    assert refund == (300 * 4) // 2
    # seats restored
    assert svc.store.get_show(s1).seats_remaining == 10
    # revenue reduced by 50%
    assert svc.revenue_for("PVR") == 300 * 4 - refund

    # book again, START show, cancel AFTER start -> no refund, no seat return
    bid2, _ = svc.order_tickets("Matrix", dt("2025-08-22 10:00"), 2, dt("2025-08-21 10:00"))
    svc.start_show(s1)
    refund2 = svc.cancel_booking(bid2, dt("2025-08-22 10:01"))
    assert refund2 == 0
    # seats should remain decreased
    assert svc.store.get_show(s1).seats_remaining == 8
    # revenue unchanged
    assert svc.revenue_for("PVR") == (300 * 4 - refund) + (300 * 2)
