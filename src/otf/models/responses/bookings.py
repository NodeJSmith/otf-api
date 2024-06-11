from datetime import datetime

from pydantic import BaseModel, Field

from .enums import ClassStatus, StudioStatus


class Location(BaseModel):
    address_one: str = Field(alias="address1")
    address_two: str | None = Field(alias="address2")
    city: str
    country: str | None = None
    distance: float | None = None
    latitude: float = Field(alias="latitude")
    location_name: str | None = Field(None, alias="locationName")
    longitude: float = Field(alias="longitude")
    phone_number: str = Field(alias="phone")


class Coach(BaseModel):
    coach_uuid: str = Field(alias="coachUUId")
    name: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    image_url: str = Field(alias="imageUrl")
    profile_picture_url: str | None = Field(None, alias="profilePictureUrl")


class Currency(BaseModel):
    currency_alphabetic_code: str = Field(alias="currencyAlphabeticCode")


class DefaultCurrency(BaseModel):
    currency_id: int = Field(alias="currencyId")
    currency: Currency


class StudioLocationCountry(BaseModel):
    country_currency_code: str = Field(alias="countryCurrencyCode")
    default_currency: DefaultCurrency = Field(alias="defaultCurrency")


class StudioLocation(BaseModel):
    latitude: float = Field(alias="latitude")
    longitude: float = Field(alias="longitude")
    phone_number: str = Field(alias="phoneNumber")
    physical_city: str = Field(alias="physicalCity")
    physical_address: str = Field(alias="physicalAddress")
    physical_address2: str | None = Field(alias="physicalAddress2")
    physical_state: str = Field(alias="physicalState")
    physical_postal_code: str = Field(alias="physicalPostalCode")
    physical_region: str = Field(alias="physicalRegion")
    physical_country_id: int = Field(alias="physicalCountryId")
    physical_country: str = Field(alias="physicalCountry")
    country: StudioLocationCountry = Field(alias="country")


class Studio(BaseModel):
    studio_uuid: str = Field(alias="studioUUId")
    studio_name: str = Field(alias="studioName")
    description: str
    contact_email: str = Field(alias="contactEmail")
    status: StudioStatus
    logo_url: str | None = Field(alias="logoUrl")
    time_zone: str = Field(alias="timeZone")
    mbo_studio_id: int = Field(alias="mboStudioId")
    studio_id: int = Field(alias="studioId")
    cr_waitlist_flag_last_updated: datetime = Field(alias="crWaitlistFlagLastUpdated")
    studio_location: StudioLocation = Field(alias="studioLocation")


class OtfClass(BaseModel):
    class_uuid: str = Field(alias="classUUId")
    name: str
    description: str
    start_date_time: datetime = Field(alias="startDateTime")
    end_date_time: datetime = Field(alias="endDateTime")
    is_available: bool = Field(alias="isAvailable")
    is_cancelled: bool = Field(alias="isCancelled")
    program_name: str = Field(alias="programName")
    coach_id: int = Field(alias="coachId")
    studio: Studio
    coach: Coach
    location: Location


class Member(BaseModel):
    member_uuid: str = Field(alias="memberUUId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str = Field(alias="email")
    phone_number: str = Field(alias="phoneNumber")
    gender: str
    cc_last_4: str = Field(alias="ccLast4")


class Booking(BaseModel):
    class_booking_id: int = Field(alias="classBookingId")
    class_booking_uuid: str = Field(alias="classBookingUUId")
    studio_id: int = Field(alias="studioId")
    class_id: int = Field(alias="classId")
    is_intro: bool = Field(alias="isIntro")
    member_id: int = Field(alias="memberId")
    mbo_member_id: str = Field(alias="mboMemberId")
    mbo_class_id: int = Field(alias="mboClassId")
    mbo_visit_id: int = Field(alias="mboVisitId")
    mbo_waitlist_entry_id: int | None = Field(alias="mboWaitlistEntryId")
    mbo_sync_message: str | None = Field(alias="mboSyncMessage")
    status: ClassStatus
    booked_date: datetime = Field(alias="bookedDate")
    checked_in_date: datetime | None = Field(alias="checkedInDate")
    cancelled_date: datetime | None = Field(alias="cancelledDate")
    created_by: str = Field(alias="createdBy")
    created_date: datetime = Field(alias="createdDate")
    updated_by: str = Field(alias="updatedBy")
    updated_date: datetime = Field(alias="updatedDate")
    is_deleted: bool = Field(alias="isDeleted")
    member: Member
    class_: OtfClass = Field(alias="class")


class BookingList(BaseModel):
    bookings: list[Booking]
