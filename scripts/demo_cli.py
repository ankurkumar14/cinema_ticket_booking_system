"""
CLI demo that shows:
1) Register a show scheduled for the next minute (auto-start scheduled).
2) Book before start (succeeds).
3) Wait until just after start_time.
4) Try booking again (fails with 'Show Already Started' due to auto-start).

Run:
  source .venv/bin/activate
  python -m scripts.demo_cli
"""

import time
from datetime import datetime, timedelta

from src.services.cinema_service import CinemaService
from src.cli.parser import run_line

DT_FMT = "%Y-%m-%d %H:%M"


def next_minute_floor():
    now = datetime.now()
    nxt = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    return now, nxt


def main():
    svc = CinemaService()
    now, start_dt = next_minute_floor()
    date_token = start_dt.strftime("%Y-%m-%d")
    time_token = start_dt.strftime("%H:%M")

    cmds = [
        f"REGISTER_SHOW PVR Avengers {date_token} {time_token} 300 5",
        f"ORDER_TICKETS Avengers {date_token} {time_token} 2",
    ]

    print("=== DEMO: Auto-start Scheduler ===")
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    print(f"Show start_time (next minute): {start_dt.strftime(DT_FMT)}")
    print()

    for c in cmds:
        print(f">> {c}")
        out = run_line(svc, c)
        print(out)

    # Sleep until just after the start time so the scheduler can fire
    wait_sec = max(0, (start_dt - datetime.now()).total_seconds()) + 2
    print(f"\n[waiting ~{int(wait_sec)}s for auto-start to trigger...]\n")
    time.sleep(wait_sec)

    # After auto-start, booking should fail with "ERROR: Show Already Started"
    c3 = f"ORDER_TICKETS Avengers {date_token} {time_token} 1"
    print(f">> {c3}")
    out3 = run_line(svc, c3)
    print(out3)

    # Revenue check
    c4 = "REPORT_REVENUE PVR"
    print(f">> {c4}")
    out4 = run_line(svc, c4)
    print(out4)

    print("\n=== DEMO COMPLETE ===")


if __name__ == "__main__":
    main()
