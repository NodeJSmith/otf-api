import httpx

__all__ = [
    "AlreadyBookedError",
    "AlreadyRatedError",
    "BookingAlreadyCancelledError",
    "BookingError",
    "ClassNotRatableError",
    "ConflictingBookingError",
    "NoCredentialsError",
    "OtfAuthenticationError",
    "OtfConfigurationError",
    "OtfError",
    "OtfRequestError",
    "OtfTransportError",
    "OutsideSchedulingWindowError",
    "ResourceNotFoundError",
    "RetryableOtfRequestError",
]


class OtfError(Exception):
    """Base class for all exceptions in this package."""


class OtfRequestError(OtfError):
    """Raised when an error occurs while making a request to the OTF API."""

    original_exception: Exception | None
    response: httpx.Response
    request: httpx.Request

    # Headers to redact from stored request objects to prevent credential leakage
    # when exceptions are logged or sent to error-reporting services.
    _SENSITIVE_HEADERS = frozenset(
        {
            "authorization",
            "x-amz-security-token",
            "x-amz-date",
            "koji-member-email",
            "koji-member-id",
        }
    )

    def __init__(
        self,
        message: str,
        original_exception: Exception | None,
        response: httpx.Response,
        request: httpx.Request,
    ):
        super().__init__(message)
        sanitized_request = self._sanitize_request(request)
        self.original_exception = original_exception
        self.response = response
        self.request = sanitized_request

        # The response and original exception hold references to the raw request
        # with unsanitized auth headers. Mutating these shared objects is intentional —
        # error-reporting tools serialize them, and we must close every leak path.
        self.response.request = sanitized_request
        if isinstance(self.original_exception, httpx.HTTPStatusError):
            self.original_exception.request = sanitized_request

    @classmethod
    def _sanitize_request(cls, request: httpx.Request) -> httpx.Request:
        """Return a copy of the request with sensitive headers redacted.

        This prevents credential leakage when exceptions are logged or sent
        to error-reporting services.
        """
        sanitized_headers = dict(request.headers)
        for header in cls._SENSITIVE_HEADERS:
            if header in sanitized_headers:
                sanitized_headers[header] = "[REDACTED]"

        try:
            content = request.content
        except httpx.RequestNotRead:
            content = b""

        return httpx.Request(
            method=request.method,
            url=request.url,
            headers=sanitized_headers,
            content=content,
        )


class RetryableOtfRequestError(OtfRequestError):
    """Raised when a request to the OTF API fails but can be retried.

    This is typically used for transient errors that may resolve on retry.
    """


class BookingError(OtfError):
    """Base class for booking-related errors, with an optional booking UUID attribute."""

    booking_uuid: str | None
    booking_id: str | None

    def __init__(self, message: str, booking_uuid: str | None = None, booking_id: str | None = None):
        super().__init__(message)
        self.booking_uuid = booking_uuid
        self.booking_id = booking_id


class AlreadyBookedError(BookingError):
    """Raised when attempting to book a class that is already booked."""


class ConflictingBookingError(BookingError):
    """Raised when attempting to book a class that conflicts with an existing booking."""


class BookingAlreadyCancelledError(BookingError):
    """Raised when attempting to cancel a booking that is already cancelled."""


class OutsideSchedulingWindowError(BookingError):
    """Raised when attempting to book a class outside the scheduling window."""


class ResourceNotFoundError(OtfError):
    """Raised when a resource is not found."""


class AlreadyRatedError(OtfError):
    """Raised when attempting to rate a class that is already rated."""


class ClassNotRatableError(OtfError):
    """Raised when attempting to rate a class that is not ratable."""


class OtfAuthenticationError(OtfError):
    """Raised when Cognito authentication fails (e.g., invalid credentials).

    The original error is available via ``__cause__``.
    """


class OtfTransportError(OtfError):
    """Raised when a network-level error occurs (timeout, connection refused, etc.).

    The original error is available via ``__cause__``.
    """


class OtfConfigurationError(OtfError):
    """Raised when the boto3/botocore client is misconfigured or invoked with invalid parameters.

    Covers non-network BotoCoreError failures (e.g. a missing AWS profile, an unresolvable region,
    or a parameter validation error) that a retry cannot fix. The original error is available via
    ``__cause__``.
    """


class NoCredentialsError(OtfError):
    """Raised when no credentials are provided and no cached tokens are available."""
