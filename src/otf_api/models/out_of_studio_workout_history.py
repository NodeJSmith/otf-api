from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase


class OutOfStudioWorkoutHistory(OtfItemBase):
    member_uuid: str = Field(..., alias="memberUUId")
    workout_uuid: str = Field(..., alias="workoutUUId")

    workout_date: datetime | None = Field(None, alias="workoutDate")
    start_time: datetime | None = Field(None, alias="startTime")
    end_time: datetime | None = Field(None, alias="endTime")
    duration: float | None = None
    duration_unit: str | None = Field(None, alias="durationUnit")
    total_calories: int | None = Field(None, alias="totalCalories")
    hr_percent_max: int | None = Field(None, alias="hrPercentMax")
    distance_unit: str | None = Field(None, alias="distanceUnit")
    total_distance: float | None = Field(None, alias="totalDistance")
    splat_points: int | None = Field(None, alias="splatPoints")
    target_heart_rate: int | None = Field(None, alias="targetHeartRate")
    total_steps: int | None = Field(None, alias="totalSteps")
    has_detailed_data: bool | None = Field(None, alias="hasDetailedData")
    avg_heartrate: int | None = Field(None, alias="avgHeartrate")
    max_heartrate: int | None = Field(None, alias="maxHeartrate")
    workout_type: str | None = Field(None, alias=AliasPath("workoutType", "displayName"))
    red_zone_seconds: int | None = Field(None, alias="redZoneSeconds")
    orange_zone_seconds: int | None = Field(None, alias="orangeZoneSeconds")
    green_zone_seconds: int | None = Field(None, alias="greenZoneSeconds")
    blue_zone_seconds: int | None = Field(None, alias="blueZoneSeconds")
    grey_zone_seconds: int | None = Field(None, alias="greyZoneSeconds")
