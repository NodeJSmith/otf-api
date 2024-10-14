class BookingError(Exception):
    booking_uuid: str | None

    def __init__(self, message: str, booking_uuid: str | None = None):
        super().__init__(message)
        self.booking_uuid = booking_uuid


class AlreadyBookedError(BookingError): ...


class BookingAlreadyCancelledError(BookingError): ...


class OutsideSchedulingWindowError(Exception): ...


class BookingNotFoundError(Exception): ...
