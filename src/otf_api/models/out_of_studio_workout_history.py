from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class WorkoutType(OtfItemBase):
    id: int
    display_name: str = Field(..., alias="displayName")
    icon: str


class OutOfStudioWorkoutHistory(OtfItemBase):
    workout_date: datetime = Field(..., alias="workoutDate")
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    duration_unit: str = Field(..., alias="durationUnit")
    duration: float
    total_calories: int = Field(..., alias="totalCalories")
    hr_percent_max: int = Field(..., alias="hrPercentMax")
    distance_unit: str = Field(..., alias="distanceUnit")
    total_distance: float = Field(..., alias="totalDistance")
    splat_points: int = Field(..., alias="splatPoints")
    target_heart_rate: int = Field(..., alias="targetHeartRate")
    red_zone_seconds: int = Field(..., alias="redZoneSeconds")
    orange_zone_seconds: int = Field(..., alias="orangeZoneSeconds")
    green_zone_seconds: int = Field(..., alias="greenZoneSeconds")
    blue_zone_seconds: int = Field(..., alias="blueZoneSeconds")
    grey_zone_seconds: int = Field(..., alias="greyZoneSeconds")
    total_steps: int = Field(..., alias="totalSteps")
    has_detailed_data: bool = Field(..., alias="hasDetailedData")
    workout_type: WorkoutType = Field(..., alias="workoutType")
    member_uuid: str = Field(..., alias="memberUUId")
    workout_uuid: str = Field(..., alias="workoutUUId")
    avg_heartrate: int = Field(..., alias="avgHeartrate")
    max_heartrate: int = Field(..., alias="maxHeartrate")


class OutOfStudioWorkoutHistoryList(OtfItemBase):
    workouts: list[OutOfStudioWorkoutHistory]
