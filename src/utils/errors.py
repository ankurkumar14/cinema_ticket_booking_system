class DomainError(Exception):
    """Base class for domain errors (mapped to CLI messages)."""


class ShowNotFoundError(DomainError):
    pass


class BookingNotFoundError(DomainError):
    pass


class BookingUnavailableError(DomainError):
    """No matching show with enough capacity that can be booked."""
    pass


class ShowAlreadyStartedError(DomainError):
    """Operation invalid because show has already started."""
    pass


class CannotEndBeforeStartError(DomainError):
    pass


class ShowAlreadyEndedError(DomainError):
    pass


class BookingAlreadyCancelledError(DomainError):
    pass


class InvalidInputError(DomainError):
    pass
