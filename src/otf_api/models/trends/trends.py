from datetime import datetime
from enum import StrEnum

from pydantic import Field

from otf_api.models.base import OtfItemBase


class TrendCategory(StrEnum):
    Effort = "effort"
    Treadmill = "treadmill"
    Rower = "rower"


class TrendType(StrEnum):
    SplatPoints = "splat_points"
    AverageHeartRate = "average_hr"
    PeakHeartRate = "peak_hr"
    TreadmillTopSpeed = "tread_top_speed"
    RowerSplitTime = "rower_500m_split_time"
    RowerTopPower = "rower_top_power"

    @property
    def category(self) -> TrendCategory:
        """Get the category this trend type belongs to."""
        return _TREND_CATEGORY_MAP[self]


_TREND_CATEGORY_MAP: dict[TrendType, TrendCategory] = {
    TrendType.SplatPoints: TrendCategory.Effort,
    TrendType.AverageHeartRate: TrendCategory.Effort,
    TrendType.PeakHeartRate: TrendCategory.Effort,
    TrendType.TreadmillTopSpeed: TrendCategory.Treadmill,
    TrendType.RowerSplitTime: TrendCategory.Rower,
    TrendType.RowerTopPower: TrendCategory.Rower,
}


class StatPoint(OtfItemBase):
    date: datetime | None = None
    value: float | None = None
    workout_id: str | None = None
    class_type: str | None = None
    class_name: str | None = None


class WorkoutStatsResponse(OtfItemBase):
    start_date_time: datetime | None = Field(None, validation_alias="start")
    end_date_time: datetime | None = Field(None, validation_alias="end")
    stat_key: str | None = None
    unit: str | None = None
    value_type: str | None = None
    points: list[StatPoint] = Field(default_factory=list)


class PreviewStat(OtfItemBase):
    points: list[StatPoint] = Field(default_factory=list)
    stat_key: str | None = None
    unit: str | None = None
    value_type: str | None = None


class WorkoutStatsPreviewResponse(OtfItemBase):
    start_date_time: datetime | None = Field(None, validation_alias="start")
    end_date_time: datetime | None = Field(None, validation_alias="end")
    stats: list[PreviewStat] = Field(default_factory=list)
    requested_workout_count: int | None = None
