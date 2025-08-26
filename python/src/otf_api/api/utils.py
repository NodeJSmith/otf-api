import typing
from datetime import date, datetime, time, timedelta
from json import JSONDecodeError
from logging import getLogger
from typing import Any

import httpx

from otf_api import exceptions as exc

if typing.TYPE_CHECKING:
    from otf_api.models.bookings import Booking, BookingV2, BookingV2Class, ClassFilter, OtfClass

LOGGER = getLogger(__name__)

MIN_TIME = datetime.min.time()


def get_studio_uuid_list(
    home_studio_uuid: str, studio_uuids: list[str] | str | None, include_home_studio: bool = True
) -> list[str]:
    """Get a list of studio UUIDs to request classes for.

    If `studio_uuids` is None or empty, it will return a list containing only the home studio UUID.
    If `studio_uuids` is a string, it will be converted to a list.
    If `studio_uuids` is a list, it will be ensured that it contains unique values.

    Args:
        home_studio_uuid (str): The UUID of the home studio.
        studio_uuids (list[str] | str | None): A list of studio UUIDs or a single UUID string.
        include_home_studio (bool): Whether to include the home studio UUID in the list. Defaults to True.

    Returns:
        list[str]: A list of unique studio UUIDs to request classes for.
    """
    studio_uuids = ensure_list(studio_uuids) or [home_studio_uuid]
    studio_uuids = list(set(studio_uuids))  # remove duplicates

    if len(studio_uuids) > 50:
        LOGGER.warning("Cannot request classes for more than 50 studios at a time.")
        studio_uuids = studio_uuids[:50]

    if include_home_studio and home_studio_uuid not in studio_uuids:
        if len(studio_uuids) == 50:
            LOGGER.warning("Cannot include home studio, request already includes 50 studios.")
        else:
            studio_uuids.append(home_studio_uuid)

    return studio_uuids


def check_for_booking_conflicts(bookings: list["Booking"], otf_class: "OtfClass") -> None:
    """Check for booking conflicts with the provided class.

    Checks the member's bookings to see if the provided class overlaps with any existing bookings. If a conflict is
    found, a ConflictingBookingError is raised.
    """
    if not bookings:
        return

    for booking in bookings:
        booking_start = booking.otf_class.starts_at
        booking_end = booking.otf_class.ends_at
        # Check for overlap
        if not (otf_class.ends_at < booking_start or otf_class.starts_at > booking_end):
            raise exc.ConflictingBookingError(
                f"You already have a booking that conflicts with this class ({booking.otf_class.class_uuid}).",
                booking_uuid=booking.booking_uuid,
            )


def filter_classes_by_filters(
    classes: list["OtfClass"], filters: "list[ClassFilter] | ClassFilter | None"
) -> list["OtfClass"]:
    """Filter classes by the provided filters.

    Args:
        classes (list[OtfClass]): The classes to filter.
        filters (list[ClassFilter] | ClassFilter | None): The filters to apply.

    Returns:
        list[OtfClass]: The filtered classes.
    """
    if not filters:
        return classes

    filters = ensure_list(filters)
    filtered_classes: list[OtfClass] = []

    # apply each filter as an OR operation
    for f in filters:
        filtered_classes.extend(f.filter_classes(classes))

    # remove duplicates
    classes = list({c.class_uuid: c for c in filtered_classes}.values())

    return classes


def filter_classes_by_date(
    classes: list["OtfClass"], start_date: date | None, end_date: date | None
) -> list["OtfClass"]:
    """Filter classes by start and end dates, as well as the max date the booking endpoint will accept.

    Args:
        classes (list[OtfClass]): The classes to filter.
        start_date (date | None): The start date to filter by.
        end_date (date | None): The end date to filter by.

    Returns:
        list[OtfClass]: The filtered classes.
    """
    # this endpoint returns classes that the `book_class` endpoint will reject, this filters them out
    max_date = datetime.today().date() + timedelta(days=29)

    classes = [c for c in classes if c.starts_at.date() <= max_date]

    # if not start date or end date, we're done
    if not start_date and not end_date:
        return classes

    if start_date := ensure_date(start_date):
        classes = [c for c in classes if c.starts_at.date() >= start_date]

    if end_date := ensure_date(end_date):
        classes = [c for c in classes if c.starts_at.date() <= end_date]

    return classes


def get_booking_uuid(booking_or_uuid: "str | Booking") -> str:
    """Gets the booking UUID from the input, which can be a string or Booking object.

    Args:
        booking_or_uuid (str | Booking): The input booking or UUID.

    Returns:
        str: The booking UUID.

    Raises:
        TypeError: If the input is not a string or Booking object.
    """
    from otf_api.models.bookings import Booking

    if isinstance(booking_or_uuid, str):
        return booking_or_uuid

    if isinstance(booking_or_uuid, Booking):
        return booking_or_uuid.booking_uuid

    raise TypeError(f"Expected Booking or str, got {type(booking_or_uuid)}")


