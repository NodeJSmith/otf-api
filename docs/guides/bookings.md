# Bookings & Classes

The bookings API lets you search for available classes, book and cancel them, view your
upcoming and past bookings, and rate classes after attending. All booking operations are
accessed through `otf.bookings`.

## Searching for Available Classes

Use `get_classes` to retrieve available classes at your home studio or any other studio:

```python
# Get all classes at your home studio (default)
classes = otf.bookings.get_classes()

# Get classes at specific studios
classes = otf.bookings.get_classes(studio_uuids=["uuid-1", "uuid-2"])

# Get classes within a date range
classes = otf.bookings.get_classes(start_date="2025-02-01", end_date="2025-02-07")
```

Each returned `OtfClass` includes the class name, type, coach, start/end times, studio
details, capacity, and whether you have already booked it.

## Filtering with ClassFilter

The `ClassFilter` class provides powerful filtering to narrow results. Filters use AND
logic between fields, but OR logic within list values for the same field.

```python
from datetime import time
from otf_api.models.bookings import ClassFilter, ClassType, DoW

# Classes on Tuesday or Thursday at 9:45 AM, standard formats only
cf = ClassFilter(
    day_of_week=[DoW.TUESDAY, DoW.THURSDAY],
    start_time=time(9, 45),
    class_type=ClassType.get_standard_class_types(),
)

# Saturday Tread 50 at 10:30 AM
cf2 = ClassFilter(
    day_of_week=DoW.SATURDAY,
    start_time=time(10, 30),
    class_type=ClassType.TREAD_50,
)

# Pass multiple filters -- classes matching EITHER filter are returned
classes = otf.bookings.get_classes(filters=[cf, cf2])
```

**Available filter fields:** `day_of_week` (DoW), `start_time` (time), `class_type`
(ClassType or str), `start_date` (date), `end_date` (date). Each accepts a single value or list.

!!! tip
    Use `ClassType.get_standard_class_types()` to match all standard 2G/3G formats
    without listing each one individually.

`class_type` also accepts a type newer than this library, compared ignoring case and treating
spaces as underscores, so `"hyrox 75"` matches `HYROX_75`. A value that matches no `ClassType`
logs a warning each time the filter is built. A misspelled type therefore returns no classes and
a warning, not an exception.

## Values the Library Doesn't Recognize

OrangeTheory can add a class type or booking status at any time. A response carrying a value this
version doesn't know still parses: the record is kept, the field holds the raw string, and the
library logs one warning per value per process. So `OtfClass.class_type` and
`BookingV2Class.class_type` are `ClassType | str`, and `Booking.status` is `BookingStatus | str`.

Compare by value, which works on either form and keeps working if a later release adds the value
as an enum member:

```python
if otf_class.class_type == "HYROX_75":
    ...

if booking.status in (BookingStatus.Booked, "Some New Status"):
    ...
```

Don't read `.value` without narrowing first, because a raw string has no `.value`:

```python
if isinstance(otf_class.class_type, ClassType):
    label = otf_class.class_type.value
else:
    label = otf_class.class_type

# the same thing, for code that doesn't need to tell them apart
label = getattr(otf_class.class_type, "value", otf_class.class_type)
```

`BookingV2.ends_at` is derived from the class type. For an unrecognized type ending in an
underscore and a number from 30 to 120, it uses that number as the length in minutes, so `HYROX_75`
lasts 75 minutes. Any other unrecognized type is assumed to last 60. This is a best guess from the
name.

## Booking a Class

```python
# Book by OtfClass object
otf.bookings.book_class(otf_class)

# Book by class UUID string
otf.bookings.book_class("c465a372-5cda-4e4b-addd-e695db2c4efa")
```

!!! warning
    `book_class` will raise `AlreadyBookedError` if you are already booked for that class,
    or `OutsideSchedulingWindowError` if the class is not yet in the booking window. It also
    checks for time conflicts with your existing bookings.

These checks, and the `exclude_cancelled` and `exclude_checkedin` options of `get_bookings`, read
`Booking.state`, which is `"cancelled"`, `"checked_in"`, or `"active"`. For an unrecognized status
it comes from the booking's dates: a `cancelled_date` means cancelled, otherwise a
`checked_in_date` means checked in, and neither means active. If a new cancelled-style status sets
no date, `book_class` wrongly refuses to rebook until a release adds that status. `book_class_new`
runs no local checks, so use it in that case.

## Viewing Your Bookings

The `get_bookings_new` endpoint returns both future bookings and past attended classes,
ordered by start time, with inline workout data for past classes.

```python
# Upcoming bookings (today through 45 days out)
bookings = otf.bookings.get_bookings_new()

# Bookings in a specific date range
import pendulum
bookings = otf.bookings.get_bookings_new(
    start_date=pendulum.today().subtract(months=1),
    end_date=pendulum.today(),
)

# Include cancelled bookings
bookings = otf.bookings.get_bookings_new(exclude_cancelled=False)
```

!!! note
    The older `get_bookings` method is still available but returns less data.
    Prefer `get_bookings_new` for new code.

## Cancelling a Booking

```python
# Cancel a BookingV2 object
otf.bookings.cancel_booking_new(booking)

# Cancel by booking ID string
otf.bookings.cancel_booking_new("94644114-8ab7-42b9-8e1a-df42fbafb3f0")
```

!!! warning
    Late cancellations (typically within 8 hours of class start) may incur a fee per your
    studio's policy. The API does not prevent late cancellations.

## Rating a Class and Coach

After attending a class, rate both the class and coach on a 0-3 scale (0 = dismiss,
1 = thumbs down, 2 = thumbs up, 3 = double thumbs up):

```python
from otf_api.exceptions import AlreadyRatedError, ClassNotRatableError

workouts = otf.workouts.get_workouts()
unrated = next((w for w in workouts if w.ratable and not w.class_rating), None)

if unrated:
    try:
        rated = otf.workouts.rate_class_from_workout(unrated, class_rating=3, coach_rating=3)
    except AlreadyRatedError:
        print("Already rated this class")
    except ClassNotRatableError:
        print("This class is no longer ratable")
```

!!! note
    Classes have an age cutoff after which they are no longer ratable. The `ratable` field
    on the workout object indicates whether rating is still possible.

## Handling Booking Conflicts

When you pass an `OtfClass` object to `book_class`, the library automatically checks for
time conflicts with your existing bookings. If a conflict is detected, a
`ConflictingBookingError` is raised before the request is sent to the server.

```python
from otf_api.exceptions import AlreadyBookedError, OutsideSchedulingWindowError

try:
    booking = otf.bookings.book_class(otf_class)
except AlreadyBookedError as e:
    print(f"Already booked: {e}")
except OutsideSchedulingWindowError as e:
    print(f"Cannot book yet: {e}")
```
