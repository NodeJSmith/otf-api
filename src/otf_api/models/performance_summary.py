from datetime import datetime, time
from typing import Any

from pydantic import AliasPath, Field, field_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ClassType
from otf_api.models.studio_detail import StudioDetail


class ZoneTimeMinutes(OtfItemBase):
    gray: int
    blue: int
    green: int
    orange: int
    red: int


class CoachRating(OtfItemBase):
    id: str
    description: str
    value: int


class ClassRating(OtfItemBase):
    id: str
    description: str
    value: int


class HeartRate(OtfItemBase):
    max_hr: int
    peak_hr: int
    peak_hr_percent: int
    avg_hr: int
    avg_hr_percent: int


class Class(OtfItemBase):
    class_uuid: str | None = Field(None, description="Only populated if class is ratable", alias="ot_base_class_uuid")
    starts_at: datetime | None = Field(None, alias="starts_at_local")
    type: ClassType | None = None
    studio: StudioDetail | None = None
    name: str | None = None


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


class PerformanceSummary(OtfItemBase):
    """Represents a workout performance summary - the same data that is shown in the OTF app after a workout"

    This data comes from two different endpoints that do not actually match, because of course not.
    The summary endpoint returns one distinct set of data plus some detailed data - this is the only place we can get
    the studio information. The detail endpoint returns more performance data but does not have much class data and does
    not have the studio.

    * The summary endpoint data is missing step_count, the value is always 0.
    * The detail endpoint data is missing active_time_seconds, the value is always 0.
    * The detail endpoint class name is more generic than the summary endpoint class name.


    """

    performance_summary_id: str = Field(..., alias="id", description="Unique identifier for this performance summary")
    class_history_uuid: str = Field(..., alias="id", description="Same as performance_summary_id")
    ratable: bool | None = None
    otf_class: Class | None = Field(None, alias="class")
    coach: str | None = Field(None, alias=AliasPath("class", "coach", "first_name"))
    coach_rating: CoachRating | None = Field(None, alias=AliasPath("ratings", "coach"))
    class_rating: ClassRating | None = Field(None, alias=AliasPath("ratings", "class"))

    active_time_seconds: int | None = Field(None, alias=AliasPath("details", "active_time_seconds"))
    calories_burned: int | None = Field(None, alias=AliasPath("details", "calories_burned"))
    splat_points: int | None = Field(None, alias=AliasPath("details", "splat_points"))
    step_count: int | None = Field(None, alias=AliasPath("details", "step_count"))
    zone_time_minutes: ZoneTimeMinutes | None = Field(None, alias=AliasPath("details", "zone_time_minutes"))
    heart_rate: HeartRate | None = Field(None, alias=AliasPath("details", "heart_rate"))

    rower_data: Rower | None = Field(None, alias=AliasPath("details", "equipment_data", "rower"))
    treadmill_data: Treadmill | None = Field(None, alias=AliasPath("details", "equipment_data", "treadmill"))

    @property
    def is_rated(self) -> bool:
        return self.coach_rating is not None or self.class_rating is not None

    @property
    def studio(self) -> StudioDetail | None:
        return self.otf_class.studio if self.otf_class else None

    def __init__(self, **kwargs) -> None:
        summary_detail = kwargs.pop("details", {}) or {}
        true_detail = kwargs.pop("detail", {}) or {}

        summary_class = kwargs.pop("class", {})
        detail_class = true_detail.pop("class", {})

        kwargs["class"] = combine_class_data(summary_class, detail_class)
        kwargs["details"] = combine_detail_data(summary_detail, true_detail.pop("details", {}))

        super().__init__(**kwargs)


def combine_class_data(summary_class: dict[str, str], detail_class: dict[str, str]) -> dict[str, str]:
    class_data = {}

    class_data["ot_base_class_uuid"] = summary_class.get("ot_base_class_uuid")
    class_data["starts_at_local"] = summary_class.get("starts_at_local") or detail_class.get("starts_at_local")
    class_data["type"] = summary_class.get("type")
    class_data["studio"] = summary_class.get("studio")
    class_data["name"] = detail_class.get("name") or summary_class.get("name")
    class_data["coach"] = summary_class.get("coach")

    return class_data


def combine_detail_data(summary_detail: dict[str, Any], true_detail: dict[str, Any]) -> dict[str, Any]:
    # active time seconds always 0 in detail
    del true_detail["active_time_seconds"]

    # step count always 0 in summary
    summary_detail["step_count"] = true_detail["step_count"]

    combined_details = summary_detail | true_detail

    return combined_details