def get_booking_id(booking_or_id: "str | BookingV2") -> str:
    """Gets the booking ID from the input, which can be a string or BookingV2 object.

    Args:
        booking_or_id (str | BookingV2): The input booking or ID.

    Returns:
        str: The booking ID.

    Raises:
        TypeError: If the input is not a string or BookingV2 object.
    """
    from otf_api.models.bookings import BookingV2

    if isinstance(booking_or_id, str):
        return booking_or_id

    if isinstance(booking_or_id, BookingV2):
        return booking_or_id.booking_id

    raise TypeError(f"Expected BookingV2 or str, got {type(booking_or_id)}")


def get_class_uuid(class_or_uuid: "str | OtfClass | BookingV2Class") -> str:
    """Gets the class UUID from the input, which can be a string, OtfClass, or BookingV2Class.

    Args:
        class_or_uuid (str | OtfClass | BookingV2Class): The input class or UUID.

    Returns:
        str: The class UUID.

    Raises:
        ValueError: If the class does not have a class_uuid.
        TypeError: If the input is not a string, OtfClass, or BookingV2Class.

    """
    if isinstance(class_or_uuid, str):
        return class_or_uuid

    if hasattr(class_or_uuid, "class_uuid"):
        class_uuid = getattr(class_or_uuid, "class_uuid", None)
        if class_uuid:
            return class_uuid
        raise ValueError("Class does not have a class_uuid")

    raise TypeError(f"Expected OtfClass, BookingV2Class, or str, got {type(class_or_uuid)}")


def get_class_id(class_or_id: "str | BookingV2Class") -> str:
    """Gets the class ID from the input, which can be a string or BookingV2Class.

    Args:
        class_or_id (str | BookingV2Class): The input class or ID.

    Returns:
        str: The class ID.

    Raises:
        TypeError: If the input is not a string or BookingV2Class.
    """
    from otf_api.models.bookings import BookingV2Class

    if isinstance(class_or_id, str):
        return class_or_id

    if isinstance(class_or_id, BookingV2Class):
        return class_or_id.class_id

    raise TypeError(f"Expected BookingV2Class or str, got {type(class_or_id)}")


def ensure_list(obj: list | Any | None) -> list:  # noqa: ANN401
    """Ensures the input is a list. If None, returns an empty list. If not a list, returns a list containing the input.

    Args:
        obj (list | Any | None): The input object to ensure is a list.

    Returns:
        list: The input object as a list. If None, returns an empty list.
    """
    if obj is None:
        return []
    if not isinstance(obj, list):
        return [obj]
    return obj


def ensure_datetime(date_str: str | date | datetime | date | None, combine_with: time = MIN_TIME) -> datetime | None:
    """Ensures the input is a date/datetime object or a string that can be converted to a datetime.

    Args:
        date_str (str | date | datetime | None): The input date string or date object. If None, returns None.
        combine_with (time): The time to combine with if the input is a date object. Defaults to MIN_TIME.

    Returns:
        datetime | None: The converted datetime object or None if the input is None.

    Raises:
        TypeError: If the input is not a string, date, or datetime object.
    """
    if not date_str:
        return None

    if isinstance(date_str, str):
        return datetime.fromisoformat(date_str)

    if isinstance(date_str, datetime):
        return date_str

    if isinstance(date_str, date):
        return datetime.combine(date_str, combine_with)

    raise TypeError(f"Expected str or datetime, got {type(date_str)}")


def ensure_date(date_str: str | date | datetime | None) -> date | None:
    """Ensures the input is a date object or a string that can be converted to a date.

    Args:
        date_str (str | date | None): The input date string or date object.

    Returns:
        date | None: The converted date object or None if the input is None.

    Raises:
        TypeError: If the input is not a string or date object.
    """
    if not date_str:
        return None

    if isinstance(date_str, str):
        return datetime.fromisoformat(date_str).date()

    if isinstance(date_str, datetime):
        return date_str.date()

    if isinstance(date_str, date):
        return date_str

    raise TypeError(f"Expected str or date, got {type(date_str)}")


def is_error_response(data: dict[str, Any]) -> bool:
    """Check if the response data indicates an error."""
    return isinstance(data, dict) and (data.get("code") == "ERROR" or "error" in data)


def get_json_from_response(response: httpx.Response) -> dict[str, Any]:
    """Extract JSON data from an HTTP response."""
    try:
        return response.json()
    except JSONDecodeError:
        return {"raw": response.text}
