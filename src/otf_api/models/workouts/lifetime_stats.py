from typing import Generic, TypeVar

from pydantic import Field, field_serializer

from otf_api.models.base import OtfItemBase

from .enums import StatsTime

T = TypeVar("T", bound=OtfItemBase)


class OutStudioMixin:
    """Mixin for out-of-studio workout distance metrics."""

    walking_distance: float | None = Field(
        None, validation_alias="walkingDistance", description="Total walking distance."
    )
    running_distance: float | None = Field(
        None, validation_alias="runningDistance", description="Total running distance."
    )
    cycling_distance: float | None = Field(
        None, validation_alias="cyclingDistance", description="Total cycling distance."
    )

    @field_serializer("walking_distance", "running_distance", "cycling_distance")
    @staticmethod
    def limit_floats(value: float | int | None) -> float | None:
        """Limit the float values to 2 decimal places."""
        if value is not None:
            return round(value, 2)
        return value


class InStudioMixin:
    """Mixin for in-studio equipment distance and performance metrics."""

    treadmill_distance: float | None = Field(
        None, validation_alias="treadmillDistance", description="Total treadmill distance."
    )
    treadmill_elevation_gained: float | None = Field(
        None, validation_alias="treadmillElevationGained", description="Total treadmill elevation gained."
    )
    rower_distance: float | None = Field(None, validation_alias="rowerDistance", description="Total rower distance.")
    rower_watt: float | None = Field(None, validation_alias="rowerWatt", description="Total rower watts.")

    @field_serializer("treadmill_distance", "treadmill_elevation_gained", "rower_distance", "rower_watt")
    @staticmethod
    def limit_floats(value: float | int | None) -> float | None:
        """Limit the float values to 2 decimal places."""
        if value is not None:
            return round(value, 2)
        return value


class BaseStatsData(OtfItemBase):
    """Base workout statistics data shared across all stat categories."""

    calories: float | None = Field(None, description="Total calories burned.")
    splat_point: float | None = Field(None, validation_alias="splatPoint", description="Total splat points earned.")
    total_black_zone: float | None = Field(
        None, validation_alias="totalBlackZone", description="Total minutes in gray/black zone."
    )
    total_blue_zone: float | None = Field(
        None, validation_alias="totalBlueZone", description="Total minutes in blue zone."
    )
    total_green_zone: float | None = Field(
        None, validation_alias="totalGreenZone", description="Total minutes in green zone."
    )
    total_orange_zone: float | None = Field(
        None, validation_alias="totalOrangeZone", description="Total minutes in orange zone."
    )
    total_red_zone: float | None = Field(
        None, validation_alias="totalRedZone", description="Total minutes in red zone."
    )
    workout_duration: float | None = Field(
        None, validation_alias="workoutDuration", description="Total workout duration in minutes."
    )
    step_count: float | None = Field(None, validation_alias="stepCount", description="Total step count.")


class InStudioStatsData(InStudioMixin, BaseStatsData):
    """In-studio workout statistics including equipment metrics."""

    pass


class OutStudioStatsData(OutStudioMixin, BaseStatsData):
    """Out-of-studio workout statistics including distance metrics."""

    pass


class AllStatsData(OutStudioMixin, InStudioMixin, BaseStatsData):
    """Combined in-studio and out-of-studio workout statistics."""

    pass


class TimeStats(OtfItemBase, Generic[T]):
    """Workout statistics broken down by time period."""

    last_year: T = Field(..., validation_alias="lastYear", description="Statistics from the previous year.")
    this_year: T = Field(..., validation_alias="thisYear", description="Statistics from the current year.")
    last_month: T = Field(..., validation_alias="lastMonth", description="Statistics from the previous month.")
    this_month: T = Field(..., validation_alias="thisMonth", description="Statistics from the current month.")
    last_week: T = Field(..., validation_alias="lastWeek", description="Statistics from the previous week.")
    this_week: T = Field(..., validation_alias="thisWeek", description="Statistics from the current week.")
    all_time: T = Field(..., validation_alias="allTime", description="All-time cumulative statistics.")

    def get_by_time(self, stats_time: StatsTime) -> T:
        """Get the stats data for a specific time period.

        Args:
            stats_time: The time period to retrieve statistics for.

        Returns:
            The statistics data for the specified time period.
        """
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
    """Complete lifetime statistics response containing all, in-studio, and out-of-studio data."""

    all_stats: TimeStats[AllStatsData] = Field(
        ..., validation_alias="allStats", description="Combined in-studio and out-of-studio statistics."
    )
    in_studio: TimeStats[InStudioStatsData] = Field(
        ..., validation_alias="inStudio", description="In-studio workout statistics only."
    )
    out_studio: TimeStats[OutStudioStatsData] = Field(
        ..., validation_alias="outStudio", description="Out-of-studio workout statistics only."
    )
