from collections.abc import Hashable
from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase


class Class(OtfItemBase):
    class_uuid: str = Field(..., alias="classUUId")
    name: str | None = None
    description: str | None = None
    start_date_time: datetime | None = Field(None, alias="startDateTime")
    end_date_time: datetime | None = Field(None, alias="endDateTime")
    is_available: bool | None = Field(None, alias="isAvailable")
    is_cancelled: bool | None = Field(None, alias="isCancelled")
    total_booked: int | None = Field(None, alias="totalBooked")
    mbo_class_id: int | None = Field(None, alias="mboClassId")
    mbo_studio_id: int | None = Field(None, alias="mboStudioId")
    studio: dict[Hashable, Any] | None = None
    coach: dict[Hashable, Any] | None = None


class CancelBooking(OtfItemBase):
    class_booking_id: int = Field(..., alias="classBookingId")
    class_booking_uuid: str = Field(..., alias="classBookingUUId")
    otf_class: Class = Field(..., alias="class")

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
    member: dict[Hashable, Any] | None = None
    continue_retry: bool | None = Field(None, alias="continueRetry")
