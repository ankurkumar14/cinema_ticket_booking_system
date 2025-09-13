from datetime import datetime
from src.services.cinema_service import CinemaService
from src.utils.time import parse_dt
from src.utils.errors import DomainError
from src.cli import commands as C


def _join_dt(parts, i):
    """
    Returns (dt, next_index).
    Accepts either:
      - parts[i] == "YYYY-MM-DD HH:MM"  (single token if your tokenizer preserved spaces)
      - parts[i], parts[i+1] == "YYYY-MM-DD", "HH:MM" (two tokens)
    Also strips any surrounding quotes.
    """
    def stripq(s: str) -> str:
        return s.strip('"').strip("'")

    # Two-token DATE TIME?
    if i + 1 < len(parts) and "-" in parts[i] and ":" in parts[i + 1]:
        dt_str = f"{stripq(parts[i])} {stripq(parts[i + 1])}"
        return parse_dt(dt_str), i + 2

    # Single token (quoted or unquoted with no space)
    dt_str = stripq(parts[i])
    return parse_dt(dt_str), i + 1


def run_line(svc: CinemaService, line: str) -> str:
    parts = line.strip().split()
    if not parts:
        return ""

    cmd = parts[0].upper()
    try:
        if cmd == "REGISTER_SHOW":
            # REGISTER_SHOW <cinema> <movie> <date> <time> <price> <capacity>
            # or REGISTER_SHOW <cinema> <movie> <"date time"> <price> <capacity>
            if len(parts) < 6:
                return C.ERR_INVALID_INPUT
            cinema = parts[1]
            movie = parts[2]
            dt, j = _join_dt(parts, 3)
            if j + 1 >= len(parts):
                return C.ERR_INVALID_INPUT
            price = int(parts[j])
            cap = int(parts[j + 1])
            show_id = svc.register_show(cinema, movie, dt, price, cap)
            return f"{C.OK} {show_id}"

        if cmd == "START_SHOW":
            if len(parts) != 2:
                return C.ERR_INVALID_INPUT
            show_id = parts[1]
            svc.start_show(show_id)
            return C.OK

        if cmd == "END_SHOW":
            if len(parts) != 2:
                return C.ERR_INVALID_INPUT
            show_id = parts[1]
            svc.end_show(show_id)
            return C.OK

        if cmd == "UPDATE_PRICE":
            if len(parts) != 3:
                return C.ERR_INVALID_INPUT
            show_id = parts[1]
            new_price = int(parts[2])
            svc.update_price(show_id, new_price)
            return C.OK

        if cmd == "ORDER_TICKETS":
            # ORDER_TICKETS <movie> <date> <time> <qty>
            if len(parts) < 4:
                return C.ERR_INVALID_INPUT
            movie = parts[1]
            dt, j = _join_dt(parts, 2)
            if j >= len(parts):
                return C.ERR_INVALID_INPUT
            qty = int(parts[j])
            bid, sid = svc.order_tickets(movie, dt, qty, datetime.now())
            return f"{C.OK} {bid} {sid}"

        if cmd == "CANCEL_BOOKING":
            if len(parts) != 2:
                return C.ERR_INVALID_INPUT
            booking_id = parts[1]
            refund = svc.cancel_booking(booking_id, datetime.now())
            return f"{C.OK} REFUND={refund}"

        if cmd == "REPORT_REVENUE":
            if len(parts) == 1:
                return " ".join([f"{k}:{v}" for k, v in svc.all_revenue().items()])
            cinema = parts[1]
            return str(svc.revenue_for(cinema))

        return "UNKNOWN_COMMAND"

    except DomainError as e:
        msg = str(e).lower()
        if "not found: b" in msg:
            return C.ERR_BOOKING_NOT_FOUND
        if "not found: s" in msg:
            return C.ERR_SHOW_NOT_FOUND
        if "already started" in msg:
            return C.ERR_SHOW_ALREADY_STARTED
        if "cannot end before start" in msg:
            return C.ERR_CANNOT_END_BEFORE_START
        if "already ended" in msg:
            return C.ERR_SHOW_ALREADY_ENDED
        if "booking unavailable" in msg:
            return C.ERR_BOOKING_UNAVAILABLE
        if "already cancelled" in msg:
            return C.ERR_ALREADY_CANCELLED
        return C.ERR_INVALID_INPUT
