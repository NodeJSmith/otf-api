from pydantic import Field

from otf_api.models.base import OtfItemBase


class ZoneTimeMinutes(OtfItemBase):
    gray: int
    blue: int
    green: int
    orange: int
    red: int


class Details(OtfItemBase):
    calories_burned: int
    splat_points: int
    step_count: int
    active_time_seconds: int
    zone_time_minutes: ZoneTimeMinutes


class Coach(OtfItemBase):
    image_url: str | None = None
    first_name: str


class Studio(OtfItemBase):
    id: str
    license_number: str
    name: str


class Class(OtfItemBase):
    ot_base_class_uuid: str | None = None
    starts_at_local: str
    name: str | None = None
    type: str | None = None
    coach: Coach
    studio: Studio


class CoachRating(OtfItemBase):
    id: str
    description: str
    value: int


class ClassRating(OtfItemBase):
    id: str
    description: str
    value: int


class Ratings(OtfItemBase):
    coach: CoachRating
    otf_class: ClassRating = Field(..., alias="class")


class PerformanceSummaryEntry(OtfItemBase):
    id: str = Field(..., alias="id")
    details: Details
    ratable: bool
    otf_class: Class = Field(..., alias="class")
    ratings: Ratings | None = None


class PerformanceSummaryList(OtfItemBase):
    summaries: list[PerformanceSummaryEntry]
