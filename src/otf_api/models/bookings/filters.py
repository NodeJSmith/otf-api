from datetime import date, datetime, time
from logging import getLogger

import pendulum
from pydantic import BaseModel, field_validator

from otf_api.models.bookings import ClassType, DoW, OtfClass
from otf_api.models.bookings.enums import class_type_key

LOGGER = getLogger(__name__)


class ClassFilter(BaseModel):
    """ClassFilter is used to filter classes, to separate the filtering logic from the API client.

    The `class_type`, `day_of_week`, and `start_time` fields can either be a single value or a list of values.
    If a single value is provided, it will be converted to a list.

    The `class_type` and `day_of_week` fields can be provided as strings or as the corresponding Enum values. The
    class will attempt to match the string to the Enum value, regardless of case.

    A `class_type` string that matches no Enum value is kept, with a warning, so a class type newer than this library
    can still be filtered on. It compares the same way, ignoring case and treating spaces as underscores, which also
    means a misspelled type matches nothing rather than raising.

    The arguments are applied as an AND filter, meaning that all filters must match for a class to be included. If
    a filter is not provided, it is not applied. If multiple values are provided for a filter the values are treated
    as an OR filter, meaning that a class will be included if it matches any of the values.

    All arguments are optional and default to None.

    Attributes:
        start_date: Filter classes that start on or after this date.
        end_date: Filter classes that start on or before this date.
        class_type: Filter classes by class type.
        day_of_week: Filter classes by day of the week.
        start_time: Filter classes by start time.
    """

    start_date: date | str | None = None
    end_date: date | str | None = None
    class_type: list[ClassType] | list[str] | ClassType | str | None = None
    day_of_week: list[DoW] | DoW | None = None
    start_time: list[time] | time | None = None

    def filter_classes(self, classes: list[OtfClass]) -> list[OtfClass]:
        """Filters a list of classes based on the filter arguments.

        Args:
            classes (list[OtfClass]): A list of classes to filter.

        Returns:
            list[OtfClass]: The filtered list of classes.
        """
        # in case these are set after the class is created
        if self.start_date and isinstance(self.start_date, datetime):
            self.start_date = self.start_date.date()

        if self.end_date and isinstance(self.end_date, datetime):
            self.end_date = self.end_date.date()

        if self.start_date:
            if not isinstance(self.start_date, date):
                raise TypeError(f"start_date must be a date object, got {type(self.start_date)}")
            classes = [c for c in classes if c.starts_at.date() >= self.start_date]

        if self.end_date:
            if not isinstance(self.end_date, date):
                raise TypeError(f"end_date must be a date object, got {type(self.end_date)}")
            classes = [c for c in classes if c.starts_at.date() <= self.end_date]

        if self.class_type:
            # a value assigned after the class is created skips the validator, so it may not be a list
            wanted = self.class_type if isinstance(self.class_type, list) else [self.class_type]
            wanted_keys = {class_type_key(t) for t in wanted}
            classes = [c for c in classes if class_type_key(c.class_type) in wanted_keys]

        if self.day_of_week:
            classes = [c for c in classes if c.day_of_week in self.day_of_week]

        if self.start_time:
            if not isinstance(self.start_time, list):
                raise TypeError(f"start_time must be a list of time objects, got {type(self.start_time)}")
            classes = [c for c in classes if c.starts_at.time() in self.start_time]

        return classes

    @field_validator("class_type", "day_of_week", "start_time", mode="before")
    @classmethod
    def _single_item_to_list(cls, v: str | list | None) -> list | None:
        if v and not isinstance(v, list):
            return [v]

        if not v:
            return None

        return v

    @field_validator("day_of_week", mode="before")
    @classmethod
    def _day_of_week_str_to_enum(cls, v: str | list[str] | None) -> list[DoW] | None:
        if v and isinstance(v, str):
            return [DoW(v.title())]

        if v and isinstance(v, list) and not all(isinstance(i, DoW) for i in v):
            return [DoW(i.title()) for i in v]

        if not v:
            return None

        return v  # pyright: ignore[reportReturnType]

    @field_validator("class_type", mode="before")
    @classmethod
    def _normalize_class_types(cls, v: str | list[str] | None) -> list[ClassType | str] | None:
        if not v:
            return None

        return [known_class_type_or_raw(i) for i in (v if isinstance(v, list) else [v])]

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _date_string_to_date(cls, v: str | date | None) -> date | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v

        try:
            value = pendulum.parse(v)
            return value.date() if isinstance(value, datetime) else value  # pyright: ignore[reportReturnType]
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date format: {v}. Expected format is YYYY-MM-DD or a date object.")


def known_class_type_or_raw(value: str) -> ClassType | str:
    """Returns the matching ClassType, or the value as given with a warning, since it may just be a typo."""
    try:
        return ClassType.get_case_insensitive(value)
    except KeyError:
        LOGGER.warning(
            "ClassFilter class_type %r is not a known class type; it matches only a class type of the same name",
            value,
        )
        return value
