import threading
from datetime import datetime
import pytest

from src.services.cinema_service import CinemaService
from src.utils.errors import BookingUnavailableError


def dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def test_concurrent_cancel_and_order_invariants_hold():
    svc = CinemaService()
    price = 300
    s = svc.register_show("PVR", "Race", dt("2025-08-29 10:00"), price, capacity=2)

    # Fill up
    bid, _ = svc.order_tickets("Race", dt("2025-08-29 10:00"), 2, now=dt("2025-08-28 09:00"))
    assert svc.store.get_show(s).seats_remaining == 0
    start_rev = svc.revenue_for("PVR")  # == price*2

    cancel_done = []
    order_done = []
    lock = threading.Lock()

    def do_cancel():
        refund = svc.cancel_booking(bid, now=dt("2025-08-28 09:05"))
        with lock:
            cancel_done.append(refund)

    def do_order():
        try:
            svc.order_tickets("Race", dt("2025-08-29 10:00"), 2, now=dt("2025-08-28 09:06"))
            ok = True
        except BookingUnavailableError:
            ok = False
        with lock:
            order_done.append(ok)

    t1 = threading.Thread(target=do_cancel)
    t2 = threading.Thread(target=do_order)
    t1.start(); t2.start(); t1.join(); t2.join()

    # Invariants:
    seats = svc.store.get_show(s).seats_remaining
    rev = svc.revenue_for("PVR")

    # Seats are either 0 (order after cancel grabbed them) or 2 (order happened first and failed)
    assert seats in (0, 2)

    # Revenue is either:
    #  - start_rev - 50% refund + price*2  (order succeeds after cancel) => 600 - 300 + 600 = 900
    #  - start_rev - 50% refund            (order fails, only cancel applies) => 600 - 300 = 300
    assert rev in (start_rev - (price) + (price * 2), start_rev - price)
