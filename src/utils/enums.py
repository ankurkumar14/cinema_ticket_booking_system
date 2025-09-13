from enum import Enum, auto


class ShowStatus(Enum):
    REGISTERED = auto()
    STARTED = auto()
    ENDED = auto()


class BookingStatus(Enum):
    CONFIRMED = auto()
    CANCELLED = auto()
