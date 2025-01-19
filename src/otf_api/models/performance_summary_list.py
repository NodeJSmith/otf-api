from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase


class ZoneTimeMinutes(OtfItemBase):
    gray: int
    blue: int
    green: int
    orange: int
    red: int


class Class(OtfItemBase):
    class_uuid: str | None = Field(None, description="Only populated if class is ratable", alias="ot_base_class_uuid")
    starts_at: datetime | None = Field(None, alias="starts_at_local")
    name: str | None = None
    type: str | None = None


class CoachRating(OtfItemBase):
    id: str
    description: str
    value: int


class ClassRating(OtfItemBase):
    id: str
    description: str
    value: int


class PerformanceSummaryEntry(OtfItemBase):
    id: str = Field(..., alias="id")
    calories_burned: int | None = Field(None, alias=AliasPath("details", "calories_burned"))
    splat_points: int | None = Field(None, alias=AliasPath("details", "splat_points"))
    step_count: int | None = Field(None, alias=AliasPath("details", "step_count"))
    active_time_seconds: int | None = Field(None, alias=AliasPath("details", "active_time_seconds"))
    zone_time_minutes: ZoneTimeMinutes | None = Field(None, alias=AliasPath("details", "zone_time_minutes"))
    ratable: bool | None = None
    otf_class: Class | None = Field(None, alias="class")
    coach: str | None = Field(None, alias=AliasPath("class", "coach", "first_name"))
    coach_rating: CoachRating | None = Field(None, alias=AliasPath("ratings", "coach"))
    class_rating: ClassRating | None = Field(None, alias=AliasPath("ratings", "class"))

    @property
    def is_rated(self) -> bool:
        return self.coach_rating is not None or self.class_rating is not None
