from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ClassType
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin
from otf_api.models.performance_summary import ZoneTimeMinutes


class Address(AddressMixin, OtfItemBase): ...


class Rating(OtfItemBase):
    id: str
    description: str
    value: int


class BookingV2Studio(PhoneLongitudeLatitudeMixin, OtfItemBase):
    studio_uuid: str = Field(alias="id")
    name: str | None = None
    time_zone: str | None = None
    email: str | None = None
    address: Address | None = None

    currency_code: str | None = Field(None, repr=False, exclude=True)
    mbo_studio_id: str | None = Field(None, description="MindBody attr", repr=False, exclude=True)


class BookingV2Class(OtfItemBase):
    class_id: str = Field(alias="id", description="Matches the `class_id` attribute of the OtfClass model")
    name: str
    class_type: ClassType = Field(alias="type")
    starts_at: datetime = Field(
        alias="starts_at_local",
        description="The start time of the class. Reflects local time, but the object does not have a timezone.",
    )
    studio: BookingV2Studio | None = None
    coach: str | None = Field(None, validation_alias=AliasPath("coach", "first_name"))

    class_uuid: str | None = Field(
        None, alias="ot_base_class_uuid", description="Only present when class is ratable", exclude=True, repr=False
    )
    starts_at_utc: datetime | None = Field(None, alias="starts_at", exclude=True, repr=False)


class BookingV2Workout(OtfItemBase):
    id: str
    performance_summary_id: str = Field(..., alias="id", description="Alias to id, to simplify the API")
    calories_burned: int
    splat_points: int
    step_count: int
    active_time_seconds: int
    zone_time_minutes: ZoneTimeMinutes


class BookingV2(OtfItemBase):
    booking_id: str = Field(
        ..., alias="id", description="The booking ID used to cancel the booking - must be canceled through new endpoint"
    )

    member_uuid: str = Field(..., alias="member_id")
    service_name: str | None = Field(None, description="Represents tier of member")

    cross_regional: bool | None = None
    intro: bool | None = None
    checked_in: bool
    canceled: bool
    late_canceled: bool | None = None
    canceled_at: str | None = None
    ratable: bool

    otf_class: BookingV2Class = Field(..., alias="class")
    workout: BookingV2Workout | None = None
    coach_rating: Rating | None = Field(None, validation_alias=AliasPath("ratings", "coach"))
    class_rating: Rating | None = Field(None, validation_alias=AliasPath("ratings", "class"))

    paying_studio_id: str | None = None
    mbo_booking_id: str | None = None
    mbo_unique_id: str | None = None
    mbo_paying_unique_id: str | None = None
    person_id: str

    created_at: datetime | None = Field(
        None,
        description="Date the booking was created in the system, not when the booking was made",
        exclude=True,
        repr=False,
    )
    updated_at: datetime | None = Field(
        None, description="Date the booking was updated, not when the booking was made", exclude=True, repr=False
    )
