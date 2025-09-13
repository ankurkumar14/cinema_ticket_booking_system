from datetime import datetime

# Canonical CLI format: "YYYY-MM-DD HH:MM"
DATETIME_FMT = "%Y-%m-%d %H:%M"


def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, DATETIME_FMT)
