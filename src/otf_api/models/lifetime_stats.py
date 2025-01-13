from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from otf_api.models.base import OtfItemBase

T = TypeVar("T", bound=BaseModel)


class OutStudioMixin(OtfItemBase):
    walking_distance: float = Field(..., alias="walkingDistance")
    running_distance: float = Field(..., alias="runningDistance")
    cycling_distance: float = Field(..., alias="cyclingDistance")


class InStudioMixin(OtfItemBase):
    treadmill_distance: float = Field(..., alias="treadmillDistance")
    treadmill_elevation_gained: float = Field(..., alias="treadmillElevationGained")
    rower_distance: float = Field(..., alias="rowerDistance")
    rower_watt: float = Field(..., alias="rowerWatt")


class BaseStatsData(OtfItemBase):
    calories: float
    splat_point: float = Field(..., alias="splatPoint")
    total_black_zone: float = Field(..., alias="totalBlackZone")
    total_blue_zone: float = Field(..., alias="totalBlueZone")
    total_green_zone: float = Field(..., alias="totalGreenZone")
    total_orange_zone: float = Field(..., alias="totalOrangeZone")
    total_red_zone: float = Field(..., alias="totalRedZone")
    workout_duration: float = Field(..., alias="workoutDuration")
    step_count: float = Field(..., alias="stepCount")


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
