from datetime import datetime

from pydantic import BaseModel, Field


class Studio(BaseModel):
    studio_uuid: str = Field(..., alias="studioUUId")
    studio_name: str = Field(..., alias="studioName")
    description: str
    contact_email: str = Field(..., alias="contactEmail")
    status: str
    logo_url: str = Field(..., alias="logoUrl")
    time_zone: str = Field(..., alias="timeZone")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_id: int = Field(..., alias="studioId")
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated")


class Coach(BaseModel):
    coach_uuid: str = Field(..., alias="coachUUId")
    name: str
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    mbo_coach_id: int = Field(..., alias="mboCoachId")


class Class(BaseModel):
    class_uuid: str = Field(..., alias="classUUId")
    name: str
    description: str
    start_date_time: datetime = Field(..., alias="startDateTime")
    end_date_time: datetime = Field(..., alias="endDateTime")
    is_available: bool = Field(..., alias="isAvailable")
    is_cancelled: bool = Field(..., alias="isCancelled")
    total_booked: int = Field(..., alias="totalBooked")
    mbo_class_id: int = Field(..., alias="mboClassId")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio: Studio
    coach: Coach


class HomeStudio(BaseModel):
    studio_uuid: str = Field(..., alias="studioUUId")
    studio_name: str = Field(..., alias="studioName")
    description: str
    contact_email: str = Field(..., alias="contactEmail")
    status: str
    logo_url: str = Field(..., alias="logoUrl")
    time_zone: str = Field(..., alias="timeZone")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_id: int = Field(..., alias="studioId")
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated")


class Member(BaseModel):
    member_id: int = Field(..., alias="memberId")
    member_uuid: str = Field(..., alias="memberUUId")
    email: str
    phone_number: str = Field(..., alias="phoneNumber")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    mbo_id: str = Field(..., alias="mboId")
    cc_last4: str = Field(..., alias="ccLast4")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    home_studio: HomeStudio = Field(..., alias="homeStudio")


class CancelBooking(BaseModel):
    class_booking_id: int = Field(..., alias="classBookingId")
    class_booking_uuid: str = Field(..., alias="classBookingUUId")
    studio_id: int = Field(..., alias="studioId")
    class_id: int = Field(..., alias="classId")
    is_intro: bool = Field(..., alias="isIntro")
    member_id: int = Field(..., alias="memberId")
    mbo_member_id: str = Field(..., alias="mboMemberId")
    mbo_class_id: int = Field(..., alias="mboClassId")
    mbo_visit_id: int = Field(..., alias="mboVisitId")
    mbo_waitlist_entry_id: None = Field(..., alias="mboWaitlistEntryId")
    mbo_sync_message: str = Field(..., alias="mboSyncMessage")
    status: str
    booked_date: datetime = Field(..., alias="bookedDate")
    checked_in_date: None = Field(..., alias="checkedInDate")
    cancelled_date: datetime = Field(..., alias="cancelledDate")
    created_by: str = Field(..., alias="createdBy")
    created_date: datetime = Field(..., alias="createdDate")
    updated_by: str = Field(..., alias="updatedBy")
    updated_date: datetime = Field(..., alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    otf_class: Class = Field(..., alias="class")
    member: Member
    continue_retry: bool = Field(..., alias="continueRetry")
