from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase


class OutOfStudioWorkoutHistory(OtfItemBase):
    member_uuid: str = Field(..., validation_alias="memberUUId")
    workout_uuid: str = Field(..., validation_alias="workoutUUId")

    workout_date: datetime | None = Field(None, validation_alias="workoutDate")
    start_time: datetime | None = Field(None, validation_alias="startTime")
    end_time: datetime | None = Field(None, validation_alias="endTime")
    duration: float | None = None
    duration_unit: str | None = Field(None, validation_alias="durationUnit")
    total_calories: int | None = Field(None, validation_alias="totalCalories")
    hr_percent_max: int | None = Field(None, validation_alias="hrPercentMax")
    distance_unit: str | None = Field(None, validation_alias="distanceUnit")
    total_distance: float | None = Field(None, validation_alias="totalDistance")
    splat_points: int | None = Field(None, validation_alias="splatPoints")
    target_heart_rate: int | None = Field(None, validation_alias="targetHeartRate")
    total_steps: int | None = Field(None, validation_alias="totalSteps")
    has_detailed_data: bool | None = Field(None, validation_alias="hasDetailedData")
    avg_heartrate: int | None = Field(None, validation_alias="avgHeartrate")
    max_heartrate: int | None = Field(None, validation_alias="maxHeartrate")
    workout_type: str | None = Field(None, validation_alias=AliasPath("workoutType", "displayName"))
    red_zone_seconds: int | None = Field(None, validation_alias="redZoneSeconds")
    orange_zone_seconds: int | None = Field(None, validation_alias="orangeZoneSeconds")
    green_zone_seconds: int | None = Field(None, validation_alias="greenZoneSeconds")
    blue_zone_seconds: int | None = Field(None, validation_alias="blueZoneSeconds")
    grey_zone_seconds: int | None = Field(None, validation_alias="greyZoneSeconds")
