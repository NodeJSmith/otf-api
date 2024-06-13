from ast import literal_eval
from datetime import datetime
from typing import Any

from pydantic import Field, PrivateAttr

from otf_api.models.base import OtfBaseModel


class WorkoutType(OtfBaseModel):
    id: int
    display_name: str = Field(..., alias="displayName")
    icon: str


class Workout(OtfBaseModel):
    studio_number: str = Field(..., alias="studioNumber")
    studio_name: str = Field(..., alias="studioName")
    class_type: str = Field(..., alias="classType")
    active_time: int = Field(..., alias="activeTime")
    coach: str
    member_uuid: str = Field(..., alias="memberUuId")
    class_date: datetime = Field(..., alias="classDate")
    total_calories: int = Field(..., alias="totalCalories")
    avg_hr: int = Field(..., alias="avgHr")
    max_hr: int = Field(..., alias="maxHr")
    avg_percent_hr: int = Field(..., alias="avgPercentHr")
    max_percent_hr: int = Field(..., alias="maxPercentHr")
    total_splat_points: int = Field(..., alias="totalSplatPoints")
    red_zone_time_second: int = Field(..., alias="redZoneTimeSecond")
    orange_zone_time_second: int = Field(..., alias="orangeZoneTimeSecond")
    green_zone_time_second: int = Field(..., alias="greenZoneTimeSecond")
    blue_zone_time_second: int = Field(..., alias="blueZoneTimeSecond")
    black_zone_time_second: int = Field(..., alias="blackZoneTimeSecond")
    step_count: int = Field(..., alias="stepCount")
    class_history_uuid: str = Field(..., alias="classHistoryUuId")
    class_id: str = Field(..., alias="classId")
    date_created: datetime = Field(..., alias="dateCreated")
    date_updated: datetime = Field(..., alias="dateUpdated")
    is_intro: bool = Field(..., alias="isIntro")
    is_leader: bool = Field(..., alias="isLeader")
    member_email: None = Field(..., alias="memberEmail")
    member_name: str = Field(..., alias="memberName")
    member_performance_id: str = Field(..., alias="memberPerformanceId")
    minute_by_minute_hr: list[int] = Field(
        ...,
        alias="minuteByMinuteHr",
        description="HR data for each minute of the workout. It is returned as a string literal, so it needs to be "
        "evaluated to a list. If can't be parsed, it will return an empty list.",
    )
    source: str
    studio_account_uuid: str = Field(..., alias="studioAccountUuId")
    version: str
    workout_type: WorkoutType = Field(..., alias="workoutType")
    _minute_by_minute_raw: str | None = PrivateAttr(None)

    @property
    def active_time_minutes(self) -> int:
        """Get the active time in minutes."""
        return self.active_time // 60

    def __init__(self, **data: Any):
        if "minuteByMinuteHr" in data:
            try:
                data["minuteByMinuteHr"] = literal_eval(data["minuteByMinuteHr"])
            except (ValueError, SyntaxError):
                data["minuteByMinuteHr"] = []

        super().__init__(**data)
        self._minute_by_minute_raw = data.get("minuteByMinuteHr")


class WorkoutList(OtfBaseModel):
    workouts: list[Workout]

    @property
    def by_class_history_uuid(self) -> dict[str, Workout]:
        return {workout.class_history_uuid: workout for workout in self.workouts}
