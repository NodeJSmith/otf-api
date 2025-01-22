from httpx import Request, Response


class OtfException(Exception):
    """Base class for all exceptions in this package."""


class OtfRequestError(OtfException):
    """Raised when an error occurs while making a request to the OTF API."""

    original_exception: Exception
    response: Response
    request: Request

    def __init__(self, message: str, original_exception: Exception | None, response: Response, request: Request):
        super().__init__(message)
        self.original_exception = original_exception
        self.response = response
        self.request = request


class BookingError(OtfException):
    """Base class for booking-related errors, with an optional booking UUID attribute."""

    booking_uuid: str | None

    def __init__(self, message: str, booking_uuid: str | None = None):
        super().__init__(message)
        self.booking_uuid = booking_uuid


class AlreadyBookedError(BookingError):
    """Raised when attempting to book a class that is already booked."""


class ConflictingBookingError(BookingError):
    """Raised when attempting to book a class that conflicts with an existing booking."""


class BookingAlreadyCancelledError(BookingError):
    """Raised when attempting to cancel a booking that is already cancelled."""


class OutsideSchedulingWindowError(OtfException):
    """Raised when attempting to book a class outside the scheduling window."""


class BookingNotFoundError(OtfException):
    """Raised when a booking is not found."""


class ResourceNotFoundError(OtfException):
    """Raised when a resource is not found."""


class AlreadyRatedError(OtfException):
    """Raised when attempting to rate a class that is already rated."""


class ClassNotRatableError(OtfException):
    """Raised when attempting to rate a class that is not ratable."""
