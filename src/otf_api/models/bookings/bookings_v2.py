from datetime import datetime
from logging import getLogger

import pendulum
from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, ApiMixin, PhoneLongitudeLatitudeMixin

# from otf_api.models.performance_summary import ZoneTimeMinutes
from .enums import BookingStatus, ClassType

LOGGER = getLogger(__name__)


class Address(AddressMixin, OtfItemBase): ...


def get_end_time(start_time: datetime, class_type: ClassType) -> datetime:
    """Get the end time of a class based on the start time and class type."""
    start_time = pendulum.instance(start_time)

    match class_type:
        case ClassType.ORANGE_60:
            return start_time.add(minutes=60)
        case ClassType.ORANGE_90:
            return start_time.add(minutes=90)
        case ClassType.STRENGTH_50 | ClassType.TREAD_50:
            return start_time.add(minutes=50)
        case ClassType.OTHER:
            LOGGER.warning(
                f"Class type {class_type} does not have defined length, returning start time plus 60 minutes"
            )
            return start_time.add(minutes=60)
        case _:
            LOGGER.warning(f"Class type {class_type} is not recognized, returning start time plus 60 minutes")
            return start_time.add(minutes=60)


class Rating(OtfItemBase):
    id: str
    description: str
    value: int


class BookingV2Studio(PhoneLongitudeLatitudeMixin, OtfItemBase):
    studio_uuid: str = Field(validation_alias="id")
    name: str | None = None
    time_zone: str | None = None
    email: str | None = None
    address: Address | None = None

    currency_code: str | None = Field(None, repr=False, exclude=True)
    mbo_studio_id: str | None = Field(None, description="MindBody attr", repr=False, exclude=True)


class BookingV2Class(ApiMixin, OtfItemBase):
    class_id: str = Field(validation_alias="id", description="Matches the `class_id` attribute of the OtfClass model")
    name: str
    class_type: ClassType = Field(validation_alias="type")
    starts_at: datetime = Field(
        validation_alias="starts_at_local",
        description="The start time of the class. Reflects local time, but the object does not have a timezone.",
    )
    studio: BookingV2Studio | None = None
    coach: str | None = Field(None, validation_alias=AliasPath("coach", "first_name"))

    class_uuid: str | None = Field(
        None,
        validation_alias="ot_base_class_uuid",
        description="Only present when class is ratable",
        exclude=True,
        repr=False,
    )
    starts_at_utc: datetime | None = Field(None, validation_alias="starts_at", exclude=True, repr=False)

    @property
    def coach_name(self) -> str:
        """Shortcut to get the coach's name, to be compatible with old Booking OtfClass model."""
        return self.coach or ""

    @property
    def ends_at(self) -> datetime:
        """Emulates the end time of the class, to be compatible with old Booking OtfClass model."""
        return get_end_time(self.starts_at, self.class_type)

    def __str__(self) -> str:
        """Returns a string representation of the class."""
        starts_at_str = self.starts_at.strftime("%a %b %d, %I:%M %p")
        return f"Class: {starts_at_str} {self.name} - {self.coach}"

    def get_booking(self) -> "BookingV2":
        """Returns a BookingV2 instance for this class.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ValueError: If class_uuid is None or empty string or if the API instance is not set.
        """
        self.raise_if_api_not_set()

        if not self.class_uuid:
            raise ValueError("class_uuid is required to get the booking")

        return self._api.bookings.get_booking_from_class_new(self)

    def cancel_booking(self) -> None:
        """Cancels the booking by calling the proper API method.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ValueError: If class_uuid is None or empty string or if the API instance is not set.
        """
        self.raise_if_api_not_set()

        self.get_booking().cancel()


class BookingV2Workout(OtfItemBase):
    id: str
    performance_summary_id: str = Field(..., validation_alias="id", description="Alias to id, to simplify the API")
    calories_burned: int
    splat_points: int
    step_count: int
    active_time_seconds: int
    # zone_time_minutes: ZoneTimeMinutes


class BookingV2(ApiMixin, OtfItemBase):
    booking_id: str = Field(
        ...,
        validation_alias="id",
        description="The booking ID used to cancel the booking - must be canceled through new endpoint",
    )

    member_uuid: str = Field(..., validation_alias="member_id")
    service_name: str | None = Field(None, description="Represents tier of member")

    cross_regional: bool | None = None
    intro: bool | None = None
    checked_in: bool
    canceled: bool
    late_canceled: bool | None = None
    canceled_at: datetime | None = None
    ratable: bool

    otf_class: BookingV2Class = Field(..., validation_alias="class")
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
    updated_at: datetime = Field(
        ..., description="Date the booking was updated, not when the booking was made", exclude=True, repr=False
    )

    @property
    def status(self) -> BookingStatus:
        """Emulates the booking status from the old API, but with less specificity."""
        if self.late_canceled:
            return BookingStatus.LateCancelled

        if self.checked_in:
            return BookingStatus.CheckedIn

        if self.canceled:
            return BookingStatus.Cancelled

        return BookingStatus.Booked

    @property
    def studio_uuid(self) -> str:
        """Shortcut to get the studio UUID."""
        if self.otf_class.studio is None:
            return ""
        return self.otf_class.studio.studio_uuid

    @property
    def class_uuid(self) -> str:
        """Shortcut to get the class UUID."""
        if self.otf_class.class_uuid is None:
            return ""
        return self.otf_class.class_uuid

    @property
    def starts_at(self) -> datetime:
        """Shortcut to get the class start time."""
        return self.otf_class.starts_at

    @property
    def ends_at(self) -> datetime:
        """Shortcut to get the class end time."""
        return self.otf_class.ends_at

    @property
    def cancelled_date(self) -> datetime | None:
        """Returns the canceled_at value in a backward-compatible way."""
        return self.canceled_at

    @property
    def id_value(self) -> str:
        """Returns the booking_id, to be compatible with old Booking model."""
        return self.booking_id

    def __str__(self) -> str:
        """Returns a string representation of the booking."""
        starts_at_str = self.otf_class.starts_at.strftime("%a %b %d, %I:%M %p")
        class_name = self.otf_class.name
        coach_name = self.otf_class.coach
        booked_str = self.status.value

        return f"Booking: {starts_at_str} {class_name} - {coach_name} ({booked_str})"

    def cancel(self) -> None:
        """Cancels the booking by calling the proper API method.

        Raises:
            ValueError: If the API instance is not set.
        """
        self.raise_if_api_not_set()

        self._api.bookings.cancel_booking_new(self)
