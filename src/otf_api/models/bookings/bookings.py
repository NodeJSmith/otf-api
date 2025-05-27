from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import ApiMixin
from otf_api.models.studios import StudioDetail

from .enums import BookingStatus


class Coach(OtfItemBase):
    coach_uuid: str = Field(validation_alias="coachUUId")
    first_name: str | None = Field(None, validation_alias="firstName")
    last_name: str | None = Field(None, validation_alias="lastName")

    # unused fields
    name: str = Field(exclude=True, repr=False)

    @property
    def full_name(self) -> str:
        """Returns the full name of the coach."""
        return f"{self.first_name} {self.last_name}"


class OtfClass(OtfItemBase):
    class_uuid: str = Field(validation_alias="classUUId")
    name: str
    starts_at: datetime = Field(validation_alias="startDateTime", description="Start time in local timezone")
    ends_at: datetime = Field(validation_alias="endDateTime", description="End time in local timezone")
    is_available: bool = Field(validation_alias="isAvailable")
    is_cancelled: bool = Field(validation_alias="isCancelled")
    studio: StudioDetail
    coach: Coach

    # unused fields
    coach_id: int | None = Field(
        None, validation_alias="coachId", exclude=True, repr=False, description="Not used by API"
    )
    description: str | None = Field(None, exclude=True, repr=False)
    program_name: str | None = Field(None, validation_alias="programName", exclude=True, repr=False)
    virtual_class: bool | None = Field(None, validation_alias="virtualClass", exclude=True, repr=False)

    @property
    def coach_name(self) -> str:
        """Shortcut to get the coach's name, to be compatible with new BookingV2Class."""
        return self.coach.first_name or ""

    def __str__(self) -> str:
        """Returns a string representation of the class."""
        starts_at_str = self.starts_at.strftime("%a %b %d, %I:%M %p")
        return f"Class: {starts_at_str} {self.name} - {self.coach.first_name}"


class Booking(ApiMixin, OtfItemBase):
    booking_uuid: str = Field(validation_alias="classBookingUUId", description="ID used to cancel the booking")
    is_intro: bool = Field(validation_alias="isIntro")
    status: BookingStatus
    booked_date: datetime | None = Field(None, validation_alias="bookedDate")
    checked_in_date: datetime | None = Field(None, validation_alias="checkedInDate")
    cancelled_date: datetime | None = Field(None, validation_alias="cancelledDate")
    created_date: datetime = Field(validation_alias="createdDate")
    updated_date: datetime = Field(validation_alias="updatedDate")
    is_deleted: bool = Field(validation_alias="isDeleted")
    waitlist_position: int | None = Field(None, validation_alias="waitlistPosition")
    otf_class: OtfClass = Field(validation_alias="class")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")

    # unused fields
    class_booking_id: int = Field(
        validation_alias="classBookingId", exclude=True, repr=False, description="Not used by API"
    )
    class_id: int = Field(validation_alias="classId", exclude=True, repr=False, description="Not used by API")
    created_by: str = Field(validation_alias="createdBy", exclude=True, repr=False)
    mbo_class_id: int | None = Field(
        None, validation_alias="mboClassId", exclude=True, repr=False, description="MindBody attr"
    )
    mbo_member_id: str | None = Field(
        None, validation_alias="mboMemberId", exclude=True, repr=False, description="MindBody attr"
    )
    mbo_sync_message: str | None = Field(
        None, validation_alias="mboSyncMessage", exclude=True, repr=False, description="MindBody attr"
    )
    mbo_visit_id: int | None = Field(
        None, validation_alias="mboVisitId", exclude=True, repr=False, description="MindBody attr"
    )
    mbo_waitlist_entry_id: int | None = Field(None, validation_alias="mboWaitlistEntryId", exclude=True, repr=False)
    member_id: int = Field(validation_alias="memberId", exclude=True, repr=False, description="Not used by API")
    studio_id: int = Field(validation_alias="studioId", exclude=True, repr=False, description="Not used by API")
    updated_by: str = Field(validation_alias="updatedBy", exclude=True, repr=False)

    @property
    def studio_uuid(self) -> str:
        """Shortcut to get the studio UUID."""
        return self.otf_class.studio.studio_uuid

    @property
    def class_uuid(self) -> str:
        """Shortcut to get the class UUID."""
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
    def id_value(self) -> str:
        """Returns the booking_uuid, to be compatible with new BookingV2 model."""
        return self.booking_uuid

    def __str__(self) -> str:
        """Returns a string representation of the booking."""
        starts_at_str = self.otf_class.starts_at.strftime("%a %b %d, %I:%M %p")
        class_name = self.otf_class.name
        coach_name = self.otf_class.coach.name
        booked_str = self.status.value

        return f"Booking: {starts_at_str} {class_name} - {coach_name} ({booked_str})"

    def cancel(self) -> None:
        """Cancels the booking by calling the proper API method.

        Raises:
            ValueError: If the API instance is not set.
        """
        self.raise_if_api_not_set()

        self._api.bookings.cancel_booking(self)
