from datetime import datetime
from enum import Enum
from typing import ClassVar

from pydantic import Field

from otf_api.models.base import OtfItemBase, OtfListBase
from otf_api.models.responses.classes import OtfClassTimeMixin


class StudioStatus(str, Enum):
    OTHER = "OTHER"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    COMING_SOON = "Coming Soon"
    TEMP_CLOSED = "Temporarily Closed"
    PERM_CLOSED = "Permanently Closed"


class BookingStatus(str, Enum):
    CheckedIn = "Checked In"
    CancelCheckinPending = "Cancel Checkin Pending"
    CancelCheckinRequested = "Cancel Checkin Requested"
    Cancelled = "Cancelled"
    LateCancelled = "Late Cancelled"
    Booked = "Booked"
    Waitlisted = "Waitlisted"
    CheckinPending = "Checkin Pending"
    CheckinRequested = "Checkin Requested"
    CheckinCancelled = "Checkin Cancelled"

    @classmethod
    def get_case_insensitive(cls, value: str) -> str:
        lcase_to_actual = {item.value.lower(): item.value for item in cls}
        return lcase_to_actual[value.lower()]


class Location(OtfItemBase):
    address_one: str = Field(alias="address1")
    address_two: str | None = Field(alias="address2")
    city: str
    country: str | None = None
    distance: float | None = None
    latitude: float = Field(alias="latitude")
    location_name: str | None = Field(None, alias="locationName")
    longitude: float = Field(alias="longitude")
    phone_number: str = Field(alias="phone")
    postal_code: str | None = Field(None, alias="postalCode")
    state: str | None = None


class Coach(OtfItemBase):
    coach_uuid: str = Field(alias="coachUUId")
    name: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    image_url: str = Field(alias="imageUrl", exclude=True)
    profile_picture_url: str | None = Field(None, alias="profilePictureUrl", exclude=True)


class Currency(OtfItemBase):
    currency_alphabetic_code: str = Field(alias="currencyAlphabeticCode")


class DefaultCurrency(OtfItemBase):
    currency_id: int = Field(alias="currencyId")
    currency: Currency


class StudioLocationCountry(OtfItemBase):
    country_currency_code: str = Field(alias="countryCurrencyCode")
    default_currency: DefaultCurrency = Field(alias="defaultCurrency")


class StudioLocation(OtfItemBase):
    latitude: float = Field(alias="latitude")
    longitude: float = Field(alias="longitude")
    phone_number: str = Field(alias="phoneNumber")
    physical_city: str = Field(alias="physicalCity")
    physical_address: str = Field(alias="physicalAddress")
    physical_address2: str | None = Field(alias="physicalAddress2")
    physical_state: str = Field(alias="physicalState")
    physical_postal_code: str = Field(alias="physicalPostalCode")
    physical_region: str = Field(alias="physicalRegion", exclude=True)
    physical_country_id: int = Field(alias="physicalCountryId", exclude=True)
    physical_country: str = Field(alias="physicalCountry")
    country: StudioLocationCountry = Field(alias="country", exclude=True)


class Studio(OtfItemBase):
    studio_uuid: str = Field(alias="studioUUId")
    studio_name: str = Field(alias="studioName")
    description: str | None = None
    contact_email: str = Field(alias="contactEmail", exclude=True)
    status: StudioStatus
    logo_url: str | None = Field(alias="logoUrl", exclude=True)
    time_zone: str = Field(alias="timeZone")
    mbo_studio_id: int = Field(alias="mboStudioId", exclude=True)
    studio_id: int = Field(alias="studioId")
    allows_cr_waitlist: bool | None = Field(None, alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(alias="crWaitlistFlagLastUpdated", exclude=True)
    studio_location: StudioLocation = Field(alias="studioLocation", exclude=True)


class OtfClass(OtfItemBase, OtfClassTimeMixin):
    class_uuid: str = Field(alias="classUUId")
    name: str
    description: str | None = Field(None, exclude=True)
    starts_at_local: datetime = Field(alias="startDateTime")
    ends_at_local: datetime = Field(alias="endDateTime")
    is_available: bool = Field(alias="isAvailable")
    is_cancelled: bool = Field(alias="isCancelled")
    program_name: str = Field(alias="programName")
    coach_id: int = Field(alias="coachId")
    studio: Studio
    coach: Coach
    location: Location
    virtual_class: bool | None = Field(None, alias="virtualClass")


class Member(OtfItemBase):
    member_uuid: str = Field(alias="memberUUId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str
    phone_number: str = Field(alias="phoneNumber")
    gender: str
    cc_last_4: str = Field(alias="ccLast4", exclude=True)


class Booking(OtfItemBase):
    class_booking_id: int = Field(alias="classBookingId")
    class_booking_uuid: str = Field(alias="classBookingUUId")
    studio_id: int = Field(alias="studioId")
    class_id: int = Field(alias="classId")
    is_intro: bool = Field(alias="isIntro")
    member_id: int = Field(alias="memberId")
    mbo_member_id: str = Field(alias="mboMemberId", exclude=True)
    mbo_class_id: int = Field(alias="mboClassId", exclude=True)
    mbo_visit_id: int | None = Field(None, alias="mboVisitId", exclude=True)
    mbo_waitlist_entry_id: int | None = Field(alias="mboWaitlistEntryId", exclude=True)
    mbo_sync_message: str | None = Field(alias="mboSyncMessage", exclude=True)
    status: BookingStatus
    booked_date: datetime | None = Field(None, alias="bookedDate")
    checked_in_date: datetime | None = Field(alias="checkedInDate")
    cancelled_date: datetime | None = Field(alias="cancelledDate")
    created_by: str = Field(alias="createdBy", exclude=True)
    created_date: datetime = Field(alias="createdDate")
    updated_by: str = Field(alias="updatedBy", exclude=True)
    updated_date: datetime = Field(alias="updatedDate")
    is_deleted: bool = Field(alias="isDeleted")
    member: Member = Field(exclude=True)
    waitlist_position: int | None = Field(None, alias="waitlistPosition")
    otf_class: OtfClass = Field(alias="class")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")


class BookingList(OtfListBase):
    collection_field: ClassVar[str] = "bookings"
    bookings: list[Booking]
