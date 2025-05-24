from typing import Generic, TypeVar

from pydantic import Field, field_serializer

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import StatsTime

T = TypeVar("T", bound=OtfItemBase)


class OutStudioMixin:
    walking_distance: float | None = Field(None, alias="walkingDistance")
    running_distance: float | None = Field(None, alias="runningDistance")
    cycling_distance: float | None = Field(None, alias="cyclingDistance")

    @field_serializer("walking_distance", "running_distance", "cycling_distance")
    @staticmethod
    def limit_floats(value: float | int | None) -> float | None:
        """Limit the float values to 2 decimal places."""
        if value is not None:
            return round(value, 2)
        return value


class InStudioMixin:
    treadmill_distance: float | None = Field(None, alias="treadmillDistance")
    treadmill_elevation_gained: float | None = Field(None, alias="treadmillElevationGained")
    rower_distance: float | None = Field(None, alias="rowerDistance")
    rower_watt: float | None = Field(None, alias="rowerWatt")

    @field_serializer("treadmill_distance", "treadmill_elevation_gained", "rower_distance", "rower_watt")
    @staticmethod
    def limit_floats(value: float | int | None) -> float | None:
        """Limit the float values to 2 decimal places."""
        if value is not None:
            return round(value, 2)
        return value


class BaseStatsData(OtfItemBase):
    calories: float | None = None
    splat_point: float | None = Field(None, alias="splatPoint")
    total_black_zone: float | None = Field(None, alias="totalBlackZone")
    total_blue_zone: float | None = Field(None, alias="totalBlueZone")
    total_green_zone: float | None = Field(None, alias="totalGreenZone")
    total_orange_zone: float | None = Field(None, alias="totalOrangeZone")
    total_red_zone: float | None = Field(None, alias="totalRedZone")
    workout_duration: float | None = Field(None, alias="workoutDuration")
    step_count: float | None = Field(None, alias="stepCount")


class InStudioStatsData(InStudioMixin, BaseStatsData):
    pass


class OutStudioStatsData(OutStudioMixin, BaseStatsData):
    pass


class AllStatsData(OutStudioMixin, InStudioMixin, BaseStatsData):
    pass


class TimeStats(OtfItemBase, Generic[T]):
    last_year: T = Field(..., alias="lastYear")
    this_year: T = Field(..., alias="thisYear")
    last_month: T = Field(..., alias="lastMonth")
    this_month: T = Field(..., alias="thisMonth")
    last_week: T = Field(..., alias="lastWeek")
    this_week: T = Field(..., alias="thisWeek")
    all_time: T = Field(..., alias="allTime")

    def get_by_time(self, stats_time: StatsTime) -> T:
        """Get the stats data by time."""
        match stats_time:
            case StatsTime.LastYear:
                return self.last_year
            case StatsTime.ThisYear:
                return self.this_year
            case StatsTime.LastMonth:
                return self.last_month
            case StatsTime.ThisMonth:
                return self.this_month
            case StatsTime.LastWeek:
                return self.last_week
            case StatsTime.ThisWeek:
                return self.this_week
            case StatsTime.AllTime:
                return self.all_time


class StatsResponse(OtfItemBase):
    all_stats: TimeStats[AllStatsData] = Field(..., alias="allStats")
    in_studio: TimeStats[InStudioStatsData] = Field(..., alias="inStudio")
    out_studio: TimeStats[OutStudioStatsData] = Field(..., alias="outStudio")
