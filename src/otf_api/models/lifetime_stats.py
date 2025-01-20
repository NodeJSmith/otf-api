from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import StatsTime

T = TypeVar("T", bound=BaseModel)


class OutStudioMixin(OtfItemBase):
    walking_distance: float | None = Field(None, alias="walkingDistance")
    running_distance: float | None = Field(None, alias="runningDistance")
    cycling_distance: float | None = Field(None, alias="cyclingDistance")


class InStudioMixin(OtfItemBase):
    treadmill_distance: float | None = Field(None, alias="treadmillDistance")
    treadmill_elevation_gained: float | None = Field(None, alias="treadmillElevationGained")
    rower_distance: float | None = Field(None, alias="rowerDistance")
    rower_watt: float | None = Field(None, alias="rowerWatt")


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


class OutStudioTimeStats(TimeStats[OutStudioStatsData]):
    pass


class InStudioTimeStats(TimeStats[InStudioStatsData]):
    pass


class AllStatsTimeStats(TimeStats[AllStatsData]):
    pass


class StatsResponse(OtfItemBase):
    all_stats: AllStatsTimeStats = Field(..., alias="allStats")
    in_studio: InStudioTimeStats = Field(..., alias="inStudio")
    out_studio: OutStudioTimeStats = Field(..., alias="outStudio")
