import time
from datetime import datetime, timedelta
import pytest

from src.services.cinema_service import CinemaService
from src.utils.enums import ShowStatus
from src.utils.errors import ShowAlreadyStartedError


def near_future(seconds=0.3):
    """Helper: returns datetime ~now + seconds, truncated to minute precision if you prefer."""
    return datetime.now() + timedelta(seconds=seconds)


def test_scheduler_autostarts_and_blocks_late_orders():
    svc = CinemaService()
    start_dt = near_future(0.4)  # ~400ms in the future
    # REGISTER schedules auto-start via Scheduler
    show_id = svc.register_show("PVR", "AutoStart", start_dt, price=200, capacity=5)

    # Before start: booking works
    bid, sid = svc.order_tickets("AutoStart", start_dt, 2, now=datetime.now())
    assert sid == show_id

    # Wait until just after the timer should have fired
    time.sleep(0.7)
    # Show should be started now
    assert svc.store.get_show(show_id).status == ShowStatus.STARTED

    # After auto-start: booking fails
    with pytest.raises(ShowAlreadyStartedError):
        svc.order_tickets("AutoStart", start_dt, 1, now=datetime.now())


def test_scheduler_ignores_past_times_and_allows_manual_start():
    svc = CinemaService()
    start_dt = datetime.now() - timedelta(minutes=5)  # already in the past
    show_id = svc.register_show("INOX", "PastShow", start_dt, price=150, capacity=3)

    # Scheduler does nothing for past start → still REGISTERED
    assert svc.store.get_show(show_id).status == ShowStatus.REGISTERED

    # Manual start still works
    svc.start_show(show_id)
    assert svc.store.get_show(show_id).status == ShowStatus.STARTED
