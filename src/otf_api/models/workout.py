from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.bookings_v2 import (
    BookingV2,
    BookingV2Class,
    BookingV2Studio,
    BookingV2Workout,
    Rating,
    ZoneTimeMinutes,
)
from otf_api.models.performance_summary import HeartRate, Rower, Treadmill
from otf_api.models.telemetry import Telemetry


class Workout(OtfItemBase):
    """Represents a workout - this combines the performance summary, data from the new bookings endpoint, and
    telemetry data.

    The final product contains all the performance summary data, the detailed data over time, as well as the class,
    coach, studio, and rating data from the new endpoint.

    This should match the data that is shown in the OTF app after a workout.
    """

    performance_summary_id: str = Field(..., alias="id", description="Unique identifier for this performance summary")
    class_history_uuid: str = Field(..., alias="id", description="Same as performance_summary_id")
    booking_id: str = Field(..., description="The booking id for the new bookings endpoint.")
    class_uuid: str | None = Field(
        None, description="Used by the ratings endpoint - seems to fall off after a few months"
    )
    coach: str | None = Field(None, description="First name of the coach")

    ratable: bool | None = None

    calories_burned: int | None = Field(None, validation_alias=AliasPath("details", "calories_burned"))
    splat_points: int | None = Field(None, validation_alias=AliasPath("details", "splat_points"))
    step_count: int | None = Field(None, validation_alias=AliasPath("details", "step_count"))
    zone_time_minutes: ZoneTimeMinutes | None = Field(None, validation_alias=AliasPath("details", "zone_time_minutes"))
    heart_rate: HeartRate | None = Field(None, validation_alias=AliasPath("details", "heart_rate"))
    active_time_seconds: int | None = None

    rower_data: Rower | None = Field(None, validation_alias=AliasPath("details", "equipment_data", "rower"))
    treadmill_data: Treadmill | None = Field(None, validation_alias=AliasPath("details", "equipment_data", "treadmill"))

    class_rating: Rating | None = None
    coach_rating: Rating | None = None

    otf_class: BookingV2Class
    studio: BookingV2Studio
    telemetry: Telemetry | None = None

    def __init__(self, **data):
        v2_booking = data.get("v2_booking")
        if not v2_booking:
            raise ValueError("v2_booking is required")

        assert isinstance(v2_booking, BookingV2), "v2_booking must be an instance of BookingV2"

        otf_class = v2_booking.otf_class
        v2_workout = v2_booking.workout
        assert isinstance(otf_class, BookingV2Class), "otf_class must be an instance of BookingV2Class"
        assert isinstance(v2_workout, BookingV2Workout), "v2_workout must be an instance of BookingV2Workout"

        data["otf_class"] = otf_class
        data["studio"] = otf_class.studio
        data["coach"] = otf_class.coach
        data["ratable"] = v2_booking.ratable  # this seems to be more accurate

        # data["v2_workout"] = v2_workout
        data["booking_id"] = v2_booking.booking_id
        data["active_time_seconds"] = v2_workout.active_time_seconds
        data["class_rating"] = v2_booking.class_rating
        data["coach_rating"] = v2_booking.coach_rating

        telemetry = data.get("telemetry")
        if telemetry and isinstance(telemetry, Telemetry):
            # max_hr seems to be left out of the heart rate data - it has peak_hr but they do not match
            # so if we have telemetry data, we can get the max_hr from there
            data["details"]["heart_rate"]["max_hr"] = telemetry.max_hr

        super().__init__(**data)
