"""Open server-owned vocabularies: keep values the library has never seen instead of failing validation."""

from collections.abc import Callable
from enum import Enum
from logging import getLogger

LOGGER = getLogger(__name__)

# (vocabulary, value) pairs already reported. Grows only when the server sends a new value.
reported_values: set[tuple[str, str | int]] = set()


def normalize_to(vocabulary: type[Enum]) -> Callable[[str | int], Enum | str | int]:
    """Build a validator that returns the member for an exact match and the raw value otherwise.

    Use it as an `AfterValidator` on the union, so a value of the wrong type still fails the record instead of being
    reported as new.
    """

    def normalize(value: str | int) -> Enum | str | int:
        try:
            return vocabulary(value)
        except ValueError:
            report_unknown_value(vocabulary.__name__, value)
            return value

    return normalize


def report_unknown_value(vocabulary: str, value: str | int) -> None:
    """Log one WARNING per vocabulary and value per process."""
    if (vocabulary, value) in reported_values:
        return

    reported_values.add((vocabulary, value))
    LOGGER.warning("Unrecognized %s value %r; keeping the raw value", vocabulary, value)
