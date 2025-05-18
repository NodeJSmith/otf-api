import json
import typing
from datetime import date, datetime
from logging import getLogger
from pathlib import Path
from typing import Any

import attrs

if typing.TYPE_CHECKING:
    from otf_api import models

LOGGER = getLogger(__name__)


def get_booking_uuid(booking_or_uuid: "str | models.Booking") -> str:
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


def get_booking_id(booking_or_id: "str | models.BookingV2") -> str:
    """Gets the booking ID from the input, which can be a string or BookingV2 object.

    Args:
        booking_or_id (str | BookingV2): The input booking or ID.

    Returns:
        str: The booking ID.

    Raises:
        TypeError: If the input is not a string or BookingV2 object.
    """
    from otf_api.models.bookings_v2 import BookingV2

    if isinstance(booking_or_id, str):
        return booking_or_id

    if isinstance(booking_or_id, BookingV2):
        return booking_or_id.booking_id

    raise TypeError(f"Expected BookingV2 or str, got {type(booking_or_id)}")


def get_class_uuid(class_or_uuid: "str | models.OtfClass | models.BookingV2Class") -> str:
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


def ensure_list(obj: list | Any | None) -> list:
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


def ensure_datetime(date_str: str | date | datetime | None) -> datetime | None:
    """Ensures the input is a date/datetime object or a string that can be converted to a datetime.

    Args:
        date_str (str | date | datetime | None): The input date string or date object.
        If None, returns None.

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
        return datetime.combine(date_str, datetime.min.time())

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


@attrs.define
class CacheableData:
    """Represents a cacheable data object, with methods to read and write to cache."""

    name: str
    cache_dir: Path

    def __attrs_post_init__(self):
        """Ensures the cache directory exists."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def cache_path(self) -> Path:
        """The path to the cache file."""
        return self.cache_dir.expanduser().joinpath(f"{self.name}_cache.json")

    def get_cached_data(self, keys: list[str] | None = None) -> dict[str, str]:
        """Reads the cache file and returns the data if it exists and is valid.

        Returns:
            dict[str, str]: The cached data, or an empty dictionary if the cache is invalid or missing.
        """
        LOGGER.debug(f"Loading {self.name} from cache ({self.cache_path})")
        try:
            if not self.cache_path.exists():
                return {}

            if self.cache_path.stat().st_size == 0:
                return {}

            data: dict[str, str] = json.loads(self.cache_path.read_text())
            if not keys:
                return data

            if set(data.keys()).issuperset(set(keys)):
                return {k: v for k, v in data.items() if k in keys}
            raise ValueError(f"Data must contain all keys: {keys}")
        except Exception:
            LOGGER.exception(f"Failed to read {self.cache_path.name}")
            return {}

    def write_to_cache(self, data: dict[str, str]) -> None:
        """Writes the data to the cache file."""
        LOGGER.debug(f"Writing {self.name} to cache ({self.cache_path})")

        # double check everything exists
        if not self.cache_path.parent.exists():
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.cache_path.exists():
            self.cache_path.touch()

        existing_data = self.get_cached_data()
        data = {**existing_data, **data}

        self.cache_path.write_text(json.dumps(data, indent=4, default=str))

    def clear_cache(self, keys: list[str] | None = None) -> None:
        """Deletes the cache file if it exists."""
        if not self.cache_path.exists():
            return

        if not keys:
            self.cache_path.unlink()
            LOGGER.debug(f"{self.name} cache deleted")
            return

        assert isinstance(keys, list), "Keys must be a list"

        data = self.get_cached_data()
        for key in keys:
            data.pop(key, None)

        self.write_to_cache(data)
