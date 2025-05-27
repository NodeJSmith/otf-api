from datetime import time

from pydantic import AliasPath, Field, field_validator

from otf_api.models.base import OtfItemBase


class ZoneTimeMinutes(OtfItemBase):
    gray: int
    blue: int
    green: int
    orange: int
    red: int


class HeartRate(OtfItemBase):
    max_hr: int
    peak_hr: int
    peak_hr_percent: int
    avg_hr: int
    avg_hr_percent: int


class PerformanceMetric(OtfItemBase):
    display_value: time | float | None
    display_unit: str
    metric_value: float

    def __str__(self) -> str:
        """Return a string representation of the PerformanceMetric."""
        return f"{self.display_value} {self.display_unit}"

    @field_validator("display_value", mode="before")
    @classmethod
    def convert_to_time_format(cls, value: str | None | float | int) -> time | float | None:
        """Convert display_value to a time object if it is in the format of HH:MM:SS or MM:SS.

        Args:
            value (str | None | float | int): The value to convert.

        Returns:
            time | float: The converted value, or the original value if it is not in the expected format.
        """
        if not value:
            return None

        if isinstance(value, float | int):
            return value

        if isinstance(value, str) and ":" in value:
            if value.count(":") == 1:
                minutes, seconds = value.split(":")
                return time(minute=int(minutes), second=int(seconds))
            if value.count(":") == 2:
                hours, minutes, seconds = value.split(":")
                return time(hour=int(hours), minute=int(minutes), second=int(seconds))

        return value  # type: ignore


class BaseEquipment(OtfItemBase):
    avg_pace: PerformanceMetric
    avg_speed: PerformanceMetric
    max_pace: PerformanceMetric
    max_speed: PerformanceMetric
    moving_time: PerformanceMetric
    total_distance: PerformanceMetric


class Treadmill(BaseEquipment):
    avg_incline: PerformanceMetric
    elevation_gained: PerformanceMetric
    max_incline: PerformanceMetric


class Rower(BaseEquipment):
    avg_cadence: PerformanceMetric
    avg_power: PerformanceMetric
    max_cadence: PerformanceMetric


class PerformanceSummary(OtfItemBase):
    """Represents a workout performance summary - much of the same data as in the app, but not all.

    You likely want to use the `Workout` model and `get_workouts` method instead.
    """

    performance_summary_id: str = Field(
        ..., validation_alias="id", description="Unique identifier for this performance summary"
    )
    class_history_uuid: str = Field(..., validation_alias="id", description="Same as performance_summary_id")
    ratable: bool | None = None

    calories_burned: int | None = Field(None, validation_alias=AliasPath("details", "calories_burned"))
    splat_points: int | None = Field(None, validation_alias=AliasPath("details", "splat_points"))
    step_count: int | None = Field(None, validation_alias=AliasPath("details", "step_count"))
    zone_time_minutes: ZoneTimeMinutes | None = Field(None, validation_alias=AliasPath("details", "zone_time_minutes"))
    heart_rate: HeartRate | None = Field(None, validation_alias=AliasPath("details", "heart_rate"))

    rower_data: Rower | None = Field(None, validation_alias=AliasPath("details", "equipment_data", "rower"))
    treadmill_data: Treadmill | None = Field(None, validation_alias=AliasPath("details", "equipment_data", "treadmill"))
