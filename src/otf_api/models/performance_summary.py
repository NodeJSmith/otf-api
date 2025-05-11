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
    display_value: time | float
    display_unit: str
    metric_value: float

    @field_validator("display_value", mode="before")
    @classmethod
    def convert_to_time_format(cls, value) -> time | float:
        if not value:
            return value

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
    """Represents a workout performance summary - the same data that is shown in the OTF app after a workout - mostly.

    The app actually includes data from another endpoint as well, so this is likely going to change soon.

    """

    performance_summary_id: str = Field(..., alias="id", description="Unique identifier for this performance summary")
    class_history_uuid: str = Field(..., alias="id", description="Same as performance_summary_id")
    ratable: bool | None = None

    calories_burned: int | None = Field(None, validation_alias=AliasPath("details", "calories_burned"))
    splat_points: int | None = Field(None, validation_alias=AliasPath("details", "splat_points"))
    step_count: int | None = Field(None, validation_alias=AliasPath("details", "step_count"))
    zone_time_minutes: ZoneTimeMinutes | None = Field(None, validation_alias=AliasPath("details", "zone_time_minutes"))
    heart_rate: HeartRate | None = Field(None, validation_alias=AliasPath("details", "heart_rate"))

    rower_data: Rower | None = Field(None, validation_alias=AliasPath("details", "equipment_data", "rower"))
    treadmill_data: Treadmill | None = Field(None, validation_alias=AliasPath("details", "equipment_data", "treadmill"))
