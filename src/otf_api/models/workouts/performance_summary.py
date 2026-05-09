from logging import getLogger
from typing import Any

from pydantic import AliasPath, Field, computed_field

from otf_api.models.base import OtfItemBase

LOGGER = getLogger(__name__)


class ZoneTimeMinutes(OtfItemBase):
    """Time spent in each heart rate zone during a workout, measured in minutes."""

    gray: int = Field(..., description="Minutes in the gray (rest) zone.")
    blue: int = Field(..., description="Minutes in the blue (light effort) zone.")
    green: int = Field(..., description="Minutes in the green (base pace) zone.")
    orange: int = Field(..., description="Minutes in the orange (push pace) zone.")
    red: int = Field(..., description="Minutes in the red (all-out) zone.")


class HeartRate(OtfItemBase):
    """Heart rate statistics from a workout."""

    max_hr: int = Field(..., description="Member's configured max heart rate.")
    peak_hr: int = Field(..., description="Highest heart rate reached during the workout.")
    peak_hr_percent: int = Field(..., description="Peak HR as a percentage of max HR.")
    avg_hr: int = Field(..., description="Average heart rate during the workout.")
    avg_hr_percent: int = Field(..., description="Average HR as a percentage of max HR.")


class PerformanceMetric(OtfItemBase):
    """A single performance metric with display and raw values."""

    display_value: Any = Field(..., description="Formatted value for display (e.g. '6:30').")
    display_unit: str = Field(..., description="Unit label for display (e.g. 'min/mi', 'mph').")
    metric_value: float | int = Field(
        coerce_numbers_to_str=True,
        description="The raw value of the metric, as a float or int. When time this reflects seconds.",
    )

    def __str__(self) -> str:
        """Return a string representation of the PerformanceMetric."""
        return f"{self.display_value} {self.display_unit}"


class BaseEquipment(OtfItemBase):
    """Base class for equipment performance data shared between treadmill and rower."""

    avg_pace: PerformanceMetric = Field(..., description="Average pace during the workout segment.")
    avg_speed: PerformanceMetric = Field(..., description="Average speed during the workout segment.")
    max_pace: PerformanceMetric = Field(..., description="Fastest pace achieved.")
    max_speed: PerformanceMetric = Field(..., description="Maximum speed achieved.")
    moving_time: PerformanceMetric = Field(..., description="Total time spent actively moving.")
    total_distance: PerformanceMetric = Field(..., description="Total distance covered.")


class Treadmill(BaseEquipment):
    """Treadmill-specific performance data from a workout."""

    avg_incline: PerformanceMetric = Field(..., description="Average incline during the treadmill segment.")
    elevation_gained: PerformanceMetric = Field(..., description="Total elevation gained.")
    max_incline: PerformanceMetric = Field(..., description="Maximum incline achieved.")


class Rower(BaseEquipment):
    """Rower-specific performance data from a workout."""

    avg_cadence: PerformanceMetric = Field(..., description="Average strokes per minute.")
    avg_power: PerformanceMetric = Field(..., description="Average power output in watts.")
    max_cadence: PerformanceMetric = Field(..., description="Maximum strokes per minute achieved.")


class PerformanceSummary(OtfItemBase):
    """Represents a workout performance summary - much of the same data as in the app, but not all.

    You likely want to use the `Workout` model and `get_workouts` method instead.
    """

    performance_summary_id: str = Field(
        ..., validation_alias="id", description="Unique identifier for this performance summary"
    )
    ratable: bool | None = Field(None, description="Whether this workout is eligible for rating.")

    @computed_field
    @property
    def class_history_uuid(self) -> str:
        """Alias for performance_summary_id."""
        return self.performance_summary_id

    calories_burned: int | None = Field(
        None, validation_alias=AliasPath("details", "calories_burned"), description="Total calories burned."
    )
    splat_points: int | None = Field(
        None, validation_alias=AliasPath("details", "splat_points"), description="Total splat points earned."
    )
    step_count: int | None = Field(
        None, validation_alias=AliasPath("details", "step_count"), description="Total step count."
    )
    zone_time_minutes: ZoneTimeMinutes | None = Field(
        None, validation_alias=AliasPath("details", "zone_time_minutes"), description="Time spent in each HR zone."
    )
    heart_rate: HeartRate | None = Field(
        None, validation_alias=AliasPath("details", "heart_rate"), description="Heart rate statistics."
    )

    rower_data: Rower | None = Field(
        None, validation_alias=AliasPath("details", "equipment_data", "rower"), description="Rower performance data."
    )
    treadmill_data: Treadmill | None = Field(
        None,
        validation_alias=AliasPath("details", "equipment_data", "treadmill"),
        description="Treadmill performance data.",
    )
