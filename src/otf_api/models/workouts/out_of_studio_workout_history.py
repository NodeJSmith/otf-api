from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase


class OutOfStudioWorkoutHistory(OtfItemBase):
    """A workout performed outside the OTF studio, tracked via the OTF app or a connected device."""

    member_uuid: str = Field(..., validation_alias="memberUUId", description="Unique identifier for the member.")
    workout_uuid: str = Field(..., validation_alias="workoutUUId", description="Unique identifier for the workout.")

    workout_date: datetime | None = Field(None, validation_alias="workoutDate", description="Date of the workout.")
    start_time: datetime | None = Field(None, validation_alias="startTime", description="Start time of the workout.")
    end_time: datetime | None = Field(None, validation_alias="endTime", description="End time of the workout.")
    duration: float | None = Field(None, description="Duration of the workout.")
    duration_unit: str | None = Field(
        None, validation_alias="durationUnit", description="Unit of the duration value (e.g. minutes)."
    )
    total_calories: int | None = Field(None, validation_alias="totalCalories", description="Total calories burned.")
    hr_percent_max: int | None = Field(
        None, validation_alias="hrPercentMax", description="Peak heart rate as percentage of max HR."
    )
    distance_unit: str | None = Field(
        None, validation_alias="distanceUnit", description="Unit of distance (e.g. miles, km)."
    )
    total_distance: float | None = Field(None, validation_alias="totalDistance", description="Total distance covered.")
    splat_points: int | None = Field(None, validation_alias="splatPoints", description="Total splat points earned.")
    target_heart_rate: int | None = Field(
        None, validation_alias="targetHeartRate", description="Target heart rate for the workout."
    )
    total_steps: int | None = Field(None, validation_alias="totalSteps", description="Total step count.")
    has_detailed_data: bool | None = Field(
        None, validation_alias="hasDetailedData", description="Whether detailed telemetry data is available."
    )
    avg_heartrate: int | None = Field(
        None, validation_alias="avgHeartrate", description="Average heart rate during the workout."
    )
    max_heartrate: int | None = Field(
        None, validation_alias="maxHeartrate", description="Maximum heart rate during the workout."
    )
    workout_type: str | None = Field(
        None, validation_alias=AliasPath("workoutType", "displayName"), description="Type of workout performed."
    )
    red_zone_seconds: float | None = Field(
        None, validation_alias="redZoneSeconds", description="Seconds spent in red HR zone."
    )
    orange_zone_seconds: float | None = Field(
        None, validation_alias="orangeZoneSeconds", description="Seconds spent in orange HR zone."
    )
    green_zone_seconds: float | None = Field(
        None, validation_alias="greenZoneSeconds", description="Seconds spent in green HR zone."
    )
    blue_zone_seconds: float | None = Field(
        None, validation_alias="blueZoneSeconds", description="Seconds spent in blue HR zone."
    )
    grey_zone_seconds: float | None = Field(
        None, validation_alias="greyZoneSeconds", description="Seconds spent in grey HR zone."
    )
