import threading
from itertools import count

_show_counter = count(1)
_booking_counter = count(1)
_lock = threading.Lock()


def next_show_id() -> str:
    with _lock:
        return f"S{next(_show_counter):05d}"


def next_booking_id() -> str:
    with _lock:
        return f"B{next(_booking_counter):05d}"
