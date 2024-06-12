from pydantic import Field

from otf.models.base import OtfBaseModel


class ZoneTimeMinutes(OtfBaseModel):
    gray: int
    blue: int
    green: int
    orange: int
    red: int


class Details(OtfBaseModel):
    calories_burned: int
    splat_points: int
    step_count: int
    active_time_seconds: int
    zone_time_minutes: ZoneTimeMinutes


class Coach(OtfBaseModel):
    image_url: str | None = None
    first_name: str


class Studio(OtfBaseModel):
    id: str
    license_number: str
    name: str


class Class(OtfBaseModel):
    ot_base_class_uuid: str | None = None
    starts_at_local: str
    name: str
    coach: Coach
    studio: Studio


class CoachRating(OtfBaseModel):
    id: str
    description: str
    value: int


class ClassRating(OtfBaseModel):
    id: str
    description: str
    value: int


class Ratings(OtfBaseModel):
    coach: CoachRating
    class_: ClassRating = Field(..., alias="class")


class PerformanceSummaryEntry(OtfBaseModel):
    performance_summary_id: str = Field(..., alias="id")
    details: Details
    ratable: bool
    class_: Class = Field(..., alias="class")
    ratings: Ratings | None = None


class PerformanceSummaryList(OtfBaseModel):
    summaries: list[PerformanceSummaryEntry]
