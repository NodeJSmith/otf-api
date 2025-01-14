from datetime import datetime, time

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

        return value


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


class EquipmentData(OtfItemBase):
    treadmill: Treadmill
    rower: Rower


class Class(OtfItemBase):
    starts_at: datetime = Field(..., alias="starts_at_local")
    name: str


class PerformanceSummaryDetail(OtfItemBase):
    id: str
    otf_class: Class = Field(..., alias="class")

    ratable: bool
    calories_burned: int = Field(..., alias=AliasPath("details", "calories_burned"))
    splat_points: int = Field(..., alias=AliasPath("details", "splat_points"))
    step_count: int = Field(..., alias=AliasPath("details", "step_count"))
    active_time_seconds: int = Field(..., alias=AliasPath("details", "active_time_seconds"))
    zone_time_minutes: ZoneTimeMinutes = Field(..., alias=AliasPath("details", "zone_time_minutes"))
    heart_rate: HeartRate = Field(..., alias=AliasPath("details", "heart_rate"))

    rower_data: Rower = Field(..., alias=AliasPath("details", "equipment_data", "rower"))
    treadmill_data: Treadmill = Field(..., alias=AliasPath("details", "equipment_data", "treadmill"))
