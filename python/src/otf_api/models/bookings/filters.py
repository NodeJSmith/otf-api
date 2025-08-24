from datetime import date, datetime, time

import pendulum
from pydantic import BaseModel, field_validator

from otf_api.models.bookings import ClassType, DoW, OtfClass


class ClassFilter(BaseModel):
    """ClassFilter is used to filter classes, to separate the filtering logic from the API client.

    The `class_type`, `day_of_week`, and `start_time` fields can either be a single value or a list of values.
    If a single value is provided, it will be converted to a list.

    The `class_type` and `day_of_week` fields can be provided as strings or as the corresponding Enum values. The
    class will attempt to match the string to the Enum value, regardless of case.

    The arguments are applied as an AND filter, meaning that all filters must match for a class to be included. If
    a filter is not provided, it is not applied. If multiple values are provided for a filter the values are treated
    as an OR filter, meaning that a class will be included if it matches any of the values.

    All arguments are optional and default to None.

    Args:
        start_date (date): Filter classes that start on or after this date.
        end_date (date): Filter classes that start on or before this date.
        class_type (list[ClassType]): Filter classes by class type.
        day_of_week (list[DoW]): Filter classes by day of the week.
        start_time (list[time]): Filter classes by start time.
    """

    start_date: date | str | None = None
    end_date: date | str | None = None
    class_type: list[ClassType] | ClassType | None = None
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
            assert isinstance(self.start_date, date), "start_date must be a date object"
            classes = [c for c in classes if c.starts_at.date() >= self.start_date]

        if self.end_date:
            assert isinstance(self.end_date, date), "end_date must be a date object"
            classes = [c for c in classes if c.starts_at.date() <= self.end_date]

        if self.class_type:
            classes = [c for c in classes if c.class_type in self.class_type]

        if self.day_of_week:
            classes = [c for c in classes if c.day_of_week in self.day_of_week]

        if self.start_time:
            assert isinstance(self.start_time, list), "start_time must be a list of time objects"
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

        return v  # type: ignore

    @field_validator("class_type", mode="before")
    @classmethod
    def _class_type_str_to_enum(cls, v: str | list[str] | None) -> list[ClassType] | None:
        if v and isinstance(v, str):
            return [ClassType.get_case_insensitive(v)]

        if v and isinstance(v, list) and not all(isinstance(i, ClassType) for i in v):
            return [ClassType.get_case_insensitive(i) for i in v]

        if not v:
            return None

        return v  # type: ignore

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _date_string_to_date(cls, v: str | date | None) -> date | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v

        try:
            value = pendulum.parse(v)
            return value.date() if isinstance(value, datetime) else value  # type: ignore
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date format: {v}. Expected format is YYYY-MM-DD or a date object.")
