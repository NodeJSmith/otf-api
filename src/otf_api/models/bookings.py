from collections.abc import Hashable
from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import BookingStatus, StudioStatus
from otf_api.models.mixins import OtfClassTimeMixin


class Location(OtfItemBase):
    address_one: str | None = Field(None, alias="address1")
    address_two: str | None = Field(alias="address2")
    city: str | None = None
    country: str | None = None
    distance: float | None = None
    location_name: str | None = Field(None, alias="locationName")
    latitude: float | None = Field(None, alias="latitude")
    longitude: float | None = Field(None, alias="longitude")
    phone_number: str | None = Field(None, alias="phone")
    postal_code: str | None = Field(None, alias="postalCode")
    state: str | None = None


class Coach(OtfItemBase):
    coach_uuid: str = Field(alias="coachUUId")
    name: str
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    image_url: str | None = Field(None, alias="imageUrl", exclude=True)
    profile_picture_url: str | None = Field(None, alias="profilePictureUrl", exclude=True)


class StudioLocation(OtfItemBase):
    latitude: float | None = Field(None, alias="latitude")
    longitude: float | None = Field(None, alias="longitude")
    phone_number: str | None = Field(None, alias="phoneNumber")
    physical_city: str | None = Field(None, alias="physicalCity")
    physical_address: str | None = Field(None, alias="physicalAddress")
    physical_address2: str | None = Field(None, alias="physicalAddress2")
    physical_state: str | None = Field(None, alias="physicalState")
    physical_postal_code: str | None = Field(None, alias="physicalPostalCode")
    physical_region: str | None = Field(None, alias="physicalRegion", exclude=True)
    physical_country_id: int | None = Field(None, alias="physicalCountryId", exclude=True)
    physical_country: str | None = Field(None, alias="physicalCountry")
    country: dict[Hashable, Any] | None = Field(None, alias="country", exclude=True)


class Studio(OtfItemBase):
    studio_uuid: str = Field(alias="studioUUId")
    studio_name: str = Field(alias="studioName")
    studio_id: int = Field(alias="studioId")
    description: str | None = None
    contact_email: str | None = Field(None, alias="contactEmail", exclude=True)
    status: StudioStatus | None = None
    logo_url: str | None = Field(None, alias="logoUrl", exclude=True)
    time_zone: str = Field(alias="timeZone")
    mbo_studio_id: int | None = Field(None, alias="mboStudioId", exclude=True)
    allows_cr_waitlist: bool | None = Field(None, alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime | None = Field(None, alias="crWaitlistFlagLastUpdated", exclude=True)
    studio_location: StudioLocation | None = Field(None, alias="studioLocation", exclude=True)


class OtfClass(OtfItemBase, OtfClassTimeMixin):
    class_uuid: str = Field(alias="classUUId")
    name: str
    description: str | None = Field(None, exclude=True)
    starts_at_local: datetime = Field(alias="startDateTime")
    ends_at_local: datetime = Field(alias="endDateTime")
    is_available: bool = Field(alias="isAvailable")
    is_cancelled: bool = Field(alias="isCancelled")
    program_name: str | None = Field(None, alias="programName")
    coach_id: int | None = Field(None, alias="coachId")
    studio: Studio
    coach: Coach
    location: Location | None = None
    virtual_class: bool | None = Field(None, alias="virtualClass")


class Member(OtfItemBase):
    member_uuid: str = Field(alias="memberUUId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    gender: str | None = None
    cc_last_4: str | None = Field(None, alias="ccLast4", exclude=True)


class Booking(OtfItemBase):
    class_booking_id: int = Field(alias="classBookingId")
    class_booking_uuid: str = Field(alias="classBookingUUId", description="ID used to cancel the booking")
    studio_id: int = Field(alias="studioId")
    class_id: int = Field(alias="classId")
    is_intro: bool = Field(alias="isIntro")
    member_id: int = Field(alias="memberId")
    mbo_member_id: str | None = Field(None, alias="mboMemberId", exclude=True)
    mbo_class_id: int | None = Field(None, alias="mboClassId", exclude=True)
    mbo_visit_id: int | None = Field(None, alias="mboVisitId", exclude=True)
    mbo_waitlist_entry_id: int | None = Field(None, alias="mboWaitlistEntryId", exclude=True)
    mbo_sync_message: str | None = Field(None, alias="mboSyncMessage", exclude=True)
    status: BookingStatus
    booked_date: datetime | None = Field(None, alias="bookedDate")
    checked_in_date: datetime | None = Field(None, alias="checkedInDate")
    cancelled_date: datetime | None = Field(None, alias="cancelledDate")
    created_by: str = Field(alias="createdBy", exclude=True)
    created_date: datetime = Field(alias="createdDate")
    updated_by: str = Field(alias="updatedBy", exclude=True)
    updated_date: datetime = Field(alias="updatedDate")
    is_deleted: bool = Field(alias="isDeleted")
    member: Member | None = Field(None, exclude=True)
    waitlist_position: int | None = Field(None, alias="waitlistPosition")
    otf_class: OtfClass = Field(alias="class")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")


class BookingList(OtfItemBase):
    bookings: list[Booking]
