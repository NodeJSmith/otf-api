import typing
from datetime import datetime

from pydantic import AliasPath, Field

from otf_api import exceptions as exc
from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import ApiMixin
from otf_api.models.studios import StudioDetail

from .enums import ClassType, DoW

if typing.TYPE_CHECKING:
    from otf_api.models.bookings import Booking, BookingV2


class OtfClass(ApiMixin, OtfItemBase):
    class_uuid: str = Field(validation_alias="ot_base_class_uuid", description="The OTF class UUID")
    class_id: str | None = Field(None, validation_alias="id", description="Matches new booking endpoint class id")

    name: str | None = Field(None, description="The name of the class")
    class_type: ClassType = Field(validation_alias="type")
    coach: str | None = Field(None, validation_alias=AliasPath("coach", "first_name"))
    ends_at: datetime = Field(
        validation_alias="ends_at_local",
        description="The end time of the class. Reflects local time, but the object does not have a timezone.",
    )
    starts_at: datetime = Field(
        validation_alias="starts_at_local",
        description="The start time of the class. Reflects local time, but the object does not have a timezone.",
    )
    studio: StudioDetail

    # capacity/status fields
    booking_capacity: int | None = None
    full: bool | None = None
    max_capacity: int | None = None
    waitlist_available: bool | None = None
    waitlist_size: int | None = Field(None, description="The number of people on the waitlist")
    is_booked: bool | None = Field(None, description="Custom helper field to determine if class is already booked")
    is_cancelled: bool | None = Field(None, validation_alias="canceled")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")

    created_at: datetime | None = Field(None, exclude=True, repr=False)
    ends_at_utc: datetime | None = Field(None, validation_alias="ends_at", exclude=True, repr=False)
    mbo_class_description_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")
    mbo_class_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")
    mbo_class_schedule_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")
    starts_at_utc: datetime | None = Field(None, validation_alias="starts_at", exclude=True, repr=False)
    updated_at: datetime | None = Field(None, exclude=True, repr=False)

    @property
    def day_of_week(self) -> DoW:
        """Returns the day of the week as an enum."""
        dow = self.starts_at.strftime("%A")
        return DoW(dow)

    def __str__(self) -> str:
        """Returns a string representation of the class."""
        starts_at_str = self.starts_at.strftime("%a %b %d, %I:%M %p")
        booked_str = ""
        if self.is_booked:
            booked_str = "Booked"
        elif self.has_availability:
            booked_str = "Available"
        elif self.waitlist_available:
            booked_str = "Waitlist Available"
        else:
            booked_str = "Full"
        return f"Class: {starts_at_str} {self.name} - {self.coach} ({booked_str})"

    @property
    def has_availability(self) -> bool:
        """Represents if the class has availability."""
        return not self.full

    @property
    def day_of_week_enum(self) -> DoW:
        """Returns the day of the week as an enum."""
        dow = self.starts_at.strftime("%A").upper()
        return DoW(dow)

    def book_class(self) -> "Booking":
        """Book a class by providing either the class_uuid or the OtfClass object.

        Returns:
            Booking: The booking.

        Raises:
            AlreadyBookedError: If the class is already booked.
            OutsideSchedulingWindowError: If the class is outside the scheduling window.
            ValueError: If class_uuid is None or empty string.
            OtfException: If there is an error booking the class.
        """
        self.raise_if_api_not_set()
        new_booking = self._api.bookings.book_class(self.class_uuid)
        self.is_booked = True
        return new_booking

    def cancel_booking(self) -> None:
        """Cancels the class booking.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ValueError: If booking_uuid is None or empty string or the API is not set.
        """
        self.raise_if_api_not_set()
        self.get_booking().cancel()

    def get_booking(self) -> "Booking | BookingV2":
        """Get the booking for this class.

        Returns:
            Booking | BookingV2: The booking associated with this class.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ValueError: If the API is not set.
        """
        self.raise_if_api_not_set()
        try:
            return self._api.bookings.get_booking_from_class(self)
        except exc.BookingNotFoundError:
            return self._api.bookings.get_booking_from_class_new(self)
