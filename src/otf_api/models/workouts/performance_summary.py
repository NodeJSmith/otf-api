from logging import getLogger
from typing import Any

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase

LOGGER = getLogger(__name__)


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
    display_value: Any
    display_unit: str
    metric_value: float | int = Field(
        coerce_numbers_to_str=True,
        description="The raw value of the metric, as a float or int. When time this reflects seconds.",
    )

    def __str__(self) -> str:
        """Return a string representation of the PerformanceMetric."""
        return f"{self.display_value} {self.display_unit}"


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
