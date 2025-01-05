class OtfException(Exception):
    """Base class for all exceptions in this package."""


class BookingError(OtfException):
    """Base class for booking-related errors, with an optional booking UUID attribute."""

    booking_uuid: str | None

    def __init__(self, message: str, booking_uuid: str | None = None):
        super().__init__(message)
        self.booking_uuid = booking_uuid


class AlreadyBookedError(BookingError):
    """Raised when attempting to book a class that is already booked."""


class BookingAlreadyCancelledError(BookingError):
    """Raised when attempting to cancel a booking that is already cancelled."""


class OutsideSchedulingWindowError(OtfException):
    """Raised when attempting to book a class outside the scheduling window."""


class BookingNotFoundError(OtfException):
    """Raised when a booking is not found."""
