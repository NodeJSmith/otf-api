from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class StatPoint(OtfItemBase):
    """A single data point in a workout stats time series."""

    date: datetime | None = None
    value: float | None = None
    workout_id: str | None = None
    class_type: str | None = None
    class_name: str | None = None


class WorkoutStatsResponse(OtfItemBase):
    """Response from the workout stats endpoint for a single metric over a date range."""

    start_date_time: datetime | None = Field(None, validation_alias="start")
    end_date_time: datetime | None = Field(None, validation_alias="end")
    stat_key: str | None = None
    unit: str | None = None
    value_type: str | None = None
    points: list[StatPoint] = Field(default_factory=list)


class PreviewStat(OtfItemBase):
    """A single metric's data within a workout stats preview response."""

    points: list[StatPoint] = Field(default_factory=list)
    stat_key: str | None = None
    unit: str | None = None
    value_type: str | None = None


class WorkoutStatsPreviewResponse(OtfItemBase):
    """Response from the workout stats preview endpoint, containing all metrics."""

    start_date_time: datetime | None = Field(None, validation_alias="start")
    end_date_time: datetime | None = Field(None, validation_alias="end")
    stats: list[PreviewStat] = Field(default_factory=list)
    requested_workout_count: int | None = None
