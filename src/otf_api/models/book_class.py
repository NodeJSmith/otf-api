from collections.abc import Hashable
from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase


class Class(OtfItemBase):
    class_id: int = Field(None, alias="classId")
    class_uuid: str = Field(None, alias="classUUId")
    mbo_studio_id: int | None = Field(None, alias="mboStudioId")
    mbo_class_id: int | None = Field(None, alias="mboClassId")
    mbo_class_schedule_id: int | None = Field(None, alias="mboClassScheduleId")
    mbo_program_id: int | None = Field(None, alias="mboProgramId")
    studio_id: int | None = Field(None, alias="studioId")
    coach_id: int | None = Field(None, alias="coachId")
    location_id: int | None = Field(None, alias="locationId")
    name: str | None = None
    description: str | None = None
    program_name: str | None = Field(None, alias="programName")
    program_schedule_type: str | None = Field(None, alias="programScheduleType")
    program_cancel_offset: int | None = Field(None, alias="programCancelOffset")
    max_capacity: int | None = Field(None, alias="maxCapacity")
    total_booked: int | None = Field(None, alias="totalBooked")
    web_capacity: int | None = Field(None, alias="webCapacity")
    web_booked: int | None = Field(None, alias="webBooked")
    total_booked_waitlist: int | None = Field(None, alias="totalBookedWaitlist")
    start_date_time: datetime | None = Field(None, alias="startDateTime")
    end_date_time: datetime | None = Field(None, alias="endDateTime")
    is_cancelled: bool | None = Field(None, alias="isCancelled")
    substitute: bool | None = None
    is_active: bool | None = Field(None, alias="isActive")
    is_waitlist_available: bool | None = Field(None, alias="isWaitlistAvailable")
    is_enrolled: bool | None = Field(None, alias="isEnrolled")
    is_hide_cancel: bool | None = Field(None, alias="isHideCancel")
    is_available: bool | None = Field(None, alias="isAvailable")
    room_number: int | None = Field(None, alias="roomNumber")
    created_by: str | None = Field(None, alias="createdBy")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_by: str | None = Field(None, alias="updatedBy")
    updated_date: datetime | None = Field(None, alias="updatedDate")
    is_deleted: bool | None = Field(None, alias="isDeleted")
    studio: dict[Hashable, Any] | None = Field(None, exclude=True)
    location: dict[Hashable, Any] | None = Field(None, exclude=True)
    coach: dict[Hashable, Any] | None = Field(None, exclude=True)
    attributes: dict[str, Any] | None = Field(None, exclude=True)


class SavedBooking(OtfItemBase):
    class_booking_id: int = Field(..., alias="classBookingId")
    class_booking_uuid: str = Field(..., alias="classBookingUUId")
    studio_id: int | None = Field(None, alias="studioId")
    class_id: int | None = Field(None, alias="classId")
    is_intro: bool | None = Field(None, alias="isIntro")
    member_id: int | None = Field(None, alias="memberId")
    mbo_member_id: str | None = Field(None, alias="mboMemberId")
    mbo_class_id: int | None = Field(None, alias="mboClassId")
    mbo_visit_id: int | None = Field(None, alias="mboVisitId")
    mbo_waitlist_entry_id: int | None = Field(None, alias="mboWaitlistEntryId")
    mbo_sync_message: str | None = Field(None, alias="mboSyncMessage")
    status: str | None = None
    booked_date: datetime | None = Field(None, alias="bookedDate")
    checked_in_date: datetime | None = Field(None, alias="checkedInDate")
    cancelled_date: datetime | None = Field(None, alias="cancelledDate")
    created_by: str | None = Field(None, alias="createdBy")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_by: str | None = Field(None, alias="updatedBy")
    updated_date: datetime | None = Field(None, alias="updatedDate")
    is_deleted: bool | None = Field(None, alias="isDeleted")
    member: dict[Hashable, Any] | None = Field(None, exclude=True)
    otf_class: Class = Field(..., alias="class")
    custom_data: Any | None = Field(None, alias="customData", exclude=True)
    attributes: dict[str, Any] | None = Field(None, exclude=True)


class BookClass(OtfItemBase):
    saved_bookings: list[SavedBooking] = Field(None, alias="savedBookings")
    mbo_response: list[dict[Hashable, Any]] | Any | None = Field(None, alias="mboResponse", exclude=True)

    @property
    def booking(self) -> SavedBooking:
        return self.saved_bookings[0]

    @property
    def booking_uuid(self) -> str:
        """Returns the booking UUID for the class. This can be used to cancel the class."""
        return self.booking.class_booking_uuid
