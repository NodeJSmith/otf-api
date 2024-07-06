from enum import Enum

from pydantic import BaseModel, Field


class StatsTime(str, Enum):
    LastYear = "lastYear"
    ThisYear = "thisYear"
    LastMonth = "lastMonth"
    ThisMonth = "thisMonth"
    LastWeek = "lastWeek"
    ThisWeek = "thisWeek"
    AllTime = "allTime"


class StatsType(str, Enum):
    Home = "outStudio"
    Studio = "inStudio"
    All = "allStats"


class OutStudioMixin(BaseModel):
    walking_distance: float = Field(..., alias="walkingDistance")
    running_distance: float = Field(..., alias="runningDistance")
    cycling_distance: float = Field(..., alias="cyclingDistance")


class InStudioMixin(BaseModel):
    treadmill_distance: float = Field(..., alias="treadmillDistance")
    treadmill_elevation_gained: float = Field(..., alias="treadmillElevationGained")
    rower_distance: float = Field(..., alias="rowerDistance")
    rower_watt: float = Field(..., alias="rowerWatt")


class BaseStatsData(BaseModel):
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


class OutStudioTimeStats(BaseModel):
    last_year: OutStudioStatsData = Field(..., alias="lastYear")
    this_year: OutStudioStatsData = Field(..., alias="thisYear")
    last_month: OutStudioStatsData = Field(..., alias="lastMonth")
    this_month: OutStudioStatsData = Field(..., alias="thisMonth")
    last_week: OutStudioStatsData = Field(..., alias="lastWeek")
    this_week: OutStudioStatsData = Field(..., alias="thisWeek")
    all_time: OutStudioStatsData = Field(..., alias="allTime")


class InStudioTimeStats(BaseModel):
    last_year: InStudioStatsData = Field(..., alias="lastYear")
    this_year: InStudioStatsData = Field(..., alias="thisYear")
    last_month: InStudioStatsData = Field(..., alias="lastMonth")
    this_month: InStudioStatsData = Field(..., alias="thisMonth")
    last_week: InStudioStatsData = Field(..., alias="lastWeek")
    this_week: InStudioStatsData = Field(..., alias="thisWeek")
    all_time: InStudioStatsData = Field(..., alias="allTime")


class AllStatsTimeStats(BaseModel):
    last_year: AllStatsData = Field(..., alias="lastYear")
    this_year: AllStatsData = Field(..., alias="thisYear")
    last_month: AllStatsData = Field(..., alias="lastMonth")
    this_month: AllStatsData = Field(..., alias="thisMonth")
    last_week: AllStatsData = Field(..., alias="lastWeek")
    this_week: AllStatsData = Field(..., alias="thisWeek")
    all_time: AllStatsData = Field(..., alias="allTime")


class StatsResponse(BaseModel):
    all_stats: AllStatsTimeStats = Field(..., alias="allStats")
    in_studio: InStudioTimeStats = Field(..., alias="inStudio")
    out_studio: OutStudioTimeStats = Field(..., alias="outStudio")
