# Error Handling

All exceptions raised by `otf-api` inherit from a single base class, making it straightforward to catch library errors broadly or handle specific failure modes.

## Exception Hierarchy

```
OtfError
├── OtfRequestError
│   └── RetryableOtfRequestError
├── BookingError
│   ├── AlreadyBookedError
│   ├── ConflictingBookingError
│   ├── BookingAlreadyCancelledError
│   └── OutsideSchedulingWindowError
├── NoCredentialsError
├── ResourceNotFoundError
├── AlreadyRatedError
└── ClassNotRatableError
```

All exceptions are importable from a single location:

```python
from otf_api.exceptions import (
    OtfError,
    OtfRequestError,
    RetryableOtfRequestError,
    BookingError,
    AlreadyBookedError,
    ConflictingBookingError,
    BookingAlreadyCancelledError,
    OutsideSchedulingWindowError,
    NoCredentialsError,
    ResourceNotFoundError,
    AlreadyRatedError,
    ClassNotRatableError,
)
```

## Exception Reference

### OtfError

The base class for all exceptions in the package. Catch this to handle any library error generically.

### OtfRequestError

Raised when an HTTP request to the OTF API fails. Carries context about the failed request.

| Attribute | Type | Description |
|-----------|------|-------------|
| `original_exception` | `Exception | None` | The underlying exception that caused the failure |
| `response` | `httpx.Response` | The HTTP response object |
| `request` | `httpx.Request` | The HTTP request that failed |

```python
from otf_api.exceptions import OtfRequestError

try:
    otf.workouts.get_workouts()
except OtfRequestError as e:
    print(f"Request failed: {e}")
    print(f"Status code: {e.response.status_code}")
    print(f"URL: {e.request.url}")
```

### RetryableOtfRequestError

A subclass of `OtfRequestError` raised for transient failures (e.g., 5xx server errors, timeouts). The library may automatically retry these requests before raising the exception.

```python
from otf_api.exceptions import RetryableOtfRequestError

try:
    classes = otf.bookings.get_classes()
except RetryableOtfRequestError as e:
    # The request was retried but still failed
    print(f"Transient failure after retries: {e}")
```

### BookingError

Base class for all booking-related errors. Carries identifiers for the affected booking.

| Attribute | Type | Description |
|-----------|------|-------------|
| `booking_uuid` | `str | None` | The UUID of the booking involved |
| `booking_id` | `str | None` | The numeric ID of the booking involved |

### AlreadyBookedError

Raised when you attempt to book a class that you are already booked into.

### ConflictingBookingError

Raised when a new booking conflicts with an existing booking at the same time.

### BookingAlreadyCancelledError

Raised when you attempt to cancel a booking that has already been cancelled.

### OutsideSchedulingWindowError

Raised when you attempt to book a class that is outside the allowed scheduling window (too far in the future or too close to the start time).

### ResourceNotFoundError

Raised when a requested resource (studio, class, workout, etc.) does not exist.

### AlreadyRatedError

Raised when you attempt to rate a class that you have already rated.

### ClassNotRatableError

Raised when you attempt to rate a class that is not eligible for rating (e.g., the class has not yet occurred).

## Error Handling Patterns

### Booking a class safely

The most common error handling pattern involves booking operations, where multiple failure modes are expected:

```python
from otf_api.exceptions import (
    AlreadyBookedError,
    ConflictingBookingError,
    OutsideSchedulingWindowError,
)

try:
    booking = otf.bookings.book_class(target_class)
    print(f"Booked successfully: {booking.booking_uuid}")
except AlreadyBookedError as e:
    print(f"Already booked for this class (booking: {e.booking_uuid})")
except ConflictingBookingError as e:
    print(f"Conflicts with existing booking: {e.booking_uuid}")
except OutsideSchedulingWindowError:
    print("Class is outside the scheduling window")
```

### Cancelling a booking safely

```python
from otf_api.exceptions import BookingAlreadyCancelledError

try:
    otf.bookings.cancel_booking(booking)
    print("Booking cancelled")
except BookingAlreadyCancelledError:
    print("Booking was already cancelled")
```

### Catching all API errors

Use the base `OtfError` class to catch any library exception:

```python
from otf_api.exceptions import OtfError

try:
    result = otf.workouts.get_workouts()
except OtfError as e:
    print(f"OTF API error: {e}")
```

### Inspecting request failures

When debugging API issues, `OtfRequestError` gives you access to the full HTTP context:

```python
from otf_api.exceptions import OtfRequestError

try:
    otf.studios.get_studio_detail(studio_uuid="bad-uuid")
except OtfRequestError as e:
    print(f"HTTP {e.response.status_code} from {e.request.method} {e.request.url}")
    if e.original_exception:
        print(f"Caused by: {e.original_exception}")
```

!!! tip
    When reporting bugs, include the `response.status_code`, `request.url`, and the response body (`response.text`) from `OtfRequestError`. This helps narrow down whether the issue is in the library or the upstream API.
